---
name: implementation-test-selector
description: 変更範囲に応じた最小十分なlint、typecheck、test、build、smoke、E2E、synthを選ぶ。
---

# 実装テスト選択

1. `git diff --name-only`で変更範囲を確認する。
2. backend変更はRuff、Pyright、Pytest、contract verifierを選ぶ。
3. frontend変更はtypecheck、Vitest、buildを選び、route/interaction変更はPlaywrightも実行する。
4. infra変更はtypecheck、CDK assertion、`cdk synth`/cdk-nagを実行する。deployしない。
5. shared contract、workspace、Taskfile変更は`task verify`を追加する。
6. docs/skillだけの変更でも`git diff --check`とpath/frontmatterを確認する。
7. 実行できないcommandはcommand名、理由、残余riskを報告する。

成功した狭いtestで広い要件の合格を代用しない。
