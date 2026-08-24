"""Vehicle ORM model — evacuation and transport fleet."""
import enum
from datetime import datetime
from sqlalchemy import (
    String, Float, Integer, Boolean, DateTime,
    Enum as SAEnum, func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base


class VehicleType(str, enum.Enum):
    TRUCK = "truck"
    VAN = "van"
    BOAT = "boat"
    HELICOPTER = "helicopter"
    FORKLIFT = "forklift"
    AMBULANCE = "ambulance"
    BUS = "bus"
    OTHER = "other"


class VehicleStatus(str, enum.Enum):
    AVAILABLE = "available"
    IN_TRANSIT = "in_transit"
    LOADING = "loading"
    MAINTENANCE = "maintenance"
    UNAVAILABLE = "unavailable"


class Vehicle(Base):
    __tablename__ = "vehicles"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    registration_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    vehicle_type: Mapped[VehicleType] = mapped_column(
        SAEnum(VehicleType, name="vehicle_type"), nullable=False
    )
    make: Mapped[str | None] = mapped_column(String(100), nullable=True)
    model: Mapped[str | None] = mapped_column(String(100), nullable=True)
    year: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Capacity
    payload_capacity_tons: Mapped[float] = mapped_column(Float, default=0.0)
    passenger_capacity: Mapped[int] = mapped_column(Integer, default=0)
    volume_capacity_cbm: Mapped[float | None] = mapped_column(Float, nullable=True)

    status: Mapped[VehicleStatus] = mapped_column(
        SAEnum(VehicleStatus, name="vehicle_status"), default=VehicleStatus.AVAILABLE
    )

    # Real-time location (updated by GPS/driver app)
    current_latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    current_longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    last_location_update: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    driver_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    driver_phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    is_amphibious: Mapped[bool] = mapped_column(Boolean, default=False)
    fuel_level_pct: Mapped[float | None] = mapped_column(Float, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    routes: Mapped[list["Route"]] = relationship("Route", back_populates="vehicle")

    def __repr__(self) -> str:
        return f"<Vehicle id={self.id} reg={self.registration_number!r} status={self.status}>"
