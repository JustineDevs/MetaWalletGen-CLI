"""
Performance Optimization System for MetaWalletGen CLI.

This module provides intelligent performance optimization capabilities
including automatic tuning, resource management, and optimization recommendations.
"""

import json
import logging
import time
import threading
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional, Callable, Tuple
from collections import defaultdict, deque
import psutil
import statistics


@dataclass
class OptimizationRule:
    """Performance optimization rule."""
    rule_id: str
    name: str
    description: str
    category: str
    priority: int
    enabled: bool = True
    conditions: Dict[str, Any] = None
    actions: List[Dict[str, Any]] = None
    last_applied: Optional[datetime] = None


@dataclass
class OptimizationResult:
    """Result of an optimization action."""
    rule_id: str
    action: str
    timestamp: datetime
    before_value: float
    after_value: float
    improvement: float
    success: bool
    details: Dict[str, Any] = None


@dataclass
class PerformanceProfile:
    """Performance profile configuration."""
    profile_name: str
    description: str
    settings: Dict[str, Any]
    target_metrics: Dict[str, float]
    created_at: datetime
    is_active: bool = False


class PerformanceOptimizer:
    """Intelligent performance optimization system."""
    
    def __init__(self, monitor=None):
        """Initialize performance optimizer."""
        self.monitor = monitor
        self.logger = logging.getLogger(__name__)
        
        # Optimization rules
        self.optimization_rules = {}
        self.rule_results = deque(maxlen=1000)
        
        # Performance profiles
        self.performance_profiles = {}
        self.active_profile = None
        
        # Optimization state
        self.is_optimizing = False
        self.optimization_thread = None
        self.stop_event = threading.Event()
        
        # Configuration
        self.auto_optimize = True
        self.optimization_interval = 30.0  # seconds
        self.min_improvement_threshold = 5.0  # percentage
        
        # Initialize default rules and profiles
        self._init_default_rules()
        self._init_default_profiles()
    
    def _init_default_rules(self):
        """Initialize default optimization rules."""
        default_rules = [
            OptimizationRule(
                rule_id="MEMORY_OPTIMIZATION",
                name="Memory Usage Optimization",
                description="Optimize memory usage when it exceeds thresholds",
                category="memory",
                priority=1,
                conditions={
                    "memory_percent": {"operator": ">", "value": 80.0},
                    "cpu_percent": {"operator": "<", "value": 70.0}
                },
                actions=[
                    {"action": "clear_cache", "target": "wallet_cache"},
                    {"action": "adjust_batch_size", "target": "wallet_generation", "value": "reduce"}
                ]
            ),
            OptimizationRule(
                rule_id="CPU_OPTIMIZATION",
                name="CPU Usage Optimization",
                description="Optimize CPU usage during high load",
                category="cpu",
                priority=2,
                conditions={
                    "cpu_percent": {"operator": ">", "value": 85.0},
                    "wallet_generation_time_ms": {"operator": ">", "value": 2000.0}
                },
                actions=[
                    {"action": "limit_concurrent_operations", "target": "wallet_generation", "value": 2},
                    {"action": "enable_async_processing", "target": "encryption"}
                ]
            ),
            OptimizationRule(
                rule_id="DISK_OPTIMIZATION",
                name="Disk I/O Optimization",
                description="Optimize disk operations for better performance",
                category="disk",
                priority=3,
                conditions={
                    "disk_usage_percent": {"operator": ">", "value": 90.0}
                },
                actions=[
                    {"action": "cleanup_temp_files", "target": "system"},
                    {"action": "compress_storage", "target": "wallet_data"}
                ]
            ),
            OptimizationRule(
                rule_id="NETWORK_OPTIMIZATION",
                name="Network Performance Optimization",
                description="Optimize network operations and API responses",
                category="network",
                priority=4,
                conditions={
                    "api_response_time_ms": {"operator": ">", "value": 3000.0}
                },
                actions=[
                    {"action": "enable_caching", "target": "api_responses"},
                    {"action": "optimize_database_queries", "target": "wallet_queries"}
                ]
            )
        ]
        
        for rule in default_rules:
            self.add_optimization_rule(rule)
    
    def _init_default_profiles(self):
        """Initialize default performance profiles."""
        default_profiles = [
            PerformanceProfile(
                profile_name="balanced",
                description="Balanced performance profile for general use",
                settings={
                    "max_concurrent_wallets": 5,
                    "batch_size": 10,
                    "cache_size": 100,
                    "async_processing": True,
                    "compression_level": "medium"
                },
                target_metrics={
                    "wallet_generation_time_ms": 1000.0,
                    "memory_percent": 70.0,
                    "cpu_percent": 60.0
                },
                created_at=datetime.now(timezone.utc)
            ),
            PerformanceProfile(
                profile_name="high_performance",
                description="High performance profile for maximum speed",
                settings={
                    "max_concurrent_wallets": 10,
                    "batch_size": 20,
                    "cache_size": 200,
                    "async_processing": True,
                    "compression_level": "low"
                },
                target_metrics={
                    "wallet_generation_time_ms": 500.0,
                    "memory_percent": 85.0,
                    "cpu_percent": 80.0
                },
                created_at=datetime.now(timezone.utc)
            ),
            PerformanceProfile(
                profile_name="resource_efficient",
                description="Resource efficient profile for limited systems",
                settings={
                    "max_concurrent_wallets": 2,
                    "batch_size": 5,
                    "cache_size": 50,
                    "async_processing": False,
                    "compression_level": "high"
                },
                target_metrics={
                    "wallet_generation_time_ms": 2000.0,
                    "memory_percent": 50.0,
                    "cpu_percent": 40.0
                },
                created_at=datetime.now(timezone.utc)
            )
        ]
        
        for profile in default_profiles:
            self.add_performance_profile(profile)
        
        # Set balanced profile as default
        self.set_active_profile("balanced")
    
    def add_optimization_rule(self, rule: OptimizationRule):
        """Add a new optimization rule."""
        self.optimization_rules[rule.rule_id] = rule
        self.logger.info(f"Added optimization rule: {rule.name}")
    
    def add_performance_profile(self, profile: PerformanceProfile):
        """Add a new performance profile."""
        self.performance_profiles[profile.profile_name] = profile
        self.logger.info(f"Added performance profile: {profile.profile_name}")
    
    def set_active_profile(self, profile_name: str):
        """Set the active performance profile."""
        if profile_name not in self.performance_profiles:
            raise ValueError(f"Profile '{profile_name}' not found")
        
        # Deactivate current profile
        if self.active_profile:
            self.performance_profiles[self.active_profile].is_active = False
        
        # Activate new profile
        self.active_profile = profile_name
        self.performance_profiles[profile_name].is_active = True
        
        # Apply profile settings
        self._apply_profile_settings(profile_name)
        
        self.logger.info(f"Activated performance profile: {profile_name}")
    
    def _apply_profile_settings(self, profile_name: str):
        """Apply settings from a performance profile."""
        profile = self.performance_profiles[profile_name]
        
        # Apply settings to system
        for setting, value in profile.settings.items():
            self._apply_setting(setting, value)
    
    def _apply_setting(self, setting: str, value: Any):
        """Apply a specific setting to the system."""
        try:
            if setting == "max_concurrent_wallets":
                # This would typically update a global configuration
                self.logger.info(f"Applied setting: {setting} = {value}")
            elif setting == "batch_size":
                # This would typically update batch processing configuration
                self.logger.info(f"Applied setting: {setting} = {value}")
            elif setting == "cache_size":
                # This would typically update cache configuration
                self.logger.info(f"Applied setting: {setting} = {value}")
            elif setting == "async_processing":
                # This would typically enable/disable async processing
                self.logger.info(f"Applied setting: {setting} = {value}")
            elif setting == "compression_level":
                # This would typically update compression settings
                self.logger.info(f"Applied setting: {setting} = {value}")
            else:
                self.logger.warning(f"Unknown setting: {setting}")
                
        except Exception as e:
            self.logger.error(f"Failed to apply setting {setting}: {e}")
    
    def start_optimization(self):
        """Start automatic performance optimization."""
        if self.is_optimizing:
            self.logger.warning("Performance optimization is already running")
            return
        
        self.is_optimizing = True
        self.stop_event.clear()
        self.optimization_thread = threading.Thread(target=self._optimization_loop, daemon=True)
        self.optimization_thread.start()
        self.logger.info("Performance optimization started")
    
    def stop_optimization(self):
        """Stop automatic performance optimization."""
        if not self.is_optimizing:
            return
        
        self.is_optimizing = False
        self.stop_event.set()
        
        if self.optimization_thread and self.optimization_thread.is_alive():
            self.optimization_thread.join(timeout=5.0)
        
        self.logger.info("Performance optimization stopped")
    
    def _optimization_loop(self):
        """Main optimization loop."""
        while not self.stop_event.is_set():
            try:
                if self.auto_optimize:
                    # Check for optimization opportunities
                    self._check_optimization_opportunities()
                
                # Wait for next optimization cycle
                self.stop_event.wait(self.optimization_interval)
                
            except Exception as e:
                self.logger.error(f"Error in optimization loop: {e}")
                time.sleep(5.0)  # Brief pause on error
    
    def _check_optimization_opportunities(self):
        """Check for optimization opportunities and apply rules."""
        if not self.monitor:
            return
        
        current_metrics = self.monitor.get_current_metrics()
        
        # Check each optimization rule
        for rule_id, rule in self.optimization_rules.items():
            if not rule.enabled:
                continue
            
            if self._should_apply_rule(rule, current_metrics):
                self._apply_optimization_rule(rule, current_metrics)
    
    def _should_apply_rule(self, rule: OptimizationRule, metrics: Dict[str, Any]) -> bool:
        """Check if an optimization rule should be applied."""
        if not rule.conditions:
            return False
        
        for metric_name, condition in rule.conditions.items():
            if metric_name not in metrics:
                continue
            
            current_value = metrics[metric_name]
            operator = condition.get("operator")
            threshold_value = condition.get("value")
            
            if operator == ">":
                if current_value <= threshold_value:
                    return False
            elif operator == "<":
                if current_value >= threshold_value:
                    return False
            elif operator == ">=":
                if current_value < threshold_value:
                    return False
            elif operator == "<=":
                if current_value > threshold_value:
                    return False
            elif operator == "==":
                if current_value != threshold_value:
                    return False
            elif operator == "!=":
                if current_value == threshold_value:
                    return False
        
        return True
    
    def _apply_optimization_rule(self, rule: OptimizationRule, metrics: Dict[str, Any]):
        """Apply an optimization rule."""
        try:
            self.logger.info(f"Applying optimization rule: {rule.name}")
            
            # Execute optimization actions
            for action_config in rule.actions:
                result = self._execute_optimization_action(action_config, metrics)
                
                if result:
                    self.rule_results.append(result)
                    rule.last_applied = datetime.now(timezone.utc)
                    
                    self.logger.info(f"Optimization action completed: {action_config['action']}")
            
        except Exception as e:
            self.logger.error(f"Failed to apply optimization rule {rule.rule_id}: {e}")
    
    def _execute_optimization_action(self, action_config: Dict[str, Any], 
                                   metrics: Dict[str, Any]) -> Optional[OptimizationResult]:
        """Execute a specific optimization action."""
        try:
            action = action_config.get("action")
            target = action_config.get("target")
            value = action_config.get("value")
            
            # Record before value
            before_value = self._get_metric_value(target, metrics)
            
            # Execute action
            success = self._perform_action(action, target, value)
            
            if success:
                # Record after value
                after_value = self._get_metric_value(target, metrics)
                improvement = before_value - after_value if before_value > after_value else after_value - before_value
                
                return OptimizationResult(
                    rule_id="",  # Will be set by caller
                    action=action,
                    timestamp=datetime.now(timezone.utc),
                    before_value=before_value,
                    after_value=after_value,
                    improvement=improvement,
                    success=True,
                    details={"target": target, "value": value}
                )
            
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to execute optimization action: {e}")
            return None
    
    def _get_metric_value(self, target: str, metrics: Dict[str, Any]) -> float:
        """Get the current value of a target metric."""
        # Map targets to actual metrics
        target_mapping = {
            "wallet_cache": "memory_percent",
            "wallet_generation": "wallet_generation_time_ms",
            "encryption": "encryption_time_ms",
            "api_responses": "api_response_time_ms",
            "system": "cpu_percent"
        }
        
        metric_name = target_mapping.get(target, target)
        return metrics.get(metric_name, 0.0)
    
    def _perform_action(self, action: str, target: str, value: Any) -> bool:
        """Perform a specific optimization action."""
        try:
            if action == "clear_cache":
                return self._clear_cache(target)
            elif action == "adjust_batch_size":
                return self._adjust_batch_size(target, value)
            elif action == "limit_concurrent_operations":
                return self._limit_concurrent_operations(target, value)
            elif action == "enable_async_processing":
                return self._enable_async_processing(target)
            elif action == "cleanup_temp_files":
                return self._cleanup_temp_files()
            elif action == "compress_storage":
                return self._compress_storage(target)
            elif action == "enable_caching":
                return self._enable_caching(target)
            elif action == "optimize_database_queries":
                return self._optimize_database_queries(target)
            else:
                self.logger.warning(f"Unknown optimization action: {action}")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to perform action {action}: {e}")
            return False
    
    def _clear_cache(self, target: str) -> bool:
        """Clear cache for a specific target."""
        # This would typically clear the actual cache
        self.logger.info(f"Cleared cache for: {target}")
        return True
    
    def _adjust_batch_size(self, target: str, adjustment: str) -> bool:
        """Adjust batch size for a target operation."""
        # This would typically update batch size configuration
        self.logger.info(f"Adjusted batch size for {target}: {adjustment}")
        return True
    
    def _limit_concurrent_operations(self, target: str, limit: int) -> bool:
        """Limit concurrent operations for a target."""
        # This would typically update concurrency limits
        self.logger.info(f"Limited concurrent operations for {target}: {limit}")
        return True
    
    def _enable_async_processing(self, target: str) -> bool:
        """Enable async processing for a target."""
        # This would typically enable async processing
        self.logger.info(f"Enabled async processing for: {target}")
        return True
    
    def _cleanup_temp_files(self) -> bool:
        """Clean up temporary files."""
        # This would typically clean up temp files
        self.logger.info("Cleaned up temporary files")
        return True
    
    def _compress_storage(self, target: str) -> bool:
        """Compress storage for a target."""
        # This would typically compress storage
        self.logger.info(f"Compressed storage for: {target}")
        return True
    
    def _enable_caching(self, target: str) -> bool:
        """Enable caching for a target."""
        # This would typically enable caching
        self.logger.info(f"Enabled caching for: {target}")
        return True
    
    def _optimize_database_queries(self, target: str) -> bool:
        """Optimize database queries for a target."""
        # This would typically optimize database queries
        self.logger.info(f"Optimized database queries for: {target}")
        return True
    
    def get_optimization_recommendations(self) -> List[Dict[str, Any]]:
        """Get current optimization recommendations."""
        if not self.monitor:
            return []
        
        current_metrics = self.monitor.get_current_metrics()
        recommendations = []
        
        for rule_id, rule in self.optimization_rules.items():
            if not rule.enabled:
                continue
            
            if self._should_apply_rule(rule, current_metrics):
                recommendation = {
                    "rule_id": rule_id,
                    "name": rule.name,
                    "description": rule.description,
                    "category": rule.category,
                    "priority": rule.priority,
                    "estimated_improvement": self._estimate_improvement(rule, current_metrics),
                    "actions": rule.actions
                }
                recommendations.append(recommendation)
        
        # Sort by priority and estimated improvement
        recommendations.sort(key=lambda x: (x["priority"], x["estimated_improvement"]), reverse=True)
        
        return recommendations
    
    def _estimate_improvement(self, rule: OptimizationRule, metrics: Dict[str, Any]) -> float:
        """Estimate the improvement from applying an optimization rule."""
        # Simple estimation based on rule category and current metrics
        if rule.category == "memory" and "memory_percent" in metrics:
            return min(metrics["memory_percent"] * 0.2, 20.0)  # Up to 20% improvement
        elif rule.category == "cpu" and "cpu_percent" in metrics:
            return min(metrics["cpu_percent"] * 0.15, 15.0)  # Up to 15% improvement
        elif rule.category == "disk":
            return 10.0  # Estimated 10% improvement
        elif rule.category == "network":
            return 25.0  # Estimated 25% improvement
        else:
            return 5.0  # Default 5% improvement
    
    def get_optimization_history(self, limit: int = 100) -> List[OptimizationResult]:
        """Get optimization history."""
        return list(self.rule_results)[-limit:]
    
    def get_performance_profiles(self) -> List[PerformanceProfile]:
        """Get all available performance profiles."""
        return list(self.performance_profiles.values())
    
    def get_active_profile(self) -> Optional[PerformanceProfile]:
        """Get the currently active performance profile."""
        if self.active_profile:
            return self.performance_profiles[self.active_profile]
        return None
    
    def create_custom_profile(self, name: str, description: str, 
                            settings: Dict[str, Any], 
                            target_metrics: Dict[str, float]) -> PerformanceProfile:
        """Create a custom performance profile."""
        profile = PerformanceProfile(
            profile_name=name,
            description=description,
            settings=settings,
            target_metrics=target_metrics,
            created_at=datetime.now(timezone.utc)
        )
        
        self.add_performance_profile(profile)
        return profile
    
    def export_optimization_data(self, format: str = "json", file_path: str = None) -> str:
        """Export optimization data to file."""
        if not file_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_path = f"optimization_data_{timestamp}.{format}"
        
        try:
            export_data = {
                'profiles': [asdict(p) for p in self.performance_profiles.values()],
                'rules': [asdict(r) for r in self.optimization_rules.values()],
                'results': [asdict(r) for r in self.rule_results],
                'recommendations': self.get_optimization_recommendations()
            }
            
            if format.lower() == "json":
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(export_data, f, indent=2, default=str)
            else:
                raise ValueError(f"Unsupported format: {format}")
            
            self.logger.info(f"Optimization data exported to {file_path}")
            return file_path
            
        except Exception as e:
            self.logger.error(f"Failed to export optimization data: {e}")
            raise
    
    def __enter__(self):
        """Context manager entry."""
        self.start_optimization()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop_optimization()


# Convenience functions
def create_performance_optimizer(monitor=None) -> PerformanceOptimizer:
    """Create a new performance optimizer instance."""
    return PerformanceOptimizer(monitor)


def quick_optimization_check(monitor=None) -> List[Dict[str, Any]]:
    """Quick optimization check without continuous optimization."""
    optimizer = PerformanceOptimizer(monitor)
    return optimizer.get_optimization_recommendations()


# Example usage
if __name__ == "__main__":
    # Example: Create and use optimizer
    optimizer = create_performance_optimizer()
    
    # Get optimization recommendations
    recommendations = optimizer.get_optimization_recommendations()
    print("Optimization Recommendations:")
    for rec in recommendations:
        print(f"- {rec['name']}: {rec['description']} (Priority: {rec['priority']})")
    
    # Get performance profiles
    profiles = optimizer.get_performance_profiles()
    print("\nAvailable Performance Profiles:")
    for profile in profiles:
        print(f"- {profile.profile_name}: {profile.description}")
    
    # Export optimization data
    try:
        export_file = optimizer.export_optimization_data()
        print(f"\nOptimization data exported to: {export_file}")
    except Exception as e:
        print(f"Export failed: {e}")
