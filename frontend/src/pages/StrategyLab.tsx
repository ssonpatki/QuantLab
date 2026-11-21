import { useState } from "react";
import { CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { MetricTable, Panel, SourceBadge, Status } from "../components/Common";
import { num, pct, usd } from "../format";
import { postJson } from "../services/api";
import type { BacktestResp } from "../types";

const DEFAULTS: Record<string, Record<string, number>> = {
  sma_crossover: { short: 20, long: 50 },
  rsi: { period: 14, buy_below: 30, sell_above: 70 },
};
const NAMES: Record<string, string> = { sma_crossover: "Moving average crossover", rsi: "RSI mean reversion" };

export default function StrategyLab({ symbol, onSaved }: { symbol: string; onSaved: () => void }) {
  const [strategy, setStrategy] = useState("sma_crossover");
  const [params, setParams] = useState(DEFAULTS.sma_crossover);
  const [capital, setCapital] = useState(10000);
  const [fee, setFee] = useState(5);
  const [start, setStart] = useState("");
  const [end, setEnd] = useState("");
  const [res, setRes] = useState<BacktestResp | null>(null);
  const [state, setState] = useState({ loading: false, error: "", saved: "" });

  async function run(save: boolean) {
    setState({ loading: true, error: "", saved: "" });
    try {
      const r = await postJson<BacktestResp>("/backtest/backtests", {
        symbol, strategy, params, capital, fee_bps: fee, save,
        start_date: start || null, end_date: end || null,
      });
      setRes(r);
      setState({ loading: false, error: "", saved: save ? `Saved as experiment #${r.experiment_id}` : "" });
      if (save) onSaved();
    } catch (e) {
      setState({ loading: false, error: (e as Error).message, saved: "" });
    }
  }

  return (
    <>
      <Panel title={`Backtest ${symbol}`}>
        <div className="form">
          <label>Strategy
            <select value={strategy} onChange={(e) => { setStrategy(e.target.value); setParams(DEFAULTS[e.target.value]); }}>
              {Object.keys(DEFAULTS).map((k) => <option key={k} value={k}>{NAMES[k]}</option>)}
            </select>
          </label>
          {Object.entries(params).map(([k, v]) => (
            <label key={k}>{k.replace("_", " ")}
              <input type="number" value={v} onChange={(e) => setParams({ ...params, [k]: Number(e.target.value) })} />
            </label>
          ))}
          <label>Starting capital ($)<input type="number" value={capital} onChange={(e) => setCapital(Number(e.target.value))} /></label>
          <label>Fee per trade (bps)<input type="number" value={fee} onChange={(e) => setFee(Number(e.target.value))} /></label>
          <label>From<input type="date" value={start} onChange={(e) => setStart(e.target.value)} /></label>
          <label>To<input type="date" value={end} onChange={(e) => setEnd(e.target.value)} /></label>
        </div>
        <div className="row">
          <button onClick={() => run(false)} disabled={state.loading}>Run backtest</button>
          {res && <button className="secondary" onClick={() => run(true)} disabled={state.loading}>Save as experiment</button>}
          <span className="muted">{state.saved}</span>
        </div>
        <Status loading={state.loading} error={state.error} />
      </Panel>

      {res && (
        <>
          <Panel title="Equity curve">
            <p className="row"><SourceBadge source={res.data_source} />
              <span className="muted">Final value {usd(res.metrics.final_value ?? 0)} vs buy-and-hold {usd(res.benchmark_metrics.final_value ?? 0)}</span></p>
            <div className="chart">
              <ResponsiveContainer>
                <LineChart data={res.equity}>
                  <CartesianGrid stroke="#dde3ea" vertical={false} />
                  <XAxis dataKey="date" minTickGap={60} tick={{ fontSize: 12 }} />
                  <YAxis domain={["auto", "auto"]} tick={{ fontSize: 12 }} width={65} tickFormatter={(v: number) => usd(v)} />
                  <Tooltip formatter={(v: number) => usd(v)} />
                  <Legend />
                  <Line name="Strategy" dataKey="strategy" stroke="#1f4fd8" dot={false} strokeWidth={2} />
                  <Line name="Buy and hold" dataKey="benchmark" stroke="#8a97a6" dot={false} strokeWidth={1.6} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </Panel>
          <Panel title="Performance">
            <MetricTable columns={[{ label: "Strategy", metrics: res.metrics }, { label: "Buy and hold", metrics: res.benchmark_metrics }]} />
            <p className="muted">Trades execute at the next day's open. 252 trading days per year, risk-free rate 0.</p>
          </Panel>
          <Panel title={`Trades (${res.trades.length})`}>
            {res.trades.length === 0 ? <p className="muted">The strategy never closed a trade in this range.</p> : (
              <div className="scroll"><table>
                <thead><tr><th>Entry</th><th>Exit</th><th className="r">Entry price</th><th className="r">Exit price</th><th className="r">Return</th><th className="r">P&amp;L</th></tr></thead>
                <tbody>{res.trades.slice(-50).map((t) => (
                  <tr key={t.entry_date}><td>{t.entry_date}</td><td>{t.exit_date}</td><td className="r">{num(t.entry_price)}</td>
                    <td className="r">{num(t.exit_price)}</td><td className="r">{pct(t.return)}</td><td className="r">{usd(t.pnl)}</td></tr>
                ))}</tbody>
              </table></div>
            )}
          </Panel>
        </>
      )}
    </>
  );
}
