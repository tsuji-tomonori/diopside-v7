from pathlib import Path

from app.services import contract_loader

from .schemas import VideoContractResponse


def read_video_contract(
    contract_dir: Path, release_id: str, video_id: str
) -> VideoContractResponse:
    """公開動画の詳細を1件読み取る。"""
    return VideoContractResponse(contract_loader.read_video(contract_dir, release_id, video_id))
