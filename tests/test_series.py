import pytest

from pulseboard.series import MetricStore, seed_demo


def test_metric_tracks_latest_and_delta():
    store = MetricStore()
    metric = store.register("m", "Metric")
    metric.add(10, at=1)
    metric.add(15, at=2)
    assert metric.latest == 15
    assert metric.delta == 5
    assert metric.delta_pct == 50.0
    assert metric.trend == "up"


def test_trend_is_flat_for_a_tiny_change():
    store = MetricStore()
    metric = store.register("m", "Metric")
    metric.add(100, at=1)
    metric.add(100.1, at=2)
    assert metric.trend == "flat"


def test_trend_is_down_for_a_drop():
    store = MetricStore()
    metric = store.register("m", "Metric")
    metric.add(100, at=1)
    metric.add(80, at=2)
    assert metric.trend == "down"


def test_delta_pct_with_zero_previous_is_zero():
    store = MetricStore()
    metric = store.register("m", "Metric")
    metric.add(0, at=1)
    metric.add(5, at=2)
    assert metric.delta_pct == 0.0


def test_mean_and_stdev():
    store = MetricStore()
    metric = store.register("m", "Metric")
    for value in (2, 4, 4, 4, 5, 5, 7, 9):
        metric.add(value)
    assert metric.mean() == 5.0
    assert abs(metric.stdev() - 2.138) < 0.01


def test_stdev_of_a_single_sample_is_zero():
    store = MetricStore()
    metric = store.register("m", "Metric")
    metric.add(3)
    assert metric.stdev() == 0.0


def test_samples_are_bounded():
    store = MetricStore()
    metric = store.register("m", "Metric")
    for index in range(500):
        metric.add(index)
    assert len(metric.samples) == 240


def test_adding_to_an_unknown_metric_raises():
    with pytest.raises(KeyError):
        MetricStore().add("nope", 1)


def test_seed_demo_registers_four_metrics():
    store = MetricStore()
    seed_demo(store, points=10)
    assert {m.key for m in store.all()} == {"requests", "latency_p95", "error_rate", "active_users"}


def test_seed_demo_is_deterministic():
    first, second = MetricStore(), MetricStore()
    seed_demo(first, points=5, seed=3)
    seed_demo(second, points=5, seed=3)
    assert first.get("requests").values == second.get("requests").values


def test_public_dict_is_serialisable():
    import json

    store = MetricStore()
    seed_demo(store, points=5)
    json.dumps([m.public() for m in store.all()])
