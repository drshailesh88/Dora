"""
Performance Profiler for Dora Medical Knowledge Platform

Provides decorators and utilities for profiling query pipeline latency,
memory usage, and other performance metrics.
"""

import time
import asyncio
import functools
import psutil
import logging
from typing import Callable, Any, Dict, Optional, List
from datetime import datetime
from dataclasses import dataclass, field
from contextlib import contextmanager, asynccontextmanager
from collections import defaultdict
import threading

logger = logging.getLogger(__name__)


@dataclass
class ProfileResult:
    """Result of a profiling operation."""

    operation: str
    duration_ms: float
    memory_mb: float
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "operation": self.operation,
            "duration_ms": self.duration_ms,
            "memory_mb": self.memory_mb,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }


class PerformanceProfiler:
    """
    Centralized performance profiler.

    Tracks execution times, memory usage, and provides statistics
    for all profiled operations.
    """

    def __init__(self):
        """Initialize profiler."""
        self._results: List[ProfileResult] = []
        self._lock = threading.Lock()
        self._operation_stats: Dict[str, List[float]] = defaultdict(list)

    def record(self, result: ProfileResult) -> None:
        """
        Record a profiling result.

        Args:
            result: ProfileResult to record
        """
        with self._lock:
            self._results.append(result)
            self._operation_stats[result.operation].append(result.duration_ms)

            # Log slow operations (>1 second)
            if result.duration_ms > 1000:
                logger.warning(
                    f"Slow operation detected: {result.operation} took {result.duration_ms:.2f}ms"
                )

    def get_results(
        self,
        operation: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[ProfileResult]:
        """
        Get profiling results.

        Args:
            operation: Filter by operation name
            limit: Maximum number of results to return

        Returns:
            List of ProfileResult
        """
        with self._lock:
            results = self._results.copy()

        if operation:
            results = [r for r in results if r.operation == operation]

        # Sort by timestamp (most recent first)
        results.sort(key=lambda r: r.timestamp, reverse=True)

        if limit:
            results = results[:limit]

        return results

    def get_statistics(self, operation: Optional[str] = None) -> Dict[str, Any]:
        """
        Get statistics for profiled operations.

        Args:
            operation: Specific operation to analyze, or None for all

        Returns:
            Dictionary with statistics (p50, p95, p99, mean, count)
        """
        with self._lock:
            if operation:
                if operation not in self._operation_stats:
                    return {}
                durations = self._operation_stats[operation]
                stats = {operation: self._calculate_stats(durations)}
            else:
                stats = {
                    op: self._calculate_stats(durations)
                    for op, durations in self._operation_stats.items()
                }

        return stats

    def _calculate_stats(self, durations: List[float]) -> Dict[str, Any]:
        """Calculate statistics from duration list."""
        if not durations:
            return {}

        sorted_durations = sorted(durations)
        count = len(sorted_durations)

        return {
            "count": count,
            "mean_ms": sum(sorted_durations) / count,
            "min_ms": sorted_durations[0],
            "max_ms": sorted_durations[-1],
            "p50_ms": sorted_durations[int(count * 0.5)],
            "p95_ms": sorted_durations[int(count * 0.95)] if count > 20 else sorted_durations[-1],
            "p99_ms": sorted_durations[int(count * 0.99)] if count > 100 else sorted_durations[-1],
        }

    def clear(self) -> None:
        """Clear all recorded results."""
        with self._lock:
            self._results.clear()
            self._operation_stats.clear()

    def export_results(self) -> List[Dict[str, Any]]:
        """Export all results as list of dictionaries."""
        with self._lock:
            return [r.to_dict() for r in self._results]


# Global profiler instance
_global_profiler = PerformanceProfiler()


def get_profiler() -> PerformanceProfiler:
    """Get the global profiler instance."""
    return _global_profiler


@contextmanager
def profile(operation: str, metadata: Optional[Dict[str, Any]] = None):
    """
    Context manager for profiling synchronous code.

    Usage:
        with profile("embedding_generation"):
            embeddings = generate_embeddings(text)

    Args:
        operation: Name of the operation being profiled
        metadata: Optional metadata to attach to the result
    """
    process = psutil.Process()
    mem_before = process.memory_info().rss / 1024 / 1024  # MB
    start_time = time.perf_counter()

    try:
        yield
    finally:
        duration_ms = (time.perf_counter() - start_time) * 1000
        mem_after = process.memory_info().rss / 1024 / 1024  # MB
        mem_delta = mem_after - mem_before

        result = ProfileResult(
            operation=operation,
            duration_ms=duration_ms,
            memory_mb=mem_delta,
            timestamp=datetime.utcnow(),
            metadata=metadata or {},
        )

        _global_profiler.record(result)


@asynccontextmanager
async def profile_async(operation: str, metadata: Optional[Dict[str, Any]] = None):
    """
    Async context manager for profiling asynchronous code.

    Usage:
        async with profile_async("llm_generation"):
            response = await llm.generate(prompt)

    Args:
        operation: Name of the operation being profiled
        metadata: Optional metadata to attach to the result
    """
    process = psutil.Process()
    mem_before = process.memory_info().rss / 1024 / 1024  # MB
    start_time = time.perf_counter()

    try:
        yield
    finally:
        duration_ms = (time.perf_counter() - start_time) * 1000
        mem_after = process.memory_info().rss / 1024 / 1024  # MB
        mem_delta = mem_after - mem_before

        result = ProfileResult(
            operation=operation,
            duration_ms=duration_ms,
            memory_mb=mem_delta,
            timestamp=datetime.utcnow(),
            metadata=metadata or {},
        )

        _global_profiler.record(result)


def profile_function(operation: Optional[str] = None):
    """
    Decorator for profiling synchronous functions.

    Usage:
        @profile_function("embedding_generation")
        def generate_embeddings(text: str) -> List[float]:
            ...

    Args:
        operation: Name of operation (defaults to function name)
    """
    def decorator(func: Callable) -> Callable:
        op_name = operation or f"{func.__module__}.{func.__name__}"

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            with profile(op_name):
                return func(*args, **kwargs)

        return wrapper

    return decorator


def profile_async_function(operation: Optional[str] = None):
    """
    Decorator for profiling asynchronous functions.

    Usage:
        @profile_async_function("llm_generation")
        async def generate_response(prompt: str) -> str:
            ...

    Args:
        operation: Name of operation (defaults to function name)
    """
    def decorator(func: Callable) -> Callable:
        op_name = operation or f"{func.__module__}.{func.__name__}"

        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            async with profile_async(op_name):
                return await func(*args, **kwargs)

        return wrapper

    return decorator


class PipelineProfiler:
    """
    Profiler for multi-stage pipelines.

    Tracks individual stages and provides detailed breakdown.
    """

    def __init__(self, pipeline_name: str):
        """
        Initialize pipeline profiler.

        Args:
            pipeline_name: Name of the pipeline
        """
        self.pipeline_name = pipeline_name
        self.stages: Dict[str, float] = {}
        self.start_time: Optional[float] = None
        self.total_duration: Optional[float] = None

    def start(self) -> None:
        """Start profiling the pipeline."""
        self.start_time = time.perf_counter()
        self.stages.clear()

    @contextmanager
    def stage(self, stage_name: str):
        """
        Profile a pipeline stage.

        Usage:
            profiler = PipelineProfiler("rag_query")
            profiler.start()
            with profiler.stage("embedding"):
                embeddings = generate_embeddings(query)
            with profiler.stage("retrieval"):
                docs = retrieve_documents(embeddings)
            profiler.stop()

        Args:
            stage_name: Name of the stage
        """
        stage_start = time.perf_counter()
        try:
            yield
        finally:
            duration = (time.perf_counter() - stage_start) * 1000
            self.stages[stage_name] = duration

    def stop(self) -> Dict[str, Any]:
        """
        Stop profiling and return results.

        Returns:
            Dictionary with total duration and stage breakdown
        """
        if self.start_time is None:
            raise ValueError("Pipeline profiler not started")

        self.total_duration = (time.perf_counter() - self.start_time) * 1000

        # Calculate percentages
        stage_percentages = {
            stage: (duration / self.total_duration * 100)
            for stage, duration in self.stages.items()
        }

        result = {
            "pipeline": self.pipeline_name,
            "total_ms": self.total_duration,
            "stages_ms": self.stages,
            "stage_percentages": stage_percentages,
            "timestamp": datetime.utcnow().isoformat(),
        }

        # Record to global profiler
        _global_profiler.record(
            ProfileResult(
                operation=f"pipeline_{self.pipeline_name}",
                duration_ms=self.total_duration,
                memory_mb=0.0,  # Not tracking memory for pipeline profiler
                timestamp=datetime.utcnow(),
                metadata=result,
            )
        )

        return result


def get_memory_usage() -> Dict[str, float]:
    """
    Get current memory usage statistics.

    Returns:
        Dictionary with memory usage in MB
    """
    process = psutil.Process()
    mem_info = process.memory_info()

    return {
        "rss_mb": mem_info.rss / 1024 / 1024,
        "vms_mb": mem_info.vms / 1024 / 1024,
        "percent": process.memory_percent(),
    }


def get_cpu_usage() -> float:
    """
    Get current CPU usage percentage.

    Returns:
        CPU usage as percentage (0-100)
    """
    return psutil.cpu_percent(interval=0.1)
