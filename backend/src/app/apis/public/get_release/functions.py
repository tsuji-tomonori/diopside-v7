from pathlib import Path

from app.services import contract_loader

from .schemas import ReleaseContractResponse


def read_release_contract(contract_dir: Path, release_id: str) -> ReleaseContractResponse:
    """Read and validate a release index."""
    return ReleaseContractResponse(contract_loader.read_release(contract_dir, release_id))
