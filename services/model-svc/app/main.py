"""FastAPI entrypoint for model-svc."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.health import router as health_router
from .api.internal import router as internal_router
from .api.providers import router as providers_router
from .services.provider_store import ModelProviderStore


def create_app() -> FastAPI:
    app = FastAPI(title="ChenSage model-svc", version="0.1.0")
    app.state.provider_store = ModelProviderStore()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(health_router)
    app.include_router(internal_router)
    app.include_router(providers_router)
    return app


app = create_app()
