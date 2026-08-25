"""ActionPlan ORM model — automated contingency and mitigation plans."""
import enum
from datetime import datetime
from sqlalchemy import (
    String, Integer, DateTime, ForeignKey,
    Enum as SAEnum, JSON, Text, func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base


class PlanStatus(str, enum.Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class PlanTrigger(str, enum.Enum):
    MANUAL = "manual"
    RISK_THRESHOLD = "risk_threshold"
    WEATHER_ALERT = "weather_alert"
    FLOOD_WARNING = "flood_warning"
    SCHEDULED = "scheduled"


class ActionPlan(Base):
    __tablename__ = "action_plans"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    business_id: Mapped[int] = mapped_column(
        ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True
    )
    created_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    title: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    trigger: Mapped[PlanTrigger] = mapped_column(
        SAEnum(PlanTrigger, name="plan_trigger"), default=PlanTrigger.MANUAL
    )
    status: Mapped[PlanStatus] = mapped_column(
        SAEnum(PlanStatus, name="plan_status"), default=PlanStatus.DRAFT
    )

    # Ordered list of action steps
    steps: Mapped[list | None] = mapped_column(JSON, nullable=True)
    # e.g. [{"order": 1, "action": "Secure inventory", "responsible": "Manager", "done": false}]

    priority: Mapped[int] = mapped_column(Integer, default=3)    # 1 = highest
    target_completion_hours: Mapped[int | None] = mapped_column(Integer, nullable=True)

    activated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    business: Mapped["Business"] = relationship("Business", back_populates="action_plans")

    def __repr__(self) -> str:
        return f"<ActionPlan id={self.id} title={self.title!r} status={self.status}>"
