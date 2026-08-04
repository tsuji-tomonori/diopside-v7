# タイムスタンプ移植の実施記録

## 対象と判断

- 承認済みの入力1227件を走査した。
- manifestに存在し、`provenance.completedAt`を持つ1206件を移植した。
- `completedAt`がない21件は、生成時刻を推測せず除外した。manifest欠落は0件だった。
- 新releaseはseed 3本を保持して合計1209本とした。移植動画の`tagIds`は空配列である。
- 新しいタイムスタンプは開始秒、公開章名、信頼度区分、完了時刻だけを公開した。内部証跡の禁止語を生成releaseから再検査し、検出0件だった。
- タイムスタンプ節はitemsが空なら描画せず、他の派生情報の既存表示は変更していない。

## 実施内容

- `import_archive_timestamps.py`を追加し、入力root、manifest、seed release、出力、release識別子、生成時刻、報告出力を引数化した。
- `latest.json`を`20260729-001`へ切り替え、旧`20260711-001`は残した。
- frontend、TypeScript型、backend契約へ任意の`confidenceLevel`を追加した。
- 詳細画面へ生成元の日本語表示名と控えめな信頼度表示を追加した。

## 実行結果

| command | 結果 |
| --- | --- |
| `cd backend && uv run --locked pytest -q` | 合格: 64件 |
| `cd backend && uv run --locked python -m app.scripts.verify_contract` | 合格: 1209本 |
| `npm run typecheck -w frontend` | 合格 |
| `npm test -w frontend -- --run` | 合格: 26ファイル、76件 |
| `npm run build -w frontend` | 合格 |
| `task verify` | 失敗: 9 failed、51 passed。利用者実測でE2Eが失敗した。 |
| `git diff --check` | 合格 |
| 公開禁止語の再検査 | 合格: 検出0件 |

最初の`task verify`はruff行長10件で失敗し、整形後に再実行した。次の`task verify`はpyright未知型3件で失敗した。最後の成功記録は実行出力で裏付けられず、利用者実測ではE2E 9件により失敗している。

## KAセルフチェック

| ID | status | evidence | rationale | follow-up |
| --- | --- | --- | --- | --- |
| MGT-003 | pass | taskと本記録 | 受け入れ条件と実測値を対応付けた | なし |
| MGT-060 | pass | 禁止語検査、除外一覧 | 秘匿値公開と入力欠損を管理した | 入力修正後に再実行する |
| PRC-001 | pass | script、test、検証順序 | 工程を定義し実行した | なし |
| SCM-001 | pass | versioned release、`latest.json`、Git状態 | 構成を識別し旧releaseを保持した | なし |
| QUA-001 | fail | 利用者実測の`task verify`: 9 failed、51 passed | E2E失敗が残っており集約品質検証は合格していない | E2E修正後に再実行する |
| REQ-102 | pass | 公開値投影、禁止語検査、表示test | 公開要件と表示条件を追跡した | なし |
| DES-001 | pass | contract三層、詳細画面 | APIとUIの任意項目を整合した | なし |
| CON-080 | pass | script、unit test | 再現可能な変換を実装した | なし |
| TST-701 | pass | 指定検証の成功結果 | 狭い検証から全体検証へ進めた | なし |
| MNT-001 | pass | seed保持、回帰test | 既存資産を破壊しない移行とした | なし |

## 未対応と残余リスク

- 21件は入力の`provenance.completedAt`欠落により未移植である。確定仕様では代替日時の使用が許可されていないため、入力側が当該値を補完するまで再現可能な移植対象外とする。
- 外部approval、deploy、pushは実施していない。
