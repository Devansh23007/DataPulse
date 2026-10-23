
from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = PROJECT_ROOT / "data" / "raw"
REPORT_DIR = PROJECT_ROOT / "docs"

def inspect_csv(file_path: Path) -> dict:
    df = pd.read_csv(file_path, low_memory=False)

    print(f"\n{'=' * 70}")
    print(f"FILE: {file_path.name}")
    print(f"ROWS: {len(df):,}")
    print(f"COLUMNS: {len(df.columns)}")
    print(f"DUPLICATE ROWS: {df.duplicated().sum():,}")

    print("\nCOLUMN DETAILS:")
    print(
        pd.DataFrame({
            "column": df.columns,
            "dtype": df.dtypes.astype(str).values,
            "missing_count": df.isna().sum().values,
            "missing_percent": (
                df.isna().mean().values * 100
            ).round(2),
            "distinct_values": df.nunique().values,
        }).to_string(index=False)
    )

    print("\nSAMPLE RECORDS:")
    print(df.head(3).to_string(index=False))

    return {
        "file_name": file_path.name,
        "row_count": len(df),
        "column_count": len(df.columns),
        "duplicate_rows": int(df.duplicated().sum()),
    }


def main():
    if not RAW_DIR.exists():
        raise FileNotFoundError(f"Raw directory not found: {RAW_DIR}")

    csv_files = sorted(RAW_DIR.glob("*.csv"))

    if not csv_files:
        raise FileNotFoundError(
            f"No CSV files found in {RAW_DIR}"
        )

    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    results = []

    for file_path in csv_files:
        try:
            results.append(inspect_csv(file_path))
        except Exception as exc:
            print(f"ERROR inspecting {file_path.name}: {exc}")
            raise

    summary = pd.DataFrame(results)
    output_path = REPORT_DIR / "dataset_inventory.csv"
    summary.to_csv(output_path, index=False)

    print("\n" + "=" * 70)
    print("DATASET INVENTORY")
    print(summary.to_string(index=False))
    print(f"\nInventory saved to: {output_path}")


if __name__ == "__main__":
    main()
