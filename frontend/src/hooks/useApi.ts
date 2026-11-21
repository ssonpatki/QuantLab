import { useEffect, useState } from "react";
import { api } from "../services/api";

export function useApi<T>(path: string | null, reload = 0) {
  const [s, setS] = useState<{ data: T | null; error: string; loading: boolean }>({ data: null, error: "", loading: false });
  useEffect(() => {
    if (!path) return;
    let live = true;
    setS((p) => ({ ...p, loading: true, error: "" }));
    api<T>(path)
      .then((data) => live && setS({ data, error: "", loading: false }))
      .catch((e: Error) => live && setS({ data: null, error: e.message, loading: false }));
    return () => { live = false; };
  }, [path, reload]);
  return s;
}
