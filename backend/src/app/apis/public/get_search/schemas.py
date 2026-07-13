from typing import Any

from pydantic import RootModel


class SearchContractResponse(RootModel[dict[str, Any]]):
    """正規検索インデックスデータ。"""
