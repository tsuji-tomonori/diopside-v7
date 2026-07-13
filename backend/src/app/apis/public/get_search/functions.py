from pathlib import Path

from app.services import contract_loader

from .schemas import SearchContractResponse


def read_search_contract(contract_dir: Path, release_id: str) -> SearchContractResponse:
    """Read a release search index."""
    return SearchContractResponse(contract_loader.read_search_index(contract_dir, release_id))
