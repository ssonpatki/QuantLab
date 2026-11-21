"""Each strategy turns prices into a daily target position (1 = long, 0 = cash).
Signals use each day's CLOSE; the engine executes them on the NEXT day's open."""
import pandas as pd


class BaseStrategy:
    name = "base"

    def __init__(self, **params):
        self.params = params

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        raise NotImplementedError


class SMACrossover(BaseStrategy):
    name = "sma_crossover"

    def __init__(self, short: int = 20, long: int = 50):
        if not 1 <= short < long:
            raise ValueError("short must be >= 1 and smaller than long")
        super().__init__(short=int(short), long=int(long))

    def generate_signals(self, df):
        fast = df["close"].rolling(self.params["short"]).mean()
        slow = df["close"].rolling(self.params["long"]).mean()
        return (fast > slow).astype(int)


class RSIStrategy(BaseStrategy):
    name = "rsi"

    def __init__(self, period: int = 14, buy_below: float = 30, sell_above: float = 70):
        if period < 2 or not 0 < buy_below < sell_above < 100:
            raise ValueError("Need period >= 2 and 0 < buy_below < sell_above < 100")
        super().__init__(period=int(period), buy_below=float(buy_below), sell_above=float(sell_above))

    def generate_signals(self, df):
        p = self.params
        delta = df["close"].diff()
        gain = delta.clip(lower=0).ewm(alpha=1 / p["period"], adjust=False).mean()
        loss = (-delta.clip(upper=0)).ewm(alpha=1 / p["period"], adjust=False).mean()
        rsi = 100 - 100 / (1 + gain / loss)
        pos, out = 0, []
        for v in rsi:
            if v < p["buy_below"]:
                pos = 1
            elif v > p["sell_above"]:
                pos = 0
            out.append(pos)  # in-between values keep the current position
        return pd.Series(out, index=df.index)


REGISTRY = {"sma_crossover": SMACrossover, "rsi": RSIStrategy}
