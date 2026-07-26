# Phase 8b: PRコメントのキャプションを証拠と一致させる

状態: done

## 受け入れ条件

- `home-normal-mobile.png`の「本文を覆わない」は、375×812・最下部スクロール・`fullPage: false`の再現可能なPNGで直接示す。full-page PNGの固定要素に関する注記をREADMEへ加える。
- calendarを開いた状態のE2Eが、視覚セル40pxと日付buttonの操作hit領域44px以上を別々に直接測定し、適合表・PR本文／コメントの測定値を同期する。
- loadingの視覚と`role=status`のアクセシブルな状態通知を分けて記述し、通知はE2E test名を根拠にする。
- README、PRコメント、PR本文の各キャプションをPNGまたは指定E2Eの直接証拠に限定し、全16枚と追加PNGを目視再点検する。
- evidence PNG合計を2.5MB以内に保つ。`cd frontend && npm run test:e2e`、`cd backend && .venv/bin/python -m pytest -q`、`task verify`を実行し、実結果をreportへ記録する。
- `gh`、commit、push、PR操作は行わない。

## 計画時セルフチェック

| ID | status | evidence | rationale | follow-up |
| --- | --- | --- | --- | --- |
| MGT-003 | pass | 本taskの受け入れ条件 | PNG、測定、容量、指定検証を第三者が判定できる形で列挙した | 実測結果で終結判定する |
| MGT-060 | pass | 指摘された3不一致 | 原因（証拠と記述の乖離）→公開PRの誤認→レビュー品質低下をリスクとして記録した | 全キャプションを画像単位で再点検する |
| PRC-001 | pass | 対象3文書と撮影script | 対象は公開証拠・PR本文／コメント、実装UIの変更はcalendarの視覚hit分離に限定する | 対象外のPR投稿は行わない |
| SCM-001 | pass | Git管理対象のdocs/evidence、script、report | 生成PNGの再現手順をscriptに置き、private元画像と公開選定画像を区別する | diffと容量を確認する |
| QUA-001 | pass | PNGの視覚証拠、E2Eのprogrammatic証拠、報告 | 画像で確認できる内容と測定・a11yテストで確認する内容を混同しない | 同じ区別をPR本文／コメントへ反映する |
| REQ-102, DES-001 | pass | design-system 6.8、component-implementation RangeCalendar、README対応表 | calendarの40px/44px要件と公開証拠を追跡する | 開いた状態で直接測定する |
| CON-080, TST-701, TST-801 | pass | design-measurements E2E、指定3 command | 変更したcalendar視覚・hit領域とキャプション根拠をE2Eで検証する | narrowからaggregateへ実行し結果を記録する |

## 完了時セルフチェック

| ID | status | evidence | rationale | follow-up |
| --- | --- | --- | --- |
| MGT-003, MGT-060 | pass | 17 PNG・2.077MiB、`20260726-2355-pr-evidence-caption-alignment-fit.md` | 画像単位の根拠確認と容量・検証結果を完了基準へ対応付けた | PR更新時に再点検する |
| PRC-001, SCM-001, QUA-001 | pass | README、capture script、PR本文／コメント、`git diff --check` | 再現可能な公開証拠とprogrammatic証拠を分け、構成と品質記録を同期した | 親agentが公開前差分を確認する |
| REQ-102, DES-001, CON-080, TST-701, TST-801 | pass | calendar測定E2E、E2E 60 passed、backend 63 passed、`task verify` exit 0 | 正本の40px／44px要件を実装・直接測定・aggregate検証で確認した | UI変更時に同じ測定を実行する |
