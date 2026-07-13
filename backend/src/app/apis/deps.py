from pathlib import Path
from typing import Annotated

from fastapi import Depends

from app.core.config import get_settings


def get_contract_directory() -> Path:
    """設定済みの正規公開契約ディレクトリを返す。"""
    return get_settings().contract_dir


ContractDirectory = Annotated[Path, Depends(get_contract_directory)]
