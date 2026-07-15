# リポジトリエージェント

正本はrepository rootの`AGENTS.md`。本ファイルは互換entry pointとする。

## Agent構成

- `agents/swebok-*.toml`: KA別の委譲可能な専門agent定義
- `skills/swebok-*/SKILL.md`: KA別のAI駆動作業手順
- `skills/swebok-*/references/checklist.md`: Excelから同期した判定基準
- `skills/swebok-*/agents/openai.yaml`: skillのUI metadata
- `docs/checklists/swebok/README.md`: 18 KAの対応表と件数

## 親agentの責務

- `tasks/`を起点に、適用KAとチェックIDを決める。
- 必要なら対応する`agents/swebok-*.toml`へ境界の明確な調査・レビューを委譲する。
- 委譲結果をそのまま合格扱いせず、正本と直接証拠を親agentが再確認する。
- 計画、実装、検証、報告の各gateで対象IDを再評価する。
- 未実行、timeout、skipped、blocked、間接証拠を`pass`にしない。
- `ID | status | evidence | rationale | follow-up`をtaskまたはreportに残す。

## 実行順

1. 仕様・要件との整合確認
2. `tasks/do`への受け入れ条件、適用KA、対象ID、期待証跡の登録
3. AIによる実装と同一変更内のcontract/test/docs更新
4. narrowからaggregateへの検証と対象IDの再判定
5. `reports/working`へのKA別結果、未対応、残余riskの記録

# ローカル制約

- 外部デプロイや本番変更は行わない。
- 破壊的変更は事前確認を必要とする。
