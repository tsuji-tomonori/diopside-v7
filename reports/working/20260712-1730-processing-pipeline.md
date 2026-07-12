# processing pipeline

## 実施

- YouTube metadataを欠落値0埋めなしでcanonical raw metadataへ正規化。
- upcoming/live/archive/unavailable状態判定を実装。
- chat event type、paid/membership/moderation/poll/unknownを共通schemaへ写像。
- commentとchatを別source seriesへ正規化。
- video-scoped HMAC-SHA-256 author tokenを実装。
- NFKC、URL/control除去、version付きtokenizeとstopword hashを実装。
- coverage付きchat/comment aggregateと安全なSVG wordcloudを実装。
- public aggregateへのauthor ID、token、本文、個別支払額混入を再帰拒否。
- 語数不足時はSVGを捏造せず`insufficient_terms`を出力。

## 検証

- Ruff: pass
- Pyright strict: pass
- Pytest: 19 tests pass
- Coverage: 73%

## 未対応

- description timestampとspike timestamp candidate生成。
- 100,000 chat/10,000 comment負荷fixtureとchunk orchestration。
- processor出力からrelease candidate全artifactを組み立てるCLI。
