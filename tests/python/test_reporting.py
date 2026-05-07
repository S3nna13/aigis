from aigis.reporting.report import format_results
from aigis.eval.metrics import MetricResult
import json


def _make_results():
    return [
        MetricResult(name="exact_match", score=1.0, reason="Matched"),
        MetricResult(name="contains", score=0.0, reason="Not found"),
    ]


def test_format_json():
    out = format_results(_make_results(), fmt="json")
    data = json.loads(out)
    assert len(data) == 2
    assert data[0]["name"] == "exact_match"


def test_format_table():
    out = format_results(_make_results(), fmt="table")
    assert "exact_match" in out
    assert "contains" in out
    assert "PASS" in out
    assert "FAIL" in out


def test_format_html():
    out = format_results(_make_results(), fmt="html")
    assert "<html" in out
    assert "exact_match" in out
    assert "AIGIS Report" in out


def test_format_markdown():
    out = format_results(_make_results(), fmt="markdown")
    assert "# AIGIS Evaluation Report" in out
    assert "| exact_match" in out
    assert "| contains" in out
    assert "Summary" in out
