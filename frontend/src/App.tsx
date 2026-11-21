import { FormEvent, useState } from "react";
import Experiments from "./pages/Experiments";
import MarketData from "./pages/MarketData";
import MlInsights from "./pages/MlInsights";
import StrategyLab from "./pages/StrategyLab";

const TABS = ["Market Data", "Strategy Lab", "ML Insights", "Experiments"] as const;
type Tab = (typeof TABS)[number];

export default function App() {
  const [tab, setTab] = useState<Tab>("Market Data");
  const [symbol, setSymbol] = useState("AAPL");
  const [draft, setDraft] = useState("AAPL");
  const [saves, setSaves] = useState(0);

  const submit = (e: FormEvent) => { e.preventDefault(); if (draft.trim()) setSymbol(draft.trim().toUpperCase()); };

  return (
    <div className="shell">
      <aside>
        <h1>QuantLab</h1>
        <form onSubmit={submit}>
          <label>Ticker
            <input value={draft} onChange={(e) => setDraft(e.target.value)} maxLength={12} />
          </label>
          <button type="submit">Load {draft.trim().toUpperCase() || "ticker"}</button>
        </form>
        <nav>
          {TABS.map((t) => (
            <button key={t} className={t === tab ? "active" : ""} onClick={() => setTab(t)}>{t}</button>
          ))}
        </nav>
        <p className="muted small">Research tool for learning. Not investment advice.</p>
      </aside>
      <main>
        {tab === "Market Data" && <MarketData symbol={symbol} />}
        {tab === "Strategy Lab" && <StrategyLab symbol={symbol} onSaved={() => setSaves((n) => n + 1)} />}
        {tab === "ML Insights" && <MlInsights symbol={symbol} />}
        {tab === "Experiments" && <Experiments reload={saves} />}
      </main>
    </div>
  );
}
