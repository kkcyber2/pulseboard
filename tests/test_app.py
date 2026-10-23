def test_health(client):
    body = client.get("/health").json()
    assert body["status"] == "ok"
    assert body["metrics"] == 4


def test_metrics_endpoint_returns_series(client):
    body = client.get("/api/metrics").json()
    assert len(body["metrics"]) == 4
    assert all(m["samples"] for m in body["metrics"])


def test_dashboard_renders(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "Pulseboard" in response.text


def test_dashboard_contains_server_rendered_charts(client):
    text = client.get("/").text
    assert "<svg" in text
    assert "polyline" in text
    assert "chart__tick" in text


def test_dashboard_has_a_card_per_metric(client):
    text = client.get("/").text
    for key in ("requests", "latency_p95", "error_rate", "active_users"):
        assert f'data-metric="{key}"' in text


def test_dashboard_works_without_javascript(client):
    # The charts are in the HTML, not injected by script.
    text = client.get("/").text
    assert text.count("<svg") >= 5


def test_stream_emits_server_sent_events(client):
    # `limit` bounds the stream so the test terminates; without it the generator
    # runs until the client disconnects.
    with client.stream("GET", "/api/stream?limit=1") as response:
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/event-stream")
        for line in response.iter_lines():
            if line.startswith("data: "):
                import json

                payload = json.loads(line[6:])
                assert "requests" in payload
                break


def test_stream_limit_zero_emits_nothing(client):
    with client.stream("GET", "/api/stream?limit=0") as response:
        assert response.status_code == 200
        assert [line for line in response.iter_lines() if line.startswith("data: ")] == []
