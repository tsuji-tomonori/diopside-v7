---
name: repository-test-runner
description: repositoryの検証を実行・分類・修復し、未実行をpass扱いせず報告する。
---

# Repositoryテスト実行

- narrow checkを先に、shared behaviorはaggregate checkまで実行する。
- failureをregression、stale expectation、dependency、sandbox、timeoutへ分類する。
- regressionとstale expectationは修正後に同じcheckを再実行する。
- sandbox/network制約のrequired checkはresolved commandを確認してから権限委譲する。
- production credentialやdeployを必要とするcheckは実行しない。
- timeout、interrupt、skippedはpassではない。

報告形式:

```text
<コマンド>: 合格
<コマンド>: 失敗 → <修正> → 合格
<command>: 未実施。理由: <具体的理由>
```
