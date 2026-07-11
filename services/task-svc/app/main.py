"""FastAPI entrypoint for task-svc.

The service is the single source of truth for task state.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.health import router as health_router
from .api.tasks import router as tasks_router


def create_app() -> FastAPI:
    app = FastAPI(title="ChenSage task-svc", version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(health_router)
    app.include_router(tasks_router)
    return app


app = create_app()
