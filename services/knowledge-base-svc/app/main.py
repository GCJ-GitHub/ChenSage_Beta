"""FastAPI entrypoint for knowledge-base-svc."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.health import router as health_router
from .api.knowledge import router as knowledge_router
from .services.knowledge_store import KnowledgeStore


def create_app() -> FastAPI:
    app = FastAPI(title="ChenSage knowledge-base-svc", version="0.1.0")
    app.state.knowledge_store = KnowledgeStore()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(health_router)
    app.include_router(knowledge_router)
    return app


app = create_app()
