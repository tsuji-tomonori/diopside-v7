from app.apis.public.common import OperationContract

CONTRACT = OperationContract(
    "getReleaseContract",
    "public/get-release-contract",
    "public",
    (),
    "正規リリースインデックスを1件取得する。",
    (404, 422, 500),
    "安全な読み取り",
    "none",
    "設定済み公開契約ディレクトリを読み取る",
)
