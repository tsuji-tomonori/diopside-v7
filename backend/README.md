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
