from __future__ import annotations

import argparse
import ast
import importlib
import json
import re
from pathlib import Path
from typing import Any, cast

from app.main import create_app

ROOT = Path(__file__).resolve().parents[2]
DOCS_ROOT = ROOT / "docs/api"
MANUAL = DOCS_ROOT / "public-contracts.manual.json"
INVENTORY = DOCS_ROOT / "public-contracts.gen.md"
OPENAPI = DOCS_ROOT / "openapi.gen.json"
REGISTRY = DOCS_ROOT / "generation-registry.gen.json"
DOCUMENT_KINDS = (
    "interface",
    "sequence",
    "detail-design",
    "test-factors",
    "examples",
)


def _manual_document() -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(MANUAL.read_text(encoding="utf-8")))


def _manual_operations(document: dict[str, Any]) -> list[dict[str, Any]]:
    operations = cast(list[dict[str, Any]], document["operations"])
    operation_ids = [str(operation["operationId"]) for operation in operations]
    if len(operation_ids) != len(set(operation_ids)):
        raise ValueError("manual contract contains duplicate operationId")
    return sorted(operations, key=lambda operation: str(operation["operationId"]))


def _runtime_openapi(operations: list[dict[str, Any]]) -> dict[str, Any]:
    schema = create_app().openapi()
    paths = cast(dict[str, Any], schema["paths"])
    runtime: dict[str, tuple[str, str]] = {}
    for path, path_item_value in paths.items():
        path_item = cast(dict[str, Any], path_item_value)
        for method, operation_value in path_item.items():
            operation_schema = cast(dict[str, Any], operation_value)
            operation_id = operation_schema.get("operationId")
            if isinstance(operation_id, str):
                runtime[operation_id] = (method.upper(), path)
    expected = {
        str(operation["operationId"]): (
            str(operation["method"]),
            str(operation["path"]),
        )
        for operation in operations
    }
    observed = {key: value for key, value in runtime.items() if key in expected}
    if observed != expected:
        raise ValueError(
            f"manual/runtime operation mismatch: expected={expected}, observed={observed}"
        )
    for operation in sorted(operations, key=lambda item: str(item["operationId"])):
        operation_schema = _operation_schema(schema, operation)
        responses = cast(dict[str, Any], operation_schema["responses"])
        observed_errors = {int(status) for status in responses if int(status) >= 400}
        expected_errors = set(cast(list[int], operation["errors"]))
        if observed_errors != expected_errors:
            raise ValueError(
                f"manual/runtime error mismatch for {operation['operationId']}: "
                f"expected={expected_errors}, observed={observed_errors}"
            )
    return schema


def _operation_schema(openapi: dict[str, Any], operation: dict[str, Any]) -> dict[str, Any]:
    paths = cast(dict[str, Any], openapi["paths"])
    path_item = cast(dict[str, Any], paths[str(operation["path"])])
    return cast(dict[str, Any], path_item[str(operation["method"]).lower()])


def _operation_output(operation_id: str, kind: str) -> Path:
    return DOCS_ROOT / "operations" / operation_id / f"{kind}.gen.md"


def _source_paths(operation: dict[str, Any]) -> dict[str, Path]:
    module_path = str(operation["module"]).replace(".", "/")
    base = ROOT / "src" / module_path
    return {
        name: base / f"{name}.py"
        for name in ("contract", "router", "functions", "schemas", "samples")
    }


def _sample(operation: dict[str, Any]) -> dict[str, Any]:
    module = importlib.import_module(f"{operation['module']}.samples")
    samples: list[dict[str, Any]] = []
    for name, value in vars(module).items():
        if name.endswith("_RESPONSE_SAMPLE") and isinstance(value, dict):
            samples.append(cast(dict[str, Any], value))
    if len(samples) != 1:
        raise ValueError(
            f"{operation['operationId']}: expected exactly one response sample, got {len(samples)}"
        )
    return samples[0]


def _loader_calls(operation: dict[str, Any]) -> list[str]:
    functions_path = _source_paths(operation)["functions"]
    tree = ast.parse(functions_path.read_text(encoding="utf-8"), filename=str(functions_path))
    calls: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
            continue
        owner = node.func.value
        if isinstance(owner, ast.Name) and owner.id == "contract_loader":
            calls.append(f"contract_loader.{node.func.attr}")
    if not calls:
        raise ValueError(f"{operation['operationId']}: no contract_loader call found")
    return calls


def _csv(values: object) -> str:
    return ", ".join(str(value) for value in cast(list[object], values)) or "none"


def _response_schema_name(operation_schema: dict[str, Any], status: int) -> str:
    responses = cast(dict[str, Any], operation_schema["responses"])
    response = cast(dict[str, Any], responses[str(status)])
    content = cast(dict[str, Any], response.get("content", {}))
    json_content = cast(dict[str, Any], content.get("application/json", {}))
    response_schema = cast(dict[str, Any], json_content.get("schema", {}))
    reference = response_schema.get("$ref")
    if isinstance(reference, str):
        return reference.rsplit("/", maxsplit=1)[-1]
    schema_type = response_schema.get("type")
    return str(schema_type) if schema_type is not None else "untyped"


def render_inventory(operations: list[dict[str, Any]]) -> bytes:
    """Render the API list and links to every per-operation document."""
    lines = [
        "# Public API documentation index (generated)",
        "",
        "> Generated from `public-contracts.manual.json` and runtime OpenAPI; do not edit.",
        "",
        "| Operation ID | Method | Path | Documents |",
        "| --- | --- | --- | --- |",
    ]
    for operation in sorted(operations, key=lambda item: str(item["operationId"])):
        operation_id = str(operation["operationId"])
        links = " · ".join(
            f"[{kind}](operations/{operation_id}/{kind}.gen.md)" for kind in DOCUMENT_KINDS
        )
        lines.append(
            f"| `{operation_id}` | {operation['method']} | `{operation['path']}` | {links} |"
        )
    lines.extend(
        [
            "",
            "## Aggregate artifacts",
            "",
            "- [OpenAPI](openapi.gen.json)",
            "- [Generation registry](generation-registry.gen.json)",
            "",
            f"Operation count: {len(operations)}",
            f"Per-operation document count: {len(operations) * len(DOCUMENT_KINDS)}",
        ]
    )
    return ("\n".join(lines) + "\n").encode()


def render_interface(operation: dict[str, Any], operation_schema: dict[str, Any]) -> bytes:
    parameters = cast(list[dict[str, Any]], operation_schema.get("parameters", []))
    responses = cast(dict[str, Any], operation_schema["responses"])
    lines = [
        f"# {operation['operationId']} interface (generated)",
        "",
        f"- Method: `{operation['method']}`",
        f"- Path: `{operation['path']}`",
        f"- Summary: {operation['summary']}",
        f"- Authentication: {operation['auth']}",
        f"- Permissions: {_csv(operation['permissions'])}",
        "- Security requirement: "
        f"{'declared' if operation_schema.get('security') else 'none (public read)'}",
        "",
        "## Parameters",
        "",
        "| Name | In | Required | Schema |",
        "| --- | --- | --- | --- |",
    ]
    if parameters:
        for parameter in parameters:
            parameter_schema = cast(dict[str, Any], parameter.get("schema", {}))
            schema_name = parameter_schema.get("type", parameter_schema.get("$ref", "unknown"))
            lines.append(
                f"| `{parameter['name']}` | {parameter['in']} | "
                f"{str(parameter.get('required', False)).lower()} | `{schema_name}` |"
            )
    else:
        lines.append("| — | — | — | — |")
    lines.extend(
        [
            "",
            "## Responses",
            "",
            "| Status | Description | Schema |",
            "| ---: | --- | --- |",
        ]
    )
    for status, response_value in sorted(responses.items(), key=lambda item: int(item[0])):
        response = cast(dict[str, Any], response_value)
        content = cast(dict[str, Any], response.get("content", {}))
        json_content = cast(dict[str, Any], content.get("application/json", {}))
        response_schema = cast(dict[str, Any], json_content.get("schema", {}))
        schema_name = response_schema.get("$ref", response_schema.get("type", "none"))
        lines.append(f"| {status} | {response['description']} | `{schema_name}` |")
    lines.extend(
        [
            "",
            "## Traceability",
            "",
            f"- Requirements: {_csv(operation['requirements'])}",
            f"- Specifications: {_csv(operation['specifications'])}",
            f"- Acceptance: {_csv(operation['acceptance'])}",
        ]
    )
    return ("\n".join(lines) + "\n").encode()


def render_sequence(operation: dict[str, Any], operation_schema: dict[str, Any]) -> bytes:
    loader_calls = _loader_calls(operation)
    function_name = str(operation["function"])
    response_model = _response_schema_name(operation_schema, int(operation["success"]))
    lines = [
        f"# {operation['operationId']} sequence (generated)",
        "",
        "```mermaid",
        "sequenceDiagram",
        "    actor Client",
        "    participant Router",
        "    participant Functions",
        "    participant Loader as Contract loader",
        "    participant Storage as Public contract directory",
        f"    Client->>Router: {operation['method']} {operation['path']}",
        "    Router->>Router: Resolve typed contract directory dependency",
        f"    Router->>Functions: {function_name}(...) ",
    ]
    for loader_call in loader_calls:
        lines.extend(
            [
                f"    Functions->>Loader: {loader_call}(...) ",
                "    Loader->>Storage: Read and parse canonical JSON",
                "    Storage-->>Loader: JSON bytes or missing file",
                "    Loader-->>Functions: Validated payload or classified HTTP error",
            ]
        )
    lines.extend(
        [
            f"    Functions-->>Router: typed {response_model} response",
            f"    Router-->>Client: {operation['success']} JSON",
            "```",
            "",
            "## Error sequence",
            "",
            "- Missing artifact is classified as 404 by the contract loader.",
            "- Invalid stored JSON or a path/payload invariant failure is classified as 500.",
            "- Framework path validation is classified as 422 where applicable.",
            "- The router catches no broad exception; classified errors propagate through FastAPI.",
        ]
    )
    return ("\n".join(lines) + "\n").encode()


def render_detail_design(operation: dict[str, Any]) -> bytes:
    paths = _source_paths(operation)
    loader_calls = _loader_calls(operation)
    lines = [
        f"# {operation['operationId']} detail design (generated)",
        "",
        f"- Stable contract slug: `{operation['slug']}`",
        f"- Business function: `{operation['function']}`",
        f"- Authentication: {operation['auth']}",
        f"- Permissions: {_csv(operation['permissions'])}",
        f"- Idempotency: {operation['idempotency']}",
        f"- Transaction boundary: {operation['transaction']}",
        f"- External effects: {operation['externalEffects']}",
        "",
        "## Source ownership",
        "",
        "| Concern | Source |",
        "| --- | --- |",
    ]
    for concern, path in paths.items():
        lines.append(f"| {concern} | `{path.relative_to(ROOT)}` |")
    lines.extend(
        [
            "",
            "## Resource boundaries",
            "",
            f"- Contract-loader calls: {', '.join(f'`{call}`' for call in loader_calls)}",
            "- Database/SQL: not applicable; this operation reads versioned filesystem artifacts.",
            "- Provider SDK: not applicable; the operation layer imports no provider adapter.",
            "- Mutation/rollback: not applicable; this is a safe read with no transaction.",
            "",
            "## Compatibility",
            "",
            f"- Operation identity `{operation['operationId']}` and path "
            f"`{operation['path']}` are stable.",
            "- Response payload validation remains owned by canonical public contract models.",
            "- Non-backward-compatible public schema changes require a major "
            "schema/path migration.",
        ]
    )
    return ("\n".join(lines) + "\n").encode()


def render_test_factors(operation: dict[str, Any]) -> bytes:
    path_parameters = re.findall(r"{([^}:]+)(?::[^}]+)?}", str(operation["path"]))
    lines = [
        f"# {operation['operationId']} test factors (generated)",
        "",
        "| ID | Type | Input/condition | Expected |",
        "| --- | --- | --- | --- |",
        f"| TF-001 | normal | Existing canonical artifact | {operation['success']} "
        "and response schema match |",
        "| TF-002 | missing-data | Artifact path does not exist | 404 without fallback data |",
        "| TF-003 | invalid-data | Stored JSON is malformed or violates its "
        "canonical model | 500 without private content exposure |",
        "| TF-004 | compatibility | Stable method/path/operationId are compared "
        "with manual contract | Generation fails on drift |",
        "| TF-005 | security | Public read without credentials | No authentication "
        "requirement or provider credential exposure |",
    ]
    if path_parameters:
        lines.append(
            f"| TF-006 | boundary/validation | Invalid {', '.join(path_parameters)} path value | "
            "Declared 422 when framework validation applies; otherwise 404; "
            "traversal cannot escape contract root |"
        )
    lines.extend(
        [
            "",
            "## Required assertions",
            "",
            f"- Declared error statuses: {_csv(operation['errors'])}.",
            "- Missing optional values remain missing; no fabricated zero, date, "
            "count, or metadata.",
            "- Repeated reads are byte/semantic stable for the same release artifact.",
            "- Generated interface and runtime OpenAPI have the same method, path, "
            "operation ID, and errors.",
        ]
    )
    return ("\n".join(lines) + "\n").encode()


def render_examples(operation: dict[str, Any]) -> bytes:
    sample = _sample(operation)
    lines = [
        f"# {operation['operationId']} examples (generated)",
        "",
        f"Source: `src/{str(operation['module']).replace('.', '/')}/samples.py`",
        "",
        "## Success response",
        "",
        "```json",
        json.dumps(sample, ensure_ascii=False, indent=2, sort_keys=True),
        "```",
        "",
        "Error payloads use FastAPI's classified HTTP error response; no demo "
        "fallback is generated.",
    ]
    return ("\n".join(lines) + "\n").encode()


def _render_operation_documents(
    operation: dict[str, Any], openapi: dict[str, Any]
) -> dict[Path, bytes]:
    operation_id = str(operation["operationId"])
    return {
        _operation_output(operation_id, "interface"): render_interface(
            operation, _operation_schema(openapi, operation)
        ),
        _operation_output(operation_id, "sequence"): render_sequence(
            operation, _operation_schema(openapi, operation)
        ),
        _operation_output(operation_id, "detail-design"): render_detail_design(operation),
        _operation_output(operation_id, "test-factors"): render_test_factors(operation),
        _operation_output(operation_id, "examples"): render_examples(operation),
    }


def build_outputs() -> dict[Path, bytes]:
    """Build every deterministic output in dependency order without writing."""
    document = _manual_document()
    operations = _manual_operations(document)
    openapi = _runtime_openapi(operations)
    outputs: dict[Path, bytes] = {
        INVENTORY: render_inventory(operations),
        OPENAPI: (
            json.dumps(openapi, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        ).encode(),
    }
    for operation in operations:
        outputs.update(_render_operation_documents(operation, openapi))
    owned_paths = sorted([str(path.relative_to(ROOT)) for path in (*outputs.keys(), REGISTRY)])
    registry = {
        "generator": "app-docs generate",
        "checkCommand": "app-docs generate --check",
        "inputs": [
            "docs/api/public-contracts.manual.json",
            "src/app/apis/public/*/{contract,router,functions,schemas,samples}.py",
            "runtime FastAPI OpenAPI",
        ],
        "outputs": owned_paths,
        "operationCount": len(operations),
        "perOperationDocumentKinds": list(DOCUMENT_KINDS),
        "ciSafe": True,
    }
    outputs[REGISTRY] = (
        json.dumps(registry, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode()
    return outputs


def generate(*, check: bool) -> None:
    outputs = build_outputs()
    expected_paths = set(outputs)
    existing_generated = set(DOCS_ROOT.rglob("*.gen.*"))
    stale = [
        str(path.relative_to(ROOT))
        for path, intended in outputs.items()
        if not path.exists() or path.read_bytes() != intended
    ]
    stale.extend(
        str(path.relative_to(ROOT)) for path in sorted(existing_generated - expected_paths)
    )
    if check:
        if stale:
            raise SystemExit(f"generated documentation is stale: {', '.join(stale)}")
        print(f"documentation is current: {len(outputs)} files")
        return
    for path, intended in sorted(outputs.items(), key=lambda item: str(item[0])):
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(path.suffix + ".tmp")
        temporary.write_bytes(intended)
        temporary.replace(path)
    print(f"documentation generated: {len(outputs)} files")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["generate"])
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    generate(check=bool(args.check))


if __name__ == "__main__":
    main()
