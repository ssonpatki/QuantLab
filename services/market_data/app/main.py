import os
import re
from datetime import date
from typing import Optional

from fastapi import FastAPI, File, HTTPException, UploadFile
from sqlalchemy import func

from . import providers
from .db import Asset, Price, SessionLocal

app = FastAPI(title="QuantLab Market Data Service")
SYMBOL_RE = re.compile(r"^[A-Z0-9.\-^=]{1,12}$")
ALLOW_SYNTHETIC = os.getenv("SYNTHETIC_FALLBACK", "true").lower() == "true"


def norm(symbol: str) -> str:
    s = symbol.strip().upper()
    if not SYMBOL_RE.match(s):
        raise HTTPException(400, "Invalid ticker symbol")
    return s


def store(db, symbol: str, df, source: str) -> int:
    """Insert only dates we don't already have (no duplicate rows)."""
    have = {d for (d,) in db.query(Price.date).filter(Price.symbol == symbol)}
    rows = [Price(symbol=symbol, date=d, open=float(r.open), high=float(r.high), low=float(r.low),
                  close=float(r.close), volume=int(r.volume))
            for d, r in df.iterrows() if d not in have]
    db.add_all(rows)
    db.merge(Asset(symbol=symbol, source=source))
    db.commit()
    return len(rows)


def acquire(db, symbol: str, years: int):
    """yfinance first; synthetic demo data only as a fallback for brand-new symbols."""
    try:
        return providers.from_yfinance(symbol, years), "yfinance"
    except Exception as e:
        has_data = db.query(func.count(Price.id)).filter(Price.symbol == symbol).scalar() > 0
        if ALLOW_SYNTHETIC and not has_data:
            return providers.synthetic(symbol, years), "synthetic"
        raise HTTPException(502, f"Could not fetch {symbol}: {e}")


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.get("/assets")
def assets():
    with SessionLocal() as db:
        return [{"symbol": a.symbol, "source": a.source} for a in db.query(Asset).order_by(Asset.symbol)]


@app.get("/prices/{symbol}")
def prices(symbol: str, start_date: Optional[date] = None, end_date: Optional[date] = None):
    symbol = norm(symbol)
    if start_date and end_date and start_date >= end_date:
        raise HTTPException(400, "start_date must be before end_date")
    with SessionLocal() as db:
        asset, dropped = db.get(Asset, symbol), 0
        if asset is None:  # first request for this symbol: ingest it
            df, source = acquire(db, symbol, 5)
            df, dropped = providers.clean(df)
            store(db, symbol, df, source)
            asset = db.get(Asset, symbol)
        q = db.query(Price).filter(Price.symbol == symbol)
        if start_date:
            q = q.filter(Price.date >= start_date)
        if end_date:
            q = q.filter(Price.date <= end_date)
        rows = q.order_by(Price.date).all()
        return {"symbol": symbol, "source": asset.source, "count": len(rows), "dropped_invalid_rows": dropped,
                "prices": [{"date": r.date.isoformat(), "open": r.open, "high": r.high, "low": r.low,
                            "close": r.close, "volume": r.volume} for r in rows]}


@app.post("/ingest/{symbol}")
def ingest(symbol: str, years: int = 5):
    symbol = norm(symbol)
    if not 1 <= years <= 20:
        raise HTTPException(400, "years must be between 1 and 20")
    with SessionLocal() as db:
        df, source = acquire(db, symbol, years)
        df, dropped = providers.clean(df)
        return {"symbol": symbol, "source": source, "inserted": store(db, symbol, df, source), "dropped": dropped}


@app.post("/import-csv/{symbol}")
async def import_csv(symbol: str, file: UploadFile = File(...)):
    symbol = norm(symbol)
    try:
        df, dropped = providers.clean(providers.from_csv(await file.read()))
    except Exception as e:
        raise HTTPException(422, f"Invalid CSV: {e}")
    with SessionLocal() as db:
        return {"symbol": symbol, "source": "csv", "inserted": store(db, symbol, df, "csv"), "dropped": dropped}
