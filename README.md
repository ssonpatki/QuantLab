# QuantLab: quantitative research platform

Pick a stock, backtest a strategy against buy-and-hold, save experiments and compare them, and explore three ML
analyses (next-day return models, market regimes, anomalous days). Free to build and host.

## Architecture (microservices)

```
React + TypeScript (Vite, Recharts)
        |  /api/*
   gateway :8000        one public entry point, forwards /api/<service>/...
   |-- market-data  :8001   Yahoo Finance / CSV / demo data -> Postgres (own DB: market)
   |-- backtest     :8002   strategies, engine, metrics, experiments -> Postgres (own DB: backtest)
   `-- ml           :8003   features, LinReg / RandomForest / XGBoost, K-Means, Isolation Forest
backtest and ml fetch prices from market-data over HTTP; services never share tables.
```

| Want to change...          | Edit only...                                                                                   |
|----------------------------|------------------------------------------------------------------------------------------------|
| Add a strategy             | `services/backtest/app/strategies.py` (class + `REGISTRY` entry) and defaults in `frontend/src/pages/StrategyLab.tsx` |
| Fees / metrics logic       | `services/backtest/app/engine.py`, `metrics.py`                                                |
| Add a data source          | `services/market_data/app/providers.py`                                                        |
| ML features / models       | `services/ml/app/features.py`, `models.py`                                                     |
| Add a service              | new folder in `services/`, one line in gateway `ROUTES`, one block in `docker-compose.yml`     |

## Run locally

**Docker:** `docker compose up --build`, then open http://localhost:3000

**Without Docker** (SQLite is used automatically), one terminal each:
```bash
cd services/market_data && pip install -r requirements.txt && uvicorn app.main:app --port 8001
cd services/backtest    && pip install -r requirements.txt && MARKET_URL=http://localhost:8001 uvicorn app.main:app --port 8002
cd services/ml          && pip install -r requirements.txt && MARKET_URL=http://localhost:8001 uvicorn app.main:app --port 8003
cd services/gateway     && pip install -r requirements.txt && uvicorn app.main:app --port 8000
cd frontend && npm install && npm run dev     # http://localhost:3000
```
Tests: `python -m pytest` inside each service folder. CI runs them plus the frontend build.
Each service serves interactive API docs at `/docs`.

## What it does

- **Market Data**: ticker search, 5 years of daily prices (yfinance), CSV import, invalid-row cleaning, unique `(symbol, date)` so nothing is stored twice.
- **Strategy Lab**: SMA crossover and RSI strategies, starting capital, fees, date range, equity curve vs buy-and-hold, metrics, trade list.
- **Experiments**: save a run, select 2+ to compare side by side.
- **ML Insights**: next-day return models vs a "predict 0" baseline, K-Means volatility regimes, Isolation Forest anomalies.

If Yahoo Finance can't be reached for a *new* ticker, the app generates clearly labelled **synthetic demo data**
(amber badge in the UI) so it still works. Set `SYNTHETIC_FALLBACK=false` on `market-data` to disable that.

## Methodology and limits

- Signals use a day's close and trade at the **next day's open** (no look-ahead). Long-only, one asset, all-in/all-out.
  An open position at the end is marked to market, not counted as a closed trade.
- Metrics: 252 trading days/year, risk-free rate 0, volatility = daily std x sqrt(252), win rate = profitable closed trades.
- ML: features use only past data (unit-tested); chronological 70/30 split with a 1-day gap, no shuffling.
  Models retrain per request and nothing is persisted yet. Daily-return prediction is hard: expect results near the
  baseline. Regimes are fit on the full history, so they describe the past.
- yfinance is unofficial and can break or rate-limit. Not investment advice.
- Not built yet (from the roadmap): portfolio risk/VaR, FinBERT sentiment, LLM assistant, MLflow, Alembic migrations, auth, strategy-by-regime backtests.

