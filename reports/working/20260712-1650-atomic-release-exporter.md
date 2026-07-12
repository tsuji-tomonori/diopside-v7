# atomic release exporter

## 実施

- canonical JSON SHA-256を実装。
- index/search/tag/taxonomy/alias/detailのreleaseId、video集合、tag参照を検証。
- candidateを一時directoryへcopyし、検証成功後だけversion directoryへrename。
- version directory確定後にだけ`latest.json`をatomic replace。
- invalid release後も直前latestを維持。
- compliance purgeがbaseにないvideoまたはtagを追加する場合に拒否。

## 検証

- Ruff: pass
- Pyright strict: pass
- Pytest: 13 tests pass
- Coverage: 69%

## 未対応

- artifactFlagsとartifact object/hashの全双方向検証。
- release catalog、直前2版rollback、CDN purge連携。
- exporter inputをcollector/processor出力から構築するprocessor。
