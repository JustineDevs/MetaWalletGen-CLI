"""
MetaWalletGen CLI - Performance & Scaling Module

Provides advanced performance monitoring, optimization,
caching, and load balancing for high-volume operations.
"""

__version__ = "2.0.0"
__author__ = "MetaWalletGen Team"
__email__ = "support@metawalletgen.com"

from .monitor import PerformanceMonitor
from .optimizer import PerformanceOptimizer
from .cache import CacheManager
from .load_balancer import LoadBalancer
from .benchmark import BenchmarkSuite

__all__ = [
    'PerformanceMonitor',
    'PerformanceOptimizer', 
    'CacheManager',
    'LoadBalancer',
    'BenchmarkSuite'
]
