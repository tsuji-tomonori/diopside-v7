# RPK0UVHEYVY タイムスタンプ作成・レビュー記録

- 対象: 台帳64行、`RPK0UVHEYVY`のみ。
- 入力: 日本語自動字幕 1,211,682 bytes、5,261 cue、SHA-256 `260fb540cf689bc06f2f05a81a0787974be2938906da65b76ced0f278d000c96`。
- コメント: 上位20件を再取得。全編章リストはなかったため補助資料に限定した。
- 作成: 字幕全編を意味単位で確認し、各境界の最近傍cueを`final.json`へ固定した18章。
- 事実レビュー: 合格。各境界と章名は近傍字幕で裏付けられ、字幕誤認識断片を章名へ転記していない。
- 編集レビュー: 合格。長すぎる章、曖昧な章名、重複、時刻逆転、動画長超過はない。
- 公開: 有効なrelease `20260804-005`をseedとしてrelease `20260804-010`を正規生成。1,216動画、動画ID重複0。

## セルフチェック

| ID | status | evidence | rationale | follow-up |
| --- | --- | --- | --- | --- |
| SCM-085 | pass | 1動画1commitと台帳commit SHA | 動画から公開releaseと変更履歴を追跡できる | なし |
| SCM-103 | pass | 字幕bytes、cue数、SHA-256 | 入力字幕の同一性を検証できる | なし |
| SCM-140 | pass | importerとcontract verifier | 正本手順でreleaseを再生成した | なし |
| QUA-071 | pass | 事実・編集レビューとvalidator | 通過条件を客観的に判定した | なし |
| QUA-090 | pass | JSONレビュー記録 | 事実と編集の別観点レビューを記録した | なし |
| AI-012 | pass | 全編字幕の意味レビュー | 自動候補だけで完了判定していない | なし |
| AI-025 | pass | provenance、evidenceRefs、review report | 入力・出力・判断の監査証跡がある | なし |
