from typing import Any

from pydantic import RootModel


class SearchContractResponse(RootModel[dict[str, Any]]):
    """Canonical search index payload."""
