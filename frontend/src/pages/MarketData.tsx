import { ChangeEvent, useState } from "react";
import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { Panel, SourceBadge, Status } from "../components/Common";
import { useApi } from "../hooks/useApi";
import { num } from "../format";
import { api } from "../services/api";
import type { PriceResp } from "../types";

export default function MarketData({ symbol }: { symbol: string }) {
  const [reload, setReload] = useState(0);
  const [msg, setMsg] = useState("");
  const { data, error, loading } = useApi<PriceResp>(`/market/prices/${symbol}`, reload);

  async function act(fn: () => Promise<unknown>, ok: string) {
    setMsg("");
    try { await fn(); setMsg(ok); setReload((n) => n + 1); } catch (e) { setMsg((e as Error).message); }
  }
  const upload = (e: ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0];
    if (!f) return;
    const fd = new FormData();
    fd.append("file", f);
    act(() => api(`/market/import-csv/${symbol}`, { method: "POST", body: fd }), "CSV imported");
    e.target.value = "";
  };
  const last = data?.prices[data.prices.length - 1];

  return (
    <Panel title={`${symbol} daily prices`}>
      <Status loading={loading} error={error} />
      {data && (
        <>
          <p className="row">
            <SourceBadge source={data.source} />
            <span className="muted">{data.count} trading days, {data.prices[0]?.date} to {last?.date}. Last close {num(last?.close)}.</span>
          </p>
          <div className="chart">
            <ResponsiveContainer>
              <LineChart data={data.prices}>
                <CartesianGrid stroke="#dde3ea" vertical={false} />
                <XAxis dataKey="date" minTickGap={60} tick={{ fontSize: 12 }} />
                <YAxis domain={["auto", "auto"]} tick={{ fontSize: 12 }} width={55} />
                <Tooltip />
                <Line dataKey="close" stroke="#1f4fd8" dot={false} strokeWidth={1.6} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </>
      )}
      <div className="row">
        <button onClick={() => act(() => api(`/market/ingest/${symbol}`, { method: "POST" }), "Prices refreshed")}>Refresh from Yahoo Finance</button>
        <label className="button secondary">Import CSV<input type="file" accept=".csv" onChange={upload} hidden /></label>
        <span className="muted">{msg}</span>
      </div>
      <p className="muted">CSV columns: date, open, high, low, close, volume. Existing dates are never duplicated.</p>
    </Panel>
  );
}
