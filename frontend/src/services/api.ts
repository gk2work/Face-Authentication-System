import axios, { AxiosError } from "axios";
import type { AxiosInstance, AxiosRequestConfig, AxiosResponse } from "axios";
import { config } from "../config";

// Token storage keys
const ACCESS_TOKEN_KEY = "access_token";
const REFRESH_TOKEN_KEY = "refresh_token";

// Create axios instance with default config
const apiClient: AxiosInstance = axios.create({
  baseURL: config.apiBaseUrl,
  timeout: 30000,
  headers: {
    "Content-Type": "application/json",
  },
});

// Token management utilities
export const tokenManager = {
  getAccessToken: (): string | null => {
    return localStorage.getItem(ACCESS_TOKEN_KEY);
  },

  setAccessToken: (token: string): void => {
    localStorage.setItem(ACCESS_TOKEN_KEY, token);
  },

  getRefreshToken: (): string | null => {
    return localStorage.getItem(REFRESH_TOKEN_KEY);
  },

  setRefreshToken: (token: string): void => {
    localStorage.setItem(REFRESH_TOKEN_KEY, token);
  },

  clearTokens: (): void => {
    localStorage.removeItem(ACCESS_TOKEN_KEY);
    localStorage.removeItem(REFRESH_TOKEN_KEY);
  },

  setTokens: (accessToken: string, refreshToken?: string): void => {
    tokenManager.setAccessToken(accessToken);
    if (refreshToken) {
      tokenManager.setRefreshToken(refreshToken);
    }
  },
};

// Request interceptor - Add auth token to requests
apiClient.interceptors.request.use(
  (config) => {
    const token = tokenManager.getAccessToken();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Track if we're currently refreshing the token
let isRefreshing = false;
let failedQueue: Array<{
  resolve: (value?: unknown) => void;
  reject: (reason?: unknown) => void;
}> = [];

const processQueue = (error: Error | null, token: string | null = null) => {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token);
    }
  });

  failedQueue = [];
};

// Response interceptor - Handle token refresh
apiClient.interceptors.response.use(
  (response: AxiosResponse) => {
    return response;
  },
  async (error: AxiosError) => {
    const originalRequest = error.config as AxiosRequestConfig & {
      _retry?: boolean;
    };

    // If error is 401 and we haven't retried yet
    if (error.response?.status === 401 && !originalRequest._retry) {
      if (isRefreshing) {
        // If already refreshing, queue this request
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        })
          .then((token) => {
            if (originalRequest.headers) {
              originalRequest.headers.Authorization = `Bearer ${token}`;
            }
            return apiClient(originalRequest);
          })
          .catch((err) => {
            return Promise.reject(err);
          });
      }

      originalRequest._retry = true;
      isRefreshing = true;

      const refreshToken = tokenManager.getRefreshToken();

      if (!refreshToken) {
        // No refresh token, clear tokens and redirect to login
        tokenManager.clearTokens();
        window.location.href = "/login";
        return Promise.reject(error);
      }

      try {
        // Attempt to refresh the token
        const response = await axios.post(
          `${config.apiBaseUrl}/api/v1/auth/refresh`,
          {
            refresh_token: refreshToken,
          }
        );

        const { access_token, refresh_token: newRefreshToken } = response.data;

        tokenManager.setTokens(access_token, newRefreshToken);

        // Update the authorization header
        if (originalRequest.headers) {
          originalRequest.headers.Authorization = `Bearer ${access_token}`;
        }

        processQueue(null, access_token);
        isRefreshing = false;

        // Retry the original request
        return apiClient(originalRequest);
      } catch (refreshError) {
        processQueue(refreshError as Error, null);
        tokenManager.clearTokens();
        window.location.href = "/login";
        isRefreshing = false;
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);

// Retry logic for failed requests
const retryRequest = async (
  error: AxiosError,
  retries: number = 3,
  delay: number = 1000
): Promise<AxiosResponse> => {
  const config = error.config;

  if (!config || retries === 0) {
    return Promise.reject(error);
  }

  // Don't retry on 4xx errors (except 429 - rate limit)
  if (
    error.response &&
    error.response.status >= 400 &&
    error.response.status < 500 &&
    error.response.status !== 429
  ) {
    return Promise.reject(error);
  }

  // Wait before retrying
  await new Promise((resolve) => setTimeout(resolve, delay));

  // Exponential backoff
  return apiClient(config).catch((err) => {
    return retryRequest(err, retries - 1, delay * 2);
  });
};

// API client wrapper with retry logic
export const api = {
  get: async <T = any>(
    url: string,
    config?: AxiosRequestConfig
  ): Promise<T> => {
    try {
      const response = await apiClient.get<T>(url, config);
      return response.data;
    } catch (error) {
      const retried = await retryRequest(error as AxiosError);
      return retried.data;
    }
  },

  post: async <T = any>(
    url: string,
    data?: any,
    config?: AxiosRequestConfig
  ): Promise<T> => {
    try {
      const response = await apiClient.post<T>(url, data, config);
      return response.data;
    } catch (error) {
      const retried = await retryRequest(error as AxiosError);
      return retried.data;
    }
  },

  put: async <T = any>(
    url: string,
    data?: any,
    config?: AxiosRequestConfig
  ): Promise<T> => {
    try {
      const response = await apiClient.put<T>(url, data, config);
      return response.data;
    } catch (error) {
      const retried = await retryRequest(error as AxiosError);
      return retried.data;
    }
  },

  patch: async <T = any>(
    url: string,
    data?: any,
    config?: AxiosRequestConfig
  ): Promise<T> => {
    try {
      const response = await apiClient.patch<T>(url, data, config);
      return response.data;
    } catch (error) {
      const retried = await retryRequest(error as AxiosError);
      return retried.data;
    }
  },

  delete: async <T = any>(
    url: string,
    config?: AxiosRequestConfig
  ): Promise<T> => {
    try {
      const response = await apiClient.delete<T>(url, config);
      return response.data;
    } catch (error) {
      const retried = await retryRequest(error as AxiosError);
      return retried.data;
    }
  },
};

// Export the raw axios instance for special cases
export { apiClient };

export default api;
