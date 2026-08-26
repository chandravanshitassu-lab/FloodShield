"""
FloodShield FastAPI Application Entry Point.

Bootstraps the app, configures middleware, registers all routers,
and wires up global exception handlers.

Start the server::

    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
"""

import logging

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from app.database.config import settings
from app.database.base import Base
from app.database.session import engine
from app.utils.exceptions import register_exception_handlers

# Import all models so Alembic / SQLAlchemy discover them
import app.models  # noqa: F401

# Routers
from app.api import (
    auth,
    businesses,
    inventory,
    risk,
    routes,
    warehouses,
    vehicles,
    action_plans,
    admin,
)

# AI/ML schemas
from app.schemas import (
    FloodRiskPredictionRequest,
    FloodRiskPredictionResponse,
    HealthResponse,
    InventoryPrioritizeResponse,
)

# AI/ML services
from app.services.model_service import FloodRiskModelService

from app.services.inventory_service import (
    load_inventory,
    get_inventory_summary,
    prioritize_inventory,
    normalize_flood_risk_level,
)


# ── Logging ──────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

logger = logging.getLogger(__name__)


# ── Application Factory ──────────────────────────────────────────────────────

def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""

    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description=(
            "## FloodShield API\n\n"
            "Smart India Hackathon — Backend REST API for flood risk assessment, "
            "business inventory management, evacuation routing, and contingency planning.\n\n"
            "### Authentication\n"
            "Use `POST /api/auth/login` to obtain a JWT. "
            "Pass it as `Authorization: Bearer <token>` on all protected endpoints."
        ),
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        contact={
            "name": "FloodShield Team",
            "email": "team@floodshield.in",
        },
        license_info={"name": "MIT"},
    )

    # ── CORS ─────────────────────────────────────────────────────────────────

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Trusted Hosts ────────────────────────────────────────────────────────

    if settings.ENVIRONMENT == "production":
        app.add_middleware(
            TrustedHostMiddleware,
       allowed_hosts=[
            "floodshield-backend.onrender.com",
            "floodshield.in",
            "www.floodshield.in",
            "*.floodshield.in",
            "localhost",
            "127.0.0.1", 
        ],
        )

    # ── Exception Handlers ───────────────────────────────────────────────────

    register_exception_handlers(app)

    # ── Routers ───────────────────────────────────────────────────────────────

    API_PREFIX = "/api"

    app.include_router(auth.router, prefix=API_PREFIX)
    app.include_router(businesses.router, prefix=API_PREFIX)
    app.include_router(inventory.router, prefix=API_PREFIX)
    app.include_router(risk.router, prefix=API_PREFIX)
    app.include_router(routes.router, prefix=API_PREFIX)
    app.include_router(warehouses.router, prefix=API_PREFIX)
    app.include_router(vehicles.router, prefix=API_PREFIX)
    app.include_router(action_plans.router, prefix=API_PREFIX)
    app.include_router(admin.router, prefix=API_PREFIX)

    # ── Lifecycle Events ──────────────────────────────────────────────────────

    @app.on_event("startup")
    async def on_startup() -> None:
        logger.info(
            "FloodShield API starting up (env=%s).",
            settings.ENVIRONMENT,
        )

        if settings.ENVIRONMENT in ("development", "testing"):
            Base.metadata.create_all(bind=engine)
            logger.info("Database tables created / verified.")

        # Initialize AI/ML model
        try:
            model_service = FloodRiskModelService.get_instance()

            logger.info(
                "Model service initialized with classes: %s",
                model_service.classes,
            )

        except Exception as exc:
            logger.error(
                "Failed to load FloodShield model on startup: %s",
                exc,
            )

    @app.on_event("shutdown")
    async def on_shutdown() -> None:
        logger.info("FloodShield API shutting down.")

    # ── Health Check ──────────────────────────────────────────────────────────

    @app.get(
        "/health",
        response_model=HealthResponse,
        summary="Health check and model status",
        tags=["System"],
    )
    def health_check() -> HealthResponse:

        try:
            model_service = FloodRiskModelService.get_instance()

            is_ready = model_service.is_loaded

            return HealthResponse(
                status="healthy" if is_ready else "degraded",
                model_loaded=is_ready,
                model_classes=(
                    model_service.classes
                    if is_ready
                    else []
                ),
                message=(
                    "FloodShield API is operational and "
                    "ML model pipeline is loaded."
                    if is_ready
                    else
                    "FloodShield API is running but "
                    "model pipeline is not loaded."
                ),
            )

        except Exception as exc:

            logger.error(
                "Health check encountered error: %s",
                exc,
            )

            return HealthResponse(
                status="unhealthy",
                model_loaded=False,
                model_classes=[],
                message=f"Health check error: {str(exc)}",
            )

    # ── Flood Risk Prediction ─────────────────────────────────────────────────

    @app.post(
        "/predict",
        response_model=FloodRiskPredictionResponse,
        summary="Predict district flood risk level",
        tags=["Inference"],
    )
    def predict_flood_risk(
        request: FloodRiskPredictionRequest,
    ) -> FloodRiskPredictionResponse:

        try:

            model_service = FloodRiskModelService.get_instance()

            if not model_service.is_loaded:

                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=(
                        "Flood risk classification model "
                        "is not loaded."
                    ),
                )

            input_data = request.model_dump()

            prediction_result = model_service.predict(
                input_data
            )

            risk_level = prediction_result[
                "flood_risk_level"
            ]

            confidence = prediction_result[
                "confidence"
            ]

            probabilities = prediction_result[
                "probabilities"
            ]

            district_display = (
                request.district_name
                or "Specified District"
            )

            state_display = (
                f", {request.state}"
                if request.state
                and request.state != "Unknown"
                else ""
            )

            summary_text = (
                f"{district_display}{state_display} "
                f"is classified as '{risk_level}' "
                f"flood risk with "
                f"{round(confidence * 100, 1)}% confidence."
            )

            return FloodRiskPredictionResponse(
                district_name=request.district_name,
                state=request.state,
                flood_risk_level=risk_level,
                confidence=confidence,
                probabilities=probabilities,
                summary=summary_text,
            )

        except HTTPException:
            raise

        except Exception as exc:

            logger.exception(
                "Inference failed for input: %s",
                request,
            )

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Inference error: {str(exc)}",
            )

    # ── Get Inventory ─────────────────────────────────────────────────────────

    @app.get(
        "/inventory",
        summary="Get inventory",
        tags=["Inventory"],
    )
    def get_inventory():

        try:

            df = load_inventory()

            return df.to_dict(
                orient="records"
            )

        except Exception as exc:

            logger.exception(
                "Failed to load inventory"
            )

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Inventory loading error: {str(exc)}",
            )

    # ── Inventory Summary ─────────────────────────────────────────────────────

    @app.get(
        "/inventory/summary",
        summary="Get inventory summary",
        tags=["Inventory"],
    )
    def inventory_summary():

        try:

            return get_inventory_summary()

        except Exception as exc:

            logger.exception(
                "Failed to generate inventory summary"
            )

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Inventory summary error: {str(exc)}",
            )

    # ── Inventory Prioritization ──────────────────────────────────────────────

    @app.post(
        "/inventory/prioritize",
        response_model=InventoryPrioritizeResponse,
        summary="Prioritize inventory based on flood risk",
        tags=["Inventory"],
    )
    def inventory_prioritize(
        flood_risk_level: str,
    ):

        try:

            flood_risk_level = normalize_flood_risk_level(
                flood_risk_level
            )

            products = prioritize_inventory(
                flood_risk_level
            )

            return {
                "flood_risk_level": flood_risk_level,
                "scoring_type": (
                    "Explainable inventory heuristic: "
                    "value, quantity, category vulnerability, "
                    "and flood risk x vulnerability exposure"
                ),
                "products": products,
            }

        except HTTPException:
            raise

        except ValueError as exc:

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(exc),
            )

        except Exception as exc:

            logger.exception(
                "Failed to prioritize inventory"
            )

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=(
                    f"Inventory prioritization error: "
                    f"{str(exc)}"
                ),
            )

    # ── Root Endpoint ─────────────────────────────────────────────────────────

    @app.get(
        "/",
        summary="FloodShield API",
        tags=["System"],
    )
    def root():

        return {
            "project": "FloodShield",
            "status": "running",
            "message": (
                "FloodShield API is running successfully."
            ),
            "docs": "/docs",
        }

    return app


# ── Application Instance ─────────────────────────────────────────────────────

app = create_app()