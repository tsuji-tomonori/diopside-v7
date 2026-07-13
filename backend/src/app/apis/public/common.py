from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class OperationContract:
    operation_id: str
    documentation_slug: str
    auth_mode: str
    permissions: tuple[str, ...]
    summary: str
    error_statuses: tuple[int, ...]
    idempotency: str
    transaction: str
    external_effects: str


ERROR_RESPONSES: dict[int, dict[str, str]] = {
    404: {"description": "要求された正規契約成果物が見つからない。"},
    422: {"description": "パスパラメーターの検証に失敗した。"},
    500: {"description": "保存済みの正規契約が不正または不整合である。"},
}
