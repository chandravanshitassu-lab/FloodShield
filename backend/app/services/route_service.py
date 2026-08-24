"""
Route Optimisation service.
Delegates route computation to the external Route Engine and persists the result.
Falls back to a straight-line placeholder when the engine is unreachable.
"""
from __future__ import annotations

import logging
import math
from typing import Any

import httpx
from sqlalchemy.orm import Session

from app.database.config import settings
from app.models.route import Route, RouteStatus
from app.schemas.route import RouteComputeRequest
from app.utils.exceptions import NotFoundError

logger = logging.getLogger(__name__)


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance in km (Haversine formula)."""
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def compute_route(db: Session, payload: RouteComputeRequest) -> Route:
    """
    Compute a flood-safe route.

    1. Calls external Route Engine for optimised, flood-aware path.
    2. Falls back to straight-line estimate on failure.
    3. Persists and returns the Route record.
    """
    engine_data: dict[str, Any] | None = None
    try:
        with httpx.Client(timeout=8.0) as client:
            resp = client.post(
                f"{settings.ROUTE_ENGINE_URL}/compute",
                json={
                    "origin": {
                        "lat": payload.origin_latitude,
                        "lng": payload.origin_longitude,
                    },
                    "destination": {
                        "lat": payload.destination_latitude,
                        "lng": payload.destination_longitude,
                    },
                    "business_id": payload.business_id,
                },
            )
            resp.raise_for_status()
            engine_data = resp.json()
    except Exception as exc:
        logger.warning("Route engine unavailable (%s). Using fallback.", exc)

    if engine_data:
        distance_km = engine_data.get("distance_km")
        duration_min = engine_data.get("estimated_duration_min")
        waypoints = engine_data.get("waypoints", [])
        flood_risk_zones = engine_data.get("flood_risk_zones", [])
        is_flood_safe = engine_data.get("is_flood_safe", True)
        safety_score = engine_data.get("safety_score")
    else:
        distance_km = round(
            _haversine_km(
                payload.origin_latitude,
                payload.origin_longitude,
                payload.destination_latitude,
                payload.destination_longitude,
            ),
            2,
        )
        # Assume avg 40 km/h in emergency conditions
        duration_min = int((distance_km / 40) * 60)
        waypoints = []
        flood_risk_zones = []
        is_flood_safe = True
        safety_score = None

    route = Route(
        business_id=payload.business_id,
        vehicle_id=payload.vehicle_id,
        destination_warehouse_id=payload.destination_warehouse_id,
        origin_address=payload.origin_address,
        origin_latitude=payload.origin_latitude,
        origin_longitude=payload.origin_longitude,
        destination_address=payload.destination_address,
        destination_latitude=payload.destination_latitude,
        destination_longitude=payload.destination_longitude,
        distance_km=distance_km,
        estimated_duration_min=duration_min,
        waypoints=waypoints,
        flood_risk_zones=flood_risk_zones,
        is_flood_safe=is_flood_safe,
        safety_score=safety_score,
        notes=payload.notes,
    )
    db.add(route)
    db.commit()
    db.refresh(route)
    return route
