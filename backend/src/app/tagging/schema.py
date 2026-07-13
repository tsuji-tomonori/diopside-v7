from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Literal, cast

from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import SchemaError, ValidationError

DocumentKind = Literal["snapshot", "correction", "usage"]

SCHEMA_ROOT = Path(__file__).resolve().parents[3] / "schemas"
SCHEMA_FILES = {
    ("snapshot", "3.0.0"): "tag-snapshot-v3.schema.json",
    ("correction", "1.0.0"): "tag-correction-ledger-v3.schema.json",
    ("usage", "1.0.0"): "usage-decision-ledger-v1.schema.json",
}


class TagSchemaError(ValueError):
    pass


def resolve_schema(document: dict[str, Any], kind: DocumentKind) -> dict[str, Any]:
    version = document.get("schemaVersion")
    if not isinstance(version, str):
        raise TagSchemaError("document requires string schemaVersion")
    filename = SCHEMA_FILES.get((kind, version))
    if filename is None:
        raise TagSchemaError(f"unsupported {kind} schemaVersion: {version}")
    raw_schema: object = json.loads(
        (SCHEMA_ROOT / filename).read_text(encoding="utf-8")
    )
    if not isinstance(raw_schema, dict):
        raise TagSchemaError(f"schema root must be an object: {filename}")
    return cast(dict[str, Any], raw_schema)


def validate_tag_document(document: dict[str, Any], kind: DocumentKind) -> None:
    schema = resolve_schema(document, kind)
    try:
        Draft202012Validator.check_schema(schema)
        Draft202012Validator(schema, format_checker=FormatChecker()).validate(  # pyright: ignore[reportUnknownMemberType]
            document
        )
    except (SchemaError, ValidationError) as exc:
        path = ".".join(str(part) for part in exc.absolute_path) or "$"
        raise TagSchemaError(f"{kind} schema violation at {path}: {exc.message}") from exc
    if kind == "usage":
        _validate_usage_semantics(document)


def _validate_usage_semantics(document: dict[str, Any]) -> None:
    decisions = cast(list[dict[str, Any]], document["decisions"])
    source_kinds = [cast(str, decision["sourceKind"]) for decision in decisions]
    if len(source_kinds) != len(set(source_kinds)):
        raise TagSchemaError("usage sourceKind values must be unique")
    unknown = next(
        (decision for decision in decisions if decision["sourceKind"] == "unknown"),
        None,
    )
    if unknown is None or unknown["decision"] != "exclude":
        raise TagSchemaError("usage ledger requires unknown=exclude")
