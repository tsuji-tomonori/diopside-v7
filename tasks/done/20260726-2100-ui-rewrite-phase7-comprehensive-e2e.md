# UI全面書き直し Phase 7: 網羅E2Eとdesign正本適合の実測

状態: done

## 受入条件

- `/`、`/search`、`/saved`、`/history`、`/videos/:id`、`/terms`、`/privacy`、未定義route、`/admin`をdesktop/mobile Chromeで検証する。
- loading、通常、empty、retryable error、permanent/policy error、artifact未作成と0件の区別をbrowserで検証する。
- 検索・条件sheet/panel・slider・calendar・URL同期・responsive・a11y・keyboard完走をE2Eへ追加する。
- 全画面・状態のfull-page PNGを`reports/private/ui-verification-20260726/`へ保存し、Playwright実測を含む適合表を`reports/working/20260726-ui-design-conformance.md`へ残す。
- 指定6 commandをnarrowからaggregateへ実行し、未実行・timeout・skippedを合格扱いにしない。commit/push/deployはしない。
- Phase 7bでは、適合表に記載する全design項目を実要素の`getComputedStyle()`または`getBoundingClientRect()`で直接測定し、項目ごとに実測値・test名・判定を記録する。未測定は`未検証`とする。
- retryable/permanentの分類を保った日本語のエラー表示、未同意詳細のリンクリスト・操作条件、artifact未作成と0件の区別をE2EとPNGで検証する。
- 404の撮影名は`data-not-found`とし、artifact未作成はartifactFlagsがfalseのfixtureで別途撮影する。

## 適用SWEBOKセルフチェック（計画時）

| ID | status | evidence | rationale | follow-up |
| --- | --- | --- | --- | --- |
| MGT-003, MGT-060 | pass | 本taskの測定可能な受入条件、リスク | E2E件数、PNG、実測表、6 commandを完了基準に固定 | 実行値をreportへ更新 |
| PRC-001 | pass | 本taskの対象・対象外・検証順 | E2E、UI実装、撮影、適合記録を同一変更単位で管理 | 終結時に判定を再評価 |
| SCM-001 | pass | AGENTS.md、Taskfile.yml、対象path | Git管理対象とprivate証跡を区分し、commit禁止を適用 | diff/check結果を記録 |
| QUA-001 | pass | E2E/a11y/実測/PNG/aggregate検証 | 動作・見た目・工程品質を別の直接証跡で確認 | 集計結果を記録 |
| REQ-102, DES-001 | pass | ユーザー受入条件、design-system/wireframes/component-implementation | 要求をbrowser assertionと実測表へ追跡 | 項目別判定を記録 |
| CON-080 | pass | styles.css、design-measurements.spec.ts、Phase 7d typecheck/E2E | browser testコードを実行で検証した | UI変更時に再実行 |
| TST-001, TST-701, TST-801 | pass | 状態マトリクス、narrow→aggregate順 | 正常・異常・a11y・responsiveの終了基準を定義 | 実行統計を記録 |
| MNT-001 | pass | Phase 6後の回帰範囲 | 既存公開UIを保守変更として網羅回帰する | 残余riskを記録 |

## Phase 7b の追加セルフチェック（計画時）

| ID | status | evidence | rationale | follow-up |
| --- | --- | --- | --- | --- |
| REQ-102 | pass | Phase 7d reportの適合表（適合28、不適合0、未検証0） | 要件を測定test、UI文言、PNG名へ追跡した | UI変更時に再測定 |
| DES-001 | pass | design-system、wireframes、component-implementation、実要素測定E2E | token定義ではなく適用先renderを設計適合の根拠にした | 正本変更時に再測定 |
| CON-080 | pass | DataErrorState、DetailPage、Playwright、指定6 command | UI・contract状態・テストを同じ変更で維持した | UI変更時に再実行 |
| TST-701, TST-801 | pass | 単一E2E終了コード0（58 passed）、`task verify`終了コード0 | 正常、エラー、未作成、responsiveの直接証跡をaggregateまで確認した | UI変更時に再実行 |
| MNT-001 | pass | frontend 76 tests、backend 63 tests、E2E 58 passed、`task verify`終了コード0 | 表示修正が同意・error分類を変えないことを回帰検証した | UI変更時に指定6 commandを再実行 |

## Phase 7c の追加セルフチェック（計画時）

| ID | status | evidence | rationale | follow-up |
| --- | --- | --- | --- | --- |
| MGT-003, MGT-060 | pass | Phase 7d reportの指定6 command結果、`task verify`終了コード0 | 単一E2Eとtask verifyの終了コード0を確認して工程完了を証明した | 実行基盤変更時に再実行 |
| PRC-001, SCM-001, QUA-001 | pass | 正本、CSS、測定E2E、Taskfile、Phase 7d aggregate実行結果 | 設計・実装・測定を同じ変更単位で維持し、aggregate完走証跡を得た | Playwright更新時に再実行 |
| REQ-102, DES-001 | pass | wireframes v1.1、component-implementation v1.2、実要素測定 | 視覚40pxとhit 44pxを正本・実装・E2Eへ追跡した | 変更時は再測定 |
| CON-080 | pass | styles.css、design-measurements.spec.ts、typecheck | 疑似要素の視覚背景とLink操作領域を同じ変更で維持した | 変更時は再測定 |
| TST-701 | pass | 単一`npm run test:e2e`のdesktop 29件・mobile 29件、直接測定 | 全browserケースを単一commandで実行した | UI変更時に再実行 |
| TST-801 | pass | 単一E2E終了コード0（58 passed、44.3秒）、`task verify`終了コード0（E2E 58 passed、39.8秒） | 全体commandの完走証跡を同一環境で取得した | UI変更時に指定6 commandを再実行 |

## Phase 7d の追加セルフチェック（計画時）

| ID | status | evidence | rationale | follow-up |
| --- | --- | --- | --- | --- |
| MGT-003, MGT-060, PRC-001, SCM-001, QUA-001, TST-801, MNT-001 | pass | `playwright.config.ts`、指定6 commandの終了コード0、Phase 7d report | WSL2の既定並列worker killをworker数の明示で回避し、単一E2Eとaggregate検証を完走した | UIまたはPlaywright変更時に再検証 |

## リスク

| リスク（原因→事象→影響） | 対応 |
| --- | --- |
| fixture routeのURLが契約と異なる→状態testが誤った画面を検証→回帰見逃し | browserの実ネットワークURLを確認してroute interceptionを限定する |
| CSS記述値だけで適合判定→実renderとの差→誤合格 | `boundingBox()`と`getComputedStyle()`の出力のみを実装値にする |
| 個別PNGが不足→状態の視覚証跡なし→受入不能 | 撮影一覧をscriptで定義し、生成後の枚数と名称をreportへ記録する |
