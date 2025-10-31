import { useState, useEffect } from "react";
import { api } from "@/services";
import type { DashboardStatistics } from "@/types/dashboard";

export const useDashboardStats = (
  autoRefresh: boolean = false,
  interval: number = 30000
) => {
  const [stats, setStats] = useState<DashboardStatistics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchStats = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.get<DashboardStatistics>(
        "/api/v1/dashboard/statistics"
      );
      setStats(data);
    } catch (err: any) {
      setError(err.message || "Failed to fetch statistics");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStats();

    if (autoRefresh) {
      const intervalId = setInterval(fetchStats, interval);
      return () => clearInterval(intervalId);
    }
  }, [autoRefresh, interval]);

  return { stats, loading, error, refetch: fetchStats };
};
