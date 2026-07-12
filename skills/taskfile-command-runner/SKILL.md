---
name: taskfile-command-runner
description: Taskfile commandの実体を確認し、安全なlocal commandだけを実行する。
---

# Taskfile Command Runner

1. `Taskfile.yml`と委譲先npm/uv scriptを読む。
2. 既存のnarrow taskを優先し、なければpackage commandを使う。
3. dev serverはsessionで起動し、readiness確認後にdependent checkを実行して停止する。
4. sandbox外再実行前にcommand、scope、外部影響を確認する。
5. deploy、bootstrap、destroy、release、production mutation taskは実行しない。
6. command、result、権限委譲、未実施理由をtask/reportへ記録する。
