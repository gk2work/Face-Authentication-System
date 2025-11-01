/**
 * Custom hook for fetching admin activity timeline data
 */

import { useState, useEffect, useCallback } from "react";
import { superadminApi } from "../services/api";
import type { AdminActivityData } from "../types";

interface UseAdminActivityOptions {
  username?: string;
  startDate?: string;
  endDate?: string;
  autoFetch?: boolean;
}

interface UseAdminActivityReturn {
  data: AdminActivityData[] | null;
  loading: boolean;
  error: Error | null;
  refetch: () => Promise<void>;
}

export const useAdminActivity = (
  options: UseAdminActivityOptions = {}
): UseAdminActivityReturn => {
  const { username, startDate, endDate, autoFetch = true } = options;

  const [data, setData] = useState<AdminActivityData[] | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<Error | null>(null);

  const fetchActivity = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      if (username) {
        // Fetch activity for specific user
        const response = await superadminApi.getAdminUserStats(username);
        setData(response.activity_timeline);
      } else {
        // If no username provided, we can't fetch activity
        // This could be extended to fetch aggregate activity if needed
        setData([]);
      }
    } catch (err) {
      setError(
        err instanceof Error ? err : new Error("Failed to fetch activity data")
      );
    } finally {
      setLoading(false);
    }
  }, [username, startDate, endDate]);

  useEffect(() => {
    if (autoFetch) {
      fetchActivity();
    }
  }, [autoFetch, fetchActivity]);

  return {
    data,
    loading,
    error,
    refetch: fetchActivity,
  };
};
