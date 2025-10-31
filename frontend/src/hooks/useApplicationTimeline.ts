import { useState, useEffect } from "react";
import { api } from "@/services";
import type { ApplicationTimeline } from "@/types";

export const useApplicationTimeline = (days: number = 30) => {
  const [data, setData] = useState<ApplicationTimeline[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchTimeline = async () => {
    try {
      setLoading(true);
      setError(null);
      const timeline = await api.get<ApplicationTimeline[]>(
        `/api/v1/dashboard/timeline?days=${days}`
      );
      setData(timeline);
    } catch (err: any) {
      setError(err.message || "Failed to fetch timeline data");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTimeline();
  }, [days]);

  return { data, loading, error, refetch: fetchTimeline };
};
