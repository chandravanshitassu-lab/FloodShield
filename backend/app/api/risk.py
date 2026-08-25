"""
Risk Assessment router.
Prefix: /api/risk
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.risk import RiskAssessment
from app.models.user import User, UserRole
from app.schemas.risk import (
    RiskAssessmentResponse,
    RiskAssessmentDetailResponse,
    ManualRiskCreateRequest,
    RiskHistoryResponse,
)
from app.services import risk_service
from app.utils.dependencies import get_current_active_user, require_roles
from app.utils.exceptions import NotFoundError

router = APIRouter(prefix="/risk", tags=["Risk Assessment"])


@router.get(
    "/business/{business_id}",
    response_model=RiskAssessmentResponse,
    summary="Get current flood risk for a business",
)
def get_business_risk(
    business_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_active_user),
):
    """
    Compute and return the **live** flood risk assessment for a business.

    Response always conforms to the canonical format:
    ```json
    {
      "risk_score": 82,
      "risk_level": "HIGH",
      "safe_window_hours": 5
    }
    ```

    Internally calls the Risk Decision Engine; falls back to heuristic
    scoring when the engine is unavailable.
    When `risk_score >= 70`, an auto-generated Action Plan is also
    created in the background.
    """
    assessment = risk_service.get_risk_for_business(db, business_id)

    # Auto-generate an action plan for high-risk businesses
    if assessment.risk_score >= 70:
        from app.services import action_plan_service

        action_plan_service.auto_generate_plan(db, business_id, assessment.risk_score)

    return assessment


@router.get(
    "/business/{business_id}/detail",
    response_model=RiskAssessmentDetailResponse,
    summary="Get detailed risk assessment (latest)",
)
def get_business_risk_detail(
    business_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_active_user),
):
    """Return the most recent persisted assessment with full factor breakdown."""
    assessment = (
        db.query(RiskAssessment)
        .filter(RiskAssessment.business_id == business_id)
        .order_by(RiskAssessment.assessed_at.desc())
        .first()
    )
    if not assessment:
        # Trigger a fresh assessment if none exist
        assessment = risk_service.get_risk_for_business(db, business_id)
    return assessment


@router.get(
    "/business/{business_id}/history",
    response_model=RiskHistoryResponse,
    summary="Risk assessment history for a business",
)
def get_risk_history(
    business_id: int,
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_active_user),
):
    """Return paginated history of past risk assessments for a business."""
    records = (
        db.query(RiskAssessment)
        .filter(RiskAssessment.business_id == business_id)
        .order_by(RiskAssessment.assessed_at.desc())
        .limit(limit)
        .all()
    )
    return RiskHistoryResponse(total=len(records), items=records)


@router.post(
    "/business/{business_id}/manual",
    response_model=RiskAssessmentDetailResponse,
    summary="Submit a manual risk override",
    dependencies=[Depends(require_roles(UserRole.ADMIN))],
)
def create_manual_risk(
    business_id: int,
    payload: ManualRiskCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Admin-only: log a manually determined risk assessment.
    Useful for analyst overrides based on ground reports.
    """
    return risk_service.create_manual_assessment(db, business_id, payload, current_user.id)
