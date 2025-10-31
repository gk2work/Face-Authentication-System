import { useState, useEffect } from "react";
import { api } from "@/services";
import type { SystemHealth } from "@/types";

export const useSystemHealth = (
  autoRefresh: boolean = false,
  interval: number = 30000
) => {
  const [health, setHealth] = useState<SystemHealth | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchHealth = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.get<SystemHealth>("/api/v1/health");
      setHealth(data);
    } catch (err: any) {
      setError(err.message || "Failed to fetch system health");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHealth();

    if (autoRefresh) {
      const intervalId = setInterval(fetchHealth, interval);
      return () => clearInterval(intervalId);
    }
  }, [autoRefresh, interval]);

  return { health, loading, error, refetch: fetchHealth };
};
