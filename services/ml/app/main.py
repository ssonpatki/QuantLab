import os
import httpx
import pandas as pd
from fastapi import FastAPI, HTTPException, Query

from .models import detect_anomalies, detect_regimes, evaluate_models

MARKET_URL = os.getenv("MARKET_URL", "http://localhost:8001")
app = FastAPI(title="QuantLab ML Service")


def load(symbol: str):
    try:
        r = httpx.get(f"{MARKET_URL}/prices/{symbol.strip().upper()}", timeout=120)
    except httpx.HTTPError:
        raise HTTPException(503, "Market data service is unreachable")
    if r.status_code != 200:
        raise HTTPException(r.status_code, r.json().get("detail", "Market data error"))
    body = r.json()
    df = pd.DataFrame(body["prices"])
    df["date"] = pd.to_datetime(df["date"])
    return df.set_index("date"), body["source"]


def guarded(fn, *a):
    try:
        return fn(*a)
    except ValueError as e:
        raise HTTPException(422, str(e))


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.get("/predict/{symbol}")
def predict(symbol: str):
    df, src = load(symbol)
    return {"symbol": symbol.upper(), "data_source": src, **guarded(evaluate_models, df),
            "disclaimer": "Experimental research output, not investment advice."}


@app.get("/regimes/{symbol}")
def regimes(symbol: str, k: int = Query(3, ge=2, le=5)):
    df, src = load(symbol)
    return {"symbol": symbol.upper(), "data_source": src, **guarded(detect_regimes, df, k)}


@app.get("/anomalies/{symbol}")
def anomalies(symbol: str, contamination: float = Query(0.02, gt=0.001, le=0.1)):
    df, src = load(symbol)
    return {"symbol": symbol.upper(), "data_source": src, **guarded(detect_anomalies, df, contamination)}
