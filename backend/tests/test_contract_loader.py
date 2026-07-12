from pathlib import Path

import pytest
from fastapi import HTTPException

from app.services.contract_loader import read_public_contract


def test_read_public_contract_rejects_path_traversal(tmp_path: Path) -> None:
    with pytest.raises(HTTPException) as error:
        read_public_contract(tmp_path, "../secret.json")

    assert error.value.status_code == 400


def test_read_public_contract_reports_invalid_json(tmp_path: Path) -> None:
    invalid = tmp_path / "invalid.json"
    invalid.write_text("not-json", encoding="utf-8")

    with pytest.raises(HTTPException) as error:
        read_public_contract(tmp_path, "invalid.json")

    assert error.value.status_code == 500
