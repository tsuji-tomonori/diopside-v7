from typing import Any

from tools.app_docs import render_inventory


def test_inventory_is_sorted_and_documents_boundaries() -> None:
    operations: list[dict[str, Any]] = [
        {
            "operationId": "z",
            "slug": "z",
            "method": "GET",
            "path": "/z",
            "auth": "public",
            "permissions": [],
            "summary": "Z.",
            "success": 200,
            "errors": [404],
            "idempotency": "safe",
            "transaction": "none",
            "externalEffects": "read",
        },
        {
            "operationId": "a",
            "slug": "a",
            "method": "GET",
            "path": "/a",
            "auth": "public",
            "permissions": [],
            "summary": "A.",
            "success": 200,
            "errors": [404],
            "idempotency": "safe",
            "transaction": "none",
            "externalEffects": "read",
        },
    ]
    rendered = render_inventory(operations).decode()
    assert rendered.index("`a`") < rendered.index("`z`")
    assert rendered.index("| `z` |") < rendered.index("## Operation boundaries")
    assert "Permissions: none" in rendered
    assert "External effects: read" in rendered
