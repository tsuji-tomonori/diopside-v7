# frontend UI/UX 改善

## 実施

- `docs/design/design-system.md` と公開画面仕様を正本に、雪白・菫色・明朝見出し・ゴシック操作文字へ視覚言語を統一。
- desktop の220px sidebar、mobile のheader / bottom navigation、skip link、現在地、focus-visibleを共通app shellへ整理。
- Home、Search、Video detail、Saved、History、404、empty / error / consent状態の情報階層と日本語copyを再設計。
- Searchを一覧中心の作業画面へ変更し、tag、配信時間、投稿日、並び順、active condition、mobile bottom sheet、reset / applyを実装。
- mobile filter sheetへEscape時のfocus returnとTab focus trapを実装。
- 日付、配信時間、件数の表示helperを追加し、video rowのscanabilityを改善。
- ワードクラウドをSVG内の環境依存fontからsemanticなDOM表示へ変更。
- 日本語fontをself-hostし、実行環境のfont有無で意匠が崩れないようにした。
- 動作確認用の公開controlと架空の表示値を除去。
- 320px overflow、44px navigation hit area、mobile filter操作のE2E回帰testを追加。
- 現行React実装に合わせてdesign systemのcomponent pathと実装差分を更新。

## visual QA

実ブラウザの初回captureを基準に、spacing、本文幅、mobile navigation、filter sheet、font、word cloudの表示崩れを修正し、再captureして比較した。

| viewport | 確認画面 / workflow | 結果 |
| --- | --- | --- |
| 1440 x 900 | Home、Search、sidebar、filter panel | 合格 |
| 375 x 812 | Home、Search、Detail、filter sheet、bottom navigation | 合格 |
| 320 x 568 | Home、主要navigation、横overflow | 合格 |

外部YouTube thumbnailは検証環境のnetwork制約で取得できない場合があるため、固定aspect ratioのplaceholder面でもlayout shiftやclippingがないことを確認した。

## 自動検証

- `npm run typecheck -w frontend`: 合格
- `npm test -w frontend`: 5 files / 16 tests 合格。App shellのaxe-core検査を含む。
- `npm run build -w frontend`: 合格
- `npm run test:e2e -w frontend`: desktop / mobile Chrome、20 tests 合格
- `git diff --check`: 合格

E2Eはsystem Chromeがない環境だったため、Playwright設定に任意のChromium executable pathを渡せる構成を追加し、検証時のみローカルChromiumを指定した。

## SWEBOK判定

| ID | 判定 | evidence |
| --- | --- | --- |
| DES-090 | pass | 全公開routeのdesktop / mobile巡回、既存routing維持 |
| DES-091 | pass | Search label、入力制約、query正規化、tag keyboard操作 |
| DES-093 | pass | loading / empty / error / consentと回復操作 |
| DES-096 | pass | 3 viewport、主要画面の初回・修正後browser capture |
| DES-097 | pass | 320 / 375 / 1440px、keyboard、axe-core、44px E2E |
| CON-081 | pass | empty、server failure、disabled機能、320px境界test |
| CON-090 | pass | lockfile更新、clean dependency install、production build |
| CON-095 | pass | TypeScript / Vite build warningなし |
| TST-408 | pass | desktop / mobile、公開route、server error、keyboard E2E |
| TST-605 | pass | visual defect修正後に同一suiteを再実行 |
| TST-805 | pass | branch、Chrome project、viewport、commandを記録 |
| QUA-001 | pass | visual QAと自動検証を分離して判定 |
| QUA-034 | pass | taskの受け入れ条件を個別に確認 |

## 残余リスク

- サンプルreleaseは3動画であり、production規模の件数に対する描画性能は未計測。
- 日本語font assetは合計約3.4MB。`font-display: swap`とbrowser cacheを利用するが、将来はsubset化の余地がある。
- backend、release contract、deploy構成は変更していない。
- icon libraryを新規追加せず、現在地navigationに必要な少数のaccessible inline SVGを共通component化した。
