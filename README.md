# ShyamEdge: NIFTY 50 & SENSEX Options Buying Algorithmic System
### Institutional Research, Event-Driven Backtesting & Live Paper-Trading Engine (V1.0)

[![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue.svg)](https://www.python.org/downloads/)
[![Architecture](https://img.shields.io/badge/execution-Paper%20Trading%20Only-orange.svg)]()
[![Virtual Capital](https://img.shields.io/badge/capital-%E2%82%B915%2C000%20Virtual-green.svg)]()
[![Status](https://img.shields.io/badge/tests-15%20passed-brightgreen.svg)]()

---

## 1. Project Overview

**ShyamEdge** is an algorithmic trading research and simulation platform built specifically for **Index Options Buying** on **NIFTY 50** and **BSE SENSEX**. 

The system operates strictly within a **₹15,000 unified virtual portfolio capital constraint**, running four independent algorithmic strategies simultaneously. The overarching objective is to statistically determine whether an option-buying edge survives realistic market friction: adverse bid-ask slippage, SEBI statutory charges, STT, and premium theta decay.

> **CRITICAL SAFEGUARD:** Live money trading is **HARD-CODED DISABLED** in this release. The platform operates strictly in **PAPER TRADING ONLY** mode.

---

## 2. Core Architecture & Highlights

- **Laptop CPU Optimized:** Zero dependency on GPU, PyTorch, TensorFlow, or cloud infrastructure. Fast memory-mapped Apache Parquet data engine runs backtests on CPU in seconds.
- **Unified ₹15,000 Capital Envelope:** One shared portfolio across all strategies with strict independent performance tracking.
- **Uncompromised Risk Governance:**
  - **Risk per trade:** 1.0% – 2.0% (₹150 – ₹300 planned risk).
  - **Daily Circuit Breaker:** Hard stop at 3.0% loss (₹450). Once breached, trading halts for the remainder of the day.
  - **Max Concurrent Positions:** Exactly 1 active position allowed at any time.
  - **Forbidden:** No averaging down, no martingale, no size escalation after losses.
- **SEBI 2025/2026 Regulatory Calibration:**
  - **NIFTY 50 Lot Size:** **65**
  - **SENSEX Lot Size:** **20**
  - **Statutory Costs:** STT (0.1% on sell premium), ₹20/order brokerage, exchange turnover charges, stamp duty, SEBI turnover fees, 18% GST, and realistic bid-ask slippage.
- **Zero Lookahead Bias:** Event-driven bar-by-bar execution. All indicators (VWAP, EMA, RSI, ATR, Opening Range) calculate incrementally.

---

## 3. The 4 Independent V1 Strategies

| Strategy | Identifier | Core Setup | Primary Trigger | Exit Parameters |
| :--- | :--- | :--- | :--- | :--- |
| **Strategy 1** | `ORB-v1.0` | Opening Range Breakout (09:15-09:30 range) | Breakout/breakdown confirmed by VWAP + $1.3\times$ volume | 15% Premium SL, 1:2 R:R Target, 14:45 Time Cutoff |
| **Strategy 2** | `VWAP-EMA-v1.0` | Trend Following Alignment | Price > VWAP, EMA20 > EMA50, RSI 58-72 | Opposite EMA20 close or 15% SL, 1:2 R:R Target |
| **Strategy 3** | `PULLBACK-v1.0` | Dynamic Support/Resistance Retracement | Pullback to EMA20/VWAP with hammer/rejection candle | Swing low/high or 15% SL, 1:1.8 R:R Target |
| **Strategy 4** | `BREAKOUT-VOL-v1.0` | Key Technical Level Breakout | Break of PDH/PDL or Donchian swing + $1.8\times$ volume surge | Invalidation below level or 18% SL, 1:2 R:R Target |

### Quantitative Signal Scorer (0–100)
Every candidate setup is evaluated across 7 weighted dimensions: VWAP alignment (20 pts), EMA alignment (15 pts), Trigger quality (20 pts), Volume surge (15 pts), RSI momentum (10 pts), ATR expansion (10 pts), and Higher-timeframe regime (10 pts).
- **Score $\ge$ 75:** Valid candidate forwarded to Option Selection & Risk Engine.
- **Score 60–74:** Watchlist only (logged as rejected).
- **Score < 60:** Instant NO-TRADE rejection.

---

## 4. Repository Structure

```text
ShyamEdge/
├── config/              # Central settings, SEBI cost model, trading hours
├── core/                # Domain models (Bar, Signal, Order, Position, Trade)
├── data_engine/         # Parquet loader, 1m->5m bar aggregator, option pricing
├── indicators/          # Lookahead-free VWAP, EMA, RSI, ATR, Opening Range
├── regime_detector/     # Multi-factor market regime classifier
├── strategies/          # ORB, VWAP+EMA, Pullback, Breakout+Volume, Scorer
├── option_engine/       # ATM/ITM strike selection, liquidity & risk validation
├── risk_engine/         # ₹15k portfolio, position limits, circuit breaker, kill switch
├── broker/              # PaperBroker with adverse slippage & locked LiveBroker
├── backtest_engine/     # Bar-by-bar historical backtest & performance metrics
├── paper_engine/        # Real-time paper trading session orchestrator
├── database/            # SQLAlchemy models, SQLite & PostgreSQL repositories
├── api/                 # FastAPI telemetry backend (port 8000)
├── dashboard/           # Streamlit interactive dashboard (port 8501)
├── alerts/              # Telegram alert dispatcher
├── scripts/             # Operational CLI tools (backtest, paper, reports)
├── tests/               # Pytest suite (15 automated tests)
├── docker-compose.yml   # Multi-container orchestration (Postgres, Redis, App)
└── requirements.txt     # Python dependencies
```

---

## 5. Quickstart & Usage

### 1. Setup Local Environment

```bash
# Clone and enter workspace
cd ShyamEdge

# Install dependencies (CPU only)
pip install -r requirements.txt
```

### 2. Run Automated Verification Tests

```bash
python -m pytest tests/ -v
```
*(All 15 unit and integration tests covering indicators, risk limits, cost calculations, and strategy execution will run and pass).*

### 3. Run Historical Backtest (CLI)

```bash
# Backtest NIFTY 50 for 30 trading days with ₹15,000 virtual capital
python scripts/run_backtest.py --symbol NIFTY50 --days 30

# Backtest SENSEX for 30 trading days
python scripts/run_backtest.py --symbol SENSEX --days 30
```

### 4. Run Live Paper Trading Session (CLI)

```bash
python scripts/run_paper.py
```

### 5. Launch Interactive Streamlit Dashboard

```bash
python -m streamlit run dashboard/app.py
```
*(Or simply double-click `run_dashboard.bat`)*
Open your browser at `http://localhost:8501` to view:
- Virtual capital balance and equity curves.
- Real-time strategy win rates and net P&L after taxes.
- Itemized round-trip trade audits with slippage and exchange charges.
- Emergency Kill Switch control button.

### 6. Launch FastAPI Telemetry Backend

```bash
uvicorn api.main:app --reload --port 8000
```
Explore OpenAPI documentation at `http://localhost:8000/docs`.

### 7. Generate End-of-Day Markdown Report

```bash
python scripts/generate_daily_report.py
```

---

## 6. Docker Deployment (Optional)

To spin up the entire institutional stack (PostgreSQL 16, Redis 7, FastAPI backend, and Streamlit dashboard) with a single command:

```bash
docker compose up -d
```

- **Dashboard:** `http://localhost:8501`
- **API Docs:** `http://localhost:8000/docs`
- **PostgreSQL:** Port `5432` (`shyam_edge`)

---

## 7. Compliance & License

Designed strictly for research, simulation, and educational paper-trading purposes. All derivatives calculations adhere to current SEBI index derivatives and Finance Act statutory taxation mandates.
