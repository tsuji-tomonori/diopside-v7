from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.apis.public.get_latest.router import router as get_latest_router
from app.apis.public.get_release.router import router as get_release_router
from app.apis.public.get_search.router import router as get_search_router
from app.apis.public.get_tags.router import router as get_tags_router
from app.apis.public.get_video.router import router as get_video_router
from app.core.config import get_settings


async def health() -> dict[str, str]:
    """Return process readiness without constructing provider clients."""
    return {"status": "ok"}


def create_app() -> FastAPI:
    settings = get_settings()
    contract_dir = settings.contract_dir

    app = FastAPI(title=settings.app_name, version=settings.app_version, debug=settings.debug)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.cors_origins),
        allow_credentials=False,
        allow_methods=["GET"],
        allow_headers=["Accept", "Content-Type"],
    )

    app.mount(
        "/data",
        StaticFiles(directory=str(contract_dir), html=False),
        name="public-data",
    )

    app.add_api_route("/health", health, methods=["GET"], tags=["system"])
    app.include_router(get_latest_router)
    app.include_router(get_release_router)
    app.include_router(get_search_router)
    app.include_router(get_tags_router)
    app.include_router(get_video_router)

    return app


app = create_app()
