from fastapi import APIRouter

from app.apis import deps
from app.apis.public.common import ERROR_RESPONSES
from app.apis.public.get_tags import functions as api_functions

from .contract import CONTRACT
from .schemas import TagsContractResponse

router = APIRouter()


@router.get(
    "/api/contracts/releases/{release_id}/tags",
    operation_id=CONTRACT.operation_id,
    summary=CONTRACT.summary,
    response_model=TagsContractResponse,
    responses={status: ERROR_RESPONSES[status] for status in CONTRACT.error_statuses},
)
async def get_release_tags_contract(
    release_id: str, contract_dir: deps.ContractDirectory
) -> TagsContractResponse:
    return api_functions.read_tags_contract(contract_dir, release_id)
