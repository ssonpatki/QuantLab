export type Metrics = Record<string, number | null>;
export type Price = { date: string; open: number; high: number; low: number; close: number; volume: number };
export type PriceResp = { symbol: string; source: string; count: number; dropped_invalid_rows: number; prices: Price[] };
export type Trade = { entry_date: string; exit_date: string; entry_price: number; exit_price: number; pnl: number; return: number };
export type BacktestResp = {
  data_source: string; metrics: Metrics; benchmark_metrics: Metrics; trades: Trade[]; experiment_id: number | null;
  equity: { date: string; strategy: number; benchmark: number }[];
};
export type Experiment = {
  id: number; created_at: string; strategy: string; params: Record<string, number>; symbol: string;
  start_date: string; end_date: string; capital: number; fee_bps: number; data_source: string;
  metrics: Metrics; benchmark_metrics: Metrics;
};
export type PredictResp = {
  as_of: string; n_train: number; n_test: number; test_start: string; data_source: string; disclaimer: string;
  baseline: { mae_predict_zero: number; rmse_predict_zero: number; share_of_up_days: number };
  models: { name: string; mae: number; rmse: number; directional_accuracy: number; next_day_prediction: number }[];
};
export type RegimeResp = {
  data_source: string;
  summary: { regime: number; label: string; days: number; share: number; mean_daily_return: number; annualized_volatility: number }[];
  points: { date: string; close: number; regime: number }[];
};
export type AnomalyResp = {
  data_source: string; count: number; contamination: number;
  points: { date: string; close: number; anom_close: number | null; score: number }[];
  top: { date: string; daily_return: number; volume_zscore: number; score: number }[];
};
