"""
Risk Assessment service.
Fetches live data from the external Risk Decision Engine and persists the result.
Falls back to a heuristic scoring algorithm when the engine is unreachable.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

import httpx
from sqlalchemy.orm import Session

from app.database.config import settings
from app.models.business import Business
from app.models.risk import RiskAssessment, RiskLevel
from app.schemas.risk import ManualRiskCreateRequest
from app.utils.exceptions import NotFoundError

logger = logging.getLogger(__name__)


def _level_from_score(score: int) -> RiskLevel:
    if score >= 75:
        return RiskLevel.CRITICAL if score >= 90 else RiskLevel.HIGH
    if score >= 50:
        return RiskLevel.MEDIUM
    return RiskLevel.LOW


def _heuristic_score(business: Business) -> dict:
    """
    Simple rule-based fallback scoring when the ML engine is unavailable.
    Uses elevation and location metadata.
    """
    score = 50  # baseline
    if business.elevation_meters is not None:
        if business.elevation_meters < 10:
            score += 25
        elif business.elevation_meters < 30:
            score += 10
        else:
            score -= 10

    # Clamp
    score = max(0, min(100, score))
    level = _level_from_score(score)
    safe_hours = max(1.0, (100 - score) / 10.0)

    return {
        "risk_score": score,
        "risk_level": level,
        "safe_window_hours": round(safe_hours, 1),
        "assessed_by": "heuristic",
    }


def get_risk_for_business(db: Session, business_id: int) -> RiskAssessment:
    """
    Retrieve or compute a fresh risk assessment for a business.

    Strategy:
    1. Try the external Risk Engine via HTTP.
    2. On failure, fall back to heuristic scoring.
    3. Persist and return the assessment.

    Raises:
        NotFoundError: if the business does not exist.
    """
    business = db.get(Business, business_id)
    if not business:
        raise NotFoundError("Business", business_id)

    engine_data: dict | None = None
    try:
        with httpx.Client(timeout=5.0) as client:
            resp = client.post(
                f"{settings.RISK_ENGINE_URL}/assess",
                json={
                    "business_id": business_id,
                    "latitude": business.latitude,
                    "longitude": business.longitude,
                    "elevation_meters": business.elevation_meters,
                },
            )
            resp.raise_for_status()
            engine_data = resp.json()
    except Exception as exc:
        logger.warning("Risk engine unavailable (%s). Using heuristic.", exc)

    if engine_data:
        result = {
            "risk_score": int(engine_data.get("risk_score", 50)),
            "risk_level": RiskLevel(engine_data.get("risk_level", "MEDIUM")),
            "safe_window_hours": float(engine_data.get("safe_window_hours", 12.0)),
            "flood_probability": engine_data.get("flood_probability"),
            "water_level_cm": engine_data.get("water_level_cm"),
            "rainfall_mm": engine_data.get("rainfall_mm"),
            "factor_breakdown": engine_data.get("factor_breakdown"),
            "assessed_by": "engine",
        }
    else:
        fallback = _heuristic_score(business)
        result = {
            "risk_score": fallback["risk_score"],
            "risk_level": fallback["risk_level"],
            "safe_window_hours": fallback["safe_window_hours"],
            "assessed_by": "heuristic",
        }

    assessment = RiskAssessment(
        business_id=business_id,
        risk_score=result["risk_score"],
        risk_level=result["risk_level"],
        safe_window_hours=result["safe_window_hours"],
        flood_probability=result.get("flood_probability"),
        water_level_cm=result.get("water_level_cm"),
        rainfall_mm=result.get("rainfall_mm"),
        factor_breakdown=result.get("factor_breakdown"),
        assessed_by=result["assessed_by"],
        valid_until=datetime.now(tz=timezone.utc) + timedelta(hours=1),
    )
    db.add(assessment)
    db.commit()
    db.refresh(assessment)
    return assessment


def create_manual_assessment(
    db: Session, business_id: int, payload: ManualRiskCreateRequest, user_id: int
) -> RiskAssessment:
    """Store an analyst-overridden risk assessment."""
    business = db.get(Business, business_id)
    if not business:
        raise NotFoundError("Business", business_id)

    assessment = RiskAssessment(
        business_id=business_id,
        risk_score=payload.risk_score,
        risk_level=payload.risk_level,
        safe_window_hours=payload.safe_window_hours,
        flood_probability=payload.flood_probability,
        water_level_cm=payload.water_level_cm,
        rainfall_mm=payload.rainfall_mm,
        notes=payload.notes,
        assessed_by=f"manual:{user_id}",
    )
    db.add(assessment)
    db.commit()
    db.refresh(assessment)
    return assessment
