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

## 作業手順

1. 仕様・gap・受け入れ条件を確認する。
2. 実装と同じ変更でcontract、test、docsを更新する。
3. narrow checkからaggregate checkへ実行する。
4. `reports/working`へ実行結果と未対応を記録する。
5. 目的単位でcommitし、検証済み変更をpublic GitHubへpushする。

## 安全性

- deploy、CDK bootstrap/destroy、production変更を実行しない。
- credential、API key、author identifier、本文をlog/public artifactへ含めない。
- 破壊的削除、履歴改変、force pushは事前確認を必要とする。
- `.workspace`はread-only参考資料として扱い、Gitへ含めない。
