# mecheng-llm-eval

An evaluation set and automatic grader for testing how well AI models solve mechanical and hardware engineering problems, with a human reviewer rubric for the parts a script cannot judge.

The grader does more than check a number. It converts units, and when an answer is wrong it matches the value against **known error patterns** to report *why* the model failed, for example using the bending formula for torsion, or the diameter instead of the radius in hoop stress.

## What is inside

```
problems/
  build_problems.py   computes every reference answer from first principles (auditable)
  problems.jsonl      15 problems with answers, tolerances, solutions and known errors
grader/
  grade.py            answer extraction, unit conversion, tolerance check, error diagnosis
samples/
  model_responses.jsonl   example model outputs with typical mistakes
  sample_report.md        grading report generated from them
tests/
  test_grade.py       22 tests, including a check that no known error falls inside tolerance
RUBRIC.md             human review rubric and error taxonomy
```

## Coverage

| Domain | Problems |
|---|---|
| Solid mechanics (beams, torsion) | ME-001, ME-002, ME-004 |
| Failure theories | ME-003 |
| Fatigue | ME-006 |
| Machine design (power, gears, springs, bearings) | ME-005, ME-010, ME-013, ME-014 |
| Fasteners | ME-007 |
| Thermal and electronics cooling | ME-008, ME-012 |
| Pressure vessels | ME-009 |
| Stability (buckling) | ME-011 |
| Dynamics and vibration | ME-015 |

## Problem format

```json
{
  "id": "ME-004",
  "domain": "solid_mechanics",
  "difficulty": "easy",
  "question": "A solid circular steel shaft of 40 mm diameter transmits a torque of 800 N*m. Find the maximum torsional shear stress in MPa.",
  "answer": 63.661977,
  "unit": "MPa",
  "rel_tol": 0.01,
  "reference_solution": "tau = T c / J = 16 T / (pi d^3) = 63.7 MPa.",
  "known_errors": [
    {"value": 127.323954, "label": "used 32T/(pi d^3) (bending formula)"},
    {"value": 509.295818, "label": "used radius in place of diameter"}
  ]
}
```

Responses are JSONL with `id` and `response`. The response must contain a line `Final answer: <value> <unit>`.

## Usage

```bash
python problems/build_problems.py                      # regenerate the problem set
python grader/grade.py --responses samples/model_responses.jsonl --report report.md
pytest -q
```

Sample output:

```
ME-001  PASS             given=20.8 mm        expected=20.83 mm
ME-004  WRONG            given=127.3 MPa      expected=63.66 MPa  [known error: used 32T/(pi d^3) (bending formula)]
ME-007  PASS             given=67.15 lbf*ft   expected=91.04 N*m
ME-009  WRONG            given=150 MPa        expected=75 MPa  [known error: used diameter instead of radius]
ME-013  NO_FINAL_ANSWER  given=-              expected=5.808 N/mm  [response has no 'Final answer:' line]
ME-015  UNIT_ERROR       given=158.1 rad/s    expected=25.16 Hz  [unit 'rad/s' is not compatible with 'Hz'; matches known error: reported omega_n in rad/s as Hz]

accuracy: 7/15 (47%)
```

## Grading statuses

| Status | Meaning |
|---|---|
| `PASS` | Within relative tolerance after unit conversion |
| `WRONG` | Compatible units, wrong value; diagnosis names the matched error if any |
| `UNIT_ERROR` | Missing or dimensionally incompatible units |
| `NO_FINAL_ANSWER` | No `Final answer:` line, a format compliance failure |
| `MISSING` | No response for this problem ID |

## Design decisions

* **Answers are computed, never typed.** `build_problems.py` derives every reference value and every known wrong value, so a typo cannot create a bad label.
* **rad/s is deliberately not convertible to Hz.** Reporting angular natural frequency when cyclic frequency was asked is one of the most common model errors, so the grader treats it as a unit error instead of silently converting it.
* **Tolerances are per problem.** Closed-form problems use 1%, while problems that depend on rounded table values use 2%.
* **Self-checking dataset.** A test guarantees that no known error value lies inside the tolerance band of the correct answer.

## Related

[mechcalc](https://github.com/kevinfajardo25/mechcalc), a tested Python library of the same formulas used to cross-check answers.

## License

MIT
