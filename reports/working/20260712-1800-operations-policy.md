# operations policy

## 実施

- UTF-8 byte length prefixによるcanonical job keyを実装。
- retry attempt 1〜4、full-jitter 2/4/8秒、Retry-After clampを実装。
- method別quota budgetとlive chat最低8時間予約を実装。
- quota 80/95%時の警告・停止とlive/deletion/compliance保護を実装。
- API/raw/processed/replay 30日、public旧版90日、運用記録400日のretentionを実装。
- permission/gate期限の短い方を優先。
- 全layerとCDN pathを必須にするdeletion eventを実装。

## 検証

- Ruff: pass
- Pyright strict: pass
- Pytest: 30 tests pass
- Coverage: 75%

## 未対応

- 永続JobEvent repository、DLQ redrive CLI、実通知連携。
- S3 object version/replicaとCloudFront invalidationの実行adapter。
- liveChatMessages継続poll loopとstreamList adapter。
