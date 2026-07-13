# diopside インフラストラクチャ

低costかつevent駆動の目標architectureに従うAWS CDK stackを提供する。

- 暗号化・version管理されたraw、processed、configuration、public、access-log用S3 bucket
- PITRとTTLを備えるDynamoDB on-demand control table
- TLSを強制する暗号化SQS job queueとDLQ
- collector、processor、exporter、operatorごとに分離したIAM role
- VPC／NATを使用しない短時間の定期Lambda worker
- CloudFront OACとsecurity headerを介した非公開S3 origin

## ローカル検証

```bash
task cdk:test
task cdk:synth
```

これらのコマンドはローカルsynthだけを実行する。ローカル検証の一部として
`cdk deploy`、`bootstrap`、`destroy` を実行しない。
