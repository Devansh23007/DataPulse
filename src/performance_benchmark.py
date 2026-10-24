
from pathlib import Path
import os
import subprocess
import sys
import time

import pandas as pd
import psycopg
from dotenv import load_dotenv


ROOT = Path(__file__).resolve().parent.parent
DBT_DIR = ROOT / "datapulse_dbt"
REPORT_DIR = ROOT / "docs"

load_dotenv(ROOT / ".env")

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", "5433")),
    "dbname": os.getenv("DB_NAME", "olist"),
    "user": os.getenv("DB_USER", "olist_user"),
    "password": os.getenv("DB_PASSWORD", ""),
    "connect_timeout": 10,
}


def run_stage(name, command, cwd):
    print(f"\nStarting: {name}")
    started = time.perf_counter()

    result = subprocess.run(
        command,
        cwd=cwd,
        check=False,
    )

    duration = round(time.perf_counter() - started, 3)

    record = {
        "stage": name,
        "duration_seconds": duration,
        "exit_code": result.returncode,
        "status": "PASS" if result.returncode == 0 else "FAIL",
    }

    print(f"Finished: {name} in {duration:.3f}s")

    if result.returncode != 0:
        raise RuntimeError(
            f"Stage '{name}' failed. "
            "Review the command output above."
        )

    return record


def get_warehouse_counts():
    query = """
        SELECT 'raw_orders' AS table_name, COUNT(*) AS row_count
        FROM raw.olist_orders_dataset

        UNION ALL

        SELECT 'stg_orders', COUNT(*)
        FROM analytics.stg_orders

        UNION ALL

        SELECT 'fact_order_items', COUNT(*)
        FROM analytics.fact_order_items

        UNION ALL

        SELECT 'mart_daily_sales', COUNT(*)
        FROM analytics.mart_daily_sales
    """

    with psycopg.connect(**DB_CONFIG) as conn:
        with conn.cursor() as cursor:
            cursor.execute(query)
            rows = cursor.fetchall()

    return {
        name: count
        for name, count in rows
    }


def main():
    records = []
    pipeline_started = time.perf_counter()

    stages = [
        (
            "raw_load",
            [sys.executable, "-m", "src.load_raw"],
            ROOT,
        ),
        (
            "dbt_run",
            ["dbt", "run"],
            DBT_DIR,
        ),
        (
            "dbt_test",
            ["dbt", "test"],
            DBT_DIR,
        ),
    ]

    try:
        for name, command, cwd in stages:
            records.append(run_stage(name, command, cwd))

        counts = get_warehouse_counts()

        total_duration = round(
            time.perf_counter() - pipeline_started, 3
        )

        records.append({
            "stage": "end_to_end",
            "duration_seconds": total_duration,
            "exit_code": 0,
            "status": "PASS",
        })

        report = pd.DataFrame(records)
        REPORT_DIR.mkdir(parents=True, exist_ok=True)

        report.to_csv(
            REPORT_DIR / "performance_report.csv",
            index=False,
        )

        pd.DataFrame(
            [
                {"table_name": name, "row_count": count}
                for name, count in counts.items()
            ]
        ).to_csv(
            REPORT_DIR / "warehouse_row_counts.csv",
            index=False,
        )

        print("\nPerformance report:")
        print(report.to_string(index=False))

        print("\nWarehouse row counts:")
        for name, count in counts.items():
            print(f"{name}: {count:,}")

        print(
            "\nReports saved in docs/performance_report.csv "
            "and docs/warehouse_row_counts.csv"
        )

    except Exception as exc:
        print(f"\nBenchmark failed: {exc}")
        raise


if __name__ == "__main__":
    main()
