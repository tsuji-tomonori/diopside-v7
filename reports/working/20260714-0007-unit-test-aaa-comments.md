# 単体テストのAAAコメント統一

## 指示と対象要件

- 全単体テストへAAAパターンを適用する。
- 各テスト本体で `1. 初期化`、`2. テストの実行`、`3. アサーション` を明示する。
- 既存の日本語コメント方針を維持し、全量を修正する。

## 判断と非対象

- 対象はbackendのpytest 59関数、frontendのVitest 13ケース、infraのNode.js 5ケース、合計77ケースとした。
- Playwrightは単体テストではなく受け入れE2Eのため、AAA修正の対象外とした。ただし集約回帰検証では14件を実行した。
- Pythonでは `#`、TypeScriptとJavaScriptでは言語仕様に従い `//` で同一の3文言を記載した。
- 直接アサーションへ埋め込まれていた操作は、結果変数または実行用関数へ分離し、3区分が実コードを表すようにした。
- productionコード、公開API契約、UI表示値は変更していない。

## 実施内容と成果物

- `backend/tests` の全59テスト関数へ、3つのAAAコメントを順番どおり一度ずつ追加した。
- `frontend/src` の全13単体テストケースへ、3つのAAAコメントを順番どおり一度ずつ追加した。
- `infra/test` の全5単体テストケースへ、3つのAAAコメントを順番どおり一度ずつ追加した。
- `backend/tests/test_japanese_content.py` を拡張し、対象テストごとのAAAコメント欠落・重複・順序違反を検出するようにした。
- 件数監査でbackendの各マーカーが59件、frontend・infraの各マーカーが18件となり、対象数と一致することを確認した。

## 検証結果

- `uv run --locked pytest tests/test_japanese_content.py -q`: 1件合格。AAA回帰検査を含む。
- `uv run --locked ruff check tests`: 合格。
- `uv run --locked ruff format --check tests`: 12ファイルが整形済み。
- `uv run --locked pyright tests`: 0エラー。
- `uv run --locked pytest`: 63件合格。
- `npm run typecheck -w frontend`: 合格。
- `npm test -w frontend -- --run`: 13件合格。
- `npm test -w @diopside/infra`: 4件合格。
- `node --test test/plan.test.js`: 1件合格。
- `task verify`: 合格。workspace型検査、frontend 13件、infra 4件、backend 63件、build、生成drift、契約・費用・quota検証、CDK synth、Playwright 14件を含む。
- `task docs:check`: 合格。生成対象28ファイルが最新。
- `git diff --check`: 合格。

frontendの初回型検査では、AAA分離で作成した2つのfixture変数の配列型が `string[]` へ拡大されて失敗した。既存の `SearchCondition` 型を明示して修正し、同じ型検査と単体テストを再実行して合格した。backendの初回Pyrightでは空配列fixtureの要素型が不明として2件失敗したため、既存関数契約に沿う型注釈を追加し、再実行して合格した。これらの初回失敗は合格として数えていない。

## 適合性と残余リスク

- 全77単体テストにAAAコメントが存在し、件数・重複・順序を回帰検査で継続確認できるため、指示へ適合する。
- infraの通常npmテストは4件だけを収集するため、残る `plan.test.js` 1件は個別実行して合格を確認した。
- deploy、CDK bootstrap/destroy、production変更、外部approval gateの判定は実施していない。

## Commit証跡

- 実装・検証: `389a291`
- `origin/main` へのpush: 完了
