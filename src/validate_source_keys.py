
from pathlib import Path
import pandas as pd

RAW_DIR = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "raw"
)

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
    for filename, keys in KEYS.items():
        path = RAW_DIR / filename
        df = pd.read_csv(path, low_memory=False)

        missing_columns = set(keys) - set(df.columns)

        if missing_columns:
            print(f"\n{filename}: MISSING KEY COLUMNS")
            print(sorted(missing_columns))
            continue

        null_key_rows = df[keys].isna().any(axis=1).sum()
        duplicate_key_rows = df.duplicated(
            subset=keys, keep=False
        ).sum()

        print(f"\n{filename}")
        print(f"Candidate key: {keys}")
        print(f"Null-key rows: {null_key_rows}")
        print(f"Rows with duplicate keys: {duplicate_key_rows}")

if __name__ == "__main__":
    main()
