# 通常公開アーカイブの入力監査・タイムスタンプ追加

## 指示と対象

年齢制限動画は一時スキップし、それ以外の未完了動画で実行可能な字幕取得、章立て、独立レビュー、公開データ追加を行い、完了不能理由をGoogle Sheetsへ記録する。

## 実施結果

- 未完了600本のうち584本を入力監査した。
- 日本語字幕取得済み429本、字幕なし・音声取得不能118本、年齢制限37本、ネットワーク承認中断による未監査16本へ分類した。
- Google Sheetsの対象600行へ、処理状態、更新日、動画別の停止理由を反映した。
- コメント取得済み動画から章候補を生成し、事実レビューと編集レビューを独立実行した。
- 未裏付け境界、字幕誤認識由来の章名、長すぎる章を不合格とし、推測生成は公開しなかった。
- `SGb6h-EOuKg`のみ6章が両レビューとvalidatorに合格したため、release `20260804-002`へ追加した。
- releaseは1,211本、videoId重複0件である。

## 検証

- `validate_final.py /tmp/diopside-final-approved/SGb6h-EOuKg/final.json`: 合格
- `git diff --check`: 合格
- `cd backend && uv run --locked python -m app.scripts.verify_contract`: 合格（release `20260804-002`、1,211本）
- `cd backend && uv run --locked pytest tests/test_import_archive_timestamps.py -q`: 2件合格

## 指示へのfitと未対応

年齢制限以外で入力・証拠・独立レビューを満たした成果は公開データへ反映し、満たせない動画はGoogle Sheetsへ理由を記録した。全件のタイムスタンプ生成は未達である。字幕なし動画の音声CDN遮断、入力監査16本のネットワーク承認中断、字幕取得済み動画の意味レビュー不合格が残る。未実行・不合格を作成済みとして扱っていない。
