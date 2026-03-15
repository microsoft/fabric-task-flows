from datetime import datetime
from airflow import DAG
from airflow.operators.bash import BashOperator

default_args = {"owner": "airflow", "depends_on_past": False, "start_date": datetime(2023, 5, 1)}

with DAG("dag1", default_args=default_args, schedule_interval=None, catchup=False) as dag:
    hello = BashOperator(task_id="hello", bash_command='echo "Hello"')
    hello
