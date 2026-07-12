# diopside-v7

This repository owns the diopside target implementation:
- `backend/`: YouTube collectors, processing/tagging pipelines, atomic exporter,
  operator CLI, FastAPI contract host, and runtime Lambda handlers.
- `frontend/`: React public app with canonical versioned release loading.
- `infra/`: AWS CDK stack for S3, DynamoDB, SQS, Lambda, EventBridge,
  Secrets Manager, CloudFront, monitoring, and cost controls.
- `tasks/`, `agents/`, `skills/`, `reports/`: execution workflow and audit artifacts.

## Local start

```bash
npm install
cd backend && uv sync
task verify
task dev:backend
# another terminal
task dev:frontend
```

Backend serves `/health` and `/data/*` contract endpoints from `backend/data/public`.

## Verification-first commands

- `task verify` runs type checks, unit tests, builds, contract validation, CDK
  assertions/nag synth, and desktop/mobile browser E2E.
- `cd backend && uv run --locked python -m app.scripts.verify_contract` validates
  the checked-in canonical release.
- `task tags:migrate:preview` verifies deterministic migration of the received
  `.workspace/tags.zip` snapshot when that private evidence is available.

No verification command deploys, bootstraps, or destroys AWS resources.

## Operator CLI

`diopside-admin` uses the operator's normal AWS IAM credentials. State-changing
commands require `--yes`. Its environment is populated from CDK outputs:

```bash
export CONTROL_TABLE=...
export JOB_QUEUE_URL=...
export EXPORT_QUEUE_URL=...
export CONFIGURATION_BUCKET=...
cd backend
uv run --locked diopside-admin get-job JOB_ID
uv run --locked diopside-admin operations-summary --from 2026-07-01 --to 2026-08-01
uv run --locked diopside-admin request-deletion VIDEO_ID --reason 'request reference' --yes
```

Production normal publication remains fail-closed until GATE-001 through
GATE-006 evidence is valid in `gates/current.json`.
