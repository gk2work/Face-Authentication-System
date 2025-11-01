/**
 * Request queue for handling offline requests
 */

interface QueuedRequest {
  id: string;
  url: string;
  method: string;
  data?: any;
  timestamp: number;
}

class RequestQueue {
  private queue: QueuedRequest[] = [];
  private readonly STORAGE_KEY = "offline_request_queue";
  private readonly MAX_QUEUE_SIZE = 50;

  constructor() {
    this.loadQueue();
  }

  /**
   * Add a request to the queue
   */
  add(url: string, method: string, data?: any): void {
    const request: QueuedRequest = {
      id: this.generateId(),
      url,
      method,
      data,
      timestamp: Date.now(),
    };

    this.queue.push(request);

    // Limit queue size
    if (this.queue.length > this.MAX_QUEUE_SIZE) {
      this.queue.shift();
    }

    this.saveQueue();
  }

  /**
   * Get all queued requests
   */
  getAll(): QueuedRequest[] {
    return [...this.queue];
  }

  /**
   * Remove a request from the queue
   */
  remove(id: string): void {
    this.queue = this.queue.filter((req) => req.id !== id);
    this.saveQueue();
  }

  /**
   * Clear all queued requests
   */
  clear(): void {
    this.queue = [];
    this.saveQueue();
  }

  /**
   * Get queue size
   */
  size(): number {
    return this.queue.length;
  }

  /**
   * Process all queued requests
   */
  async processQueue(
    processor: (request: QueuedRequest) => Promise<void>
  ): Promise<void> {
    const requests = this.getAll();

    for (const request of requests) {
      try {
        await processor(request);
        this.remove(request.id);
      } catch (error) {
        console.error("Failed to process queued request:", error);
        // Keep the request in queue for next attempt
      }
    }
  }

  /**
   * Load queue from localStorage
   */
  private loadQueue(): void {
    try {
      const stored = localStorage.getItem(this.STORAGE_KEY);
      if (stored) {
        this.queue = JSON.parse(stored);
      }
    } catch (error) {
      console.error("Failed to load request queue:", error);
      this.queue = [];
    }
  }

  /**
   * Save queue to localStorage
   */
  private saveQueue(): void {
    try {
      localStorage.setItem(this.STORAGE_KEY, JSON.stringify(this.queue));
    } catch (error) {
      console.error("Failed to save request queue:", error);
    }
  }

  /**
   * Generate unique ID
   */
  private generateId(): string {
    return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  }
}

export const requestQueue = new RequestQueue();
