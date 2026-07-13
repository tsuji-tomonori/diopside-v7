from app.apis.public.common import OperationContract

CONTRACT = OperationContract(
    "getReleaseTagsContract",
    "public/get-release-tags-contract",
    "public",
    (),
    "Read taxonomy, tag index, and alias projections.",
    (404, 422, 500),
    "safe read",
    "none",
    "reads the configured public contract directory",
)
