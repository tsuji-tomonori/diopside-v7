from pathlib import Path

from app.services import contract_loader

from .schemas import LatestContractResponse


def read_latest_contract(contract_dir: Path) -> LatestContractResponse:
    """Read and validate the active release pointer."""
    return LatestContractResponse(contract_loader.read_latest(contract_dir))
