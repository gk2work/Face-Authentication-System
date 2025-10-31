export interface Application {
  application_id: string;
  identity_id?: string;
  status: "pending" | "processing" | "completed" | "failed";
  created_at: string;
  updated_at?: string;
  photograph_path?: string;
  metadata?: string;
  processing_result?: ProcessingResult;
}

export interface ProcessingResult {
  is_duplicate: boolean;
  confidence_score: number;
  matched_identity_id?: string;
  face_detected: boolean;
  quality_score?: number;
  matches?: MatchResult[];
}

export interface MatchResult {
  identity_id: string;
  similarity_score: number;
  confidence: number;
  photograph_path?: string;
}

export interface ApplicationFilters {
  status?: string;
  start_date?: string;
  end_date?: string;
  search?: string;
}
