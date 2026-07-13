from fastapi import APIRouter

from app.apis import deps
from app.apis.public.common import ERROR_RESPONSES
from app.apis.public.get_release import functions as api_functions

from .contract import CONTRACT
from .schemas import ReleaseContractResponse

router = APIRouter()


@router.get(
    "/api/contracts/release/{release_id}",
    operation_id=CONTRACT.operation_id,
    summary=CONTRACT.summary,
    response_model=ReleaseContractResponse,
    responses={status: ERROR_RESPONSES[status] for status in CONTRACT.error_statuses},
)
async def get_release_contract(
    release_id: str, contract_dir: deps.ContractDirectory
) -> ReleaseContractResponse:
    return api_functions.read_release_contract(contract_dir, release_id)
