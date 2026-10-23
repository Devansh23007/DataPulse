
from pathlib import Path
import pandas as pd

from src.quality import validate_business_key

ROOT_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT_DIR / "data" / "raw"
REPORT_DIR = ROOT_DIR / "docs"

KEYS = {
    "olist_customers_dataset.csv": ["customer_id"],
    "olist_orders_dataset.csv": ["order_id"],
    "olist_order_items_dataset.csv": [
        "order_id", "order_item_id"
    ],
    "olist_order_payments_dataset.csv": [
        "order_id", "payment_sequential"
    ],
    "olist_products_dataset.csv": ["product_id"],
    "olist_sellers_dataset.csv": ["seller_id"],
    "product_category_name_translation.csv": [
        "product_category_name"
    ],
}

def main():
    results = []

    for filename, keys in KEYS.items():
        path = RAW_DIR / filename

        if not path.exists():
            results.append({
                "file_name": filename,
                "status": "FAILED",
                "error": "File not found",
            })
            continue

        try:
            df = pd.read_csv(path, low_memory=False)
            result = validate_business_key(df, keys)

            results.append({
                "file_name": filename,
                "status": (
                    "PASS" if result["passed"] else "FAIL"
                ),
                "row_count": result["row_count"],
                "key_columns": ", ".join(keys),
                "null_key_rows": result["null_key_rows"],
                "duplicate_key_rows": (
                    result["duplicate_key_rows"]
                ),
                "error": "",
            })

        except Exception as exc:
            results.append({
                "file_name": filename,
                "status": "ERROR",
                "error": str(exc),
            })

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    report = pd.DataFrame(results)

    output = REPORT_DIR / "data_quality_report.csv"
    report.to_csv(output, index=False)

    print(report.to_string(index=False))
    print(f"\nReport saved to: {output}")


if __name__ == "__main__":
    main()
