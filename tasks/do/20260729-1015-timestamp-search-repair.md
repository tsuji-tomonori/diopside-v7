# タイムスタンプ移植の検索修正

状態: 完了

## 受け入れ条件

- 移植動画の検索語をfrontendと同じ正規化・分割規則で生成する。
- `20260729-001`を同一入力から安全に再生成でき、seed 3本の検索語は保持する。
- 実release由来の移植動画が代表的な日本語検索語で検索結果に含まれるtestを追加する。
- 信頼度区分は日本語で表示し、公開enum値は変えない。
- backend、frontend、全体検証を実行し、実測結果を報告する。pushはしない。

## 計画時セルフチェック

| ID | status | evidence | rationale | follow-up |
| --- | --- | --- | --- | --- |
| MGT-003 | pass | 本taskの受け入れ条件 | 修正対象、回帰test、検証を判定可能にした | 実測で完了判定する |
| MGT-060 | pass | 検索不能、再生成、表示不備 | 検索回帰とrelease上書きを主要riskとして扱う | force時の対象を限定する |
| PRC-001 | pass | script、frontend検索、詳細画面 | 同一規則の実装と回帰testを同じ変更単位で行う | 全体検証へ進む |
| SCM-001 | pass | versioned releaseとforce手順 | 生成物を同一入力から再構築できるようにする | 旧seed語を比較する |
| QUA-001 | pass | script unit test、frontend実release test、詳細test | 変換、検索、表示を個別かつ集約で検証する | 失敗は再実行前に修正する |
| REQ-102 | pass | 利用者の修正方針 | frontend正本との規則一致を追跡する | 実release検索を確認する |
| DES-001 | pass | tokenizer、検索index、詳細画面 | 表記と検索語生成の詳細設計を更新する | 型検査で整合を確認する |
| CON-080 | pass | 移植scriptと生成release | 決定的な再生成とseed維持を実装する | contract verifierを実行する |
| TST-701 | pass | 指定回帰testと`task verify` | 実data検索と表示を自動化する | 全体検証を実行する |
| MNT-001 | pass | 既存releaseの修正 | versioned releaseを安全に再構築する | 残余riskを記録する |

## 完了時セルフチェック

| ID | status | evidence | rationale | follow-up |
| --- | --- | --- | --- | --- |
| MGT-003 | pass | 本task、作業記録、実測件数 | 修正、test、検証の完了基準を満たした | なし |
| MGT-060 | pass | `--force`、検索回帰test、再生成確認 | 上書き対象を明示し、検索不能を回帰testで防ぐ | なし |
| PRC-001 | pass | script、frontend、release、test | 変換、公開data、表示を同じ変更単位で修正した | なし |
| SCM-001 | pass | runbook、`--force`、release差分 | 再生成手順と構成状態を記録した | なし |
| QUA-001 | pass | `task verify`成功 | 狭いtestと全体検証の双方を実行した | なし |
| REQ-102 | pass | 実release検索test、表示test | frontend正本との規則一致と日本語表示を確認した | なし |
| DES-001 | pass | tokenizer、confidence map | 検索語生成と表示写像を実装した | なし |
| CON-080 | pass | script unit test、contract verifier | 同一入力から1209本を再構築した | なし |
| TST-701 | pass | backend 65件、frontend 77件、infra 4件 | 追加した分割、force、検索、表示のtestを含めて検証した | なし |
| MNT-001 | pass | seed検索語保持、旧release保持 | seed 3本を変更せず保守修正した | なし |
