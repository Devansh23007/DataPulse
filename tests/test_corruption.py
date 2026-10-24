
import pandas as pd

from src.quality import (
    validate_business_key,
    validate_non_negative,
)


def test_missing_order_id_is_detected():
    df = pd.DataFrame({
        "order_id": ["O1", None, "O3"]
    })

    result = validate_business_key(df, ["order_id"])

    assert result["passed"] is False
    assert result["null_key_rows"] == 1


def test_duplicate_composite_key_is_detected():
    df = pd.DataFrame({
        "order_id": ["O1", "O1"],
        "order_item_id": [1, 1],
    })

    result = validate_business_key(
        df, ["order_id", "order_item_id"]
    )

    assert result["passed"] is False
    assert result["duplicate_key_rows"] == 2


def test_negative_price_is_detected():
    df = pd.DataFrame({
        "price": [10.0, -5.0, 20.0]
    })

    result = validate_non_negative(df, "price")

    assert result["passed"] is False
    assert result["invalid_count"] == 1


def test_valid_data_passes():
    df = pd.DataFrame({
        "order_id": ["O1", "O2", "O3"]
    })

    result = validate_business_key(df, ["order_id"])

    assert result["passed"] is True
