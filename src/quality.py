
import pandas as pd


def validate_business_key(
    df: pd.DataFrame,
    keys: list[str],
) -> dict:
    """Validate required key columns, nulls, and duplicates."""

    missing_columns = sorted(set(keys) - set(df.columns))

    if missing_columns:
        raise ValueError(
            f"Missing business key columns: {missing_columns}"
        )

    null_key_rows = int(
        df[keys].isna().any(axis=1).sum()
    )

    duplicate_key_rows = int(
        df.duplicated(subset=keys, keep=False).sum()
    )

    return {
        "row_count": len(df),
        "key_columns": keys,
        "null_key_rows": null_key_rows,
        "duplicate_key_rows": duplicate_key_rows,
        "passed": (
            null_key_rows == 0
            and duplicate_key_rows == 0
        ),
    }


def validate_required_columns(
    df: pd.DataFrame,
    required_columns: list[str],
) -> dict:
    """Check required columns without rejecting extra columns."""

    missing = sorted(
        set(required_columns) - set(df.columns)
    )

    return {
        "passed": len(missing) == 0,
        "missing_columns": missing,
    }


def validate_non_negative(
    df: pd.DataFrame,
    column: str,
) -> dict:
    """Check whether a numeric column has negative values."""

    if column not in df.columns:
        raise ValueError(f"Column not found: {column}")

    values = pd.to_numeric(df[column], errors="coerce")

    invalid_count = int(
        (values.isna() | (values < 0)).sum()
    )

    return {
        "column": column,
        "invalid_count": invalid_count,
        "passed": invalid_count == 0,
    }
