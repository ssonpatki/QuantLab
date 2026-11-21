const BASE = (import.meta.env.VITE_API_URL as string | undefined) ?? "/api";

export async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const r = await fetch(BASE + path, init);
  if (!r.ok) {
    let msg = r.statusText;
    try {
      const b = await r.json();
      msg = typeof b.detail === "string" ? b.detail : JSON.stringify(b.detail);
    } catch { /* keep statusText */ }
    throw new Error(msg);
  }
  return r.json() as Promise<T>;
}

export const postJson = <T,>(path: string, body: unknown) =>
  api<T>(path, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
