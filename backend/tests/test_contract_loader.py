from pathlib import Path

import pytest
from fastapi import HTTPException

from app.services.contract_loader import read_public_contract


def test_read_public_contract_rejects_path_traversal(tmp_path: Path) -> None:
    """公開契約の読み取りがパストラバーサルを拒否することを検証する。"""
    # 1. 初期化
    path = "../secret.json"

    # 2. テストの実行
    with pytest.raises(HTTPException) as error:
        read_public_contract(tmp_path, path)

    # 3. アサーション
    assert error.value.status_code == 400


def test_read_public_contract_reports_invalid_json(tmp_path: Path) -> None:
    """不正なJSONを契約エラーとして報告することを検証する。"""
    # 1. 初期化
    invalid = tmp_path / "invalid.json"
    invalid.write_text("not-json", encoding="utf-8")

    # 2. テストの実行
    with pytest.raises(HTTPException) as error:
        read_public_contract(tmp_path, "invalid.json")

    # 3. アサーション
    assert error.value.status_code == 500
