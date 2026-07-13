# 単体テストのAAAコメント統一

状態: done

## 対象

- `backend/tests` 配下の全pytestテスト関数
- `frontend/src` 配下の全Vitest単体テストケース
- `infra/test` 配下の全Node.js単体テストケース
- 今後の欠落を防ぐ静的回帰検査

## 判断

- E2Eは受け入れテストであり、単体テストの対象外とする。
- Pythonでは `# 1. 初期化`、`# 2. テストの実行`、`# 3. アサーション` を使用する。
- TypeScriptとJavaScriptでは同じ文言を `//` コメントで使用する。
- 各コメントはテスト本体内へこの順番で一度ずつ配置し、実際の準備・操作・検証を区切る。
- 直接呼び出しを `expect` や `assert` に埋め込んで区分できない箇所は、結果変数へ分離する。

## 受け入れ条件

- [x] backendの全単体テスト関数が3つのAAAコメントを順番どおり一度ずつ持つ。
- [x] frontendの全Vitest単体テストケースが3つのAAAコメントを順番どおり一度ずつ持つ。
- [x] infraの全Node.js単体テストケースが3つのAAAコメントを順番どおり一度ずつ持つ。
- [x] AAAコメントが実際の初期化・テスト実行・アサーションを区切っている。
- [x] AAAコメント欠落・重複・順序違反を検出する静的回帰検査がある。
- [x] backend、frontend、infraのnarrow testが成功する。
- [x] `task verify`、`task docs:check`、`git diff --check` が成功する。
- [x] 実行結果と残余リスクを `reports/working` に記録する。
- [x] 検証済み変更を目的単位でcommitし、public GitHubへpushする。

## 非対象

- `frontend/e2e` のPlaywright受け入れテスト
- productionコードの振る舞い、公開API契約、UI表示値の変更
- deploy、CDK bootstrap/destroy、production変更
