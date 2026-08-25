"""Business ORM model — represents a registered commercial entity."""
import enum
from datetime import datetime
from sqlalchemy import (
    String, Float, Integer, Boolean, DateTime, ForeignKey,
    Enum as SAEnum, Text, func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base


class BusinessType(str, enum.Enum):
    RETAIL = "retail"
    WAREHOUSE = "warehouse"
    MANUFACTURING = "manufacturing"
    PHARMACY = "pharmacy"
    FOOD_STORAGE = "food_storage"
    LOGISTICS = "logistics"
    OTHER = "other"


class BusinessStatus(str, enum.Enum):
    ACTIVE = "active"
    EVACUATING = "evacuating"
    EVACUATED = "evacuated"
    DAMAGED = "damaged"
    CLOSED = "closed"


class Business(Base):
    __tablename__ = "businesses"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)

    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    registration_number: Mapped[str | None] = mapped_column(String(100), unique=True, nullable=True)
    business_type: Mapped[BusinessType] = mapped_column(
        SAEnum(BusinessType, name="business_type"), default=BusinessType.OTHER
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Location
    address: Mapped[str] = mapped_column(String(500), nullable=False)
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    state: Mapped[str] = mapped_column(String(100), nullable=False)
    pincode: Mapped[str] = mapped_column(String(10), nullable=False)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    elevation_meters: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Metadata
    status: Mapped[BusinessStatus] = mapped_column(
        SAEnum(BusinessStatus, name="business_status"), default=BusinessStatus.ACTIVE
    )
    contact_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    contact_phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    employee_count: Mapped[int] = mapped_column(Integer, default=0)
    estimated_asset_value: Mapped[float] = mapped_column(Float, default=0.0)
    is_critical_infrastructure: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    owner: Mapped["User"] = relationship("User", back_populates="businesses")
    inventories: Mapped[list["Inventory"]] = relationship(
        "Inventory", back_populates="business", lazy="selectin"
    )
    risk_assessments: Mapped[list["RiskAssessment"]] = relationship(
        "RiskAssessment", back_populates="business", lazy="selectin"
    )
    action_plans: Mapped[list["ActionPlan"]] = relationship(
        "ActionPlan", back_populates="business", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<Business id={self.id} name={self.name!r}>"
