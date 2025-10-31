import { useState, useEffect } from "react";
import { api } from "@/services";
import type { RecentApplication } from "@/types";

export const useRecentApplications = (limit: number = 10) => {
  const [applications, setApplications] = useState<RecentApplication[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchApplications = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.get<RecentApplication[]>(
        `/api/v1/dashboard/recent-applications?limit=${limit}`
      );
      setApplications(data);
    } catch (err: any) {
      setError(err.message || "Failed to fetch recent applications");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchApplications();
  }, [limit]);

  return { applications, loading, error, refetch: fetchApplications };
};
