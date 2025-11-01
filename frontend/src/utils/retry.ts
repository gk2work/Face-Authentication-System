/**
 * Retry utility for failed async operations
 */

export interface RetryOptions {
  maxAttempts?: number;
  initialDelay?: number;
  maxDelay?: number;
  exponentialBase?: number;
  shouldRetry?: (error: any) => boolean;
  onRetry?: (attempt: number, error: any) => void;
}

const defaultOptions: Required<RetryOptions> = {
  maxAttempts: 3,
  initialDelay: 1000,
  maxDelay: 10000,
  exponentialBase: 2,
  shouldRetry: (error: any) => {
    // Retry on network errors or 5xx server errors
    if (!error.response) return true; // Network error
    const status = error.response?.status;
    return status >= 500 && status < 600;
  },
  onRetry: () => {},
};

/**
 * Retry an async function with exponential backoff
 */
export async function retryAsync<T>(
  fn: () => Promise<T>,
  options: RetryOptions = {}
): Promise<T> {
  const opts = { ...defaultOptions, ...options };
  let lastError: any;

  for (let attempt = 1; attempt <= opts.maxAttempts; attempt++) {
    try {
      return await fn();
    } catch (error) {
      lastError = error;

      // Don't retry if this is the last attempt
      if (attempt === opts.maxAttempts) {
        break;
      }

      // Check if we should retry this error
      if (!opts.shouldRetry(error)) {
        throw error;
      }

      // Calculate delay with exponential backoff
      const delay = Math.min(
        opts.initialDelay * Math.pow(opts.exponentialBase, attempt - 1),
        opts.maxDelay
      );

      // Call retry callback
      opts.onRetry(attempt, error);

      // Wait before retrying
      await sleep(delay);
    }
  }

  throw lastError;
}

/**
 * Sleep for a specified duration
 */
function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

/**
 * Create a retryable version of an async function
 */
export function withRetry<T extends (...args: any[]) => Promise<any>>(
  fn: T,
  options: RetryOptions = {}
): T {
  return ((...args: any[]) => {
    return retryAsync(() => fn(...args), options);
  }) as T;
}
