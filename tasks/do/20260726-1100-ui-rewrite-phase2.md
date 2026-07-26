# UI全面書き直し Phase 2: design tokens / AppShell / 共通コンポーネント

状態: in_progress（Phase 2b 是正）

## 受け入れ条件

- `styles.css`、AppShell、指定14 UI component、VideoCard、DataErrorStateを設計正本に沿って実装し、既存公開契約を維持する。
- 各UI componentにunit testを追加し、variant/state、keyboard、ARIA、44px、disabledを検証する。
- `frontend`で typecheck → test → build を順に実行して成功させる。e2eはPhase 4対象として未実行記録にする。
- `reports/working/20260726-ui-rewrite-phase2.md`へ実装、実測結果、SWEBOK判定、follow-upを記録する。

## 適用SWEBOK（計画前選定）

| ID | 期待する証跡 | 検証方法 |
| --- | --- | --- |
| MGT-003, MGT-060 | scope/完了条件、リスク | 本task/report |
| PRC-013 | phase/gateと変更統制 | 本task/report |
| SCM-001 | 構成品目と変更範囲 | git diff/report |
| QUA-090, QUA-100 | review/verification境界 | report/test output |
| DES-018 | component DOM/a11y | source/unit tests |
| CON-001 | 再利用可能なcomponent実装 | source/typecheck |
| TST-701, TST-801 | component要件カバーと終了判定 | test output/report |
| MNT-043, MNT-100 | 既存contractの回帰範囲 | aggregate Vitest |

## リスク

| リスク | 確率 | 影響 | 対応 |
| --- | --- | --- | --- |
| 既存ページとのCSS/DOM互換性低下 | medium | high | 既存classを保ちaggregate test/typecheck/buildを実施 |
| 外部font/iconのCSP逸脱 | low | high | CDN・新依存を使わずfont stack/inline SVGに限定 |
| calendar/sheetのa11y不足 | medium | high | role/keyboard/focus trapをunit testで検証 |

## Phase 2b 是正計画

対象: `frontend/src/components/ui/*`、同 unit test、`frontend/src/styles.css`、Phase 2 report。

| ID | 期待する証跡 | 検証方法 |
| --- | --- | --- |
| MGT-003, MGT-060 | 是正範囲、完了条件、残余リスク | 本task/report |
| PRC-013 | Phase 2b の変更統制 | 本task/report |
| SCM-001 | 対象構成品目の差分 | git diff --check / report |
| QUA-090, QUA-100 | review 指摘の是正と検証結果 | source/test output |
| DES-018 | dialog、combobox、grid、slider の DOM/a11y | component source/unit tests |
| CON-001 | 読みやすい再利用 component | source/typecheck |
| TST-701, TST-801 | contract を覆う test と終了判定 | npm test/report |
| MNT-043, MNT-100 | 既存 DOM contract の回帰確認 | aggregate Vitest |

## Phase 2c 是正計画

対象は未是正の8 test files（`ConditionPanel`、`ConditionRow`、`EmptyState`、`Icon`、`LoadingState`、`SuggestList`、`VideoGridCard`、`VideoListItem`）に限定する。実装変更は、新しいcontract testが現行の公開挙動の欠陥を直接示した場合だけ最小限に行う。既に是正済みのtest filesは変更しない。

| ID | 期待する証跡 | 検証方法 |
| --- | --- | --- |
| MGT-003, MGT-060 | 8ファイル限定の範囲、完了条件、chat count表示リスク | 本task/report |
| PRC-013 | Phase 2cの変更統制 | 本task/report |
| SCM-001 | 対象testと必要時の実装差分 | `git diff --check` / report |
| QUA-090, QUA-100 | contract reviewと静的・動的検証 | source / typecheck / Vitest / build |
| DES-018 | component DOM、ARIA、表示状態のcontract | component source / unit tests |
| CON-001 | 最小の実装修正と型整合 | source / typecheck |
| TST-701, TST-801 | 8 component contractの網羅と終了判定 | targeted / aggregate Vitest |
| MNT-043, MNT-100 | 既存DOM contractを含む回帰確認 | aggregate Vitest |

| リスク | 対応 |
| --- | --- |
| artifactがない動画にchat countを0として表示する | `artifactFlags.chat=false`とcount有りの組合せをtestし、実装をprops補完なしに限定する |
| 既存の未是正test以外へ差分が広がる | 対象8ファイル以外のtestは変更せず、必要実装だけを差分確認する |
