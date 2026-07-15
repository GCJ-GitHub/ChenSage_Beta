"""FastAPI entrypoint for model-svc."""

from fastapi import FastAPI

from .api.health import router as health_router
from .api.internal import router as internal_router


def create_app() -> FastAPI:
    app = FastAPI(title="ChenSage model-svc", version="0.1.0")
    app.include_router(health_router)
    app.include_router(internal_router)
    return app


app = create_app()
