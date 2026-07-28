# タイムスタンプ検索修正の実施記録

## 指示と判断

- 移植1206本の検索語がタイトル全文だったため、frontendの検索規則と一致しなかった。
- 移植scriptはNFKC正規化、小文字化、文字または数値以外での分割、空要素除去を同じ順序で実装した。
- `normalizationVersion`は`unicode-15.1/tokenizer-v1`のままとし、`latest.json`とreleaseの値一致を確認した。
- `--force`なしでは既存出力を保持して停止し、明示時だけ対象releaseを再構築する。
- 信頼度のenumは公開dataで保持し、画面だけ高・中・低へ写像した。

## 成果

- `20260729-001`を同じ入力から再生成した。1206件移植、21件除外、seed 3本を含む1209本である。
- 移植動画の空検索語は0件である。`第五人格`を含む検索語は3件である。
- seedの`rY4A7Lxk12Q`検索語は既存の4要素のまま保持した。

## 追加した回帰test

- 移植scriptのtestは代表タイトルを`第五人格`、本文、出演者名へ分割する期待値と、`force=True`再生成を確認する。
- frontend検索testは公開releaseのsearch indexを読み、`第五人格`で移植動画`-9KPzXpz8fI`が結果に入ることを確認する。
- 詳細画面testは信頼度`high`が画面で高と表示されることを確認する。

## 実行結果

| command | 結果 |
| --- | --- |
| `cd backend && uv run --locked pytest -q tests/test_import_archive_timestamps.py` | 合格: 2件 |
| `cd backend && uv run --locked python -m app.scripts.verify_contract` | 合格: 1209本 |
| `cd backend && uv run --locked pytest -q` | 合格: 65件 |
| `npm run typecheck -w frontend` | 合格 |
| `npm test -w frontend -- --run` | 合格: 26ファイル、77件 |
| `npm run build -w frontend` | 合格 |
| `task verify` | 失敗: 9 failed、51 passed。利用者実測でE2Eが失敗した。 |
| `git diff --check` | 合格 |

## KAセルフチェック

| ID | status | evidence | rationale | follow-up |
| --- | --- | --- | --- | --- |
| MGT-003 | pass | taskと本記録 | 成功基準と実測結果を対応付けた | なし |
| MGT-060 | pass | force手順、検索test | 上書きと回帰のriskを制御した | なし |
| PRC-001 | pass | script、data、frontend、test | 定義した修正工程を実行した | なし |
| SCM-001 | pass | runbook、release差分 | 再生成可能な構成を記録した | なし |
| QUA-001 | fail | 利用者実測の`task verify`: 9 failed、51 passed | E2E失敗が残っており集約品質検証は合格していない | E2E修正後に再実行する |
| REQ-102 | pass | 実release検索test、画面test | 要求の検索可能性と日本語表示を確認した | なし |
| DES-001 | pass | tokenizerと表示写像 | frontend規則に合わせた詳細設計を実装した | なし |
| CON-080 | pass | script、contract verifier | 再生成後の公開contractを検証した | なし |
| TST-701 | pass | 追加3種類のtest、全体検証 | 変換、検索、表示を回帰対象にした | なし |
| MNT-001 | pass | seed語保持、旧release保持 | 既存資産を維持して修正した | なし |

## 未対応と残余risk

- 先行作業と同様に、`provenance.completedAt`がない21件は生成時刻を推測できないため未移植である。
- deploy、外部approval、pushは実施していない。
