import { useState } from "react";
import { MetricTable, Panel, Status } from "../components/Common";
import { useApi } from "../hooks/useApi";
import { pct } from "../format";
import { api } from "../services/api";
import type { Experiment } from "../types";

export default function Experiments({ reload }: { reload: number }) {
  const [bump, setBump] = useState(0);
  const [picked, setPicked] = useState<number[]>([]);
  const { data, error, loading } = useApi<Experiment[]>("/backtest/experiments", reload + bump);
  const chosen = (data ?? []).filter((e) => picked.includes(e.id));
  const label = (e: Experiment) => `#${e.id} ${e.symbol} ${e.strategy === "rsi" ? "RSI" : "SMA"}`;

  async function remove(id: number) {
    await api(`/backtest/experiments/${id}`, { method: "DELETE" });
    setPicked(picked.filter((p) => p !== id));
    setBump((n) => n + 1);
  }

  return (
    <>
      <Panel title="Saved experiments">
        <Status loading={loading} error={error} />
        {data && data.length === 0 && <p className="muted">Nothing saved yet. Run a backtest in Strategy Lab and choose Save as experiment.</p>}
        {data && data.length > 0 && (
          <div className="scroll"><table>
            <thead><tr><th>Compare</th><th>Experiment</th><th>Range</th><th>Parameters</th><th className="r">Return</th><th className="r">Sharpe</th><th>Data</th><th /></tr></thead>
            <tbody>{data.map((e) => (
              <tr key={e.id}>
                <td><input type="checkbox" aria-label={`Compare ${label(e)}`} checked={picked.includes(e.id)}
                  onChange={(ev) => setPicked(ev.target.checked ? [...picked, e.id] : picked.filter((p) => p !== e.id))} /></td>
                <td>{label(e)}</td><td>{e.start_date} to {e.end_date}</td>
                <td>{Object.entries(e.params).map(([k, v]) => `${k}=${v}`).join(", ")}</td>
                <td className="r">{pct(e.metrics.total_return)}</td><td className="r">{e.metrics.sharpe?.toFixed(2) ?? "—"}</td>
                <td>{e.data_source}</td><td><button className="link" onClick={() => remove(e.id)}>Delete</button></td>
              </tr>
            ))}</tbody>
          </table></div>
        )}
      </Panel>
      {chosen.length >= 2 && (
        <Panel title="Comparison">
          <MetricTable columns={chosen.map((e) => ({ label: label(e), metrics: e.metrics }))} />
        </Panel>
      )}
      {chosen.length === 1 && <p className="muted">Select one more experiment to compare.</p>}
    </>
  );
}
