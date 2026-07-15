# SWEBOK KA別AI駆動開発ワークフロー

状態: complete

## 入力

- `.workspace/swebok_checklist.xlsx`（read-onlyの正本入力）
- repository root `AGENTS.md`
- `docs/spec/`、`docs/design/design-system.md`

## 対象

- ExcelのKAシート（01〜10、12〜19）ごとのrepository-local skill
- 各skillのUI向けagent metadataと、委譲可能なrepository agent定義
- root/agentsの`AGENTS.md`によるAI駆動工程・セルフチェック規約
- Git管理可能なMarkdown版チェックリストと再生成・検証手段

## 受け入れ条件

- [x] Excelの18 KAすべてに、一意な`skills/<name>/SKILL.md`がある。
- [x] 各skillに`agents/openai.yaml`、`references/checklist.md`があり、対応KAと件数が一致する。
- [x] 各KAに`agents/<name>.toml`があり、対応skill、工程、証跡、非対象を指示する。
- [x] root `AGENTS.md`と`agents/AGENTS.md`が、AIによる計画→実装→検証→報告の各工程で該当チェックリストを自己検査するよう規定する。
- [x] セルフチェックは`pass/fail/not-applicable/blocked`と根拠を記録し、未実行をpassにしない。
- [x] `.workspace`をGitへ追加せず、チェックリスト内容をGit管理可能なMarkdownへ持ち込む。
- [x] Excelからの再生成が決定的で、元シート名・全ID・項目数・内容の一致を自動検証できる。
- [x] 全skillを`quick_validate.py`で検証し、agent TOML/YAML、Markdown link、生成差分なしを検証する。
- [x] `reports/working`にコマンド結果、fit、未対応、残余riskを事実どおり記録する。
- [x] 変更を目的単位でcommitし、public GitHubの`main`へpushする。

## 非対象

- 各チェック項目について、現行製品がすでに合格しているとの判定
- deploy、production変更、外部approvalの代行
- `.workspace/swebok_checklist.xlsx`自体の変更・Git追加

## 制約と前提

### 制約

- `.workspace`はread-onlyで、Gitへ追加しない。
- deploy、production変更、履歴改変、force pushを行わない。
- author identifierや依頼本文をpublic artifactへ転記しない。

### 前提

- KAはExcelの番号付き18シート（01〜10、12〜19）を指す。
- `agent`は`agents/*.toml`、skill UI metadataは`skills/*/agents/openai.yaml`として提供する。
- `agent.md`のrepository-wide指示は既存規約に合わせてrootと`agents/`の`AGENTS.md`へ反映する。

## 検証候補

- checklist生成・整合検証スクリプト
- 全skillへの`quick_validate.py`
- TOML/YAML構文検証
- `git diff --check`
- `task verify`（Taskfile/shared workflow変更時のみ）

## 適用KAとセルフチェック対象

Excel構造と既存agent規約の棚卸し後に対象を確定した。今後のgateで同じIDを再評価する。

| KA | 対象ID | このtaskで期待する証跡 |
| --- | --- | --- |
| マネジメント | MGT-002, MGT-003, MGT-006, MGT-022, MGT-092, MGT-132 | 対象/非対象、検証可能な受け入れ条件、制約、成果物一覧、事実ベース進捗、task/report整合 |
| プロセス | PRC-001, PRC-003, PRC-004, PRC-056, PRC-079, PRC-081, PRC-082, PRC-086 | 適用範囲、用語、入力/活動/出力、チェックによる遵守検出、Git/task/tool連携、成果物間整合 |
| 構成管理 | SCM-020, SCM-021, SCM-080, SCM-081, SCM-085, SCM-102, SCM-164, SCM-166 | 管理対象一覧、Git管理、変更task、trace、同期自動化、相互参照、Markdown整形 |
| 品質保証 | QUA-070, QUA-080, QUA-090, QUA-091, QUA-097, QUA-122, QUA-123 | 工程gate、遵守検証、checklist review、指摘追跡、版管理、CI/検証、記録様式 |
| 実装 | CON-010, CON-112, CON-113, CON-114 | Python静的検証、review記録、指摘解消、目的単位commit |
| テスト | TST-009, TST-311, TST-401, TST-601, TST-801, TST-802, TST-804 | 自動/手動方針、4状態の結果欄、決定的同期検証、全ケース結果、終了基準、残余risk、件数一致 |
| AI | AI-002, AI-019 | AI工程のreview point、自律agentの権限境界・approval・停止・監査可能性 |

AI-012は生成AI製品の出力品質評価を対象とし、今回のrepository agent定義の実装検証には適用しない。人による最終acceptanceは実装完了と分離し、user reviewで扱う。
