import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.ensemble import IsolationForest, RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from xgboost import XGBRegressor

from .features import FEATURES, make_features


def evaluate_models(df: pd.DataFrame, test_frac: float = 0.3) -> dict:
    """Predict NEXT-day return. Chronological split with a 1-day embargo; no shuffling."""
    f = make_features(df)[FEATURES]
    y = df["close"].pct_change().shift(-1)  # return from t to t+1
    data = f.assign(y=y).dropna()
    latest = f.iloc[[-1]]
    if len(data) < 150 or latest.isna().any(axis=None):
        raise ValueError("Need at least ~200 daily observations")
    cut = int(len(data) * (1 - test_frac))
    train, test = data.iloc[:cut], data.iloc[cut + 1:]
    models = {
        "Linear Regression": make_pipeline(StandardScaler(), LinearRegression()),
        "Random Forest": RandomForestRegressor(n_estimators=150, max_depth=5, min_samples_leaf=20,
                                               random_state=42, n_jobs=1),
        "XGBoost": XGBRegressor(n_estimators=200, max_depth=3, learning_rate=0.05, subsample=0.8,
                                random_state=42, n_jobs=1),
    }
    out = []
    for name, m in models.items():
        m.fit(train[FEATURES], train["y"])
        p = m.predict(test[FEATURES])
        err = p - test["y"].values
        out.append({"name": name, "mae": float(np.abs(err).mean()), "rmse": float(np.sqrt((err ** 2).mean())),
                    "directional_accuracy": float((np.sign(p) == np.sign(test["y"].values)).mean()),
                    "next_day_prediction": float(m.predict(latest)[0])})
    return {"as_of": df.index[-1].strftime("%Y-%m-%d"), "n_train": len(train), "n_test": len(test),
            "test_start": test.index[0].strftime("%Y-%m-%d"),
            "baseline": {"mae_predict_zero": float(test["y"].abs().mean()),
                         "rmse_predict_zero": float(np.sqrt((test["y"] ** 2).mean())),
                         "share_of_up_days": float((test["y"] > 0).mean())},
            "models": out}


def detect_regimes(df: pd.DataFrame, k: int = 3) -> dict:
    """K-Means on volatility/momentum, fit on the whole history (descriptive, not a live forecast).
    Regimes are numbered by average volatility: 0 = calmest."""
    X = make_features(df)[["vol_21", "mom_21", "ret_5"]].dropna()
    if len(X) < 100:
        raise ValueError("Need at least ~130 daily observations")
    km = KMeans(n_clusters=k, n_init=10, random_state=42).fit(StandardScaler().fit_transform(X))
    order = X.groupby(km.labels_)["vol_21"].mean().sort_values().index.tolist()
    regime = pd.Series(km.labels_, index=X.index).map({c: i for i, c in enumerate(order)})
    names = ["Low volatility", "Medium volatility", "High volatility"] if k == 3 else \
        [f"Volatility tier {i + 1} of {k}" for i in range(k)]
    ret = df["close"].pct_change().reindex(X.index)
    summary = [{"regime": i, "label": names[i], "days": int((regime == i).sum()),
                "share": float((regime == i).mean()), "mean_daily_return": float(ret[regime == i].mean()),
                "annualized_volatility": float(ret[regime == i].std() * np.sqrt(252))} for i in range(k)]
    pts = [{"date": d.strftime("%Y-%m-%d"), "close": float(df.loc[d, "close"]), "regime": int(r)}
           for d, r in regime.items()]
    return {"k": k, "summary": summary, "points": pts}


def detect_anomalies(df: pd.DataFrame, contamination: float = 0.02) -> dict:
    """Isolation Forest on return, volatility, volume z-score and daily range.
    `contamination` is an assumption about how many days to flag, not a known anomaly rate."""
    X = make_features(df)[["ret_1", "vol_10", "vol_z", "range"]].dropna()
    if len(X) < 100:
        raise ValueError("Need at least ~130 daily observations")
    iso = IsolationForest(n_estimators=200, contamination=contamination, random_state=42).fit(X)
    flag, score = iso.predict(X) == -1, -iso.score_samples(X)
    pts = [{"date": d.strftime("%Y-%m-%d"), "close": float(df.loc[d, "close"]),
            "anom_close": float(df.loc[d, "close"]) if a else None, "score": float(s)}
           for d, a, s in zip(X.index, flag, score)]
    top = X.assign(score=score)[flag].sort_values("score", ascending=False).head(10)
    return {"contamination": contamination, "count": int(flag.sum()), "points": pts,
            "top": [{"date": d.strftime("%Y-%m-%d"), "daily_return": float(r.ret_1),
                     "volume_zscore": float(r.vol_z), "score": float(r.score)} for d, r in top.iterrows()]}
