import pandas as pd
import pytest
from app.engine import run_backtest
from app.metrics import compute_metrics
from app.strategies import RSIStrategy, SMACrossover


def frame():
    idx = pd.to_datetime(["2025-01-01", "2025-01-02", "2025-01-03", "2025-01-06"])
    return pd.DataFrame({"open": [10, 10, 12, 15.0], "close": [10, 11, 12, 15.0]}, index=idx)


def test_hand_calculated_trade_executes_next_open():
    df = frame()
    equity, trades = run_backtest(df, pd.Series([1, 1, 0, 0], index=df.index), 1000, 0)
    # signal on day0 close -> buy day1 open (10) = 100 shares; sell day3 open (15) = 1500
    assert len(trades) == 1 and trades[0]["entry_date"] == "2025-01-02"
    assert trades[0]["pnl"] == 500 and equity.iloc[-1] == 1500


def test_fees_reduce_proceeds():
    df = frame()
    _, trades = run_backtest(df, pd.Series([1, 1, 0, 0], index=df.index), 1000, 100)  # 1% per side
    assert round(trades[0]["pnl"], 2) == round(1000 * 0.99 * 1.5 * 0.99 - 1000, 2)


def test_max_drawdown_and_total_return():
    m = compute_metrics([110, 99, 120], 100, [])
    assert round(m["max_drawdown"], 4) == -0.1 and round(m["total_return"], 4) == 0.2


def test_strategy_validation():
    with pytest.raises(ValueError):
        SMACrossover(short=50, long=20)
    with pytest.raises(ValueError):
        RSIStrategy(buy_below=80, sell_above=70)
