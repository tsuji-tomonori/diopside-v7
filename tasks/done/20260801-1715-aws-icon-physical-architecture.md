# AWSアイコン物理構成図の品質改善

## 指示

`docs/design/architecture.drawio.svg`を、元の添付図と同じAWS Architecture Iconsベースの物理構成図へ更新する。現行CDK／runtimeと正本文書に合わせ、接続線の重なり、図形・ラベルの貫通、誤ったAWSサービス名を残さず、完了条件を満たすまでレンダリングレビューと修正を反復する。

## スコープ

- 対象: `docs/design/architecture.drawio.svg`、第三者素材通知、図の機械検証、Taskfile／GitHub Actions gate、task／作業報告
- 正本: `infra/lib/diopside-stack.ts`、`backend/src/app/runtime/handlers.py`、`backend/src/app/runtime/jobs.py`、`docs/spec/00.index.md`、`docs/spec/25.gaps-and-decisions.md`
- 対象外: CDK／runtimeの機能修正、AWS deploy、production acceptance、open gapの解消

## 受け入れ条件

- [x] 通常のSVG表示で、AWS Architecture Iconsベースの物理構成図として読める。
- [x] draw.ioで再編集できる非圧縮`mxfile`／`mxGraphModel`をSVGへ埋め込む。
- [x] 現行CDKに存在する主要サービスと物理リソースを、公式名称で表す。
- [x] `Amazon EventBridge Scheduler`ではなく、実装どおり`Amazon EventBridge`のscheduled ruleとして表す。
- [x] Nuxt、API Gateway、FastAPI Lambda、Aurora DSQL、CloudFront Functionsを現行物理リソースとして表示しない。
- [x] current pathとopen gapを線種・凡例で明確に区別する。
- [x] connector同士の交差・重複が0件である。
- [x] connectorが接続先以外のアイコン、カード、ラベルを貫通する箇所が0件である。
- [x] サービス名、リソース名、責務ラベルに欠け・切れ・重なりがない。
- [x] SVG外部参照とraster画像を使わず、ベクターのまま拡大できる。
- [x] 埋め込んだiconの取得元、version、copyright、MIT licenseを隣接文書へ記録する。
- [x] XML、embedded draw.io model、サービスinventory、禁止語、幾何交差を機械検査して合格する。
- [x] SVGをPNGへレンダリングし、100%表示と縮小表示を目視レビューして合格する。
- [x] `git diff --check`とdocs範囲の既存検証が合格する。
- [x] 実行結果、初回指摘、是正内容、最終判定、未検証の外部gateを作業報告へ記録する。

## 品質メトリクス

| 指標                              | 合格値 | 証跡                |
| --------------------------------- | -----: | ------------------- |
| 必須AWSサービス名の不足           |      0 | diagram verifier    |
| legacy／未実装サービス名          |      0 | diagram verifier    |
| connector交差・重複               |      0 | diagram verifier    |
| connectorによる非接続obstacle貫通 |      0 | diagram verifier    |
| 外部image参照・raster image       |      0 | XML／SVG inspection |
| draw.io model parse error         |      0 | XML parser          |
| 目視指摘の未解決                  |      0 | rendered PNG review |

## 適用KAと期待証跡

| KA                       | 対象ID                                                                                                                       | 期待証跡・検証                                                                                |
| ------------------------ | ---------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------- |
| Engineering Management   | MGT-003、MGT-022、MGT-072、MGT-092、MGT-103                                                                                  | 検証可能な完了条件、成果物、review loop、OSS icon license確認                                 |
| Engineering Process      | PRC-041、PRC-053、PRC-054、PRC-086、PRC-091                                                                                  | 再現可能なメトリクス、製品／工程検証、不適合是正、成果物整合、実在service確認                 |
| Configuration Management | SCM-020、SCM-021、SCM-026、SCM-048                                                                                           | diagram／verifier／reportの構成識別、Git管理、CDKとの関係、PR検証                             |
| Quality                  | QUA-034、QUA-052、QUA-061、QUA-070、QUA-071、QUA-072、QUA-090、QUA-091、QUA-100                                              | 数値gate、機械／目視V&V、指摘の修正後再検証                                                   |
| Architecture             | ARC-003、ARC-031、ARC-032、ARC-033、ARC-034、ARC-035、ARC-037、ARC-039、ARC-040                                              | AWS境界、物理view、凡例、責務、接続、CDK整合、draw.io source、適切な粒度                      |
| Design                   | DES-002、DES-005、DES-055、DES-056、DES-101、DES-102、DES-105、DES-110                                                       | AWS公式名称、同期／非同期、参加者整合、図本文整合、可読性、凡例、review記録                   |
| Cloud                    | CLD-001、CLD-002、CLD-003                                                                                                    | cloud責任境界、managed service構成、current／external／gapの区別                              |
| AWS                      | AWS-001、AWS-003、AWS-005、AWS-006、AWS-007、AWS-012、AWS-015、AWS-018、AWS-025、AWS-035、AWS-037、AWS-054、AWS-060、AWS-074 | CDK／AWSサービスinventoryとの一致、IAM、監視、疎結合、data store、budget、scheduled async構成 |

## 検証予定

1. diagram専用verifier
2. SVGと埋め込みdraw.ioモデルのXML構文解析
3. Inkscape PNG renderと目視review
4. `git diff --check`
5. docs／spec link・format検査（repository既存commandから選択）
6. `npm run typecheck -w @diopside/infra`
7. `npm test -w @diopside/infra`
8. `npm run synth -w @diopside/infra`

AWS deployは行わない。production acceptanceは本taskの外部gateとして残す。
