# ドキュメントとコードコメントの日本語統一

## 指示と受け入れ条件

- ドキュメント、生成ドキュメント、コメントを日本語へ統一する。
- テストと `functions.py` の関数には、目的または役割を簡潔に説明する日本語コメントを必須とする。
- `docs/spec`、設計システム、タスク受け入れ条件を正本として、既存契約を変更しない。
- narrow checkから集約検証まで実行し、未実行・中断・失敗を合格として扱わない。

## 判断と成果物

- API path、operation ID、JSON key、型名、コマンド、製品名、状態列挙値は機械可読な契約識別子として保持した。
- README、仕様、設計、runbook、skill、task、既存作業報告の自然言語を日本語へ統一した。
- API契約の説明、OpenAPI、操作別Markdownを日本語化し、生成器から同じ内容を再現できるようにした。
- Pythonの説明コメントとdocstringを日本語化し、backendのテスト関数57件と `functions.py` の関数5件へ日本語docstringを追加した。
- frontendとinfraのテストケースへ日本語の目的コメントを追加し、テスト名も日本語化した。
- `backend/tests/test_japanese_content.py` を追加し、文書、コメント、docstring、テスト、Task説明、生成OpenAPIの日本語要件を回帰検査するようにした。

## 検証結果

- `uv run --locked pytest tests/test_japanese_content.py tests/tools/test_app_docs.py tests/test_main.py -q`: 5件合格。
- `task docs:check`: 合格。生成対象28ファイルが最新。
- `uv run --locked ruff check tests/test_japanese_content.py`: 合格。
- `uv run --locked ruff format --check tests/test_japanese_content.py`: 合格。
- `uv run --locked pyright tests/test_japanese_content.py`: 0エラー。
- `uv run --locked pytest tests/test_japanese_content.py -q`: 1件合格。
- `task verify`: 合格。frontend単体13件、infra 4件、backend 63件、Playwright 14件、型検査、静的解析、build、CDK synth、費用・quota検証を含む。
- `git diff --check`: 合格。

初回の `task verify` は、追加したJSON走査の型が不明としてPyright 4件で失敗した。`json.loads` の結果と再帰走査対象を `object` へ明示的に絞り、narrow checkと集約検証を再実行して解消した。sandbox内のbackend pytestはAnyIO worker threadが進まず、infraテストはDocker socket権限で停止したため、これらを合格に数えず、同じ検証をsandbox外で完走させた。

## 適合性と残余リスク

- 文書と説明コメントの日本語化、生成再現性、対象関数・テストの説明、回帰防止という受け入れ条件に適合する。
- AWS、CDK、OpenAPIなどが生成する固定キー・識別子・機械文言、および公開契約の列挙値は翻訳していない。
- deploy、CDK bootstrap/destroy、production変更、外部approval gateの判定は実施していない。
