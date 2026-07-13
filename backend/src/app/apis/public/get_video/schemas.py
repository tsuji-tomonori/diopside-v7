from typing import Any

from pydantic import RootModel


class VideoContractResponse(RootModel[dict[str, Any]]):
    """Canonical video detail payload."""
