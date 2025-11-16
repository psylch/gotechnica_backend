from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api import api_router
from src.config import get_settings
from src.models.response import HealthResponse
from src.utils.errors import register_exception_handlers
from src.utils.logger import get_logger


def create_app() -> FastAPI:
    settings = get_settings()
    logger = get_logger(__name__)

    app = FastAPI(
        title="Snapopedia API",
        description="Backend service for card generation pipeline",
        version="0.1.0",
        debug=settings.debug,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_exception_handlers(app)
    app.include_router(api_router)

    @app.get("/health", response_model=HealthResponse, tags=["system"])
    async def health_check() -> HealthResponse:
        logger.debug("Health check requested")
        return HealthResponse(data={"status": "healthy"})

    return app


app = create_app()
