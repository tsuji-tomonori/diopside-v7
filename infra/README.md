# diopside インフラストラクチャ

低costかつevent駆動の現行AWS CDK stackを提供する。構成図は[architecture.drawio.svg](../docs/design/architecture.drawio.svg)を正とする。

- 暗号化・version管理されたraw、processed、configuration、public、access-log用S3 bucket
- PITRとTTLを備えるDynamoDB on-demand control table
- TLSを強制する暗号化SQS job queueとDLQ
- collector、processor、exporter、operatorごとに分離したIAM role
- VPC／NATを使用しない短時間の定期Lambda worker
- CloudFront OACとsecurity headerを介した非公開S3 origin

公開originはversion付きpublic data用S3であり、API Gateway、Aurora DSQL、VPC／NATを構成しない。React／Vite build assetのS3配備、CloudFront default root／SPA rewrite、operator setupの完全なoutputは現時点のstackに含まれない。Lambda package、ProcessorRoleのraw書込、versioned S3の完全削除・保持、SQS timeout／batch設定を含む残件は[`GAP-ARCH-001`](../docs/spec/25.gaps-and-decisions.md#4-architecture実装のgap)配下で管理する。

## ローカル検証

```bash
task cdk:test
task cdk:synth
```

これらのコマンドはローカルsynthだけを実行する。ローカル検証の一部として
`cdk deploy`、`bootstrap`、`destroy` を実行しない。
