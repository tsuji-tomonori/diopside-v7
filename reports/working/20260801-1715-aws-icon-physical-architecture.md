# AWSアイコン物理構成図の品質改善

## 結果

`docs/design/architecture.drawio.svg`を、AWS Architecture Iconsベースの現行物理構成図へ更新した。通常のSVG表示とdraw.io再編集用の非圧縮modelを同居させ、現行CDK／runtime、正本文書、open gapを同じ図で区別した。

図成果物に定義した受け入れ条件はすべて合格した。connector 19本の相互交差・重複は0件、接続先以外の26 obstacle貫通は0件、必須service 15件と必須resource 19件の不足は0件、legacy／未実装serviceの混入は0件である。AWS deploy、post-deploy smoke、production acceptanceは行っておらず、図中の赤破線gapも解消していない。

## 成果物

| 対象                                   | 内容                                                                 |
| -------------------------------------- | -------------------------------------------------------------------- |
| `docs/design/architecture.drawio.svg`  | AWS icon、editable draw.io model、current／gap凡例を持つ物理構成図   |
| `docs/design/THIRD_PARTY_NOTICES.md`   | `aws-icons` 3.3.0の取得元、copyright、MIT license全文                |
| `tools/verify_architecture_diagram.py` | XML、draw.io model、inventory、禁止語、vector参照、connector幾何検査 |
| `Taskfile.yml`                         | `architecture:verify`と全体`verify`への組み込み                      |
| `.github/workflows/verify.yml`         | diagram verifierと専用Python lintをPR／main CIへ組み込み             |

## 現行構成との照合

| 領域       | 図の表現                                                                                    | 実装根拠                                                                                  |
| ---------- | ------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------- |
| 公開配信   | Public user → Amazon CloudFront Distribution → private／versioned Amazon S3 `PublicData`    | `Distribution`、OAC、HTTPS redirect、security header、access log                          |
| 収集処理   | Amazon EventBridgeの3 scheduled rule → `Collector` Lambda → `JobQueue` → `Processor` Lambda | `MetadataSchedule`、`MonthlyFullRefreshSchedule`、`LiveStartSchedule`                     |
| 外部取得   | `Processor` → YouTube Data API v3                                                           | metadata、comment、live chatのruntime job                                                 |
| 公開処理   | Amazon EventBridgeの2 scheduled rule →単一`Exporter` Lambda ↔ `ExportQueue`                | `ExportSchedule`、`OperationsHeartbeatSchedule`、同じExporterへのSQS event source mapping |
| 再試行     | `JobQueue`／`ExportQueue` →共有`JobDeadLetterQueue`                                         | 両queueの`maxReceiveCount: 4`                                                             |
| データ     | Amazon S3 `Raw`／`Processed`／`Configuration`、Amazon DynamoDB `ControlTable`               | 本文／成果物はS3、小さいcontrol stateはDynamoDB                                           |
| 秘密情報   | AWS Secrets Manager `YouTubeApiKey`／`PseudonymSecret`                                      | CDK secretとworker role grant                                                             |
| 監視       | AWS X-Ray、Amazon S3 `AccessLogs`、Amazon CloudWatch dashboard＋4 alarms                    | 3 Lambdaのactive tracing、400日log、`OperationsDashboard`                                 |
| 通知／費用 | Amazon SNS `OperationsAlerts`、任意email、AWS Budgets `MonthlyCostBudget`                   | alarm action、forecast 80% notification                                                   |
| 管理       | Operator → AWS CLI → AWS IAM／AWS STS `AdminRole` → AWS service API                         | 現行は管理Web/APIではなくAssumeRoleするCLI                                                |
| 未解決     | frontend deploy／default root／SPA rewriteとproduction blockerを赤破線表示                  | `GAP-WEB-DEPLOY-001`、`GAP-ARCH-001` child gap                                            |

`Amazon EventBridge Scheduler`は使用していない。CDKが生成する物理resourceは`AWS::Events::Rule`であるため、図では`Amazon EventBridge`のscheduled ruleとした。Nuxt、API Gateway、FastAPI Lambda、Aurora DSQL、CloudFront Functionsは現行resourceから除外した。

## レンダリングレビューループ

|  回 | 指摘                                                                                       | 是正                                                             | 再判定                       |
| --: | ------------------------------------------------------------------------------------------ | ---------------------------------------------------------------- | ---------------------------- |
|   0 | 既存図はgeneric box中心で、AWS iconによる物理resource判別性が不足                          | AWS公式配色のvector iconと4つの物理zoneへ再構成                  | 次回確認                     |
|   1 | `<use href>`がInkscapeで解決されずiconが消え、長いservice名が衝突                          | internal `xlink:href`、vector symbol実体、公式短縮名、改行を採用 | icon表示合格、余白は継続修正 |
|   2 | Exporter／ExportQueue間が短くarrowheadが接近し、Cloud label配色と一部注記が過密            | node間隔、両矢印、CSS fill、注記行、英字labelへ修正              | full render合格              |
|   3 | `PublicData`／`AccessLogs`が別zoneと重複表示され、CollectorのControlTable access説明が不足 | S3 bucketを物理的に一度だけ表示し、runtime data access表を補完   | content review合格           |
|   4 | 2800×1987と1400×993で最終確認                                                              | 追加指摘なし                                                     | 合格                         |

## 品質メトリクス

| 指標                        |            合格値 |                          実測 | 判定 |
| --------------------------- | ----------------: | ----------------------------: | ---- |
| 必須AWS service不足         |                 0 |                         0／15 | pass |
| 必須physical resource不足   |                 0 |                         0／19 | pass |
| legacy／未実装service混入   |                 0 |                             0 | pass |
| connector交差・重複         |                 0 |              0／19 connectors | pass |
| 非接続obstacle貫通          |                 0 |               0／26 obstacles | pass |
| 外部image参照・raster image |                 0 |                             0 | pass |
| draw.io parse error         |                 0 | 0／124 XML elements、52 cells | pass |
| draw.io AWS4 shape参照      |            12以上 |                            42 | pass |
| 埋め込みAWS vector symbol   | 必須serviceを充足 |           15 symbols、27 uses | pass |
| 目視未解決指摘              |                 0 |                             0 | pass |

negative controlとして、禁止語`FastAPI`、PublicData貫通、connector重複を一時fixtureへ注入した。verifierは3件を検出して非0終了し、不正図を拒否した。

## 検証結果

| 検証                                           | 結果                                                               |
| ---------------------------------------------- | ------------------------------------------------------------------ |
| `python3 tools/verify_architecture_diagram.py` | pass、15 services／19 resources／19 connectors／26 obstacles       |
| Ruff lint／format                              | `tools/verify_architecture_diagram.py`合格                         |
| Prettier 3.6.2 `--single-quote`                | `Taskfile.yml`、GitHub Actions workflow合格                        |
| Inkscape render／目視                          | 2800×1987と1400×993でicon、label、connector、凡例、gapを確認       |
| `app-docs generate --check`                    | 28 generated files最新                                             |
| 文書対象test                                   | 3 tests合格                                                        |
| backend全test                                  | 63 tests合格                                                       |
| `npm run ci`                                   | typecheck、frontend 16 tests、infra 4 tests、両workspace build合格 |
| `npm run synth -w @diopside/infra`             | pass、CloudFormation生成のみでdeployなし                           |
| `git diff --check`                             | pass                                                               |

`python3 tools/sync_swebok_ka.py --check`は、read-only入力`.workspace/swebok_checklist.xlsx`がworkspaceに存在しないため実行できなかった。選定済みchecklist本文はrepository内Markdownから適用し、この外部fixture不足を図の合否へ読み替えていない。

## SWEBOK／WAF判定

`pass`は本taskの成果物で確認済み、`partial`はrepository定義のみで実AWS証拠がないか全project条件を満たさない、`n/a`はこのserverless構成に該当resourceがないことを表す。

| ID      | status  | evidence／判定理由                                                   | follow-up                                            |
| ------- | ------- | -------------------------------------------------------------------- | ---------------------------------------------------- |
| MGT-003 | pass    | 15個の受入条件と数値gateをtaskに定義                                 | なし                                                 |
| MGT-022 | pass    | diagram、verifier、license notice、CI gate、reportを成果物として特定 | なし                                                 |
| MGT-072 | pass    | machine check、render review、CDK test、aggregate testを計画・実行   | なし                                                 |
| MGT-092 | pass    | checkboxとtest結果に基づき進捗・完了を判定                           | なし                                                 |
| MGT-103 | pass    | `aws-icons` 3.3.0／MITのcopyrightとlicense全文を記録                 | なし                                                 |
| PRC-041 | pass    | 件数、算出対象、data sourceをverifierとtask tableに固定              | なし                                                 |
| PRC-053 | pass    | process側はreview loop、product側はgeometry／inventory／renderを測定 | なし                                                 |
| PRC-054 | pass    | 不合格時は同task内で是正して同じ検査を再実行                         | なし                                                 |
| PRC-086 | pass    | diagram、embedded model、CDK、runtime、gapのservice名を統一          | なし                                                 |
| PRC-091 | pass    | AWS service、draw.io、Inkscape、`aws-icons`の実在と名称を確認        | なし                                                 |
| SCM-020 | pass    | 管理対象SCIと格納pathをtask／reportへ列挙                            | なし                                                 |
| SCM-021 | pass    | diagram source、verifier、CI、notice、reportをGit管理対象に追加      | なし                                                 |
| SCM-026 | pass    | CDK→diagram→verifier→CIの依存・派生関係を記録                        | なし                                                 |
| SCM-048 | partial | PR CI gateは追加したがapproval数／conflict責任は本taskで未監査       | repository protectionを別途確認                      |
| QUA-034 | pass    | 不足・交差・貫通・外部参照・未解決指摘を0件目標に設定                | なし                                                 |
| QUA-052 | pass    | 各受入条件へmachine checkまたはrender reviewを対応                   | なし                                                 |
| QUA-061 | pass    | metricの母数・単位・sourceを品質メトリクス表へ固定                   | なし                                                 |
| QUA-070 | partial | diagram gateはlocal／PRに存在するが全project milestoneは未監査       | project全体のgateは別review                          |
| QUA-071 | pass    | exit criteriaを数値・parse・test結果で第三者判定可能にした           | なし                                                 |
| QUA-072 | partial | CIは未達時failするがrisk acceptance承認者は未定義                    | repository governanceで定義                          |
| QUA-090 | pass    | CDK照合、checklist、幾何検査、full／thumbnail目視を計画              | なし                                                 |
| QUA-091 | pass    | 4回の指摘・是正・再判定を記録し未解決0件                             | なし                                                 |
| QUA-100 | pass    | machine verificationと元図意図／可読性validationを両方実施           | なし                                                 |
| ARC-003 | pass    | Public user、Operator、YouTube、email、AWS Cloud境界を図示           | なし                                                 |
| ARC-031 | pass    | repository／CDK／runtime deployment viewと対象外claimをheaderに明記  | なし                                                 |
| ARC-032 | pass    | solid、double-headed、red dashed、current／gap凡例を定義             | なし                                                 |
| ARC-033 | pass    | 各serviceへresource名または責務labelを付与                           | なし                                                 |
| ARC-034 | pass    | HTTPS、origin GET、SQS、scheduled rule、API request等を特定          | なし                                                 |
| ARC-035 | pass    | embedded draw.io model、visible SVG、CDK、runtimeの名称を照合        | なし                                                 |
| ARC-037 | partial | AWS managed runtimeと外部境界は具体化したがregion／AZ実配置は未表示  | deploy済み構成図が必要ならregion／account viewを追加 |
| ARC-039 | pass    | 非圧縮draw.io modelをSVGへ埋め込みGit管理                            | なし                                                 |
| ARC-040 | pass    | 4 zoneへ分割し、各zoneを同じphysical resource粒度に統一              | なし                                                 |
| DES-002 | pass    | DEC-DB-001と現行S3／DynamoDB／async architectureに整合               | なし                                                 |
| DES-005 | pass    | EventBridge、Lambda、SQS、resource logical IDの用語を統一            | なし                                                 |
| DES-055 | partial | 非同期境界とredriveは明示したが完了確認詳細は正本文書参照            | 必要ならoperation sequenceを別図で保持               |
| DES-056 | pass    | dynamic pathの参加者がCDK／runtime componentと一致                   | なし                                                 |
| DES-101 | pass    | 図、report、正本文書のcurrent／gap表現を照合                         | なし                                                 |
| DES-102 | pass    | overviewを4 zone、詳細をresource／responsibility labelで階層化       | なし                                                 |
| DES-105 | pass    | icon source、arrow、gap、data boundaryの凡例を表示                   | なし                                                 |
| DES-110 | pass    | review日時、4回の指摘・是正、最終結果を本reportへ記録                | なし                                                 |
| CLD-001 | partial | CloudFront／S3／SQS等はmanaged serviceだがAZ喪失test未実施           | 非本番AWSでfailure validation                        |
| CLD-002 | partial | 本図はRTO／RPO目標の証拠ではない                                     | 正本の目標とproduction evidenceを別review            |
| CLD-003 | partial | S3 versioning／DynamoDB PITRは定義済みだがrestore testなし           | 定期restore testを実施                               |
| AWS-001 | pass    | CDKとarchitecture artifactを同repository／PRで管理                   | なし                                                 |
| AWS-003 | partial | CloudWatch metric／logとX-RayはCDK定義済み、実送信は未確認           | post-deploy telemetry確認                            |
| AWS-005 | partial | 4 alarms→SNSは定義済みだが全runbook紐付け未確認                      | alarm別runbookを完成                                 |
| AWS-006 | partial | `OperationsDashboard`は定義済みだが実AWS画面未確認                   | deploy後にKPI表示を確認                              |
| AWS-007 | partial | frontend deployment自体がopen gapで安全なrelease実証なし             | GAP-WEB-DEPLOY-001解消後に検証                       |
| AWS-012 | partial | account／Organizations境界は本図・repositoryから確認不能             | account topologyを別途確認                           |
| AWS-015 | partial | Lambda roleとOperatorのIAM／STSは表現、CI／端末credential棚卸しなし  | AdminRole runbookとcredential audit                  |
| AWS-018 | partial | role分離はあるがProcessor Raw PutObject不足と権限棚卸しgapあり       | GAP-IAM-PROCESSOR-001を解消                          |
| AWS-025 | n/a     | VPC、security group、NACL、管理portを作成しないserverless構成        | network resource追加時に再評価                       |
| AWS-035 | partial | public endpointはCloudFrontだがdeploy／availability証拠なし          | post-deploy smokeと可用性確認                        |
| AWS-037 | pass    | EventBridge／SQS／共有DLQの疎結合関係を図とCDKで確認                 | fault injectionは別task                              |
| AWS-054 | pass    | payload＝S3、small control state＝DynamoDBをDEC-DB-001と一致         | 再検討条件成立時にdecision review                    |
| AWS-060 | partial | forecast 80% Budget→SNSは定義済みだが実通知未確認                    | non-production notification test                     |
| AWS-074 | pass    | scheduled rule、queue、on-demand Lambdaで常時workerを持たない        | 実測効率は運用開始後に確認                           |

## 残余リスク

- 図はrepository／CDK／runtimeの物理viewであり、AWSへdeployされた実景を証明しない。
- frontend deployment、Lambda package、Processor Raw write、S3 purge／lifecycle、SQS runtime、AdminRole setupの既知gapは赤破線で残している。
- service availability、RTO／RPO、restore、alarm通知、IAM最小権限は実AWSまたは運用証拠を要する。
- draw.ioで再保存するとvisible SVGはdraw.io rendererのlayoutへ再生成されるため、PR上のdiagram verifierとrender reviewを再実行する。
