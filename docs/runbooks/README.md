# Operations runbooks

| Runbook | Trigger | Local evidence |
|---|---|---|
| [rollback](rollback.md) | invalid/stale public release | atomic publisher tests |
| [quota-cost-exhaustion](quota-cost-exhaustion.md) | quota/cost 80% or 95% | operations policy tests |
| [dlq-redrive](dlq-redrive.md) | DLQ count > 0 | retry/job-key tests |
| [deletion-cdn-purge](deletion-cdn-purge.md) | source deletion, retention, privacy request | retention/deletion tests |
| [key-rotation](key-rotation.md) | scheduled/incident credential rotation | tabletop only |
| [gate-evidence](gate-evidence.md) | evidence expiry/replacement | tabletop only |
| [disaster-restore](disaster-restore.md) | control/public loss or corruption | CDK synth + restore drill pending |

本作業ではdeploy、bootstrap、production操作を実行しない。production手順はoperator承認、対象account、correlation ID、開始/終了時刻を監査記録へ残す。
