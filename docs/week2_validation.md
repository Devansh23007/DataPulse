
# Week 2: Warehouse and Orchestration Validation

## Objective
Build and validate a repeatable analytics warehouse using dbt
Core, PostgreSQL, and Apache Airflow.

## Components
- Python ingestion pipeline
- PostgreSQL raw schema
- dbt staging models
- Customer, product, and seller dimensions
- Order item fact table
- Daily sales reporting mart
- dbt quality tests
- Airflow orchestration DAG

## Validation Results

| Check | Result |
|---|---|
| PostgreSQL connection | Pass |
| dbt parsing | Pass |
| dbt model execution | Pass |
| dbt tests | Pass |
| Warehouse row counts | Pass |
| Airflow workflow | Pass |
| Batch replay behavior | Pass|
| dbt documentation | Pass |

Replace Pending with PASS or FAIL after running each check.

## Limitations
- Airflow currently uses a local development configuration.
- The raw layer retains batch metadata, not historical row snapshots.
- The reporting mart measures order item value and freight,
  not necessarily completed or paid sales.
- Incremental transformations and production deployment
  require further development.

## Next Steps
- Add pipeline monitoring and operational metrics.
- Introduce CI checks for Python and dbt.
- Build a dashboard for pipeline health and sales reporting.
- Improve deployment and secret management.
