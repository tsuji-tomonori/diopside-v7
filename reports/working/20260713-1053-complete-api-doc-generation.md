# 操作別APIドキュメント生成の完成

## 指示と要件

- API一覧だけでなく、APIごとの各種文書を生成するscriptを作り、実行して内容を確認する。
- `docs/spec`を正本とし、`.workspace/bootstrap-fastapi-design.zip`のartifact graph、determinism、atomic write、drift checkを適用した。

## 実施内容

- `app-docs`を全生成物ownerへ拡張し、`task docs:generate`と`task docs:check`を追加した。
- API一覧、OpenAPI、生成registryに加え、5 operation × 5種類の文書を生成した。
  - interface
  - sequence（Mermaid）
  - detail design
  - test factors
  - examples
- manual contractへmodule/functionとrequirements/specification/acceptance traceを追加した。
- runtime OpenAPIとのmethod、path、operation ID、error status不一致を生成失敗にした。
- functions.pyをAST解析し、実際の`contract_loader.*`呼出しをsequence/detailへ反映した。
- sample moduleは各operation exactly oneを要求し、canonical version/fieldに沿う例へ更新した。
- 生成対象外の古い`*.gen.*`もdriftとして検出する。

## 内容レビュー

- 一覧に5 APIと各5文書への25 linkが存在することを確認した。
- 各文書種別が5件ずつ存在し、registryが28 outputを所有することを確認した。
- 全interfaceがparameter、200、404/422/500、public/no-security、traceabilityを表すことを確認した。
- `getReleaseTagsContract`のsequenceがtaxonomy/tag index/aliasの3 loader callを実装順に表すことを確認した。
- detailが5 source file、auth、idempotency、transaction、external effect、DB/provider非該当を表すことを確認した。
- test factorがnormal、missing、invalid stored data、compatibility、security、path boundaryを表すことを確認した。
- 初回レビューで誤った`release_id}/tags`抽出と`typed tags response`を検出し、regexとOpenAPI schema参照へ修正後、全APIを再生成した。
- examplesの旧`schemaVersion=1`／placeholderをcanonical `1.0.0`と実field構成へ修正した。

## 検証結果

```text
task docs:generate: 合格（28ファイルを生成）
task docs:check: 合格（28ファイルが最新）
ruff: 失敗（行長）→ ソース分割 → 合格
pyright: 失敗（動的サンプル・空リスト型）→ 明示的な型付け → 合格
mypy src tests: 合格
app-archlint: 合格
pytest tests/tools/test_app_docs.py: 失敗（rendererの並び順）→ rendererを整列 → 2件合格
pytest初回全件: 中断。test_main途中で出力停止したため合格に数えず停止
pytest tests/test_main.py -vv: 合格（2件）
pytest全件再実行: 合格（62件、分岐カバレッジ66%）
verify_contract: 合格（release 20260711-001、3動画）
task verify: 合格（frontend単体13件、infra assertionとsynth 4件、backend 62件、Playwright 14件）
git diff --check: 合格
```

## 適合性、非対象、残余リスク

- 要求されたAPI一覧とAPI別文書は生成・実行・drift検査・内容修正まで完了した。
- 現行5 APIはDB、SQL、provider SDKを使わないため、SQL/ER/外部resource CRUD独立文書は生成せずdetailで非該当根拠を明記した。
- 生成文書はmanual/runtime整合の証拠であり、外部approvalやproduction acceptanceの代替ではない。
- deploy、bootstrap、destroy、production変更は実施していない。

## Commit証拠

- implementation: `b240f4a`
- 本追記をverification evidence commitとして作成し、両commitを`origin/main`へpushする。
