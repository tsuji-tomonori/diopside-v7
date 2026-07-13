from pathlib import Path

from app.services import contract_loader

from .schemas import TagsContractResponse


def read_tags_contract(contract_dir: Path, release_id: str) -> TagsContractResponse:
    """Read all public tag projections for a release."""
    return TagsContractResponse(
        taxonomy=contract_loader.read_taxonomy(contract_dir, release_id),
        index=contract_loader.read_tag_index(contract_dir, release_id),
        alias=contract_loader.read_alias_index(contract_dir, release_id),
    )
