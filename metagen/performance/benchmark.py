"""
Benchmark Suite for MetaWalletGen CLI.

This module provides comprehensive benchmarking capabilities for
wallet generation, encryption, and overall system performance.
"""

import json
import logging
import time
import threading
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional, Callable, Union
from collections import defaultdict, deque
import statistics
import psutil
import matplotlib.pyplot as plt
import pandas as pd
from pathlib import Path


@dataclass
class BenchmarkResult:
    """Benchmark result data structure."""
    benchmark_name: str
    timestamp: datetime
    duration_seconds: float
    iterations: int
    metrics: Dict[str, float]
    metadata: Dict[str, Any] = None


@dataclass
class BenchmarkSuite:
    """Benchmark suite configuration."""
    suite_name: str
    description: str
    benchmarks: List[str]
    iterations: int
    warmup_iterations: int
    timeout_seconds: int
    created_at: datetime


@dataclass
class PerformanceMetrics:
    """Performance metrics for benchmarking."""
    cpu_usage_percent: float
    memory_usage_mb: float
    disk_io_bytes: int
    network_io_bytes: int
    response_time_ms: float
    throughput_per_second: float
    error_rate: float


class BenchmarkRunner:
    """Comprehensive benchmark runner for MetaWalletGen CLI."""
    
    def __init__(self, output_dir: str = "benchmarks"):
        """Initialize benchmark runner."""
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        self.logger = logging.getLogger(__name__)
        
        # Benchmark results
        self.results = []
        self.current_suite = None
        
        # Performance monitoring
        self.metrics_history = []
        self.baseline_metrics = None
        
        # Configuration
        self.enable_plots = True
        self.save_detailed_results = True
        
        # Initialize matplotlib for non-interactive use
        plt.switch_backend('Agg')
    
    def run_wallet_generation_benchmark(self, wallet_count: int = 100, 
                                       iterations: int = 5) -> BenchmarkResult:
        """Run wallet generation benchmark."""
        benchmark_name = f"wallet_generation_{wallet_count}"
        self.logger.info(f"Starting {benchmark_name} benchmark")
        
        # Warmup
        self._warmup_wallet_generation(wallet_count)
        
        # Run benchmark
        start_time = time.time()
        metrics_list = []
        
        for i in range(iterations):
            self.logger.info(f"Running iteration {i+1}/{iterations}")
            
            # Record baseline metrics
            baseline = self._capture_system_metrics()
            
            # Run wallet generation
            iteration_start = time.time()
            wallets_generated = self._generate_wallets(wallet_count)
            iteration_duration = time.time() - iteration_start
            
            # Record final metrics
            final = self._capture_system_metrics()
            
            # Calculate metrics
            metrics = self._calculate_metrics(baseline, final, iteration_duration, wallet_count)
            metrics_list.append(metrics)
            
            # Store metrics history
            self.metrics_history.append({
                'iteration': i,
                'benchmark': benchmark_name,
                'metrics': metrics,
                'timestamp': datetime.now(timezone.utc)
            })
        
        # Calculate final results
        duration = time.time() - start_time
        avg_metrics = self._average_metrics(metrics_list)
        
        result = BenchmarkResult(
            benchmark_name=benchmark_name,
            timestamp=datetime.now(timezone.utc),
            duration_seconds=duration,
            iterations=iterations,
            metrics=avg_metrics,
            metadata={
                'wallet_count': wallet_count,
                'individual_metrics': metrics_list
            }
        )
        
        self.results.append(result)
        self.logger.info(f"Completed {benchmark_name} benchmark in {duration:.2f}s")
        
        return result
    
    def run_encryption_benchmark(self, data_size_mb: int = 10, 
                                iterations: int = 5) -> BenchmarkResult:
        """Run encryption benchmark."""
        benchmark_name = f"encryption_{data_size_mb}mb"
        self.logger.info(f"Starting {benchmark_name} benchmark")
        
        # Warmup
        self._warmup_encryption(data_size_mb)
        
        # Run benchmark
        start_time = time.time()
        metrics_list = []
        
        for i in range(iterations):
            self.logger.info(f"Running iteration {i+1}/{iterations}")
            
            # Record baseline metrics
            baseline = self._capture_system_metrics()
            
            # Run encryption
            iteration_start = time.time()
            encrypted_data = self._encrypt_data(data_size_mb)
            iteration_duration = time.time() - iteration_start
            
            # Record final metrics
            final = self._capture_system_metrics()
            
            # Calculate metrics
            metrics = self._calculate_metrics(baseline, final, iteration_duration, data_size_mb)
            metrics_list.append(metrics)
            
            # Store metrics history
            self.metrics_history.append({
                'iteration': i,
                'benchmark': benchmark_name,
                'metrics': metrics,
                'timestamp': datetime.now(timezone.utc)
            })
        
        # Calculate final results
        duration = time.time() - start_time
        avg_metrics = self._average_metrics(metrics_list)
        
        result = BenchmarkResult(
            benchmark_name=benchmark_name,
            timestamp=datetime.now(timezone.utc),
            duration_seconds=duration,
            iterations=iterations,
            metrics=avg_metrics,
            metadata={
                'data_size_mb': data_size_mb,
                'individual_metrics': metrics_list
            }
        )
        
        self.results.append(result)
        self.logger.info(f"Completed {benchmark_name} benchmark in {duration:.2f}s")
        
        return result
    
    def run_api_performance_benchmark(self, endpoint: str, request_count: int = 100,
                                    concurrent_requests: int = 10) -> BenchmarkResult:
        """Run API performance benchmark."""
        benchmark_name = f"api_performance_{endpoint}_{request_count}"
        self.logger.info(f"Starting {benchmark_name} benchmark")
        
        # Warmup
        self._warmup_api(endpoint)
        
        # Run benchmark
        start_time = time.time()
        metrics_list = []
        
        # Run concurrent requests
        for i in range(0, request_count, concurrent_requests):
            batch_size = min(concurrent_requests, request_count - i)
            self.logger.info(f"Running batch {i//concurrent_requests + 1}, size: {batch_size}")
            
            # Record baseline metrics
            baseline = self._capture_system_metrics()
            
            # Run concurrent requests
            iteration_start = time.time()
            responses = self._run_concurrent_api_requests(endpoint, batch_size)
            iteration_duration = time.time() - iteration_start
            
            # Record final metrics
            final = self._capture_system_metrics()
            
            # Calculate metrics
            metrics = self._calculate_metrics(baseline, final, iteration_duration, batch_size)
            metrics_list.append(metrics)
            
            # Store metrics history
            self.metrics_history.append({
                'iteration': i//concurrent_requests,
                'benchmark': benchmark_name,
                'metrics': metrics,
                'timestamp': datetime.now(timezone.utc)
            })
        
        # Calculate final results
        duration = time.time() - start_time
        avg_metrics = self._average_metrics(metrics_list)
        
        result = BenchmarkResult(
            benchmark_name=benchmark_name,
            timestamp=datetime.now(timezone.utc),
            duration_seconds=duration,
            iterations=len(metrics_list),
            metrics=avg_metrics,
            metadata={
                'endpoint': endpoint,
                'request_count': request_count,
                'concurrent_requests': concurrent_requests,
                'individual_metrics': metrics_list
            }
        )
        
        self.results.append(result)
        self.logger.info(f"Completed {benchmark_name} benchmark in {duration:.2f}s")
        
        return result
    
    def run_system_stress_test(self, duration_minutes: int = 10, 
                              wallet_batch_size: int = 50) -> BenchmarkResult:
        """Run system stress test."""
        benchmark_name = f"system_stress_{duration_minutes}min"
        self.logger.info(f"Starting {benchmark_name} benchmark")
        
        # Warmup
        self._warmup_system()
        
        # Run stress test
        start_time = time.time()
        end_time = start_time + (duration_minutes * 60)
        metrics_list = []
        iteration = 0
        
        while time.time() < end_time:
            iteration += 1
            self.logger.info(f"Running stress iteration {iteration}")
            
            # Record baseline metrics
            baseline = self._capture_system_metrics()
            
            # Run stress operations
            iteration_start = time.time()
            self._run_stress_operations(wallet_batch_size)
            iteration_duration = time.time() - iteration_start
            
            # Record final metrics
            final = self._capture_system_metrics()
            
            # Calculate metrics
            metrics = self._calculate_metrics(baseline, final, iteration_duration, wallet_batch_size)
            metrics_list.append(metrics)
            
            # Store metrics history
            self.metrics_history.append({
                'iteration': iteration,
                'benchmark': benchmark_name,
                'metrics': metrics,
                'timestamp': datetime.now(timezone.utc)
            })
            
            # Brief pause between iterations
            time.sleep(1.0)
        
        # Calculate final results
        duration = time.time() - start_time
        avg_metrics = self._average_metrics(metrics_list)
        
        result = BenchmarkResult(
            benchmark_name=benchmark_name,
            timestamp=datetime.now(timezone.utc),
            duration_seconds=duration,
            iterations=iteration,
            metrics=avg_metrics,
            metadata={
                'duration_minutes': duration_minutes,
                'wallet_batch_size': wallet_batch_size,
                'individual_metrics': metrics_list
            }
        )
        
        self.results.append(result)
        self.logger.info(f"Completed {benchmark_name} benchmark in {duration:.2f}s")
        
        return result
    
    def run_comprehensive_benchmark_suite(self, suite: BenchmarkSuite) -> List[BenchmarkResult]:
        """Run a comprehensive benchmark suite."""
        self.current_suite = suite
        self.logger.info(f"Starting benchmark suite: {suite.suite_name}")
        
        results = []
        
        for benchmark_name in suite.benchmarks:
            try:
                if "wallet_generation" in benchmark_name:
                    # Extract wallet count from benchmark name
                    wallet_count = int(benchmark_name.split('_')[-1])
                    result = self.run_wallet_generation_benchmark(wallet_count, suite.iterations)
                elif "encryption" in benchmark_name:
                    # Extract data size from benchmark name
                    data_size = int(benchmark_name.split('_')[1])
                    result = self.run_encryption_benchmark(data_size, suite.iterations)
                elif "api_performance" in benchmark_name:
                    # Extract endpoint from benchmark name
                    endpoint = benchmark_name.split('_')[2]
                    result = self.run_api_performance_benchmark(endpoint, 100, 10)
                elif "system_stress" in benchmark_name:
                    # Extract duration from benchmark name
                    duration = int(benchmark_name.split('_')[2])
                    result = self.run_system_stress_test(duration, 50)
                else:
                    self.logger.warning(f"Unknown benchmark type: {benchmark_name}")
                    continue
                
                results.append(result)
                
            except Exception as e:
                self.logger.error(f"Benchmark {benchmark_name} failed: {e}")
                continue
        
        # Generate comprehensive report
        self._generate_comprehensive_report(suite, results)
        
        return results
    
    def _warmup_wallet_generation(self, wallet_count: int):
        """Warmup wallet generation operations."""
        self.logger.info("Warming up wallet generation...")
        try:
            self._generate_wallets(wallet_count // 10)  # Generate fewer wallets for warmup
        except Exception as e:
            self.logger.warning(f"Warmup failed: {e}")
    
    def _warmup_encryption(self, data_size_mb: int):
        """Warmup encryption operations."""
        self.logger.info("Warming up encryption...")
        try:
            self._encrypt_data(data_size_mb // 10)  # Encrypt smaller data for warmup
        except Exception as e:
            self.logger.warning(f"Warmup failed: {e}")
    
    def _warmup_api(self, endpoint: str):
        """Warmup API operations."""
        self.logger.info("Warming up API...")
        try:
            self._run_concurrent_api_requests(endpoint, 5)
        except Exception as e:
            self.logger.warning(f"Warmup failed: {e}")
    
    def _warmup_system(self):
        """Warmup system operations."""
        self.logger.info("Warming up system...")
        try:
            self._run_stress_operations(10)
        except Exception as e:
            self.logger.warning(f"Warmup failed: {e}")
    
    def _generate_wallets(self, count: int) -> int:
        """Generate a specified number of wallets."""
        # This would typically call the actual wallet generation function
        # For benchmarking, we'll simulate the operation
        time.sleep(0.1 * count)  # Simulate generation time
        return count
    
    def _encrypt_data(self, size_mb: int) -> bytes:
        """Encrypt data of specified size."""
        # This would typically call the actual encryption function
        # For benchmarking, we'll simulate the operation
        time.sleep(0.05 * size_mb)  # Simulate encryption time
        return b"encrypted_data" * size_mb
    
    def _run_concurrent_api_requests(self, endpoint: str, count: int) -> List[Dict[str, Any]]:
        """Run concurrent API requests."""
        # This would typically make actual API requests
        # For benchmarking, we'll simulate the operation
        time.sleep(0.01 * count)  # Simulate request time
        return [{"status": "success"} for _ in range(count)]
    
    def _run_stress_operations(self, batch_size: int):
        """Run stress operations."""
        # This would typically run various stress operations
        # For benchmarking, we'll simulate the operation
        time.sleep(0.2 * batch_size)  # Simulate stress time
    
    def _capture_system_metrics(self) -> Dict[str, float]:
        """Capture current system metrics."""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=0.1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_mb = memory.used / (1024 * 1024)
            
            # Disk I/O
            disk_io = psutil.disk_io_counters()
            disk_io_bytes = disk_io.read_bytes + disk_io.write_bytes if disk_io else 0
            
            # Network I/O
            network_io = psutil.net_io_counters()
            network_io_bytes = network_io.bytes_sent + network_io.bytes_recv if network_io else 0
            
            return {
                'cpu_percent': cpu_percent,
                'memory_mb': memory_mb,
                'disk_io_bytes': disk_io_bytes,
                'network_io_bytes': network_io_bytes
            }
            
        except Exception as e:
            self.logger.error(f"Failed to capture system metrics: {e}")
            return {
                'cpu_percent': 0.0,
                'memory_mb': 0.0,
                'disk_io_bytes': 0,
                'network_io_bytes': 0
            }
    
    def _calculate_metrics(self, baseline: Dict[str, float], final: Dict[str, float],
                          duration: float, operation_count: int) -> Dict[str, float]:
        """Calculate performance metrics from baseline and final measurements."""
        try:
            # CPU usage change
            cpu_change = final['cpu_percent'] - baseline['cpu_percent']
            
            # Memory usage change
            memory_change = final['memory_mb'] - baseline['memory_mb']
            
            # Disk I/O change
            disk_io_change = final['disk_io_bytes'] - baseline['disk_io_bytes']
            
            # Network I/O change
            network_io_change = final['network_io_bytes'] - baseline['network_io_bytes']
            
            # Response time
            response_time_ms = duration * 1000
            
            # Throughput
            throughput_per_second = operation_count / duration if duration > 0 else 0
            
            # Error rate (simulated)
            error_rate = 0.0  # Would be calculated from actual results
            
            return {
                'cpu_usage_percent': cpu_change,
                'memory_usage_mb': memory_change,
                'disk_io_bytes': disk_io_change,
                'network_io_bytes': network_io_change,
                'response_time_ms': response_time_ms,
                'throughput_per_second': throughput_per_second,
                'error_rate': error_rate
            }
            
        except Exception as e:
            self.logger.error(f"Failed to calculate metrics: {e}")
            return {}
    
    def _average_metrics(self, metrics_list: List[Dict[str, float]]) -> Dict[str, float]:
        """Calculate average metrics from a list of metric dictionaries."""
        if not metrics_list:
            return {}
        
        avg_metrics = {}
        
        # Get all metric keys
        all_keys = set()
        for metrics in metrics_list:
            all_keys.update(metrics.keys())
        
        # Calculate averages for each metric
        for key in all_keys:
            values = [metrics.get(key, 0) for metrics in metrics_list if key in metrics]
            if values:
                avg_metrics[key] = statistics.mean(values)
        
        return avg_metrics
    
    def _generate_comprehensive_report(self, suite: BenchmarkSuite, results: List[BenchmarkResult]):
        """Generate comprehensive benchmark report."""
        try:
            # Create report directory
            report_dir = self.output_dir / f"suite_{suite.suite_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            report_dir.mkdir(exist_ok=True)
            
            # Save detailed results
            if self.save_detailed_results:
                self._save_detailed_results(report_dir, suite, results)
            
            # Generate plots
            if self.enable_plots:
                self._generate_plots(report_dir, results)
            
            # Generate summary report
            self._generate_summary_report(report_dir, suite, results)
            
            self.logger.info(f"Comprehensive report generated in: {report_dir}")
            
        except Exception as e:
            self.logger.error(f"Failed to generate comprehensive report: {e}")
    
    def _save_detailed_results(self, report_dir: Path, suite: BenchmarkSuite, results: List[BenchmarkResult]):
        """Save detailed benchmark results."""
        try:
            # Save results as JSON
            results_file = report_dir / "detailed_results.json"
            with open(results_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'suite': asdict(suite),
                    'results': [asdict(result) for result in results],
                    'metrics_history': self.metrics_history
                }, f, indent=2, default=str)
            
            # Save metrics history as CSV
            if self.metrics_history:
                metrics_file = report_dir / "metrics_history.csv"
                df = pd.DataFrame(self.metrics_history)
                df.to_csv(metrics_file, index=False)
                
        except Exception as e:
            self.logger.error(f"Failed to save detailed results: {e}")
    
    def _generate_plots(self, report_dir: Path, results: List[BenchmarkResult]):
        """Generate performance plots."""
        try:
            # Create plots directory
            plots_dir = report_dir / "plots"
            plots_dir.mkdir(exist_ok=True)
            
            # Response time comparison
            self._plot_response_time_comparison(plots_dir, results)
            
            # Throughput comparison
            self._plot_throughput_comparison(plots_dir, results)
            
            # Resource usage over time
            self._plot_resource_usage_over_time(plots_dir)
            
            # Performance trends
            self._plot_performance_trends(plots_dir, results)
            
        except Exception as e:
            self.logger.error(f"Failed to generate plots: {e}")
    
    def _plot_response_time_comparison(self, plots_dir: Path, results: List[BenchmarkResult]):
        """Plot response time comparison across benchmarks."""
        try:
            names = [result.benchmark_name for result in results]
            response_times = [result.metrics.get('response_time_ms', 0) for result in results]
            
            plt.figure(figsize=(12, 6))
            plt.bar(names, response_times, color='skyblue')
            plt.title('Response Time Comparison Across Benchmarks')
            plt.xlabel('Benchmark')
            plt.ylabel('Response Time (ms)')
            plt.xticks(rotation=45, ha='right')
            plt.tight_layout()
            
            plot_file = plots_dir / "response_time_comparison.png"
            plt.savefig(plot_file, dpi=300, bbox_inches='tight')
            plt.close()
            
        except Exception as e:
            self.logger.error(f"Failed to generate response time plot: {e}")
    
    def _plot_throughput_comparison(self, plots_dir: Path, results: List[BenchmarkResult]):
        """Plot throughput comparison across benchmarks."""
        try:
            names = [result.benchmark_name for result in results]
            throughputs = [result.metrics.get('throughput_per_second', 0) for result in results]
            
            plt.figure(figsize=(12, 6))
            plt.bar(names, throughputs, color='lightgreen')
            plt.title('Throughput Comparison Across Benchmarks')
            plt.xlabel('Benchmark')
            plt.ylabel('Throughput (operations/second)')
            plt.xticks(rotation=45, ha='right')
            plt.tight_layout()
            
            plot_file = plots_dir / "throughput_comparison.png"
            plt.savefig(plot_file, dpi=300, bbox_inches='tight')
            plt.close()
            
        except Exception as e:
            self.logger.error(f"Failed to generate throughput plot: {e}")
    
    def _plot_resource_usage_over_time(self, plots_dir: Path):
        """Plot resource usage over time."""
        try:
            if not self.metrics_history:
                return
            
            # Extract time series data
            timestamps = [entry['timestamp'] for entry in self.metrics_history]
            cpu_usage = [entry['metrics'].get('cpu_usage_percent', 0) for entry in self.metrics_history]
            memory_usage = [entry['metrics'].get('memory_usage_mb', 0) for entry in self.metrics_history]
            
            plt.figure(figsize=(15, 8))
            
            # CPU usage
            plt.subplot(2, 1, 1)
            plt.plot(timestamps, cpu_usage, 'b-', label='CPU Usage (%)')
            plt.title('CPU Usage Over Time')
            plt.ylabel('CPU Usage (%)')
            plt.legend()
            plt.grid(True, alpha=0.3)
            
            # Memory usage
            plt.subplot(2, 1, 2)
            plt.plot(timestamps, memory_usage, 'r-', label='Memory Usage (MB)')
            plt.title('Memory Usage Over Time')
            plt.xlabel('Time')
            plt.ylabel('Memory Usage (MB)')
            plt.legend()
            plt.grid(True, alpha=0.3)
            
            plt.tight_layout()
            
            plot_file = plots_dir / "resource_usage_over_time.png"
            plt.savefig(plot_file, dpi=300, bbox_inches='tight')
            plt.close()
            
        except Exception as e:
            self.logger.error(f"Failed to generate resource usage plot: {e}")
    
    def _plot_performance_trends(self, plots_dir: Path, results: List[BenchmarkResult]):
        """Plot performance trends across iterations."""
        try:
            for result in results:
                if 'individual_metrics' in result.metadata:
                    individual_metrics = result.metadata['individual_metrics']
                    
                    if len(individual_metrics) > 1:
                        iterations = list(range(1, len(individual_metrics) + 1))
                        response_times = [m.get('response_time_ms', 0) for m in individual_metrics]
                        throughputs = [m.get('throughput_per_second', 0) for m in individual_metrics]
                        
                        plt.figure(figsize=(15, 6))
                        
                        # Response time trend
                        plt.subplot(1, 2, 1)
                        plt.plot(iterations, response_times, 'bo-', label='Response Time')
                        plt.title(f'{result.benchmark_name} - Response Time Trend')
                        plt.xlabel('Iteration')
                        plt.ylabel('Response Time (ms)')
                        plt.legend()
                        plt.grid(True, alpha=0.3)
                        
                        # Throughput trend
                        plt.subplot(1, 2, 2)
                        plt.plot(iterations, throughputs, 'go-', label='Throughput')
                        plt.title(f'{result.benchmark_name} - Throughput Trend')
                        plt.xlabel('Iteration')
                        plt.ylabel('Throughput (ops/sec)')
                        plt.legend()
                        plt.grid(True, alpha=0.3)
                        
                        plt.tight_layout()
                        
                        plot_file = plots_dir / f"{result.benchmark_name}_trends.png"
                        plt.savefig(plot_file, dpi=300, bbox_inches='tight')
                        plt.close()
                        
        except Exception as e:
            self.logger.error(f"Failed to generate performance trends plots: {e}")
    
    def _generate_summary_report(self, report_dir: Path, suite: BenchmarkSuite, results: List[BenchmarkResult]):
        """Generate summary benchmark report."""
        try:
            summary_file = report_dir / "summary_report.md"
            
            with open(summary_file, 'w', encoding='utf-8') as f:
                f.write(f"# Benchmark Suite Summary Report\n\n")
                f.write(f"**Suite Name:** {suite.suite_name}\n")
                f.write(f"**Description:** {suite.description}\n")
                f.write(f"**Created:** {suite.created_at.isoformat()}\n")
                f.write(f"**Completed:** {datetime.now().isoformat()}\n\n")
                
                f.write(f"## Benchmark Results Summary\n\n")
                
                for result in results:
                    f.write(f"### {result.benchmark_name}\n")
                    f.write(f"- **Duration:** {result.duration_seconds:.2f} seconds\n")
                    f.write(f"- **Iterations:** {result.iterations}\n")
                    f.write(f"- **Response Time:** {result.metrics.get('response_time_ms', 0):.2f} ms\n")
                    f.write(f"- **Throughput:** {result.metrics.get('throughput_per_second', 0):.2f} ops/sec\n")
                    f.write(f"- **CPU Usage:** {result.metrics.get('cpu_usage_percent', 0):.2f}%\n")
                    f.write(f"- **Memory Usage:** {result.metrics.get('memory_usage_mb', 0):.2f} MB\n\n")
                
                f.write(f"## Recommendations\n\n")
                
                # Generate recommendations based on results
                self._generate_recommendations(f, results)
                
        except Exception as e:
            self.logger.error(f"Failed to generate summary report: {e}")
    
    def _generate_recommendations(self, file_handle, results: List[BenchmarkResult]):
        """Generate recommendations based on benchmark results."""
        try:
            file_handle.write("### Performance Recommendations\n\n")
            
            for result in results:
                response_time = result.metrics.get('response_time_ms', 0)
                throughput = result.metrics.get('throughput_per_second', 0)
                cpu_usage = result.metrics.get('cpu_usage_percent', 0)
                memory_usage = result.metrics.get('memory_usage_mb', 0)
                
                file_handle.write(f"#### {result.benchmark_name}\n")
                
                if response_time > 1000:
                    file_handle.write(f"- **High Response Time:** Consider optimizing algorithms or increasing resources\n")
                
                if throughput < 10:
                    file_handle.write(f"- **Low Throughput:** Review batch processing and concurrency settings\n")
                
                if cpu_usage > 80:
                    file_handle.write(f"- **High CPU Usage:** Consider load balancing or scaling horizontally\n")
                
                if memory_usage > 1000:
                    file_handle.write(f"- **High Memory Usage:** Review memory management and caching strategies\n")
                
                file_handle.write("\n")
                
        except Exception as e:
            self.logger.error(f"Failed to generate recommendations: {e}")
    
    def get_benchmark_results(self) -> List[BenchmarkResult]:
        """Get all benchmark results."""
        return self.results.copy()
    
    def get_metrics_history(self) -> List[Dict[str, Any]]:
        """Get metrics history."""
        return self.metrics_history.copy()
    
    def clear_results(self):
        """Clear all benchmark results."""
        self.results.clear()
        self.metrics_history.clear()
        self.logger.info("Benchmark results cleared")
    
    def export_results(self, format: str = "json", file_path: str = None) -> str:
        """Export benchmark results to file."""
        if not file_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_path = f"benchmark_results_{timestamp}.{format}"
        
        try:
            export_data = {
                'results': [asdict(result) for result in self.results],
                'metrics_history': self.metrics_history
            }
            
            if format.lower() == "json":
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(export_data, f, indent=2, default=str)
            else:
                raise ValueError(f"Unsupported format: {format}")
            
            self.logger.info(f"Benchmark results exported to {file_path}")
            return file_path
            
        except Exception as e:
            self.logger.error(f"Failed to export results: {e}")
            raise


# Convenience functions
def create_benchmark_runner(output_dir: str = "benchmarks") -> BenchmarkRunner:
    """Create a new benchmark runner instance."""
    return BenchmarkRunner(output_dir)


def create_sample_benchmark_suite() -> BenchmarkSuite:
    """Create a sample benchmark suite."""
    return BenchmarkSuite(
        suite_name="comprehensive_performance",
        description="Comprehensive performance testing suite for MetaWalletGen CLI",
        benchmarks=[
            "wallet_generation_100",
            "wallet_generation_500",
            "encryption_10",
            "encryption_50",
            "api_performance_wallet_create",
            "system_stress_5"
        ],
        iterations=5,
        warmup_iterations=2,
        timeout_seconds=3600,
        created_at=datetime.now(timezone.utc)
    )


# Example usage
if __name__ == "__main__":
    # Example: Run comprehensive benchmark suite
    runner = create_benchmark_runner()
    
    # Create and run benchmark suite
    suite = create_sample_benchmark_suite()
    results = runner.run_comprehensive_benchmark_suite(suite)
    
    print(f"Benchmark suite completed: {len(results)} benchmarks run")
    
    # Export results
    try:
        export_file = runner.export_results()
        print(f"Results exported to: {export_file}")
    except Exception as e:
        print(f"Export failed: {e}")
