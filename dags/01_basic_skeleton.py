from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta

# ==========================================
# CONCEPT: Default Arguments
# ==========================================
# These args are passed to every operator in the DAG.
# It's best practice to define them here to avoid repetition.
default_args = {
    'owner': 'airflow',
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# ==========================================
# CONCEPT: The DAG Context Manager
# ==========================================
# catchup=False: Crucial! If True (default), Airflow will run this DAG for every 
# interval from start_date to now. Usually you want this False for dev.
with DAG(
    dag_id='01_basic_skeleton',
    default_args=default_args,
    description='A simple tutorial DAG',
    start_date=datetime(2023, 1, 1),
    schedule_interval='@daily',  # Run once a day at midnight
    catchup=False, 
    tags=['tutorial', 'module_1'],
) as dag:

    # ==========================================
    # CONCEPT: BashOperator
    # ==========================================
    # Executes a bash command. Good for simple scripts or moving files.
    t1 = BashOperator(
        task_id='print_date',
        bash_command='date',
    )

    # ==========================================
    # CONCEPT: PythonOperator
    # ==========================================
    # Executes a Python function. The most versatile operator.
    def my_python_function():
        print("Hello from the Python Operator!")
        return "This is a return value"

    t2 = PythonOperator(
        task_id='hello_python',
        python_callable=my_python_function,
    )

    # ==========================================
    # CONCEPT: Dependencies
    # ==========================================
    # t1 must finish successfully before t2 starts.
    # This is the "Bitshift" operator.
    t1 >> t2
