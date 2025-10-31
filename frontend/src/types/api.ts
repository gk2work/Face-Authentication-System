// Common API response types

export interface ApiError {
  message: string;
  detail?: string;
  status?: number;
}

export interface ApiResponse<T> {
  data: T;
  message?: string;
  success: boolean;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface AuthTokens {
  access_token: string;
  refresh_token?: string;
  token_type: string;
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user?: User;
}

export interface User {
  user_id?: string;
  username: string;
  email: string;
  full_name: string;
  roles: Array<"admin" | "reviewer" | "auditor" | "operator">;
  is_active: boolean;
  created_at: string;
  last_login?: string;
  // Legacy field for backward compatibility
  role?: "admin" | "operator" | "viewer";
}
