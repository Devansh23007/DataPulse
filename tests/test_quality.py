
import pandas as pd
import pytest

from src.quality import (
    validate_business_key,
    validate_required_columns,
    validate_non_negative,
)


def test_business_key_passes_for_unique_values():
    df = pd.DataFrame({
        "order_id": ["A", "B", "C"]
    })

    result = validate_business_key(df, ["order_id"])

    assert result["passed"] is True
    assert result["null_key_rows"] == 0
    assert result["duplicate_key_rows"] == 0


def test_business_key_detects_duplicates():
    df = pd.DataFrame({
        "order_id": ["A", "B", "A"]
    })

    result = validate_business_key(df, ["order_id"])

    assert result["passed"] is False
    assert result["duplicate_key_rows"] == 2


def test_business_key_detects_nulls():
    df = pd.DataFrame({
        "order_id": ["A", None, "C"]
    })

    result = validate_business_key(df, ["order_id"])

    assert result["passed"] is False
    assert result["null_key_rows"] == 1


def test_composite_key():
    df = pd.DataFrame({
        "order_id": ["A", "A", "B"],
        "order_item_id": [1, 2, 1],
    })

    result = validate_business_key(
        df, ["order_id", "order_item_id"]
    )

    assert result["passed"] is True


def test_missing_key_column_raises_error():
    df = pd.DataFrame({"customer_id": ["A"]})

    with pytest.raises(ValueError):
        validate_business_key(df, ["order_id"])


def test_required_columns_detect_missing_column():
    df = pd.DataFrame({"order_id": ["A"]})

    result = validate_required_columns(
        df, ["order_id", "customer_id"]
    )

    assert result["passed"] is False
    assert result["missing_columns"] == ["customer_id"]


def test_non_negative_values():
    df = pd.DataFrame({"price": [10, 20, 0]})

    result = validate_non_negative(df, "price")

    assert result["passed"] is True


def test_negative_values_are_detected():
    df = pd.DataFrame({"price": [10, -5, 20]})

    result = validate_non_negative(df, "price")

    assert result["passed"] is False
    assert result["invalid_count"] == 1
