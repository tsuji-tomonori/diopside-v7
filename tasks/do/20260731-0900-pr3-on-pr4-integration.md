# PR #3をPR #4後のUIへ統合

状態: 実施中

## 目的

PR #4を取り込んだ`main`をPR #3へ通常mergeし、PR #2由来の旧UI実装を残さず、タイムスタンプ移植・検索修正・公開releaseだけを現行UIへ適応する。

## 対象

- release `20260729-001`と1209本の公開データ
- タイムスタンプの公開契約、import script、再生成runbook
- 現行Detail画面でのタイムスタンプ、信頼度、YouTube時刻リンク
- 実releaseを使う検索・契約・E2E
- PR #4後のdesktop/mobileスクリーンショット

## 対象外

- PR #2の代替AppShell、ページ、component、CSS、旧UI証跡
- production deploy、AWS resource変更
- `completedAt`がない21本への推測値追加

## 受け入れ条件

- [x] PR #3の最終treeが`main`との差分としてタイムスタンプ機能とその証跡だけを持つ。
- [x] `20260729-001`がseed 3本を含む1209本を保持し、公開禁止値を含まない。
- [x] `confidenceLevel`を高・中・低へ写像し、数値の確度を捏造しない。
- [x] itemsがない動画ではタイムスタンプカードを表示しない。
- [x] 移植動画の時刻リンク、信頼度、長い章題をdesktop/mobileで確認する。
- [x] `第五人格`検索が実releaseから3件を返す。
- [x] frontend narrow test、backend narrow test、contract verifier、build、desktop/mobile E2E、`task verify`相当の全commandが成功する。
- [ ] PR #4後のUIでスクリーンショットを再生成し、PR本文とコメントを更新する。

## リスク

| 原因 | 事象 | 影響 | 対応 |
| --- | --- | --- | --- |
| PR #3がPR #2をbaseとしていた | 旧UIのファイルが差分へ再混入する | #4のUIが上書きされる | 最終treeを`origin/main`基準で構築し、差分ファイルを監査する |
| 1209本のreleaseを初期読込する | E2E timeoutまたはmobile overflowが再発する | 検索・詳細が操作不能になる | 実releaseでE2Eと画像確認を行う |
| 生成元に確定日時がない | 推測日時を公開する | provenanceを捏造する | 21本を除外した既存方針を維持する |

## 適用SWEBOK

| ID | status | evidence | rationale | follow-up |
| --- | --- | --- | --- | --- |
| MGT-003 | pass | 本受け入れ条件 | 完了を成果物と検証結果で判定できる | 完了時に実測を記録する |
| MGT-060 | pass | 本リスク表 | 旧UI混入、性能、provenanceを具体化した | 検証後に再評価する |
| PRC-001 | pass | 目的、対象、対象外、実行順 | 統合工程の境界を明示した | なし |
| SCM-001 | pass | PR #4 merge、PR #3通常merge | 履歴改変せず構成変更を追跡する | 最終差分を監査する |
| QUA-001 | pass | verify相当command列、Playwright 34件 | Taskfileの全非deploy gateが成功した | remote CIを確認する |
| REQ-102 | pass | 既存taskと公開値制約 | タイムスタンプ公開要件を維持する | 公開JSONを検査する |
| DES-001 | pass | 現行Detail UI、画像5枚 | PR #4後のdesktop/mobileへ適合した | なし |
| CON-080 | pass | typecheck、unit、build、backend 65件 | 変更分岐の自動testが成功した | なし |
| TST-701 | pass | Playwright 34件 | 実release要求をdesktop/mobileで確認した | なし |
| MNT-001 | pass | 対象・対象外 | 既存releaseを保持する保守変更として限定した | 最終差分を確認する |
