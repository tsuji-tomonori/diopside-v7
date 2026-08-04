# PR #3のPR #4後UIへの統合記録

## 結果

- PR #4はhead `4dbdbc7`、verify成功を確認後、squash commit `356d919`として`main`へmergeした。
- PR #3へ`main`を通常mergeし、履歴改変やforce pushを使わずに統合するtreeを作成した。
- PR #2由来の旧AppShell、UI component、CSS、E2E証跡は採用せず、release、公開契約、import script、検索修正、タイムスタンプ表示だけをPR #4のUIへ適応した。
- release `20260729-001`はseed 3本と移植1206本の合計1209本を保持する。入力1227件のうち`provenance.completedAt`がない21件は推測せず移植対象外とした。
- 現行Detail UIではタイムスタンプがある場合だけ見どころ候補カードを表示し、信頼度を高・中・低で示す。ない場合はカード自体を表示しない。

## 差分監査

- 最終treeは`origin/main`基準で1245 path。内訳の大半はversioned releaseの1209 video JSONとwordcloud資産である。
- PR #2と重なり得る画面差分は`DetailPage.tsx`、`styles.css`、`public-routes.spec.ts`の3 pathだけを現行UI向けに実装した。
- `components/ui`、`comprehensive-coverage.spec.ts`、`design-measurements.spec.ts`、`ui-rewrite-20260726`証跡は最終差分に含めていない。
- `frontend/package.json`、`package-lock.json`、`frontend/playwright.config.ts`は`main`から変更していない。

## 検証

環境にGo Taskの`task` binaryがなかったため、`Taskfile.yml`の`verify`を読み、同一の非deploy command列を順番どおり直接実行した。

| 検証 | 結果 |
| --- | --- |
| frontend typecheck | pass |
| frontend Vitest | pass: 5 files、17 tests |
| frontend production build | pass |
| backend Ruff check / format | pass |
| backend Pyright / mypy | pass |
| architecture / generated docs check | pass |
| backend pytest | pass: 65 tests |
| public contract verifier | pass: release `20260729-001`、1209 videos |
| 公開禁止field検査 | pass: 0件 |
| cost / quota verifier | pass |
| infra typecheck / 4 tests / plan / CDK synth | pass、deployなし |
| Playwright desktop + mobile | pass: 34 tests |
| `git diff --check origin/main` | pass |

## E2Eと画像証跡

- `-9FORuRCQ8k`で章題、信頼度、時刻つきYouTube link、provenanceを確認した。
- `G2m9kPq8xJv`でタイムスタンプカードを描画しないことを確認した。
- `第五人格`の実release検索で3件を確認した。
- `docs/evidence/timestamps-20260729`の5画像をPR #4後UIで再生成した。
- 撮影時はfont loading完了を待ち、タイムスタンプなし画面を独立した初回navigationとして撮影した。これにより遷移直後のfont swapを証跡へ混入させていない。

## 残余リスク

- `completedAt`欠落21件は引き続き未移植である。入力側に確定値が追加されるまで推測しない。
- release全体の追加量が大きいため、PR reviewではUI差分とversioned data差分を分けて確認する。
- 外部サムネイル通信はE2E画像では遮断した。fallbackと操作導線は確認済みだが、外部サービス自体の可用性は本変更の保証対象外である。

## KAセルフチェック

| ID | status | evidence | rationale | follow-up |
| --- | --- | --- | --- | --- |
| MGT-003 | pass | task、検証表 | 完了条件を実測へ対応付けた | remote CIを確認する |
| MGT-060 | pass | 差分監査、残余リスク | 旧UI混入、入力欠損、大容量差分を管理した | 21件は入力更新待ち |
| PRC-001 | pass | #4 merge、通常merge、narrowからaggregate | 統合順と検証順を維持した | なし |
| SCM-001 | pass | merge parent、差分監査 | 履歴改変せずbase変更可能なtreeにした | branchを通常pushする |
| QUA-001 | pass | verify相当command列、exit 0 | 全品質gateをskipなしで完走した | remote CIを確認する |
| REQ-102 | pass | 1209本、禁止field 0件、表示条件 | 公開要件を実装とE2Eへ追跡した | なし |
| DES-001 | pass | PR #4 UI画像5枚 | 現行desktop/mobile設計へ適合した | なし |
| CON-080 | pass | 型検査、unit、build | 契約から表示まで整合した | なし |
| TST-701 | pass | Playwright 34件 | 実releaseの要求分岐をdesktop/mobileで確認した | なし |
| MNT-001 | pass | seed保持、旧UI除外 | 既存UIを上書きしない保守統合とした | なし |
