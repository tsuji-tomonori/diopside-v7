# diopside-v7

このリポジトリはdiopsideの目標実装を管理する。

- `backend/`: YouTube収集、処理・タグ付けパイプライン、原子的export、operator CLI、FastAPI契約host、Lambda実行時handler
- `frontend/`: 正規のversion付きreleaseを読み込むReact公開app
- `infra/`: S3、DynamoDB、SQS、Lambda、EventBridge、Secrets Manager、CloudFront、監視、cost制御を構成するAWS CDK stack
- `tasks/`、`agents/`、`skills/`、`reports/`: 実行workflowと監査成果物

## アーキテクチャ

現行CDK／runtimeの構成は[architecture.drawio.svg](docs/design/architecture.drawio.svg)を参照する。公開閲覧はCloudFrontからversion付きS3 public dataを取得し、収集・生成はEventBridge、SQS、Lambdaで非同期実行する。本文データはS3、job・quota・gate等の小さなcontrol stateはDynamoDBに置き、Aurora DSQLは採用しない。

この図はrepository上の構成を表し、deploy済みまたはproduction acceptance済みであることを示さない。現行CDKにはReact／Vite build assetのS3配備とSPA rewriteがなく、runtime package、IAM、versioned object削除、SQS設定、operator setupにも未解決事項がある。詳細は[gap一覧](docs/spec/25.gaps-and-decisions.md#4-architecture実装のgap)を正とする。

## ローカル起動

```bash
npm install
cd backend && uv sync
task verify
task dev:backend
# 別のterminalで実行する
task dev:frontend
```

backendは `backend/data/public` から `/health` と `/data/*` の契約endpointを提供する。

## 検証優先のコマンド

- `task verify` は型検査、unit test、build、契約検証、CDK assertion・nag synth、desktop・mobile browser E2Eを実行する。
- `cd backend && uv run --locked python -m app.scripts.verify_contract` は保存済みの正規releaseを検証する。
- `task tags:migrate:preview` は非公開証拠 `.workspace/tags.zip` を利用できる場合に、受領snapshotの決定的移行を検証する。

どの検証コマンドもAWS resourceのdeploy、bootstrap、destroyを実行しない。

## 運用 CLI

`diopside-admin` はAWS SDKの現在のcredentialを使用する。production運用ではAdminRoleを引き受けた一時credentialを使い、状態変更コマンドには`--yes`が必要である。必要な環境変数は次のとおりである。

```bash
export CONTROL_TABLE=...
export JOB_QUEUE_URL=...
export EXPORT_QUEUE_URL=...
export CONFIGURATION_BUCKET=...
export RAW_BUCKET=...
export PROCESSED_BUCKET=...
export PUBLIC_BUCKET=...
cd backend
uv run --locked diopside-admin get-job JOB_ID
uv run --locked diopside-admin operations-summary --from 2026-07-01 --to 2026-08-01
uv run --locked diopside-admin publish-candidate /path/to/release --yes
uv run --locked diopside-admin request-deletion VIDEO_ID --reason 'request reference' --yes
```

現行CDK outputにはRaw／Processed bucket名とAdminRole ARNがなく、完全なoperator setup情報がそろっていない。production運用手順は`GAP-ADMIN-SETUP-001`を解消してから確定する。

`gates/current.json` でGATE-001〜006の証拠が有効になるまで、productionの通常公開は
fail-closedを維持する。
