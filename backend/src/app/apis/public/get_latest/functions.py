from pathlib import Path

from app.services import contract_loader

from .schemas import LatestContractResponse


def read_latest_contract(contract_dir: Path) -> LatestContractResponse:
    """有効なリリースポインターを読み取り、検証する。"""
    return LatestContractResponse(contract_loader.read_latest(contract_dir))
