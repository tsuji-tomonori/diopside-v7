from typing import Any

from pydantic import RootModel


class LatestContractResponse(RootModel[dict[str, Any]]):
    """Canonical latest.json payload."""
