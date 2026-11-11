import json
import math
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "grader"))

import grade  # noqa: E402

PROBLEMS = grade.load_jsonl(ROOT / "problems" / "problems.jsonl")
P = {p["id"]: p for p in PROBLEMS}


@pytest.mark.parametrize("text,expected", [
    ("Final answer: 20.8 mm", (20.8, "mm")),
    ("final answer = 1,250 N", (1250.0, "N")),
    ("**Final answer: 63.7 MPa**", (63.7, "MPa")),
    ("Final answer: 144 MPa (compressive)", (144.0, "MPa")),
    ("Final answer: 1.36", (1.36, "")),
    ("Final answer: 2.5e3 N/mm", (2500.0, "N/mm")),
    ("Final answer: T = 98.8 N·m", (98.8, "N·m")),
])
def test_extract(text, expected):
    assert grade.extract_final_answer(text) == expected


def test_no_final_answer():
    assert grade.extract_final_answer("the answer is 5 mm") is None


@pytest.mark.parametrize("v,a,b,out", [
    (20.8, "mm", "m", 0.0208),
    (10766, "N", "kN", 10.766),
    (67.15, "lbf*ft", "N*m", 91.04),
    (10, "ksi", "MPa", 68.95),
    (89, "°C", "C", 89),
])
def test_convert(v, a, b, out):
    assert grade.convert(v, a, b) == pytest.approx(out, rel=1e-3)


def test_incompatible_units():
    assert grade.convert(1, "rad/s", "Hz") is None
    assert grade.convert(1, "N", "N*m") is None


def test_pass_with_unit_conversion():
    r = grade.grade_one(P["ME-011"], "Final answer: 10766 N")
    assert r.status == "PASS"
    assert r.notes


def test_known_error_is_diagnosed():
    r = grade.grade_one(P["ME-004"], "Final answer: 127.3 MPa")
    assert r.status == "WRONG"
    assert "32T" in r.diagnosis


def test_missing_units_is_unit_error():
    assert grade.grade_one(P["ME-001"], "Final answer: 20.8").status == "UNIT_ERROR"


def test_dimensionless_answer():
    assert grade.grade_one(P["ME-006"], "Final answer: 1.36").status == "PASS"


def test_reference_answers_pass_their_own_grader():
    for p in PROBLEMS:
        r = grade.grade_one(p, f"Final answer: {p['answer']} {p['unit']}")
        assert r.status == "PASS", p["id"]


def test_known_errors_are_outside_tolerance():
    # A known-error value must never be accepted as correct
    for p in PROBLEMS:
        for err in p["known_errors"]:
            assert not math.isclose(err["value"], p["answer"], rel_tol=p["rel_tol"]), (p["id"], err)


def test_problem_schema():
    ids = [p["id"] for p in PROBLEMS]
    assert len(ids) == len(set(ids))
    for p in PROBLEMS:
        assert {"id", "domain", "difficulty", "question", "answer", "unit", "rel_tol",
                "reference_solution", "known_errors"} <= p.keys()
        assert p["unit"] in grade.UNITS or grade.normalize_unit(p["unit"]) in grade.UNITS


def test_sample_run_summary():
    responses = grade.load_jsonl(ROOT / "samples" / "model_responses.jsonl")
    s = grade.summarize(grade.grade(PROBLEMS, responses))
    assert s["total"] == 15
    assert s["passed"] == 7
