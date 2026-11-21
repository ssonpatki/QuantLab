import numpy as np
import pandas as pd

FEATURES = ["ret_1", "ret_5", "mom_21", "vol_10", "vol_21", "rsi_14",
            "sma_gap_20", "sma_gap_50", "macd_hist", "vol_chg"]


def make_features(df: pd.DataFrame) -> pd.DataFrame:
    """Every feature at row t uses only data up to and including day t's close."""
    c, r = df["close"], df["close"].pct_change()
    f = pd.DataFrame(index=df.index)
    f["ret_1"], f["ret_5"], f["mom_21"] = r, c.pct_change(5), c.pct_change(21)
    f["vol_10"], f["vol_21"] = r.rolling(10).std(), r.rolling(21).std()
    d = c.diff()
    gain = d.clip(lower=0).ewm(alpha=1 / 14, adjust=False).mean()
    loss = (-d.clip(upper=0)).ewm(alpha=1 / 14, adjust=False).mean()
    f["rsi_14"] = 100 - 100 / (1 + gain / loss)
    f["sma_gap_20"], f["sma_gap_50"] = c / c.rolling(20).mean() - 1, c / c.rolling(50).mean() - 1
    macd = c.ewm(span=12, adjust=False).mean() - c.ewm(span=26, adjust=False).mean()
    f["macd_hist"] = (macd - macd.ewm(span=9, adjust=False).mean()) / c
    f["vol_chg"] = np.log(df["volume"].replace(0, np.nan)).diff()
    f["range"] = (df["high"] - df["low"]) / c
    v = df["volume"].astype(float)
    f["vol_z"] = (v - v.rolling(21).mean()) / v.rolling(21).std()
    return f.replace([np.inf, -np.inf], np.nan)
