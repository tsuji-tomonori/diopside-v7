# 全実装の基準再設定／YouTube基盤

## 指示

既存実装を完成済みとみなさず仕様から再評価し、`.workspace/tags.zip` と `.workspace/scripts.zip` を参照してYouTube API呼び出しを含む完全実装へ進める。

## 判断

- 現行はfrontend試作とstatic fixtureのみで、collector/processor/tagging/export/IaCが主要未実装だった。
- 最初の完成単位を、検証可能なworkspace、strict backend、canonical release validation、YouTube Data API clientとした。
- production deploy、credential作成、quota申請、外部gate承認は行わない。

## 実施

- `.workspace/` をgitignoreへ追加。
- npm workspaceへtypecheck/test/build集約scriptとlockfileを追加。
- backendへruff、pyright strict、pytest、coverage、uv.lockを追加。
- Pydanticによるlatest/release canonical contract検証とrelease間整合検査を追加。
- CORSをlocalhost/GET限定へ変更し、FastAPI routeをasync化。
- YouTube Data API clientを追加。
  - `channels.list -> playlistItems.list -> videos.list`
  - 動画50 ID単位のbatch、uploads page checkpoint
  - commentThreadsと不足replyのcomments.list
  - liveChatMessages page取得
  - quota event、reason、status、latency、retryability記録
  - 429/5xx/network timeoutの上限付きretry
  - `search.list`は明示的channel discoveryだけに限定
- frontend query canonicalization testとinfra contract testを追加。

## 検証結果

- frontend／infra `typecheck`: 合格
- frontend Vitest: 2件のtestが合格
- infra Node test: 1件のtestが合格
- frontend／infra build: 合格
- backend Ruff: 合格
- backend Pyright strict: 合格
- backend Pytest: 7件のtestが合格、coverage 65%
- 正規契約verifier: `ok: release 20260711-001 with 3 videos`
- npm audit: 脆弱性0件

## 未対応・リスク

- `task verify`はproto管理下にNodeがないため、指定npm 10.9.0導入時に停止。system Node 22.14.0/npm 10.8.2で同内容はpass。
- collector CLIの実YouTube API smokeはcredential未提供のため未実行。
- streamList、live chat継続poll/checkpoint、quota予約/停止制御、raw retentionは後続実装。
- `.workspace`のtagging scripts/dataをcanonical stable tagId pipelineへ移植する作業は後続。
- processor/export/CDK/admin/runbook/observabilityとfrontend受入試験は未完了。
- `.git` directoryが空でありcommit/pushは実行不能。
