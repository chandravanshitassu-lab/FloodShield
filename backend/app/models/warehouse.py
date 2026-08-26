"""Warehouse ORM model — safe holding/evacuation facilities."""
import enum
from datetime import datetime
from sqlalchemy import (
    String, Float, Integer, Boolean, DateTime,
    Enum as SAEnum, Text, func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base


class WarehouseStatus(str, enum.Enum):
    AVAILABLE = "available"
    PARTIALLY_FULL = "partially_full"
    FULL = "full"
    UNSAFE = "unsafe"
    CLOSED = "closed"


class Warehouse(Base):
    __tablename__ = "warehouses"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    operator_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Location
    address: Mapped[str] = mapped_column(String(500), nullable=False)
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    state: Mapped[str] = mapped_column(String(100), nullable=False)
    pincode: Mapped[str] = mapped_column(String(10), nullable=False)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    elevation_meters: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    # Capacity
    total_capacity_sqm: Mapped[float] = mapped_column(Float, default=0.0)
    available_capacity_sqm: Mapped[float] = mapped_column(Float, default=0.0)
    max_weight_tons: Mapped[float | None] = mapped_column(Float, nullable=True)

    status: Mapped[WarehouseStatus] = mapped_column(
        SAEnum(WarehouseStatus, name="warehouse_status"), default=WarehouseStatus.AVAILABLE
    )
    is_flood_safe: Mapped[bool] = mapped_column(Boolean, default=True)
    has_power_backup: Mapped[bool] = mapped_column(Boolean, default=False)
    has_cold_storage: Mapped[bool] = mapped_column(Boolean, default=False)
    contact_phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    contact_email: Mapped[str | None] = mapped_column(String(255), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    routes: Mapped[list["Route"]] = relationship("Route", back_populates="destination_warehouse")

    def __repr__(self) -> str:
        return f"<Warehouse id={self.id} name={self.name!r} status={self.status}>"
