from fastapi import APIRouter

from app.apis import deps
from app.apis.public.common import ERROR_RESPONSES
from app.apis.public.get_latest import functions as api_functions

from .contract import CONTRACT
from .schemas import LatestContractResponse

router = APIRouter()


@router.get(
    "/api/contracts/latest",
    operation_id=CONTRACT.operation_id,
    summary=CONTRACT.summary,
    response_model=LatestContractResponse,
    responses={status: ERROR_RESPONSES[status] for status in CONTRACT.error_statuses},
)
async def get_latest_contract(
    contract_dir: deps.ContractDirectory,
) -> LatestContractResponse:
    return api_functions.read_latest_contract(contract_dir)
