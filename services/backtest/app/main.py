import os
from datetime import date
from typing import Literal, Optional

import httpx
import pandas as pd
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from .db import Experiment, SessionLocal
from .engine import buy_and_hold, run_backtest
from .metrics import compute_metrics
from .strategies import REGISTRY

MARKET_URL = os.getenv("MARKET_URL", "http://localhost:8001")
app = FastAPI(title="QuantLab Backtest Service")


class BacktestRequest(BaseModel):
    symbol: str
    strategy: Literal["sma_crossover", "rsi"]
    params: dict = {}
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    capital: float = Field(10_000, gt=0)
    fee_bps: float = Field(5, ge=0, le=500)
    save: bool = False


def load_prices(symbol: str):
    try:
        r = httpx.get(f"{MARKET_URL}/prices/{symbol}", timeout=120)
    except httpx.HTTPError:
        raise HTTPException(503, "Market data service is unreachable")
    if r.status_code != 200:
        raise HTTPException(r.status_code, r.json().get("detail", "Market data error"))
    body = r.json()
    df = pd.DataFrame(body["prices"])
    df["date"] = pd.to_datetime(df["date"])
    return df.set_index("date"), body["source"]


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.get("/strategies")
def strategies():
    return list(REGISTRY)


@app.post("/backtests")
def backtests(req: BacktestRequest):
    df, source = load_prices(req.symbol.strip().upper())
    try:
        strategy = REGISTRY[req.strategy](**req.params)
    except (ValueError, TypeError) as e:
        raise HTTPException(422, f"Invalid strategy parameters: {e}")
    signals = strategy.generate_signals(df)  # computed on full history so indicators are warmed up
    if req.start_date:
        keep = df.index >= pd.Timestamp(req.start_date)
        df, signals = df[keep], signals[keep]
    if req.end_date:
        keep = df.index <= pd.Timestamp(req.end_date)
        df, signals = df[keep], signals[keep]
    if len(df) < 60:
        raise HTTPException(422, f"Only {len(df)} trading days in range; need at least 60")
    equity, trades = run_backtest(df, signals, req.capital, req.fee_bps)
    bench = buy_and_hold(df, req.capital, req.fee_bps)
    m, bm = compute_metrics(equity, req.capital, trades), compute_metrics(bench, req.capital, [])
    result = {
        "config": {**req.model_dump(mode="json"), "params": strategy.params},
        "data_source": source,
        "equity": [{"date": d.strftime("%Y-%m-%d"), "strategy": float(equity[d]), "benchmark": float(bench[d])}
                   for d in df.index],
        "trades": trades, "metrics": m, "benchmark_metrics": bm, "experiment_id": None,
    }
    if req.save:
        with SessionLocal() as db:
            exp = Experiment(strategy=req.strategy, params=strategy.params, symbol=req.symbol.strip().upper(),
                             start_date=df.index[0].strftime("%Y-%m-%d"), end_date=df.index[-1].strftime("%Y-%m-%d"),
                             capital=req.capital, fee_bps=req.fee_bps, data_source=source,
                             metrics=m, benchmark_metrics=bm)
            db.add(exp)
            db.commit()
            result["experiment_id"] = exp.id
    return result


def serialize(e: Experiment):
    return {"id": e.id, "created_at": e.created_at.isoformat(), "strategy": e.strategy, "params": e.params,
            "symbol": e.symbol, "start_date": e.start_date, "end_date": e.end_date, "capital": e.capital,
            "fee_bps": e.fee_bps, "data_source": e.data_source, "metrics": e.metrics,
            "benchmark_metrics": e.benchmark_metrics}


@app.get("/experiments")
def list_experiments():
    with SessionLocal() as db:
        return [serialize(e) for e in db.query(Experiment).order_by(Experiment.id.desc())]


@app.delete("/experiments/{exp_id}")
def delete_experiment(exp_id: int):
    with SessionLocal() as db:
        e = db.get(Experiment, exp_id)
        if not e:
            raise HTTPException(404, "Experiment not found")
        db.delete(e)
        db.commit()
        return {"deleted": exp_id}
