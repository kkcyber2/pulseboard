from pulseboard.charts import area_chart, bar_breakdown, sparkline


def test_sparkline_emits_an_svg_with_a_polyline():
    svg = sparkline([1, 3, 2, 5, 4])
    assert svg.startswith("<svg")
    assert "<polyline" in svg
    assert svg.count("<svg") == 1


def test_sparkline_handles_too_few_points():
    assert "no data" in sparkline([1])


def test_sparkline_handles_an_empty_series():
    assert "no data" in sparkline([])


def test_sparkline_handles_a_flat_series():
    svg = sparkline([5, 5, 5, 5])
    assert "<polyline" in svg
    assert "nan" not in svg.lower()


def test_area_chart_has_gridlines_and_ticks():
    svg = area_chart([1, 4, 2, 8, 5, 9])
    # Count "<line " with the space, so <linearGradient is not matched too.
    assert svg.count("<line ") == 5
    assert svg.count("chart__tick") == 5


def test_area_chart_escapes_the_label():
    svg = area_chart([1, 2, 3], label='<script>alert(1)</script>')
    assert "<script>" not in svg
    assert "&lt;script&gt;" in svg


def test_area_chart_handles_too_few_points():
    assert "no data" in area_chart([1])


def test_bar_breakdown_renders_one_row_per_item():
    svg = bar_breakdown([("a", 10), ("b", 5)])
    assert svg.count("<rect") == 2
    assert ">a<" in svg


def test_bar_breakdown_handles_empty_input():
    assert "no data" in bar_breakdown([])


def test_bar_breakdown_handles_all_zero_values():
    svg = bar_breakdown([("a", 0), ("b", 0)])
    assert "<rect" in svg
    assert "nan" not in svg.lower()
