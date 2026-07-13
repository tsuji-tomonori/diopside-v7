from app.apis.public.common import OperationContract

CONTRACT = OperationContract(
    "getReleaseVideoContract",
    "public/get-release-video-contract",
    "public",
    (),
    "Read one public video detail.",
    (404, 422, 500),
    "safe read",
    "none",
    "reads the configured public contract directory",
)
