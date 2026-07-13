from fastapi import APIRouter

from app.apis import deps
from app.apis.public.common import ERROR_RESPONSES
from app.apis.public.get_search import functions as api_functions

from .contract import CONTRACT
from .schemas import SearchContractResponse

router = APIRouter()


@router.get(
    "/api/contracts/releases/{release_id}/search",
    operation_id=CONTRACT.operation_id,
    summary=CONTRACT.summary,
    response_model=SearchContractResponse,
    responses={status: ERROR_RESPONSES[status] for status in CONTRACT.error_statuses},
)
async def get_release_search_contract(
    release_id: str, contract_dir: deps.ContractDirectory
) -> SearchContractResponse:
    return api_functions.read_search_contract(contract_dir, release_id)
