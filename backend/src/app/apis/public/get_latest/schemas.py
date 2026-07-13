from typing import Any

from pydantic import RootModel


class LatestContractResponse(RootModel[dict[str, Any]]):
    """正規 `latest.json` データ。"""
