# UI全面書き直し Phase 8: PR用視覚証跡と本文準備

状態: done

## 受入条件

- `docs/evidence/ui-rewrite-20260726/`へ、PRに必要な16〜20枚のPNGと、各画像の正本対応を示すREADMEを追加する。合計は2MB以内を目安とする。
- `reports/working/20260726-pr-body.md`へ、実測済みの検証値、不適合の修正、設計判断、既知の未対応を含む日本語のPR本文下書きを追加する。
- `reports/working/20260726-pr-comments.md`へ、`__RAW_BASE__`を用いた画像付きの日本語PRコメント4本を追加する。
- `cd backend && .venv/bin/python -m pytest -q`と`task verify`を実行し、結果を適合レポートへ記録する。commit、push、PR作成、PRコメント投稿はしない。

## 計画時セルフチェック

| ID | status | evidence | rationale | follow-up |
| --- | --- | --- | --- | --- |
| MGT-003 | pass | 本taskの受入条件 | 成果物の配置、枚数・容量、検証command、非実施操作を第三者が判定できる形で定義した | 検証後に実測値へ更新する |
| PRC-001 | pass | 正本、private PNG、PR下書き対象 | 既存の実装証跡を公開用に選定・対応付け、本文とコメントを同じ変更単位で整備する | 容量とリンクを確認する |
| SCM-001 | pass | `.gitignore`、対象path、commit禁止 | private証跡を追跡対象の`docs/evidence/`へ限定して複製し、元ファイルを変更しない | `git diff --check`で確認する |
| QUA-001 | pass | 既存の実測適合表、backend pytest、`task verify` | 視覚証跡と実測検証を分けて示し、未実施の外部検証を合格扱いにしない | 実行結果をreportへ記録する |
| REQ-102, DES-001 | pass | `docs/spec/`、design-system、wireframes、component-implementation | 画像ごとに正本と証明対象を追跡可能にする | READMEをレビューする |
| TST-801 | pass | backend pytest 63 passed、`task verify`終了コード0 | 指定されたbackend pytestとaggregate検証を実行し、すべて完走した | UI変更時は再実行する |
