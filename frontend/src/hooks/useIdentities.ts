import { useState, useEffect } from "react";
import { api } from "@/services";
import type { Identity, IdentityFilters, PaginatedResponse } from "@/types";

interface UseIdentitiesOptions {
  page?: number;
  pageSize?: number;
  filters?: IdentityFilters;
}

export const useIdentities = (options: UseIdentitiesOptions = {}) => {
  const { page = 1, pageSize = 12, filters = {} } = options;
  const [identities, setIdentities] = useState<Identity[]>([]);
  const [total, setTotal] = useState(0);
  const [totalPages, setTotalPages] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchIdentities = async () => {
    try {
      setLoading(true);
      setError(null);

      const params = new URLSearchParams({
        page: page.toString(),
        page_size: pageSize.toString(),
      });

      if (filters.status) {
        params.append("status", filters.status);
      }
      if (filters.search) {
        params.append("search", filters.search);
      }

      const response = await api.get<PaginatedResponse<Identity>>(
        `/api/v1/identities?${params.toString()}`
      );

      setIdentities(response.items);
      setTotal(response.total);
      setTotalPages(response.total_pages);
    } catch (err: any) {
      setError(err.message || "Failed to fetch identities");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchIdentities();
  }, [page, pageSize, JSON.stringify(filters)]);

  return {
    identities,
    total,
    totalPages,
    loading,
    error,
    refetch: fetchIdentities,
  };
};
