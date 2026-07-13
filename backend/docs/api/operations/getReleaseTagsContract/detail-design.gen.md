# getReleaseTagsContract 詳細設計(自動生成)

- 安定契約スラッグ: `public/get-release-tags-contract`
- ビジネス関数: `read_tags_contract`
- 認証: public
- 権限: なし
- 冪等性: 安全な読み取り
- トランザクション境界: none
- 外部影響: 設定済み公開契約ディレクトリを読み取る

## ソースの責務

| 関心事 | ソース |
| --- | --- |
| contract | `src/app/apis/public/get_tags/contract.py` |
| router | `src/app/apis/public/get_tags/router.py` |
| functions | `src/app/apis/public/get_tags/functions.py` |
| schemas | `src/app/apis/public/get_tags/schemas.py` |
| samples | `src/app/apis/public/get_tags/samples.py` |

## リソース境界

- 契約ローダー呼び出し: `contract_loader.read_taxonomy`, `contract_loader.read_tag_index`, `contract_loader.read_alias_index`
- データベース/SQL: 非該当。この操作はバージョン付きファイルシステム成果物を読み取る。
- プロバイダーSDK: 非該当。操作層はプロバイダーアダプターをimportしない。
- 変更/切り戻し: 非該当。トランザクションを伴わない安全な読み取りである。

## 互換性

- 操作ID `getReleaseTagsContract` とパス `/api/contracts/releases/{release_id}/tags` は安定している。
- レスポンスデータの検証責務は正規公開契約モデルが持つ。
- 後方互換性のない公開スキーマ変更には、メジャースキーマまたはパスの移行が必要である。
