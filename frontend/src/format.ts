export const pct = (x: number | null | undefined, d = 1) => (x == null ? "—" : `${(x * 100).toFixed(d)}%`);
export const num = (x: number | null | undefined, d = 2) => (x == null ? "—" : x.toFixed(d));
export const usd = (x: number) => x.toLocaleString("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 });
