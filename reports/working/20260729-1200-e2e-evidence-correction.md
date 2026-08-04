# E2E証跡訂正とmobile修正

## 結果

過去reportの`task verify`合格記載を訂正した。利用者実測の`9 failed, 51 passed`を正とする。

長い公開titleがmobile一覧gridの最小幅を拡大していた。カードgrid itemと本文flex itemの最小幅を0にし、実測文書幅を412pxへ戻した。条件sheetはdynamic viewport上端を明示し、focusのscrollを抑止した。

## 検証

`npm run typecheck -w frontend`: pass。

`npm test -w frontend -- --run`の実行結果: 26ファイル、77件が成功。

`npm run build -w frontend`: pass。

`task verify`は実行した。E2E開始前のfrontend 77 tests、backend 65 tests、contract、CDK synthまでpassした。実行環境がE2E開始後に出力channelを切断したため、exit codeと最終`N passed`行は未取得である。合格とは判定しない。

個別E2Eはdesktop検索query、desktop slider、desktop calendar、mobile色、mobile寸法、mobile calendar、mobile日付cell、mobile policyでpassした。

## KA

MGT-003 | pass | task記録 | 範囲と未完了を分離 | なし
PRC-001 | pass | narrowからaggregate | 工程順を維持 | 最終E2E再実行
SCM-001 | blocked | `.git/index.lock`がread-only | commit不能 | 書込可能環境でcommit
QUA-001 | blocked | `task verify`最終summary未取得 | aggregate合格証跡不足 | 最終run
REQ-102 | pass | 受入条件 | 実測欠陥を修正 | なし
DES-001 | pass | 412px実測 | mobile layoutを正本へ復帰 | なし
CON-080 | pass | typecheck | 変更整合 | なし
TST-701 | blocked | aggregate E2E summary未取得 | skipなし | 最終run
MNT-001 | pass | 根本原因修正 | 横overflowを修正 | なし

## 残余

最終`task verify`のexit 0とE2E summaryを取得していない。commitもsandboxの`.git` read-onlyにより未作成。
