
import pandas as pd
import pytest

from src.ingestion import validate_file


def test_missing_file_is_rejected(tmp_path):
    missing_file = tmp_path / "missing.csv"

    with pytest.raises(FileNotFoundError):
        validate_file(missing_file, ["order_id"])


def test_empty_file_is_rejected(tmp_path):
    empty_file = tmp_path / "empty.csv"
    empty_file.write_text("", encoding="utf-8")

    with pytest.raises(ValueError, match="empty"):
        validate_file(empty_file, ["order_id"])


def test_missing_required_column_is_rejected(tmp_path):
    file_path = tmp_path / "orders.csv"

    pd.DataFrame({
        "customer_id": ["C1"]
    }).to_csv(file_path, index=False)

    with pytest.raises(ValueError, match="Missing"):
        validate_file(
            file_path, ["order_id", "customer_id"]
        )


def test_valid_file_passes(tmp_path):
    file_path = tmp_path / "orders.csv"

    pd.DataFrame({
        "order_id": ["O1"],
        "customer_id": ["C1"],
    }).to_csv(file_path, index=False)

    columns, unexpected = validate_file(
        file_path, ["order_id", "customer_id"]
    )

    assert columns == ["order_id", "customer_id"]
    assert unexpected == []


def test_extra_column_is_reported(tmp_path):
    file_path = tmp_path / "orders.csv"

    pd.DataFrame({
        "order_id": ["O1"],
        "customer_id": ["C1"],
        "extra_field": ["X"],
    }).to_csv(file_path, index=False)

    columns, unexpected = validate_file(
        file_path, ["order_id", "customer_id"]
    )

    assert "extra_field" in unexpected
