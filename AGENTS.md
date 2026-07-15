# Repository agent向け指示

## 完了規律

- `docs/spec`、`docs/design/design-system.md`、task acceptance criteriaを正本として扱う。
- 実装前に`tasks/todo|do|done`を確認し、複数step作業は`tasks/do`へ受け入れ条件を記録する。
- 未実行、timeout、skipped、blockedな検証をpassまたは完了として記録しない。
- `/goal`が有効な場合、旧completion orchestration skillを重複導入しない。
- 外部approval gateは実装完了と区別し、証跡がないgateを合格扱いしない。

## 必須ローカルskill

実装を伴う作業では、該当する次のskillを読む。

- `skills/implementation-test-selector/SKILL.md`
- `skills/repository-test-runner/SKILL.md`
- `skills/taskfile-command-runner/SKILL.md`（Taskfile利用時）
- `skills/no-mock-product-ui/SKILL.md`（UI/API公開値変更時）
- `skills/post-task-fit-report/SKILL.md`（作業報告時）

## SWEBOK KA別skillとagent

- Git管理上のKA索引は`docs/checklists/swebok/README.md`とする。チェック内容は同索引から各skillの`references/checklist.md`を参照する。
- AI agentは全taskで次の4 KAを適用候補として確認する。
  - `swebok-engineering-management`: スコープ、見積り、リスク、進捗、終結
  - `swebok-engineering-process`: ライフサイクル、工程定義、測定、改善
  - `swebok-configuration-management`: 変更統制、構成、build、release
  - `swebok-quality`: 品質計画、保証、レビュー、測定
- 作業内容に応じて次を追加する。

| 変更・工程 | Skill |
| --- | --- |
| 要求、acceptance、traceability | `swebok-requirements` |
| architecture、ADR、品質属性 | `swebok-architecture` |
| API、data、UI、component詳細設計 | `swebok-design` |
| source code、build、code review | `swebok-construction` |
| test計画、test code、検証、欠陥 | `swebok-testing` |
| observability、SLO、runbook、incident、release | `swebok-operations` |
| bug fix、migration、retirement、保守変更 | `swebok-maintenance` |
| threat、authn/authz、秘密、privacy、安全な実装 | `swebok-security` |
| cloud共通設計 | `swebok-cloud` |
| AWS | `swebok-aws` |
| Google Cloud | `swebok-google-cloud` |
| Azure | `swebok-azure` |
| OCI | `swebok-oci` |
| AI/ML/LLM製品・pipeline・評価 | `swebok-ai` |

各skillの`agents/openai.yaml`はUI metadata、`agents/swebok-*.toml`は委譲可能な専門agent定義である。親agentは委譲しても最終判定と証跡の完全性に責任を持つ。

## AI駆動セルフチェックgate

1. **計画前**: task、仕様、gap、変更対象を読み、適用KAとチェックIDを選ぶ。Critical/Highを先に扱い、期待する証跡と検証commandをtaskへ記録する。
2. **実装中**: AIが生成・変更したcontract、code、test、docsを同じ変更単位で保つ。判断を推測値で埋めず、関連KAへの波及を都度見直す。
3. **実装後**: 適用IDごとに`pass/fail/not-applicable/blocked`、直接証拠、理由、follow-upを記録する。`fail`は修正後に同じ検証を再実行する。
4. **検証後**: narrowからaggregateへ実行し、結果に応じてチェック判定を更新する。未実行、timeout、skipped、blocked、間接証拠を`pass`にしない。
5. **報告前**: 対象ID数と判定数を一致させ、未対応、外部gate、残余riskを`reports/working`に残す。適用IDに未解決`fail`があれば完了宣言しない。

記録形式:

```text
ID | status | evidence | rationale | follow-up
```

`not-applicable`には対象外と判断できるスコープ根拠を、`blocked`には不足するapproval、credential、環境、証跡を記載する。

## 作業手順

1. 仕様・gap・受け入れ条件を確認し、適用するKA別skillとチェックIDをtaskへ記録する。
2. 実装と同じ変更でcontract、test、docsを更新し、工程gateごとにセルフチェックする。
3. narrow checkからaggregate checkへ実行し、判定と証跡を更新する。
4. `reports/working`へ実行結果、KA別判定、未対応を記録する。
5. 目的単位でcommitし、検証済み変更をpublic GitHubへpushする。

## 安全性

- deploy、CDK bootstrap/destroy、production変更を実行しない。
- credential、API key、author identifier、本文をlog/public artifactへ含めない。
- 破壊的削除、履歴改変、force pushは事前確認を必要とする。
- `.workspace`はread-only参考資料として扱い、Gitへ含めない。
