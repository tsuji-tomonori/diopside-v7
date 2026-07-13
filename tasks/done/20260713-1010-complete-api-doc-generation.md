# Complete per-operation API documentation generation

状態: done

## 正本と判断

- 正本順位は `docs/spec/00.index.md` に従う。
- `backend/docs/api/public-contracts.manual.json` とruntime OpenAPI／operation layoutを生成入力とする。
- `.workspace/bootstrap-fastapi-design.zip` のartifact graph、determinism、atomic write、`--check`要件を適用する。
- 現行APIはDB／providerを直接使わないためSQL、ER、外部resource CRUDの独立文書は生成せず、非該当理由をdetail designに生成する。

## 受け入れ条件

- [x] API一覧indexが全operationと全個別文書へのlinkを持つ。
- [x] 5 APIそれぞれにinterface、sequence、detail design、test factors、examplesを生成する。
- [x] interfaceはmethod/path/parameters/response/error/securityをruntime OpenAPIと一致させる。
- [x] sequenceはrouterからfunctions、contract loaderまでの実処理順を表す。
- [x] detail designはsource files、auth、idempotency、transaction、external effects、DB/provider非該当を表す。
- [x] test factorsはnormal、validation、missing、invalid stored contract、compatibilityを列挙する。
- [x] examplesはoperationのsample sourceから生成する。
- [x] generatorは決定的、atomic write、全outputのno-write drift checkを持つ。
- [x] generator unit test、Ruff、Pyright、mypy、architecture lint、pytest、contract、`task verify`が成功する。
- [x] 生成後に全output数、link、内容を目視／機械確認する。
- [ ] report、commit、public GitHub pushを完了する。
