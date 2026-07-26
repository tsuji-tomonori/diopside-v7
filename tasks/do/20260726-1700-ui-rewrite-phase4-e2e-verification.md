# UI全面書き直し Phase 4: E2E更新・全体検証・視覚証跡・完了記録

状態: completed_with_blocked_repository_gate（frontend受入・視覚証跡は完了。`task verify`の既存Phase 1〜3 test comment違反はreport参照）

## 対象と受入条件

- `frontend/e2e/public-routes.spec.ts`で既存公開route、query正規化、タグ候補keyboard選択を維持し、responsive、条件sheet/panel、件数CTA、calendar、keyboard完了経路、axe critical/serious 0件をbrowserで検証する。
- 通常E2Eに含めない撮影scriptで、指定14枚のfull-page PNGを`reports/private/ui-rewrite-20260726/`へ保存する。
- `frontend`のtypecheck/test/build/E2Eと、安全な`task verify`を実行し、実結果をreportへ記録する。失敗は修正後に同じcommandを再実行する。
- design正本との差は実装を修正するか文書version updateで理由を明示し、`GAP-FE-A11Y-001`を実証に合わせて更新する。
- commit/push/deploy、新規npm依存、`.workspace`変更、`reports/private`のGit追加はしない。

## 適用SWEBOKセルフチェック（計画時）

| ID | status | evidence | rationale | follow-up |
| --- | --- | --- | --- | --- |
| MGT-003, MGT-060 | pass | 本taskの受入条件・risk | 完了判定と失敗時の修正方針を明示 | 実行結果をreportへ更新 |
| PRC-001 | pass | 対象・対象外・検証順 | Phase 4の工程境界を定義 | reportへ実績化 |
| SCM-001 | pass | 対象path、非変更制約 | 構成品目と変更境界を固定 | diff checkを記録 |
| QUA-001 | pass | E2E/a11y/visual/documentationを分離 | 製品品質と工程品質を混同しない | 実行結果を記録 |
| REQ-102 | pass | 各受入条件とE2E/axe/PNG | すべて第三者が検証できる条件に対応 | test実行後に再評価 |
| DES-001 | pass | design-system/wireframes/component-implementation | target UIと実装・E2Eを追跡 | 差分を文書更新または修正 |
| CON-080 | pending | E2E/撮影script追加予定 | 変更されたbrowser検証コードを実行で確認 | E2E後に更新 |
| TST-001, TST-701, TST-801 | pass | 対象/除外とnarrow→aggregate順 | browser coverageと終了基準を定義 | 実施統計をreportへ記録 |

## リスク

| リスク（原因→事象→影響） | 対応 |
| --- | --- |
| Chromeまたはbackend起動不可→E2E/PNG取得不能→browser品質を証明できない | Playwright webServerの起動結果を確認し、未解消ならblockedとして記録する |
| UI targetのrole/label不一致→testが脆弱またはa11y欠陥を見逃す→回帰検出不能 | role/name中心のassertionとaxe実行を使い、必要なら実装をtargetへ修正する |
| visual撮影が通常suiteへ混入→通常検証が遅延/不安定→CI品質低下 | root `tools/`の独立scriptとして置き、通常E2Eから分離する |
