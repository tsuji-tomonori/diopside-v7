from app.apis.public.common import OperationContract

CONTRACT = OperationContract(
    "getReleaseTagsContract",
    "public/get-release-tags-contract",
    "public",
    (),
    "分類体系、タグインデックス、別名投影を取得する。",
    (404, 422, 500),
    "安全な読み取り",
    "none",
    "設定済み公開契約ディレクトリを読み取る",
)
