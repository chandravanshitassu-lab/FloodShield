from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[3]
INVENTORY_FILE = PROJECT_ROOT / "ml" / "datasets" / "raw" / "Goods.csv"


REQUIRED_COLUMNS = {
    "product_id",
    "name",
    "category",
    "price",
    "stock_quantity",
}


# Flood vulnerability based on product category.
# This is an explainable MVP rule, not a scientific disaster formula.
CATEGORY_VULNERABILITY = {
    "Electronics": 1.00,
    "Apparel": 0.85,
    "Home & Kitchen": 0.65,
    "Groceries": 0.60,
    "Sports": 0.50,
    "Stationery": 0.35,
}


# Operator-selected flood warning levels used by the dashboard.
# Distinct from ML district classes (Low / Moderate / High / Very High).
FLOOD_RISK_WEIGHTS = {
    "low": 0.20,
    "medium": 0.55,
    "high": 0.90,
}

ALLOWED_FLOOD_RISK_LEVELS = frozenset(FLOOD_RISK_WEIGHTS.keys())


def normalize_flood_risk_level(flood_risk_level: str) -> str:
    """Normalize and validate dashboard flood-risk values."""

    if flood_risk_level is None:
        raise ValueError(
            "Invalid flood risk. Use: low, medium, or high."
        )

    normalized = str(flood_risk_level).strip().lower()

    aliases = {
        "moderate": "medium",
        "very high": "high",
        "veryhigh": "high",
    }
    normalized = aliases.get(normalized, normalized)

    if normalized not in ALLOWED_FLOOD_RISK_LEVELS:
        raise ValueError(
            "Invalid flood risk. Use: low, medium, or high."
        )

    return normalized


def load_inventory() -> pd.DataFrame:
    """Load, coerce, and skip malformed inventory rows."""

    if not INVENTORY_FILE.exists():
        raise FileNotFoundError(
            f"Inventory file not found: {INVENTORY_FILE}"
        )

    df = pd.read_csv(INVENTORY_FILE)

    missing_columns = REQUIRED_COLUMNS - set(df.columns)

    if missing_columns:
        raise ValueError(
            f"Missing required inventory columns: "
            f"{sorted(missing_columns)}"
        )

    df = df[
        [
            "product_id",
            "name",
            "category",
            "price",
            "stock_quantity",
        ]
    ].copy()

    df["product_id"] = pd.to_numeric(
        df["product_id"],
        errors="coerce",
    )
    df["price"] = pd.to_numeric(
        df["price"],
        errors="coerce",
    )
    df["stock_quantity"] = pd.to_numeric(
        df["stock_quantity"],
        errors="coerce",
    )
    df["name"] = df["name"].astype(str).str.strip()
    df["category"] = df["category"].astype(str).str.strip()

    valid_mask = (
        df["product_id"].notna()
        & df["name"].ne("")
        & df["name"].ne("nan")
        & df["category"].ne("")
        & df["category"].ne("nan")
        & df["price"].notna()
        & (df["price"] >= 0)
        & df["stock_quantity"].notna()
        & (df["stock_quantity"] >= 0)
    )

    df = df.loc[valid_mask].copy()
    df = df.drop_duplicates(
        subset=["product_id"],
        keep="first",
    )

    if df.empty:
        raise ValueError(
            "Invalid inventory data. No usable product records found."
        )

    df["product_id"] = df["product_id"].astype(int)
    df["stock_quantity"] = df["stock_quantity"].round().astype(int)

    return df


def get_inventory_summary() -> dict:
    """Return summary statistics for the real inventory."""

    df = load_inventory()

    df["inventory_value"] = (
        df["price"] * df["stock_quantity"]
    )

    category_summary = (
        df.groupby("category")
        .agg(
            product_count=("product_id", "count"),
            total_units=("stock_quantity", "sum"),
            total_value=("inventory_value", "sum"),
        )
        .reset_index()
    )

    return {
        "total_products": int(len(df)),
        "total_inventory_units": int(
            df["stock_quantity"].sum()
        ),
        "total_inventory_value": round(
            float(df["inventory_value"].sum()),
            2,
        ),
        "category_wise_summary": category_summary.to_dict(
            orient="records"
        ),
    }


def _priority_level(score: float) -> str:
    if score >= 75:
        return "Critical"
    if score >= 60:
        return "High"
    if score >= 40:
        return "Medium"
    return "Low"


def _recommended_action(
    flood_risk_level: str,
    score: float,
    vulnerability_score: float,
) -> str:
    """
    Map flood risk + score + vulnerability to an operator action.

    LOW avoids emergency movement except for highly exposed stock.
    MEDIUM raises prepare / move-soon / move-first urgency.
    HIGH treats high-loss vulnerable stock as immediate movement.
    """

    if flood_risk_level == "low":
        if score >= 62 and vulnerability_score >= 85:
            return "MOVE SOON"
        if score >= 48:
            return "PREPARE"
        return "MONITOR"

    if flood_risk_level == "medium":
        if score >= 72:
            return "MOVE FIRST"
        if score >= 58:
            return "MOVE SOON"
        if score >= 42:
            return "PREPARE"
        return "MONITOR"

    if score >= 68:
        return "MOVE FIRST"
    if score >= 50:
        return "MOVE SOON"
    return "MONITOR"


def prioritize_inventory(
    flood_risk_level: str,
) -> list[dict]:
    """
    Prioritize inventory using an explainable scoring model.

    Score components (weights sum to 1.00):
    - 28% inventory value
    - 12% stock quantity
    - 22% product flood vulnerability
    - 28% flood exposure (flood risk x vulnerability)
    - 10% flood urgency (global risk shift)

    Flood risk changes the last two terms, so vulnerable
    high-value items rise faster than low-vulnerability stock.
    """

    df = load_inventory()
    normalized_risk = normalize_flood_risk_level(
        flood_risk_level
    )
    risk_weight = FLOOD_RISK_WEIGHTS[normalized_risk]

    df["inventory_value"] = (
        df["price"] * df["stock_quantity"]
    )

    max_value = max(
        float(df["inventory_value"].max()),
        1.0,
    )
    value_score = (
        df["inventory_value"] / max_value
    ) * 100

    max_stock = max(
        float(df["stock_quantity"].max()),
        1.0,
    )
    stock_score = (
        df["stock_quantity"] / max_stock
    ) * 100

    df["vulnerability"] = (
        df["category"]
        .map(CATEGORY_VULNERABILITY)
        .fillna(0.50)
    )
    df["vulnerability_score"] = (
        df["vulnerability"] * 100
    )

    # Risk x vulnerability: electronics move more than stationery
    # when the flood warning increases.
    exposure_score = (
        risk_weight * df["vulnerability_score"]
    )
    urgency_score = risk_weight * 100

    df["priority_score"] = (
        0.28 * value_score
        + 0.12 * stock_score
        + 0.22 * df["vulnerability_score"]
        + 0.28 * exposure_score
        + 0.10 * urgency_score
    )

    df["priority_level"] = df["priority_score"].apply(
        _priority_level
    )

    df["recommended_action"] = [
        _recommended_action(
            normalized_risk,
            float(score),
            float(vuln),
        )
        for score, vuln in zip(
            df["priority_score"],
            df["vulnerability_score"],
        )
    ]

    def make_reason(row) -> str:
        return (
            f"{row['recommended_action']} at "
            f"{normalized_risk.upper()} flood risk because "
            f"{row['category']} has "
            f"{int(row['vulnerability_score'])}% flood vulnerability "
            f"and {int(row['stock_quantity'])} units worth "
            f"${row['inventory_value']:,.2f}."
        )

    df["reason"] = df.apply(make_reason, axis=1)

    df = df.sort_values(
        by="priority_score",
        ascending=False,
    )

    return [
        {
            "product_id": int(row["product_id"]),
            "name": row["name"],
            "category": row["category"],
            "price": float(row["price"]),
            "stock_quantity": int(row["stock_quantity"]),
            "inventory_value": round(
                float(row["inventory_value"]),
                2,
            ),
            "vulnerability_score": round(
                float(row["vulnerability_score"]),
                2,
            ),
            "priority_score": round(
                float(row["priority_score"]),
                2,
            ),
            "priority_level": row["priority_level"],
            "recommended_action": row["recommended_action"],
            "reason": row["reason"],
        }
        for _, row in df.iterrows()
    ]
