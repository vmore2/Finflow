# 📈 FinFlow: Financial Intelligence Pipeline

> An automated data pipeline that fetches real-time stock and cryptocurrency prices, performs technical analysis, and generates trading signals using Apache Airflow.

![Python](https://img.shields.io/badge/Python-3.9+-blue?logo=python)
![Airflow](https://img.shields.io/badge/Apache%20Airflow-2.0+-017CEE?logo=apache-airflow)
![Astro](https://img.shields.io/badge/Astronomer-Astro%20CLI-purple)

---

## 📋 Problem Definition

### The Challenge
Individual investors and traders need to monitor multiple assets (stocks, crypto) across different markets. Manually tracking prices and calculating technical indicators is:
- **Time-consuming**: Checking multiple sources daily
- **Error-prone**: Manual calculations can be wrong
- **Reactive**: You find out about price drops too late

### The Solution
FinFlow automates the entire process:
1. **Fetches** prices from Yahoo Finance (stocks) and CoinGecko (crypto)
2. **Calculates** technical indicators (RSI, Moving Averages)
3. **Generates** trading signals (BUY / SELL / HOLD)
4. **Alerts** when significant price movements occur

All scheduled to run automatically during market hours (Mon-Fri, 9 AM).

---

## 🏗️ Architecture

### High-Level Flow
```
┌────────────────────────────────────────────────────────────────┐
│                         AIRFLOW DAG                            │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │              TASKGROUP: DATA INGESTION                   │  │
│  │  ┌─────────────────┐    ┌─────────────────┐             │  │
│  │  │  Fetch Stocks   │    │  Fetch Crypto   │             │  │
│  │  │  (Yahoo Finance)│    │  (CoinGecko)    │             │  │
│  │  └────────┬────────┘    └────────┬────────┘             │  │
│  │           │                      │                       │  │
│  │           └──────────┬───────────┘                       │  │
│  │                      ▼                                   │  │
│  │               XCom (price data)                          │  │
│  └─────────────────────────────────────────────────────────┘  │
│                         │                                      │
│                         ▼                                      │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │              TASKGROUP: DATA PROCESSING                  │  │
│  │  ┌─────────────────┐    ┌─────────────────┐             │  │
│  │  │ Analyze Stocks  │    │ Analyze Crypto  │             │  │
│  │  │ (RSI, MA)       │    │ (24h Change)    │             │  │
│  │  └────────┬────────┘    └────────┬────────┘             │  │
│  │           │                      │                       │  │
│  │           └──────────┬───────────┘                       │  │
│  │                      ▼                                   │  │
│  │               XCom (analysis)                            │  │
│  └─────────────────────────────────────────────────────────┘  │
│                         │                                      │
│                         ▼                                      │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │                   BRANCHING LOGIC                        │  │
│  │                                                          │  │
│  │                  ┌──────────────┐                        │  │
│  │                  │ Check Alerts │                        │  │
│  │                  └──────┬───────┘                        │  │
│  │                         │                                │  │
│  │           ┌─────────────┴─────────────┐                  │  │
│  │           ▼                           ▼                  │  │
│  │   ┌──────────────┐           ┌──────────────┐           │  │
│  │   │ Send Alert   │    OR     │ Gen Report   │           │  │
│  │   │ (if signals) │           │ (no signals) │           │  │
│  │   └──────────────┘           └──────────────┘           │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

### Project Structure
```
finflow/
├── dags/
│   ├── finflow_pipeline.py      # Main DAG orchestrator
│   └── utils/
│       ├── fetchers.py          # API integration (Yahoo, CoinGecko)
│       └── indicators.py        # Technical analysis functions
├── include/
│   └── data/                    # Generated reports
├── requirements.txt             # Python dependencies
├── Dockerfile                   # Astro runtime
└── README.md
```

---

## 🧠 Logic & Technical Indicators

### Moving Average (MA)
Smooths out price fluctuations to identify trends.

```
MA = (Price₁ + Price₂ + ... + Priceₙ) / n

Example (5-day MA):
Prices: [150, 152, 148, 155, 153]
MA = (150 + 152 + 148 + 155 + 153) / 5 = 151.6

Signal: If current price (153) > MA (151.6) → Bullish 📈
```

### RSI (Relative Strength Index)
Measures momentum on a scale of 0-100.

```
RSI = 100 - (100 / (1 + RS))
where RS = Average Gain / Average Loss

Interpretation:
- RSI > 70 → Overbought (potential SELL)
- RSI < 30 → Oversold (potential BUY)
- RSI 30-70 → Neutral
```

### Signal Generation Logic
```python
if rsi < 30 and price > moving_average:
    signal = "BUY"   # Oversold but trending up
elif rsi > 70 and price < moving_average:
    signal = "SELL"  # Overbought and trending down
else:
    signal = "HOLD"
```

---

## 🔧 Key Airflow Concepts Used

| Concept | What It Does | Where Used |
|---------|--------------|------------|
| **TaskGroup** | Groups related tasks for cleaner DAG | `data_ingestion`, `data_processing` |
| **XCom** | Passes data between tasks | Price data → Analysis |
| **BranchPythonOperator** | Conditional task execution | Alert vs Report path |
| **PythonOperator** | Runs Python functions | All data processing |
| **Default Args** | Retries, timeouts, ownership | DAG configuration |

---

## 🚀 How to Run

### Prerequisites
1. **Docker Desktop** - [Download here](https://www.docker.com/products/docker-desktop/)
2. **Astro CLI** - Install with:
   ```bash
   # macOS/Linux
   curl -sSL https://install.astronomer.io | sudo bash -s

   # Windows (PowerShell)
   winget install astronomer.astro
   ```

### Step-by-Step

```bash
# 1. Clone the repository
git clone https://github.com/vmore2/Finflow.git
cd Finflow

# 2. Start Docker Desktop (make sure it's running!)

# 3. Start Airflow locally
astro dev start
# First time takes ~5 minutes to pull images

# 4. Access the Airflow UI
# Open: http://localhost:8080
# Username: admin
# Password: admin

# 5. Enable and trigger the DAG
# - Find 'finflow_pipeline' in the DAG list
# - Toggle the switch to ON (blue)
# - Click the Play button → Trigger DAG
```

### Viewing Results

| Where to Look | What You'll See |
|---------------|-----------------|
| **Logs tab** | Print statements with analysis |
| **XCom tab** | Raw JSON data between tasks |
| **include/data/** | Generated report.json file |

### Stop the Environment
```bash
astro dev stop
```

---

## ⚙️ Configuration

### Add More Assets
Edit `dags/finflow_pipeline.py`:
```python
STOCK_SYMBOLS = ['AAPL', 'GOOGL', 'MSFT', 'NVDA', 'TSLA']
CRYPTO_SYMBOLS = ['bitcoin', 'ethereum', 'solana']
```

### Adjust Alert Thresholds
```python
PRICE_DROP_THRESHOLD = -10  # Alert if drops more than 10%
RSI_OVERBOUGHT = 75         # Custom overbought level
RSI_OVERSOLD = 25           # Custom oversold level
```

---

## 📊 Sample Output

```
✅ Fetched AAPL: $195.50 (+2.35%)
✅ Fetched GOOGL: $141.20 (-0.85%)
✅ Fetched MSFT: $378.90 (+1.20%)
🪙 Fetched bitcoin: $42,500.00 (+3.50%)
🪙 Fetched ethereum: $2,250.00 (+2.10%)

📊 AAPL: HOLD - Price above 20-day MA (bullish) | RSI 55.2 is neutral
📊 GOOGL: HOLD - Price below 20-day MA (bearish) | RSI 48.1 is neutral
📊 MSFT: HOLD - Price above 20-day MA (bullish) | RSI 62.3 is neutral
```

---

## 🛣️ Roadmap

- [x] Stock price fetching (Yahoo Finance)
- [x] Crypto price fetching (CoinGecko)
- [x] Technical indicators (RSI, MA)
- [x] Branching logic for alerts
- [ ] Slack/Email notifications
- [ ] PostgreSQL storage
- [ ] Historical backtesting
- [ ] Airflow Sensors for market hours

---

## 📜 License

MIT License - Feel free to use this for your portfolio!

---

## 🤝 Author

**Vrush More** | [GitHub](https://github.com/vmore2)
