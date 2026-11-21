import { CartesianGrid, ComposedChart, Line, ReferenceArea, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { Panel, SourceBadge, Status } from "../components/Common";
import { useApi } from "../hooks/useApi";
import { num, pct } from "../format";
import type { AnomalyResp, PredictResp, RegimeResp } from "../types";

const REGIME_COLORS = ["#2a9d8f", "#e0a100", "#c8452c"];

function segments(pts: RegimeResp["points"]) {
  const out: { x1: string; x2: string; regime: number }[] = [];
  let s = 0;
  for (let i = 1; i <= pts.length; i++) {
    if (i === pts.length || pts[i].regime !== pts[s].regime) {
      out.push({ x1: pts[s].date, x2: pts[i - 1].date, regime: pts[s].regime });
      s = i;
    }
  }
  return out;
}

export default function MlInsights({ symbol }: { symbol: string }) {
  const pred = useApi<PredictResp>(`/ml/predict/${symbol}`);
  const reg = useApi<RegimeResp>(`/ml/regimes/${symbol}?k=3`);
  const ano = useApi<AnomalyResp>(`/ml/anomalies/${symbol}?contamination=0.02`);

  return (
    <>
      <Panel title="Next-day return prediction">
        <Status loading={pred.loading} error={pred.error} />
        {pred.data && (
          <>
            <p className="row"><SourceBadge source={pred.data.data_source} />
              <span className="muted">Trained on {pred.data.n_train} days, tested on {pred.data.n_test} later days (from {pred.data.test_start}).</span></p>
            <div className="scroll"><table>
              <thead><tr><th>Model</th><th className="r">MAE</th><th className="r">RMSE</th><th className="r">Direction accuracy</th><th className="r">Prediction for next day</th></tr></thead>
              <tbody>
                <tr className="baseline"><td>Baseline: always predict 0</td><td className="r">{pct(pred.data.baseline.mae_predict_zero, 2)}</td>
                  <td className="r">{pct(pred.data.baseline.rmse_predict_zero, 2)}</td>
                  <td className="r">{pct(pred.data.baseline.share_of_up_days)} (if always "up")</td><td className="r">—</td></tr>
                {pred.data.models.map((m) => (
                  <tr key={m.name}><td>{m.name}</td><td className="r">{pct(m.mae, 2)}</td><td className="r">{pct(m.rmse, 2)}</td>
                    <td className="r">{pct(m.directional_accuracy)}</td><td className="r">{pct(m.next_day_prediction, 2)}</td></tr>
                ))}
              </tbody>
            </table></div>
            <p className="muted">Data as of {pred.data.as_of}. A model only matters if it beats the baseline on unseen days; daily returns are mostly noise. {pred.data.disclaimer}</p>
          </>
        )}
      </Panel>

      <Panel title="Market regimes (K-Means, 3 clusters)">
        <Status loading={reg.loading} error={reg.error} />
        {reg.data && (
          <>
            <div className="chart">
              <ResponsiveContainer>
                <ComposedChart data={reg.data.points}>
                  <CartesianGrid stroke="#dde3ea" vertical={false} />
                  <XAxis dataKey="date" minTickGap={60} tick={{ fontSize: 12 }} />
                  <YAxis domain={["auto", "auto"]} tick={{ fontSize: 12 }} width={55} />
                  <Tooltip />
                  {segments(reg.data.points).map((s, i) => (
                    <ReferenceArea key={i} x1={s.x1} x2={s.x2} fill={REGIME_COLORS[s.regime]} fillOpacity={0.2} strokeOpacity={0} />
                  ))}
                  <Line dataKey="close" stroke="#14212b" dot={false} strokeWidth={1.3} />
                </ComposedChart>
              </ResponsiveContainer>
            </div>
            <div className="scroll"><table>
              <thead><tr><th>Regime</th><th className="r">Days</th><th className="r">Share</th><th className="r">Mean daily return</th><th className="r">Annualized volatility</th></tr></thead>
              <tbody>{reg.data.summary.map((s) => (
                <tr key={s.regime}><td><span className="swatch" style={{ background: REGIME_COLORS[s.regime] }} />{s.label}</td>
                  <td className="r">{s.days}</td><td className="r">{pct(s.share, 0)}</td>
                  <td className="r">{pct(s.mean_daily_return, 3)}</td><td className="r">{pct(s.annualized_volatility)}</td></tr>
              ))}</tbody>
            </table></div>
            <p className="muted">Clusters are ranked by average volatility. They describe the past and are fit on the full history.</p>
          </>
        )}
      </Panel>

      <Panel title="Anomalous days (Isolation Forest)">
        <Status loading={ano.loading} error={ano.error} />
        {ano.data && (
          <>
            <div className="chart">
              <ResponsiveContainer>
                <ComposedChart data={ano.data.points}>
                  <CartesianGrid stroke="#dde3ea" vertical={false} />
                  <XAxis dataKey="date" minTickGap={60} tick={{ fontSize: 12 }} />
                  <YAxis domain={["auto", "auto"]} tick={{ fontSize: 12 }} width={55} />
                  <Tooltip />
                  <Line dataKey="close" stroke="#14212b" dot={false} strokeWidth={1.3} />
                  <Line dataKey="anom_close" stroke="none" dot={{ r: 3.5, fill: "#c8452c", stroke: "none" }} activeDot={false} isAnimationActive={false} />
                </ComposedChart>
              </ResponsiveContainer>
            </div>
            <p className="muted">{ano.data.count} days flagged. The {pct(ano.data.contamination, 0)} flag rate is a setting we chose, not a measured fact. Most unusual days:</p>
            <div className="scroll"><table>
              <thead><tr><th>Date</th><th className="r">Daily return</th><th className="r">Volume z-score</th><th className="r">Anomaly score</th></tr></thead>
              <tbody>{ano.data.top.map((t) => (
                <tr key={t.date}><td>{t.date}</td><td className="r">{pct(t.daily_return, 2)}</td><td className="r">{num(t.volume_zscore)}</td><td className="r">{num(t.score, 3)}</td></tr>
              ))}</tbody>
            </table></div>
          </>
        )}
      </Panel>
    </>
  );
}
