import { api, tokenManager } from "./api";
import type { LoginRequest, LoginResponse, User } from "@/types";

class AuthService {
  private currentUser: User | null = null;

  /**
   * Login with username and password
   */
  async login(credentials: LoginRequest): Promise<LoginResponse> {
    try {
      const response = await api.post<LoginResponse>(
        "/api/v1/auth/login",
        credentials
      );

      // Store tokens
      tokenManager.setTokens(response.access_token);

      // Fetch current user
      await this.fetchCurrentUser();

      return response;
    } catch (error) {
      throw error;
    }
  }

  /**
   * Logout and clear tokens
   */
  logout(): void {
    tokenManager.clearTokens();
    this.currentUser = null;

    // Redirect to login page
    window.location.href = "/login";
  }

  /**
   * Get current authenticated user
   */
  getCurrentUser(): User | null {
    return this.currentUser;
  }

  /**
   * Check if user is authenticated
   */
  isAuthenticated(): boolean {
    const token = tokenManager.getAccessToken();

    if (!token) {
      return false;
    }

    // Check if token is expired
    try {
      const payload = this.parseJwt(token);
      const currentTime = Date.now() / 1000;

      return payload.exp > currentTime;
    } catch (error) {
      return false;
    }
  }

  /**
   * Parse JWT token to get payload
   */
  private parseJwt(token: string): any {
    try {
      const base64Url = token.split(".")[1];
      const base64 = base64Url.replace(/-/g, "+").replace(/_/g, "/");
      const jsonPayload = decodeURIComponent(
        atob(base64)
          .split("")
          .map((c) => "%" + ("00" + c.charCodeAt(0).toString(16)).slice(-2))
          .join("")
      );

      return JSON.parse(jsonPayload);
    } catch (error) {
      throw new Error("Invalid token");
    }
  }

  /**
   * Get token expiration time
   */
  getTokenExpiration(): Date | null {
    const token = tokenManager.getAccessToken();

    if (!token) {
      return null;
    }

    try {
      const payload = this.parseJwt(token);
      return new Date(payload.exp * 1000);
    } catch (error) {
      return null;
    }
  }

  /**
   * Check if token will expire soon (within 5 minutes)
   */
  isTokenExpiringSoon(): boolean {
    const expiration = this.getTokenExpiration();

    if (!expiration) {
      return true;
    }

    const fiveMinutesFromNow = new Date(Date.now() + 5 * 60 * 1000);
    return expiration < fiveMinutesFromNow;
  }

  /**
   * Fetch current user profile from API
   */
  async fetchCurrentUser(): Promise<User> {
    try {
      const user = await api.get<User>("/api/v1/auth/me");
      this.currentUser = user;
      return user;
    } catch (error) {
      throw error;
    }
  }

  /**
   * Refresh authentication token
   */
  async refreshToken(): Promise<void> {
    const refreshToken = tokenManager.getRefreshToken();

    if (!refreshToken) {
      throw new Error("No refresh token available");
    }

    try {
      const response = await api.post<{
        access_token: string;
        refresh_token?: string;
      }>("/api/v1/auth/refresh", { refresh_token: refreshToken });

      tokenManager.setTokens(response.access_token, response.refresh_token);
    } catch (error) {
      // If refresh fails, logout user
      this.logout();
      throw error;
    }
  }
}

// Export singleton instance
export const authService = new AuthService();
