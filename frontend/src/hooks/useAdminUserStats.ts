/**
 * Custom hook for fetching admin user statistics
 */

import { useState, useEffect, useCallback } from "react";
import { superadminApi } from "../services/api";
import type { AdminUserStats } from "../types";

interface UseAdminUserStatsOptions {
  username: string;
  autoFetch?: boolean;
}

interface UseAdminUserStatsReturn {
  data: AdminUserStats | null;
  loading: boolean;
  error: Error | null;
  refetch: () => Promise<void>;
}

export const useAdminUserStats = (
  options: UseAdminUserStatsOptions
): UseAdminUserStatsReturn => {
  const { username, autoFetch = true } = options;

  const [data, setData] = useState<AdminUserStats | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<Error | null>(null);

  const fetchStats = useCallback(async () => {
    if (!username) {
      setError(new Error("Username is required"));
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await superadminApi.getAdminUserStats(username);
      setData(response);
    } catch (err) {
      setError(
        err instanceof Error
          ? err
          : new Error("Failed to fetch user statistics")
      );
    } finally {
      setLoading(false);
    }
  }, [username]);

  useEffect(() => {
    if (autoFetch && username) {
      fetchStats();
    }
  }, [autoFetch, username, fetchStats]);

  return {
    data,
    loading,
    error,
    refetch: fetchStats,
  };
};
