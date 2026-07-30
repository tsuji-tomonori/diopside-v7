# PR #4 E2E・画像レビュー

## 指示と対象

PR #4 `agent/frontend-ui-ux-polish` で E2E を実行し、主要画面をスクリーンショットで確認する。デザイン上の material かつ修正可能な指摘がなくなるまで、実装、再検証、再撮影を反復し、最終画像と結果を PR コメントへ掲載する。

正本は `docs/design/design-system.md`、`docs/spec`、添付のユースケース・ペルソナ・提供価値整理とした。公開 UI の Home、Search、検索条件、Detail、Insights、Saved を対象とし、backend contract、release data、deploy は変更していない。

## 初回画像レビュー

| 指摘 | 影響 | 対応 | 最終判定 |
| --- | --- | --- | --- |
| 375px Home の「すべての条件を見る」が2行に折り返す | Quick Search 見出しの視線を分断する | mobile actionを一行表示し、13pxへ調整 | 解消 |
| 1440×900 Search の条件パネルで主要CTAがviewport外へ切れる | 絞り込み完了操作を初見で発見しにくい | desktop panelの高さ・内部余白を調整 | 解消 |
| 一覧thumbnail取得失敗時に無地面だけが残る | video cardとしての識別性が弱い | 実データ取得失敗時のplay fallbackを追加 | 解消 |
| Detail thumbnail取得失敗時に壊れた画像iconが残る | heroの完成度と信頼感を損なう | 16:9 video面を維持し、失敗画像をDOMから除外 | 解消 |

最終画像では、情報階層、文字組み、配色、余白、操作状態、mobile overflow、44px target、固定navigation、filter sheet、thumbnail error stateを再確認し、materialかつ修正可能な指摘は残っていない。

## ペルソナ・ユースケース適合

| 対象 | 画像上の確認 |
| --- | --- |
| ライト視聴者 | Homeの主CTA、Quick Search、新着一覧が375pxの初期viewport内で連続し、1分以内の発見導線を妨げる折返し・被りがない |
| 常連ファン | Searchでkeyword、theme、duration、date、sort、recent searchを同じ作業面から利用できる |
| 切り抜き・まとめ作成者 | Detailのチャット件数、見どころ候補、頻出語が見出しとカードで区別され、YouTube時刻導線が明確 |
| 再訪利用 | Detailの「あとで見る」とSavedの保存件数・解除操作が一貫し、mobile bottom navigationから到達できる |

## 最終スクリーンショット

保存先: `reports/screenshots/20260731-pr4-ui-review/`

- `desktop-home-1440x900.png`
- `desktop-search-filter-1440x900.png`
- `desktop-detail-1440x900.png`
- `mobile-home-375x812.png`
- `mobile-search-filter-375x812.png`
- `mobile-detail-top-375x812.png`
- `mobile-detail-insights-375x812.png`
- `mobile-saved-375x812.png`

検証環境では外部のsample thumbnail domainへ接続できないため、最終画像では実装済みの取得失敗fallbackを明示的に再現した。画像が取得できる場合の`object-fit: cover`、16:9比率、layout寸法は変更していない。

## 実行結果

- `npm ci --cache /tmp/npm-cache-diopside-pr4`: 合格
- `UV_CACHE_DIR=/tmp/uv-cache-diopside-pr4 uv sync --locked`: 合格
- `npx playwright install chromium`: 失敗。Playwright CDNの証明書時刻不整合による502で、browser未導入
- npm registryから一時取得したheadless Chromiumを`PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH`へ指定: 解決
- 初回 `npm run test:e2e -w frontend`: desktop / mobile 20件合格
- 修正後 `npm run test:e2e -w frontend`: desktop / mobile 28件合格
- `npm run typecheck -w frontend`: 合格
- `npm test -w frontend`: 5 files / 16 tests合格
- `npm run build -w frontend`: 合格
- `UV_CACHE_DIR=/tmp/uv-cache-diopside-pr4 uv run --locked pytest`: 63件合格
- `git diff --check`: 合格

## SWEBOK判定

| ID | status | evidence | rationale | follow-up |
| --- | --- | --- | --- | --- |
| DES-096 | pass | 8枚のdesktop / mobile captureと2回の画像レビュー | 主要workflowと状態を実ブラウザで確認 | なし |
| DES-097 | pass | 320 / 375 / 1440px E2E、44px、overflow、focus検査 | responsiveとkeyboard要件を直接検証 | なし |
| CON-081 | pass | thumbnail failure、server failure、empty、境界E2E | 失敗・境界状態を製品UIで安全に表示 | なし |
| CON-090 | pass | clean npm install、uv sync、production build | lockfileから再現可能 | なし |
| CON-095 | pass | TypeScriptとVite build成功 | compile / bundle errorなし | なし |
| TST-408 | pass | desktop / mobile 28 E2E | route、interaction、error、responsiveを網羅 | なし |
| TST-605 | pass | 指摘修正後に同じcaptureとsuiteを再実行 | regressionと視覚差分を再判定 | なし |
| TST-805 | pass | branch、browser path、viewport、commandsを本記録へ保存 | 実行条件を再現可能 | なし |
| QUA-001 | pass | 自動testと画像レビューを別表で判定 | build成功をvisual passの代用にしていない | なし |
| QUA-034 | pass | taskの全受け入れ条件を個別確認 | 未実行・blocked項目なし | なし |

## fit・残余リスク

指示へのfitは100%。指定したE2E、capture、画像レビュー、改善反復、再検証、PRコメント用成果物を完了した。

production規模の動画件数に対する描画性能と、実配信環境から外部thumbnail domainへ到達できることは本taskの対象外であり、従来の残余リスクとして継続する。thumbnail接続不能時の表示崩れは今回解消した。
