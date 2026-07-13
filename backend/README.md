# diopsideバックエンド

## エンドポイント

- `GET /health`
- `GET /api/contracts/latest`
- `GET /api/contracts/release/{release_id}`
- `GET /api/contracts/releases/{release_id}/videos/{video_id}`
- `/data/*` 配下の静的JSON／SVG

各JSON APIは `src/app/apis/public/{operation}` 配下へ実装する。人が記述する
`docs/api/public-contracts.manual.json` の契約metadataを実行時OpenAPIと照合し、
全操作についてAPI索引、interface、sequence、詳細設計、テスト観点、例を生成する。
生成済みの `*.gen.*` は直接編集しない。

```bash
uv run --locked app-docs generate
uv run --locked app-docs generate --check
uv run --locked app-archlint
```

repository rootの `task docs:generate` で全APIドキュメントを再生成し、
`task docs:check` で書き込みなしの差異検査を行う。生成済みentry pointは
`backend/docs/api/public-contracts.gen.md` である。

## 起動

```bash
cd backend
uv run --locked uvicorn app.main:app --app-dir src --reload --host 0.0.0.0 --port 8000
```

## タグ移行preview

受領した `.workspace/tags.zip` snapshotは移行入力であり、実行時依存ではない。

```bash
task tags:migrate:preview
```

このコマンドは安定した `tagId`、version field、正規alias、割り当て証拠、公開タグ件数を持つ
決定的なv3 previewを `/tmp` 配下へ書き込む。
