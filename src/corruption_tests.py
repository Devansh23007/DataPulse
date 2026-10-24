
import pandas as pd

from src.quality import (
    validate_business_key,
    validate_non_negative,
)


def run_corruption_tests():
    results = []

    def record(name, passed, details):
        results.append({
            "test_name": name,
            "status": "PASS" if passed else "FAIL",
            "details": details,
        })

    # Test 1: Missing business key
    missing_id = pd.DataFrame({
        "order_id": ["O1", None, "O3"]
    })
    result = validate_business_key(
        missing_id, ["order_id"]
    )
    record(
        "missing_order_id",
        not result["passed"] and result["null_key_rows"] == 1,
        f"Detected {result['null_key_rows']} rows with null keys",
    )

    # Test 2: Duplicate composite key
    duplicate_items = pd.DataFrame({
        "order_id": ["O1", "O1", "O2"],
        "order_item_id": [1, 1, 1],
    })
    result = validate_business_key(
        duplicate_items, ["order_id", "order_item_id"]
    )
    record(
        "duplicate_order_item_key",
        not result["passed"]
        and result["duplicate_key_rows"] == 2,
        f"Detected {result['duplicate_key_rows']} duplicate-key rows",
    )

    # Test 3: Negative price
    invalid_prices = pd.DataFrame({
        "price": [100.0, -25.0, 50.0]
    })
    result = validate_non_negative(invalid_prices, "price")
    record(
        "negative_price",
        not result["passed"] and result["invalid_count"] == 1,
        f"Detected {result['invalid_count']} invalid price values",
    )

    # Test 4: Broken product relationship
    order_items = pd.DataFrame({
        "product_id": ["P1", "P2", "P3"]
    })
    products = pd.DataFrame({
        "product_id": ["P1", "P3"]
    })

    unmatched = order_items[
        ~order_items["product_id"].isin(products["product_id"])
    ]

    record(
        "missing_product_relationship",
        len(unmatched) == 1,
        f"Detected {len(unmatched)} order items with missing products",
    )

    # Test 5: Valid data should pass
    valid_orders = pd.DataFrame({
        "order_id": ["O1", "O2", "O3"]
    })
    result = validate_business_key(
        valid_orders, ["order_id"]
    )
    record(
        "valid_orders",
        result["passed"],
        "Valid unique order IDs accepted",
    )

    report = pd.DataFrame(results)

    print("\nDATA CORRUPTION TEST REPORT")
    print("=" * 60)
    print(report.to_string(index=False))

    failed = int((report["status"] == "FAIL").sum())
    print(f"\nTests: {len(report)}, Failed: {failed}")

    return report


if __name__ == "__main__":
    report = run_corruption_tests()
    report.to_csv(
        "docs/corruption_test_report.csv",
        index=False,
    )

    if (report["status"] == "FAIL").any():
        raise SystemExit("Some corruption tests failed.")

    print("\nAll corruption tests passed.")
