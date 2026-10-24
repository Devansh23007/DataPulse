
FROM apache/airflow:2.10.5-python3.11

USER airflow

COPY requirements.txt /tmp/project-requirements.txt

RUN pip install --no-cache-dir \
    "apache-airflow==2.10.5" \
    --constraint \
    "https://raw.githubusercontent.com/apache/airflow/constraints-2.10.5/constraints-3.11.txt" \
    && pip install --no-cache-dir \
    -r /tmp/project-requirements.txt \
    "dbt-postgres"
