from airflow import DAG
from airflow import configuration as conf
from airflow.contrib.operators.kubernetes_pod_operator import KubernetesPodOperator
from airflow.operators.dummy_operator import DummyOperator
from airflow.utils.dates import days_ago
from datetime import datetime, timedelta
from kubernetes.client import models as k8s

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': days_ago(2),
    'email': 'vu@gotitapp.co',
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5)
}

dag = DAG(
    'k8s_init_pod', default_args=default_args, catchup=False, schedule_interval=None)

start = DummyOperator(task_id='run_this_first', dag=dag)

passing = KubernetesPodOperator(name="abacus-test",
                                task_id="abacus-task",
                                get_logs=True,
                                pod_template_file="git_init_container.yaml",
                                dag=dag
                                )

passing.set_upstream(start)
