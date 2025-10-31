import { useState, useEffect } from "react";
import { api } from "@/services";
import type { Identity, IdentityApplication } from "@/types";

export const useIdentity = (id: string | undefined) => {
  const [identity, setIdentity] = useState<Identity | null>(null);
  const [applications, setApplications] = useState<IdentityApplication[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchIdentity = async () => {
    if (!id) return;

    try {
      setLoading(true);
      setError(null);

      const [identityData, applicationsData] = await Promise.all([
        api.get<Identity>(`/api/v1/identities/${id}`),
        api.get<IdentityApplication[]>(`/api/v1/identities/${id}/applications`),
      ]);

      setIdentity(identityData);
      setApplications(applicationsData);
    } catch (err: any) {
      setError(err.message || "Failed to fetch identity details");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchIdentity();
  }, [id]);

  return {
    identity,
    applications,
    loading,
    error,
    refetch: fetchIdentity,
  };
};
