# frontend UI/UX 改善

状態: completed

## 目的

`docs/design/design-system.md` と `docs/spec/22.system-specifications.md` を正本として、公開フロントエンドの見た目・情報階層・操作性・レスポンシブ・アクセシビリティを一貫した製品品質へ引き上げる。

## 対象

- 公開 app shell とモバイル下部ナビゲーション
- Home、Search、Video detail、Saved、History、policy/error/empty 状態
- 共通 token、button、chip、card、section、form、feedback
- desktop Chrome と mobile Chrome の主要フロー
- 変更に対応する component test / E2E

## 非対象

- backend、public release contract、検索アルゴリズムの変更
- AWS deploy、production data、外部 gate の変更
- 正本とは異なる新しいデザインシステムの導入
- 架空の件数、動画、タグ、操作の追加

## デザイン契約

- 視覚: 雪白の静かな面に菫色を唯一のアクセントとして使い、明朝は画面見出しだけ、操作はゴシックで統一する。
- 階層: 各画面は eyebrow → 明確な日本語見出し → 目的を一文 → 作業面の順にする。Home は検索導線と新着を最優先にする。
- コンテナ: mobile は左右16pxの単一カラム、desktop は220px sidebarと最大960pxの本文。動画一覧は読みやすいリストを基本とする。
- component: navigation、button、chip、video row、empty/error、field、section headerを共通表現に寄せる。
- interaction: hover / focus-visible / active / selected / disabled / loading / empty / error / successを区別し、44px以上の操作領域を守る。
- responsive: 320px / 375px で横overflowを出さず、下部ナビが内容を覆わない。768px以上はside navigationへ切り替える。
- motion: 状態フィードバックのみに限定し、`prefers-reduced-motion`を尊重する。

## 受け入れ条件

- [x] 正本のtoken、画面順序、mobile/desktop navigationへ適合する。
- [x] Home、Search、Detail、Saved、Historyの見出し・操作・empty/error状態が日本語で一貫する。
- [x] 製品UIから動作確認用操作、架空値、dead controlが除去される。
- [x] desktop 1440x900、mobile 375x812、mobile 320x568で主要操作にoverflow・clipping・重なりがない。
- [x] keyboardでskip navigation、主要navigation、search、tag suggestion、保存操作を完了できる。
- [x] 主要controlのhit areaが44px以上で、focus-visibleとcurrent stateが視覚・programmaticに分かる。
- [x] browser screenshotで初回評価→修正後評価を行い、material mismatchを解消する。
- [x] frontend typecheck、Vitest、build、Playwright desktop/mobile、`git diff --check`が合格する。
- [x] 実行結果・SWEBOK判定・残余riskを`reports/working`へ記録する。

## 適用SWEBOKチェック

| ID | status | evidence | rationale | follow-up |
| --- | --- | --- | --- | --- |
| DES-090 | pass | `docs/spec/22.system-specifications.md`、E2E route巡回 | 全公開画面と遷移を維持した | なし |
| DES-091 | pass | Search入力、component/E2E | 入力のlabel・制約・errorを維持した | なし |
| DES-093 | pass | error/empty/policy UI、E2E | error時の回復操作を視覚化した | なし |
| DES-096 | pass | desktop/mobile screenshot、主要フロー | 実ブラウザで主要フローを評価した | なし |
| DES-097 | pass | 320/375/1440px、keyboard、axe | 対応viewportとa11yを直接検証した | なし |
| CON-081 | pass | Vitest/E2Eの境界・empty/error | 正常系・異常系を検証した | なし |
| CON-090 | pass | lockfile、clean build | build再現性を確認した | なし |
| CON-095 | pass | typecheck/build | frontend warningを残していない | なし |
| TST-408 | pass | desktop/mobile E2E、error route | 境界・異常系を自動検証した | なし |
| TST-605 | pass | 修正後の同一check再実行 | visual defect修正後に回帰確認した | なし |
| TST-805 | pass | branch、Chrome project、viewport | 対象版と環境を記録した | なし |
| QUA-001 | pass | visual reviewと自動checkを分離記録 | build成功だけで完了判定していない | なし |
| QUA-034 | pass | 上記受け入れ条件 | 客観的完了条件で判定した | なし |

## 検証コマンド

- `npm run typecheck -w frontend`
- `npm test -w frontend`
- `npm run build -w frontend`
- `npm run test:e2e -w frontend`
- `git diff --check`

## リスク

- 外部Web fontを実行時依存にするとoffline/slow networkで崩れるため、system fallbackを含める。
- サンプルreleaseは3動画であり、大量件数時の密度は構造・CSS・自動testから評価し、production規模の性能保証とは分離する。
- GitHub CLIは環境にないため、push/PRはGitHub Apps APIを用いる。
