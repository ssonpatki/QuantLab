import numpy as np
import pandas as pd
from app.features import FEATURES, make_features
from app.models import detect_anomalies, detect_regimes, evaluate_models


def prices(n=600):
    rng = np.random.default_rng(0)
    close = 100 * np.exp(np.cumsum(0.0003 + 0.01 * rng.standard_normal(n)))
    return pd.DataFrame({"open": close, "high": close * 1.01, "low": close * 0.99, "close": close,
                         "volume": rng.integers(1_000_000, 2_000_000, n)}, index=pd.bdate_range("2022-01-03", periods=n))


def test_features_have_no_lookahead():
    df = prices()
    pd.testing.assert_frame_equal(make_features(df)[FEATURES].iloc[:400], make_features(df.iloc[:400])[FEATURES])


def test_models_regimes_anomalies_run():
    df = prices()
    out = evaluate_models(df)
    assert len(out["models"]) == 3 and out["n_test"] > 0
    assert len(detect_regimes(df)["summary"]) == 3
    assert detect_anomalies(df)["count"] > 0
