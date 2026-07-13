# ローカル検証（diopside-v7）

## 必須コマンド

- `task verify`
- `cd backend && uv run python src/app/scripts/verify_contract.py`
- `npm run build -w frontend`
- `npm run typecheck -w frontend`
- `task dev:backend`
- `task dev:frontend`

## 受け入れ証拠

- backend契約成果物が次のpathに存在する。
  - `backend/data/public/latest.json`
  - `backend/data/public/releases/<releaseId>/`
- frontend route pageとして `/`、`/search`、`/saved`、`/history`、`/videos/:id` が実装されている。
- local stateの永続化keyにschema versionが含まれている。
