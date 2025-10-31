"""Performance monitoring service for tracking system metrics"""

import time
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from collections import deque
from dataclasses import dataclass, field
from enum import Enum

from app.core.logging import logger


class MetricType(str, Enum):
    """Types of metrics to track"""
    SEARCH_LATENCY = "search_latency"
    EMBEDDING_GENERATION = "embedding_generation"
    DUPLICATE_DETECTION = "duplicate_detection"
    DATABASE_QUERY = "database_query"
    VECTOR_INDEX_QUERY = "vector_index_query"


@dataclass
class PerformanceMetric:
    """Performance metric data"""
    metric_type: MetricType
    duration_ms: float
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


class PerformanceMonitor:
    """Service for monitoring and tracking performance metrics"""
    
    def __init__(self):
        self.metrics_history: Dict[MetricType, deque] = {
            metric_type: deque(maxlen=1000)  # Keep last 1000 metrics per type
            for metric_type in MetricType
        }
        
        self.alert_thresholds = {
            MetricType.SEARCH_LATENCY: 5000,  # 5 seconds
            MetricType.EMBEDDING_GENERATION: 3000,  # 3 seconds
            MetricType.DUPLICATE_DETECTION: 5000,  # 5 seconds
            MetricType.DATABASE_QUERY: 2000,  # 2 seconds
            MetricType.VECTOR_INDEX_QUERY: 5000,  # 5 seconds
        }
        
        self.alert_count = 0
        self.total_alerts = 0
        
        logger.info("Performance monitor initialized")
    
    def record_metric(self, metric_type: MetricType, duration_ms: float, 
                     metadata: Optional[Dict[str, Any]] = None):
        """
        Record a performance metric
        
        Args:
            metric_type: Type of metric
            duration_ms: Duration in milliseconds
            metadata: Optional metadata about the operation
        """
        metric = PerformanceMetric(
            metric_type=metric_type,
            duration_ms=duration_ms,
            metadata=metadata or {}
        )
        
        self.metrics_history[metric_type].append(metric)
        
        # Check if metric exceeds threshold
        threshold = self.alert_thresholds.get(metric_type)
        if threshold and duration_ms > threshold:
            self._trigger_alert(metric_type, duration_ms, threshold, metadata)
        
        logger.debug(f"Recorded metric: {metric_type} = {duration_ms:.2f}ms")
    
    def _trigger_alert(self, metric_type: MetricType, duration_ms: float, 
                      threshold: float, metadata: Optional[Dict[str, Any]]):
        """
        Trigger alert for slow operation
        
        Args:
            metric_type: Type of metric
            duration_ms: Actual duration
            threshold: Threshold that was exceeded
            metadata: Operation metadata
        """
        self.alert_count += 1
        self.total_alerts += 1
        
        logger.warning(
            f"PERFORMANCE ALERT: {metric_type} took {duration_ms:.2f}ms "
            f"(threshold: {threshold}ms). Metadata: {metadata}"
        )
    
    def get_statistics(self, metric_type: MetricType, 
                      time_window_minutes: Optional[int] = None) -> Dict[str, Any]:
        """
        Get statistics for a specific metric type
        
        Args:
            metric_type: Type of metric to analyze
            time_window_minutes: Optional time window in minutes (None = all data)
            
        Returns:
            Dictionary with statistics
        """
        metrics = list(self.metrics_history[metric_type])
        
        if not metrics:
            return {
                "metric_type": metric_type,
                "count": 0,
                "avg_ms": 0.0,
                "min_ms": 0.0,
                "max_ms": 0.0,
                "p50_ms": 0.0,
                "p95_ms": 0.0,
                "p99_ms": 0.0
            }
        
        # Filter by time window if specified
        if time_window_minutes:
            cutoff_time = datetime.utcnow() - timedelta(minutes=time_window_minutes)
            metrics = [m for m in metrics if m.timestamp >= cutoff_time]
        
        if not metrics:
            return {
                "metric_type": metric_type,
                "count": 0,
                "avg_ms": 0.0,
                "min_ms": 0.0,
                "max_ms": 0.0,
                "p50_ms": 0.0,
                "p95_ms": 0.0,
                "p99_ms": 0.0
            }
        
        # Calculate statistics
        durations = sorted([m.duration_ms for m in metrics])
        count = len(durations)
        
        avg_ms = sum(durations) / count
        min_ms = durations[0]
        max_ms = durations[-1]
        
        # Calculate percentiles
        p50_idx = int(count * 0.50)
        p95_idx = int(count * 0.95)
        p99_idx = int(count * 0.99)
        
        p50_ms = durations[p50_idx] if p50_idx < count else max_ms
        p95_ms = durations[p95_idx] if p95_idx < count else max_ms
        p99_ms = durations[p99_idx] if p99_idx < count else max_ms
        
        return {
            "metric_type": metric_type,
            "count": count,
            "avg_ms": round(avg_ms, 2),
            "min_ms": round(min_ms, 2),
            "max_ms": round(max_ms, 2),
            "p50_ms": round(p50_ms, 2),
            "p95_ms": round(p95_ms, 2),
            "p99_ms": round(p99_ms, 2),
            "threshold_ms": self.alert_thresholds.get(metric_type, 0)
        }
    
    def get_all_statistics(self, time_window_minutes: Optional[int] = None) -> Dict[str, Any]:
        """
        Get statistics for all metric types
        
        Args:
            time_window_minutes: Optional time window in minutes
            
        Returns:
            Dictionary with statistics for all metrics
        """
        stats = {}
        for metric_type in MetricType:
            stats[metric_type] = self.get_statistics(metric_type, time_window_minutes)
        
        return {
            "metrics": stats,
            "alert_count": self.alert_count,
            "total_alerts": self.total_alerts,
            "time_window_minutes": time_window_minutes
        }
    
    def get_slow_queries(self, metric_type: MetricType, 
                        limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get slowest queries for a metric type
        
        Args:
            metric_type: Type of metric
            limit: Maximum number of results
            
        Returns:
            List of slowest queries with metadata
        """
        metrics = list(self.metrics_history[metric_type])
        
        # Sort by duration (descending)
        metrics.sort(key=lambda m: m.duration_ms, reverse=True)
        
        # Return top N
        return [
            {
                "duration_ms": m.duration_ms,
                "timestamp": m.timestamp.isoformat(),
                "metadata": m.metadata
            }
            for m in metrics[:limit]
        ]
    
    def reset_alerts(self):
        """Reset alert counter"""
        self.alert_count = 0
        logger.info("Alert counter reset")
    
    def clear_metrics(self, metric_type: Optional[MetricType] = None):
        """
        Clear metrics history
        
        Args:
            metric_type: Optional specific metric type to clear (None = clear all)
        """
        if metric_type:
            self.metrics_history[metric_type].clear()
            logger.info(f"Cleared metrics for {metric_type}")
        else:
            for mt in MetricType:
                self.metrics_history[mt].clear()
            logger.info("Cleared all metrics")
    
    def set_alert_threshold(self, metric_type: MetricType, threshold_ms: float):
        """
        Set alert threshold for a metric type
        
        Args:
            metric_type: Type of metric
            threshold_ms: Threshold in milliseconds
        """
        self.alert_thresholds[metric_type] = threshold_ms
        logger.info(f"Set alert threshold for {metric_type}: {threshold_ms}ms")


class PerformanceTimer:
    """Context manager for timing operations"""
    
    def __init__(self, monitor: PerformanceMonitor, metric_type: MetricType, 
                 metadata: Optional[Dict[str, Any]] = None):
        self.monitor = monitor
        self.metric_type = metric_type
        self.metadata = metadata or {}
        self.start_time = None
        self.duration_ms = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        end_time = time.time()
        self.duration_ms = (end_time - self.start_time) * 1000
        
        # Record metric
        self.monitor.record_metric(
            self.metric_type,
            self.duration_ms,
            self.metadata
        )
        
        return False  # Don't suppress exceptions


# Global performance monitor instance
performance_monitor = PerformanceMonitor()
