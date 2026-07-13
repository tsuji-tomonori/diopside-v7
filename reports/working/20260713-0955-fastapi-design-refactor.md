# FastAPI設計駆動refactorレポート

## 指示と対象要件

- `.workspace/bootstrap-fastapi-design.zip` の設計駆動・operation単位・strict gate・派生docs方式へ既存backendを適合した。
- 正本順位は `docs/spec/00.index.md`、公開契約は `docs/spec/20`、`22`、`23` を優先した。
- 既存 `/data/*` と `/api/contracts/*` のURL互換性を維持し、deploy／production変更は実施していない。

## 判断と成果物

- 既存repoのためbootstrap scriptは`--dry-run`だけ実行し、既存規約へ手動移植した。
- 5つのpublic JSON APIを `src/app/apis/public/{operation}` の `contract/functions/router/samples/schemas` へ分割した。
- `docs/api/public-contracts.manual.json`を人手正本とし、`public-contracts.gen.md`と`openapi.gen.json`を決定的に生成する`app-docs`を追加した。
- generatorはoperation ID、method、path、error statusのmanual/runtime不一致を拒否し、atomic writeとno-write `--check`を持つ。
- `app-archlint`、mypy strict、Ruff format checkをaggregate gateへ追加した。mypy導入時に検出した既存のJSON型、live-chat結果型、型stub不足も修正した。

## 自動生成docs内容確認

- inventoryのMarkdown tableが連続した有効なtableであり、5 operationのID、method、path、auth、success/error、summaryを含むことを目視確認した。
- operation boundary節がslug、permissions、idempotency、transaction、external effectsを含むことを確認した。
- OpenAPIが5 operationのstable IDとpath、response schema、manual通りの404/422/500、public APIのsecurity requirementなしを表現することを確認した。
- 初回目視でtable layoutと404/500欠落を不適切と判定し、generator/runtimeを修正後に再生成・再確認した。
- code由来OpenAPIは要求正当性の独立証拠ではなく、manual contractとの整合証拠として扱った。

## 実行結果

```text
bootstrap_fastapi_project.py ... --dry-run: 合格（39候補、既存5件を保持）
uv lock --check: 合格
uv run --locked ruff format --check src tests: 合格（75ファイル）
uv run --locked ruff check src tests: 失敗（インポート・行長）→ 整形・行修正 → 合格
uv run --locked pyright: 失敗（サンプル型）→ 型注釈追加 → 合格
uv run --locked mypy src tests: 失敗（スタブ・JSON・ライブチャット・エクスポート）→ 型・依存修正 → 合格
uv run --locked app-archlint: 合格
uv run --locked app-docs generate: 合格
uv run --locked app-docs generate --check: 合格
uv run --locked pytest: 合格（61件、分岐カバレッジ66%）
uv run --locked python -m app.scripts.verify_contract: 合格（release 20260711-001、3動画）
task verify: 合格（frontend型検査・単体13件・build、infra型検査・4件・build・synth、backend全ゲート、cost・quota、Playwright desktop・mobile 10件）
git diff --check: 合格
```

## 適合性、未対応、外部ゲート

- 本taskのローカル実装・生成・検証条件は満たした。生成物は反復生成後もdriftなし。
- GATE-001〜005等の外部approval、production credential、deploy/read-backは対象外かつ未合格のままであり、本変更は合格を主張しない。
- `task verify`のCDK処理はlocal synthのみで、deploy/bootstrap/destroyを実行していない。
- 実装commitは `666c05a`。本追記を証跡commitとして作成し、両commitを`origin/main`へpushする。
