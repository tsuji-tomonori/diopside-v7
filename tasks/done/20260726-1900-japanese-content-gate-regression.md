# Phase 5: 日本語コンテンツgate回帰の是正

状態: done

## 対象と受け入れ条件

- `backend/tests/test_japanese_content.py`の規則に従い、リポジトリ全体の違反243件を0件にする。
- TypeScript/JavaScriptの英語のみ行コメントと、単体テストの直前説明・AAAマーカーを日本語の実際のテスト段階へ是正する。アサーションは削除しない。
- 対象Markdownの英語だけの自然言語を日本語化またはコード化し、識別子・commandの意味を損なわない。
- Phase 4 reportの`task verify`失敗を、Phase 1〜4変更が原因の回帰`fail`として訂正し、全7 commandの実測結果を記録する。
- 新規npm依存、commit、push、deployは行わない。

## 対象外・制約

- UIの公開挙動、API契約、依存関係、`.workspace`は変更しない。必要な既存違反だけはgateを0件にするため是正対象に含める。
- 未実行、skipped、timeoutは`pass`として記録しない。

## リスク

| 原因 → 事象 → 影響 | 対応 |
| --- | --- |
| AAAを機械挿入 → 実際の段階とコメントが乖離 → テスト意図を損なう | 各`it`を読んで初期化・実行・アサーションを対応付け、必要ならtestを分割する |
| Markdownの一律置換 → 識別子やcommandの意味が変わる → 文書の実用性低下 | 日本語の説明を補い、識別子とcommandはbacktickで保持する |
| gate対象外と思い込み → 既存違反が残る → aggregate verify失敗 | gateを再実行して0件を確認後、backend/frontend/Taskfileの順に全検証する |

## 適用SWEBOKセルフチェック（計画時）

| ID | status | evidence | rationale | follow-up |
| --- | --- | --- | --- | --- |
| MGT-003 | pass | 本taskの0件・7 command受入条件 | 完了を第三者が判定可能にした | 実測結果へ更新 |
| MGT-060 | pass | 上記リスク表 | 原因→事象→影響と対応を記録した | 実行時に再評価 |
| PRC-001 | pass | 対象・対象外・実施順 | 是正工程の境界を定義した | reportへ実績化 |
| SCM-001 | pass | 対象path、git差分確認 | 構成品目と変更境界を識別する | `git diff --check`を実行 |
| QUA-001 | pass | gate品質と工程記録を分離 | プロセス遵守を製品品質の証拠と混同しない | command結果を区別して記録 |
| REQ-102 | pass | test_japanese_contentと7 command | 各受入条件を実行可能な検証に対応付けた | 実測結果へ更新 |
| DES-001 | not-applicable | コメント・Markdownの規約是正のみ | UI/API/data詳細設計を変更しない | 設計資料の日本語表記だけを保持 |
| CON-080 | pass | 既存unit test構造と`npm test` | 既存テストの意図を保持し回帰を実行する | test削減がないことを確認 |
| TST-001 | pass | 対象・対象外、narrow→aggregate順 | テスト範囲と順序を定義した | 実行結果へ更新 |
| TST-701 | pass | 違反種別の集計とgate 0件 | 規約要求を網羅して測定する | 243件の内訳をreportへ記録 |
| TST-801 | pending | 実行前 | 終了基準は未検証 | 全7 command後に更新 |
| MNT-043 | pass | gate対象全体→backend→frontend→E2E→Taskfile | 影響範囲と回帰範囲を対応付けた | command結果へ更新 |
| MNT-100 | pending | 実行前 | 回帰実行結果が未取得 | reportへ実測を記録 |

## 実施結果

- 違反243件を0件へ是正した。内訳は英語のみ行コメント147件、単体テストの直前説明・AAA規則92件、Markdownの英語だけの自然言語4件である。
- 21個のunit testファイルで、各テストの実際の初期化・実行・アサーション段階を`// 1. 初期化`、`// 2. テストの実行`、`// 3. アサーション`へ置換した。49ケースに直前の日本語説明を置いた。アサーションの削除はない。
- `Icon.test.tsx`のparameterized testは、gateが`it.each`をブロック境界として認識しないため、同じ3寸法ケースを`for ... of`内の3テストに展開した。テスト総数は69から減らず、68から69へ増加している。
- Markdown 4行は日本語説明を補い、component名・状態名・command名を保持した。

## SWEBOKセルフチェック（完了時）

| ID | status | evidence | rationale | follow-up |
| --- | --- | --- | --- | --- |
| MGT-003 | pass | 0件、7 commandの実測結果 | 完了条件をすべて第三者が確認できる | なし |
| MGT-060 | pass | 本taskのrisk表、243→0の再実行 | 識別した回帰リスクを修正・再検証した | なし |
| PRC-001 | pass | 対象・対象外、narrow→aggregate実行 | 是正工程の境界を維持した | なし |
| SCM-001 | pass | `git status --short`、`git diff --check` exit 0 | 既存dirty worktreeを保持し、変更品目を識別した | commit/pushは実施しない |
| QUA-001 | pass | gate 0件、unit/E2E/aggregate結果、report | 規約品質・製品回帰・工程記録を別々の証跡で確認した | なし |
| REQ-102 | pass | 受入条件7項目とcommand結果 | すべての条件を実測で判定した | なし |
| DES-001 | not-applicable | コメント・Markdownのみ変更 | UI/API/data詳細設計を変更していない | なし |
| CON-080 | pass | `npm test` 69/69 | 既存unit testの意図とアサーションを保持した | なし |
| TST-001 | pass | 対象・対象外、実行順 | テスト範囲を定義して実行した | なし |
| TST-701 | pass | 243件の分類、gate 0件 | 規約要求を全種別で測定して解消した | なし |
| TST-801 | pass | 全7 command exit 0 | 終了条件を個別に実測した | なし |
| MNT-043 | pass | gate→backend→frontend→E2E→Taskfile | 影響範囲に対応する回帰を実施した | なし |
| MNT-100 | pass | backend 63、frontend 69、E2E 26、`task verify` exit 0 | 修正後の回帰結果を記録した | なし |

対象ID 13件、判定13件（pass 12、not-applicable 1、fail 0、blocked 0）。
