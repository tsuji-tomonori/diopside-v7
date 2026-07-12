# diopside Backend

## Endpoints

- `GET /health`
- `GET /api/contracts/latest`
- `GET /api/contracts/release/{release_id}`
- `GET /api/contracts/releases/{release_id}/videos/{video_id}`
- Static JSON/SVG under `/data/*`

## Run

```bash
cd backend
uv run --locked uvicorn app.main:app --app-dir src --reload --host 0.0.0.0 --port 8000
```

## Tag migration preview

The received `.workspace/tags.zip` snapshot is migration input, not a runtime dependency.

```bash
task tags:migrate:preview
```

The command writes deterministic v3 previews under `/tmp` with stable `tagId`, version fields,
canonical aliases, assignment evidence, and public tag counts.
