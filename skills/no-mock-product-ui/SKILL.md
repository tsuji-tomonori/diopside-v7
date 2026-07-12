---
name: no-mock-product-ui
description: production UI/APIへ架空値、demo fallback、未実装操作を混入させない。
---

# No Mock Product UI

- 表示値はcontract、props、永続状態、設定、または明示的loading/empty/error/unavailableに由来させる。
- 欠落count、duration、date、metadataを0や架空値で埋めない。
- 推定値は「推定」とsource/coverageを表示する。
- handlerのないbuttonや未実装navigationを公開しない。
- fixtureはtest/local seedへ隔離し、production fallbackにしない。
- 変更後にempty response、optional missing、error stateをtestする。
