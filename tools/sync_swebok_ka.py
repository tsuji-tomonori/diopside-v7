#!/usr/bin/env python3
"""ExcelのKAチェックリストからrepository-local skill/agentを同期する。"""
# ruff: noqa: E501  # 生成する日本語テンプレートは可読性を保つため改行しない。

from __future__ import annotations

import argparse
import hashlib
import re
import sys
import tomllib
from dataclasses import dataclass
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZipFile

XML_NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
REL_NS = {"r": "http://schemas.openxmlformats.org/package/2006/relationships"}
OFFICE_REL = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"
HEADERS = (
    "ID",
    "区分",
    "カテゴリ",
    "重要度",
    "チェック項目",
    "合格基準",
    "意図(なぜ確認するか)",
    "対象ドキュメント(参照箇所)",
)
SUMMARY_HEADERS = (
    "領域",
    "シート",
    "対象ドキュメント",
    "項目数",
    "Critical",
    "High",
    "Medium",
    "Low",
    "カバレッジ総評",
)
GAP_HEADERS = (
    "KA",
    "不足していたSWEBOKトピック",
    "なぜ重要か",
    "反映ID",
    "重要度",
    "追加チェック項目",
    "合格基準",
    "意図",
)
MAX_COLUMNS = len(SUMMARY_HEADERS)


@dataclass(frozen=True)
class Ka:
    sheet: str
    skill: str
    title: str
    phase: str
    focus: str


KAS = (
    Ka(
        "01_要件定義",
        "swebok-requirements",
        "要件定義",
        "発見・要件定義",
        "要求の獲得、分析、仕様化、妥当性確認、変更管理",
    ),
    Ka(
        "02_アーキテクチャ",
        "swebok-architecture",
        "アーキテクチャ",
        "アーキテクチャ設計",
        "ステークホルダー関心事、ビュー、設計判断、品質属性、評価",
    ),
    Ka(
        "03_詳細設計",
        "swebok-design",
        "詳細設計",
        "詳細設計",
        "要求・アーキテクチャとの追跡、API、データ、UI、設計品質",
    ),
    Ka(
        "04_実装",
        "swebok-construction",
        "実装",
        "実装",
        "複雑性、再利用、コーディング、レビュー、ビルド、生成AI利用",
    ),
    Ka(
        "05_テスト",
        "swebok-testing",
        "テスト",
        "検証",
        "計画、レベル、技法、環境、実行、欠陥、完了判定",
    ),
    Ka(
        "06_運用",
        "swebok-operations",
        "運用",
        "運用設計・運用",
        "可観測性、インシデント、継続性、リリース、SLO、Runbook",
    ),
    Ka(
        "07_保守",
        "swebok-maintenance",
        "保守",
        "保守・変更",
        "保守計画、影響分析、変更、回帰、移行、廃止",
    ),
    Ka(
        "08_構成管理",
        "swebok-configuration-management",
        "構成管理",
        "全工程",
        "構成識別、変更統制、状態記録、監査、ビルド、リリース",
    ),
    Ka(
        "09_マネジメント",
        "swebok-engineering-management",
        "マネジメント",
        "計画・統制",
        "立上げ、スコープ、見積り、リスク、進捗、終結",
    ),
    Ka(
        "10_プロセス",
        "swebok-engineering-process",
        "プロセス",
        "全工程",
        "ライフサイクル、プロセス定義、評価、測定、継続的改善",
    ),
    Ka(
        "12_品質保証",
        "swebok-quality",
        "品質保証",
        "全工程",
        "品質計画、保証、管理、レビュー、測定、改善",
    ),
    Ka(
        "13_セキュリティ",
        "swebok-security",
        "セキュリティ",
        "全工程",
        "脅威、要求、設計、実装、検証、運用、インシデント",
    ),
    Ka(
        "14_クラウド",
        "swebok-cloud",
        "クラウド",
        "クラウド設計・運用",
        "共通Well-Architected観点、責任分界、信頼性、コスト、持続可能性",
    ),
    Ka(
        "15_AWS",
        "swebok-aws",
        "AWS",
        "AWS設計・運用",
        "AWS Well-Architected各柱とサービス固有の統制",
    ),
    Ka(
        "16_GoogleCloud",
        "swebok-google-cloud",
        "Google Cloud",
        "Google Cloud設計・運用",
        "Google Cloud Architecture Framework各柱とサービス固有の統制",
    ),
    Ka(
        "17_Azure",
        "swebok-azure",
        "Azure",
        "Azure設計・運用",
        "Azure Well-Architected各柱とサービス固有の統制",
    ),
    Ka(
        "18_OCI",
        "swebok-oci",
        "OCI",
        "OCI設計・運用",
        "OCI Well-Architected各柱とサービス固有の統制",
    ),
    Ka(
        "19_AI",
        "swebok-ai",
        "AI",
        "AIライフサイクル全体",
        "AIガバナンス、データ、評価、責任あるAI、LLMOps、コスト、セキュリティ",
    ),
)


def column_index(cell_reference: str) -> int:
    letters = re.match(r"[A-Z]+", cell_reference)
    if letters is None:
        raise ValueError(f"不正なセル参照: {cell_reference}")
    result = 0
    for char in letters.group(0):
        result = result * 26 + ord(char) - ord("A") + 1
    return result - 1


def cell_text(cell: ET.Element) -> str:
    if cell.get("t") == "inlineStr":
        return "".join(node.text or "" for node in cell.findall(".//m:t", XML_NS))
    value = cell.find("m:v", XML_NS)
    return "" if value is None else value.text or ""


def read_workbook(path: Path) -> dict[str, list[tuple[str, ...]]]:
    with ZipFile(path) as archive:
        # `.workspace`のread-only受領ファイルだけを入力とし、外部入力は受け付けない。
        workbook = ET.fromstring(archive.read("xl/workbook.xml"))  # noqa: S314
        relationships = ET.fromstring(  # noqa: S314
            archive.read("xl/_rels/workbook.xml.rels")
        )
        targets = {
            node.get("Id"): node.get("Target", "").lstrip("/")
            for node in relationships.findall("r:Relationship", REL_NS)
        }
        result: dict[str, list[tuple[str, ...]]] = {}
        for sheet in workbook.findall(".//m:sheets/m:sheet", XML_NS):
            name = sheet.get("name", "")
            target = targets[sheet.get(OFFICE_REL)]
            root = ET.fromstring(archive.read(target))  # noqa: S314
            rows: list[tuple[str, ...]] = []
            for row in root.findall(".//m:sheetData/m:row", XML_NS):
                values = [""] * MAX_COLUMNS
                for cell in row.findall("m:c", XML_NS):
                    index = column_index(cell.get("r", ""))
                    if index < len(values):
                        values[index] = cell_text(cell)
                if any(values):
                    rows.append(tuple(values))
            result[name] = rows
    return result


def markdown_cell(value: str) -> str:
    return value.replace("\\", "\\\\").replace("|", "\\|").replace("\r", "").replace("\n", "<br>")


def checklist_markdown(ka: Ka, rows: list[tuple[str, ...]], source_hash: str) -> str:
    rows = [tuple(row[: len(HEADERS)]) for row in rows]
    if not rows or rows[0] != HEADERS:
        raise ValueError(f"{ka.sheet}: ヘッダーが期待値と一致しない: {rows[:1]}")
    items = rows[1:]
    if len({row[0] for row in items}) != len(items):
        raise ValueError(f"{ka.sheet}: IDが空または重複している")
    lines = [
        f"# {ka.title}チェックリスト",
        "",
        f"- 元シート: `{ka.sheet}`",
        f"- 項目数: {len(items)}",
        f"- 元Excel SHA-256: `{source_hash}`",
        "- 同期方法: `python3 tools/sync_swebok_ka.py --write`",
        "",
        "> このファイルは `.workspace/swebok_checklist.xlsx` から生成する。手編集しない。判定結果はtaskまたは`reports/working`へ記録する。",
        "",
        "| " + " | ".join(HEADERS) + " |",
        "| " + " | ".join("---" for _ in HEADERS) + " |",
    ]
    lines.extend("| " + " | ".join(markdown_cell(value) for value in row) + " |" for row in items)
    return "\n".join(lines) + "\n"


def source_summary_markdown(rows: list[tuple[str, ...]], source_hash: str) -> str:
    if len(rows) < 3 or tuple(rows[2]) != SUMMARY_HEADERS:
        raise ValueError("サマリのヘッダーが期待値と一致しない")
    lines = [
        f"# {rows[0][0]}",
        "",
        rows[1][0],
        "",
        f"元Excel SHA-256: `{source_hash}`",
        "",
        "| " + " | ".join(SUMMARY_HEADERS) + " |",
        "| " + " | ".join("---" for _ in SUMMARY_HEADERS) + " |",
    ]
    lines.extend(
        "| " + " | ".join(markdown_cell(value) for value in row) + " |" for row in rows[3:]
    )
    return "\n".join(lines) + "\n"


def gap_analysis_markdown(rows: list[tuple[str, ...]], source_hash: str) -> str:
    trimmed = [tuple(row[: len(GAP_HEADERS)]) for row in rows]
    if not trimmed or trimmed[0] != GAP_HEADERS:
        raise ValueError("抜け漏れ分析のヘッダーが期待値と一致しない")
    lines = [
        "# SWEBOK抜け漏れ分析",
        "",
        f"元Excel SHA-256: `{source_hash}`",
        "",
        "| " + " | ".join(GAP_HEADERS) + " |",
        "| " + " | ".join("---" for _ in GAP_HEADERS) + " |",
    ]
    lines.extend(
        "| " + " | ".join(markdown_cell(value) for value in row) + " |" for row in trimmed[1:]
    )
    return "\n".join(lines) + "\n"


def validate_workbook(workbook: dict[str, list[tuple[str, ...]]]) -> None:
    summary_rows = workbook.get("サマリ", [])
    if len(summary_rows) < 3 or tuple(summary_rows[2]) != SUMMARY_HEADERS:
        raise ValueError("サマリの構造が期待値と一致しない")
    summaries = {row[1]: row for row in summary_rows[3:] if row[1]}
    all_ids: set[str] = set()
    for ka in KAS:
        rows = [tuple(row[: len(HEADERS)]) for row in workbook.get(ka.sheet, [])]
        if not rows or rows[0] != HEADERS:
            raise ValueError(f"{ka.sheet}: ヘッダーが期待値と一致しない")
        items = rows[1:]
        if any(not item[0] for item in items):
            raise ValueError(f"{ka.sheet}: IDが空の項目がある")
        ids = {item[0] for item in items}
        if len(ids) != len(items):
            raise ValueError(f"{ka.sheet}: IDが重複している")
        duplicate = all_ids.intersection(ids)
        if duplicate:
            raise ValueError(f"KA間でIDが重複している: {sorted(duplicate)}")
        all_ids.update(ids)

        summary = summaries.get(ka.sheet)
        if summary is None:
            raise ValueError(f"サマリに{ka.sheet}がない")
        priorities = {name: 0 for name in ("Critical", "High", "Medium", "Low")}
        for item in items:
            if item[3] not in priorities:
                raise ValueError(f"{ka.sheet}: 不正な重要度 {item[3]!r}")
            priorities[item[3]] += 1
        actual = (len(items), *(priorities[name] for name in priorities))
        expected = tuple(int(value) for value in summary[3:8])
        if actual != expected:
            raise ValueError(f"{ka.sheet}: サマリ集計{expected}と実項目{actual}が一致しない")

    gap_rows = [tuple(row[: len(GAP_HEADERS)]) for row in workbook.get("抜け漏れ分析", [])]
    if not gap_rows or gap_rows[0] != GAP_HEADERS:
        raise ValueError("抜け漏れ分析の構造が期待値と一致しない")
    missing_gap_ids = {row[3] for row in gap_rows[1:] if row[3]} - all_ids
    if missing_gap_ids:
        raise ValueError(f"抜け漏れ分析の反映IDがKAにない: {sorted(missing_gap_ids)}")


def skill_markdown(ka: Ka) -> str:
    return f"""---
name: {ka.skill}
description: {ka.title}に関する計画、作成、変更、レビュー、完了判定を、repository同梱のSWEBOK/Well-Architectedチェックリストで証跡ベースに自己検査する。{ka.phase}の作業、関連成果物の更新、工程gateの判定時に使用する。
---

# {ka.title}のAI駆動セルフチェック

## 正本を読む

1. repository rootの`AGENTS.md`と対象taskの受け入れ条件を読む。
2. `docs/spec/`、該当設計、既存実装・testから現在状態を確認する。
3. [チェックリスト](references/checklist.md)を読み、対象範囲に適用するIDを選ぶ。

## AI駆動で進める

1. 作業前に、対象ID、期待する証跡、検証方法をtaskへ記録する。Critical/Highを先に評価する。
2. {ka.focus}を、正本、contract、test、docsと同じ変更単位で実装する。
3. 設計判断や生成物を推測で補わず、ファイル、command出力、runtime挙動、承認記録など再確認可能な証跡へ結びつける。
4. 計画完了、実装完了、検証完了、報告前の各gateで、適用IDを再評価する。変更により適用範囲が増えた場合は対象IDを追加する。
5. 関連KAへ影響する場合は、対応skillも読む。少なくとも要件→設計→実装→テスト→運用・保守の下流影響を確認する。

## 判定を記録する

taskまたは`reports/working`に次の列を持つ表を作る。

```text
ID | status | evidence | rationale | follow-up
```

- `pass`: 合格基準を直接証明する証跡がある場合だけ使う。
- `fail`: 合格基準への反証、欠落、または回帰がある場合に使い、修正後に再評価する。
- `not-applicable`: 対象外である具体的理由とスコープ根拠がある場合だけ使う。
- `blocked`: 外部approval、credential、環境などが不足し、ローカルで証明不能な場合に使う。
- 未確認、未実行、timeout、skipped、間接証拠は`pass`にしない。

## gateを閉じる

1. 適用IDがすべて`pass`、または根拠付き`not-applicable`か確認する。
2. `fail`を修正し、同じ検証を再実行する。`blocked`は実装完了と外部gateを分離して残す。
3. 実行commandと結果、未対応、残余riskを`reports/working`へ記録する。
4. 対象IDの件数と判定件数が一致しない場合、工程完了を宣言しない。
"""


def openai_yaml(ka: Ka) -> str:
    description = f"{ka.title}工程をSWEBOKチェックリストで証跡付き自己検査"
    return f'''interface:
  display_name: "SWEBOK {ka.title}"
  short_description: "{description}"
  default_prompt: "Use ${ka.skill} to perform an evidence-based self-check for this work."
'''


def agent_toml(ka: Ka) -> str:
    agent_name = ka.skill.replace("-", "_")
    return f'''name = "{agent_name}"
description = "{ka.title}の成果物と変更を、{ka.sheet}チェックリストにより証跡ベースで計画・レビューする専門agent。"
model_reasoning_effort = "high"
sandbox_mode = "workspace-write"

developer_instructions = """
repository rootのAGENTS.mdに従う{ka.title}担当agentである。

開始時に skills/{ka.skill}/SKILL.md と skills/{ka.skill}/references/checklist.md を全文読み、taskの受け入れ条件、docs/spec、実装・testの現在状態を確認する。

担当範囲は{ka.focus}。計画、実装、検証、報告の各gateで適用IDを選定し、IDごとに status、直接証拠、判定理由、follow-upを記録する。未確認、未実行、timeout、skipped、間接証拠をpassにしない。対象外はスコープ根拠付きnot-applicable、外部gateはblockedとして実装完了と分離する。

変更が他KAへ波及する場合は該当skillを明示し、親agentへ引き継ぐ。deploy、production変更、外部approval代行は行わない。

返却形式:
## Scope
## Applicable checklist IDs
## Findings and changes
## Verification evidence
## Checklist result
## Failures, blocked gates, and residual risk
"""
'''


def index_markdown(workbook: dict[str, list[tuple[str, ...]]], source_hash: str) -> str:
    item_count = sum(len(workbook[ka.sheet]) - 1 for ka in KAS)
    lines = [
        "# SWEBOK KA別AI駆動チェックリスト",
        "",
        "`.workspace/swebok_checklist.xlsx`のKAシートを、AI agentが工程ごとに利用できるMarkdownへ同期した索引。元Excelはread-only入力でありGitへ追加しない。",
        "",
        f"元Excel SHA-256: `{source_hash}`",
        "",
        f"同期対象: {len(KAS)} KA / {item_count}チェック項目",
        "",
        "元ブックの[サマリ](source-summary.md)と[抜け漏れ分析](gap-analysis.md)も同期対象とする。",
        "",
        "| KA | 元シート | 件数 | Skill | Agent | Checklist |",
        "| --- | --- | ---: | --- | --- | --- |",
    ]
    for ka in KAS:
        count = len(workbook[ka.sheet]) - 1
        lines.append(
            f"| {ka.title} | `{ka.sheet}` | {count} | "
            f"[`{ka.skill}`](../../../skills/{ka.skill}/SKILL.md) | "
            f"[`{ka.skill}.toml`](../../../agents/{ka.skill}.toml) | "
            f"[checklist](../../../skills/{ka.skill}/references/checklist.md) |"
        )
    lines.extend(
        [
            "",
            "## 同期と検証",
            "",
            "```bash",
            "python3 tools/sync_swebok_ka.py --write",
            "python3 tools/sync_swebok_ka.py --check",
            "task swebok:check",
            "```",
            "",
            "`--check`は元シート、ID、件数、生成済みskill/agent/checklistの完全一致を検証する。",
        ]
    )
    return "\n".join(lines) + "\n"


def expected_files(root: Path, source: Path) -> dict[Path, str]:
    workbook = read_workbook(source)
    missing = [ka.sheet for ka in KAS if ka.sheet not in workbook]
    if missing:
        raise ValueError(f"KAシートが不足している: {', '.join(missing)}")
    validate_workbook(workbook)
    source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    files: dict[Path, str] = {}
    for ka in KAS:
        rows = workbook[ka.sheet]
        files[root / "skills" / ka.skill / "SKILL.md"] = skill_markdown(ka)
        files[root / "skills" / ka.skill / "agents" / "openai.yaml"] = openai_yaml(ka)
        files[root / "skills" / ka.skill / "references" / "checklist.md"] = checklist_markdown(
            ka, rows, source_hash
        )
        files[root / "agents" / f"{ka.skill}.toml"] = agent_toml(ka)
    files[root / "docs" / "checklists" / "swebok" / "README.md"] = index_markdown(
        workbook, source_hash
    )
    files[root / "docs" / "checklists" / "swebok" / "source-summary.md"] = source_summary_markdown(
        workbook["サマリ"], source_hash
    )
    files[root / "docs" / "checklists" / "swebok" / "gap-analysis.md"] = gap_analysis_markdown(
        workbook["抜け漏れ分析"], source_hash
    )
    return files


def validate_generated(files: dict[Path, str]) -> None:
    ids: set[str] = set()
    for path, content in files.items():
        if path.suffix == ".toml":
            tomllib.loads(content)
        if path.name == "checklist.md":
            current = set(re.findall(r"^\| ([A-Z]+-[0-9]+) \|", content, re.MULTILINE))
            duplicate = ids.intersection(current)
            if duplicate:
                raise ValueError(f"チェックリストIDがKA間で重複している: {sorted(duplicate)}")
            ids.update(current)


def main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true", help="生成物を同期する")
    mode.add_argument("--check", action="store_true", help="生成物が同期済みか検証する")
    parser.add_argument("--source", type=Path, default=Path(".workspace/swebok_checklist.xlsx"))
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    source = args.source if args.source.is_absolute() else root / args.source
    files = expected_files(root, source)
    validate_generated(files)

    changed: list[Path] = []
    for path, content in files.items():
        if not path.exists() or path.read_text(encoding="utf-8") != content:
            changed.append(path)
            if args.write:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content, encoding="utf-8", newline="\n")

    if changed and args.check:
        for path in changed:
            print(f"OUT-OF-SYNC: {path.relative_to(root)}", file=sys.stderr)
        return 1
    action = "同期" if args.write else "検証"
    print(f"{action}完了: {len(KAS)} KA / {len(files)} files / changes={len(changed)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
