export interface DashboardStatistics {
  total_applications: number;
  total_identities: number;
  total_duplicates: number;
  pending_applications: number;
  applications_trend?: number;
  identities_trend?: number;
  duplicates_trend?: number;
}

export interface SystemHealth {
  database_status: "healthy" | "degraded" | "down";
  face_recognition_service: "healthy" | "degraded" | "down";
  storage_service: "healthy" | "degraded" | "down";
  last_check: string;
}

export interface RecentApplication {
  application_id: string;
  status: "pending" | "processing" | "completed" | "failed";
  created_at: string;
  identity_id?: string;
  is_duplicate?: boolean;
}

export interface ApplicationTimeline {
  date: string;
  count: number;
}
