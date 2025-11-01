/**
 * Custom hook for fetching aggregate admin statistics with caching
 */

import { useState, useEffect, useCallback, useRef } from "react";
import { superadminApi } from "../services/api";
import type { AggregateAdminStats } from "../types";

interface UseAggregateStatsOptions {
  autoFetch?: boolean;
  cacheTTL?: number; // Cache time-to-live in milliseconds (default: 5 minutes)
}

interface UseAggregateStatsReturn {
  data: AggregateAdminStats | null;
  loading: boolean;
  error: Error | null;
  refetch: () => Promise<void>;
  isCached: boolean;
}

export const useAggregateStats = (
  options: UseAggregateStatsOptions = {}
): UseAggregateStatsReturn => {
  const { autoFetch = true, cacheTTL = 5 * 60 * 1000 } = options; // 5 minutes default

  const [data, setData] = useState<AggregateAdminStats | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<Error | null>(null);
  const [isCached, setIsCached] = useState<boolean>(false);

  const lastFetchTime = useRef<number>(0);
  const cacheData = useRef<AggregateAdminStats | null>(null);

  const fetchStats = useCallback(async () => {
    const now = Date.now();
    const timeSinceLastFetch = now - lastFetchTime.current;

    // Check if we have cached data that's still valid
    if (cacheData.current && timeSinceLastFetch < cacheTTL) {
      setData(cacheData.current);
      setIsCached(true);
      return;
    }

    setLoading(true);
    setError(null);
    setIsCached(false);

    try {
      const response = await superadminApi.getAggregateStats();
      setData(response);
      cacheData.current = response;
      lastFetchTime.current = now;
    } catch (err) {
      setError(
        err instanceof Error
          ? err
          : new Error("Failed to fetch aggregate statistics")
      );
    } finally {
      setLoading(false);
    }
  }, [cacheTTL]);

  useEffect(() => {
    if (autoFetch) {
      fetchStats();
    }
  }, [autoFetch, fetchStats]);

  return {
    data,
    loading,
    error,
    refetch: fetchStats,
    isCached,
  };
};
