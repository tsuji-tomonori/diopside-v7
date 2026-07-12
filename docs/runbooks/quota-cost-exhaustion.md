# Quota and cost exhaustion

## Thresholds

- 80%: warning。新規低優先処理を抑制する。
- 95%: YouTube APIを使う低優先jobを停止する。
- 保護: deletion、期限7日未満compliance refresh、5分live start check、進行中live chat。

## Stop order

1. 過去wordcloud/分析再生成。
2. 期限7日以上のcomment full refresh。
3. 12時間comment incremental。
4. 期限7日以上の6時間metadata refresh。

live chat開始前に8時間以上を予約し、超過時は開始せず通知する。AWS予測額80%では同じ低優先順で停止し、security/deletion/metadata freshnessを止めない。

## Evidence

method別quota event、予約量、停止job、再開判断、actual project quota、Cost Explorer/Budgets値を記録する。
