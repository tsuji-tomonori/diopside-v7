# ローカルskill

rag-assistの運用規約から、GPT-5.6 `/goal`と重複しない実作業skillだけを移植する。

- `implementation-test-selector`: 変更範囲に応じた検証選択
- `repository-test-runner`: 実行・再実行・事実ベース報告
- `taskfile-command-runner`: Taskfile commandの安全な解決・実行
- `no-mock-product-ui`: production pathへの架空値混入防止
- `post-task-fit-report`: taskごとの作業・fit・未対応記録
