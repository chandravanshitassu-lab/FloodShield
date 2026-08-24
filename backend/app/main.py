"""
FloodShield FastAPI Application Entry Point.

Bootstraps the app, configures middleware, registers all routers,
and wires up global exception handlers.

Start the server::

    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
"""
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from app.database.config import settings
from app.database.base import Base
from app.database.session import engine
from app.utils.exceptions import register_exception_handlers

# ── Import all models so Alembic / SQLAlchemy discover them ────────────────
import app.models  # noqa: F401

# ── Routers ─────────────────────────────────────────────────────────────────
from app.api import auth, businesses, inventory, risk, routes, warehouses, vehicles, action_plans, admin

# ── Logging ─────────────────────────────────────────────────────────────────
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

    # ── CORS ────────────────────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Trusted Hosts (production hardening) ────────────────────────────────
    if settings.ENVIRONMENT == "production":
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=["floodshield.in", "*.floodshield.in"],
        )

    # ── Exception Handlers ──────────────────────────────────────────────────
    register_exception_handlers(app)

    # ── Routers ─────────────────────────────────────────────────────────────
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

    # ── Lifecycle Events ────────────────────────────────────────────────────
    @app.on_event("startup")
    async def on_startup() -> None:
        logger.info("FloodShield API starting up (env=%s).", settings.ENVIRONMENT)
        # Create tables automatically in dev; use Alembic in production
        if settings.ENVIRONMENT in ("development", "testing"):
            Base.metadata.create_all(bind=engine)
            logger.info("Database tables created / verified.")

    @app.on_event("shutdown")
    async def on_shutdown() -> None:
        logger.info("FloodShield API shutting down.")

    # ── Health Check ─────────────────────────────────────────────────────────
    @app.get("/health", tags=["Health"], summary="Health check")
    async def health_check():
        """Returns 200 OK when the API is running."""
        return {
            "status": "healthy",
            "app": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "environment": settings.ENVIRONMENT,
        }

    return app


app = create_app()
