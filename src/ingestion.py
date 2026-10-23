
from pathlib import Path
import hashlib
import json
import logging
import sys
import time
from datetime import datetime, timezone

import pandas as pd


ROOT_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT_DIR / "data" / "raw"
LOG_DIR = ROOT_DIR / "logs"
LOG_FILE = LOG_DIR / "ingestion.jsonl"

CHUNK_SIZE = 10_000


# Required columns for each source file.
SCHEMAS = {
    "olist_customers_dataset.csv": [
        "customer_id",
        "customer_unique_id",
        "customer_zip_code_prefix",
        "customer_city",
        "customer_state",
    ],
    "olist_geolocation_dataset.csv": [
        "geolocation_zip_code_prefix",
        "geolocation_lat",
        "geolocation_lng",
        "geolocation_city",
        "geolocation_state",
    ],
    "olist_order_items_dataset.csv": [
        "order_id",
        "order_item_id",
        "product_id",
        "seller_id",
        "shipping_limit_date",
        "price",
        "freight_value",
    ],
    "olist_order_payments_dataset.csv": [
        "order_id",
        "payment_sequential",
        "payment_type",
        "payment_installments",
        "payment_value",
    ],
    "olist_order_reviews_dataset.csv": [
        "review_id",
        "order_id",
        "review_score",
        "review_comment_title",
        "review_comment_message",
        "review_creation_date",
        "review_answer_timestamp",
    ],
    "olist_orders_dataset.csv": [
        "order_id",
        "customer_id",
        "order_status",
        "order_purchase_timestamp",
        "order_approved_at",
        "order_delivered_carrier_date",
        "order_delivered_customer_date",
        "order_estimated_delivery_date",
    ],
    "olist_products_dataset.csv": [
        "product_id",
        "product_category_name",
        "product_name_lenght",
        "product_description_lenght",
        "product_photos_qty",
        "product_weight_g",
        "product_length_cm",
        "product_height_cm",
        "product_width_cm",
    ],
    "olist_sellers_dataset.csv": [
        "seller_id",
        "seller_zip_code_prefix",
        "seller_city",
        "seller_state",
    ],
    "product_category_name_translation.csv": [
        "product_category_name",
        "product_category_name_english",
    ],
}


class JsonFormatter(logging.Formatter):
    def format(self, record):
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
        }

        if hasattr(record, "event_data"):
            entry.update(record.event_data)

        if record.exc_info:
            entry["exception"] = self.formatException(
                record.exc_info
            )

        return json.dumps(entry, default=str)


def configure_logging():
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger("olist_ingestion")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()
    logger.propagate = False

    formatter = JsonFormatter()

    file_handler = logging.FileHandler(
        LOG_FILE, encoding="utf-8"
    )
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


def log_event(logger, level, message, **fields):
    logger.log(
        level,
        message,
        extra={"event_data": fields},
    )


def calculate_batch_id(file_path):
    """Return a stable ID based on the complete file contents."""
    digest = hashlib.sha256()

    with file_path.open("rb") as file:
        for chunk in iter(
            lambda: file.read(1024 * 1024), b""
        ):
            digest.update(chunk)

    return digest.hexdigest()


def validate_file(file_path, required_columns):
    if not file_path.exists():
        raise FileNotFoundError(
            f"Source file not found: {file_path.name}"
        )

    if not file_path.is_file():
        raise ValueError("Source path is not a file")

    if file_path.stat().st_size == 0:
        raise ValueError("Source file is empty")

    # Read only the header first.
    actual_columns = pd.read_csv(
        file_path, nrows=0
    ).columns.tolist()

    if len(actual_columns) != len(set(actual_columns)):
        raise ValueError("Duplicate column names detected")

    missing = sorted(
        set(required_columns) - set(actual_columns)
    )

    unexpected = sorted(
        set(actual_columns) - set(required_columns)
    )

    if missing:
        raise ValueError(
            f"Missing required columns: {missing}"
        )

    # Extra columns are reported, not automatically rejected.
    # This allows us to detect source schema changes.
    return actual_columns, unexpected


def count_rows(file_path):
    total = 0

    for chunk in pd.read_csv(
        file_path,
        chunksize=CHUNK_SIZE,
        low_memory=False,
    ):
        total += len(chunk)

    return total


def inspect_source(file_name, required_columns, logger):
    file_path = RAW_DIR / file_name
    batch_id = None
    start_time = time.perf_counter()

    try:
        columns, unexpected = validate_file(
            file_path, required_columns
        )

        batch_id = calculate_batch_id(file_path)
        row_count = count_rows(file_path)

        duration_seconds = round(
            time.perf_counter() - start_time, 3
        )

        log_event(
            logger,
            logging.INFO,
            "Source validated successfully",
            file_name=file_name,
            batch_id=batch_id,
            row_count=row_count,
            column_count=len(columns),
            file_size_bytes=file_path.stat().st_size,
            duration_seconds=duration_seconds,
            unexpected_columns=unexpected,
            status="SUCCESS",
        )

        return {
            "file_name": file_name,
            "batch_id": batch_id,
            "row_count": row_count,
            "column_count": len(columns),
            "status": "SUCCESS",
            "error": "",
        }

    except Exception as exc:
        log_event(
            logger,
            logging.ERROR,
            "Source validation failed",
            file_name=file_name,
            batch_id=batch_id,
            duration_seconds=round(
                time.perf_counter() - start_time, 3
            ),
            status="FAILED",
            error=str(exc),
        )

        return {
            "file_name": file_name,
            "batch_id": batch_id,
            "row_count": None,
            "column_count": None,
            "status": "FAILED",
            "error": str(exc),
        }


def main():
    logger = configure_logging()

    if not RAW_DIR.is_dir():
        raise FileNotFoundError(
            f"Raw data directory does not exist: {RAW_DIR}"
        )

    results = []

    for file_name, required_columns in SCHEMAS.items():
        results.append(
            inspect_source(
                file_name, required_columns, logger
            )
        )

    summary = pd.DataFrame(results)

    report_path = ROOT_DIR / "docs" / "ingestion_report.csv"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    summary.to_csv(report_path, index=False)

    successful = int(
        (summary["status"] == "SUCCESS").sum()
    )
    failed = len(summary) - successful

    log_event(
        logger,
        logging.INFO if failed == 0 else logging.ERROR,
        "Ingestion preflight completed",
        total_files=len(summary),
        successful_files=successful,
        failed_files=failed,
        report_path=str(report_path),
    )

    print(f"\nSuccessful files: {successful}")
    print(f"Failed files: {failed}")
    print(f"Report: {report_path}")
    print(f"Logs: {LOG_FILE}")

    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
