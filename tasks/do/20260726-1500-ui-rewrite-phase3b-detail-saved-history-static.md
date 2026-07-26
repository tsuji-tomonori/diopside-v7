# UI全面書き直し Phase 3b: 詳細・保存・履歴・静的ページ

## 対象と受入条件

- `DetailPage`、`SavedPage`、`HistoryPage`、利用規約・プライバシー・Not Found と route を wireframe/component implementation に移植する。
- Detail の同意、releaseMode、GATE失効、artifact未作成、履歴更新、公開データエラーの既存契約を維持する。
- 保存・履歴は `VideoListItem` と `EmptyState` を使い、localStorageのversioned形式と失敗eventを変えない。
- 全routeの `main` と `h1`、shell navigation、skip link、`/admin` redirectを維持する。
- 詳細、保存、履歴、Not Found、静的ページの Vitest を追加し、typecheck、Vitest、buildを順に完走する。

## 非対象・リスク

- 公開contract/Zod schema/PublicDataContext/storage API、npm依存、`.workspace`、deploy/commit/pushは変更しない。
- responsiveの表示切替は既存CSS media queryに委ねる。browser E2Eは本タスクの明示必須commandではない。

## 実施順

1. 正本、既存page、storage/policy及びPhase 2 component契約を照合する。
2. pageとrouteを実装し、`VideoCard`参照を解消する。
3. pageごとのVitestを追加し、narrowからaggregate検証へ進む。
4. Phase 3 reportへ実装、実行結果、SWEBOK判定と残余リスクを記録する。

## 適用SWEBOKセルフチェック（計画時）

| ID | status | evidence | rationale | follow-up |
| --- | --- | --- | --- | --- |
| MGT-003 | pass | 本taskの受入条件・完了command | scopeと完了判断を成果物・検証で定義した | reportで実績化 |
| PRC-001 | pass | 対象・非対象・実施順 | lifecycleの適用範囲を固定した | 結果をreportへ記録 |
| SCM-001 | pass | 対象path、非変更contract、`.workspace`制約 | 構成品目と変更境界を識別した | diff確認 |
| QUA-001 | pass | UI品質と検証commandを分離 | 品質観点を混同しない | 実行結果を記録 |
| REQ-102 | pass | 画面別受入条件とpage test | 検証可能な要求へ追跡する | test結果で再評価 |
| DES-001 | pass | wireframe/component implementationのpage構造 | 要求からUI設計への追跡を確保 | 実装後に照合 |
| CON-080 | pending | page test追加予定 | 変更分岐をテストする | Vitest後に判定 |
| TST-001 | pass | page別対象とnarrow→aggregate順 | テスト範囲と手順を定義した | 実施統計をreportへ記録 |
| TST-801 | pending | 実行前 | 終了基準は未検証 | 全command後に判定 |
