"""Data sources + cleaning. Every source returns a DataFrame indexed by date with COLS."""
import io
import zlib
import numpy as np
import pandas as pd

COLS = ["open", "high", "low", "close", "volume"]


def clean(df: pd.DataFrame):
    """Validate and normalise. Returns (clean_df, number_of_rows_dropped)."""
    df = df.copy()
    df.columns = [str(c).lower().strip() for c in df.columns]
    missing = [c for c in COLS if c not in df.columns]
    if missing:
        raise ValueError(f"Missing columns: {', '.join(missing)}")
    n0 = len(df)
    df = df[COLS].apply(pd.to_numeric, errors="coerce").dropna()
    df = df[(df[["open", "high", "low", "close"]] > 0).all(axis=1) & (df["high"] >= df["low"])]
    df = df[~df.index.duplicated(keep="last")].sort_index()
    return df, n0 - len(df)


def from_yfinance(symbol: str, years: int) -> pd.DataFrame:
    import yfinance as yf  # lazy import so tests/offline use don't need it
    h = yf.Ticker(symbol).history(period=f"{years}y", interval="1d", auto_adjust=True)
    if h is None or h.empty:
        raise ValueError(f"No data returned for {symbol}")
    h = h.reset_index()
    h.columns = [str(c).lower() for c in h.columns]
    h["date"] = pd.to_datetime(h["date"]).dt.tz_localize(None).dt.normalize().dt.date
    return h.set_index("date")


def from_csv(raw: bytes) -> pd.DataFrame:
    df = pd.read_csv(io.BytesIO(raw))
    df.columns = [c.lower().strip() for c in df.columns]
    if "date" not in df.columns:
        raise ValueError("CSV needs a 'date' column")
    df["date"] = pd.to_datetime(df["date"]).dt.date
    return df.set_index("date")


def synthetic(symbol: str, years: int = 5) -> pd.DataFrame:
    """Regime-switching random walk, deterministic per symbol. Demo data only, NOT real prices."""
    rng = np.random.default_rng(zlib.crc32(symbol.encode()))
    n = int(years * 252)
    idx = pd.bdate_range(end=pd.Timestamp.today().normalize(), periods=n)
    state, s = np.zeros(n, dtype=int), 0
    for i in range(n):
        if rng.random() < 0.02:
            s = int(rng.integers(0, 3))
        state[i] = s
    r = np.array([0.0006, 0.0002, -0.0008])[state] + np.array([0.008, 0.015, 0.03])[state] * rng.standard_normal(n)
    close = 100 * np.exp(np.cumsum(r))
    open_ = np.r_[100.0, close[:-1]] * (1 + 0.002 * rng.standard_normal(n))
    high = np.maximum(open_, close) * (1 + 0.004 * np.abs(rng.standard_normal(n)))
    low = np.minimum(open_, close) * (1 - 0.004 * np.abs(rng.standard_normal(n)))
    vol = (1e6 * np.exp(0.4 * rng.standard_normal(n)) * (1 + 40 * np.abs(r))).astype(np.int64)
    return pd.DataFrame({"open": open_, "high": high, "low": low, "close": close, "volume": vol},
                        index=[d.date() for d in idx])
