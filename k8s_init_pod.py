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
    'k8s_pod', default_args=default_args, catchup=False, schedule_interval=None)

start = DummyOperator(task_id='run_this_first', dag=dag)

volume = k8s.V1Volume(
    name='git-volume',
    empty_dir=k8s.V1EmptyDirVolumeSource(),
)

init_environments = [k8s.V1EnvVar(name='GIT_SYNC_REPO', value='https://github.com/vunh76/udacity_cs_101'), k8s.V1EnvVar(name='GIT_SYNC_BRANCH', value='master'), k8s.V1EnvVar(name='GIT_SYNC_ONE_TIME', value='true')]
init_container_volume_mounts = [
    k8s.V1VolumeMount(mount_path='/tmp/git', name='git-volume', sub_path=None, read_only=False)
]
init_container = k8s.V1Container(
    name="init-container",
    image="k8s.gcr.io/git-sync:v3.0.1",
    volume_mounts=init_container_volume_mounts,
    env=init_environments
)

volume_mount = k8s.V1VolumeMount(
    name='git-volume', mount_path='/tmp/git', sub_path=None, read_only=True
)
passing = KubernetesPodOperator(namespace='airflow',
                                image="python:3.7",
                                cmds=["python", "/tmp/git/abacus.py"],
                                labels={"task": "abacus"},
                                name="abacus-test",
                                task_id="abacus-task",
                                get_logs=True,
                                #is_delete_operator_pod=True,
                                init_containers=[init_container],
                                volumes=[volume],
                                volume_mounts=[volume_mount],
                                dag=dag
                                )

passing.set_upstream(start)
