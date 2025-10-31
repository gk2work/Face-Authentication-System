// Application configuration
export const config = {
  apiBaseUrl: import.meta.env.VITE_API_BASE_URL || "http://localhost:8000",
  wsBaseUrl: import.meta.env.VITE_WS_BASE_URL || "ws://localhost:8000",
  isDevelopment: import.meta.env.DEV,
  isProduction: import.meta.env.PROD,
};
