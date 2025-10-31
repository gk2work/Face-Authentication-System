import { useState, useEffect } from "react";
import { api } from "@/services";
import type {
  Application,
  ApplicationFilters,
  PaginatedResponse,
} from "@/types";

interface UseApplicationsOptions {
  page?: number;
  pageSize?: number;
  filters?: ApplicationFilters;
}

export const useApplications = (options: UseApplicationsOptions = {}) => {
  const { page = 1, pageSize = 10, filters = {} } = options;
  const [applications, setApplications] = useState<Application[]>([]);
  const [total, setTotal] = useState(0);
  const [totalPages, setTotalPages] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchApplications = async () => {
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
      if (filters.start_date) {
        params.append("start_date", filters.start_date);
      }
      if (filters.end_date) {
        params.append("end_date", filters.end_date);
      }
      if (filters.search) {
        params.append("search", filters.search);
      }

      const response = await api.get<PaginatedResponse<Application>>(
        `/api/v1/applications?${params.toString()}`
      );

      setApplications(response.items);
      setTotal(response.total);
      setTotalPages(response.total_pages);
    } catch (err: any) {
      setError(err.message || "Failed to fetch applications");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchApplications();
  }, [page, pageSize, JSON.stringify(filters)]);

  return {
    applications,
    total,
    totalPages,
    loading,
    error,
    refetch: fetchApplications,
  };
};
