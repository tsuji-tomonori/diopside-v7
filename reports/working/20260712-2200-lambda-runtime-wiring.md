# Lambda runtimeの配線

## 実施

- CDK inline placeholder Lambdaをbackend source assetへ置換。
- metadata/live/export scheduleへschema-valid job inputを設定。
- canonicalJobKeyをjobIdに使い、DynamoDB conditional putで重複起動を拒否。
- persist成功後だけSQSへenqueue。
- processorへSQS event sourceとpartial batch failureを設定。
- collector/processor/exporter handlerを分離。
- boto3 runtime依存とDynamoDB/SQS type stubsを追加。

## 検証

- Ruff: 合格
- Pyright strict: 合格
- Pytest: 34件のtestが合格
- Backend coverage: 76%
- Infra typecheck／assertion／synth／cdk-nag: 合格
- deploy: 未実行

## 未対応

- processor handlerからnormalize/aggregate/export domain処理へのjob-type dispatch。
- succeeded/failed/retry/DLQ JobEventの全state永続化。
- Secrets ManagerからYouTube API keyを読むcollector execution adapter。
