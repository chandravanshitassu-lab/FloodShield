"""
Transport Engine — Member 4: Maps & Logistics
Finds the nearest available vehicle for a business using haversine distance.
"""
from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from app.models.business import Business
from app.models.vehicle import Vehicle, VehicleStatus
from app.services.storage_engine import haversine_km


def find_best_transport(
    db: Session,
    business: Business,
    required_weight_tons: Optional[float] = None,
) -> Optional[Vehicle]:
    """
    Return the nearest AVAILABLE vehicle whose payload capacity meets the
    business's logistics requirement.  Returns None when no qualifying
    vehicle is found or the business has no geocoordinates.
    """
    if business.latitude is None or business.longitude is None:
        return None

    query = db.query(Vehicle).filter(
        Vehicle.status == VehicleStatus.AVAILABLE,
        Vehicle.current_latitude != None,   # noqa: E711
        Vehicle.current_longitude != None,  # noqa: E711
    )

    if required_weight_tons:
        query = query.filter(Vehicle.payload_capacity_tons >= required_weight_tons)

    vehicles = query.all()
    if not vehicles:
        return None

    return min(
        vehicles,
        key=lambda v: haversine_km(
            business.latitude, business.longitude,
            v.current_latitude, v.current_longitude,
        ),
    )