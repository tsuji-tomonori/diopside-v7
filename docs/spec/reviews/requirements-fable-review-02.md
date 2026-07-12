# diopside 要件定義 Fableレビュー2

- 実行日時: 2026-07-11 02:37 JST
- 対象: docs/spec/20.requirements-definition.md
- 比較: .workspace/diopside_use_cases_personas_value (1).md
- 前回: reviews/requirements-fable-review-01.md
- 判定: NEEDS_IMPROVEMENT
- 前回指摘: 17件すべてRESOLVED
- 新規High: 2件
- 新規Medium: 1件
- 新規Low: 2件

## 前回指摘の解消

| 前回ID   | 判定     | 根拠                                                                |
| -------- | -------- | ------------------------------------------------------------------- |
| B-1      | RESOLVED | video-scoped authorDedupToken、保持条件、削除優先、再現性境界を定義 |
| B-2      | RESOLVED | 全API Dataの同意ウォールと初回同意込み60秒KPIを定義                 |
| H-1      | RESOLVED | AC-FE-01の操作をThenと整合し、検索条件保持をAC-FE-02へ移動          |
| H-2      | RESOLVED | GATE-005、quota予約、停止順序、AC-QUOTA-01、method別証跡を追加      |
| H-3      | RESOLVED | replay chatの適法なoperator-provided inputとAC-ING-05を追加         |
| H-4      | RESOLVED | standard 1,500、peak 2,000動画へ性能基準を統一                      |
| M-1〜M-6 | RESOLVED | KPI分母、gate波及、12時間走査、許諾対象、認証裁量、計数規則を修正   |
| L-1〜L-5 | RESOLVED | source役割、fallback、測定端末、governance AC、復旧起点を修正       |

## 新規指摘

| ID   | Severity | 対象                                  | 指摘                                                              | 対応方針                                              |
| ---- | -------- | ------------------------------------- | ----------------------------------------------------------------- | ----------------------------------------------------- |
| N-H1 | High     | FR-OPS-008、AC-QUOTA-01-B             | 予告なしliveでは開始前quota予約が不可能                           | chat collector開始前へ変更し、予定不明時は8時間で計算 |
| N-H2 | High     | FR-OPS-007、FR-COM-004、AC-QUOTA-01-D | quota 95%時にコメント全件再走査を停止しつつ30日確認を継続する矛盾 | compliance期限まで7日以上／未満で停止可否を分ける     |
| N-M1 | Medium   | FR-FE-002、004                        | GATE-001失効時のUI縮退を検証するACがない                          | AC-FE-07を追加                                        |
| N-L1 | Low      | 文書header                            | 版・状態・変更履歴がレビュー反映を追跡できない                    | 0.3.0と変更履歴を追加                                 |
| N-L2 | Low      | AC-ING-05-E                           | 重複hashだけ「隔離」でなく「処理されない」                        | reason付き隔離・正規化対象外へ統一                    |

## 評価要約

- 受け入れ条件: 正常、異常、境界、権限、復旧、非機能を概ね網羅。残る穴はquota条件2件とgate失効UI。
- 実現可能性: 静的export、短時間Lambda、quota gate、Policy対応は妥当。指摘は文言の精緻化で解消可能。
- 指定文書充足: UC-01〜10、ペルソナA〜E、価値、成功指標、スコープ、原則を充足。UC-08 replay chatも解消済み。

## 次回条件

新規5件を修正し、Fableレビュー3でBlocking/Highがないことを確認する。
