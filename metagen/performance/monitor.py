"""
Performance Monitoring System for MetaWalletGen CLI.

This module provides comprehensive performance monitoring capabilities
including system metrics, wallet generation performance, and resource usage.
"""

import json
import logging
import time
import threading
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional, Callable
from collections import deque, defaultdict
import psutil
import statistics


@dataclass
class PerformanceMetric:
    """Performance metric data structure."""
    name: str
    value: float
    unit: str
    timestamp: datetime
    category: str
    metadata: Dict[str, Any] = None


@dataclass
class PerformanceAlert:
    """Performance alert data structure."""
    alert_id: str
    metric_name: str
    threshold: float
    current_value: float
    severity: str
    message: str
    timestamp: datetime
    acknowledged: bool = False


@dataclass
class SystemMetrics:
    """System performance metrics."""
    cpu_percent: float
    memory_percent: float
    disk_usage_percent: float
    network_io: Dict[str, float]
    timestamp: datetime


class PerformanceMonitor:
    """Real-time performance monitoring system."""
    
    def __init__(self, max_history_size: int = 1000, monitoring_interval: float = 1.0):
        """Initialize performance monitor."""
        self.max_history_size = max_history_size
        self.monitoring_interval = monitoring_interval
        self.logger = logging.getLogger(__name__)
        
        # Metrics storage
        self.metrics_history = defaultdict(lambda: deque(maxlen=max_history_size))
        self.current_metrics = {}
        
        # Alerting system
        self.alert_thresholds = {}
        self.active_alerts = {}
        self.alert_handlers = []
        
        # Monitoring state
        self.is_monitoring = False
        self.monitor_thread = None
        self.stop_event = threading.Event()
        
        # Performance counters
        self.wallet_generation_times = deque(maxlen=max_history_size)
        self.encryption_times = deque(maxlen=max_history_size)
        self.api_response_times = deque(maxlen=max_history_size)
        
        # Initialize default thresholds
        self._init_default_thresholds()
    
    def _init_default_thresholds(self):
        """Initialize default performance thresholds."""
        self.alert_thresholds = {
            'cpu_percent': {'warning': 70.0, 'critical': 90.0},
            'memory_percent': {'warning': 80.0, 'critical': 95.0},
            'disk_usage_percent': {'warning': 85.0, 'critical': 95.0},
            'wallet_generation_time_ms': {'warning': 1000.0, 'critical': 5000.0},
            'encryption_time_ms': {'warning': 500.0, 'critical': 2000.0},
            'api_response_time_ms': {'warning': 1000.0, 'critical': 5000.0}
        }
    
    def start_monitoring(self):
        """Start performance monitoring."""
        if self.is_monitoring:
            self.logger.warning("Performance monitoring is already running")
            return
        
        self.is_monitoring = True
        self.stop_event.clear()
        self.monitor_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitor_thread.start()
        self.logger.info("Performance monitoring started")
    
    def stop_monitoring(self):
        """Stop performance monitoring."""
        if not self.is_monitoring:
            return
        
        self.is_monitoring = False
        self.stop_event.set()
        
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=5.0)
        
        self.logger.info("Performance monitoring stopped")
    
    def _monitoring_loop(self):
        """Main monitoring loop."""
        while not self.stop_event.is_set():
            try:
                # Collect system metrics
                system_metrics = self._collect_system_metrics()
                self._store_metrics(system_metrics)
                
                # Check for alerts
                self._check_alerts()
                
                # Wait for next monitoring cycle
                self.stop_event.wait(self.monitoring_interval)
                
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                time.sleep(1.0)  # Brief pause on error
    
    def _collect_system_metrics(self) -> SystemMetrics:
        """Collect current system performance metrics."""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=0.1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_usage_percent = (disk.used / disk.total) * 100
            
            # Network I/O
            network = psutil.net_io_counters()
            network_io = {
                'bytes_sent': network.bytes_sent,
                'bytes_recv': network.bytes_recv,
                'packets_sent': network.packets_sent,
                'packets_recv': network.packets_recv
            }
            
            return SystemMetrics(
                cpu_percent=cpu_percent,
                memory_percent=memory_percent,
                disk_usage_percent=disk_usage_percent,
                network_io=network_io,
                timestamp=datetime.now(timezone.utc)
            )
            
        except Exception as e:
            self.logger.error(f"Failed to collect system metrics: {e}")
            return SystemMetrics(
                cpu_percent=0.0,
                memory_percent=0.0,
                disk_usage_percent=0.0,
                network_io={},
                timestamp=datetime.now(timezone.utc)
            )
    
    def _store_metrics(self, metrics: SystemMetrics):
        """Store metrics in history."""
        timestamp = metrics.timestamp
        
        # Store system metrics
        self.metrics_history['cpu_percent'].append(
            PerformanceMetric('cpu_percent', metrics.cpu_percent, '%', timestamp, 'system')
        )
        self.metrics_history['memory_percent'].append(
            PerformanceMetric('memory_percent', metrics.memory_percent, '%', timestamp, 'system')
        )
        self.metrics_history['disk_usage_percent'].append(
            PerformanceMetric('disk_usage_percent', metrics.disk_usage_percent, '%', timestamp, 'system')
        )
        
        # Store network metrics
        for name, value in metrics.network_io.items():
            self.metrics_history[f'network_{name}'].append(
                PerformanceMetric(f'network_{name}', value, 'bytes', timestamp, 'network')
            )
        
        # Update current metrics
        self.current_metrics.update({
            'cpu_percent': metrics.cpu_percent,
            'memory_percent': metrics.memory_percent,
            'disk_usage_percent': metrics.disk_usage_percent,
            'timestamp': timestamp
        })
    
    def record_wallet_generation_time(self, generation_time_ms: float):
        """Record wallet generation performance."""
        timestamp = datetime.now(timezone.utc)
        metric = PerformanceMetric(
            'wallet_generation_time_ms',
            generation_time_ms,
            'ms',
            timestamp,
            'wallet_generation'
        )
        
        self.metrics_history['wallet_generation_time_ms'].append(metric)
        self.wallet_generation_times.append(generation_time_ms)
        
        # Check for alerts
        self._check_metric_alert('wallet_generation_time_ms', generation_time_ms)
    
    def record_encryption_time(self, encryption_time_ms: float):
        """Record encryption performance."""
        timestamp = datetime.now(timezone.utc)
        metric = PerformanceMetric(
            'encryption_time_ms',
            encryption_time_ms,
            'ms',
            timestamp,
            'encryption'
        )
        
        self.metrics_history['encryption_time_ms'].append(metric)
        self.encryption_times.append(encryption_time_ms)
        
        # Check for alerts
        self._check_metric_alert('encryption_time_ms', encryption_time_ms)
    
    def record_api_response_time(self, endpoint: str, response_time_ms: float):
        """Record API response time."""
        timestamp = datetime.now(timezone.utc)
        metric = PerformanceMetric(
            f'api_response_time_{endpoint}_ms',
            response_time_ms,
            'ms',
            timestamp,
            'api',
            metadata={'endpoint': endpoint}
        )
        
        self.metrics_history[f'api_response_time_{endpoint}_ms'].append(metric)
        self.api_response_times.append(response_time_ms)
        
        # Check for alerts
        self._check_metric_alert('api_response_time_ms', response_time_ms)
    
    def _check_metric_alert(self, metric_name: str, current_value: float):
        """Check if metric exceeds alert thresholds."""
        if metric_name not in self.alert_thresholds:
            return
        
        thresholds = self.alert_thresholds[metric_name]
        
        # Check critical threshold first
        if 'critical' in thresholds and current_value >= thresholds['critical']:
            self._create_alert(metric_name, thresholds['critical'], current_value, 'critical')
        # Check warning threshold
        elif 'warning' in thresholds and current_value >= thresholds['warning']:
            self._create_alert(metric_name, thresholds['warning'], current_value, 'warning')
    
    def _create_alert(self, metric_name: str, threshold: float, current_value: float, severity: str):
        """Create a new performance alert."""
        alert_id = f"{metric_name}_{int(time.time())}"
        
        alert = PerformanceAlert(
            alert_id=alert_id,
            metric_name=metric_name,
            threshold=threshold,
            current_value=current_value,
            severity=severity,
            message=f"{metric_name} exceeded {severity} threshold: {current_value} >= {threshold}",
            timestamp=datetime.now(timezone.utc)
        )
        
        self.active_alerts[alert_id] = alert
        
        # Notify alert handlers
        for handler in self.alert_handlers:
            try:
                handler(alert)
            except Exception as e:
                self.logger.error(f"Error in alert handler: {e}")
        
        self.logger.warning(f"Performance alert: {alert.message}")
    
    def _check_alerts(self):
        """Check all active alerts and clear resolved ones."""
        current_time = datetime.now(timezone.utc)
        resolved_alerts = []
        
        for alert_id, alert in self.active_alerts.items():
            # Check if alert is still relevant (within last 5 minutes)
            if (current_time - alert.timestamp) > timedelta(minutes=5):
                resolved_alerts.append(alert_id)
        
        # Remove resolved alerts
        for alert_id in resolved_alerts:
            del self.active_alerts[alert_id]
    
    def add_alert_handler(self, handler: Callable[[PerformanceAlert], None]):
        """Add a custom alert handler."""
        self.alert_handlers.append(handler)
    
    def set_alert_threshold(self, metric_name: str, threshold_type: str, value: float):
        """Set custom alert threshold."""
        if metric_name not in self.alert_thresholds:
            self.alert_thresholds[metric_name] = {}
        
        self.alert_thresholds[metric_name][threshold_type] = value
        self.logger.info(f"Set {threshold_type} threshold for {metric_name}: {value}")
    
    def get_current_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics."""
        return self.current_metrics.copy()
    
    def get_metric_history(self, metric_name: str, 
                          start_time: datetime = None, 
                          end_time: datetime = None) -> List[PerformanceMetric]:
        """Get historical metrics for a specific metric."""
        if metric_name not in self.metrics_history:
            return []
        
        metrics = list(self.metrics_history[metric_name])
        
        # Apply time filters
        if start_time:
            metrics = [m for m in metrics if m.timestamp >= start_time]
        if end_time:
            metrics = [m for m in metrics if m.timestamp <= end_time]
        
        return metrics
    
    def get_metric_statistics(self, metric_name: str, 
                             time_window: timedelta = None) -> Dict[str, float]:
        """Get statistical summary for a metric."""
        metrics = self.get_metric_history(metric_name)
        
        if time_window:
            cutoff_time = datetime.now(timezone.utc) - time_window
            metrics = [m for m in metrics if m.timestamp >= cutoff_time]
        
        if not metrics:
            return {}
        
        values = [m.value for m in metrics]
        
        return {
            'count': len(values),
            'min': min(values),
            'max': max(values),
            'mean': statistics.mean(values),
            'median': statistics.median(values),
            'std_dev': statistics.stdev(values) if len(values) > 1 else 0.0
        }
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance summary."""
        current_time = datetime.now(timezone.utc)
        last_hour = current_time - timedelta(hours=1)
        last_24h = current_time - timedelta(hours=24)
        
        summary = {
            'timestamp': current_time.isoformat(),
            'system_health': {
                'cpu_percent': self.current_metrics.get('cpu_percent', 0.0),
                'memory_percent': self.current_metrics.get('memory_percent', 0.0),
                'disk_usage_percent': self.current_metrics.get('disk_usage_percent', 0.0)
            },
            'wallet_generation': {
                'last_hour': self.get_metric_statistics('wallet_generation_time_ms', timedelta(hours=1)),
                'last_24h': self.get_metric_statistics('wallet_generation_time_ms', timedelta(hours=24))
            },
            'encryption': {
                'last_hour': self.get_metric_statistics('encryption_time_ms', timedelta(hours=1)),
                'last_24h': self.get_metric_statistics('encryption_time_ms', timedelta(hours=24))
            },
            'api_performance': {
                'last_hour': self.get_metric_statistics('api_response_time_ms', timedelta(hours=1)),
                'last_24h': self.get_metric_statistics('api_response_time_ms', timedelta(hours=24))
            },
            'active_alerts': len(self.active_alerts),
            'alert_summary': {
                'critical': len([a for a in self.active_alerts.values() if a.severity == 'critical']),
                'warning': len([a for a in self.active_alerts.values() if a.severity == 'warning'])
            }
        }
        
        return summary
    
    def export_metrics(self, format: str = "json", file_path: str = None) -> str:
        """Export performance metrics to file."""
        if not file_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_path = f"performance_metrics_{timestamp}.{format}"
        
        try:
            if format.lower() == "json":
                # Export all metrics
                export_data = {
                    'summary': self.get_performance_summary(),
                    'metrics': {}
                }
                
                for metric_name in self.metrics_history:
                    export_data['metrics'][metric_name] = [
                        asdict(m) for m in self.metrics_history[metric_name]
                    ]
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(export_data, f, indent=2, default=str)
            
            elif format.lower() == "csv":
                # Export as CSV
                import csv
                
                with open(file_path, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    
                    # Write header
                    writer.writerow(['metric_name', 'value', 'unit', 'timestamp', 'category'])
                    
                    # Write data
                    for metric_name, metrics in self.metrics_history.items():
                        for metric in metrics:
                            writer.writerow([
                                metric.name,
                                metric.value,
                                metric.unit,
                                metric.timestamp.isoformat(),
                                metric.category
                            ])
            
            else:
                raise ValueError(f"Unsupported format: {format}")
            
            self.logger.info(f"Performance metrics exported to {file_path}")
            return file_path
            
        except Exception as e:
            self.logger.error(f"Failed to export metrics: {e}")
            raise
    
    def clear_history(self):
        """Clear all historical metrics."""
        for metric_name in self.metrics_history:
            self.metrics_history[metric_name].clear()
        
        self.wallet_generation_times.clear()
        self.encryption_times.clear()
        self.api_response_times.clear()
        
        self.logger.info("Performance metrics history cleared")
    
    def __enter__(self):
        """Context manager entry."""
        self.start_monitoring()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop_monitoring()


# Convenience functions
def create_performance_monitor(max_history_size: int = 1000, 
                              monitoring_interval: float = 1.0) -> PerformanceMonitor:
    """Create a new performance monitor instance."""
    return PerformanceMonitor(max_history_size, monitoring_interval)


def quick_performance_check() -> Dict[str, Any]:
    """Quick performance check without continuous monitoring."""
    monitor = PerformanceMonitor()
    monitor.start_monitoring()
    
    # Wait for initial metrics collection
    time.sleep(2.0)
    
    summary = monitor.get_performance_summary()
    monitor.stop_monitoring()
    
    return summary


# Example usage
if __name__ == "__main__":
    # Example: Monitor performance during wallet generation
    with create_performance_monitor() as monitor:
        # Add custom alert handler
        def alert_handler(alert):
            print(f"ALERT: {alert.message}")
        
        monitor.add_alert_handler(alert_handler)
        
        # Simulate some operations
        for i in range(5):
            # Simulate wallet generation
            generation_time = 100 + (i * 50)  # Increasing time
            monitor.record_wallet_generation_time(generation_time)
            
            # Simulate encryption
            encryption_time = 50 + (i * 20)
            monitor.record_encryption_time(encryption_time)
            
            time.sleep(1.0)
        
        # Get performance summary
        summary = monitor.get_performance_summary()
        print("Performance Summary:")
        print(json.dumps(summary, indent=2, default=str))
