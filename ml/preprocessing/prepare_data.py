"""
FloodShield - Data Preprocessing and Feature Engineering Pipeline
================================================================
This script dynamically discovers and reads raw flood and rainfall datasets
from `ml/datasets/raw/`, cleans and normalizes district names, aggregates historical
flood event records, computes precipitation departures and flood-risk features,
and outputs a merged district-level flood risk dataset in `ml/datasets/processed/`.
"""

import os
import re
import sys
import logging
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("FloodShield.DataPrep")

# Paths
DEFAULT_RAW_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "datasets", "raw")
DEFAULT_PROCESSED_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "datasets", "processed")
OUTPUT_FILENAME = "flood_risk_dataset.csv"

# Known administrative and historical aliases in Indian districts
KNOWN_DISTRICT_ALIASES = {
    "ayodhya": "faizabad",
    "faizabad": "faizabad",
    "prayagraj": "allahabad",
    "allahabad": "allahabad",
    "bandipora": "bandipore",
    "bandipore": "bandipore",
    "bengaluruurban": "bangalore",
    "bangaloreurban": "bangalore",
    "bangalore": "bangalore",
    "bengaluru": "bangalore",
    "balodabazarbhatapara": "balodabazar",
    "balodabazar": "balodabazar",
    "sripottisriramulunellore": "sripottisriramulunellore",
    "sripottisriramulunell": "sripottisriramulunellore",
    "nellore": "sripottisriramulunellore",
    "sahibzadaajitsinghnagar": "sahibzadaajitsinghnagar",
    "sahibzadaajitsinghnag": "sahibzadaajitsinghnagar",
    "sasnagar": "sahibzadaajitsinghnagar",
    "southtwentyfourpargan": "south24parganas",
    "northtwentyfourpargan": "north24parganas",
    "south24parganas": "south24parganas",
    "north24parganas": "north24parganas",
    "thiruvallur": "tiruvallur",
    "tiruvallur": "tiruvallur",
    "viluppuram": "villupuram",
    "villupuram": "villupuram",
    "thiruvarur": "tiruvarur",
    "tiruvarur": "tiruvarur",
    "thoothukkudi": "thoothukudi",
    "thoothukudi": "thoothukudi",
    "kanniyakumari": "kanyakumari",
    "kanyakumari": "kanyakumari",
    "ahmedabad": "ahmadabad",
    "ahmadabad": "ahmadabad",
    "ahmednagar": "ahmadnagar",
    "ahmadnagar": "ahmadnagar",
    "arvalli": "aravalli",
    "aravalli": "aravalli",
    "bagalkotee": "bagalkote",
    "bagalkote": "bagalkote",
    "shrawasti": "shravasti",
    "sshrawasti": "shravasti",
    "shravasti": "shravasti",
    "chamarajanagaraa": "chamarajanagar",
    "chamarajanagar": "chamarajanagar",
    "jhunjhunun": "jhunjhunu",
    "jhunjhunu": "jhunjhunu",
}


def clean_text_name(name: Any) -> str:
    """Cleans basic string formatting issues like trailing punctuation, newlines, and asterisks."""
    if not isinstance(name, str) or not name.strip():
        return ""
    s = name.strip().replace("\r", "").replace("\n", "")
    s = re.sub(r"[*.,;]+$", "", s).strip()
    # Remove repeated prefixes from corrupted scrape entries
    s = re.sub(r"^(Bhadradri\s+)+", "Bhadradri ", s, flags=re.IGNORECASE)
    s = re.sub(r"^(Yadadri\s+)+", "Yadadri ", s, flags=re.IGNORECASE)
    s = re.sub(r"^(Sri\s+)+", "Sri ", s, flags=re.IGNORECASE)
    s = re.sub(r"^(Purba\s+)+", "Purba ", s, flags=re.IGNORECASE)
    s = re.sub(r"^(New\s+)+", "New ", s, flags=re.IGNORECASE)
    s = s.replace("&", "and")
    s = re.sub(r"\s+", " ", s).strip()
    return s


def canonical_district_key(name: Any) -> str:
    """
    Produces a normalized canonical key for resilient cross-dataset joining.
    Handles transliterations, vowel variations, double letters, and stop words.
    """
    if not isinstance(name, str):
        return ""
    s = clean_text_name(name).lower()
    # Remove parenthetical descriptions, e.g. "Kaimur (Bhabua)" -> "kaimur"
    s = re.sub(r"\(.*?\)", "", s)
    # Remove descriptor stop words
    s = re.sub(r"\b(district|districts|parts?|of|and|the|suburbans?)\b", "", s)
    # Strip non-alphanumeric
    s = re.sub(r"[^a-z0-9]", "", s)
    if not s:
        return ""

    # Common transliteration normalization
    s = s.replace("ahmed", "ahmad")
    s = s.replace("ananthapuramuamu", "anantapur").replace("ananthapuramu", "anantapur").replace("ananthapur", "anantapur")
    s = s.replace("arvalli", "aravalli")
    s = s.replace("sshrawasti", "shravasti").replace("shrawasti", "shravasti").replace("shrawasthi", "shravasti")
    s = s.replace("chamarajanagaraa", "chamarajanagar")
    s = s.replace("bagalkotee", "bagalkote")
    s = s.replace("ghazipurr", "ghazipur")
    s = s.replace("jhunjhunun", "jhunjhunu")
    s = s.replace("kanpurnagarnagar", "kanpurnagar").replace("kanpurnagardehat", "kanpurdehat")
    s = s.replace("uttarkashiakannada", "uttarakannada").replace("uttarkashidinajpur", "uttardinajpur")
    s = s.replace("purbapurbabardhaman", "purbabardhaman").replace("purbapurbamedinipur", "purbamedinipur")

    if s.startswith("thiru"):
        s = "tiru" + s[5:]
    s = s.replace("villu", "vilu")
    s = s.replace("tt", "t").replace("kk", "k").replace("pp", "p").replace("ll", "l")
    s = s.replace("mm", "m").replace("nn", "n").replace("dd", "d").replace("ee", "i").replace("oo", "u")

    # Apply known alias lookup
    if s in KNOWN_DISTRICT_ALIASES:
        s = KNOWN_DISTRICT_ALIASES[s]

    return s


def parse_numeric_safe(val: Any, default: float = 0.0) -> float:
    """Safely extracts numeric float values from text or number representations."""
    if pd.isna(val):
        return default
    if isinstance(val, (int, float)):
        return float(val)
    val_str = str(val).replace(",", "").strip()
    match = re.search(r"(\d+(?:\.\d+)?)", val_str)
    if match:
        try:
            return float(match.group(1))
        except (ValueError, TypeError):
            return default
    return default


def discover_raw_files(raw_dir: str) -> Dict[str, str]:
    """
    Scans raw_dir and automatically classifies CSV files based on column headers and filenames.
    """
    if not os.path.isdir(raw_dir):
        raise FileNotFoundError(f"Raw directory does not exist: {raw_dir}")

    csv_files = [f for f in os.listdir(raw_dir) if f.lower().endswith(".csv")]
    logger.info(f"Discovered {len(csv_files)} CSV files in '{raw_dir}': {csv_files}")

    discovered: Dict[str, str] = {}

    for f in csv_files:
        path = os.path.join(raw_dir, f)
        try:
            sample_df = pd.read_csv(path, nrows=5)
            cols_lower = [c.lower() for c in sample_df.columns]
            cols_str = " ".join(cols_lower)
            f_lower = f.lower()

            if "flooded_area" in cols_str or "floodedarea" in f_lower:
                discovered["flooded_area"] = path
                logger.info(f"-> Categorized '{f}' as District Flooded Area dataset.")
            elif "uei" in cols_str or "flood_inventory" in f_lower:
                discovered["flood_inventory"] = path
                logger.info(f"-> Categorized '{f}' as India Flood Inventory dataset.")
            elif "monsoon" in cols_str or "rainfall" in f_lower:
                discovered["rainfall"] = path
                logger.info(f"-> Categorized '{f}' as District Rainfall dataset.")
            else:
                logger.warning(f"-> Unrecognized CSV format in '{f}', skipping.")
        except Exception as e:
            logger.error(f"Error reading sample from '{f}': {e}")

    return discovered


def process_district_flooded_area(file_path: str) -> Tuple[pd.DataFrame, Dict[str, str]]:
    """
    Cleans District_FloodedArea dataset and returns aggregated unique districts and canonical mapping dictionary.
    """
    logger.info(f"Reading District Flooded Area from: {file_path}")
    df = pd.read_csv(file_path)
    logger.info(f"Raw Flooded Area shape: {df.shape}")

    # Standardize column names
    col_map = {}
    for c in df.columns:
        cl = c.strip().lower()
        if "dist" in cl:
            col_map[c] = "raw_dist_name"
        elif "corrected" in cl:
            col_map[c] = "corrected_percent_flooded_area"
        elif "parmanent" in cl or "permanent" in cl:
            col_map[c] = "permanent_water_percent"
        elif "percent" in cl:
            col_map[c] = "percent_flooded_area"

    df = df.rename(columns=col_map)
    df["district_name"] = df["raw_dist_name"].apply(clean_text_name)

    # Standardize explicit truncated names in raw data
    name_replacements = {
        "Sri Potti Sriramulu Nell": "Sri Potti Sriramulu Nellore",
        "Sahibzada Ajit Singh Nag": "Sahibzada Ajit Singh Nagar",
        "South Twenty Four Pargan": "South 24 Parganas",
        "North Twenty Four Pargan": "North 24 Parganas",
        "Thiruvallur": "Tiruvallur",
        "Viluppuram": "Villupuram",
        "Thiruvarur": "Tiruvarur",
        "Thoothukkudi": "Thoothukudi",
    }
    df["district_name"] = df["district_name"].replace(name_replacements)

    # Parse numeric columns
    df["percent_flooded_area"] = pd.to_numeric(df["percent_flooded_area"], errors="coerce").fillna(0.0)
    df["permanent_water_percent"] = pd.to_numeric(df["permanent_water_percent"], errors="coerce").fillna(0.0)
    df["corrected_percent_flooded_area"] = pd.to_numeric(df["corrected_percent_flooded_area"], errors="coerce").fillna(0.0)

    # Group by district_name if duplicates exist across state boundaries
    df_agg = df.groupby("district_name").agg({
        "percent_flooded_area": "mean",
        "permanent_water_percent": "mean",
        "corrected_percent_flooded_area": "mean"
    }).reset_index()

    df_agg["canonical_key"] = df_agg["district_name"].apply(canonical_district_key)

    canonical_map = dict(zip(df_agg["canonical_key"], df_agg["district_name"]))
    logger.info(f"Processed Flooded Area: {len(df_agg)} unique districts.")
    return df_agg, canonical_map


def process_flood_inventory(file_path: str, canonical_map: Dict[str, str]) -> Tuple[pd.DataFrame, Dict[str, str]]:
    """
    Parses India Flood Inventory, cleans numeric/date columns, explodes multi-district events,
    aggregates district-level flood risk statistics, and identifies district-to-state mappings.
    """
    logger.info(f"Reading Flood Inventory from: {file_path}")
    df = pd.read_csv(file_path, low_memory=False)
    logger.info(f"Raw Flood Inventory shape: {df.shape}")

    # Parse dates
    df["start_dt"] = pd.to_datetime(df["Start Date"], errors="coerce", dayfirst=True)
    df["end_dt"] = pd.to_datetime(df["End Date"], errors="coerce", dayfirst=True)
    df["event_year"] = df["start_dt"].dt.year
    df["event_month"] = df["start_dt"].dt.month

    # Clean numeric impact metrics
    df["duration_days"] = pd.to_numeric(df["Duration(Days)"], errors="coerce").fillna(1.0).clip(lower=1.0)
    df["human_fatalities"] = pd.to_numeric(df["Human fatality"], errors="coerce").fillna(0.0)
    df["human_injured"] = pd.to_numeric(df["Human injured"], errors="coerce").fillna(0.0)
    df["human_displaced"] = df["Human Displaced"].apply(parse_numeric_safe)
    df["animal_fatalities"] = df["Animal Fatality"].apply(parse_numeric_safe)

    # Explode events by affected districts
    records: List[Dict[str, Any]] = []
    dist_state_pairs: List[Tuple[str, str]] = []

    for _, row in df.iterrows():
        raw_dist_val = row.get("Districts")
        raw_state_val = row.get("State")
        if pd.isna(raw_dist_val):
            continue

        raw_dists = [p.strip() for p in re.split(r"[,;/]", str(raw_dist_val)) if p.strip()]
        states = [s.strip() for s in str(raw_state_val).split(",") if s.strip()] if pd.notna(raw_state_val) else []

        for rd in raw_dists:
            k = canonical_district_key(rd)
            matched_name = canonical_map.get(k)

            # Check inside parenthesis or before parenthesis if direct key did not match
            if not matched_name and "(" in rd:
                sub_main = re.sub(r"\(.*?\)", "", rd).strip()
                k_main = canonical_district_key(sub_main)
                matched_name = canonical_map.get(k_main)
                if not matched_name:
                    match_paren = re.search(r"\((.*?)\)", rd)
                    if match_paren:
                        k_paren = canonical_district_key(match_paren.group(1))
                        matched_name = canonical_map.get(k_paren)

            if matched_name:
                month = row["event_month"]
                year = row["event_year"]
                cause_str = str(row.get("Main Cause", "")).lower()

                records.append({
                    "district_name": matched_name,
                    "canonical_key": canonical_district_key(matched_name),
                    "duration_days": row["duration_days"],
                    "human_fatalities": row["human_fatalities"],
                    "human_injured": row["human_injured"],
                    "human_displaced": row["human_displaced"],
                    "animal_fatalities": row["animal_fatalities"],
                    "is_monsoon": 1 if (pd.notna(month) and month in [6, 7, 8, 9, 10, 11, 12]) else 0,
                    "is_heavy_rain": 1 if ("rain" in cause_str or "burst" in cause_str or "flash" in cause_str) else 0,
                    "is_recent": 1 if (pd.notna(year) and year >= 2010) else 0
                })

                if len(states) == 1:
                    dist_state_pairs.append((matched_name, states[0]))
                elif len(states) > 1:
                    for st in states:
                        dist_state_pairs.append((matched_name, st))

    df_exploded = pd.DataFrame(records)
    logger.info(f"Exploded {len(df_exploded)} district-event pairs across {df_exploded['district_name'].nunique()} unique districts.")

    # District to state mapping
    state_map_df = pd.DataFrame(dist_state_pairs, columns=["district_name", "state"])
    district_state_map = {}
    if not state_map_df.empty:
        district_state_map = (
            state_map_df.groupby("district_name")["state"]
            .agg(lambda x: x.mode().iloc[0] if len(x) > 0 else "Unknown")
            .to_dict()
        )

    # Aggregating flood inventory statistics
    df_agg = df_exploded.groupby("district_name").agg(
        total_flood_events=("duration_days", "count"),
        total_flood_duration_days=("duration_days", "sum"),
        avg_flood_duration_days=("duration_days", "mean"),
        max_flood_duration_days=("duration_days", "max"),
        total_human_fatalities=("human_fatalities", "sum"),
        avg_human_fatalities_per_event=("human_fatalities", "mean"),
        max_human_fatalities_single_event=("human_fatalities", "max"),
        total_human_injured=("human_injured", "sum"),
        total_human_displaced=("human_displaced", "sum"),
        total_animal_fatalities=("animal_fatalities", "sum"),
        monsoon_flood_events=("is_monsoon", "sum"),
        heavy_rain_flood_events=("is_heavy_rain", "sum"),
        recent_flood_events_2010_2023=("is_recent", "sum")
    ).reset_index()

    df_agg["canonical_key"] = df_agg["district_name"].apply(canonical_district_key)
    logger.info(f"Aggregated historical flood statistics for {len(df_agg)} districts.")
    return df_agg, district_state_map


def process_rainfall_data(file_path: str, canonical_map: Dict[str, str]) -> pd.DataFrame:
    """
    Cleans seasonal rainfall metrics, standardizes column names, computes precipitation anomalies/departures.
    """
    logger.info(f"Reading Rainfall dataset from: {file_path}")
    df = pd.read_csv(file_path)
    logger.info(f"Raw Rainfall dataset shape: {df.shape}")

    # Exclude state average / summary row
    df_districts = df[~df["District"].astype(str).str.contains("Average", case=False, na=False)].copy()
    df_districts["cleaned_district"] = df_districts["District"].apply(clean_text_name)
    df_districts["canonical_key"] = df_districts["cleaned_district"].apply(canonical_district_key)

    # Standardize column naming
    col_mapping = {
        "Actual Rainfall in South West Monsoon (June'17 to September'17) in mm": "actual_rainfall_sw_monsoon_mm",
        "Normal Rainfall in South West Monsoon (June'17 to September'17) in mm": "normal_rainfall_sw_monsoon_mm",
        "Actual Rainfall in North East Monsoon (October'17 to December'17) in mm": "actual_rainfall_ne_monsoon_mm",
        "Normal Rainfall in North East Monsoon (October'17 to December'17) in mm": "normal_rainfall_ne_monsoon_mm",
        "Actual Rainfall in Winter Season (January'18 to and February'18) in mm": "actual_rainfall_winter_mm",
        "Normal Rainfall in Winter Season (January'18 to and February'18) in mm": "normal_rainfall_winter_mm",
        "Actual Rainfall in Hot Weather Season (March'18 to May'18) in mm": "actual_rainfall_hot_weather_mm",
        "Normal Rainfall in Hot Weather Season (March'18 to May'18) in mm": "normal_rainfall_hot_weather_mm",
        "Total Actual Rainfall (June'17 to May'18) in mm": "total_actual_rainfall_mm",
        "Total Normal Rainfall (June'17 to May'18) in mm": "total_normal_rainfall_mm",
    }
    df_districts = df_districts.rename(columns=col_mapping)

    # Convert numeric columns
    numeric_cols = list(col_mapping.values())
    for col in numeric_cols:
        if col in df_districts.columns:
            df_districts[col] = pd.to_numeric(df_districts[col], errors="coerce").fillna(0.0)

    # Derived rainfall departure percentages
    df_districts["sw_monsoon_departure_percent"] = (
        (df_districts["actual_rainfall_sw_monsoon_mm"] - df_districts["normal_rainfall_sw_monsoon_mm"])
        / df_districts["normal_rainfall_sw_monsoon_mm"].replace(0, np.nan) * 100.0
    ).round(2)

    df_districts["ne_monsoon_departure_percent"] = (
        (df_districts["actual_rainfall_ne_monsoon_mm"] - df_districts["normal_rainfall_ne_monsoon_mm"])
        / df_districts["normal_rainfall_ne_monsoon_mm"].replace(0, np.nan) * 100.0
    ).round(2)

    df_districts["annual_rainfall_departure_percent"] = (
        (df_districts["total_actual_rainfall_mm"] - df_districts["total_normal_rainfall_mm"])
        / df_districts["total_normal_rainfall_mm"].replace(0, np.nan) * 100.0
    ).round(2)

    # Monsoon contribution ratio
    total_rain = df_districts["total_actual_rainfall_mm"].replace(0, np.nan)
    monsoon_rain = df_districts["actual_rainfall_sw_monsoon_mm"] + df_districts["actual_rainfall_ne_monsoon_mm"]
    df_districts["monsoon_intensity_ratio"] = (monsoon_rain / total_rain).fillna(0.0).round(4)

    selected_cols = [
        "canonical_key",
        "actual_rainfall_sw_monsoon_mm",
        "normal_rainfall_sw_monsoon_mm",
        "sw_monsoon_departure_percent",
        "actual_rainfall_ne_monsoon_mm",
        "normal_rainfall_ne_monsoon_mm",
        "ne_monsoon_departure_percent",
        "actual_rainfall_winter_mm",
        "normal_rainfall_winter_mm",
        "actual_rainfall_hot_weather_mm",
        "normal_rainfall_hot_weather_mm",
        "total_actual_rainfall_mm",
        "total_normal_rainfall_mm",
        "annual_rainfall_departure_percent",
        "monsoon_intensity_ratio"
    ]
    df_out = df_districts[selected_cols].copy()
    logger.info(f"Processed Rainfall features for {len(df_out)} districts.")
    return df_out


def calculate_flood_risk_score(df: pd.DataFrame) -> pd.DataFrame:
    """
    Computes normalized multi-criteria flood risk scores and risk categories.
    """
    def min_max_scale(series: pd.Series) -> pd.Series:
        min_v = series.min()
        max_v = series.max()
        if max_v == min_v:
            return pd.Series(0.0, index=series.index)
        return (series - min_v) / (max_v - min_v)

    # Factor 1: Flooded area exposure (corrected % flooded area)
    exposure_score = min_max_scale(df["corrected_percent_flooded_area"]) * 100.0

    # Factor 2: Historical flood frequency (log-scaled)
    frequency_score = min_max_scale(np.log1p(df["total_flood_events"])) * 100.0

    # Factor 3: Historical flood duration (log-scaled)
    duration_score = min_max_scale(np.log1p(df["total_flood_duration_days"])) * 100.0

    # Factor 4: Historical human fatality impact (log-scaled)
    impact_score = min_max_scale(np.log1p(df["total_human_fatalities"])) * 100.0

    # Weighted composite score (0-100 scale)
    composite_score = (
        0.40 * exposure_score +
        0.25 * frequency_score +
        0.20 * duration_score +
        0.15 * impact_score
    ).round(2)

    df["flood_risk_score"] = composite_score

    # Assign risk levels
    def assign_level(score: float) -> str:
        if score >= 60.0:
            return "Very High"
        elif score >= 35.0:
            return "High"
        elif score >= 15.0:
            return "Moderate"
        else:
            return "Low"

    df["flood_risk_level"] = df["flood_risk_score"].apply(assign_level)
    return df


def prepare_dataset(raw_dir: str = DEFAULT_RAW_DIR, processed_dir: str = DEFAULT_PROCESSED_DIR) -> pd.DataFrame:
    """
    Main orchestration function: discovers raw CSVs, processes and merges datasets,
    generates flood risk features, and saves the final processed dataset.
    """
    logger.info("Starting FloodShield data preparation pipeline...")
    os.makedirs(processed_dir, exist_ok=True)

    # Discover files
    raw_files = discover_raw_files(raw_dir)
    if "flooded_area" not in raw_files:
        raise FileNotFoundError("District Flooded Area dataset not found in raw directory.")

    # 1. Process Flooded Area dataset (master district list)
    df_master, canonical_map = process_district_flooded_area(raw_files["flooded_area"])

    # 2. Process Flood Inventory if present
    df_inv_agg = None
    district_state_map = {}
    if "flood_inventory" in raw_files:
        df_inv_agg, district_state_map = process_flood_inventory(raw_files["flood_inventory"], canonical_map)

    # 3. Process Rainfall dataset if present
    df_rain_processed = None
    if "rainfall" in raw_files:
        df_rain_processed = process_rainfall_data(raw_files["rainfall"], canonical_map)

    # Merge datasets
    merged = df_master.copy()

    if df_inv_agg is not None:
        merged = pd.merge(
            merged,
            df_inv_agg.drop(columns=["district_name"]),
            on="canonical_key",
            how="left"
        )

    if df_rain_processed is not None:
        merged = pd.merge(
            merged,
            df_rain_processed,
            on="canonical_key",
            how="left"
        )

    # Handle missing values safely
    inv_metric_cols = [
        "total_flood_events", "total_flood_duration_days", "avg_flood_duration_days",
        "max_flood_duration_days", "total_human_fatalities", "avg_human_fatalities_per_event",
        "max_human_fatalities_single_event", "total_human_injured", "total_human_displaced",
        "total_animal_fatalities", "monsoon_flood_events", "heavy_rain_flood_events",
        "recent_flood_events_2010_2023"
    ]
    for col in inv_metric_cols:
        if col in merged.columns:
            merged[col] = merged[col].fillna(0.0)

    # Assign state
    merged["state"] = merged["district_name"].map(district_state_map).fillna("Unknown")
    # Resolve state for districts present in the rainfall dataset if state is Unknown
    if "total_actual_rainfall_mm" in merged.columns:
        merged.loc[(merged["state"] == "Unknown") & (merged["total_actual_rainfall_mm"].notna()), "state"] = "Tamil Nadu"

    # Add presence indicator flags
    if "total_flood_events" in merged.columns:
        merged["has_historical_flood_record"] = (merged["total_flood_events"] > 0).astype(int)
    if "total_actual_rainfall_mm" in merged.columns:
        merged["has_detailed_rainfall_data"] = (merged["total_actual_rainfall_mm"].notna()).astype(int)

    # Compute risk scores
    merged = calculate_flood_risk_score(merged)

    # Drop temporary joining key
    merged = merged.drop(columns=["canonical_key"])

    # Reorder columns logically
    priority_cols = [
        "district_name", "state", "flood_risk_level", "flood_risk_score",
        "corrected_percent_flooded_area", "percent_flooded_area", "permanent_water_percent",
        "total_flood_events", "total_flood_duration_days", "avg_flood_duration_days",
        "max_flood_duration_days", "total_human_fatalities", "avg_human_fatalities_per_event",
        "max_human_fatalities_single_event", "total_human_injured", "total_human_displaced",
        "total_animal_fatalities", "monsoon_flood_events", "heavy_rain_flood_events",
        "recent_flood_events_2010_2023", "has_historical_flood_record", "has_detailed_rainfall_data"
    ]
    other_cols = [c for c in merged.columns if c not in priority_cols]
    final_cols = [c for c in priority_cols if c in merged.columns] + other_cols
    df_final = merged[final_cols].copy()

    # Save processed CSV
    output_path = os.path.join(processed_dir, OUTPUT_FILENAME)
    df_final.to_csv(output_path, index=False)
    logger.info(f"Successfully exported processed flood risk dataset to: {output_path}")

    # Summary reporting
    print("\n" + "=" * 75)
    print("FLOODSHIELD DATA PREPARATION COMPLETE")
    print("=" * 75)
    print(f"Output File: {output_path}")
    print(f"Dataset Dimensions: {df_final.shape[0]} rows (districts) x {df_final.shape[1]} columns")
    print("\nRisk Level Distribution:")
    print(df_final["flood_risk_level"].value_counts().to_string())
    print("\nTop 10 High-Risk Districts:")
    print(df_final.sort_values(by="flood_risk_score", ascending=False)[
        ["district_name", "state", "flood_risk_score", "flood_risk_level", "corrected_percent_flooded_area", "total_flood_events"]
    ].head(10).to_string(index=False))
    print("\nColumns in Processed Dataset:")
    for idx, col in enumerate(df_final.columns, start=1):
        print(f"  {idx:2d}. {col} ({df_final[col].dtype})")
    print("=" * 75 + "\n")

    return df_final


if __name__ == "__main__":
    raw_path = DEFAULT_RAW_DIR
    processed_path = DEFAULT_PROCESSED_DIR
    if len(sys.argv) > 1:
        raw_path = sys.argv[1]
    if len(sys.argv) > 2:
        processed_path = sys.argv[2]
    prepare_dataset(raw_path, processed_path)
