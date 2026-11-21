import pandas as pd
from app.providers import clean, from_csv, synthetic


def test_synthetic_is_valid_and_deterministic():
    a = synthetic("AAPL", 2)
    assert a.equals(synthetic("AAPL", 2))
    assert clean(a)[1] == 0


def test_clean_drops_bad_rows_and_dupes():
    idx = pd.to_datetime(["2025-01-01", "2025-01-01", "2025-01-02"]).date
    df = pd.DataFrame({"open": [1, 1, -1], "high": [2, 2, 2], "low": [1, 1, 1],
                       "close": [1.5, 1.5, 1], "volume": [1, 1, 1]}, index=idx)
    out, dropped = clean(df)
    assert len(out) == 1 and dropped == 2


def test_csv_import():
    out, _ = clean(from_csv(b"Date,Open,High,Low,Close,Volume\n2025-01-02,1,2,1,1.5,100\n"))
    assert len(out) == 1
