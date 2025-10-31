"""Simple metrics collection service for monitoring system performance"""

import time
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict, deque
from threading import Lock
from enum import Enum

from app.core.logging import logger


class MetricType(str, Enum):
    """Types of metrics tracked"""
    APPLICATION_SUBMISSION = "application_submission"
    FACE_RECOGNITION = "face_recognition"
    DUPLICATE_DETECTION = "duplicate_detection"
    IDENTITY_ISSUANCE = "identity_issuance"
    FAISS_SEARCH = "faiss_search"
    API_REQUEST = "api_request"
    ERROR = "error"


class MetricsService:
    """Service for collecting and tracking system metrics"""
    
    def __init__(self, max_history: int = 1000):
        """
        Initialize metrics service
        
        Args:
            max_history: Maximum number of metric entries to keep in memory
        """
        self.max_history = max_history
        self.lock = Lock()
        
        # Counters for different metric types
        self.counters: Dict[str, int] = defaultdict(int)
        
        # Latency tracking (deque for efficient append/pop)
        self.latencies: Dict[str, deque] = defaultdict(lambda: deque(maxlen=max_history))
        
        # Error tracking
        self.errors: Dict[str, int] = defaultdict(int)
        self.error_details: deque = deque(maxlen=100)
        
        # Processing rate tracking (timestamp, metric_type)
        self.events: deque = deque(maxlen=max_history)
        
        # Start time for uptime calculation
        self.start_time = datetime.utcnow()
        
        logger.info("Metrics service initialized")
    
    def record_count(self, metric_type: MetricType, count: int = 1):
        """
        Record a counter metric
        
        Args:
            metric_type: Type of metric
            count: Count to add (default 1)
        """
        with self.lock:
            self.counters[metric_type] += count
            self.events.append((datetime.utcnow(), metric_type))
    
    def record_latency(self, metric_type: MetricType, latency_ms: float, metadata: Optional[Dict[str, Any]] = None):
        """
        Record a latency metric
        
        Args:
            metric_type: Type of metric
            latency_ms: Latency in milliseconds
            metadata: Optional metadata about the operation
        """
        with self.lock:
            self.latencies[metric_type].append({
                "timestamp": datetime.utcnow(),
                "latency_ms": latency_ms,
                "metadata": metadata or {}
            })
            self.counters[metric_type] += 1
            self.events.append((datetime.utcnow(), metric_type))
    
    def record_error(self, metric_type: MetricType, error_message: str, metadata: Optional[Dict[str, Any]] = None):
        """
        Record an error metric
        
        Args:
            metric_type: Type of metric
            error_message: Error message
            metadata: Optional metadata about the error
        """
        with self.lock:
            error_key = f"{metric_type}_error"
            self.errors[error_key] += 1
            self.error_details.append({
                "timestamp": datetime.utcnow(),
                "metric_type": metric_type,
                "error_message": error_message,
                "metadata": metadata or {}
            })
            self.events.append((datetime.utcnow(), MetricType.ERROR))
    
    def get_counter(self, metric_type: MetricType) -> int:
        """Get current counter value"""
        with self.lock:
            return self.counters.get(metric_type, 0)
    
    def get_latency_stats(self, metric_type: MetricType) -> Dict[str, Any]:
        """
        Get latency statistics for a metric type
        
        Returns:
            Dictionary with min, max, avg, p50, p95, p99 latencies
        """
        with self.lock:
            latencies = self.latencies.get(metric_type, deque())
            
            if not latencies:
                return {
                    "count": 0,
                    "min_ms": 0,
                    "max_ms": 0,
                    "avg_ms": 0,
                    "p50_ms": 0,
                    "p95_ms": 0,
                    "p99_ms": 0
                }
            
            # Extract latency values
            values = sorted([entry["latency_ms"] for entry in latencies])
            count = len(values)
            
            # Calculate percentiles
            def percentile(data: List[float], p: float) -> float:
                if not data:
                    return 0
                k = (len(data) - 1) * p
                f = int(k)
                c = f + 1
                if c >= len(data):
                    return data[-1]
                return data[f] + (k - f) * (data[c] - data[f])
            
            return {
                "count": count,
                "min_ms": min(values),
                "max_ms": max(values),
                "avg_ms": sum(values) / count,
                "p50_ms": percentile(values, 0.50),
                "p95_ms": percentile(values, 0.95),
                "p99_ms": percentile(values, 0.99)
            }
    
    def get_processing_rate(self, metric_type: Optional[MetricType] = None, window_seconds: int = 60) -> float:
        """
        Get processing rate (events per second)
        
        Args:
            metric_type: Optional metric type to filter by
            window_seconds: Time window in seconds (default 60)
            
        Returns:
            Events per second
        """
        with self.lock:
            cutoff_time = datetime.utcnow() - timedelta(seconds=window_seconds)
            
            # Filter events by time window and optionally by type
            recent_events = [
                event for event in self.events
                if event[0] >= cutoff_time and (metric_type is None or event[1] == metric_type)
            ]
            
            if not recent_events:
                return 0.0
            
            # Calculate rate
            return len(recent_events) / window_seconds
    
    def get_error_rate(self, window_seconds: int = 60) -> float:
        """
        Get error rate (errors per total events)
        
        Args:
            window_seconds: Time window in seconds (default 60)
            
        Returns:
            Error rate as percentage (0-100)
        """
        with self.lock:
            cutoff_time = datetime.utcnow() - timedelta(seconds=window_seconds)
            
            # Count recent events and errors
            recent_events = [event for event in self.events if event[0] >= cutoff_time]
            recent_errors = [event for event in recent_events if event[1] == MetricType.ERROR]
            
            if not recent_events:
                return 0.0
            
            return (len(recent_errors) / len(recent_events)) * 100
    
    def get_recent_errors(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent error details
        
        Args:
            limit: Maximum number of errors to return
            
        Returns:
            List of error details
        """
        with self.lock:
            errors = list(self.error_details)[-limit:]
            return [
                {
                    "timestamp": error["timestamp"].isoformat(),
                    "metric_type": error["metric_type"],
                    "error_message": error["error_message"],
                    "metadata": error["metadata"]
                }
                for error in errors
            ]
    
    def get_uptime_seconds(self) -> float:
        """Get system uptime in seconds"""
        return (datetime.utcnow() - self.start_time).total_seconds()
    
    def get_all_metrics(self) -> Dict[str, Any]:
        """
        Get all metrics summary
        
        Returns:
            Dictionary with all metrics
        """
        with self.lock:
            # Get latency stats for each metric type
            latency_stats = {}
            for metric_type in MetricType:
                if metric_type != MetricType.ERROR:
                    stats = self.get_latency_stats(metric_type)
                    if stats["count"] > 0:
                        latency_stats[metric_type] = stats
            
            # Get processing rates
            processing_rates = {}
            for metric_type in MetricType:
                if metric_type != MetricType.ERROR:
                    rate = self.get_processing_rate(metric_type, window_seconds=60)
                    if rate > 0:
                        processing_rates[metric_type] = round(rate, 2)
            
            return {
                "uptime_seconds": round(self.get_uptime_seconds(), 2),
                "counters": dict(self.counters),
                "latency_stats": latency_stats,
                "processing_rates": processing_rates,
                "error_rate_percent": round(self.get_error_rate(), 2),
                "total_errors": sum(self.errors.values()),
                "recent_errors": self.get_recent_errors(5)
            }
    
    def reset_metrics(self):
        """Reset all metrics (useful for testing)"""
        with self.lock:
            self.counters.clear()
            self.latencies.clear()
            self.errors.clear()
            self.error_details.clear()
            self.events.clear()
            self.start_time = datetime.utcnow()
            logger.info("Metrics reset")
    
    def log_metrics_summary(self):
        """Log current metrics summary to console"""
        metrics = self.get_all_metrics()
        
        logger.info("=== Metrics Summary ===")
        logger.info(f"Uptime: {metrics['uptime_seconds']}s")
        logger.info(f"Total Events: {sum(metrics['counters'].values())}")
        logger.info(f"Error Rate: {metrics['error_rate_percent']}%")
        logger.info(f"Total Errors: {metrics['total_errors']}")
        
        if metrics['processing_rates']:
            logger.info("Processing Rates (events/sec):")
            for metric_type, rate in metrics['processing_rates'].items():
                logger.info(f"  {metric_type}: {rate}")
        
        if metrics['latency_stats']:
            logger.info("Latency Stats:")
            for metric_type, stats in metrics['latency_stats'].items():
                logger.info(f"  {metric_type}: avg={stats['avg_ms']:.2f}ms, p95={stats['p95_ms']:.2f}ms")


# Global metrics service instance
metrics_service = MetricsService()
