"""FAILSAFE FastAPI application entrypoint."""
from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .database import Base, engine
from .inference import InferenceEngine, get_engine
from .routers import auth as auth_router
from .routers import predictions as pred_router
from .schemas import HealthResponse

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(name)s | %(message)s")
logger = logging.getLogger(__name__)

settings = get_settings()
app = FastAPI(
    title="FAILSAFE API",
    description=(
        "Backend for the FAILSAFE early-warning system: XGBoost risk "
        "scoring, SHAP explanations, and intervention generation."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)
    try:
        get_engine()
        logger.info("ML engine ready.")
    except FileNotFoundError as exc:
        logger.warning(
            "ML model not loaded yet (%s). The /api/predict* endpoints "
            "will fail until you run the training script.",
            exc,
        )


app.include_router(auth_router.router)
app.include_router(pred_router.router)


@app.get("/api/health", response_model=HealthResponse)
def health() -> HealthResponse:
    try:
        engine_obj: InferenceEngine = get_engine()
        return HealthResponse(
            status="ok",
            model_loaded=True,
            feature_count=len(engine_obj.feature_columns_transformed),
        )
    except FileNotFoundError:
        return HealthResponse(status="ok", model_loaded=False, feature_count=0)


@app.get("/")
def index() -> dict[str, str]:
    return {
        "name": "FAILSAFE API",
        "docs": "/docs",
        "health": "/api/health",
    }
