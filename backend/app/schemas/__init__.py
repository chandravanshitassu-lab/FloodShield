"""FloodShield schemas — re-export all public schemas."""

# Core backend schemas
from app.schemas.action_plan import *  # noqa: F401, F403
from app.schemas.business import *     # noqa: F401, F403
from app.schemas.inventory import *    # noqa: F401, F403
from app.schemas.risk import *         # noqa: F401, F403
from app.schemas.route import *        # noqa: F401, F403
from app.schemas.user import *         # noqa: F401, F403
from app.schemas.vehicle import *      # noqa: F401, F403
from app.schemas.warehouse import *    # noqa: F401, F403

# ML / AI schemas (Member 3)
from app.schemas.ml_schemas import (
    FloodRiskPredictionRequest,
    FloodRiskPredictionResponse,
    HealthResponse,
    InventoryPrioritizeResponse,
)

__all__ = [
    "FloodRiskPredictionRequest",
    "FloodRiskPredictionResponse",
    "HealthResponse",
    "InventoryPrioritizeResponse",
]
