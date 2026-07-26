# UI全面書き直し Phase 4 — E2E更新・全体検証・視覚証跡

## 指示と判断

Phase 1〜3のReact UIを対象に、公開routeの既存E2E意図を維持したまま、responsive、条件sheet/右panel、結果件数CTA、カレンダー、keyboard完了経路、axeを追加した。新規npm依存、公開API/data contract、backend/infra実装、commit/push/deployは対象外である。

通常suiteを遅くしないため、PNG撮影は`tools/capture-ui-rewrite-screenshots.mjs`へ分離した。scriptはbackend uvicornとViteをローカル起動し、Chromeで撮影後に停止する。`reports/private/`はignore済みであり、Gitの構成品目に含めない。

## 成果物

- `frontend/e2e/public-routes.spec.ts`: 既存7 caseを維持し、responsive、条件UIとfocus return、CTA、calendar、Tab/Arrow/Enter、axeを追加。両Playwright projectで各13、計26 caseとなった。
- `tools/capture-ui-rewrite-screenshots.mjs`: 通常E2E外の全画面PNG撮影script。
- `docs/design/design-system.md`: v1.2へ更新。旧Vue/path参照をReact実装へ正規化し、44px/calendar/focus returnの実証に合わせた。
- `docs/spec/25.gaps-and-decisions.md`: `GAP-FE-A11Y-001`のresolved根拠をPhase 4の実測値へ更新。screen reader／追加browser matrixはAC-NFR-02の外部検証として明記した。

## 実行commandと実結果

| command | 実結果 |
| --- | --- |
| `cd frontend && npm run typecheck` | exit 0。`tsc -p tsconfig.json --noEmit`成功。最終実行 2.4s。 |
| `cd frontend && npm test` | exit 0。Vitest `Test Files 25 passed (25)`、`Tests 69 passed (69)`、`Duration 2.70s`。 |
| `cd frontend && npm run build` | exit 0。Vite 6.4.3、150 modules transformed、`✓ built in 1.05s`。 |
| `cd frontend && npm run test:e2e`（初回） | exit 1。26中22 passed、calendar chip locatorのstrict一致とkeyboard Tab順序の4 failure（desktop/mobile各2）。実装を緩めず、exact accessible-name locatorとTabのみの到達ループに修正。 |
| `cd frontend && npm run test:e2e`（再実行・最終） | exit 0。`26 passed (10.7s)`。desktop-chrome 13/13、mobile-chrome 13/13。Playwright webServerがbackend uvicornとViteを起動した。 |
| `node tools/capture-ui-rewrite-screenshots.mjs` | exit 0。`Captured 14 screenshots in /home/t-tsuji/project/diopside-v7/reports/private/ui-rewrite-20260726`。19.9s。 |
| `task verify`（初回） | exit 1、27.7s。frontend typecheck/test/build、infra typecheck/test/build、ruff、pyright、mypy、architecture、API docsまでは成功。backend pytestは63件中62 passed/1 failed。`tests/test_japanese_content.py::test_repository_explanations_are_written_in_japanese`がPhase 1〜4で追加・変更したtest/documentの日本語規約違反を検出した。これは外部要因ではなく今回の変更による回帰（fail）である。 |
| `cd backend && UV_CACHE_DIR=/tmp/diopside-uv-cache uv run --locked pytest tests/test_japanese_content.py -q` | exit 1、0.9s。Phase 5開始時点で違反243件を確認した。Phase 1〜4の変更により持ち込んだ回帰（fail）であり、blockedではない。 |
| `task verify`（再実行） | exit 1、23.9s。初回後のE2Eコメント是正を含めて再実行した。frontend 25 files/69 tests、infra 4 tests、backend static checksは成功し、backend pytestは同じく62 passed/1 failed（243件の回帰）で停止。 |
| `task verify`（Phase 5最終） | exit 0。Phase 5で243件を是正後に再実行し、frontend 25 files/69 tests、infra 4 tests、backend pytest 63 passed、contract/cost/quota/infra synth、E2E 26/26を含む全工程が成功。 |
| `git diff --check` | exit 0。whitespace errorなし。 |

axeは`/`、`/search`、`/videos/rY4A7Lxk12Q`を各desktop/mobile projectで実行した。critical 0件、serious 0件（実行合計6 route viewport）。axe違反修正は不要だった。

## 視覚証跡

全て`fullPage: true`、Chrome、mobile=375×812、desktop=1280×900で撮影した。親agentが視覚確認した対象はhome mobile、search results desktop、condition sheet mobile、detail desktopであり、targetのnavigation切替、sticky条件行、sheet/panel、詳細レイアウトを確認した。

- `reports/private/ui-rewrite-20260726/home-mobile.png`
- `reports/private/ui-rewrite-20260726/home-desktop.png`
- `reports/private/ui-rewrite-20260726/search-empty-mobile.png`
- `reports/private/ui-rewrite-20260726/search-empty-desktop.png`
- `reports/private/ui-rewrite-20260726/search-results-mobile.png`
- `reports/private/ui-rewrite-20260726/search-results-desktop.png`
- `reports/private/ui-rewrite-20260726/condition-sheet-mobile.png`
- `reports/private/ui-rewrite-20260726/condition-panel-desktop.png`
- `reports/private/ui-rewrite-20260726/calendar-mobile.png`
- `reports/private/ui-rewrite-20260726/detail-mobile.png`
- `reports/private/ui-rewrite-20260726/detail-desktop.png`
- `reports/private/ui-rewrite-20260726/saved-empty-mobile.png`
- `reports/private/ui-rewrite-20260726/history-mobile.png`

## Design正本との整合

`wireframes.md`と`component-implementation.md`はPhase 1〜3の実装／E2E targetと差がなかった。`design-system.md`だけに旧Vue componentおよび`apps/web` token実体、calendar 40px gapの記述が残っていたため、実装を変更せず文書をv1.2へ更新した。RangeCalendarのbutton hit areaは実装CSSで44px、future disabled、2タップ範囲、sheet内差し替えをE2Eで直接確認済みである。

`GAP-FE-A11Y-001`はresolvedを維持し、根拠を古い一般記述からPhase 4のChrome E2E 26/26とaxe 0へ更新した。screen reader／追加browser matrixは本phaseで実施していないため、AC-NFR-02の外部検証として残る。

## SWEBOKセルフチェック

| ID | status | evidence | rationale | follow-up |
| --- | --- | --- | --- | --- |
| MGT-003 | pass | task受入条件、26/26 E2E、14 PNG、Phase 5の`task verify` exit 0、report | 完了基準を成果物と実行結果で第三者判定可能にした | screen reader matrixは別の外部検証として管理 |
| MGT-060 | pass | taskの原因→事象→影響risk表、初回E2E failure→修正→再実行 | browser/環境/selectorのリスクを具体化し処置した | screen reader matrixを次のAC検証で管理 |
| PRC-001 | pass | taskの対象・非対象・narrow→aggregate順、Phase 5是正task | Phase 4の工程境界と回帰是正を記録した | screen reader matrixは別taskで管理 |
| SCM-001 | pass | `git status --short`、`git diff --check` exit 0、private ignore確認 | Phase 4構成品目と非Git PNGを識別し、既存dirty worktreeを保持した | commit/pushは親agent判断 |
| QUA-001 | pass | E2E/axe/visualを製品品質、task/report/commandを工程品質として分離 | process遵守だけを製品品質の根拠にしていない | Phase 5のaggregate合格を確認済み |
| REQ-102 | pass | 各受入条件にE2E/axe/PNGまたはcommandを対応 | Phase 4要求はテスト可能な形で追跡した | screen reader requirementは外部gate |
| DES-001 | pass | design-system v1.2、wireframes/component implementation、E2E target | 設計のresponsive/条件/calendar/a11y仕様を実装検証へ対応付けた | target変更時に同じE2Eを更新 |
| CON-080 | pass | 追加E2E 26/26、撮影script exit 0、Phase 5の69 unit tests | 変更したbrowser検証コードと既存unit testを実行した | 追加browser/SRは別検証 |
| TST-001 | pass | task対象/対象外、実行順、project別件数 | E2E・axe・visualのテスト範囲を定義した | 追加browser/SRは対象外根拠を維持 |
| TST-701 | pass | responsive/条件/CTA/calendar/keyboard/axeのE2E case、PNG14枚 | Phase 4対象受入条件を直接テストまたはvisual evidenceでカバーした | visualは回帰検出を自動比較していない |
| TST-801 | pass | Phase 5の`task verify` exit 0、backend 63 passed、frontend 69 passed、E2E 26/26 | 回帰をfailとして是正後、全終了基準を直接実測した | screen reader matrixは本終了基準の外部検証として残す |

対象ID 11件、判定11件（pass 11）。

## 未対応・外部gate・残余risk

- `task verify`の未合格記録はPhase 5で訂正した。243件は「既存・本phase外」ではなく、Phase 1〜4で追加・変更したファイルによる回帰（fail）だった。Phase 5で是正し、最終実行はexit 0である。
- screen readerとChrome以外のbrowser matrixは未実施であり、`AC-NFR-02`の外部検証として残る。axe 0はそれらの代替ではない。
- 視覚証跡はprivate artifactであり、目視確認済みだがpixel-diff自動回帰検出は未導入。
- commit/push/deployは実行していない。
