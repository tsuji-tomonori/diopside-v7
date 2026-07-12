# diopside-v7

This repository is structured toward the diopside target implementation:
- `backend/`: FastAPI API + static public-data contract host.
- `frontend/`: React public app (mobile-first, route-based).
- `infra/`: operation/infrastructure starter scripts.
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

- `task verify` for baseline local checks.
- `npm run verify-contract -C backend` for contract shape checks.
- `npm run typecheck -w frontend` and `npm run build -w frontend` for UI consistency.
