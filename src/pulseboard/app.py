"""The dashboard application."""
from __future__ import annotations

import asyncio
import json
import math
import random
import time
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates

from .charts import PALETTE, area_chart, bar_breakdown, sparkline
from .series import MetricStore, seed_demo

TEMPLATES = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))

store = MetricStore()
seed_demo(store)

app = FastAPI(title="Pulseboard", version="1.0.0")


@app.get("/health", tags=["meta"])
def health() -> dict[str, Any]:
    return {"status": "ok", "metrics": len(store.all())}


@app.get("/api/metrics", tags=["data"])
def metrics() -> dict[str, Any]:
    return {"metrics": [m.public() for m in store.all()]}


@app.get("/", response_class=HTMLResponse, tags=["ui"])
def dashboard(request: Request) -> HTMLResponse:
    cards = []
    for metric in store.all():
        values = metric.values
        cards.append(
            {
                "key": metric.key,
                "label": metric.label,
                "unit": metric.unit,
                "latest": f"{metric.latest:,.1f}",
                "delta": f"{metric.delta:+,.1f}",
                "delta_pct": f"{metric.delta_pct:+.1f}%",
                "trend": metric.trend,
                "spark": sparkline(values, colour=PALETTE.get(metric.key, "#8b95a8")),
            }
        )

    primary = store.get("requests")
    chart = area_chart(
        primary.values if primary else [],
        colour=PALETTE["requests"],
        label="Requests per minute",
        unit="req",
    )
    breakdown = bar_breakdown(
        [(m.key, m.latest) for m in store.all()],
    )
    return TEMPLATES.TemplateResponse(
        request,
        "dashboard.html",
        {"cards": cards, "chart": chart, "breakdown": breakdown},
    )


@app.get("/api/stream", tags=["data"])
async def stream(request: Request, limit: int | None = None) -> StreamingResponse:
    """Server-sent events: one JSON sample per metric, once a second.

    `limit` bounds the number of events, which makes the stream testable and is
    useful for debugging. Without it the stream runs until the client disconnects.
    """

    async def generator():
        rng = random.Random()
        sent = 0
        while True:
            if await request.is_disconnected():
                break
            if limit is not None and sent >= max(0, limit):
                break
            payload: dict[str, float] = {}
            for metric in store.all():
                # A small random walk around the last value keeps the demo alive.
                drift = math.sin(time.time() / 20.0) * 12
                value = max(0.0, metric.latest + rng.gauss(0, 6) + drift * 0.1)
                store.add(metric.key, value)
                payload[metric.key] = round(value, 2)
            yield f"data: {json.dumps(payload)}\n\n"
            sent += 1
            await asyncio.sleep(1.0)

    return StreamingResponse(
        generator(),
        media_type="text/event-stream",
        headers={"cache-control": "no-cache", "x-accel-buffering": "no"},
    )
