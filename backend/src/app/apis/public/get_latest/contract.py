from app.apis.public.common import OperationContract

CONTRACT = OperationContract(
    operation_id="getLatestContract",
    documentation_slug="public/get-latest-contract",
    auth_mode="public",
    permissions=(),
    summary="Read the active canonical release pointer.",
    error_statuses=(404, 500),
    idempotency="safe read",
    transaction="none",
    external_effects="reads the configured public contract directory",
)
