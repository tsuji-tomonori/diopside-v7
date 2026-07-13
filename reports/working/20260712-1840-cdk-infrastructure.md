# CDK infrastructure実装

## 実施

- rag-assist型の`bin/lib/test` TypeScript CDK構成へ移行。
- encrypted/versioned S3 raw/processed/config/public/access log bucketを追加。
- on-demand DynamoDB control table、PITR、TTLを追加。
- TLS/SSE付きSQS job queueとDLQを追加。
- collector/processor/export/admin IAM roleを分離。
- 5分live確認、6時間metadata、24時間export scheduleを追加。
- CloudFront OAC、HTTPS redirect、CSP、frame/content/referrer/HSTS headerを追加。
- S3/CloudFront access logging、Lambda tracing、reserved concurrencyを追加。
- cdk-nagをsynth gateとして追加。

## 検証

- TypeScript strict typecheck: 合格
- CDK assertion test: 4件のassertionが合格
- `cdk synth`: 合格
- cdk-nag: 証拠に基づく静的site抑制後のerror／warning 0件
- npm audit: 脆弱性0件
- deploy/bootstrap: 未実行（指示どおり）

## 未対応

- inline worker placeholderをbackend artifact bundleへ接続。
- CloudWatch alarm、Budgets、運用dashboard。
- API keyをSecrets Managerから取得するcollector runtime adapter。
