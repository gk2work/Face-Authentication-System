export interface Identity {
  unique_id: string;
  status: "active" | "flagged" | "merged";
  created_at: string;
  updated_at?: string;
  photographs: string[];
  application_count: number;
  metadata?: Record<string, any>;
}

export interface IdentityFilters {
  status?: string;
  search?: string;
}

export interface IdentityApplication {
  application_id: string;
  status: string;
  created_at: string;
  is_duplicate: boolean;
  confidence_score?: number;
}
