# DataPulse Performance and Reliability Analysis

## 1. Objective

This report summarizes the recorded execution time of the DataPulse ingestion and dbt workflow, the resulting warehouse row counts, and the results of selected synthetic data-quality checks.

The measurements were collected from a local execution of the pipeline. Results may vary depending on the machine, database state, dataset size, and whether unchanged source batches are skipped.

## 2. Performance Benchmark Results

The following values are from `docs/performance_report.csv`.

| Pipeline Stage | Duration (seconds) | Exit Code | Status |
|---|---:|---:|---|
| Raw data loading | 2.530 | 0 | PASS |
| dbt transformations | 16.338 | 0 | PASS |
| dbt tests | 12.597 | 0 | PASS |
| End-to-end workflow | 31.579 | 0 | PASS |

The recorded end-to-end workflow completed in approximately 31.6 seconds. All four recorded stages reported a successful exit code.

The individual stage durations should not be expected to sum exactly to the end-to-end duration because the measurements may include different orchestration and execution overheads.

## 3. Warehouse Row Counts

The following counts were recorded in `docs/warehouse_row_counts.csv`.

| Table | Row Count |
|---|---:|
| `raw_orders` | 99,441 |
| `stg_orders` | 99,441 |
| `fact_order_items` | 112,650 |
| `mart_daily_sales` | 1,783 |

The raw orders and staging orders counts match in this recorded snapshot. This is a useful reconciliation check for the orders staging model.

The fact table contains order-item records, so its row count is expected to differ from the number of orders. The daily-sales mart contains aggregated records rather than individual transactions.

These counts describe the recorded database snapshot and are not throughput measurements.

## 4. Synthetic Data-Quality Tests

The recorded results in `docs/corruption_test_report.csv` show that the test suite detected the following deliberately introduced issues.

| Test Scenario | Recorded Result |
|---|---|
| Missing order ID | PASS: detected 1 row with a null key |
| Duplicate order-item key | PASS: detected 2 duplicate-key rows |
| Negative price | PASS: detected 1 invalid price value |
| Missing product relationship | PASS: detected 1 order item with a missing product |
| Valid order IDs | PASS: accepted valid unique order IDs |

These tests demonstrate that the implemented checks can identify selected key, value, and relationship problems in synthetic test data. They do not establish that every possible data-quality issue in the source dataset will be detected.

## 5. Reliability and Replay Validation

The project includes reliability checks for duplicate batch replay, ingestion metadata, database transaction rollback, and selected Airflow failure scenarios.

The detailed test descriptions are maintained in `docs/reliability_test_report.md`.

A repeat-run benchmark must distinguish between a fresh ingestion and a replay where unchanged batches are skipped. A skipped replay does not measure the throughput of a full reload.

For a reproducible reliability claim, retain the corresponding test output and database checks alongside the report.

## 6. Limitations

- The performance measurements represent a recorded local run and may vary across environments.
- The available row counts are snapshots, not ingestion throughput metrics.
- Synthetic corruption tests cover selected scenarios rather than all possible source-data failures.
- Successful pipeline execution does not, by itself, prove that all business metrics are semantically correct.
- The local Docker and Airflow setup is intended for a portfolio project and requires additional hardening before production use.

## 7. Conclusion

In the recorded benchmark, raw loading completed in 2.530 seconds, dbt transformations in 16.338 seconds, dbt tests in 12.597 seconds, and the end-to-end workflow in 31.579 seconds. All recorded stages returned exit code zero.

The warehouse snapshot contained 99,441 raw orders, 99,441 staging orders, 112,650 fact order items, and 1,783 daily-sales mart rows. The synthetic data-quality report also recorded successful detection of five tested scenarios.

Together, these results provide evidence of pipeline execution, warehouse population, and selected data-quality checks. They should be treated as a baseline for future reproducible performance and reliability testing.
