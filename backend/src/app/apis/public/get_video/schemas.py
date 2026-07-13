from typing import Any

from pydantic import RootModel


class VideoContractResponse(RootModel[dict[str, Any]]):
    """正規動画詳細データ。"""
