# get-archives-infoタイムスタンプ移植と表示

状態: 完了

## 受け入れ条件

- `approved` の生成結果を入力として、新release `20260729-001` に既存seed 3本と移植対象動画を収録する。
- 入力、出力、release識別子は移植scriptの引数で指定でき、参照元への書込みを行わない。
- 公開データは許可されたタイムスタンプ値だけを持ち、内部証跡を含まない。
- manifestに存在する動画は実title、公開日時、長さを使い、存在しない動画は理由と件数を記録して除外する。
- 公開契約、一覧、検索、詳細表示、unit testを更新し、itemsがないタイムスタンプ節は表示しない。
- `latest.json` は新releaseを指し、旧releaseは保持する。
- 指定したbackend、frontend、全体検証を実行し、実測結果と未対応を報告へ記録する。
- 目的単位で日本語commitを作成し、生成データがcommit対象であることを確認する。pushはしない。

## 計画時セルフチェック

| ID | status | evidence | rationale | follow-up |
| --- | --- | --- | --- | --- |
| MGT-003 | pass | 本taskの受け入れ条件 | 成果物、対象件数、検証を判定可能な形で定義した | 実測値で終結判定する |
| MGT-060 | pass | 参照元保護、内部証跡非公開、旧release保持 | データ漏えい、回帰、意図しない削除を主要リスクとして扱う | 生成後に公開禁止値を検査する |
| PRC-001 | pass | 本taskの工程と狭い検証から全体検証への順序 | 既存release互換を保つ増分移植として進める | 各工程の結果を報告へ記録する |
| SCM-001 | pass | versioned release、`latest.json`、移植script | 構成項目、生成手順、release切替をGit管理する | 生成データをcommit前に確認する |
| QUA-001 | pass | contract verifier、unit test、型検査、E2E | 公開値と表示を独立した検証で保証する | 失敗時は原因を修正して再実行する |
| REQ-102 | pass | 利用者承認済み確定仕様、要件定義20章 | 公開禁止値と表示条件を追跡する | 公開JSONを機械検査する |
| DES-001 | pass | 公開contractと`DetailPage.tsx` | optionalなconfidenceLevelと非表示条件を詳細設計へ反映する | UI unit testで確認する |
| CON-080 | pass | 移植script、contract、release生成物 | 再現可能な変換と最小公開値を実装する | unit testとcontract verifierを実行する |
| TST-701 | pass | script unit test、詳細表示unit test | 入力検証、公開値、empty表示を自動化する | 狭いtestから全体検証へ進む |
| MNT-001 | pass | versioned releaseの追加と旧release保持 | 既存seed資産を残した保守的な移行とする | 回帰期待値を新releaseへ更新する |

## 完了時セルフチェック

| ID | status | evidence | rationale | follow-up |
| --- | --- | --- | --- | --- |
| MGT-003 | pass | 受け入れ条件、`reports/working/20260729-001-archive-timestamps.md` | 成果物、実測件数、検証結果を対応付けた | 入力更新時に再移植する |
| MGT-060 | pass | 公開禁止語の生成release検査 | 内部証跡を公開releaseへ複写しなかった | 入力schema変更時に禁止語を見直す |
| PRC-001 | pass | 移植script、unit test、全体検証 | 計画した工程順で実装と検証を完了した | なし |
| SCM-001 | pass | `20260729-001`、`latest.json`、旧release保持 | versioned releaseとして構成を追加し、Git管理対象を確認した | なし |
| QUA-001 | pass | `task verify`成功 | 型、unit、build、契約、CDK、E2Eを含む検証を実行した | なし |
| REQ-102 | pass | 最小公開値、除外記録、表示test | 公開禁止値、実値利用、非表示要件を追跡した | `completedAt`不足は入力側で補完後に再移植する |
| DES-001 | pass | 三層contract、`DetailPage.tsx`、unit test | `confidenceLevel`とタイムスタンプ節の条件表示を実装した | なし |
| CON-080 | pass | `import_archive_timestamps.py`とunit test | CLI入力で決定的にreleaseを構築し、内部値を投影しない | なし |
| TST-701 | pass | backend 64件、frontend 76件、infra 4件、E2E | script、公開contract、表示条件、回帰資産を検証した | なし |
| MNT-001 | pass | seed 3本保持、新release 1209本 | 旧releaseを削除せず、seed互換を維持した | なし |
