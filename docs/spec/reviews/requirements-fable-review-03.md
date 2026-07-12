# diopside 要件定義 Fableレビュー3

- 実行日時: 2026-07-11 02:52 JST
- 対象: docs/spec/20.requirements-definition.md 1.0.1、docs/spec/30.tagging-requirements.md 1.0.0
- 比較: .workspace/diopside_use_cases_personas_value (1).md
- 前回: reviews/requirements-fable-review-02.md
- 判定: IMPROVEMENT_COMPLETE
- Blocking: 0件
- High: 0件
- Medium: 2件
- Low: 3件

## 前回指摘の解消

| 前回ID | 判定     | 根拠                                                             |
| ------ | -------- | ---------------------------------------------------------------- |
| N-H1   | RESOLVED | quota予約をchat collector開始前へ変更し、予定不明時8時間で算出   |
| N-H2   | RESOLVED | 30日期限まで7日以上／未満でquota停止可否を分離し、ACの両側を定義 |
| N-M1   | RESOLVED | AC-FE-07でGATE-001失効時のmostChat・派生表示縮退を検証           |
| N-L1   | RESOLVED | 1.0.1、レビュー状態、変更履歴を追加                              |
| N-L2   | RESOLVED | duplicate_contentをreason付き隔離へ統一                          |

## 非blocking指摘

| ID    | Severity | 対象                    | 指摘                                           | 対応                                   |
| ----- | -------- | ----------------------- | ---------------------------------------------- | -------------------------------------- |
| N3-M1 | Medium   | FR-OPS-007、FR-META-004 | quota 95%時に5分間隔live候補確認を止めるか曖昧 | 停止対象外とACへ明記                   |
| N3-M2 | Medium   | FR-OPS-007、FR-COM-004  | 12時間新着comment差分走査の扱いが未定義        | quota停止順へ明記                      |
| N3-L1 | Low      | FR-OPS-007              | quotaを使わない過去分析再生成がquota停止対象   | quota停止から除外しAWS費用側だけで扱う |
| N3-L2 | Low      | FR-OPS-008              | 配信予定時間の判明手段が曖昧                   | operator設定値だけを使用               |
| N3-L3 | Low      | 30.md                   | DR-TAG-006等のhigh pipe mediumが表を破壊       | 「highまたはmedium」へ修正             |

## 評価

- 受け入れ条件: 正常、異常、境界、権限、復旧、非機能を網羅。
- 実現可能性: 個人1名＋Codex、単一リリース、コスト最小、YouTube API/Policy制約内で実現可能。
- 指定文書: UC-01〜10、ペルソナA〜E、価値、成功指標、スコープ、原則の充足漏れなし。

## 終了判定

Blocking/Highが0件のため要件baselineとして受け入れ可能。非blocking 5件は1.0.2で反映する。

## レビュー後対応

| ID    | 状態     | 1.0.2での対応                                                                 |
| ----- | -------- | ----------------------------------------------------------------------------- |
| N3-M1 | RESOLVED | FR-OPS-007で5分間隔live候補確認を停止対象外とし、AC-QUOTA-01-Hを追加          |
| N3-M2 | RESOLVED | 12時間新着comment差分走査をquota停止順へ追加し、AC-QUOTA-01-Iを追加           |
| N3-L1 | RESOLVED | quota停止をYouTube API要求jobへ限定し、過去分析再生成をAWS費用停止側へ移動    |
| N3-L2 | RESOLVED | 予定配信時間はoperator設定値だけを使用し、YouTube APIから終了時刻を推定しない |
| N3-L3 | RESOLVED | DR-TAG-006とAC-TAG-01-19を「highまたはmedium」へ修正                          |
