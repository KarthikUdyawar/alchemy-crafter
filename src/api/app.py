"""Phase 10 — FastAPI application factory."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.api.routes import router
from src.db.connection import init_db
from src.logger import setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Startup: init logging + DB. Shutdown: nothing needed."""
    setup_logging()
    init_db()
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="Alchemy Crafter API",
        description="Combine elements, discover new ones — powered by local LLM.",
        version="1.0.0",
        lifespan=lifespan,
    )
    app.include_router(router)
    return app


app = create_app()
