# FastAPI design-driven refactor

状態: done

## 正本と範囲

- 正本順位は `docs/spec/00.index.md` に従う。
- FastAPI構成と自動生成方式は `.workspace/bootstrap-fastapi-design.zip` を移植指針とする。
- 既存の `/api/contracts/*` と `/data/*` の公開互換性を維持する。
- deploy、bootstrap、destroy、production変更は対象外とする。

## 受け入れ条件

- [x] backend APIが `src/app/apis/{domain}/{operation}` の operation 単位構成になる。
- [x] 各operationにstable ID、slug、auth、権限、error、idempotency、transaction、外部影響を持つmanual contractがある。
- [x] routerはHTTP sequenceだけを担当し、business/resource accessをfunctionsへ委譲する。
- [x] manual sourceからOpenAPI/interface inventoryを決定的に生成できる。
- [x] docs生成は `generate` とno-write `--check` の両方が成功し、反復生成で差分が出ない。
- [x] Ruff format/lint、Pyright strict、mypy strict、architecture lint、pytest、contract、aggregate verifyが成功する。
- [x] 自動生成docsのpath、operation ID、response、error、security記述を目視照合する。
- [x] 実行結果と未達gateを `reports/working` に記録する。
- [x] 検証済み変更を目的単位でcommitしpublic GitHubへpushする。

## Commit evidence

- implementation: `666c05a`
- verification evidence: 本taskと `reports/working/20260713-0955-fastapi-design-refactor.md`
