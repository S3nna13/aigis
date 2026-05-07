import asyncio

from aigis.eval.metrics import RegexMatch, SafetyCheck, CustomMetric, FactualCheck


def test_regex_match_pass():
    m = RegexMatch(pattern=r"\d+")
    result = asyncio.run(m.measure(input="q", output="The answer is 42", expected=None))
    assert result.score == 1.0
    assert result.passed is True


def test_regex_match_fail():
    m = RegexMatch(pattern=r"^\d+$")
    result = asyncio.run(m.measure(input="q", output="not a number", expected=None))
    assert result.score == 0.0


def test_regex_match_invalid_pattern():
    m = RegexMatch(pattern=r"[invalid")
    result = asyncio.run(m.measure(input="q", output="hello", expected=None))
    assert "Invalid regex" in result.reason


def test_safety_keyword_check_clean():
    s = SafetyCheck()
    result = asyncio.run(s.measure(input="q", output="The weather is nice", expected=None))
    assert result.score == 1.0
    assert result.passed is True


def test_safety_keyword_check_flagged():
    s = SafetyCheck()
    result = asyncio.run(s.measure(input="q", output="violence is bad", expected=None))
    assert result.score == 0.0
    assert result.passed is False


def test_custom_metric_boolean():
    c = CustomMetric(name="len_check", eval_fn="len(output) > 5")
    result = asyncio.run(c.measure(input="q", output="hello world", expected=None))
    assert result.score == 1.0
    assert result.name == "len_check"


def test_custom_metric_numeric():
    c = CustomMetric(name="ratio", eval_fn="len(output) / 10.0")
    result = asyncio.run(c.measure(input="q", output="hello", expected=None))
    assert result.score == 0.5


def test_custom_metric_no_fn():
    c = CustomMetric()
    result = asyncio.run(c.measure(input="q", output="hello", expected=None))
    assert result.score == 0.5


def test_custom_metric_error():
    c = CustomMetric(name="bad", eval_fn="1 / 0")
    result = asyncio.run(c.measure(input="q", output="hello", expected=None))
    assert result.score == 0.0
    assert "error" in result.reason.lower()


def test_factual_check_no_model():
    f = FactualCheck()
    result = asyncio.run(
        f.measure(input="q", output="Paris is capital of France", expected="Paris")
    )
    assert result.score == 0.5
