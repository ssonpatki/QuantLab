"""Assumptions: 252 trading days/year, risk-free rate 0, volatility = daily-return std * sqrt(252),
CAGR uses the number of trading days, win rate = profitable closed trades / closed trades."""
import math
import numpy as np


def _f(x):
    x = float(x)
    return x if math.isfinite(x) else None


def compute_metrics(equity, capital: float, trades: list) -> dict:
    eq = np.r_[capital, np.asarray(equity, dtype=float)]
    rets = eq[1:] / eq[:-1] - 1
    total = eq[-1] / capital - 1
    years = len(equity) / 252
    cagr = (1 + total) ** (1 / years) - 1 if years > 0 and 1 + total > 0 else None
    sd = rets.std(ddof=1) if len(rets) > 1 else 0.0
    dd = (eq / np.maximum.accumulate(eq) - 1).min()
    wins = sum(1 for t in trades if t["pnl"] > 0)
    return {"total_return": _f(total), "cagr": None if cagr is None else _f(cagr),
            "volatility": _f(sd * math.sqrt(252)),
            "sharpe": _f(rets.mean() / sd * math.sqrt(252)) if sd > 0 else None,
            "max_drawdown": _f(dd), "win_rate": wins / len(trades) if trades else None,
            "n_trades": len(trades), "final_value": _f(eq[-1])}
