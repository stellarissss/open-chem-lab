import { create } from "zustand";

export interface HealthState {
  status: "unknown" | "ok" | "error";
  version: string;
  protocol: string;
  uptimeMs: number | null;
  checkedAt: number | null;
  refresh: () => Promise<void>;
}

// 唯一取数口：/api/v1/health 经网关，不直连任何求解服务。
export const useHealth = create<HealthState>((set) => ({
  status: "unknown",
  version: "—",
  protocol: "—",
  uptimeMs: null,
  checkedAt: null,
  refresh: async () => {
    try {
      const res = await fetch("/api/v1/health");
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = (await res.json()) as {
        status?: string;
        version?: string;
        protocol?: string;
        uptime_ms?: number;
      };
      set({
        status: data.status === "ok" ? "ok" : "error",
        version: data.version ?? "—",
        protocol: data.protocol ?? "—",
        uptimeMs: data.uptime_ms ?? null,
        checkedAt: Date.now(),
      });
    } catch {
      set({ status: "error", checkedAt: Date.now() });
    }
  },
}));
