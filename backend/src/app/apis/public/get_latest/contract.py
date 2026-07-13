from app.apis.public.common import OperationContract

CONTRACT = OperationContract(
    operation_id="getLatestContract",
    documentation_slug="public/get-latest-contract",
    auth_mode="public",
    permissions=(),
    summary="有効な正規リリースポインターを取得する。",
    error_statuses=(404, 500),
    idempotency="安全な読み取り",
    transaction="none",
    external_effects="設定済み公開契約ディレクトリを読み取る",
)
