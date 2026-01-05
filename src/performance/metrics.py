"""
Prometheus-Compatible Metrics Collection

Collects and exposes metrics for monitoring the Dora platform.
"""

import logging
import threading
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class MetricType(str, Enum):
    """Types of metrics."""

    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


@dataclass
class MetricValue:
    """A single metric value."""

    name: str
    type: MetricType
    value: float
    labels: Dict[str, str] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_prometheus(self) -> str:
        """Format as Prometheus exposition format."""
        label_str = ""
        if self.labels:
            label_pairs = [f'{k}="{v}"' for k, v in self.labels.items()]
            label_str = "{" + ",".join(label_pairs) + "}"

        return f"{self.name}{label_str} {self.value}"


class MetricsCollector:
    """
    Collect and expose Prometheus-compatible metrics.

    Supports:
    - Counters (monotonically increasing)
    - Gauges (can increase or decrease)
    - Histograms (distribution of values)
    - Summaries (percentiles)
    """

    # Default histogram buckets for latency (ms)
    DEFAULT_BUCKETS = [5, 10, 25, 50, 100, 250, 500, 1000, 2500, 5000, 10000]

    def __init__(self, prefix: str = "dora"):
        """
        Initialize metrics collector.

        Args:
            prefix: Prefix for all metric names
        """
        self.prefix = prefix
        self._lock = threading.Lock()

        # Storage
        self._counters: Dict[str, float] = defaultdict(float)
        self._gauges: Dict[str, float] = {}
        self._histograms: Dict[str, List[float]] = defaultdict(list)
        self._histogram_buckets: Dict[str, List[float]] = {}

        # Metadata
        self._metric_types: Dict[str, MetricType] = {}
        self._metric_help: Dict[str, str] = {}

        # Register default metrics
        self._register_defaults()

        logger.info(f"Initialized MetricsCollector (prefix={prefix})")

    def _register_defaults(self) -> None:
        """Register default metrics."""
        # Query metrics
        self.register_histogram(
            "query_duration_ms",
            "Query pipeline duration in milliseconds",
            buckets=self.DEFAULT_BUCKETS,
        )
        self.register_counter(
            "queries_total",
            "Total number of queries processed",
        )
        self.register_counter(
            "query_errors_total",
            "Total number of query errors",
        )

        # Retrieval metrics
        self.register_histogram(
            "retrieval_duration_ms",
            "Retrieval operation duration",
            buckets=self.DEFAULT_BUCKETS,
        )
        self.register_gauge(
            "retrieval_documents_returned",
            "Number of documents returned by retrieval",
        )

        # LLM metrics
        self.register_histogram(
            "llm_duration_ms",
            "LLM generation duration",
            buckets=[100, 500, 1000, 2000, 5000, 10000, 30000],
        )
        self.register_counter(
            "llm_tokens_input_total",
            "Total input tokens to LLM",
        )
        self.register_counter(
            "llm_tokens_output_total",
            "Total output tokens from LLM",
        )

        # Cache metrics
        self.register_counter(
            "cache_hits_total",
            "Total cache hits",
        )
        self.register_counter(
            "cache_misses_total",
            "Total cache misses",
        )

        # System metrics
        self.register_gauge(
            "memory_usage_mb",
            "Current memory usage in MB",
        )
        self.register_gauge(
            "cpu_usage_percent",
            "Current CPU usage percentage",
        )
        self.register_gauge(
            "active_connections",
            "Number of active connections",
        )

    def register_counter(self, name: str, help_text: str) -> None:
        """Register a counter metric."""
        full_name = f"{self.prefix}_{name}"
        self._metric_types[full_name] = MetricType.COUNTER
        self._metric_help[full_name] = help_text

    def register_gauge(self, name: str, help_text: str) -> None:
        """Register a gauge metric."""
        full_name = f"{self.prefix}_{name}"
        self._metric_types[full_name] = MetricType.GAUGE
        self._metric_help[full_name] = help_text

    def register_histogram(
        self,
        name: str,
        help_text: str,
        buckets: Optional[List[float]] = None,
    ) -> None:
        """Register a histogram metric."""
        full_name = f"{self.prefix}_{name}"
        self._metric_types[full_name] = MetricType.HISTOGRAM
        self._metric_help[full_name] = help_text
        self._histogram_buckets[full_name] = buckets or self.DEFAULT_BUCKETS

    def inc(self, name: str, value: float = 1, labels: Optional[Dict[str, str]] = None) -> None:
        """
        Increment a counter.

        Args:
            name: Metric name
            value: Amount to increment
            labels: Optional labels
        """
        full_name = f"{self.prefix}_{name}"
        key = self._make_key(full_name, labels)

        with self._lock:
            self._counters[key] += value

    def set_gauge(self, name: str, value: float, labels: Optional[Dict[str, str]] = None) -> None:
        """
        Set a gauge value.

        Args:
            name: Metric name
            value: Value to set
            labels: Optional labels
        """
        full_name = f"{self.prefix}_{name}"
        key = self._make_key(full_name, labels)

        with self._lock:
            self._gauges[key] = value

    def observe(self, name: str, value: float, labels: Optional[Dict[str, str]] = None) -> None:
        """
        Observe a value for histogram/summary.

        Args:
            name: Metric name
            value: Observed value
            labels: Optional labels
        """
        full_name = f"{self.prefix}_{name}"
        key = self._make_key(full_name, labels)

        with self._lock:
            self._histograms[key].append(value)
            # Keep last 10000 observations
            if len(self._histograms[key]) > 10000:
                self._histograms[key] = self._histograms[key][-10000:]

    def _make_key(self, name: str, labels: Optional[Dict[str, str]]) -> str:
        """Create storage key from name and labels."""
        if not labels:
            return name
        label_str = ",".join(f"{k}={v}" for k, v in sorted(labels.items()))
        return f"{name}{{{label_str}}}"

    def _parse_key(self, key: str) -> tuple[str, Dict[str, str]]:
        """Parse storage key into name and labels."""
        if "{" not in key:
            return key, {}

        name = key[: key.index("{")]
        label_str = key[key.index("{") + 1 : key.index("}")]
        labels = {}
        for pair in label_str.split(","):
            if "=" in pair:
                k, v = pair.split("=", 1)
                labels[k] = v
        return name, labels

    def export_prometheus(self) -> str:
        """
        Export all metrics in Prometheus format.

        Returns:
            Prometheus exposition format string
        """
        lines = []

        with self._lock:
            # Export counters
            for key, value in self._counters.items():
                name, labels = self._parse_key(key)
                if name in self._metric_help:
                    lines.append(f"# HELP {name} {self._metric_help[name]}")
                    lines.append(f"# TYPE {name} counter")
                lines.append(MetricValue(name, MetricType.COUNTER, value, labels).to_prometheus())

            # Export gauges
            for key, value in self._gauges.items():
                name, labels = self._parse_key(key)
                if name in self._metric_help:
                    lines.append(f"# HELP {name} {self._metric_help[name]}")
                    lines.append(f"# TYPE {name} gauge")
                lines.append(MetricValue(name, MetricType.GAUGE, value, labels).to_prometheus())

            # Export histograms
            for key, values in self._histograms.items():
                name, labels = self._parse_key(key)
                if not values:
                    continue

                if name in self._metric_help:
                    lines.append(f"# HELP {name} {self._metric_help[name]}")
                    lines.append(f"# TYPE {name} histogram")

                buckets = self._histogram_buckets.get(name, self.DEFAULT_BUCKETS)

                # Count values in each bucket
                sorted_values = sorted(values)
                count = len(sorted_values)
                total = sum(sorted_values)

                for bucket in buckets:
                    bucket_count = sum(1 for v in sorted_values if v <= bucket)
                    bucket_labels = {**labels, "le": str(bucket)}
                    lines.append(
                        MetricValue(
                            f"{name}_bucket", MetricType.COUNTER, bucket_count, bucket_labels
                        ).to_prometheus()
                    )

                # +Inf bucket
                inf_labels = {**labels, "le": "+Inf"}
                lines.append(
                    MetricValue(f"{name}_bucket", MetricType.COUNTER, count, inf_labels).to_prometheus()
                )

                # Sum and count
                lines.append(MetricValue(f"{name}_sum", MetricType.COUNTER, total, labels).to_prometheus())
                lines.append(MetricValue(f"{name}_count", MetricType.COUNTER, count, labels).to_prometheus())

        return "\n".join(lines)

    def get_stats(self, name: str) -> Dict[str, float]:
        """
        Get statistics for a metric.

        Args:
            name: Metric name

        Returns:
            Dictionary with statistics
        """
        full_name = f"{self.prefix}_{name}"

        with self._lock:
            if full_name in self._histograms:
                values = self._histograms[full_name]
                if not values:
                    return {}

                sorted_values = sorted(values)
                count = len(sorted_values)

                return {
                    "count": count,
                    "sum": sum(sorted_values),
                    "mean": sum(sorted_values) / count,
                    "min": sorted_values[0],
                    "max": sorted_values[-1],
                    "p50": sorted_values[int(count * 0.5)],
                    "p95": sorted_values[int(count * 0.95)] if count > 20 else sorted_values[-1],
                    "p99": sorted_values[int(count * 0.99)] if count > 100 else sorted_values[-1],
                }

            if full_name in self._counters:
                return {"value": self._counters[full_name]}

            if full_name in self._gauges:
                return {"value": self._gauges[full_name]}

        return {}

    def reset(self) -> None:
        """Reset all metrics."""
        with self._lock:
            self._counters.clear()
            self._gauges.clear()
            self._histograms.clear()


# Global metrics instance
_global_metrics = MetricsCollector()


def get_metrics() -> MetricsCollector:
    """Get the global metrics collector."""
    return _global_metrics
