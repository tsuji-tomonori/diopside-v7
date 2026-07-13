from typing import Any

from tools.app_docs import DOCUMENT_KINDS, ROOT, build_outputs, render_inventory


def test_inventory_is_sorted_and_documents_boundaries() -> None:
    operations: list[dict[str, Any]] = [
        {
            "operationId": "z",
            "slug": "z",
            "module": "app.apis.public.get_latest",
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
            "module": "app.apis.public.get_latest",
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
    assert "operations/a/interface.gen.md" in rendered
    assert "Operation count: 2" in rendered
    assert "Per-operation document count: 10" in rendered


def test_build_outputs_generates_every_document_for_every_operation() -> None:
    outputs = build_outputs()
    relative_paths = {str(path.relative_to(ROOT)) for path in outputs}
    operation_ids = {
        "getLatestContract",
        "getReleaseContract",
        "getReleaseSearchContract",
        "getReleaseTagsContract",
        "getReleaseVideoContract",
    }
    for operation_id in operation_ids:
        for kind in DOCUMENT_KINDS:
            path = f"docs/api/operations/{operation_id}/{kind}.gen.md"
            assert path in relative_paths
            assert operation_id.encode() in outputs[ROOT / path]
    assert len(outputs) == 28
    assert b"404" in outputs[ROOT / "docs/api/operations/getLatestContract/interface.gen.md"]
    assert (
        b"contract_loader.read_taxonomy"
        in outputs[ROOT / "docs/api/operations/getReleaseTagsContract/sequence.gen.md"]
    )
