# Lambda runtime wiring

## 実施

- CDK inline placeholder Lambdaをbackend source assetへ置換。
- metadata/live/export scheduleへschema-valid job inputを設定。
- canonicalJobKeyをjobIdに使い、DynamoDB conditional putで重複起動を拒否。
- persist成功後だけSQSへenqueue。
- processorへSQS event sourceとpartial batch failureを設定。
- collector/processor/exporter handlerを分離。
- boto3 runtime依存とDynamoDB/SQS type stubsを追加。

## 検証

- Ruff: pass
- Pyright strict: pass
- Pytest: 34 tests pass
- Backend coverage: 76%
- Infra typecheck/assertion/synth/cdk-nag: pass
- deploy: 未実行

## 未対応

- processor handlerからnormalize/aggregate/export domain処理へのjob-type dispatch。
- succeeded/failed/retry/DLQ JobEventの全state永続化。
- Secrets ManagerからYouTube API keyを読むcollector execution adapter。
