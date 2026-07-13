from app.apis.public.common import OperationContract

CONTRACT = OperationContract(
    "getReleaseSearchContract",
    "public/get-release-search-contract",
    "public",
    (),
    "Read one release search index.",
    (404, 422, 500),
    "safe read",
    "none",
    "reads the configured public contract directory",
)
