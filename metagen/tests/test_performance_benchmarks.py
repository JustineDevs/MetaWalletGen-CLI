#!/usr/bin/env python3
"""
MetaWalletGen CLI - Performance Benchmark Suite

This module provides comprehensive performance testing and benchmarking
of the MetaWalletGen CLI system under various load conditions.
"""

import time
import json
import statistics
import psutil
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import queue

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from metagen.core.wallet_generator import WalletGenerator
from metagen.core.encryption import EncryptionManager
from metagen.core.storage_manager import StorageManager
from metagen.performance.monitor import PerformanceMonitor
from metagen.performance.cache import CacheManager
from metagen.performance.load_balancer import LoadBalancer
from metagen.performance.benchmark import BenchmarkSuite

@dataclass
class BenchmarkResult:
    """Result of a benchmark test"""
    test_name: str
    duration: float
    success: bool
    error: str = None
    metadata: Dict[str, Any] = None

@dataclass
class PerformanceMetrics:
    """Performance metrics for a benchmark"""
    cpu_usage: float
    memory_usage: float
    disk_io: float
    network_io: float
    timestamp: float

class PerformanceBenchmarkSuite:
    """Comprehensive performance benchmark suite"""
    
    def __init__(self, output_dir: str = "benchmark_results"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Initialize components
        self.wallet_generator = WalletGenerator()
        self.encryption_manager = EncryptionManager()
        self.storage_manager = StorageManager()
        self.performance_monitor = PerformanceMonitor()
        self.cache_manager = CacheManager()
        self.load_balancer = LoadBalancer()
        self.benchmark_suite = BenchmarkSuite()
        
        # Results storage
        self.results: List[BenchmarkResult] = []
        self.performance_metrics: List[PerformanceMetrics] = []
        
        # Benchmark configuration
        self.config = {
            'wallet_generation': {
                'counts': [1, 10, 100, 1000],
                'iterations': 5
            },
            'encryption': {
                'data_sizes': [1, 10, 100, 1000],  # KB
                'iterations': 5
            },
            'storage': {
                'formats': ['json', 'csv', 'yaml'],
                'iterations': 3
            },
            'cache': {
                'entry_counts': [100, 1000, 10000],
                'iterations': 5
            },
            'load_balancing': {
                'worker_counts': [2, 5, 10, 20],
                'iterations': 5
            }
        }
    
    def run_all_benchmarks(self) -> Dict[str, Any]:
        """Run all benchmark tests"""
        print("🚀 Starting MetaWalletGen CLI Performance Benchmark Suite")
        print("=" * 70)
        
        start_time = time.time()
        
        # Run individual benchmark categories
        benchmarks = {
            'wallet_generation': self.benchmark_wallet_generation,
            'encryption': self.benchmark_encryption,
            'storage': self.benchmark_storage,
            'caching': self.benchmark_caching,
            'load_balancing': self.benchmark_load_balancing,
            'system_performance': self.benchmark_system_performance,
            'stress_testing': self.benchmark_stress_testing
        }
        
        all_results = {}
        
        for benchmark_name, benchmark_func in benchmarks.items():
            print(f"\n📊 Running {benchmark_name.replace('_', ' ').title()} Benchmark...")
            try:
                result = benchmark_func()
                all_results[benchmark_name] = result
                print(f"✅ {benchmark_name.replace('_', ' ').title()} completed successfully")
            except Exception as e:
                print(f"❌ {benchmark_name.replace('_', ' ').title()} failed: {e}")
                all_results[benchmark_name] = {'error': str(e)}
        
        total_time = time.time() - start_time
        
        # Generate comprehensive report
        report = self.generate_comprehensive_report(all_results, total_time)
        
        # Save results
        self.save_benchmark_results(report)
        
        print(f"\n🎉 All benchmarks completed in {total_time:.2f} seconds")
        print(f"📁 Results saved to: {self.output_dir}")
        
        return report
    
    def benchmark_wallet_generation(self) -> Dict[str, Any]:
        """Benchmark wallet generation performance"""
        results = {}
        
        for count in self.config['wallet_generation']['counts']:
            durations = []
            
            for i in range(self.config['wallet_generation']['iterations']):
                start_time = time.time()
                
                try:
                    wallets = self.wallet_generator.generate_wallets(count)
                    duration = time.time() - start_time
                    
                    if len(wallets) == count:
                        durations.append(duration)
                        self.record_performance_metrics()
                    else:
                        print(f"Warning: Expected {count} wallets, got {len(wallets)}")
                        
                except Exception as e:
                    print(f"Error generating {count} wallets: {e}")
                    continue
            
            if durations:
                results[f'{count}_wallets'] = {
                    'count': count,
                    'iterations': len(durations),
                    'avg_duration': statistics.mean(durations),
                    'min_duration': min(durations),
                    'max_duration': max(durations),
                    'std_deviation': statistics.stdev(durations) if len(durations) > 1 else 0,
                    'wallets_per_second': count / statistics.mean(durations)
                }
        
        return results
    
    def benchmark_encryption(self) -> Dict[str, Any]:
        """Benchmark encryption/decryption performance"""
        results = {}
        
        for size_kb in self.config['encryption']['data_sizes']:
            # Generate test data
            data_size = size_kb * 1024
            test_data = 'x' * data_size
            password = "benchmark_password_123"
            
            encrypt_durations = []
            decrypt_durations = []
            
            for i in range(self.config['encryption']['iterations']):
                # Test encryption
                start_time = time.time()
                try:
                    encrypted_data = self.encryption_manager.encrypt_data(test_data, password)
                    encrypt_duration = time.time() - start_time
                    encrypt_durations.append(encrypt_duration)
                    
                    # Test decryption
                    start_time = time.time()
                    decrypted_data = self.encryption_manager.decrypt_data(encrypted_data, password)
                    decrypt_duration = time.time() - start_time
                    decrypt_durations.append(decrypt_duration)
                    
                    # Verify data integrity
                    if decrypted_data != test_data:
                        print(f"Warning: Data integrity check failed for {size_kb}KB")
                        
                except Exception as e:
                    print(f"Error in encryption benchmark for {size_kb}KB: {e}")
                    continue
            
            if encrypt_durations and decrypt_durations:
                results[f'{size_kb}KB'] = {
                    'data_size_kb': size_kb,
                    'iterations': len(encrypt_durations),
                    'encryption': {
                        'avg_duration': statistics.mean(encrypt_durations),
                        'min_duration': min(encrypt_durations),
                        'max_duration': max(encrypt_durations),
                        'throughput_mbps': (size_kb / 1024) / statistics.mean(encrypt_durations)
                    },
                    'decryption': {
                        'avg_duration': statistics.mean(decrypt_durations),
                        'min_duration': min(decrypt_durations),
                        'max_duration': max(decrypt_durations),
                        'throughput_mbps': (size_kb / 1024) / statistics.mean(decrypt_durations)
                    }
                }
        
        return results
    
    def benchmark_storage(self) -> Dict[str, Any]:
        """Benchmark storage operations"""
        results = {}
        
        # Generate test data
        test_wallets = []
        for i in range(100):
            test_wallets.append({
                'address': f'0x{i:040x}',
                'private_key': f'0x{i:064x}',
                'mnemonic': f'test mnemonic phrase {i} with some additional text',
                'network': 'mainnet',
                'created_at': time.time()
            })
        
        for format_type in self.config['storage']['formats']:
            durations = []
            file_sizes = []
            
            for i in range(self.config['storage']['iterations']):
                temp_file = self.output_dir / f'test_storage_{format_type}_{i}.{format_type}'
                
                try:
                    # Test save performance
                    start_time = time.time()
                    self.storage_manager.save_wallets(test_wallets, str(temp_file), format=format_type)
                    save_duration = time.time() - start_time
                    
                    # Get file size
                    file_size = temp_file.stat().st_size if temp_file.exists() else 0
                    file_sizes.append(file_size)
                    
                    # Test load performance
                    start_time = time.time()
                    loaded_wallets = self.storage_manager.load_wallets(str(temp_file), format=format_type)
                    load_duration = time.time() - start_time
                    
                    total_duration = save_duration + load_duration
                    durations.append(total_duration)
                    
                    # Verify data integrity
                    if len(loaded_wallets) != len(test_wallets):
                        print(f"Warning: Data integrity check failed for {format_type}")
                    
                    # Clean up
                    temp_file.unlink(missing_ok=True)
                    
                except Exception as e:
                    print(f"Error in storage benchmark for {format_type}: {e}")
                    continue
            
            if durations:
                results[format_type] = {
                    'format': format_type,
                    'iterations': len(durations),
                    'avg_duration': statistics.mean(durations),
                    'min_duration': min(durations),
                    'max_duration': max(durations),
                    'avg_file_size_kb': statistics.mean(file_sizes) / 1024,
                    'throughput_wallets_per_second': len(test_wallets) / statistics.mean(durations)
                }
        
        return results
    
    def benchmark_caching(self) -> Dict[str, Any]:
        """Benchmark caching system performance"""
        results = {}
        
        for entry_count in self.config['cache']['entry_counts']:
            durations = []
            
            for i in range(self.config['cache']['iterations']):
                # Clear cache
                self.cache_manager.clear()
                
                start_time = time.time()
                
                try:
                    # Fill cache
                    for j in range(entry_count):
                        self.cache_manager.set(f"key_{j}", f"value_{j}", ttl=60)
                    
                    # Read from cache
                    for j in range(entry_count):
                        value = self.cache_manager.get(f"key_{j}")
                        if value != f"value_{j}":
                            print(f"Warning: Cache read failed for key_{j}")
                    
                    duration = time.time() - start_time
                    durations.append(duration)
                    
                except Exception as e:
                    print(f"Error in cache benchmark for {entry_count} entries: {e}")
                    continue
            
            if durations:
                results[f'{entry_count}_entries'] = {
                    'entry_count': entry_count,
                    'iterations': len(durations),
                    'avg_duration': statistics.mean(durations),
                    'min_duration': min(durations),
                    'max_duration': max(durations),
                    'operations_per_second': (entry_count * 2) / statistics.mean(durations)  # write + read
                }
        
        return results
    
    def benchmark_load_balancing(self) -> Dict[str, Any]:
        """Benchmark load balancing performance"""
        results = {}
        
        for worker_count in self.config['load_balancing']['worker_counts']:
            durations = []
            
            for i in range(self.config['load_balancing']['iterations']):
                # Reset load balancer
                self.load_balancer = LoadBalancer()
                
                start_time = time.time()
                
                try:
                    # Add workers
                    for j in range(worker_count):
                        self.load_balancer.add_worker(f"worker_{j}", capacity=100)
                    
                    # Simulate load balancing
                    strategies = ['round_robin', 'least_connections', 'random']
                    for strategy in strategies:
                        for k in range(1000):  # 1000 requests
                            worker = self.load_balancer.get_next_worker(strategy)
                            if worker:
                                # Simulate work
                                worker.current_connections += 1
                    
                    duration = time.time() - start_time
                    durations.append(duration)
                    
                except Exception as e:
                    print(f"Error in load balancing benchmark for {worker_count} workers: {e}")
                    continue
            
            if durations:
                results[f'{worker_count}_workers'] = {
                    'worker_count': worker_count,
                    'iterations': len(durations),
                    'avg_duration': statistics.mean(durations),
                    'min_duration': min(durations),
                    'max_duration': max(durations),
                    'requests_per_second': 3000 / statistics.mean(durations)  # 3 strategies * 1000 requests
                }
        
        return results
    
    def benchmark_system_performance(self) -> Dict[str, Any]:
        """Benchmark system performance monitoring"""
        results = {}
        
        # Test system metrics collection
        metric_durations = []
        for i in range(10):
            start_time = time.time()
            
            try:
                cpu_usage = self.performance_monitor.get_cpu_usage()
                memory_usage = self.performance_monitor.get_memory_usage()
                disk_usage = self.performance_monitor.get_disk_usage()
                
                duration = time.time() - start_time
                metric_durations.append(duration)
                
                # Verify metrics are reasonable
                if not (0 <= cpu_usage <= 100):
                    print(f"Warning: CPU usage out of range: {cpu_usage}")
                if not (0 <= memory_usage <= 100):
                    print(f"Warning: Memory usage out of range: {memory_usage}")
                if not (0 <= disk_usage <= 100):
                    print(f"Warning: Disk usage out of range: {disk_usage}")
                    
            except Exception as e:
                print(f"Error collecting system metrics: {e}")
                continue
        
        if metric_durations:
            results['system_metrics'] = {
                'iterations': len(metric_durations),
                'avg_duration': statistics.mean(metric_durations),
                'min_duration': min(metric_durations),
                'max_duration': max(metric_durations),
                'metrics_per_second': 1 / statistics.mean(metric_durations)
            }
        
        return results
    
    def benchmark_stress_testing(self) -> Dict[str, Any]:
        """Benchmark system under stress conditions"""
        results = {}
        
        # Test concurrent wallet generation
        print("   Testing concurrent wallet generation...")
        concurrent_results = self._stress_test_concurrent_wallets()
        results['concurrent_wallets'] = concurrent_results
        
        # Test memory pressure
        print("   Testing memory pressure...")
        memory_results = self._stress_test_memory()
        results['memory_pressure'] = memory_results
        
        # Test cache pressure
        print("   Testing cache pressure...")
        cache_results = self._stress_test_cache()
        results['cache_pressure'] = cache_results
        
        return results
    
    def _stress_test_concurrent_wallets(self) -> Dict[str, Any]:
        """Test concurrent wallet generation"""
        results = {}
        
        # Test different concurrency levels
        concurrency_levels = [1, 5, 10, 20]
        
        for level in concurrency_levels:
            durations = []
            
            for i in range(3):  # 3 iterations per level
                start_time = time.time()
                
                try:
                    with ThreadPoolExecutor(max_workers=level) as executor:
                        futures = []
                        for j in range(level):
                            future = executor.submit(self.wallet_generator.generate_wallets, 10)
                            futures.append(future)
                        
                        # Wait for all to complete
                        for future in as_completed(futures):
                            wallets = future.result()
                            if len(wallets) != 10:
                                print(f"Warning: Expected 10 wallets, got {len(wallets)}")
                    
                    duration = time.time() - start_time
                    durations.append(duration)
                    
                except Exception as e:
                    print(f"Error in concurrent wallet test for level {level}: {e}")
                    continue
            
            if durations:
                results[f'{level}_workers'] = {
                    'concurrency_level': level,
                    'iterations': len(durations),
                    'avg_duration': statistics.mean(durations),
                    'wallets_per_second': (level * 10) / statistics.mean(durations)
                }
        
        return results
    
    def _stress_test_memory(self) -> Dict[str, Any]:
        """Test system under memory pressure"""
        results = {}
        
        # Generate large amounts of data to stress memory
        memory_sizes = [10, 50, 100]  # MB
        
        for size_mb in memory_sizes:
            durations = []
            
            for i in range(3):
                start_time = time.time()
                
                try:
                    # Generate large data
                    large_data = []
                    for j in range(size_mb * 1024):  # Convert MB to KB
                        large_data.append('x' * 1024)  # 1KB strings
                    
                    # Perform operations on large data
                    encrypted_data = []
                    for chunk in large_data:
                        encrypted = self.encryption_manager.encrypt_data(chunk, "test_password")
                        encrypted_data.append(encrypted)
                    
                    duration = time.time() - start_time
                    durations.append(duration)
                    
                    # Clear memory
                    large_data.clear()
                    encrypted_data.clear()
                    
                except Exception as e:
                    print(f"Error in memory stress test for {size_mb}MB: {e}")
                    continue
            
            if durations:
                results[f'{size_mb}MB'] = {
                    'memory_size_mb': size_mb,
                    'iterations': len(durations),
                    'avg_duration': statistics.mean(durations),
                    'throughput_mbps': size_mb / statistics.mean(durations)
                }
        
        return results
    
    def _stress_test_cache(self) -> Dict[str, Any]:
        """Test cache system under pressure"""
        results = {}
        
        # Test cache with many entries and frequent access
        entry_counts = [1000, 5000, 10000]
        
        for count in entry_counts:
            durations = []
            
            for i in range(3):
                start_time = time.time()
                
                try:
                    # Fill cache
                    for j in range(count):
                        self.cache_manager.set(f"stress_key_{j}", f"stress_value_{j}", ttl=60)
                    
                    # Access cache randomly
                    import random
                    for j in range(count * 2):  # 2x access operations
                        key = f"stress_key_{random.randint(0, count-1)}"
                        value = self.cache_manager.get(key)
                    
                    duration = time.time() - start_time
                    durations.append(duration)
                    
                    # Clear cache
                    self.cache_manager.clear()
                    
                except Exception as e:
                    print(f"Error in cache stress test for {count} entries: {e}")
                    continue
            
            if durations:
                results[f'{count}_entries'] = {
                    'entry_count': count,
                    'iterations': len(durations),
                    'avg_duration': statistics.mean(durations),
                    'operations_per_second': (count * 3) / statistics.mean(durations)  # write + read + clear
                }
        
        return results
    
    def record_performance_metrics(self):
        """Record current performance metrics"""
        try:
            cpu_usage = self.performance_monitor.get_cpu_usage()
            memory_usage = self.performance_monitor.get_memory_usage()
            
            # Get disk I/O (simplified)
            disk_io = 0.0
            try:
                disk_stats = psutil.disk_io_counters()
                if disk_stats:
                    disk_io = (disk_stats.read_bytes + disk_stats.write_bytes) / 1024 / 1024  # MB
            except:
                pass
            
            # Get network I/O (simplified)
            network_io = 0.0
            try:
                net_stats = psutil.net_io_counters()
                if net_stats:
                    network_io = (net_stats.bytes_sent + net_stats.bytes_recv) / 1024 / 1024  # MB
            except:
                pass
            
            metrics = PerformanceMetrics(
                cpu_usage=cpu_usage,
                memory_usage=memory_usage,
                disk_io=disk_io,
                network_io=network_io,
                timestamp=time.time()
            )
            
            self.performance_metrics.append(metrics)
            
        except Exception as e:
            print(f"Warning: Could not record performance metrics: {e}")
    
    def generate_comprehensive_report(self, results: Dict[str, Any], total_time: float) -> Dict[str, Any]:
        """Generate comprehensive benchmark report"""
        report = {
            'metadata': {
                'timestamp': time.time(),
                'total_benchmark_time': total_time,
                'system_info': self._get_system_info(),
                'benchmark_config': self.config
            },
            'summary': {
                'total_benchmarks': len(results),
                'successful_benchmarks': len([r for r in results.values() if 'error' not in r]),
                'failed_benchmarks': len([r for r in results.values() if 'error' in r])
            },
            'results': results,
            'performance_metrics': [
                {
                    'cpu_usage': m.cpu_usage,
                    'memory_usage': m.memory_usage,
                    'disk_io_mb': m.disk_io,
                    'network_io_mb': m.network_io,
                    'timestamp': m.timestamp
                }
                for m in self.performance_metrics
            ],
            'recommendations': self._generate_recommendations(results)
        }
        
        return report
    
    def _get_system_info(self) -> Dict[str, Any]:
        """Get system information"""
        try:
            return {
                'platform': sys.platform,
                'python_version': sys.version,
                'cpu_count': psutil.cpu_count(),
                'memory_total_gb': psutil.virtual_memory().total / 1024 / 1024 / 1024,
                'disk_total_gb': psutil.disk_usage('/').total / 1024 / 1024 / 1024
            }
        except Exception:
            return {'error': 'Could not retrieve system info'}
    
    def _generate_recommendations(self, results: Dict[str, Any]) -> List[str]:
        """Generate performance recommendations based on results"""
        recommendations = []
        
        # Analyze wallet generation performance
        if 'wallet_generation' in results:
            wallet_results = results['wallet_generation']
            for key, result in wallet_results.items():
                if isinstance(result, dict) and 'wallets_per_second' in result:
                    if result['wallets_per_second'] < 10:
                        recommendations.append(f"Consider optimizing wallet generation for {key} (current: {result['wallets_per_second']:.1f} wallets/sec)")
        
        # Analyze encryption performance
        if 'encryption' in results:
            encryption_results = results['encryption']
            for key, result in encryption_results.items():
                if isinstance(result, dict) and 'encryption' in result:
                    throughput = result['encryption']['throughput_mbps']
                    if throughput < 1.0:
                        recommendations.append(f"Consider optimizing encryption for {key} (current: {throughput:.2f} MB/s)")
        
        # Analyze cache performance
        if 'caching' in results:
            cache_results = results['caching']
            for key, result in cache_results.items():
                if isinstance(result, dict) and 'operations_per_second' in result:
                    if result['operations_per_second'] < 1000:
                        recommendations.append(f"Consider optimizing cache operations for {key} (current: {result['operations_per_second']:.0f} ops/sec)")
        
        # General recommendations
        if not recommendations:
            recommendations.append("All performance benchmarks are within acceptable ranges")
        
        return recommendations
    
    def save_benchmark_results(self, report: Dict[str, Any]):
        """Save benchmark results to files"""
        timestamp = int(time.time())
        
        # Save JSON report
        json_file = self.output_dir / f'benchmark_report_{timestamp}.json'
        with open(json_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        # Save performance metrics as CSV
        csv_file = self.output_dir / f'performance_metrics_{timestamp}.csv'
        with open(csv_file, 'w') as f:
            f.write("timestamp,cpu_usage,memory_usage,disk_io_mb,network_io_mb\n")
            for metrics in report['performance_metrics']:
                f.write(f"{metrics['timestamp']},{metrics['cpu_usage']},{metrics['memory_usage']},{metrics['disk_io_mb']},{metrics['network_io_mb']}\n")
        
        # Save summary report
        summary_file = self.output_dir / f'benchmark_summary_{timestamp}.txt'
        with open(summary_file, 'w') as f:
            f.write("MetaWalletGen CLI Performance Benchmark Summary\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(timestamp))}\n")
            f.write(f"Total Benchmark Time: {report['metadata']['total_benchmark_time']:.2f} seconds\n")
            f.write(f"Total Benchmarks: {report['summary']['total_benchmarks']}\n")
            f.write(f"Successful: {report['summary']['successful_benchmarks']}\n")
            f.write(f"Failed: {report['summary']['failed_benchmarks']}\n\n")
            
            f.write("Key Performance Metrics:\n")
            f.write("-" * 25 + "\n")
            
            # Add key metrics
            if 'wallet_generation' in report['results']:
                wallet_results = report['results']['wallet_generation']
                for key, result in wallet_results.items():
                    if isinstance(result, dict) and 'wallets_per_second' in result:
                        f.write(f"Wallet Generation ({key}): {result['wallets_per_second']:.1f} wallets/sec\n")
            
            if 'encryption' in report['results']:
                encryption_results = report['results']['encryption']
                for key, result in encryption_results.items():
                    if isinstance(result, dict) and 'encryption' in result:
                        throughput = result['encryption']['throughput_mbps']
                        f.write(f"Encryption ({key}): {throughput:.2f} MB/s\n")
            
            f.write("\nRecommendations:\n")
            f.write("-" * 18 + "\n")
            for rec in report['recommendations']:
                f.write(f"- {rec}\n")
        
        print(f"📁 Benchmark results saved:")
        print(f"   - JSON Report: {json_file}")
        print(f"   - Performance CSV: {csv_file}")
        print(f"   - Summary: {summary_file}")

def run_performance_benchmarks():
    """Run the complete performance benchmark suite"""
    benchmark_suite = PerformanceBenchmarkSuite()
    return benchmark_suite.run_all_benchmarks()

if __name__ == "__main__":
    run_performance_benchmarks()
