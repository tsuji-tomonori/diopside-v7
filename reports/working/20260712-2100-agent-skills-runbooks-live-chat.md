# agent skills, runbooks, live chat

## 実施

- root AGENTSと互換agents entry pointを追加。
- rag-assist由来のtest selector、test runner、Taskfile、no-mock、post-task skillを5.6向けに移植。
- `/goal`と重複する旧completion skillは非採用。
- rollback、quota/cost、DLQ、deletion/CDN、key rotation、gate evidence、restoreの7 runbookを追加。
- live chat継続poll、checkpoint、messageId dedupe、terminal state保存を実装。

## 検証

- Ruff: pass
- Pyright strict: pass
- Pytest: 32 tests pass
- Coverage: 77%
- `git diff --check`: 集約commit前に実施

## Fit

rag-assistの透明なtask/report/test disciplineを維持しつつ、GPT-5.6 `/goal`と重なるcompletion orchestrationは削減した。

## 未対応

- YouTube Live Streaming API `streamList` adapter。利用不能時のData API fallbackは実装済み。
- runbookのnon-production restore/DLQ/deletion実drill。
