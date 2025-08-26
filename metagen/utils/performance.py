"""
Performance Monitoring and Optimization Module

This module provides:
- Performance metrics collection
- Memory usage monitoring
- Execution time profiling
- Optimization suggestions
- Resource usage tracking
"""

import time
import psutil
import threading
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from contextlib import contextmanager
import logging
from collections import defaultdict, deque


@dataclass
class PerformanceMetric:
    """Individual performance metric."""
    name: str
    value: float
    unit: str
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PerformanceSnapshot:
    """Snapshot of performance metrics at a point in time."""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    memory_mb: float
    disk_io_read: float
    disk_io_write: float
    network_io_sent: float
    network_io_recv: float
    active_threads: int
    open_files: int


class PerformanceMonitor:
    """Performance monitoring and analysis system."""
    
    def __init__(self, max_history: int = 1000):
        self.max_history = max_history
        self.metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=max_history))
        self.snapshots: deque = deque(maxlen=max_history)
        self.logger = logging.getLogger("performance")
        self.monitoring = False
        self.monitor_thread: Optional[threading.Thread] = None
        
        # Performance thresholds
        self.thresholds = {
            "cpu_percent": 80.0,
            "memory_percent": 85.0,
            "memory_mb": 1000.0,  # 1GB
            "execution_time_ms": 5000.0,  # 5 seconds
        }
    
    def start_monitoring(self, interval_seconds: float = 1.0):
        """Start continuous performance monitoring."""
        if self.monitoring:
            return
        
        self.monitoring = True
        self.monitor_thread = threading.Thread(
            target=self._monitor_loop,
            args=(interval_seconds,),
            daemon=True
        )
        self.monitor_thread.start()
        self.logger.info("Performance monitoring started")
    
    def stop_monitoring(self):
        """Stop continuous performance monitoring."""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=1.0)
        self.logger.info("Performance monitoring stopped")
    
    def _monitor_loop(self, interval_seconds: float):
        """Main monitoring loop."""
        while self.monitoring:
            try:
                snapshot = self._take_snapshot()
                self.snapshots.append(snapshot)
                
                # Check thresholds
                self._check_thresholds(snapshot)
                
                time.sleep(interval_seconds)
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
    
    def _take_snapshot(self) -> PerformanceSnapshot:
        """Take a snapshot of current system performance."""
        process = psutil.Process()
        
        # CPU and memory
        cpu_percent = process.cpu_percent()
        memory_info = process.memory_info()
        memory_percent = process.memory_percent()
        
        # Disk I/O
        disk_io = process.io_counters()
        
        # Network I/O
        network_io = process.connections()
        
        # Threads and files
        active_threads = process.num_threads()
        open_files = len(process.open_files())
        
        return PerformanceSnapshot(
            timestamp=datetime.now(),
            cpu_percent=cpu_percent,
            memory_percent=memory_percent,
            memory_mb=memory_info.rss / (1024 * 1024),
            disk_io_read=disk_io.read_bytes / (1024 * 1024),  # MB
            disk_io_write=disk_io.write_bytes / (1024 * 1024),  # MB
            network_io_sent=0,  # Would need more complex monitoring
            network_io_recv=0,  # Would need more complex monitoring
            active_threads=active_threads,
            open_files=open_files
        )
    
    def _check_thresholds(self, snapshot: PerformanceSnapshot):
        """Check if any performance thresholds are exceeded."""
        warnings = []
        
        if snapshot.cpu_percent > self.thresholds["cpu_percent"]:
            warnings.append(f"High CPU usage: {snapshot.cpu_percent:.1f}%")
        
        if snapshot.memory_percent > self.thresholds["memory_percent"]:
            warnings.append(f"High memory usage: {snapshot.memory_percent:.1f}%")
        
        if snapshot.memory_mb > self.thresholds["memory_mb"]:
            warnings.append(f"High memory usage: {snapshot.memory_mb:.1f} MB")
        
        if warnings:
            for warning in warnings:
                self.logger.warning(warning)
    
    def record_metric(self, name: str, value: float, unit: str, 
                     metadata: Optional[Dict[str, Any]] = None):
        """Record a custom performance metric."""
        metric = PerformanceMetric(
            name=name,
            value=value,
            unit=unit,
            timestamp=datetime.now(),
            metadata=metadata or {}
        )
        self.metrics[name].append(metric)
    
    @contextmanager
    def measure_execution_time(self, operation_name: str):
        """Context manager to measure execution time of operations."""
        start_time = time.time()
        start_memory = psutil.Process().memory_info().rss
        
        try:
            yield
        finally:
            end_time = time.time()
            end_memory = psutil.Process().memory_info().rss
            
            execution_time = (end_time - start_time) * 1000  # Convert to milliseconds
            memory_delta = (end_memory - start_memory) / (1024 * 1024)  # Convert to MB
            
            self.record_metric(
                f"{operation_name}_execution_time",
                execution_time,
                "ms",
                {"memory_delta_mb": memory_delta}
            )
            
            # Check if execution time exceeds threshold
            if execution_time > self.thresholds["execution_time_ms"]:
                self.logger.warning(
                    f"Slow operation detected: {operation_name} took {execution_time:.1f}ms"
                )
    
    def get_performance_summary(self, time_window_minutes: int = 15) -> Dict:
        """Get performance summary for the specified time window."""
        cutoff_time = datetime.now() - timedelta(minutes=time_window_minutes)
        
        # Filter recent snapshots
        recent_snapshots = [
            s for s in self.snapshots
            if s.timestamp > cutoff_time
        ]
        
        if not recent_snapshots:
            return {"error": "No performance data available"}
        
        # Calculate averages
        avg_cpu = sum(s.cpu_percent for s in recent_snapshots) / len(recent_snapshots)
        avg_memory = sum(s.memory_mb for s in recent_snapshots) / len(recent_snapshots)
        avg_memory_percent = sum(s.memory_percent for s in recent_snapshots) / len(recent_snapshots)
        
        # Find peaks
        max_cpu = max(s.cpu_percent for s in recent_snapshots)
        max_memory = max(s.memory_mb for s in recent_snapshots)
        
        # Calculate trends
        if len(recent_snapshots) > 1:
            cpu_trend = (recent_snapshots[-1].cpu_percent - recent_snapshots[0].cpu_percent)
            memory_trend = (recent_snapshots[-1].memory_mb - recent_snapshots[0].memory_mb)
        else:
            cpu_trend = memory_trend = 0
        
        return {
            "time_window_minutes": time_window_minutes,
            "data_points": len(recent_snapshots),
            "averages": {
                "cpu_percent": round(avg_cpu, 2),
                "memory_mb": round(avg_memory, 2),
                "memory_percent": round(avg_memory_percent, 2)
            },
            "peaks": {
                "cpu_percent": round(max_cpu, 2),
                "memory_mb": round(max_memory, 2)
            },
            "trends": {
                "cpu_trend": round(cpu_trend, 2),
                "memory_trend": round(memory_trend, 2)
            },
            "status": self._get_performance_status(avg_cpu, avg_memory_percent)
        }
    
    def _get_performance_status(self, avg_cpu: float, avg_memory_percent: float) -> str:
        """Determine overall performance status."""
        if avg_cpu > 80 or avg_memory_percent > 85:
            return "CRITICAL"
        elif avg_cpu > 60 or avg_memory_percent > 70:
            return "WARNING"
        elif avg_cpu > 40 or avg_memory_percent > 50:
            return "ATTENTION"
        else:
            return "NORMAL"
    
    def get_optimization_suggestions(self) -> List[str]:
        """Generate optimization suggestions based on performance data."""
        suggestions = []
        
        if not self.snapshots:
            return ["No performance data available for analysis"]
        
        recent_snapshots = list(self.snapshots)[-50:]  # Last 50 snapshots
        
        # Analyze CPU usage
        high_cpu_count = sum(1 for s in recent_snapshots if s.cpu_percent > 70)
        if high_cpu_count > len(recent_snapshots) * 0.3:  # More than 30% of time
            suggestions.append("Consider optimizing CPU-intensive operations or adding caching")
        
        # Analyze memory usage
        high_memory_count = sum(1 for s in recent_snapshots if s.memory_mb > 500)
        if high_memory_count > len(recent_snapshots) * 0.2:  # More than 20% of time
            suggestions.append("Memory usage is high - consider implementing memory pooling or cleanup")
        
        # Analyze disk I/O
        total_disk_io = sum(s.disk_io_read + s.disk_io_write for s in recent_snapshots)
        if total_disk_io > 1000:  # More than 1GB total I/O
            suggestions.append("High disk I/O detected - consider implementing I/O batching or caching")
        
        # Analyze thread usage
        avg_threads = sum(s.active_threads for s in recent_snapshots) / len(recent_snapshots)
        if avg_threads > 10:
            suggestions.append("High thread count - consider using thread pools or async operations")
        
        if not suggestions:
            suggestions.append("Performance appears to be within normal ranges")
        
        return suggestions
    
    def export_metrics(self, format: str = "json") -> str:
        """Export performance metrics in specified format."""
        if format.lower() == "json":
            import json
            data = {
                "snapshots": [
                    {
                        "timestamp": s.timestamp.isoformat(),
                        "cpu_percent": s.cpu_percent,
                        "memory_mb": s.memory_mb,
                        "memory_percent": s.memory_percent,
                        "active_threads": s.active_threads
                    }
                    for s in self.snapshots
                ],
                "custom_metrics": {
                    name: [
                        {
                            "value": m.value,
                            "unit": m.unit,
                            "timestamp": m.timestamp.isoformat(),
                            "metadata": m.metadata
                        }
                        for m in metrics
                    ]
                    for name, metrics in self.metrics.items()
                }
            }
            return json.dumps(data, indent=2)
        else:
            return f"Unsupported format: {format}"


# Global performance monitor instance
_performance_monitor: Optional[PerformanceMonitor] = None


def get_performance_monitor() -> PerformanceMonitor:
    """Get or create global performance monitor instance."""
    global _performance_monitor
    if _performance_monitor is None:
        _performance_monitor = PerformanceMonitor()
    return _performance_monitor


def start_performance_monitoring(interval_seconds: float = 1.0):
    """Start global performance monitoring."""
    monitor = get_performance_monitor()
    monitor.start_monitoring(interval_seconds)


def stop_performance_monitoring():
    """Stop global performance monitoring."""
    monitor = get_performance_monitor()
    monitor.stop_monitoring()


@contextmanager
def performance_timer(operation_name: str):
    """Context manager for measuring operation performance."""
    monitor = get_performance_monitor()
    with monitor.measure_execution_time(operation_name):
        yield
