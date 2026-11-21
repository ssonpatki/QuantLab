import type { ReactNode } from "react";
import { num, pct } from "../format";
import type { Metrics } from "../types";

export function Status({ loading, error }: { loading?: boolean; error?: string }) {
  if (error) return <p className="error" role="alert">{error}</p>;
  return loading ? <p className="muted">Working…</p> : null;
}

export function SourceBadge({ source }: { source: string }) {
  return source === "synthetic"
    ? <span className="badge warn">Synthetic demo data, not real prices</span>
    : <span className="badge">Data: {source}</span>;
}

export const Panel = ({ title, children }: { title: string; children: ReactNode }) => (
  <section className="panel"><h2>{title}</h2>{children}</section>
);

const ROWS: [string, string, "pct" | "num" | "int"][] = [
  ["total_return", "Total return", "pct"], ["cagr", "Annualized return", "pct"], ["volatility", "Volatility", "pct"],
  ["sharpe", "Sharpe ratio", "num"], ["max_drawdown", "Max drawdown", "pct"], ["win_rate", "Win rate", "pct"],
  ["n_trades", "Closed trades", "int"],
];

export function MetricTable({ columns }: { columns: { label: string; metrics: Metrics }[] }) {
  return (
    <div className="scroll">
      <table>
        <thead><tr><th>Metric</th>{columns.map((c) => <th key={c.label} className="r">{c.label}</th>)}</tr></thead>
        <tbody>
          {ROWS.map(([k, label, kind]) => (
            <tr key={k}>
              <td>{label}</td>
              {columns.map((c) => {
                const v = c.metrics[k];
                return <td key={c.label} className="r">{kind === "pct" ? pct(v) : kind === "num" ? num(v) : v ?? "—"}</td>;
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
