"""FastAPI entrypoint for agent-svc."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.health import router as health_router
from .api.internal import router as internal_router
from .api.prompts import router as prompts_router
from .services.prompt_registry import PromptRegistry


def create_app() -> FastAPI:
    app = FastAPI(title="ChenSage agent-svc", version="0.1.0")
    app.state.prompt_registry = PromptRegistry()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(health_router)
    app.include_router(internal_router)
    app.include_router(prompts_router)
    return app


app = create_app()
