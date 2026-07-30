# PR #4 E2E・画像レビュー

## 指示

PR #4 の E2E を実行して主要画面のスクリーンショットを取得し、画像を確認してデザイン上の指摘がなくなるまで改善を反復する。最終画像と検証結果を PR コメントへ添付する。

## 正本

- `docs/design/design-system.md`
- `docs/spec/10.use-cases-personas-value.md`
- `docs/spec/20.requirements-definition.md`
- `docs/spec/22.system-specifications.md`
- 添付 `diopside_use_cases_personas_value (1).md`

## 受け入れ条件

- [x] PR #4 head で desktop / mobile の Playwright E2E が全件成功する。
- [x] Home、Search、検索条件、Detail、保存済み状態を 1440×900 と 375×812 の必要な viewport で撮影する。
- [x] ライト視聴者の「1分以内に発見」、常連ファンの断片検索、切り抜き作成者の見どころ把握、片手操作を画像からレビューする。
- [x] 情報階層、文字、余白、色、画像、操作状態、mobile overflow、44px target、固定 navigation の被りを確認する。
- [x] material かつ修正可能な指摘をすべて修正し、同じ画面を再撮影して解消を確認する。
- [x] typecheck、unit test、build、E2E、`git diff --check` が成功する。
- [x] 最終画像、確認 viewport、E2E 結果、画像レビュー結果を PR #4 のコメントへ掲載する。

## 適用 SWEBOK

| ID | 期待する証拠 |
| --- | --- |
| DES-096 | desktop / mobile の browser capture と再レビュー |
| DES-097 | 320 / 375 / 1440px、keyboard、44px、overflow 検証 |
| CON-081 | boundary、error、empty、状態遷移の E2E |
| CON-090 | clean install と production build |
| CON-095 | typecheck / build の警告・失敗なし |
| TST-408 | desktop / mobile の主要 workflow E2E |
| TST-605 | 指摘修正後に同じ suite と capture を再実行 |
| TST-805 | branch、browser、viewport、command の記録 |
| QUA-001 | 自動検証と目視画像レビューの分離 |
| QUA-034 | 受け入れ条件の個別判定 |

## 非対象

- backend、public contract、release data の仕様変更
- deploy、production data 変更
- 大量動画データでの性能測定
