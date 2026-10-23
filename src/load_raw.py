
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
        
        conn.execute("""
            ALTER TABLE raw.ingestion_batches
            ADD COLUMN IF NOT EXISTS is_current BOOLEAN
            NOT NULL DEFAULT TRUE
        """)



def load_file(conn, filename, required_columns, logger):
    path = RAW_DIR / filename
    started = time.perf_counter()

    columns, unexpected = validate_file(
        path, required_columns
    )
    batch_id = calculate_batch_id(path)
    table_name = Path(filename).stem

    with conn.transaction():
        # Find the currently active version of this source.
        current = conn.execute(
            """
            SELECT batch_id, row_count
            FROM raw.ingestion_batches
            WHERE source_file = %s
              AND is_current = TRUE
            """,
            (filename,),
        ).fetchone()

        # Exact same file version: no work needed.
        if current and current[0] == batch_id:
            log_event(
                logger,
                logging.INFO,
                "Current batch already loaded; skipping",
                file_name=filename,
                batch_id=batch_id,
                row_count=current[1],
                status="SKIPPED",
            )
            return "SKIPPED", current[1]

        # Create the raw table if it does not exist.
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

        # Remove the previous snapshot inside this transaction.
        # If loading fails, PostgreSQL rolls this deletion back.
        conn.execute(
            sql.SQL("DELETE FROM {}.{}").format(
                sql.Identifier("raw"),
                sql.Identifier(table_name),
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
            chunk = chunk.astype(object).where(
                chunk != "", None
            )

            records = list(
                chunk.itertuples(index=False, name=None)
            )

            if records:
                with conn.cursor() as cur:
                    cur.executemany(insert_query, records)

            total_rows += len(records)

        # Mark the previous version as historical.
        conn.execute(
            """
            UPDATE raw.ingestion_batches
            SET is_current = FALSE
            WHERE source_file = %s
            """,
            (filename,),
        )

        # Record the newly loaded version. If this exact
        # version existed historically, reactivate its record.
        conn.execute(
            """
            INSERT INTO raw.ingestion_batches
                (batch_id, source_file, row_count,
                 loaded_at, is_current)
            VALUES (%s, %s, %s, NOW(), TRUE)
            ON CONFLICT (batch_id)
            DO UPDATE SET
                row_count = EXCLUDED.row_count,
                loaded_at = NOW(),
                is_current = TRUE
            """,
            (batch_id, filename, total_rows),
        )

    # This point is reached after the transaction commits.
    log_event(
        logger,
        logging.INFO,
        "Raw source snapshot loaded",
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
