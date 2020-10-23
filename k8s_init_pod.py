from airflow import DAG
from airflow import configuration as conf
from airflow.contrib.operators.kubernetes_pod_operator import KubernetesPodOperator
from airflow.operators.dummy_operator import DummyOperator
from airflow.utils.dates import days_ago
from datetime import datetime, timedelta
from kubernetes.client import models as k8s
from airflow.contrib.kubernetes.volume_mount import VolumeMount
from airflow.contrib.kubernetes.volume import Volume

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': days_ago(2),
    'email': 'vu@gotitapp.co',
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=1)
}

dag = DAG(
    'k8s_init_pod', default_args=default_args, catchup=False, schedule_interval=None)

start = DummyOperator(task_id='run_this_first', dag=dag)

volume_mount = VolumeMount(
    'git-volume', '/tmp/git', None, True
)

volume = Volume(
    'git-volume',
    {
        "empty_dir": k8s.V1EmptyDirVolumeSource()
    }
)

init_container_volume_mounts = [
    VolumeMount('git-volume', '/tmp/git', None, False)
]

init_environments = [
    k8s.V1EnvVar(name='GIT_SYNC_REPO', value='https://github.com/vunh76/udacity_cs_101.git'),
    k8s.V1EnvVar(name='GIT_SYNC_BRANCH', value='master'),
    k8s.V1EnvVar(name='GIT_SYNC_ONE_TIME', value='true'),
    k8s.V1EnvVar(name='GIT_SYNC_DEST', value='cs101'),
]

init_container = k8s.V1Container(
    name="git-sync",
    image="k8s.gcr.io/git-sync:v3.0.1",
    env=init_environments,
    volume_mounts=init_container_volume_mounts
)

abacus = KubernetesPodOperator(
        namespace='airflow',
        image="python:3.7",
        cmds=["python"],
        arguments=["/tmp/git/cs101/abacus.py"],
        labels={"cs101": "abacus"},
        volumes=[volume],
        volume_mounts=[volume_mount],
        name="airflow-abacus-pod",
        task_id="abacus-task",
        is_delete_operator_pod=True,
        init_containers=[init_container],
        priority_class_name="medium",
        in_cluster=True,
        dag=dag
    )

# abacus = KubernetesPodOperator(namespace='airflow',
#                                 name="abacus-test",
#                                 task_id="abacus-task",
#                                 get_logs=True,
#                                 full_pod_spec=None,
#                                 pod_template_file="git_init_container.yaml",
#                                 dag=dag
#                                 )

abacus.set_upstream(start)