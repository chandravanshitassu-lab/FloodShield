"""
Storage Engine — Member 4: Maps & Logistics
Finds the nearest flood-safe warehouse for a business using haversine distance.
"""
from __future__ import annotations

import math
from typing import Optional

from sqlalchemy.orm import Session

from app.models.business import Business
from app.models.warehouse import Warehouse, WarehouseStatus


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Return great-circle distance in kilometres between two GPS points."""
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def find_safe_warehouse(
    db: Session,
    business: Business,
    required_weight_tons: Optional[float] = None,
) -> Optional[Warehouse]:
    """
    Return the nearest flood-safe warehouse that can accommodate the
    business's inventory weight.  Returns None when no suitable warehouse
    is found or the business has no GPS coordinates.
    """
    if business.latitude is None or business.longitude is None:
        return None

    safe_statuses = {WarehouseStatus.AVAILABLE, WarehouseStatus.PARTIALLY_FULL}
    query = db.query(Warehouse).filter(
        Warehouse.is_flood_safe.is_(True),
        Warehouse.status.in_(safe_statuses),
    )

    if required_weight_tons:
        query = query.filter(
            (Warehouse.max_weight_tons == None) |  # noqa: E711
            (Warehouse.max_weight_tons >= required_weight_tons)
        )

    warehouses = query.all()
    if not warehouses:
        return None

    return min(
        warehouses,
        key=lambda wh: haversine_km(
            business.latitude, business.longitude,
            wh.latitude, wh.longitude,
        ),
    )