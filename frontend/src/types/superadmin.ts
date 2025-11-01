/**
 * Superadmin management types
 */

export interface AdminUser {
  username: string;
  email: string;
  full_name: string;
  roles: string[];
  is_active: boolean;
  created_at: string;
  updated_at: string;
  last_login: string | null;
  application_count: number;
}

export interface AdminUserFilters {
  search?: string;
  role?: string;
  is_active?: boolean;
  created_after?: string;
  created_before?: string;
  sort_by?: string;
  sort_order?: "asc" | "desc";
}

export interface AdminUserStats {
  username: string;
  total_applications: number;
  applications_by_status: Record<string, number>;
  total_overrides: number;
  overrides_by_decision: Record<string, number>;
  activity_timeline: AdminActivityData[];
  last_30_days_total: number;
}

export interface AdminActivityData {
  date: string;
  applications_processed: number;
  verified: number;
  duplicate: number;
  rejected: number;
}

export interface AggregateAdminStats {
  total_admin_users: number;
  active_admin_users: number;
  inactive_admin_users: number;
  users_by_role: Record<string, number>;
  total_applications_last_30_days: number;
  most_active_users: MostActiveUser[];
}

export interface MostActiveUser {
  username: string;
  full_name: string;
  application_count: number;
}

export interface PaginatedAdminUsers {
  users: AdminUser[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface CreateAdminUserRequest {
  username: string;
  email: string;
  password: string;
  full_name: string;
  roles: string[];
}

export interface UpdateAdminUserRequest {
  email?: string;
  full_name?: string;
  roles?: string[];
  is_active?: boolean;
}

export interface DeactivateUserResponse {
  success: boolean;
  message: string;
}
