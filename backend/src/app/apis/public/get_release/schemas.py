from typing import Any

from pydantic import RootModel


class ReleaseContractResponse(RootModel[dict[str, Any]]):
    """正規リリースインデックスデータ。"""
