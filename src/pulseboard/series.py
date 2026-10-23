"""Time-series storage and the statistics the dashboard displays."""
from __future__ import annotations

import math
import random
import threading
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Sample:
    at: float
    value: float

    def public(self) -> dict[str, float]:
        return {"at": self.at, "value": self.value}


@dataclass
class Metric:
    key: str
    label: str
    unit: str = ""
    samples: deque[Sample] = field(default_factory=lambda: deque(maxlen=240))

    def add(self, value: float, at: float | None = None) -> Sample:
        sample = Sample(at=at if at is not None else time.time(), value=float(value))
        self.samples.append(sample)
        return sample

    @property
    def values(self) -> list[float]:
        return [s.value for s in self.samples]

    @property
    def latest(self) -> float:
        return self.samples[-1].value if self.samples else 0.0

    @property
    def previous(self) -> float:
        return self.samples[-2].value if len(self.samples) > 1 else self.latest

    @property
    def delta(self) -> float:
        return self.latest - self.previous

    @property
    def delta_pct(self) -> float:
        if self.previous == 0:
            return 0.0
        return (self.delta / abs(self.previous)) * 100.0

    @property
    def trend(self) -> str:
        if abs(self.delta_pct) < 0.5:
            return "flat"
        return "up" if self.delta > 0 else "down"

    def mean(self) -> float:
        values = self.values
        return sum(values) / len(values) if values else 0.0

    def stdev(self) -> float:
        values = self.values
        if len(values) < 2:
            return 0.0
        mean = self.mean()
        return math.sqrt(sum((v - mean) ** 2 for v in values) / (len(values) - 1))

    def public(self) -> dict[str, Any]:
        return {
            "key": self.key,
            "label": self.label,
            "unit": self.unit,
            "latest": round(self.latest, 2),
            "delta": round(self.delta, 2),
            "delta_pct": round(self.delta_pct, 2),
            "trend": self.trend,
            "mean": round(self.mean(), 2),
            "stdev": round(self.stdev(), 2),
            "samples": [s.public() for s in self.samples],
        }


class MetricStore:
    """Thread-safe collection of metrics."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._metrics: dict[str, Metric] = {}

    def register(self, key: str, label: str, unit: str = "") -> Metric:
        with self._lock:
            metric = Metric(key=key, label=label, unit=unit)
            self._metrics[key] = metric
            return metric

    def get(self, key: str) -> Metric | None:
        with self._lock:
            return self._metrics.get(key)

    def all(self) -> list[Metric]:
        with self._lock:
            return list(self._metrics.values())

    def add(self, key: str, value: float, at: float | None = None) -> Sample:
        with self._lock:
            metric = self._metrics.get(key)
            if metric is None:
                raise KeyError(f"unknown metric {key!r}")
            return metric.add(value, at)

    def clear(self) -> None:
        with self._lock:
            for metric in self._metrics.values():
                metric.samples.clear()


def seed_demo(store: MetricStore, *, points: int = 60, seed: int = 7) -> None:
    """Fill the store with plausible traffic data so the dashboard has something to show."""
    rng = random.Random(seed)
    now = time.time()
    definitions = [
        ("requests", "Requests / min", "req"),
        ("latency_p95", "p95 latency", "ms"),
        ("error_rate", "Error rate", "%"),
        ("active_users", "Active users", ""),
    ]
    for key, label, unit in definitions:
        store.register(key, label, unit)

    for index in range(points):
        at = now - (points - index) * 60
        # A daily-ish wave plus noise, so the charts have real shape.
        wave = math.sin(index / 9.0)
        store.add("requests", 1200 + wave * 320 + rng.gauss(0, 45), at)
        store.add("latency_p95", 180 + wave * 40 + rng.gauss(0, 12), at)
        store.add("error_rate", max(0.0, 1.4 - wave * 0.6 + rng.gauss(0, 0.25)), at)
        store.add("active_users", 340 + wave * 90 + rng.gauss(0, 18), at)
