# Local Verification (diopside-v7)

## Required commands

- `task verify`
- `cd backend && uv run python src/app/scripts/verify_contract.py`
- `npm run build -w frontend`
- `npm run typecheck -w frontend`
- `task dev:backend`
- `task dev:frontend`

## Acceptance evidence

- Backend contract artifacts exist in:
  - `backend/data/public/latest.json`
  - `backend/data/public/releases/<releaseId>/`
- Frontend route pages are implemented for `/`, `/search`, `/saved`, `/history`, `/videos/:id`.
- Local state persistence keys include schema version.
