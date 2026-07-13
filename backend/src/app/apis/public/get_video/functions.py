from pathlib import Path

from app.services import contract_loader

from .schemas import VideoContractResponse


def read_video_contract(
    contract_dir: Path, release_id: str, video_id: str
) -> VideoContractResponse:
    """Read one public video detail."""
    return VideoContractResponse(contract_loader.read_video(contract_dir, release_id, video_id))
