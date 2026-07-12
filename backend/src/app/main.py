from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.core.config import get_settings
from app.services import contract_loader


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

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/api/contracts/latest")
    async def latest_contract() -> dict[str, object]:
        return contract_loader.read_latest(contract_dir)

    @app.get("/api/contracts/release/{release_id}")
    async def release_contract(release_id: str) -> dict[str, object]:
        return contract_loader.read_release(contract_dir, release_id)

    @app.get("/api/contracts/releases/{release_id}/search")
    async def release_search_contract(release_id: str) -> dict[str, object]:
        return contract_loader.read_search_index(contract_dir, release_id)

    @app.get("/api/contracts/releases/{release_id}/tags")
    async def release_tags_contract(release_id: str) -> dict[str, object]:
        return {
            "taxonomy": contract_loader.read_taxonomy(contract_dir, release_id),
            "index": contract_loader.read_tag_index(contract_dir, release_id),
            "alias": contract_loader.read_alias_index(contract_dir, release_id),
        }

    @app.get("/api/contracts/releases/{release_id}/videos/{video_id}")
    async def video_contract(release_id: str, video_id: str) -> JSONResponse:
        return JSONResponse(contract_loader.read_video(contract_dir, release_id, video_id))

    return app


app = create_app()
