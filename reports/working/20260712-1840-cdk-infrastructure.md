# CDK infrastructure

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

- TypeScript strict typecheck: pass
- CDK assertion tests: 4 assertions pass
- `cdk synth`: pass
- cdk-nag: error/warning 0 after evidence-backed static-site suppressions
- npm audit: vulnerabilities 0
- deploy/bootstrap: 未実行（指示どおり）

## 未対応

- inline worker placeholderをbackend artifact bundleへ接続。
- CloudWatch alarms、Budgets、operational dashboard。
- API keyをSecrets Managerから取得するcollector runtime adapter。
