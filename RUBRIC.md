# Reviewer rubric: mechanical and hardware engineering responses

Automatic grading catches wrong final numbers. It does not catch a right number reached by wrong reasoning, an unsafe recommendation, or a missing validity check. This rubric is for human reviewers scoring AI model responses to engineering problems, and for writing feedback that a model or annotator can act on.

## Scoring dimensions (1 to 5 each)

### 1. Correctness of the final answer
| Score | Description |
|---|---|
| 5 | Within tolerance, correct units, correct sign or direction where relevant |
| 3 | Method correct, small arithmetic slip that changes the answer by under 10% |
| 1 | Wrong by a factor (2, 4, 2 pi, 1000) or a different quantity was computed |

### 2. Model and formula selection
Did the response pick the physics that matches the stated boundary conditions?

* Cantilever vs simply supported, pinned vs fixed column end conditions
* Von Mises vs Tresca when the problem names one
* Goodman vs Soderberg vs Gerber when the problem names one
* Ball bearing exponent 3 vs roller bearing exponent 10/3
* Hoop stress uses radius, not diameter

A response that silently swaps a model scores at most 2, even if the number happens to land close.

### 3. Units and dimensional consistency
* Every intermediate quantity carries a unit
* Conversions are shown (rpm to rad/s, mm to m, kN to N)
* Natural frequency in Hz is not reported as rad/s
* Temperature differences in K and absolute temperatures in C are not mixed up

### 4. Assumptions and validity checks
Strong responses state and check the assumptions that the formula depends on:

* Thin-wall theory: r/t of at least about 10
* Euler buckling: slenderness ratio above the Johnson transition
* Small deflection theory for beams
* Linear elastic behavior: stress below yield
* Steady state for thermal resistance networks

Missing a check that would have changed the conclusion scores 1. Missing a check that holds anyway scores 3 or 4.

### 5. Engineering judgment and safety
* Does the response flag a result that is physically implausible (a 3 mm shaft carrying 5 kW, a junction at 300 C)?
* Does it note when a safety factor below 1 means failure, and below about 1.5 means the design needs review?
* Does it avoid recommending an unsafe action (exceeding bolt proof load, ignoring stress concentration on a notched shaft)?

Any unsafe recommendation is an automatic fail for the response regardless of other scores.

## Error taxonomy

Use these labels when tagging failures so errors can be counted across a dataset. They match the `known_errors` labels in `problems/problems.jsonl` where possible.

| Label | Example |
|---|---|
| `wrong_formula` | 32T/(pi d^3) used for torsion |
| `wrong_boundary_condition` | Simply supported formula for a cantilever |
| `geometry_error` | Width and depth swapped in b h^3/12, diameter used for radius |
| `unit_conversion` | Missing 2 pi / 60, forgot 60 min per hour |
| `wrong_criterion` | Soderberg used when Goodman was asked |
| `omitted_factor` | Efficiency, Marin factor or stress concentration left out |
| `arithmetic` | Correct setup, calculation slip |
| `format` | No clearly stated final answer, or no units |
| `unsafe` | Recommendation that could cause failure or injury |

## Writing feedback

Good feedback names the error, points to the step where it happened, and gives the corrected value.

> The torsional shear formula is 16T/(pi d^3), not 32T/(pi d^3). The 32 belongs to the bending stress formula. With 16, tau = 63.7 MPa, half of the value given.

Weak feedback only says "incorrect" or restates the reference answer without explaining the cause.
