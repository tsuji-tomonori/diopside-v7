# E2E修正と証跡訂正

状態: 実施中

## 受け入れ条件

- 2件の作業記録から根拠のない`task verify`合格と品質判定を訂正し、訂正をcommitする。
- 現在のdesign正本に照らしてE2E 9件を再現、分類、修正する。期待値は正しい現行仕様だけへ更新する。
- mobile横方向はみ出しをlayout側で修正し、click timeoutの根本原因を確認する。
- 初期表示の1209本読み込みの性能所見を実測で記録する。
- 最後に`task verify`を実行し、exit 0とE2E summaryを作業記録へ残す。pushしない。

## 計画時セルフチェック

| ID | status | evidence | rationale | follow-up |
| --- | --- | --- | --- | --- |
| MGT-003 | pass | 本taskの受け入れ条件 | 訂正、修正、性能、全体検証の完了基準を定義した | 実行結果で判定する |
| MGT-060 | pass | 虚偽の合格記録、E2E 9件、横はみ出し | 証跡信頼性とmobile操作不能を最優先riskにした | root causeを記録する |
| PRC-001 | pass | report、E2E、design正本 | 証跡訂正後に再現、修正、再検証の順で進める | なし |
| SCM-001 | pass | release、E2E期待値、report | 構成と検証基準を変更前に確認する | 差分をcommitする |
| QUA-001 | fail | 利用者実測: 9 failed、51 passed | E2E未解決のため集約検証は不合格である | 修正後に`task verify`を再実行する |
| REQ-102 | pass | 利用者の判断指針、design正本 | 正しい仕様と実測を区別して修正する | なし |
| DES-001 | pass | design system、wireframe、layout | mobile幅と操作性を詳細設計として確認する | なし |
| CON-080 | pass | frontend codeとE2E | 実装とtestを同じ変更単位で扱う | なし |
| TST-701 | pass | E2E 9件、全体検証 | 再現、原因分類、修正後の同test再実行を行う | なし |
| MNT-001 | pass | 既存release後の回帰修正 | 既存機能を削除せず修正する | なし |
