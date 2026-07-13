# ドキュメントとコードコメントの日本語統一

状態: done

## 対象

- リポジトリ管理下のドキュメントおよび生成ドキュメントにある自然言語の記述
- APIドキュメント生成元と生成結果
- ソースコード内の説明コメントとdocstring
- backendのテスト関数と `functions.py` 内の関数
- frontendおよびinfraのテストケース

## 判断

- API path、operation ID、JSON key、型名、コマンド、製品名など、契約または実行に必要な識別子は翻訳しない。
- HTMLへ埋め込まれたライブラリコードやbase64資産は、手書きコメントの監査対象外とする。
- 既存の意味や公開契約は変えず、自然言語の説明だけを日本語へ統一する。

## 受け入れ条件

- [x] Markdown、手書きHTML、README、生成Markdownの自然言語が日本語で記述されている。
- [x] APIドキュメント生成器が日本語の文書を生成し、`app-docs generate --check` が成功する。
- [x] ソースコードの説明コメントとdocstringが日本語で記述されている。
- [x] backendの全テスト関数に、目的を簡潔に説明する日本語docstringがある。
- [x] backendの全 `functions.py` 関数に、役割を簡潔に説明する日本語docstringがある。
- [x] frontendおよびinfraの各テストケースに、目的を簡潔に説明する日本語コメントがある。
- [x] 対象漏れを検査する静的テストまたは検証スクリプトを追加し、回帰を防止する。
- [x] narrow check、`task docs:check`、`task verify`、`git diff --check` が成功する。
- [x] 実行結果と残余リスクを `reports/working` に記録する。
- [x] 検証済み変更を目的単位でcommitし、public GitHubへpushする。

## 非対象

- deploy、CDK bootstrap/destroy、production変更
- 外部ライブラリ、lockfile、機械生成SVG、JSON契約値の翻訳
- `.workspace` の変更
