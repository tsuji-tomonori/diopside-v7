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
    for path_value in paths.values():
        path_item = cast(dict[str, Any], path_value)
        for operation_value in path_item.values():
            operation_schema = cast(dict[str, Any], operation_value)
            responses = cast(dict[str, Any], operation_schema.get("responses", {}))
            for response_value in responses.values():
                response = cast(dict[str, Any], response_value)
                if response.get("description") == "Successful Response":
                    response["description"] = "成功レスポンス"
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
    return ", ".join(str(value) for value in cast(list[object], values)) or "なし"


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
    return str(schema_type) if schema_type is not None else "型なし"


def render_inventory(operations: list[dict[str, Any]]) -> bytes:
    """API一覧と操作別文書へのリンクを生成する。"""
    lines = [
        "# 公開APIドキュメント索引(自動生成)",
        "",
        "> `public-contracts.manual.json` と実行時OpenAPIから自動生成しているため、"
        "直接編集しないこと。",
        "",
        "| 操作ID | メソッド | パス | 文書 |",
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
            "## 集約成果物",
            "",
            "- [OpenAPI](openapi.gen.json)",
            "- [生成レジストリ](generation-registry.gen.json)",
            "",
            f"操作数: {len(operations)}",
            f"操作別文書数: {len(operations) * len(DOCUMENT_KINDS)}",
        ]
    )
    return ("\n".join(lines) + "\n").encode()


def render_interface(operation: dict[str, Any], operation_schema: dict[str, Any]) -> bytes:
    parameters = cast(list[dict[str, Any]], operation_schema.get("parameters", []))
    responses = cast(dict[str, Any], operation_schema["responses"])
    lines = [
        f"# {operation['operationId']} インターフェース(自動生成)",
        "",
        f"- メソッド: `{operation['method']}`",
        f"- パス: `{operation['path']}`",
        f"- 概要: {operation['summary']}",
        f"- 認証: {operation['auth']}",
        f"- 権限: {_csv(operation['permissions'])}",
        "- セキュリティ要件: "
        f"{'宣言あり' if operation_schema.get('security') else 'なし(公開読み取り)'}",
        "",
        "## パラメーター",
        "",
        "| 名前 | 場所 | 必須 | スキーマ |",
        "| --- | --- | --- | --- |",
    ]
    if parameters:
        for parameter in parameters:
            parameter_schema = cast(dict[str, Any], parameter.get("schema", {}))
            schema_name = parameter_schema.get("type", parameter_schema.get("$ref", "不明"))
            lines.append(
                f"| `{parameter['name']}` | {parameter['in']} | "
                f"{str(parameter.get('required', False)).lower()} | `{schema_name}` |"
            )
    else:
        lines.append("| — | — | — | — |")
    lines.extend(
        [
            "",
            "## レスポンス",
            "",
            "| 状態 | 説明 | スキーマ |",
            "| ---: | --- | --- |",
        ]
    )
    for status, response_value in sorted(responses.items(), key=lambda item: int(item[0])):
        response = cast(dict[str, Any], response_value)
        content = cast(dict[str, Any], response.get("content", {}))
        json_content = cast(dict[str, Any], content.get("application/json", {}))
        response_schema = cast(dict[str, Any], json_content.get("schema", {}))
        schema_name = response_schema.get("$ref", response_schema.get("type", "なし"))
        lines.append(f"| {status} | {response['description']} | `{schema_name}` |")
    lines.extend(
        [
            "",
            "## トレーサビリティ",
            "",
            f"- 要件: {_csv(operation['requirements'])}",
            f"- 仕様: {_csv(operation['specifications'])}",
            f"- 受け入れ条件: {_csv(operation['acceptance'])}",
        ]
    )
    return ("\n".join(lines) + "\n").encode()


def render_sequence(operation: dict[str, Any], operation_schema: dict[str, Any]) -> bytes:
    loader_calls = _loader_calls(operation)
    function_name = str(operation["function"])
    response_model = _response_schema_name(operation_schema, int(operation["success"]))
    lines = [
        f"# {operation['operationId']} シーケンス(自動生成)",
        "",
        "```mermaid",
        "sequenceDiagram",
        "    actor Client as クライアント",
        "    participant Router as ルーター",
        "    participant Functions as 関数",
        "    participant Loader as 契約ローダー",
        "    participant Storage as 公開契約ディレクトリ",
        f"    Client->>Router: {operation['method']} {operation['path']}",
        "    Router->>Router: 型付き契約ディレクトリ依存を解決する",
        f"    Router->>Functions: {function_name}(...) ",
    ]
    for loader_call in loader_calls:
        lines.extend(
            [
                f"    Functions->>Loader: {loader_call}(...) ",
                "    Loader->>Storage: 正規JSONを読み込んで解析する",
                "    Storage-->>Loader: JSONバイト列またはファイルなし",
                "    Loader-->>Functions: 検証済みデータまたは分類済みHTTPエラー",
            ]
        )
    lines.extend(
        [
            f"    Functions-->>Router: 型付き{response_model}レスポンス",
            f"    Router-->>Client: {operation['success']} JSON",
            "```",
            "",
            "## エラーシーケンス",
            "",
            "- 契約ローダーは成果物の欠落を404へ分類する。",
            "- 保存済みJSONの不正またはパス・データ不変条件の違反を500へ分類する。",
            "- フレームワークによるパス検証の失敗は、該当する場合に422へ分類する。",
            "- ルーターは広範な例外を捕捉せず、分類済みエラーをFastAPI経由で伝播する。",
        ]
    )
    return ("\n".join(lines) + "\n").encode()


def render_detail_design(operation: dict[str, Any]) -> bytes:
    paths = _source_paths(operation)
    loader_calls = _loader_calls(operation)
    lines = [
        f"# {operation['operationId']} 詳細設計(自動生成)",
        "",
        f"- 安定契約スラッグ: `{operation['slug']}`",
        f"- ビジネス関数: `{operation['function']}`",
        f"- 認証: {operation['auth']}",
        f"- 権限: {_csv(operation['permissions'])}",
        f"- 冪等性: {operation['idempotency']}",
        f"- トランザクション境界: {operation['transaction']}",
        f"- 外部影響: {operation['externalEffects']}",
        "",
        "## ソースの責務",
        "",
        "| 関心事 | ソース |",
        "| --- | --- |",
    ]
    for concern, path in paths.items():
        lines.append(f"| {concern} | `{path.relative_to(ROOT)}` |")
    lines.extend(
        [
            "",
            "## リソース境界",
            "",
            f"- 契約ローダー呼び出し: {', '.join(f'`{call}`' for call in loader_calls)}",
            "- データベース/SQL: 非該当。この操作はバージョン付き"
            "ファイルシステム成果物を読み取る。",
            "- プロバイダーSDK: 非該当。操作層はプロバイダーアダプターをimportしない。",
            "- 変更/切り戻し: 非該当。トランザクションを伴わない安全な読み取りである。",
            "",
            "## 互換性",
            "",
            f"- 操作ID `{operation['operationId']}` とパス `{operation['path']}` は安定している。",
            "- レスポンスデータの検証責務は正規公開契約モデルが持つ。",
            "- 後方互換性のない公開スキーマ変更には、メジャースキーマまたは"
            "パスの移行が必要である。",
        ]
    )
    return ("\n".join(lines) + "\n").encode()


def render_test_factors(operation: dict[str, Any]) -> bytes:
    path_parameters = re.findall(r"{([^}:]+)(?::[^}]+)?}", str(operation["path"]))
    lines = [
        f"# {operation['operationId']} テスト観点(自動生成)",
        "",
        "| ID | 種別 | 入力/条件 | 期待結果 |",
        "| --- | --- | --- | --- |",
        f"| TF-001 | 正常 | 既存の正規成果物 | {operation['success']}かつレスポンススキーマ一致 |",
        "| TF-002 | データ欠落 | 成果物パスが存在しない | 代替データなしで404 |",
        "| TF-003 | 不正データ | 保存済みJSONが不正または正規モデルに違反 | "
        "非公開内容を露出せず500 |",
        "| TF-004 | 互換性 | 安定したメソッド、パス、操作IDを手動契約と比較 | "
        "差異があれば生成失敗 |",
        "| TF-005 | セキュリティ | credentialなしの公開読み取り | "
        "認証要件もプロバイダーcredential露出もない |",
    ]
    if path_parameters:
        lines.append(
            f"| TF-006 | 境界/検証 | 不正な{', '.join(path_parameters)}パス値 | "
            "フレームワーク検証が適用される場合は宣言済み422、それ以外は404。"
            "契約ルート外へ移動できない |"
        )
    lines.extend(
        [
            "",
            "## 必須アサーション",
            "",
            f"- 宣言済みエラー状態: {_csv(operation['errors'])}。",
            "- 任意値の欠落は欠落のまま維持し、架空の0、日付、件数、metadataを補わない。",
            "- 同じリリース成果物への反復読み取りはバイト列と意味の両方で安定する。",
            "- 生成インターフェースと実行時OpenAPIでメソッド、パス、操作ID、エラーが一致する。",
        ]
    )
    return ("\n".join(lines) + "\n").encode()


def render_examples(operation: dict[str, Any]) -> bytes:
    sample = _sample(operation)
    lines = [
        f"# {operation['operationId']} 例(自動生成)",
        "",
        f"生成元: `src/{str(operation['module']).replace('.', '/')}/samples.py`",
        "",
        "## 成功レスポンス",
        "",
        "```json",
        json.dumps(sample, ensure_ascii=False, indent=2, sort_keys=True),
        "```",
        "",
        "エラーデータにはFastAPIの分類済みHTTPエラーレスポンスを使用し、デモ用の代替データは生成しない。",
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
    """決定的な全出力を依存順に、書き込まず構築する。"""
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
            raise SystemExit(f"生成ドキュメントが古い: {', '.join(stale)}")
        print(f"ドキュメントは最新: {len(outputs)}ファイル")
        return
    for path, intended in sorted(outputs.items(), key=lambda item: str(item[0])):
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(path.suffix + ".tmp")
        temporary.write_bytes(intended)
        temporary.replace(path)
    print(f"ドキュメントを生成: {len(outputs)}ファイル")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["generate"])
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    generate(check=bool(args.check))


if __name__ == "__main__":
    main()
