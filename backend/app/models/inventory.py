"""Inventory ORM model — tracks stock and asset levels per business."""
import enum
from datetime import datetime
from sqlalchemy import (
    String, Float, Integer, DateTime, ForeignKey,
    Enum as SAEnum, Text, Boolean, func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base


class ItemCategory(str, enum.Enum):
    ESSENTIAL_SUPPLIES = "essential_supplies"
    MEDICINES = "medicines"
    FOOD = "food"
    ELECTRONICS = "electronics"
    MACHINERY = "machinery"
    DOCUMENTS = "documents"
    FUEL = "fuel"
    OTHER = "other"


class Inventory(Base):
    __tablename__ = "inventories"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    business_id: Mapped[int] = mapped_column(
        ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True
    )

    item_name: Mapped[str] = mapped_column(String(200), nullable=False)
    sku: Mapped[str | None] = mapped_column(String(100), nullable=True)
    category: Mapped[ItemCategory] = mapped_column(
        SAEnum(ItemCategory, name="item_category"), default=ItemCategory.OTHER
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    quantity: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    unit: Mapped[str] = mapped_column(String(50), default="units")
    unit_value: Mapped[float] = mapped_column(Float, default=0.0)   # value per unit (INR)
    total_value: Mapped[float] = mapped_column(Float, default=0.0)  # computed field

    is_perishable: Mapped[bool] = mapped_column(Boolean, default=False)
    is_hazardous: Mapped[bool] = mapped_column(Boolean, default=False)
    evacuation_priority: Mapped[int] = mapped_column(Integer, default=3)  # 1=highest

    storage_location: Mapped[str | None] = mapped_column(String(200), nullable=True)
    last_audited_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    business: Mapped["Business"] = relationship("Business", back_populates="inventories")

    def __repr__(self) -> str:
        return f"<Inventory id={self.id} item={self.item_name!r} qty={self.quantity}>"
