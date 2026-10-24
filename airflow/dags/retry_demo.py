
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator


def intentionally_fail():
    raise RuntimeError(
        "Intentional Day 13 failure: testing Airflow retries."
    )


with DAG(
    dag_id="datapulse_retry_demo",
    description="Demonstrates Airflow task retries safely.",
    start_date=datetime(2026, 1, 1),
    schedule=None,
    catchup=False,
    default_args={
        "owner": "datapulse",
        "retries": 2,
        "retry_delay": timedelta(seconds=30),
    },
    tags=["datapulse", "testing"],
) as dag:

    test_retry = PythonOperator(
        task_id="intentional_failure",
        python_callable=intentionally_fail,
    )
