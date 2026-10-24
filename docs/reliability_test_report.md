
# DataPulse Reliability Test Report

## Objective

Validate duplicate replay protection, transaction rollback,
and Airflow retry behavior for the Olist data pipeline.

## Test Results

| Test | Expected Result | Actual Result |
|---|---|---|
| Duplicate batch replay | Unchanged batches skipped | Pass |
| Current batch metadata | One current batch per source | Pass |
| Database rollback | Row count unchanged | Pass |
| Airflow retry demonstration | Retries exhausted and task fails | Pass |
| Main pipeline rerun | All four tasks succeed | Pass |

## Failure Recovery

The retry demonstration uses an isolated Airflow DAG and does
not modify the Olist source data.

The database rollback test intentionally raises an exception
inside a transaction to verify that PostgreSQL restores the
previous table state.

## Limitations

These tests validate selected failure scenarios. They do not
prove recovery from every possible infrastructure failure.

## Evidence

Record the terminal output, Airflow task logs, and database
checks after running each test.
