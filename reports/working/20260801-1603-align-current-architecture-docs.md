# 現行アーキテクチャ文書・draw.io SVG整合

## 結果

現行repositoryのCDK／runtimeを基準に、README、正本文書、traceability、decision／gap、編集可能なdraw.io SVGを同期した。公開経路はCloudFront／S3、frontendはReact 19／Vite 6、非同期処理はEventBridge／SQS／Collector・Processor・Exporter Lambda、本文データはS3、control stateはDynamoDB、operator経路はIAM／STS AdminRole＋CLIとして統一した。

旧図にあったNuxt、API Gateway、FastAPI Lambda、Aurora DSQLを現行production経路から除外した。仕様中の`/admin/...`は将来HTTP adapter用の論理操作contractであり、現行CDKに独自HTTP endpointが存在することを意味しないと明記した。

本taskの文書／図変更scopeへのfitは100%。ただし、documentation verificationの合格をAWS deploy、post-deploy smoke、product acceptance、production gateの合格へ読み替えない。

## 主な変更

| 対象                                  | 変更内容                                                                                      |
| ------------------------------------- | --------------------------------------------------------------------------------------------- |
| `README.md`、`infra/README.md`        | 現行構成、図への導線、operator setup、未解決deployment／runtime gapを記載                     |
| `docs/design/architecture.drawio.svg` | 現行CDK／runtimeの4 view、凡例、open gap、DEC-DB-001を描画し、draw.io埋め込みmodelを保持      |
| `docs/spec/00`、`10`、`20`、`22`      | current／target、source path、React／Vite、public path、IAM／STS CLI、将来HTTP contractを同期 |
| `docs/spec/23`、`24`                  | product acceptanceとlocal implementation／documentation verificationを分離し、RTM状態を更新   |
| `docs/spec/25`                        | GAP-ARCH-001を再openし、6 child gapとDEC-DB-001を追加                                         |
| `docs/spec/30`、`31`                  | tag実装path、alias方針、snapshotとcurrent decisionの境界を同期                                |
| `docs/spec/21`                        | review scope、発見、反映、検証証拠、非合格範囲を記録                                          |

## 意思決定とopen gap

- DEC-DB-001: data body／public artifactはS3、job・quota・gate等のsmall control stateはDynamoDBに置き、Aurora DSQLは採用しない。全面DSQL、public dataの動的API化、curation領域だけの限定採用を比較し、現行access pattern、静的公開、移行負荷を根拠に判断した。複数operatorによる同時編集、任意JOIN、複数record ACID更新が主要機能になった場合だけ再検討する。
- GAP-ARCH-001: local moduleが存在することとAWS上で成立することを分離し、statusをopenへ戻した。
- child gap: frontend asset deploy／SPA rewrite、Lambda package、Processor raw write IAM、versioned S3削除・lifecycle、SQS visibility／batch、AdminRole output／AssumeRole runbookを個別管理した。
- GAP-PUB-001、GAP-AUTH-001、GAP-VERIFY-001等の既存product gapはopenのまま維持した。

## 検証結果

| 検証                                                                   | 結果                                                                                        |
| ---------------------------------------------------------------------- | ------------------------------------------------------------------------------------------- |
| Prettier 3.6.2 `--single-quote --no-semi --check`                      | 対象14 Markdown files合格                                                                   |
| local Markdown link検査                                                | 14 files、欠落0                                                                             |
| SVG／draw.io model検査                                                 | XML parse合格、embedded `mxfile`／`mxGraphModel`、55 cells、必須service labelを確認         |
| Inkscape render／目視                                                  | 1600×1100 PNG生成。4 section、node、arrow、凡例、open gap、DEC-DB-001を確認                 |
| stale fact scan                                                        | retrospectiveなreview logを除くcurrent-state文書で旧Nuxt／path／alias記述0件                |
| `npm run ci`                                                           | typecheck合格、frontend 5 files／16 tests合格、infra 4 tests合格、frontend／infra build合格 |
| `npm run synth -w @diopside/infra`                                     | 合格。CloudFormation生成のみでdeployなし                                                    |
| `UV_CACHE_DIR=/tmp/diopside-uv-cache uv run app-docs generate --check` | 28 files最新                                                                                |
| `UV_CACHE_DIR=/tmp/diopside-uv-cache uv run pytest -q`                 | 63 tests合格。日本語文書検査を含む                                                          |
| `git diff --check`                                                     | 合格                                                                                        |

最初の`uv run`はread-onlyなdefault cache path `/root/.cache/uv`を作成できず終了した。repositoryや依存関係の問題ではないため、`UV_CACHE_DIR=/tmp/diopside-uv-cache`を明示して同じ検証を再実行し、合格した。

## SWEBOK／WAF判定

| ID       | status  | evidence／判定理由                                                                  | follow-up                                                                |
| -------- | ------- | ----------------------------------------------------------------------------------- | ------------------------------------------------------------------------ |
| ARC-003  | pass    | 利用者、operator、YouTube、AWS serviceの境界とinteractionを図示                     | なし                                                                     |
| ARC-032  | pass    | solid／red dashed arrowと色の意味を図の凡例で定義                                   | なし                                                                     |
| ARC-060  | pass    | DEC-DB-001と既存decisionを識別子付きで記録                                          | なし                                                                     |
| ARC-090  | pass    | S3／DynamoDB／DSQLの選定理由、代替案、再検討条件を記録                              | なし                                                                     |
| REQ-201  | pass    | current／targetと管理CLI／将来HTTP contractの矛盾を解消                             | なし                                                                     |
| REQ-202  | pass    | CDK／runtime／正本文書／use-case資料の出典優先度を明記して同期                      | なし                                                                     |
| REQ-605  | pass    | draw.io SVGと自然言語のservice、data flow、gapが一致                                | なし                                                                     |
| REQ-1003 | pass    | review log、decision、gap、traceabilityへ変更影響を記録                             | なし                                                                     |
| REQ-1107 | pass    | RTMのimplementation／acceptance状態とopen gapを更新                                 | なし                                                                     |
| CLD-010  | partial | SQS／EventBridgeによる疎結合と冪等contractは存在                                    | 重複配信・timeoutを非本番AWSで検証                                       |
| CLD-017  | partial | role分離とAdminRole方針は記載                                                       | Processor IAM修正、AdminRole setup、権限棚卸しが未完了                   |
| CLD-042  | partial | bucketごとのlifecycleはCDKに存在                                                    | versioned objectの完全削除と旧public releaseのcurrent expiryを実装・検証 |
| CLD-047  | partial | CloudWatch logs／metrics／X-Ray／dashboardをCDKに定義                               | deploy後のcritical flow横断telemetryを確認                               |
| AWS-018  | partial | service roleは分離されresource scopeを持つ                                          | Processor raw write不足と未使用Collector権限を是正しIAM assertionを追加  |
| AWS-037  | pass    | SQS、EventBridge、shared DLQによる非同期境界をCDKと図で確認                         | runtime fault injectionは別task                                          |
| AWS-054  | pass    | data特性とaccess patternに応じてS3とDynamoDBを分離しDEC-DB-001に記録                | DSQL再検討条件成立時にdecision review                                    |
| AWS-075  | partial | raw／processed／configuration／public／access logにlifecycleを定義                  | version current／noncurrent／delete markerの期待を結合試験               |
| QUA-001  | pass    | process test、documentation verification、product acceptance、production gateを分離 | なし                                                                     |
| QUA-090  | pass    | taskで対象成果物、checklist-based review、実施時点を記録                            | なし                                                                     |
| QUA-904  | pass    | requirement、spec、AC、implementation、gapのRTMとreview logを更新                   | なし                                                                     |

## 残余リスク

- 図はrepository／CDK／runtimeのcurrent viewであり、AWSへdeploy済み、またはproduction acceptedとは主張しない。
- critical／highのdeployment・runtime gapは文書化しただけで解消していない。
- non-production環境で、収集→処理→公開→SPA直link→version完全削除と、operator AssumeRole→job／redrive／deletionを通す証拠が必要である。
- 外部policy、費用、quota、restore、securityのproduction gateは別の証拠と承認を必要とする。
