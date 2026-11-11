# Grading report

**Accuracy:** 7/15 (47%)

| ID | Domain | Status | Given | Expected | Diagnosis |
|---|---|---|---|---|---|
| ME-001 | solid_mechanics | PASS | 20.8 mm | 20.83 mm |  |
| ME-002 | solid_mechanics | WRONG | 14.8 mm | 25 mm | known error: used solid section I |
| ME-003 | failure_theory | PASS | 128.5 MPa | 128.5 MPa |  |
| ME-004 | solid_mechanics | WRONG | 127.3 MPa | 63.66 MPa | known error: used 32T/(pi d^3) (bending formula) |
| ME-005 | machine_design | PASS | 98.8 N·m | 98.79 N*m |  |
| ME-006 | fatigue | WRONG | 1.25 | 1.357 | known error: Soderberg (used Sy) |
| ME-007 | fasteners | PASS | 67.15 lbf*ft | 91.04 N*m | correct after converting lbf*ft -> N*m |
| ME-008 | thermal | PASS | 89 °C | 89 C |  |
| ME-009 | pressure_vessels | WRONG | 150 MPa | 75 MPa | known error: used diameter instead of radius |
| ME-010 | machine_design | WRONG | 90 N*m | 81.22 N*m | known error: ignored efficiency |
| ME-011 | stability | PASS | 10766 N | 10.77 kN | correct after converting N -> kN |
| ME-012 | thermal | PASS | 144 MPa | 144 MPa |  |
| ME-013 | machine_design | NO_FINAL_ANSWER |  | 5.808 N/mm | response has no 'Final answer:' line |
| ME-014 | machine_design | WRONG | 180000 h | 3000 h | known error: forgot the 60 min/h conversion |
| ME-015 | dynamics | UNIT_ERROR | 158.1 rad/s | 25.16 Hz | unit 'rad/s' is not compatible with 'Hz'; matches known error: reported omega_n in rad/s as Hz |

## By domain

| Domain | Passed | Total |
|---|---|---|
| dynamics | 0 | 1 |
| failure_theory | 1 | 1 |
| fasteners | 1 | 1 |
| fatigue | 0 | 1 |
| machine_design | 1 | 4 |
| pressure_vessels | 0 | 1 |
| solid_mechanics | 1 | 3 |
| stability | 1 | 1 |
| thermal | 2 | 2 |
