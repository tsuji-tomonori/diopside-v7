from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REQUIRED = {"__init__.py", "contract.py", "functions.py", "router.py", "samples.py", "schemas.py"}
FORBIDDEN = {"boto3", "botocore", "httpx", "requests"}


def imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    result: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            result.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            result.add(node.module)
    return result


def check() -> list[str]:
    errors: list[str] = []
    main = ROOT / "src/app/main.py"
    source = main.read_text(encoding="utf-8")
    for token in ("def create_app(", "app = create_app()", '"/health"'):
        if token not in source:
            errors.append(f"src/app/main.py: missing {token}")
    for router in sorted((ROOT / "src/app/apis").glob("*/*/router.py")):
        missing = sorted(REQUIRED - {path.name for path in router.parent.iterdir()})
        if missing:
            errors.append(f"{router.parent.relative_to(ROOT)}: missing {', '.join(missing)}")
        router_source = router.read_text(encoding="utf-8")
        if "api_functions" not in router_source:
            errors.append(f"{router.relative_to(ROOT)}: functions must use api_functions alias")
        for module in imports(router):
            if module.split(".")[0] in FORBIDDEN or "_provider" in module:
                errors.append(f"{router.relative_to(ROOT)}: forbidden import {module}")
        for token in ("contract_loader.", "session.execute(", "fetch_one(", "fetch_all("):
            if token in router_source:
                errors.append(f"{router.relative_to(ROOT)}: direct resource call {token}")
    return errors


def main() -> None:
    errors = check()
    if errors:
        raise SystemExit("\n".join(f"ERROR: {error}" for error in errors))
    print("architecture checks passed")


if __name__ == "__main__":
    main()
