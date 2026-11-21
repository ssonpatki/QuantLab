import pandas as pd


def run_backtest(df: pd.DataFrame, signals: pd.Series, capital: float, fee_bps: float):
    """Long-only, one asset, all-in/all-out. A signal on day t executes at day t+1's OPEN (no look-ahead).
    Fee is charged on each buy and sell. An open position at the end is marked to market, not counted as a
    closed trade. Returns (equity Series, trades list)."""
    fee = fee_bps / 10_000
    target = signals.reindex(df.index).shift(1).fillna(0)
    cash, shares, entry = float(capital), 0.0, None
    equity, trades = [], []
    for ts, row in df.iterrows():
        want = target.loc[ts]
        if want == 1 and shares == 0:
            shares = cash * (1 - fee) / row["open"]
            entry = {"date": ts, "price": row["open"], "cost": cash}
            cash = 0.0
        elif want == 0 and shares > 0:
            proceeds = shares * row["open"] * (1 - fee)
            trades.append({"entry_date": entry["date"].strftime("%Y-%m-%d"), "exit_date": ts.strftime("%Y-%m-%d"),
                           "entry_price": float(entry["price"]), "exit_price": float(row["open"]),
                           "pnl": float(proceeds - entry["cost"]), "return": float(proceeds / entry["cost"] - 1)})
            cash, shares = proceeds, 0.0
        equity.append(cash + shares * row["close"])
    return pd.Series(equity, index=df.index), trades


def buy_and_hold(df: pd.DataFrame, capital: float, fee_bps: float) -> pd.Series:
    return capital * (1 - fee_bps / 10_000) / df["open"].iloc[0] * df["close"]
