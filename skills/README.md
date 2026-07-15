# ローカルskill

rag-assistの運用規約から、GPT-5.6 `/goal`と重複しない実作業skillだけを移植する。

- `implementation-test-selector`: 変更範囲に応じた検証選択
- `repository-test-runner`: 実行・再実行・事実ベース報告
- `taskfile-command-runner`: Taskfile commandの安全な解決・実行
- `no-mock-product-ui`: production pathへの架空値混入防止
- `post-task-fit-report`: taskごとの作業・fit・未対応記録

## SWEBOK / Well-Architected KA別skill

`.workspace/swebok_checklist.xlsx`の18 KAを、AI agentが工程ごとに証跡ベースで自己検査できるskillへ同期する。全一覧、件数、対応agent、チェックリストへのリンクは`docs/checklists/swebok/README.md`を参照する。

- 各`skills/swebok-*/SKILL.md`: AI駆動の計画、実装、検証、報告gate
- 各`skills/swebok-*/references/checklist.md`: 元Excelの全チェック項目
- 各`skills/swebok-*/agents/openai.yaml`: skill UI metadata
- 各`agents/swebok-*.toml`: KA専門agent
- `tools/sync_swebok_ka.py`: Excelからの決定的な同期・完全一致検証

```bash
python3 tools/sync_swebok_ka.py --check
```
