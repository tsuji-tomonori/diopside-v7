# Complete per-operation API documentation generation

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
task docs:generate: pass（28 files generated）
task docs:check: pass（28 files current）
ruff: fail（line length）-> source分割 -> pass
pyright: fail（dynamic sample/empty list型）-> explicit typing -> pass
mypy src tests: pass
app-archlint: pass
pytest tests/tools/test_app_docs.py: fail（unsorted renderer）-> renderer sort -> 2 passed
pytest初回全件: interrupted。test_main途中で出力停止したためpassに数えず停止
pytest tests/test_main.py -vv: pass（2 tests）
pytest全件再実行: pass（62 tests、branch coverage 66%）
verify_contract: pass（release 20260711-001、3 videos）
task verify: pass（frontend 13 unit、infra 4 assertion+synth、backend 62、Playwright 14）
git diff --check: pass
```

## Fit、非対象、残余risk

- 要求されたAPI一覧とAPI別文書は生成・実行・drift検査・内容修正まで完了した。
- 現行5 APIはDB、SQL、provider SDKを使わないため、SQL/ER/外部resource CRUD独立文書は生成せずdetailで非該当根拠を明記した。
- 生成文書はmanual/runtime整合の証拠であり、外部approvalやproduction acceptanceの代替ではない。
- deploy、bootstrap、destroy、production変更は実施していない。
