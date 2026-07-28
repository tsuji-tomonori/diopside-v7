# タイムスタンプrelease再生成

`20260729-001`を同じ入力から再生成するときは、出力releaseを`--force`で明示して実行する。`--force`なしでは既存出力を保持して停止する。

```bash
cd backend
uv run --locked python -m app.scripts.import_archive_timestamps \
  --final-root /home/t-tsuji/project/get-archives-info/timestamps/work/v1 \
  --manifest /home/t-tsuji/project/get-archives-info/timestamps/target_manifest_v1.json \
  --seed-release data/public/releases/20260711-001 \
  --output data/public/releases/20260729-001 \
  --release-id 20260729-001 \
  --generated-at 2026-07-29T00:00:00Z \
  --report /tmp/diopside-archive-timestamp-import-report.json \
  --latest-output data/public/latest.json \
  --force
```

実行後は次を確認する。

```bash
uv run --locked python -m app.scripts.verify_contract
```
