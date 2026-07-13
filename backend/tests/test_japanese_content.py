import ast
import io
import json
import re
import tokenize
from pathlib import Path
from typing import cast

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
JAPANESE_PATTERN = re.compile(r"[ぁ-んァ-ヶ一-龠々]")
PYTHON_ROOTS = (
    REPOSITORY_ROOT / "backend/src",
    REPOSITORY_ROOT / "backend/tests",
    REPOSITORY_ROOT / "tools",
)
SCRIPT_ROOTS = (REPOSITORY_ROOT / "frontend", REPOSITORY_ROOT / "infra")
UNIT_SCRIPT_ROOTS = (
    REPOSITORY_ROOT / "frontend/src",
    REPOSITORY_ROOT / "infra/test",
)
MARKDOWN_ROOTS = (
    REPOSITORY_ROOT / "README.md",
    REPOSITORY_ROOT / "AGENTS.md",
    REPOSITORY_ROOT / "agents",
    REPOSITORY_ROOT / "backend/README.md",
    REPOSITORY_ROOT / "backend/docs",
    REPOSITORY_ROOT / "docs",
    REPOSITORY_ROOT / "infra/README.md",
    REPOSITORY_ROOT / "reports",
    REPOSITORY_ROOT / "skills",
    REPOSITORY_ROOT / "tasks",
)
COMMENT_DIRECTIVES = ("#!", "# pyright:", "# type:", "# noqa", "# pragma:")
SOURCE_REFERENCE_PREFIXES = ("- IEEE ", "- YouTube ", "- AWS ")
AAA_MARKERS = ("1. 初期化", "2. テストの実行", "3. アサーション")


def _files(root: Path, suffixes: tuple[str, ...]) -> list[Path]:
    """指定root配下から対象拡張子の管理ファイルを列挙する。"""
    if root.is_file():
        return [root] if root.suffix in suffixes else []
    return sorted(
        path
        for path in root.rglob("*")
        if path.is_file()
        and path.suffix in suffixes
        and not {"node_modules", "dist", "cdk.out", ".venv"}.intersection(path.parts)
    )


def _has_japanese(value: str) -> bool:
    """文字列に日本語文字が含まれるか判定する。"""
    return JAPANESE_PATTERN.search(value) is not None


def _python_violations() -> list[str]:
    """Pythonの説明コメント、docstring、必須関数説明を検査する。"""
    violations: list[str] = []
    for root in PYTHON_ROOTS:
        for path in _files(root, (".py",)):
            source = path.read_text(encoding="utf-8")
            relative = path.relative_to(REPOSITORY_ROOT)
            for token in tokenize.generate_tokens(io.StringIO(source).readline):
                if token.type != tokenize.COMMENT:
                    continue
                comment = token.string.strip()
                if comment.startswith(COMMENT_DIRECTIVES):
                    continue
                if not _has_japanese(comment):
                    violations.append(f"{relative}:{token.start[0]}: コメントが日本語ではない")

            tree = ast.parse(source, filename=str(path))
            for node in ast.walk(tree):
                if not isinstance(
                    node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)
                ):
                    continue
                docstring = ast.get_docstring(node)
                if docstring is not None and not _has_japanese(docstring):
                    line = getattr(node, "lineno", 1)
                    violations.append(f"{relative}:{line}: docstringが日本語ではない")
                if (
                    isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                    and (docstring is None or not _has_japanese(docstring))
                    and (node.name.startswith("test_") or path.name == "functions.py")
                ):
                    violations.append(f"{relative}:{node.lineno}: {node.name}に日本語の説明がない")
    return violations


def _script_violations() -> list[str]:
    """TypeScriptとJavaScriptのコメントおよびテスト説明を検査する。"""
    violations: list[str] = []
    for root in SCRIPT_ROOTS:
        for path in _files(root, (".ts", ".tsx", ".js")):
            lines = path.read_text(encoding="utf-8").splitlines()
            relative = path.relative_to(REPOSITORY_ROOT)
            for index, line in enumerate(lines):
                stripped = line.strip()
                if stripped.startswith("//") and not _has_japanese(stripped):
                    violations.append(f"{relative}:{index + 1}: コメントが日本語ではない")
                if not re.search(r"\b(?:it|test)\s*\(", line):
                    continue
                previous = index - 1
                while previous >= 0 and not lines[previous].strip():
                    previous -= 1
                explanation = lines[previous].strip() if previous >= 0 else ""
                if not explanation.startswith("//") or not _has_japanese(explanation):
                    violations.append(
                        f"{relative}:{index + 1}: テストケース直前に日本語の説明がない"
                    )
    return violations


def _aaa_violations() -> list[str]:
    """単体テスト内のAAAコメントの件数と順序を検査する。"""
    violations: list[str] = []
    test_root = REPOSITORY_ROOT / "backend/tests"
    for path in _files(test_root, (".py",)):
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(path))
        relative = path.relative_to(REPOSITORY_ROOT)
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if not node.name.startswith("test_") or node.end_lineno is None:
                continue
            segment = "\n".join(source.splitlines()[node.lineno - 1 : node.end_lineno])
            positions = [segment.find(f"# {marker}") for marker in AAA_MARKERS]
            counts = [segment.count(f"# {marker}") for marker in AAA_MARKERS]
            if counts != [1, 1, 1] or positions != sorted(positions) or -1 in positions:
                violations.append(
                    f"{relative}:{node.lineno}: {node.name}のAAAコメントが欠落・重複・順序違反"
                )

    test_pattern = re.compile(r"\b(?:it|test)\s*\(")
    for root in UNIT_SCRIPT_ROOTS:
        for path in _files(root, (".ts", ".tsx", ".js")):
            lines = path.read_text(encoding="utf-8").splitlines()
            starts = [index for index, line in enumerate(lines) if test_pattern.search(line)]
            relative = path.relative_to(REPOSITORY_ROOT)
            for position, start in enumerate(starts):
                end = starts[position + 1] if position + 1 < len(starts) else len(lines)
                segment = "\n".join(lines[start:end])
                positions = [segment.find(f"// {marker}") for marker in AAA_MARKERS]
                counts = [segment.count(f"// {marker}") for marker in AAA_MARKERS]
                if counts != [1, 1, 1] or positions != sorted(positions) or -1 in positions:
                    violations.append(
                        f"{relative}:{start + 1}: 単体テストのAAAコメントが欠落・重複・順序違反"
                    )
    return violations


def _markdown_violations() -> list[str]:
    """Markdownの英語だけで書かれた自然言語を検査する。"""
    violations: list[str] = []
    for root in MARKDOWN_ROOTS:
        for path in _files(root, (".md",)):
            in_fence = False
            relative = path.relative_to(REPOSITORY_ROOT)
            for line_number, line in enumerate(
                path.read_text(encoding="utf-8").splitlines(), start=1
            ):
                stripped = line.strip()
                if stripped.startswith("```"):
                    in_fence = not in_fence
                    continue
                if in_fence or not stripped or _has_japanese(stripped):
                    continue
                if stripped.startswith(SOURCE_REFERENCE_PREFIXES):
                    continue
                if stripped.startswith("|") or stripped.startswith("- ["):
                    continue
                if re.fullmatch(r"[-|: #>*0-9.,/`()\[\]{}_+=]+", stripped):
                    continue
                without_code = re.sub(r"`[^`]+`", "", stripped)
                without_links = re.sub(r"\([^)]*\)", "", without_code)
                words = re.findall(r"[A-Za-z][A-Za-z'-]*", without_links)
                natural_words = [word for word in words if not word.isupper()]
                if len(natural_words) >= 3:
                    violations.append(
                        f"{relative}:{line_number}: 英語だけの自然言語: {stripped[:80]}"
                    )
    return violations


def _configuration_violations() -> list[str]:
    """生成文書へ流れる設定値とTask説明を検査する。"""
    violations: list[str] = []
    taskfile = REPOSITORY_ROOT / "Taskfile.yml"
    for line_number, line in enumerate(taskfile.read_text(encoding="utf-8").splitlines(), start=1):
        if "desc:" in line and not _has_japanese(line):
            violations.append(f"Taskfile.yml:{line_number}: task説明が日本語ではない")

    openapi_path = REPOSITORY_ROOT / "backend/docs/api/openapi.gen.json"
    openapi = cast(object, json.loads(openapi_path.read_text(encoding="utf-8")))
    pending: list[object] = [openapi]
    while pending:
        value = pending.pop()
        if isinstance(value, dict):
            for key, child in cast(dict[object, object], value).items():
                if (
                    key in {"description", "summary"}
                    and isinstance(child, str)
                    and not _has_japanese(child)
                ):
                    relative = openapi_path.relative_to(REPOSITORY_ROOT)
                    violations.append(f"{relative}: {key}が日本語ではない: {child}")
                pending.append(child)
        elif isinstance(value, list):
            pending.extend(cast(list[object], value))
    return violations


def test_repository_explanations_are_written_in_japanese() -> None:
    """文書、コメント、テスト、functions関数の日本語説明を一括検証する。"""
    # 1. 初期化
    checks = (
        _python_violations,
        _script_violations,
        _aaa_violations,
        _markdown_violations,
        _configuration_violations,
    )

    # 2. テストの実行
    violations = [violation for check in checks for violation in check()]

    # 3. アサーション
    assert violations == [], "\n" + "\n".join(violations)
