"""
Performance Module for Dora Medical Knowledge Platform

Provides profiling, metrics collection, and benchmarking:
- Query pipeline profiling
- Prometheus-compatible metrics
- Performance benchmarks
"""

from .profiler import (
    PerformanceProfiler,
    ProfileResult,
    PipelineProfiler,
    profile,
    profile_async,
    profile_function,
    profile_async_function,
    get_profiler,
    get_memory_usage,
    get_cpu_usage,
)
from .metrics import MetricsCollector, MetricType, get_metrics

__all__ = [
    # Profiler
    "PerformanceProfiler",
    "ProfileResult",
    "PipelineProfiler",
    "profile",
    "profile_async",
    "profile_function",
    "profile_async_function",
    "get_profiler",
    "get_memory_usage",
    "get_cpu_usage",
    # Metrics
    "MetricsCollector",
    "MetricType",
    "get_metrics",
]
