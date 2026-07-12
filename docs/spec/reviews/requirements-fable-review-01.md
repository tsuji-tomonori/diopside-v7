# diopside 要件定義 Fableレビュー1

- 実行日時: 2026-07-11 02:26 JST
- 対象: docs/spec/20.requirements-definition.md
- 比較: .workspace/diopside_use_cases_personas_value (1).md
- 判定: NEEDS_IMPROVEMENT
- Blocking: 2件
- High: 4件
- Medium: 6件
- Low: 5件

## 指摘一覧

| ID  | Severity | 対象                                     | 指摘                                                                       | 対応方針                                                                     |
| --- | -------- | ---------------------------------------- | -------------------------------------------------------------------------- | ---------------------------------------------------------------------------- |
| B-1 | Blocking | DR-005、FR-AN-002、FR-AN-007、AC-AN-01-A | authorChannelId削除後はuniqueAuthorsApproxを再計算できず、再現性要件と矛盾 | video-scoped不可逆dedup tokenの保持条件と、削除前／削除後の再現性境界を定義  |
| B-2 | Blocking | FR-FE-011、AC-FE-06、AC-FE-01、KPI-001   | 同意前にブロックするAPI Dataの範囲と60秒測定範囲が曖昧                     | 全API Data表示を同意ウォールで遮断し、初回同意をKPI・ACの操作に含める        |
| H-1 | High     | AC-FE-01-B/C                             | Whenにない戻る操作・検索条件をThenで検証                                   | Whenへscroll・戻る操作を追加し、検索条件保持はAC-FE-02へ移動                 |
| H-2 | High     | 11.1、FR-OPS-007、15.4                   | 基準負荷のYouTube quota成立性と停止順序が未定義                            | quota gate、method別見積、進行中live chat優先、quota予約を追加               |
| H-3 | High     | UC-08、5.2、14.5                         | replay chat入力経路がないのにcovered判定                                   | 適法なoperator-provided replay inputの自動取込を追加し、非公式自動取得は禁止 |
| H-4 | High     | NFR-PERF-002、15.4                       | 1,000動画の性能試験がstandard 1,500動画未満                                | standard 1,500、peak 2,000へ基準を統一                                       |
| M-1 | Medium   | KPI-002                                  | 16件の分母が曖昧                                                           | 20query中16queryと明記                                                       |
| M-2 | Medium   | FR-AN-005/006、FR-FE-002/004             | GATE-001条件がwordcloud以外の派生機能へ波及していない                      | 全派生生成・sort・表示へgate条件を明記                                       |
| M-3 | Medium   | KPI-003、FR-COM-004                      | 24時間走査では処理時間込み24時間反映を満たせない                           | 新着走査を12時間間隔へ変更                                                   |
| M-4 | Medium   | GATE-002                                 | 「必要な投稿者許諾」の対象が曖昧                                           | channel運営者／所属事務所に限定し、投稿者個人は匿名化・削除窓口で対応        |
| M-5 | Medium   | 11.2、NFR-SEC-003                        | 1名運用に対して管理認証方式を固定しすぎ                                    | 必要なsecurity outcomeを固定し、cookieまたはIAM/SigV4等を設計裁量にする      |
| M-6 | Medium   | AC-AN-01-C/D                             | tombstone・unknownを入力件数に含むか曖昧                                   | 有効レコードと除外レコードの計数規則を明記                                   |
| L-1 | Low      | 3                                        | .workspaceの一時pathが長期正本                                             | user-specified原典とGit管理正規化版の役割を明記                              |
| L-2 | Low      | FR-CHAT-001                              | streamList利用不能時の挙動がない                                           | listへのfallbackを追加                                                       |
| L-3 | Low      | AC-FE-02-B                               | 100msの測定環境がない                                                      | NFR-PERF-001の端末条件を参照                                                 |
| L-4 | Low      | AC-DEV-01-D                              | fixture setupのWhenと外部承認assertionが不整合                             | 独立したgovernance ACへ移動                                                  |
| L-5 | Low      | KPI-006、AC-OPS-02                       | 復旧時間の起点が不一致                                                     | 検知→原因特定30分、redrive30分、合計60分へ統一                               |

## 評価要約

- 受け入れ条件: Given/When/Thenと原子的assertionは高水準だが、AC-FE-01とAC-AN-01に操作・計数の不整合がある。
- 実現可能性: 静的export、短時間Lambda、checkpoint、冪等性は妥当。YouTube quotaと1名運用の管理認証が主な補強点。
- 指定文書充足: UC-01〜07、09、10とペルソナ・価値・原則は充足。UC-08のreplay chat入力だけが未充足。

## 判定条件

Blocking 2件とHigh 4件を解消し、Medium・Lowの曖昧性を修正した後、同じ観点でFableレビュー2を実施する。
