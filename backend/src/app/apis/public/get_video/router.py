from fastapi import APIRouter

from app.apis import deps
from app.apis.public.common import ERROR_RESPONSES
from app.apis.public.get_video import functions as api_functions

from .contract import CONTRACT
from .schemas import VideoContractResponse

router = APIRouter()


@router.get(
    "/api/contracts/releases/{release_id}/videos/{video_id}",
    operation_id=CONTRACT.operation_id,
    summary=CONTRACT.summary,
    response_model=VideoContractResponse,
    responses={status: ERROR_RESPONSES[status] for status in CONTRACT.error_statuses},
)
async def get_release_video_contract(
    release_id: str, video_id: str, contract_dir: deps.ContractDirectory
) -> VideoContractResponse:
    return api_functions.read_video_contract(contract_dir, release_id, video_id)
