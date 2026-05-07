import asyncio

from aigis.eval.metrics import Contains, ExactMatch, MetricResult


def test_exact_match_pass():
    m = ExactMatch()
    result = asyncio.run(m.measure(input="q", output="42", expected="42"))
    assert isinstance(result, MetricResult)
    assert result.score == 1.0
    assert result.passed is True


def test_exact_match_fail():
    m = ExactMatch()
    result = asyncio.run(m.measure(input="q", output="43", expected="42"))
    assert result.score == 0.0
    assert result.passed is False


def test_contains_pass():
    m = Contains()
    result = asyncio.run(m.measure(input="q", output="The answer is 42", expected="42"))
    assert result.score == 1.0
    assert result.passed is True


def test_contains_fail():
    m = Contains()
    result = asyncio.run(m.measure(input="q", output="The answer is 99", expected="42"))
    assert result.score == 0.0
    assert result.passed is False


def test_contains_no_expected():
    m = Contains()
    result = asyncio.run(m.measure(input="q", output="something", expected=None))
    assert result.score == 0.0
