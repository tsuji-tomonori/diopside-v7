# diopside infrastructure

AWS CDK stack following the low-cost, event-driven target architecture:

- encrypted/versioned S3 raw, processed, configuration, public, and access-log buckets
- DynamoDB on-demand control table with PITR and TTL
- encrypted SQS job queue and DLQ with TLS enforcement
- separated collector, processor, exporter, and operator IAM roles
- short-running scheduled Lambda workers without VPC/NAT
- private S3 origin through CloudFront OAC and security headers

## Local verification

```bash
task cdk:test
task cdk:synth
```

These commands only synthesize locally. Do not run `cdk deploy`, `bootstrap`, or `destroy` as part
of local verification.
