# 災害復旧

## 目的

- RPO 24時間、RTO 4時間。

## 手順

1. 隔離したnon-production account/regionを指定する。productionへ直接restoreしない。
2. CDK synth/template hashとconfiguration backupを検証する。
3. S3 versioning backup、raw manifest、checkpoint、DynamoDB PITRからcontrol stateを復元する。
4. source freshness、permission/policy gate、retention/deletion ledgerを再適用する。
5. processed/publicを再生成し、既存latestをコピーだけで昇格させない。
6. canonical contract、hash/join、representative UI smokeを確認する。
7. RPO/RTO、欠落、手動操作、改善項目をdrill reportへ記録する。

初回受入前に隔離non-production restore testを実施する。local synthだけをrestore成功証拠にしない。
