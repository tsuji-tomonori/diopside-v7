# getReleaseSearchContract インターフェース(自動生成)

- メソッド: `GET`
- パス: `/api/contracts/releases/{release_id}/search`
- 概要: リリースの検索インデックスを1件取得する。
- 認証: public
- 権限: なし
- セキュリティ要件: なし(公開読み取り)

## パラメーター

| 名前 | 場所 | 必須 | スキーマ |
| --- | --- | --- | --- |
| `release_id` | path | true | `string` |

## レスポンス

| 状態 | 説明 | スキーマ |
| ---: | --- | --- |
| 200 | 成功レスポンス | `#/components/schemas/SearchContractResponse` |
| 404 | 要求された正規契約成果物が見つからない。 | `なし` |
| 422 | パスパラメーターの検証に失敗した。 | `なし` |
| 500 | 保存済みの正規契約が不正または不整合である。 | `なし` |

## トレーサビリティ

- 要件: FR-EXP-001, FR-FE-002, FR-FE-010
- 仕様: SPEC-DATA-PUB-001, SPEC-UI-SEARCH-001
- 受け入れ条件: AC-DATA-01, AC-FE-02, AC-FE-05
