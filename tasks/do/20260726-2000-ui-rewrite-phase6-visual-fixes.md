# UI全面書き直し Phase 6: 視覚レビュー不具合修正

状態: implementation_and_verification_completed（親agentの再視覚評価待ち）

## 対象と受入条件

- 表示専用の`frontend/src/lib/format.ts`へ日付、長さ、件数、タイムスタンプの整形を集約し、契約・Zod schemaを変更せずカード、詳細、派生情報の生値を置換する。
- 派生情報を日本語の利用者向け表現にし、artifact未作成と0件を区別し、同意・release modeのgateを維持する。
- PC条件パネルをviewport内の幅320pxに固定し、375pxのカレンダーヘッダーを一行化する。
- LengthSliderは仕様通り単一トラック・2つまみに戻し、下限≦上限、キーボード、aria-valuetext、44px hit areaを保持する。
- 375×812でフッターが下タブに隠れないことをbrowserで確認し、必要時に`h56 + safe-area`の余白を確保する。
- frontend typecheck/test/build/E2E、backend pytest、撮影scriptを実行し、`reports/working/20260726-ui-rewrite-phase6.md`へ実結果を記録する。

## 適用SWEBOKセルフチェック（計画時）

| ID | status | evidence | rationale | follow-up |
| --- | --- | --- | --- | --- |
| MGT-003, MGT-060 | pass | 本taskの受入条件・リスク | 6不具合と実測コマンドを完了基準へ固定 | 実結果をreportへ更新 |
| PRC-001 | pass | 対象・非対象・検証順 | 表示層、設計文書、テストを対象とし契約/schemaを除外 | reportへ実績化 |
| SCM-001 | pass | AGENTS.md、既存Taskfile、対象path | 既存の変更統制と非commit制約を適用 | diffを記録 |
| QUA-001 | pass | 単体・browser・build・backend検証の分離 | 製品UIと工程記録を別々に検証する | 実結果を記録 |
| REQ-102, DES-001 | pass | ユーザー指示、design-system、component-implementation | 要求をformat/UI/CSS/a11y testへ追跡する | 受入条件別に再評価 |
| CON-080 | pass | `format.test.ts`、カード・詳細・slider test、frontend 75 tests | 変更公開関数と重要分岐を単体テストした | report参照 |
| TST-001, TST-701, TST-801 | pass | 対象/除外、narrow→aggregate、6 command | 単体・browser・backend・視覚証跡を完了条件に対応 | 実施結果で更新 |
| MNT-001 | pass | Phase 4の視覚レビューで検出した回帰修正 | 保守変更の対象をfrontend UIと設計文書へ限定 | 残余riskをreportへ記録 |

## リスク

| リスク（原因→事象→影響） | 対応 |
| --- | --- |
| 二重range inputの重なり→thumb操作・focusが曖昧→条件誤設定 | 値に応じたz-indexと44px native input hit area、keyboard testを実装する |
| optional artifactを数値0へ置換→未作成の意味が消失→利用者誤認 | existenceとcountを別条件で表示し、既存未作成testを維持・拡張する |
| fixed panel/footerの寸法不整合→viewport外/本文隠れ→操作不能 | 1280/1440 desktop、375×812 mobileをPlaywright実測と再撮影で確認する |

## 実行結果

詳細は`reports/working/20260726-ui-rewrite-phase6.md`を参照。frontend typecheck、75 unit tests、build、26 E2E、backend 63 tests、14枚の再撮影はすべて合格した。親agentの最終視覚評価は外部review gateとして残す。
