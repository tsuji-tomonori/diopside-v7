# 運用runbook

| Runbook | 起動条件 | ローカル証拠 |
|---|---|---|
| [rollback](rollback.md) | 不正または古い公開release | 原子的publisher test |
| [quota-cost-exhaustion](quota-cost-exhaustion.md) | quotaまたはcostが80%／95% | 運用policy test |
| [dlq-redrive](dlq-redrive.md) | DLQ件数が1件以上 | retry・job key test |
| [deletion-cdn-purge](deletion-cdn-purge.md) | source削除、retention、privacy request | retention・deletion test |
| [key-rotation](key-rotation.md) | 定期またはincident時のcredential rotation | 机上確認のみ |
| [gate-evidence](gate-evidence.md) | 証拠の失効または置換 | 机上確認のみ |
| [disaster-restore](disaster-restore.md) | control／publicの喪失または破損 | CDK synth済み、restore訓練は未実施 |

本作業ではdeploy、bootstrap、production操作を実行しない。production手順はoperator承認、対象account、correlation ID、開始/終了時刻を監査記録へ残す。
