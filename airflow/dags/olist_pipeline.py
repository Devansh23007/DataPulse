
from datetime import datetime, timedelta
import subprocess

from airflow import DAG
from airflow.operators.python import PythonOperator


PROJECT_DIR = "/opt/airflow/project"
DBT_DIR = f"{PROJECT_DIR}/datapulse_dbt"

default_args = {
    "owner": "datapulse",
    "depends_on_past": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=2),
}


def run_command(command, working_dir):
    result = subprocess.run(
        command,
        cwd=working_dir,
        check=False,
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"Command failed with exit code {result.returncode}: "
            f"{' '.join(command)}"
        )


def validate_sources():
    run_command(
        ["python", "-m", "src.ingestion"],
        PROJECT_DIR,
    )


def load_raw_data():
    run_command(
        ["python", "-m", "src.load_raw"],
        PROJECT_DIR,
    )


def build_warehouse():
    run_command(
        ["dbt", "run"],
        DBT_DIR,
    )


def test_warehouse():
    run_command(
        ["dbt", "test"],
        DBT_DIR,
    )


with DAG(
    dag_id="olist_data_pipeline",
    description="Ingest Olist data and build the dbt warehouse",
    default_args=default_args,
    start_date=datetime(2026, 1, 1),
    schedule=None,
    catchup=False,
    tags=["datapulse", "olist", "data-engineering"],
) as dag:

    validate_task = PythonOperator(
        task_id="validate_source_files",
        python_callable=validate_sources,
    )

    load_task = PythonOperator(
        task_id="load_raw_postgres",
        python_callable=load_raw_data,
    )

    transform_task = PythonOperator(
        task_id="build_dbt_warehouse",
        python_callable=build_warehouse,
    )

    test_task = PythonOperator(
        task_id="test_dbt_warehouse",
        python_callable=test_warehouse,
    )

    validate_task >> load_task >> transform_task >> test_task
