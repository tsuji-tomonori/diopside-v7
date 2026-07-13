from typing import Any

from pydantic import BaseModel


class TagsContractResponse(BaseModel):
    taxonomy: dict[str, Any]
    index: dict[str, Any]
    alias: dict[str, Any]
