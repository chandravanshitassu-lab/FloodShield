"""
FloodShield - FastAPI Application
=================================
REST API for FloodShield.

Endpoints:
- GET  /health
- POST /predict
- GET  /inventory
- GET  /inventory/summary
- POST /inventory/prioritize
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from schemas import (
    FloodRiskPredictionRequest,
    FloodRiskPredictionResponse,
    HealthResponse,
    InventoryPrioritizeResponse,
)

from services.model_service import FloodRiskModelService

from services.inventory_service import (
    load_inventory,
    get_inventory_summary,
    prioritize_inventory,
    normalize_flood_risk_level,
)


# ============================================================
# LOGGING
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger("FloodShield.API")


# ============================================================
# APPLICATION LIFESPAN
# ============================================================

@asynccontextmanager
async def lifespan(app: FastAPI):

    logger.info("Initializing FloodShield FastAPI application...")

    try:
        model_service = FloodRiskModelService.get_instance()

        logger.info(
            f"Model service initialized with classes: "
            f"{model_service.classes}"
        )

    except Exception as exc:

        logger.error(
            f"Failed to load FloodShield model on startup: {exc}"
        )

    yield

    logger.info(
        "Shutting down FloodShield FastAPI application..."
    )


# ============================================================
# FASTAPI APPLICATION
# ============================================================

app = FastAPI(
    title="FloodShield Flood Risk Classification API",
    description=(
        "MVP API for FloodShield district-level flood risk "
        "classification and inventory prioritization."
    ),
    version="1.0.0",
    lifespan=lifespan,
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# HEALTH CHECK
# ============================================================

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
            f"Health check encountered error: {exc}"
        )

        return HealthResponse(
            status="unhealthy",
            model_loaded=False,
            model_classes=[],
            message=f"Health check error: {str(exc)}",
        )


# ============================================================
# FLOOD RISK PREDICTION
# ============================================================

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

        # Convert Pydantic request to dictionary
        input_data = request.model_dump()

        # Run ML prediction
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
            f"Inference failed for input: {request}"
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Inference error: {str(exc)}",
        )


# ============================================================
# GET INVENTORY
# ============================================================

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


# ============================================================
# INVENTORY SUMMARY
# ============================================================

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


# ============================================================
# INVENTORY PRIORITIZATION
# ============================================================

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


# ============================================================
# ROOT ENDPOINT
# ============================================================

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
