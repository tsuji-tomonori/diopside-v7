# 現行アーキテクチャ文書・図の整合

状態: completed

## 背景

既存の仕様書には、過去のNuxt／frontend-only構成と、現在のReact／AWS serverless実装が混在している。添付されたdraw.io SVGもAPI Gateway、FastAPI Lambda、Aurora DSQLを現行構成として描いており、CDK・runtimeと一致しない。現在の実装事実、未解決の運用成立gap、DynamoDB／Aurora DSQLの選定判断を同一変更で同期する。

## 対象

- `README.md`、`infra/README.md`
- `docs/spec`のcurrent／target境界、実装coverage、source path、decision／gap
- 現行CDKとruntimeを表す編集可能な`docs/design/architecture.drawio.svg`
- 変更に必要なtraceabilityと受け入れ状態の説明

## 非対象

- runtime、CDK、frontend実装の修正
- AWSへのdeploy、bootstrap、destroy
- production gateの承認、実AWS smoke／recovery drill
- 添付資料の旧内容を正本へ再導入すること

## 受け入れ条件

- [x] Nuxt、API Gateway、FastAPI Lambda、Aurora DSQLを現行production経路として記載しない。
- [x] React／Vite、CloudFront／S3、EventBridge、SQS、Collector／Processor／Exporter Lambda、DynamoDB control、Secrets Manager、CloudWatch／SNS／Budgets、IAM／STS CLIの現行境界が図と文書で一致する。
- [x] frontend asset配備／SPA rewrite、Lambda package、Processor IAM、versioned S3削除・保持、SQS設定、operator setupの未解決事項を実装済みと誤認させずgap管理する。
- [x] S3をdata body、DynamoDBをcontrol stateに使い、Aurora DSQLを現時点で採用しない決定、代替案、trade-off、再検討条件を記録する。
- [x] `architecture.drawio.svg`がSVGとして描画でき、draw.ioで再編集できる埋め込みmodelを保持する。
- [x] source path、current／target記述、図への参照を関係文書で同期する。
- [x] product acceptanceとdocumentation verificationを分離して記録する。
- [x] deployを実行しない。

## 検証方法

- `git diff --check`
- stale fact／pathの`rg`検査
- Python XML parserによるSVG parseとdraw.io model属性検査
- InkscapeによるSVG→PNG renderと目視確認
- repositoryのMarkdown／document検証command（実在する最小commandからaggregateへ拡張）

## 選択したSWEBOK／WAFチェック

- ARC-003、ARC-032、ARC-060、ARC-090
- REQ-201、REQ-202、REQ-605、REQ-1003、REQ-1107
- CLD-010、CLD-017、CLD-042、CLD-047
- AWS-018、AWS-037、AWS-054、AWS-075
- QUA-001、QUA-090、QUA-904

## リスク

- 図は「CDKで定義された現行構成」を表し、deploy済みとは主張しない。
- 文書修正だけでは、登録するcritical／high gapは解消しない。
- 外部サービスの価格・機能説明を今回の決定理由の主根拠にせず、repoのアクセスパターンと実装事実を根拠にする。
