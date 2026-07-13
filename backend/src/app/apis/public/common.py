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
    404: {"description": "The requested canonical contract artifact was not found."},
    422: {"description": "A path parameter failed validation."},
    500: {"description": "The stored canonical contract is invalid or inconsistent."},
}
