
from pathlib import Path
import logging
import os
import sys
import time

import pandas as pd
import psycopg
from dotenv import load_dotenv
from psycopg import sql

from src.ingestion import (
    RAW_DIR,
    SCHEMAS,
    calculate_batch_id,
    validate_file,
    configure_logging,
    log_event,
)

ROOT_DIR = Path(__file__).resolve().parent.parent
CHUNK_SIZE = 5_000


def get_connection():
    load_dotenv(ROOT_DIR / ".env")

    required = [
        "DB_HOST",
        "DB_PORT",
        "DB_NAME",
        "DB_USER",
        "DB_PASSWORD",
    ]
    missing = [key for key in required if not os.getenv(key)]

    if missing:
        raise ValueError(
            f"Missing database settings: {missing}"
        )

    return psycopg.connect(
        host=os.environ["DB_HOST"],
        port=os.environ["DB_PORT"],
        dbname=os.environ["DB_NAME"],
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        connect_timeout=10,
    )


def setup_database(conn):
    with conn.transaction():
        conn.execute(
            "CREATE SCHEMA IF NOT EXISTS raw"
        )

        conn.execute("""
            CREATE TABLE IF NOT EXISTS raw.ingestion_batches (
                batch_id TEXT PRIMARY KEY,
                source_file TEXT NOT NULL,
                row_count BIGINT NOT NULL,
                loaded_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
        """)


def load_file(conn, filename, required_columns, logger):
    path = RAW_DIR / filename
    started = time.perf_counter()

    # Validate before opening the database transaction.
    columns, unexpected = validate_file(
        path, required_columns
    )
    batch_id = calculate_batch_id(path)
    table_name = Path(filename).stem

    with conn.transaction():
        existing = conn.execute(
            """
            SELECT row_count
            FROM raw.ingestion_batches
            WHERE batch_id = %s
            """,
            (batch_id,),
        ).fetchone()

        if existing:
            log_event(
                logger,
                logging.INFO,
                "Batch already loaded; skipping",
                file_name=filename,
                batch_id=batch_id,
                row_count=existing[0],
                status="SKIPPED",
            )
            return "SKIPPED", existing[0]

        # Create a raw table with source columns as TEXT.
        column_definitions = sql.SQL(", ").join(
            sql.SQL("{} TEXT").format(sql.Identifier(col))
            for col in columns
        )

        conn.execute(
            sql.SQL(
                "CREATE TABLE IF NOT EXISTS {}.{} ({})"
            ).format(
                sql.Identifier("raw"),
                sql.Identifier(table_name),
                column_definitions,
            )
        )

        insert_query = sql.SQL(
            "INSERT INTO {}.{} ({}) VALUES ({})"
        ).format(
            sql.Identifier("raw"),
            sql.Identifier(table_name),
            sql.SQL(", ").join(
                sql.Identifier(col) for col in columns
            ),
            sql.SQL(", ").join(
                sql.Placeholder() for _ in columns
            ),
        )

        total_rows = 0

        for chunk in pd.read_csv(
            path,
            dtype=str,
            chunksize=CHUNK_SIZE,
            keep_default_na=False,
        ):
            # Preserve strings. Represent empty CSV fields
            # as SQL NULL in the raw table.
            chunk = chunk.astype(object).where(
                chunk != "", None
            )

            records = list(chunk.itertuples(
                index=False, name=None
            ))

            if records:
                with conn.cursor() as cur:
                    cur.executemany(
                        insert_query, records
                    )

            total_rows += len(records)

        conn.execute(
            """
            INSERT INTO raw.ingestion_batches
                (batch_id, source_file, row_count)
            VALUES (%s, %s, %s)
            """,
            (batch_id, filename, total_rows),
        )

    # The transaction has committed successfully here.
    log_event(
        logger,
        logging.INFO,
        "Raw table loaded",
        file_name=filename,
        table_name=f"raw.{table_name}",
        batch_id=batch_id,
        row_count=total_rows,
        unexpected_columns=unexpected,
        duration_seconds=round(
            time.perf_counter() - started, 3
        ),
        status="SUCCESS",
    )

    return "SUCCESS", total_rows


def main():
    logger = configure_logging()

    try:
        with get_connection() as conn:
            setup_database(conn)

            results = []

            for filename, required_columns in SCHEMAS.items():
                try:
                    status, rows = load_file(
                        conn,
                        filename,
                        required_columns,
                        logger,
                    )
                    results.append(
                        (filename, status, rows)
                    )
                except Exception as exc:
                    results.append(
                        (filename, "FAILED", None)
                    )
                    log_event(
                        logger,
                        logging.ERROR,
                        "Raw load failed",
                        file_name=filename,
                        error=str(exc),
                        status="FAILED",
                    )

            print("\nRAW LOAD SUMMARY")
            for filename, status, rows in results:
                print(
                    f"{filename}: {status}, rows={rows}"
                )

            failures = sum(
                status == "FAILED"
                for _, status, _ in results
            )

            print(f"\nFailed files: {failures}")

            if failures:
                sys.exit(1)

    except Exception:
        logger.exception("Database connection or setup failed")
        raise


if __name__ == "__main__":
    main()
