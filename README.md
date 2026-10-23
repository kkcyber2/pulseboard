# Pulseboard

An analytics dashboard that renders its charts as **server-side SVG**. No charting
library, no client-side data fetching for the first paint, and the whole page works
with JavaScript disabled.

## Why server-rendered charts

A charting library is 200 KB of JavaScript to draw a line. Rendering the SVG on the
server means the dashboard paints immediately, is readable by a screen reader, is
indexable, and degrades to a static image if scripting fails. The live-update layer is
then a small progressive enhancement on top.

## What it shows

* **Sparkline grid** — one per metric, with the trend direction and delta.
* **Time-series chart** — an area chart with axis ticks and a hover readout.
* **Distribution bars** — a horizontal breakdown by segment.
* **Live mode** — an SSE endpoint pushes new samples; the client appends them and
  redraws only the affected path.

## Quick start

```bash
python -m venv .venv && . .venv/bin/activate
pip install -e ".[dev]"
uvicorn pulseboard.app:app --reload
# open http://127.0.0.1:8000
```

## Endpoints

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/` | the dashboard |
| `GET` | `/api/metrics` | current values and series |
| `GET` | `/api/stream` | SSE stream of new samples |
| `GET` | `/health` | liveness |

## Tests

```bash
pytest -q
```

## License

MIT — see `LICENSE`.
