from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, cast

from app.main import create_app

ROOT = Path(__file__).resolve().parents[2]
MANUAL = ROOT / "docs/api/public-contracts.manual.json"
INVENTORY = ROOT / "docs/api/public-contracts.gen.md"
OPENAPI = ROOT / "docs/api/openapi.gen.json"


def _manual_operations() -> list[dict[str, Any]]:
    document = cast(dict[str, Any], json.loads(MANUAL.read_text(encoding="utf-8")))
    return cast(list[dict[str, Any]], document["operations"])


def render_inventory(operations: list[dict[str, Any]]) -> bytes:
    """Render stable human-readable API inventory bytes."""
    lines = [
        "# Public API inventory (generated)",
        "",
        "> Generated from `public-contracts.manual.json`; do not edit manually.",
        "",
        "| Operation ID | Method | Path | Auth | Success | Errors | Summary |",
        "| --- | --- | --- | --- | ---: | --- | --- |",
    ]
    for operation in sorted(operations, key=lambda item: str(item["operationId"])):
        errors = ", ".join(str(value) for value in cast(list[int], operation["errors"]))
        lines.append(
            f"| `{operation['operationId']}` | {operation['method']} "
            f"| `{operation['path']}` | {operation['auth']} | {operation['success']} "
            f"| {errors} | {operation['summary']} |"
        )
    lines.extend(["", "## Operation boundaries"])
    for operation in sorted(operations, key=lambda item: str(item["operationId"])):
        lines.extend(
            [
                "",
                f"### `{operation['operationId']}`",
                "",
                f"- Contract: `{operation['slug']}`",
                f"- Permissions: {', '.join(cast(list[str], operation['permissions'])) or 'none'}",
                f"- Idempotency: {operation['idempotency']}",
                f"- Transaction: {operation['transaction']}",
                f"- External effects: {operation['externalEffects']}",
            ]
        )
    return ("\n".join(lines) + "\n").encode()


def render_openapi(operations: list[dict[str, Any]]) -> bytes:
    """Render OpenAPI only after manual and runtime identities agree."""
    schema = create_app().openapi()
    runtime = {
        value[method]["operationId"]: (method.upper(), path)
        for path, value in schema["paths"].items()
        for method in value
        if method != "parameters" and "operationId" in value[method]
    }
    expected = {
        str(item["operationId"]): (str(item["method"]), str(item["path"])) for item in operations
    }
    observed = {key: value for key, value in runtime.items() if key in expected}
    if observed != expected:
        raise ValueError(
            f"manual/runtime operation mismatch: expected={expected}, observed={observed}"
        )
    for operation in operations:
        runtime_operation = schema["paths"][operation["path"]][operation["method"].lower()]
        observed_errors = {
            int(status) for status in runtime_operation["responses"] if int(status) >= 400
        }
        expected_errors = set(cast(list[int], operation["errors"]))
        if observed_errors != expected_errors:
            raise ValueError(
                f"manual/runtime error mismatch for {operation['operationId']}: "
                f"expected={expected_errors}, observed={observed_errors}"
            )
    return (json.dumps(schema, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode()


def generate(*, check: bool) -> None:
    operations = _manual_operations()
    outputs = {INVENTORY: render_inventory(operations), OPENAPI: render_openapi(operations)}
    stale: list[str] = []
    for path, intended in outputs.items():
        if check:
            if not path.exists() or path.read_bytes() != intended:
                stale.append(str(path.relative_to(ROOT)))
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            temporary = path.with_suffix(path.suffix + ".tmp")
            temporary.write_bytes(intended)
            temporary.replace(path)
    if stale:
        raise SystemExit(f"generated documentation is stale: {', '.join(stale)}")
    print("documentation is current" if check else "documentation generated")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["generate"])
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    generate(check=bool(args.check))


if __name__ == "__main__":
    main()
