"""Route ORM model — computed evacuation or transport routes."""
import enum
from datetime import datetime
from sqlalchemy import (
    String, Float, Integer, Boolean, DateTime, ForeignKey,
    Enum as SAEnum, JSON, Text, func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base


class RouteStatus(str, enum.Enum):
    PLANNED = "planned"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    BLOCKED = "blocked"


class Route(Base):
    __tablename__ = "routes"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    business_id: Mapped[int | None] = mapped_column(
        ForeignKey("businesses.id", ondelete="SET NULL"), nullable=True, index=True
    )
    vehicle_id: Mapped[int | None] = mapped_column(
        ForeignKey("vehicles.id", ondelete="SET NULL"), nullable=True, index=True
    )
    destination_warehouse_id: Mapped[int | None] = mapped_column(
        ForeignKey("warehouses.id", ondelete="SET NULL"), nullable=True, index=True
    )

    # Origin
    origin_address: Mapped[str] = mapped_column(String(500), nullable=False)
    origin_latitude: Mapped[float] = mapped_column(Float, nullable=False)
    origin_longitude: Mapped[float] = mapped_column(Float, nullable=False)

    # Destination
    destination_address: Mapped[str] = mapped_column(String(500), nullable=False)
    destination_latitude: Mapped[float] = mapped_column(Float, nullable=False)
    destination_longitude: Mapped[float] = mapped_column(Float, nullable=False)

    # Route details
    distance_km: Mapped[float | None] = mapped_column(Float, nullable=True)
    estimated_duration_min: Mapped[int | None] = mapped_column(Integer, nullable=True)
    waypoints: Mapped[list | None] = mapped_column(JSON, nullable=True)     # [{lat, lng}]
    flood_risk_zones: Mapped[list | None] = mapped_column(JSON, nullable=True)
    is_flood_safe: Mapped[bool] = mapped_column(Boolean, default=True)
    safety_score: Mapped[float | None] = mapped_column(Float, nullable=True)  # 0–100

    status: Mapped[RouteStatus] = mapped_column(
        SAEnum(RouteStatus, name="route_status"), default=RouteStatus.PLANNED
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    vehicle: Mapped["Vehicle | None"] = relationship("Vehicle", back_populates="routes")
    destination_warehouse: Mapped["Warehouse | None"] = relationship(
        "Warehouse", back_populates="routes"
    )

    def __repr__(self) -> str:
        return f"<Route id={self.id} status={self.status}>"
