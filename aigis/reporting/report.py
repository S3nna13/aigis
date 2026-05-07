import json
from typing import Sequence

from aigis.eval.metrics import MetricResult


def format_results(results: Sequence[MetricResult], fmt: str = "table") -> str:
    match fmt:
        case "json":
            return json.dumps(
                [{"name": r.name, "score": r.score, "passed": r.passed, "reason": r.reason} for r in results],
                indent=2,
            )
        case "html":
            return _to_html(results)
        case "table":
            return _to_table(results)
        case _:
            return _to_table(results)


def _to_table(results: Sequence[MetricResult]) -> str:
    lines = ["Metric                Score    Passed  Reason", "-" * 72]
    for r in results:
        status = "PASS" if r.passed else "FAIL"
        reason_short = (r.reason or "")[:45]
        lines.append(f"{r.name:<20} {r.score:<8.2f} {status:<7} {reason_short}")
    return "\n".join(lines)


def _to_html(results: Sequence[MetricResult]) -> str:
    rows = "\n".join(
        f"""<tr>
          <td>{r.name}</td>
          <td>{r.score:.2f}</td>
          <td class="{'pass' if r.passed else 'fail'}">{'PASS' if r.passed else 'FAIL'}</td>
          <td>{r.reason or ''}</td>
        </tr>"""
        for r in results
    )
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>AIGIS Report</title>
  <style>
    body {{ font-family: system-ui, sans-serif; max-width: 960px; margin: 2rem auto; padding: 0 1rem; }}
    table {{ width: 100%; border-collapse: collapse; }}
    th, td {{ padding: 0.75rem; text-align: left; border-bottom: 1px solid #e5e7eb; }}
    th {{ background: #f9fafb; font-weight: 600; }}
    .pass {{ color: #059669; font-weight: 600; }}
    .fail {{ color: #dc2626; font-weight: 600; }}
    h1 {{ color: #111827; }}
  </style>
</head>
<body>
  <h1>AIGIS Evaluation Report</h1>
  <table>
    <thead><tr><th>Metric</th><th>Score</th><th>Status</th><th>Reason</th></tr></thead>
    <tbody>{rows}</tbody>
  </table>
</body>
</html>"""
