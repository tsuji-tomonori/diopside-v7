from app.apis.public.common import OperationContract

CONTRACT = OperationContract(
    "getReleaseSearchContract",
    "public/get-release-search-contract",
    "public",
    (),
    "リリースの検索インデックスを1件取得する。",
    (404, 422, 500),
    "安全な読み取り",
    "none",
    "設定済み公開契約ディレクトリを読み取る",
)
