from app.apis.public.common import OperationContract

CONTRACT = OperationContract(
    "getReleaseContract",
    "public/get-release-contract",
    "public",
    (),
    "Read one canonical release index.",
    (404, 422, 500),
    "safe read",
    "none",
    "reads the configured public contract directory",
)
