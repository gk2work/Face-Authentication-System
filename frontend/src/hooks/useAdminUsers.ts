/**
 * Custom hook for fetching and managing admin users list
 */

import { useState, useEffect, useCallback } from "react";
import { superadminApi } from "../services/api";
import type { PaginatedAdminUsers, AdminUserFilters } from "../types";

interface UseAdminUsersOptions {
  initialPage?: number;
  initialPageSize?: number;
  initialFilters?: AdminUserFilters;
  autoFetch?: boolean;
}

interface UseAdminUsersReturn {
  data: PaginatedAdminUsers | null;
  loading: boolean;
  error: Error | null;
  page: number;
  pageSize: number;
  filters: AdminUserFilters;
  setPage: (page: number) => void;
  setPageSize: (pageSize: number) => void;
  setFilters: (filters: AdminUserFilters) => void;
  refetch: () => Promise<void>;
}

export const useAdminUsers = (
  options: UseAdminUsersOptions = {}
): UseAdminUsersReturn => {
  const {
    initialPage = 1,
    initialPageSize = 50,
    initialFilters = {},
    autoFetch = true,
  } = options;

  const [data, setData] = useState<PaginatedAdminUsers | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<Error | null>(null);
  const [page, setPage] = useState<number>(initialPage);
  const [pageSize, setPageSize] = useState<number>(initialPageSize);
  const [filters, setFilters] = useState<AdminUserFilters>(initialFilters);

  const fetchAdminUsers = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await superadminApi.getAdminUsers(
        page,
        pageSize,
        filters
      );
      setData(response);
    } catch (err) {
      setError(
        err instanceof Error ? err : new Error("Failed to fetch admin users")
      );
    } finally {
      setLoading(false);
    }
  }, [page, pageSize, filters]);

  useEffect(() => {
    if (autoFetch) {
      fetchAdminUsers();
    }
  }, [autoFetch, fetchAdminUsers]);

  return {
    data,
    loading,
    error,
    page,
    pageSize,
    filters,
    setPage,
    setPageSize,
    setFilters,
    refetch: fetchAdminUsers,
  };
};
