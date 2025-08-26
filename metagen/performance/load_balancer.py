"""
Load Balancing System for MetaWalletGen CLI.

This module provides intelligent load balancing capabilities for
distributing wallet generation and processing tasks across multiple
workers and optimizing resource utilization.
"""

import json
import logging
import time
import threading
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional, Callable, Union
from collections import defaultdict, deque
import random
import statistics
from enum import Enum


class LoadBalancingStrategy(Enum):
    """Load balancing strategies."""
    ROUND_ROBIN = "round_robin"
    LEAST_CONNECTIONS = "least_connections"
    WEIGHTED_ROUND_ROBIN = "weighted_round_robin"
    LEAST_RESPONSE_TIME = "least_response_time"
    IP_HASH = "ip_hash"
    RANDOM = "random"


class WorkerStatus(Enum):
    """Worker status enumeration."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    OFFLINE = "offline"


@dataclass
class Worker:
    """Worker node information."""
    worker_id: str
    name: str
    host: str
    port: int
    weight: int = 1
    max_connections: int = 100
    current_connections: int = 0
    response_time_ms: float = 0.0
    success_rate: float = 1.0
    last_health_check: datetime = None
    status: WorkerStatus = WorkerStatus.HEALTHY
    metadata: Dict[str, Any] = None


@dataclass
class LoadBalancingStats:
    """Load balancing statistics."""
    total_requests: int
    successful_requests: int
    failed_requests: int
    average_response_time_ms: float
    requests_per_worker: Dict[str, int]
    last_updated: datetime


class LoadBalancer:
    """Intelligent load balancing system."""
    
    def __init__(self, strategy: LoadBalancingStrategy = LoadBalancingStrategy.ROUND_ROBIN,
                 health_check_interval: float = 30.0, 
                 max_retries: int = 3):
        """Initialize load balancer."""
        self.strategy = strategy
        self.health_check_interval = health_check_interval
        self.max_retries = max_retries
        
        self.logger = logging.getLogger(__name__)
        
        # Workers
        self.workers = {}
        self.worker_list = []
        self.current_worker_index = 0
        
        # Statistics
        self.stats = LoadBalancingStats(
            total_requests=0,
            successful_requests=0,
            failed_requests=0,
            average_response_time_ms=0.0,
            requests_per_worker={},
            last_updated=datetime.now(timezone.utc)
        )
        
        # Request tracking
        self.request_history = deque(maxlen=1000)
        self.worker_response_times = defaultdict(list)
        
        # Health checking
        self.health_check_thread = None
        self.stop_event = threading.Event()
        
        # Locks
        self.workers_lock = threading.RLock()
        self.stats_lock = threading.Lock()
        
        # Start health checking
        self._start_health_check_thread()
    
    def _start_health_check_thread(self):
        """Start the health check thread."""
        self.health_check_thread = threading.Thread(target=self._health_check_loop, daemon=True)
        self.health_check_thread.start()
    
    def add_worker(self, worker: Worker) -> bool:
        """Add a worker to the load balancer."""
        try:
            with self.workers_lock:
                self.workers[worker.worker_id] = worker
                self.worker_list.append(worker)
                
                # Initialize statistics
                self.stats.requests_per_worker[worker.worker_id] = 0
                
                # Set initial health check time
                if worker.last_health_check is None:
                    worker.last_health_check = datetime.now(timezone.utc)
                
                self.logger.info(f"Added worker: {worker.name} ({worker.host}:{worker.port})")
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to add worker: {e}")
            return False
    
    def remove_worker(self, worker_id: str) -> bool:
        """Remove a worker from the load balancer."""
        try:
            with self.workers_lock:
                if worker_id in self.workers:
                    worker = self.workers[worker_id]
                    
                    # Remove from collections
                    del self.workers[worker_id]
                    self.worker_list = [w for w in self.worker_list if w.worker_id != worker_id]
                    
                    # Remove from statistics
                    if worker_id in self.stats.requests_per_worker:
                        del self.stats.requests_per_worker[worker_id]
                    
                    self.logger.info(f"Removed worker: {worker.name}")
                    return True
                else:
                    self.logger.warning(f"Worker not found: {worker_id}")
                    return False
                    
        except Exception as e:
            self.logger.error(f"Failed to remove worker: {e}")
            return False
    
    def get_worker(self, request_data: Dict[str, Any] = None) -> Optional[Worker]:
        """Get the next worker based on the selected strategy."""
        with self.workers_lock:
            if not self.worker_list:
                return None
            
            # Filter healthy workers
            healthy_workers = [w for w in self.worker_list if w.status != WorkerStatus.OFFLINE]
            
            if not healthy_workers:
                self.logger.warning("No healthy workers available")
                return None
            
            # Select worker based on strategy
            if self.strategy == LoadBalancingStrategy.ROUND_ROBIN:
                worker = self._round_robin_select(healthy_workers)
            elif self.strategy == LoadBalancingStrategy.LEAST_CONNECTIONS:
                worker = self._least_connections_select(healthy_workers)
            elif self.strategy == LoadBalancingStrategy.WEIGHTED_ROUND_ROBIN:
                worker = self._weighted_round_robin_select(healthy_workers)
            elif self.strategy == LoadBalancingStrategy.LEAST_RESPONSE_TIME:
                worker = self._least_response_time_select(healthy_workers)
            elif self.strategy == LoadBalancingStrategy.IP_HASH:
                worker = self._ip_hash_select(healthy_workers, request_data)
            elif self.strategy == LoadBalancingStrategy.RANDOM:
                worker = self._random_select(healthy_workers)
            else:
                # Default to round robin
                worker = self._round_robin_select(healthy_workers)
            
            return worker
    
    def _round_robin_select(self, workers: List[Worker]) -> Worker:
        """Round robin worker selection."""
        if not workers:
            return None
        
        worker = workers[self.current_worker_index % len(workers)]
        self.current_worker_index = (self.current_worker_index + 1) % len(workers)
        return worker
    
    def _least_connections_select(self, workers: List[Worker]) -> Worker:
        """Select worker with least connections."""
        if not workers:
            return None
        
        return min(workers, key=lambda w: w.current_connections)
    
    def _weighted_round_robin_select(self, workers: List[Worker]) -> Worker:
        """Weighted round robin worker selection."""
        if not workers:
            return None
        
        # Calculate total weight
        total_weight = sum(w.weight for w in workers)
        
        # Use current index to select worker
        current_weight = self.current_worker_index % total_weight
        self.current_worker_index = (self.current_worker_index + 1) % total_weight
        
        # Find worker based on weight
        cumulative_weight = 0
        for worker in workers:
            cumulative_weight += worker.weight
            if current_weight < cumulative_weight:
                return worker
        
        # Fallback to first worker
        return workers[0]
    
    def _least_response_time_select(self, workers: List[Worker]) -> Worker:
        """Select worker with least response time."""
        if not workers:
            return None
        
        # Filter workers with response time data
        workers_with_times = [w for w in workers if w.response_time_ms > 0]
        
        if not workers_with_times:
            return random.choice(workers)
        
        return min(workers_with_times, key=lambda w: w.response_time_ms)
    
    def _ip_hash_select(self, workers: List[Worker], request_data: Dict[str, Any]) -> Worker:
        """Select worker based on IP hash."""
        if not workers:
            return None
        
        if not request_data or 'client_ip' not in request_data:
            return random.choice(workers)
        
        # Hash the client IP
        client_ip = request_data['client_ip']
        ip_hash = hash(client_ip) % len(workers)
        
        return workers[ip_hash]
    
    def _random_select(self, workers: List[Worker]) -> Worker:
        """Random worker selection."""
        if not workers:
            return None
        
        return random.choice(workers)
    
    def record_request(self, worker_id: str, response_time_ms: float, success: bool):
        """Record request statistics."""
        try:
            with self.stats_lock:
                # Update overall statistics
                self.stats.total_requests += 1
                if success:
                    self.stats.successful_requests += 1
                else:
                    self.stats.failed_requests += 1
                
                # Update worker-specific statistics
                if worker_id in self.stats.requests_per_worker:
                    self.stats.requests_per_worker[worker_id] += 1
                
                # Update response time tracking
                self.worker_response_times[worker_id].append(response_time_ms)
                
                # Keep only recent response times (last 100)
                if len(self.worker_response_times[worker_id]) > 100:
                    self.worker_response_times[worker_id] = self.worker_response_times[worker_id][-100:]
                
                # Update average response time
                all_response_times = []
                for times in self.worker_response_times.values():
                    all_response_times.extend(times)
                
                if all_response_times:
                    self.stats.average_response_time_ms = statistics.mean(all_response_times)
                
                self.stats.last_updated = datetime.now(timezone.utc)
                
                # Update worker response time
                with self.workers_lock:
                    if worker_id in self.workers:
                        worker = self.workers[worker_id]
                        worker.response_time_ms = statistics.mean(self.worker_response_times[worker_id])
                        
                        # Update success rate
                        worker_requests = self.stats.requests_per_worker.get(worker_id, 0)
                        if worker_requests > 0:
                            worker_successes = sum(1 for t in self.worker_response_times[worker_id] if t > 0)
                            worker.success_rate = worker_successes / worker_requests
                
        except Exception as e:
            self.logger.error(f"Failed to record request statistics: {e}")
    
    def update_worker_connections(self, worker_id: str, connection_change: int):
        """Update worker connection count."""
        try:
            with self.workers_lock:
                if worker_id in self.workers:
                    worker = self.workers[worker_id]
                    worker.current_connections = max(0, worker.current_connections + connection_change)
                    
        except Exception as e:
            self.logger.error(f"Failed to update worker connections: {e}")
    
    def _health_check_loop(self):
        """Main health check loop."""
        while not self.stop_event.is_set():
            try:
                self._perform_health_checks()
                
                # Wait for next health check cycle
                self.stop_event.wait(self.health_check_interval)
                
            except Exception as e:
                self.logger.error(f"Error in health check loop: {e}")
                time.sleep(5.0)
    
    def _perform_health_checks(self):
        """Perform health checks on all workers."""
        current_time = datetime.now(timezone.utc)
        
        with self.workers_lock:
            for worker in self.worker_list:
                try:
                    # Perform health check
                    is_healthy = self._check_worker_health(worker)
                    
                    # Update worker status
                    if is_healthy:
                        if worker.status == WorkerStatus.UNHEALTHY:
                            worker.status = WorkerStatus.DEGRADED
                        elif worker.status == WorkerStatus.DEGRADED:
                            worker.status = WorkerStatus.HEALTHY
                    else:
                        if worker.status == WorkerStatus.HEALTHY:
                            worker.status = WorkerStatus.DEGRADED
                        elif worker.status == WorkerStatus.DEGRADED:
                            worker.status = WorkerStatus.UNHEALTHY
                    
                    # Update last health check time
                    worker.last_health_check = current_time
                    
                    # Log status changes
                    if worker.status == WorkerStatus.UNHEALTHY:
                        self.logger.warning(f"Worker {worker.name} is unhealthy")
                    elif worker.status == WorkerStatus.OFFLINE:
                        self.logger.error(f"Worker {worker.name} is offline")
                    
                except Exception as e:
                    self.logger.error(f"Health check failed for worker {worker.name}: {e}")
                    worker.status = WorkerStatus.UNHEALTHY
    
    def _check_worker_health(self, worker: Worker) -> bool:
        """Check if a worker is healthy."""
        try:
            # This would typically make an actual health check request
            # For now, we'll use a simple heuristic based on response time and success rate
            
            # Check if worker has recent activity
            if worker.last_health_check:
                time_since_last_check = (datetime.now(timezone.utc) - worker.last_health_check).total_seconds()
                if time_since_last_check > 300:  # 5 minutes
                    return False
            
            # Check response time
            if worker.response_time_ms > 10000:  # 10 seconds
                return False
            
            # Check success rate
            if worker.success_rate < 0.8:  # 80% success rate
                return False
            
            # Check connection limit
            if worker.current_connections >= worker.max_connections:
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Health check error for worker {worker.name}: {e}")
            return False
    
    def get_worker_status(self, worker_id: str) -> Optional[WorkerStatus]:
        """Get the status of a specific worker."""
        with self.workers_lock:
            if worker_id in self.workers:
                return self.workers[worker_id].status
        return None
    
    def get_healthy_workers(self) -> List[Worker]:
        """Get list of healthy workers."""
        with self.workers_lock:
            return [w for w in self.worker_list if w.status == WorkerStatus.HEALTHY]
    
    def get_worker_stats(self, worker_id: str) -> Optional[Dict[str, Any]]:
        """Get statistics for a specific worker."""
        with self.workers_lock:
            if worker_id in self.workers:
                worker = self.workers[worker_id]
                return {
                    'worker_id': worker.worker_id,
                    'name': worker.name,
                    'host': worker.host,
                    'port': worker.port,
                    'status': worker.status.value,
                    'current_connections': worker.current_connections,
                    'max_connections': worker.max_connections,
                    'response_time_ms': worker.response_time_ms,
                    'success_rate': worker.success_rate,
                    'last_health_check': worker.last_health_check.isoformat() if worker.last_health_check else None,
                    'total_requests': self.stats.requests_per_worker.get(worker_id, 0)
                }
        return None
    
    def get_all_worker_stats(self) -> List[Dict[str, Any]]:
        """Get statistics for all workers."""
        stats = []
        for worker in self.worker_list:
            worker_stats = self.get_worker_stats(worker.worker_id)
            if worker_stats:
                stats.append(worker_stats)
        return stats
    
    def get_load_balancing_stats(self) -> LoadBalancingStats:
        """Get load balancing statistics."""
        with self.stats_lock:
            return self.stats
    
    def set_strategy(self, strategy: LoadBalancingStrategy):
        """Change the load balancing strategy."""
        self.strategy = strategy
        self.logger.info(f"Load balancing strategy changed to: {strategy.value}")
    
    def set_worker_weight(self, worker_id: str, weight: int):
        """Set the weight of a worker."""
        with self.workers_lock:
            if worker_id in self.workers:
                self.workers[worker_id].weight = max(1, weight)
                self.logger.info(f"Worker {worker_id} weight set to: {weight}")
    
    def set_worker_max_connections(self, worker_id: str, max_connections: int):
        """Set the maximum connections for a worker."""
        with self.workers_lock:
            if worker_id in self.workers:
                self.workers[worker_id].max_connections = max(1, max_connections)
                self.logger.info(f"Worker {worker_id} max connections set to: {max_connections}")
    
    def export_load_balancing_data(self, format: str = "json", file_path: str = None) -> str:
        """Export load balancing data to file."""
        if not file_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_path = f"load_balancing_data_{timestamp}.{format}"
        
        try:
            export_data = {
                'strategy': self.strategy.value,
                'stats': asdict(self.stats),
                'workers': self.get_all_worker_stats(),
                'worker_response_times': dict(self.worker_response_times)
            }
            
            if format.lower() == "json":
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(export_data, f, indent=2, default=str)
            else:
                raise ValueError(f"Unsupported format: {format}")
            
            self.logger.info(f"Load balancing data exported to {file_path}")
            return file_path
            
        except Exception as e:
            self.logger.error(f"Failed to export load balancing data: {e}")
            raise
    
    def close(self):
        """Close the load balancer."""
        self.stop_event.set()
        
        if self.health_check_thread and self.health_check_thread.is_alive():
            self.health_check_thread.join(timeout=5.0)
        
        self.logger.info("Load balancer closed")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


# Convenience functions
def create_load_balancer(strategy: LoadBalancingStrategy = LoadBalancingStrategy.ROUND_ROBIN,
                        health_check_interval: float = 30.0,
                        max_retries: int = 3) -> LoadBalancer:
    """Create a new load balancer instance."""
    return LoadBalancer(strategy, health_check_interval, max_retries)


def create_sample_workers() -> List[Worker]:
    """Create sample workers for testing."""
    return [
        Worker(
            worker_id="worker1",
            name="Primary Worker",
            host="localhost",
            port=8001,
            weight=2,
            max_connections=100
        ),
        Worker(
            worker_id="worker2",
            name="Secondary Worker",
            host="localhost",
            port=8002,
            weight=1,
            max_connections=80
        ),
        Worker(
            worker_id="worker3",
            name="Tertiary Worker",
            host="localhost",
            port=8003,
            weight=1,
            max_connections=60
        )
    ]


# Example usage
if __name__ == "__main__":
    # Example: Create and use load balancer
    with create_load_balancer(strategy=LoadBalancingStrategy.LEAST_CONNECTIONS) as lb:
        # Add sample workers
        workers = create_sample_workers()
        for worker in workers:
            lb.add_worker(worker)
        
        # Simulate some requests
        for i in range(10):
            worker = lb.get_worker()
            if worker:
                print(f"Request {i+1} assigned to: {worker.name}")
                
                # Simulate response time and success
                response_time = random.uniform(100, 1000)
                success = random.random() > 0.1  # 90% success rate
                
                lb.record_request(worker.worker_id, response_time, success)
        
        # Get statistics
        stats = lb.get_load_balancing_stats()
        print(f"\nLoad Balancing Stats:")
        print(f"Total requests: {stats.total_requests}")
        print(f"Success rate: {stats.successful_requests/stats.total_requests:.2%}")
        print(f"Average response time: {stats.average_response_time_ms:.2f}ms")
        
        # Get worker statistics
        worker_stats = lb.get_all_worker_stats()
        print(f"\nWorker Statistics:")
        for worker_stat in worker_stats:
            print(f"- {worker_stat['name']}: {worker_stat['status']}, "
                  f"Connections: {worker_stat['current_connections']}/{worker_stat['max_connections']}, "
                  f"Response time: {worker_stat['response_time_ms']:.2f}ms")
