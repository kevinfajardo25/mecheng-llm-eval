"""Grade model responses to mechanical engineering problems.

For every response the grader:
  1. extracts the final answer (requires a "Final answer: <value> <unit>" line),
  2. converts the unit to the problem's reference unit (mm vs m, kN vs N, psi vs MPa ...),
  3. checks it against the reference value within the problem's relative tolerance,
  4. if wrong, checks it against known wrong answers to diagnose the reasoning error.

Usage:
  python grader/grade.py --problems problems/problems.jsonl --responses samples/model_responses.jsonl
  python grader/grade.py ... --report report.md      # also write a Markdown report
"""
from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

# unit -> (dimension, factor to SI base for that dimension)
UNITS = {
    # length
    "m": ("length", 1.0), "cm": ("length", 1e-2), "mm": ("length", 1e-3), "um": ("length", 1e-6),
    "in": ("length", 0.0254), "ft": ("length", 0.3048),
    # stress / pressure
    "pa": ("stress", 1.0), "kpa": ("stress", 1e3), "mpa": ("stress", 1e6), "gpa": ("stress", 1e9),
    "n/mm^2": ("stress", 1e6), "n/mm2": ("stress", 1e6), "psi": ("stress", 6894.757), "ksi": ("stress", 6894757.0),
    "bar": ("stress", 1e5),
    # force
    "n": ("force", 1.0), "kn": ("force", 1e3), "mn": ("force", 1e6), "lbf": ("force", 4.448222),
    # torque / moment
    "n*m": ("torque", 1.0), "nm": ("torque", 1.0), "n-m": ("torque", 1.0), "n.m": ("torque", 1.0),
    "kn*m": ("torque", 1e3), "n*mm": ("torque", 1e-3), "lbf*ft": ("torque", 1.355818), "lb-ft": ("torque", 1.355818),
    "lbf*in": ("torque", 0.1129848), "lb-in": ("torque", 0.1129848),
    # stiffness
    "n/m": ("stiffness", 1.0), "n/mm": ("stiffness", 1e3), "kn/m": ("stiffness", 1e3), "lbf/in": ("stiffness", 175.1268),
    # time
    "h": ("time", 3600.0), "hr": ("time", 3600.0), "hrs": ("time", 3600.0), "hours": ("time", 3600.0),
    "min": ("time", 60.0), "s": ("time", 1.0),
    # frequency (rad/s deliberately NOT convertible: reporting omega_n as f_n is a graded error)
    "hz": ("frequency", 1.0), "khz": ("frequency", 1e3), "rpm": ("rotation", 1.0),
    # temperature (absolute, Celsius only)
    "c": ("temperature_c", 1.0), "degc": ("temperature_c", 1.0),
    # dimensionless
    "": ("dimensionless", 1.0),
}

_NUM = r"[-+]?(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?(?:[eE][-+]?\d+)?"
FINAL_RE = re.compile(rf"final\s+answer\s*[:=]\s*(?:\S+\s*=\s*)?\**\s*({_NUM})\s*([^\n]*)", re.IGNORECASE)


def normalize_unit(raw: str) -> str:
    u = raw.strip().rstrip(".").strip()
    u = u.replace("·", "*").replace("×", "*").replace("°", "deg").replace("µ", "u").replace(" ", "")
    u = u.replace("degc", "c").replace("degC", "c")
    u = u.lower()
    if u.startswith("(") or u in ("(dimensionless)", "dimensionless", "-"):
        u = ""
    return u


def convert(value: float, from_unit: str, to_unit: str) -> float | None:
    """Convert value between units of the same dimension; None if incompatible/unknown."""
    a, b = UNITS.get(normalize_unit(from_unit)), UNITS.get(normalize_unit(to_unit))
    if a is None or b is None or a[0] != b[0]:
        return None
    return value * a[1] / b[1]


def extract_final_answer(text: str) -> tuple[float, str] | None:
    matches = FINAL_RE.findall(text)
    if not matches:
        return None
    num, unit = matches[-1]
    # drop trailing commentary such as "mm (downward)" or "MPa, compressive"
    unit = unit.strip().rstrip("*").strip()
    unit = re.split(r"\s+\(|,|;|\s+-\s|\s+(?:at|in|which|compressive|tensile)\b", unit.strip())[0]
    return float(num.replace(",", "")), unit.strip()


@dataclass
class Result:
    id: str
    domain: str
    status: str                 # PASS | WRONG | UNIT_ERROR | NO_FINAL_ANSWER | MISSING
    given: str = ""
    expected: str = ""
    diagnosis: str = ""
    rel_error: float | None = None
    notes: list = field(default_factory=list)


def grade_one(problem: dict, response: str | None) -> Result:
    expected = f"{problem['answer']:.4g} {problem['unit']}".strip()
    res = Result(problem["id"], problem["domain"], "MISSING", expected=expected)
    if response is None:
        return res
    parsed = extract_final_answer(response)
    if parsed is None:
        res.status = "NO_FINAL_ANSWER"
        res.diagnosis = "response has no 'Final answer:' line"
        return res
    value, unit = parsed
    res.given = f"{value:g} {unit}".strip()
    # a bare number for a dimensioned answer is a unit error, not a pass
    if problem["unit"] and not unit:
        res.status = "UNIT_ERROR"
        res.diagnosis = "answer given without units"
        return res
    converted = convert(value, unit, problem["unit"])
    if converted is None:
        res.status = "UNIT_ERROR"
        res.diagnosis = f"unit '{unit}' is not compatible with '{problem['unit']}'"
        # still try to diagnose against known errors using the raw number
        converted = value
        for err in problem.get("known_errors", []):
            if _close(converted, err["value"], problem["rel_tol"]):
                res.diagnosis += f"; matches known error: {err['label']}"
        return res
    res.rel_error = abs(converted - problem["answer"]) / abs(problem["answer"])
    if _close(converted, problem["answer"], problem["rel_tol"]):
        res.status = "PASS"
        if normalize_unit(unit) != normalize_unit(problem["unit"]):
            res.notes.append(f"correct after converting {unit} -> {problem['unit']}")
        return res
    res.status = "WRONG"
    for err in problem.get("known_errors", []):
        if _close(converted, err["value"], problem["rel_tol"]):
            res.diagnosis = f"known error: {err['label']}"
            break
    else:
        res.diagnosis = f"off by {res.rel_error:.1%}, no known error pattern matched"
    return res


def _close(a: float, b: float, rel_tol: float) -> bool:
    return abs(a - b) <= rel_tol * max(abs(b), 1e-12)


def load_jsonl(path: Path) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def grade(problems: list[dict], responses: list[dict]) -> list[Result]:
    by_id = {r["id"]: r["response"] for r in responses}
    return [grade_one(p, by_id.get(p["id"])) for p in problems]


def summarize(results: list[Result]) -> dict:
    total = len(results)
    passed = sum(r.status == "PASS" for r in results)
    by_domain = defaultdict(lambda: [0, 0])
    for r in results:
        by_domain[r.domain][1] += 1
        by_domain[r.domain][0] += r.status == "PASS"
    by_status = defaultdict(int)
    for r in results:
        by_status[r.status] += 1
    return {"total": total, "passed": passed, "accuracy": passed / total if total else 0.0,
            "by_domain": dict(by_domain), "by_status": dict(by_status)}


def to_markdown(results: list[Result], summary: dict) -> str:
    lines = ["# Grading report", "",
             f"**Accuracy:** {summary['passed']}/{summary['total']} ({summary['accuracy']:.0%})", "",
             "| ID | Domain | Status | Given | Expected | Diagnosis |", "|---|---|---|---|---|---|"]
    for r in results:
        diag = "; ".join(filter(None, [r.diagnosis, *r.notes]))
        lines.append(f"| {r.id} | {r.domain} | {r.status} | {r.given} | {r.expected} | {diag} |")
    lines += ["", "## By domain", "", "| Domain | Passed | Total |", "|---|---|---|"]
    for d, (p, t) in sorted(summary["by_domain"].items()):
        lines.append(f"| {d} | {p} | {t} |")
    return "\n".join(lines) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--problems", type=Path, default=Path("problems/problems.jsonl"))
    ap.add_argument("--responses", type=Path, required=True)
    ap.add_argument("--report", type=Path, help="optional Markdown report path")
    args = ap.parse_args()

    results = grade(load_jsonl(args.problems), load_jsonl(args.responses))
    summary = summarize(results)
    for r in results:
        extra = f"  [{r.diagnosis}]" if r.diagnosis else ""
        print(f"{r.id}  {r.status:<16} given={r.given or '-':<14} expected={r.expected}{extra}")
    print(f"\naccuracy: {summary['passed']}/{summary['total']} ({summary['accuracy']:.0%})")
    print("status counts:", summary["by_status"])
    if args.report:
        args.report.write_text(to_markdown(results, summary), encoding="utf-8")
        print(f"report written to {args.report}")


if __name__ == "__main__":
    main()
