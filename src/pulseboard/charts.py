"""Server-side SVG chart rendering.

Every function returns an SVG string. No charting library, no client-side layout.
"""
from __future__ import annotations

from dataclasses import dataclass
from html import escape
from typing import Sequence

PALETTE = {
    "requests": "#6fb3ff",
    "latency_p95": "#ffb454",
    "error_rate": "#ff6b6b",
    "active_users": "#5fd3a6",
}
DEFAULT_COLOUR = "#8b95a8"


@dataclass
class Box:
    width: int
    height: int
    padding: int = 8

    @property
    def inner_width(self) -> int:
        return max(1, self.width - self.padding * 2)

    @property
    def inner_height(self) -> int:
        return max(1, self.height - self.padding * 2)


def _scale(values: Sequence[float], box: Box) -> tuple[float, float]:
    """Return (min, range) with a little headroom so the line never touches the edge."""
    if not values:
        return 0.0, 1.0
    low, high = min(values), max(values)
    if high == low:
        return low - 1.0, 2.0
    span = high - low
    return low - span * 0.08, span * 1.16


def sparkline(values: Sequence[float], *, width: int = 160, height: int = 40, colour: str = DEFAULT_COLOUR) -> str:
    """A compact line chart with no axes."""
    box = Box(width, height, padding=3)
    if len(values) < 2:
        return f'<svg class="spark" viewBox="0 0 {width} {height}" role="img" aria-label="no data"></svg>'
    low, span = _scale(values, box)
    step = box.inner_width / (len(values) - 1)
    points = []
    for index, value in enumerate(values):
        x = box.padding + index * step
        y = box.padding + box.inner_height - ((value - low) / span) * box.inner_height
        points.append(f"{x:.2f},{y:.2f}")
    path = " ".join(points)
    area = f"{box.padding},{box.padding + box.inner_height} {path} {box.padding + box.inner_width},{box.padding + box.inner_height}"
    return (
        f'<svg class="spark" viewBox="0 0 {width} {height}" preserveAspectRatio="none" '
        f'role="img" aria-label="trend">'
        f'<polygon points="{area}" fill="{colour}" opacity="0.12"/>'
        f'<polyline points="{path}" fill="none" stroke="{colour}" stroke-width="1.6" '
        f'stroke-linejoin="round" stroke-linecap="round"/>'
        f"</svg>"
    )


def area_chart(
    values: Sequence[float],
    *,
    width: int = 720,
    height: int = 240,
    colour: str = DEFAULT_COLOUR,
    label: str = "",
    unit: str = "",
) -> str:
    """A time-series area chart with horizontal gridlines and a y-axis readout."""
    box = Box(width, height, padding=34)
    if len(values) < 2:
        return f'<svg class="chart" viewBox="0 0 {width} {height}" role="img" aria-label="no data"></svg>'
    low, span = _scale(values, box)
    step = box.inner_width / (len(values) - 1)

    def y_for(value: float) -> float:
        return box.padding + box.inner_height - ((value - low) / span) * box.inner_height

    points = [
        f"{box.padding + index * step:.2f},{y_for(value):.2f}"
        for index, value in enumerate(values)
    ]
    path = " ".join(points)
    baseline = box.padding + box.inner_height
    area = f"{box.padding},{baseline} {path} {box.padding + box.inner_width},{baseline}"

    gridlines = []
    for fraction in (0.0, 0.25, 0.5, 0.75, 1.0):
        y = box.padding + box.inner_height * fraction
        value = low + span * (1 - fraction)
        gridlines.append(
            f'<line x1="{box.padding}" y1="{y:.1f}" x2="{box.padding + box.inner_width}" '
            f'y2="{y:.1f}" stroke="rgba(140,160,200,0.14)" stroke-width="1"/>'
        )
        gridlines.append(
            f'<text x="{box.padding - 8}" y="{y + 4:.1f}" text-anchor="end" '
            f'class="chart__tick">{value:,.0f}</text>'
        )

    return (
        f'<svg class="chart" viewBox="0 0 {width} {height}" role="img" '
        f'aria-label="{escape(label)} over time">'
        f'<defs><linearGradient id="fill-{escape(label)}" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0%" stop-color="{colour}" stop-opacity="0.35"/>'
        f'<stop offset="100%" stop-color="{colour}" stop-opacity="0.02"/>'
        f"</linearGradient></defs>"
        + "".join(gridlines)
        + f'<polygon points="{area}" fill="url(#fill-{escape(label)})"/>'
        + f'<polyline points="{path}" fill="none" stroke="{colour}" stroke-width="2" '
        f'stroke-linejoin="round" stroke-linecap="round"/>'
        + f'<text x="{box.padding}" y="{height - 8}" class="chart__axis">{escape(label)}'
        + (f" ({escape(unit)})" if unit else "")
        + "</text>"
        + "</svg>"
    )


def bar_breakdown(items: Sequence[tuple[str, float]], *, width: int = 360, row_height: int = 30) -> str:
    """Horizontal bars with labels and values."""
    if not items:
        return f'<svg class="bars" viewBox="0 0 {width} 40" role="img" aria-label="no data"></svg>'
    height = row_height * len(items) + 8
    label_width = 120
    bar_width = width - label_width - 70
    peak = max(value for _, value in items) or 1.0
    rows = []
    for index, (name, value) in enumerate(items):
        y = index * row_height + 6
        length = max(2.0, (value / peak) * bar_width)
        rows.append(
            f'<text x="0" y="{y + 14}" class="bars__label">{escape(name)}</text>'
            f'<rect x="{label_width}" y="{y + 4}" width="{length:.1f}" height="14" rx="3" '
            f'fill="{PALETTE.get(name, DEFAULT_COLOUR)}" opacity="0.85"/>'
            f'<text x="{label_width + length + 8:.1f}" y="{y + 15}" class="bars__value">{value:,.0f}</text>'
        )
    return (
        f'<svg class="bars" viewBox="0 0 {width} {height}" role="img" aria-label="breakdown">'
        + "".join(rows)
        + "</svg>"
    )
