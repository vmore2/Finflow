# ================================================
# FINFLOW_PIPELINE.PY - Main DAG
# ================================================
# This is the HEART of our project. It orchestrates everything.
# 
# CONCEPTS DEMONSTRATED:
# 1. TaskGroups - Organizing related tasks
# 2. XComs - Passing data between tasks
# 3. BranchPythonOperator - Conditional logic
# 4. PythonOperator - Running Python functions
# 5. Dependencies - Task ordering with >>

from airflow import DAG
from airflow.operators.python import PythonOperator, BranchPythonOperator
from airflow.operators.empty import EmptyOperator  # For end points
from airflow.utils.task_group import TaskGroup
from datetime import datetime, timedelta
import json
import os

# Import our custom utility functions
# (These are in dags/utils/ folder)
from utils.fetchers import fetch_stock_prices, fetch_crypto_prices
from utils.indicators import analyze_asset


# ================================================
# CONFIGURATION
# ================================================
# Assets we want to track - easy to modify!
STOCK_SYMBOLS = ['AAPL', 'GOOGL', 'MSFT']
CRYPTO_SYMBOLS = ['bitcoin', 'ethereum']

# Alert thresholds
PRICE_DROP_THRESHOLD = -5  # Alert if price drops more than 5%
RSI_OVERBOUGHT = 70
RSI_OVERSOLD = 30


# ================================================
# DEFAULT ARGS
# ================================================
# These settings apply to ALL tasks in this DAG
# Think of it as "global settings"
default_args = {
    'owner': 'finflow',  # Who owns this DAG (for filtering in UI)
    'retries': 2,  # If a task fails, retry this many times
    'retry_delay': timedelta(minutes=5),  # Wait 5 mins between retries
    'email_on_failure': False,  # Don't spam emails (we don't have email set up)
}


# ================================================
# TASK FUNCTIONS
# ================================================
# Each function below becomes a task in the DAG.
# We use **context to access Airflow's runtime info (like xcom_push).

def fetch_all_stocks(**context):
    """
    Task 1A: Fetch stock prices for all configured symbols.
    
    XCOM EXPLANATION:
    -----------------
    XCom = "Cross Communication" - how tasks share data.
    
    We use xcom_push() to SEND data to other tasks.
    Other tasks use xcom_pull() to RECEIVE that data.
    
    Think of it like putting a note in a shared mailbox.
    """
    print(f"📈 Fetching stock prices for: {STOCK_SYMBOLS}")
    
    # Call our fetcher function
    stock_data = fetch_stock_prices(STOCK_SYMBOLS, period='1mo')
    
    # Push data to XCom so other tasks can use it
    # 'ti' = Task Instance (gives us access to XCom)
    context['ti'].xcom_push(key='stock_data', value=stock_data)
    
    print(f"✅ Stock data pushed to XCom: {list(stock_data.keys())}")
    return stock_data


def fetch_all_crypto(**context):
    """
    Task 1B: Fetch crypto prices for all configured symbols.
    """
    print(f"🪙 Fetching crypto prices for: {CRYPTO_SYMBOLS}")
    
    crypto_data = fetch_crypto_prices(CRYPTO_SYMBOLS)
    context['ti'].xcom_push(key='crypto_data', value=crypto_data)
    
    print(f"✅ Crypto data pushed to XCom: {list(crypto_data.keys())}")
    return crypto_data


def analyze_stocks(**context):
    """
    Task 2A: Analyze stock data using technical indicators.
    
    XCOM PULL EXPLANATION:
    ----------------------
    Here we RECEIVE data from Task 1A.
    
    xcom_pull(task_ids='fetch_stocks', key='stock_data')
                ^                          ^
                |                          |
          Which task sent it         What key to look for
    """
    # Pull stock data from the previous task
    ti = context['ti']
    stock_data = ti.xcom_pull(task_ids='data_ingestion.fetch_stocks', key='stock_data')
    
    if not stock_data:
        print("⚠️ No stock data received from XCom!")
        return {}
    
    analysis_results = {}
    
    for symbol, data in stock_data.items():
        if 'prices' in data:
            result = analyze_asset(symbol, data['prices'])
            analysis_results[symbol] = result
            print(f"📊 {symbol}: {result['signal']} - {result.get('analysis', 'N/A')}")
    
    # Push analysis results for the next task
    ti.xcom_push(key='stock_analysis', value=analysis_results)
    return analysis_results


def analyze_crypto(**context):
    """
    Task 2B: Process crypto data.
    (Crypto uses simpler analysis since we only get current price from CoinGecko)
    """
    ti = context['ti']
    crypto_data = ti.xcom_pull(task_ids='data_ingestion.fetch_crypto', key='crypto_data')
    
    if not crypto_data:
        print("⚠️ No crypto data received!")
        return {}
    
    analysis_results = {}
    
    for symbol, data in crypto_data.items():
        if 'price' in data:
            change = data.get('change_24h', 0)
            signal = 'SELL' if change < PRICE_DROP_THRESHOLD else ('BUY' if change > 5 else 'HOLD')
            
            analysis_results[symbol] = {
                'symbol': symbol,
                'price': data['price'],
                'change_24h': change,
                'signal': signal
            }
            print(f"🪙 {symbol}: ${data['price']:,.2f} ({change:+.2f}%) → {signal}")
    
    ti.xcom_push(key='crypto_analysis', value=analysis_results)
    return analysis_results


def check_alerts(**context):
    """
    Task 3: BRANCHING - Decide which path to take.
    
    BRANCHING EXPLANATION:
    ----------------------
    This function returns the TASK ID of the next task to run.
    - If we find alerts, return 'send_alerts'
    - If no alerts, return 'generate_report'
    
    This creates an IF/ELSE in our pipeline!
    """
    ti = context['ti']
    
    # Pull all analysis data
    stock_analysis = ti.xcom_pull(task_ids='data_processing.analyze_stocks', key='stock_analysis') or {}
    crypto_analysis = ti.xcom_pull(task_ids='data_processing.analyze_crypto', key='crypto_analysis') or {}
    
    alerts = []
    
    # Check for stock alerts
    for symbol, data in stock_analysis.items():
        if data.get('signal') in ['BUY', 'SELL']:
            alerts.append(f"🚨 STOCK {symbol}: {data['signal']} signal!")
        if data.get('change_pct', 0) < PRICE_DROP_THRESHOLD:
            alerts.append(f"📉 STOCK {symbol}: Down {data['change_pct']}%!")
    
    # Check for crypto alerts
    for symbol, data in crypto_analysis.items():
        if data.get('signal') in ['BUY', 'SELL']:
            alerts.append(f"🚨 CRYPTO {symbol}: {data['signal']} signal!")
        if data.get('change_24h', 0) < PRICE_DROP_THRESHOLD:
            alerts.append(f"📉 CRYPTO {symbol}: Down {data['change_24h']}%!")
    
    # Push alerts for the send_alerts task
    ti.xcom_push(key='alerts', value=alerts)
    
    # BRANCHING LOGIC: Return the task_id to execute next
    if alerts:
        print(f"⚠️ Found {len(alerts)} alerts! Routing to send_alerts")
        return 'send_alerts'
    else:
        print("✅ No alerts. Routing to generate_report")
        return 'generate_report'


def send_alerts(**context):
    """
    Task 4A: Send alert notifications.
    (In a real project, this would send emails/Slack messages)
    """
    ti = context['ti']
    alerts = ti.xcom_pull(task_ids='check_alerts', key='alerts') or []
    
    print("\n" + "="*50)
    print("🚨 ALERT NOTIFICATION 🚨")
    print("="*50)
    for alert in alerts:
        print(alert)
    print("="*50 + "\n")
    
    # In production, you would:
    # - Send to Slack: slack_webhook.send(alerts)
    # - Send email: send_email(to='trader@company.com', body=alerts)
    # - Push to PagerDuty, etc.
    
    return {'alerts_sent': len(alerts)}


def generate_report(**context):
    """
    Task 4B: Generate summary report (when no alerts).
    Saves a JSON file to the include/data folder.
    """
    ti = context['ti']
    
    stock_analysis = ti.xcom_pull(task_ids='data_processing.analyze_stocks', key='stock_analysis') or {}
    crypto_analysis = ti.xcom_pull(task_ids='data_processing.analyze_crypto', key='crypto_analysis') or {}
    
    report = {
        'generated_at': datetime.now().isoformat(),
        'stocks': stock_analysis,
        'crypto': crypto_analysis,
        'summary': {
            'total_assets': len(stock_analysis) + len(crypto_analysis),
            'signals': {
                'buy': sum(1 for a in list(stock_analysis.values()) + list(crypto_analysis.values()) 
                          if a.get('signal') == 'BUY'),
                'sell': sum(1 for a in list(stock_analysis.values()) + list(crypto_analysis.values()) 
                           if a.get('signal') == 'SELL'),
                'hold': sum(1 for a in list(stock_analysis.values()) + list(crypto_analysis.values()) 
                           if a.get('signal') == 'HOLD'),
            }
        }
    }
    
    # Save to file
    report_path = '/usr/local/airflow/include/data/report.json'
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"📄 Report saved to {report_path}")
    print(f"📊 Summary: {report['summary']}")
    
    return report


# ================================================
# THE DAG DEFINITION
# ================================================
# This is where we put it all together!

with DAG(
    dag_id='finflow_pipeline',
    default_args=default_args,
    description='Financial Intelligence Pipeline - Stocks & Crypto Analysis',
    start_date=datetime(2024, 1, 1),
    schedule='0 9 * * 1-5',  # Cron: 9:00 AM, Monday-Friday (market hours!)
    catchup=False,
    tags=['finance', 'stocks', 'crypto', 'portfolio'],
) as dag:
    
    # ============================================
    # TASK GROUP 1: Data Ingestion
    # ============================================
    # TaskGroups visually group related tasks in the UI.
    # Makes complex DAGs easier to understand.
    
    with TaskGroup("data_ingestion", tooltip="Fetch data from external APIs") as ingestion:
        
        fetch_stocks = PythonOperator(
            task_id='fetch_stocks',
            python_callable=fetch_all_stocks,
        )
        
        fetch_crypto = PythonOperator(
            task_id='fetch_crypto',
            python_callable=fetch_all_crypto,
        )
        
        # These can run in parallel (no dependency between them)
        # [fetch_stocks, fetch_crypto]  ← No >> means parallel!
    
    # ============================================
    # TASK GROUP 2: Data Processing
    # ============================================
    
    with TaskGroup("data_processing", tooltip="Analyze data with technical indicators") as processing:
        
        analyze_stocks_task = PythonOperator(
            task_id='analyze_stocks',
            python_callable=analyze_stocks,
        )
        
        analyze_crypto_task = PythonOperator(
            task_id='analyze_crypto',
            python_callable=analyze_crypto,
        )
    
    # ============================================
    # BRANCHING: Check for Alerts
    # ============================================
    
    check_alerts_task = BranchPythonOperator(
        task_id='check_alerts',
        python_callable=check_alerts,
    )
    
    # ============================================
    # OUTPUT TASKS (Mutually exclusive branches)
    # ============================================
    
    send_alerts_task = PythonOperator(
        task_id='send_alerts',
        python_callable=send_alerts,
    )
    
    generate_report_task = PythonOperator(
        task_id='generate_report',
        python_callable=generate_report,
    )
    
    # End task - both branches converge here
    # trigger_rule='none_failed_min_one_success' means:
    # "Run if at least one upstream succeeded and none failed"
    end = EmptyOperator(
        task_id='end',
        trigger_rule='none_failed_min_one_success'
    )
    
    # ============================================
    # DEPENDENCIES (The Pipeline Flow)
    # ============================================
    # This is the "wiring" that connects everything!
    
    # Step 1: Ingestion runs first
    # Step 2: Processing runs after ingestion
    ingestion >> processing
    
    # Step 3: Check for alerts after processing
    processing >> check_alerts_task
    
    # Step 4: Branch to either alerts OR report
    check_alerts_task >> [send_alerts_task, generate_report_task]
    
    # Step 5: Both branches end at the same point
    [send_alerts_task, generate_report_task] >> end
