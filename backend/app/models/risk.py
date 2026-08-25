"""RiskAssessment ORM model — flood risk scoring for a business."""
import enum
from datetime import datetime
from sqlalchemy import (
    String, Float, Integer, DateTime, ForeignKey,
    Enum as SAEnum, JSON, func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base


class RiskLevel(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class RiskAssessment(Base):
    __tablename__ = "risk_assessments"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    business_id: Mapped[int] = mapped_column(
        ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True
    )

    risk_score: Mapped[int] = mapped_column(Integer, nullable=False)       # 0 – 100
    risk_level: Mapped[RiskLevel] = mapped_column(
        SAEnum(RiskLevel, name="risk_level"), nullable=False
    )
    safe_window_hours: Mapped[float] = mapped_column(Float, nullable=False)

    # Detailed factor breakdown stored as JSON
    flood_probability: Mapped[float | None] = mapped_column(Float, nullable=True)
    water_level_cm: Mapped[float | None] = mapped_column(Float, nullable=True)
    rainfall_mm: Mapped[float | None] = mapped_column(Float, nullable=True)
    distance_to_river_km: Mapped[float | None] = mapped_column(Float, nullable=True)
    elevation_risk_factor: Mapped[float | None] = mapped_column(Float, nullable=True)
    historical_flood_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    factor_breakdown: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    assessed_by: Mapped[str] = mapped_column(String(50), default="engine")  # "engine" | "manual"
    notes: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    assessed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    valid_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    business: Mapped["Business"] = relationship("Business", back_populates="risk_assessments")

    def __repr__(self) -> str:
        return (
            f"<RiskAssessment id={self.id} business_id={self.business_id} "
            f"score={self.risk_score} level={self.risk_level}>"
        )
