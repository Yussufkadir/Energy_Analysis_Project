FROM apache/airflow:3.3.2-python3.12

COPY requirements.txt /tmp/requirements.txt
# Pinning apache-airflow stops pip from upgrading or downgrading Airflow itself.
RUN pip install --no-cache-dir "apache-airflow==${AIRFLOW_VERSION}" -r /tmp/requirements.txt
