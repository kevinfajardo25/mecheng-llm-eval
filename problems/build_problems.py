"""Generate problems.jsonl with reference answers computed from first principles.

Answers are never typed by hand: each one is computed here so the derivation is
auditable. Each problem also lists "known wrong answers" that correspond to
common reasoning errors, so the grader can tag *why* a response failed.

Run:  python problems/build_problems.py
"""
import json
import math
from pathlib import Path

OUT = Path(__file__).with_name("problems.jsonl")
problems = []


def add(pid, domain, difficulty, question, answer, unit, rel_tol, solution, wrong=None):
    problems.append({
        "id": pid,
        "domain": domain,
        "difficulty": difficulty,
        "question": question,
        "answer": round(answer, 6),
        "unit": unit,
        "rel_tol": rel_tol,
        "reference_solution": solution,
        "known_errors": [{"value": round(v, 6), "label": label} for label, v in (wrong or {}).items()],
    })


# 1 Cantilever deflection
b, h, L, P, E = 0.030, 0.060, 1.5, 2000.0, 200e9
I = b * h**3 / 12
d = P * L**3 / (3 * E * I)
I_swapped = h * b**3 / 12
add("ME-001", "solid_mechanics", "easy",
    "A steel cantilever (E = 200 GPa) is 1.5 m long with a solid rectangular section 30 mm wide and "
    "60 mm deep (load acts in the depth direction). A 2 kN point load acts at the free end. "
    "Find the tip deflection in mm.",
    d * 1e3, "mm", 0.02,
    "I = b h^3/12 = 0.03(0.06)^3/12 = 5.4e-7 m^4. delta = P L^3 / (3 E I) = 2000(1.5)^3/(3*200e9*5.4e-7) = 20.8 mm.",
    {"width and depth swapped in I": P * L**3 / (3 * E * I_swapped) * 1e3,
     "used simply supported PL^3/48EI": P * L**3 / (48 * E * I) * 1e3})

# 2 Simply supported UDL, tube
Do, Di, L, w, E = 0.050, 0.040, 2.0, 1500.0, 69e9
I = math.pi * (Do**4 - Di**4) / 64
d = 5 * w * L**4 / (384 * E * I)
add("ME-002", "solid_mechanics", "medium",
    "A simply supported aluminum tube (E = 69 GPa), span 2.0 m, outer diameter 50 mm, inner diameter "
    "40 mm, carries a uniformly distributed load of 1.5 kN/m. Find the maximum deflection in mm.",
    d * 1e3, "mm", 0.02,
    "I = pi(Do^4 - Di^4)/64 = 1.811e-7 m^4. delta = 5 w L^4/(384 E I) = 25.0 mm.",
    {"used cantilever wL^4/8EI": w * L**4 / (8 * E * I) * 1e3,
     "used solid section I": 5 * w * L**4 / (384 * E * math.pi * Do**4 / 64) * 1e3})

# 3 Von Mises from plane stress
sx, sy, txy = 90.0, -30.0, -40.0
vm = math.sqrt(sx**2 - sx * sy + sy**2 + 3 * txy**2)
c, r = (sx + sy) / 2, math.hypot((sx - sy) / 2, txy)
tresca = max(c + r, 0) - min(c - r, 0)
add("ME-003", "failure_theory", "easy",
    "A point in a machine part has plane stress sigma_x = 90 MPa, sigma_y = -30 MPa, tau_xy = -40 MPa. "
    "Find the von Mises equivalent stress in MPa.",
    vm, "MPa", 0.01,
    "sigma_vm = sqrt(sx^2 - sx sy + sy^2 + 3 txy^2) = sqrt(8100 + 2700 + 900 + 4800) = 128.5 MPa.",
    {"Tresca equivalent instead of von Mises": tresca,
     "sign error on sx*sy term": math.sqrt(sx**2 + sx * sy + sy**2 + 3 * txy**2)})

# 4 Torsional shear in a solid shaft
dd, T = 0.040, 800.0
tau = 16 * T / (math.pi * dd**3)
add("ME-004", "solid_mechanics", "easy",
    "A solid circular steel shaft of 40 mm diameter transmits a torque of 800 N*m. "
    "Find the maximum torsional shear stress in MPa.",
    tau / 1e6, "MPa", 0.01,
    "tau = T c / J = 16 T / (pi d^3) = 16(800)/(pi 0.04^3) = 63.7 MPa.",
    {"used 32T/(pi d^3) (bending formula)": 32 * T / (math.pi * dd**3) / 1e6,
     "used radius in place of diameter": 16 * T / (math.pi * (dd / 2) ** 3) / 1e6})

# 5 Power to torque
Pw, n = 15000.0, 1450.0
T = Pw / (2 * math.pi * n / 60)
add("ME-005", "machine_design", "easy",
    "An electric motor delivers 15 kW at 1450 rpm. What torque does it deliver, in N*m?",
    T, "N*m", 0.01,
    "omega = 2 pi n / 60 = 151.8 rad/s. T = P / omega = 98.8 N*m.",
    {"forgot 2*pi/60 (used rpm as rad/s)": Pw / n,
     "used rev/s without 2*pi": Pw / (n / 60)})

# 6 Goodman fatigue
sa, sm, Se, Sut, Sy = 120.0, 180.0, 250.0, 700.0, 560.0
nG = 1 / (sa / Se + sm / Sut)
add("ME-006", "fatigue", "medium",
    "A steel part has alternating stress 120 MPa and mean stress 180 MPa. The fully corrected endurance "
    "limit is 250 MPa, Sut = 700 MPa and Sy = 560 MPa. Using the modified Goodman criterion, find the "
    "fatigue factor of safety.",
    nG, "", 0.01,
    "1/n = sa/Se + sm/Sut = 120/250 + 180/700 = 0.737, so n = 1.36.",
    {"Soderberg (used Sy)": 1 / (sa / Se + sm / Sy),
     "ignored mean stress": Se / sa})

# 7 Bolt torque
At, Sp, K, db = 84.3, 600.0, 0.2, 0.012
Fi = 0.75 * At * Sp
Tq = K * Fi * db
add("ME-007", "fasteners", "medium",
    "An M12 x 1.75 ISO class 8.8 bolt (tensile stress area 84.3 mm^2, proof strength 600 MPa) is to be "
    "preloaded to 75% of proof load for a reusable joint. Using a torque coefficient K = 0.2, find the "
    "required tightening torque in N*m.",
    Tq, "N*m", 0.02,
    "Fp = At Sp = 50.6 kN. Fi = 0.75 Fp = 37.9 kN. T = K Fi d = 0.2(37935)(0.012) = 91.0 N*m.",
    {"used 100% of proof load": K * At * Sp * db,
     "used 90% (permanent joint)": K * 0.9 * At * Sp * db})

# 8 Junction temperature
Q, Ta, Rjc, Rtim, Rsa = 40.0, 35.0, 0.30, 0.15, 0.90
Tj = Ta + Q * (Rjc + Rtim + Rsa)
add("ME-008", "thermal", "easy",
    "A 40 W power device sits in 35 C ambient air. Thermal resistances are junction-to-case 0.30 K/W, "
    "thermal interface 0.15 K/W and heatsink-to-air 0.90 K/W. Find the junction temperature in C.",
    Tj, "C", 0.005,
    "Tj = Ta + Q(Rjc + Rtim + Rsa) = 35 + 40(1.35) = 89 C.",
    {"treated resistances in parallel": Ta + Q / (1 / Rjc + 1 / Rtim + 1 / Rsa),
     "omitted TIM resistance": Ta + Q * (Rjc + Rsa)})

# 9 Thin-wall pressure vessel
p, D, t = 1.2e6, 1.0, 0.008
hoop = p * (D / 2) / t
add("ME-009", "pressure_vessels", "easy",
    "A thin-walled cylindrical air receiver has an inside diameter of 1.0 m and wall thickness 8 mm, "
    "with internal pressure 1.2 MPa. Find the hoop stress in MPa.",
    hoop / 1e6, "MPa", 0.01,
    "sigma_h = p r / t = 1.2e6(0.5)/0.008 = 75 MPa. (r/t = 62.5, thin-wall theory is valid.)",
    {"used diameter instead of radius": p * D / t / 1e6,
     "gave longitudinal stress pr/2t": p * (D / 2) / (2 * t) / 1e6})

# 10 Compound gear train
Tin, eff = 10.0, 0.95
ratio = (60 / 20) * (54 / 18)
Tout = Tin * ratio * eff**2
add("ME-010", "machine_design", "medium",
    "A compound gear train has a 20-tooth pinion driving a 60-tooth gear; on the same shaft an 18-tooth "
    "pinion drives a 54-tooth output gear. Input torque is 10 N*m and each mesh is 95% efficient. "
    "Find the output torque in N*m.",
    Tout, "N*m", 0.01,
    "Ratio = (60/20)(54/18) = 9. T_out = 10 * 9 * 0.95^2 = 81.2 N*m.",
    {"ignored efficiency": Tin * ratio,
     "applied efficiency once": Tin * ratio * eff})

# 11 Euler buckling
dr, Lc, E = 0.020, 1.2, 200e9
I = math.pi * dr**4 / 64
Pcr = math.pi**2 * E * I / Lc**2
add("ME-011", "stability", "medium",
    "A pinned-pinned solid steel rod (E = 200 GPa), 20 mm diameter and 1.2 m long, is loaded in axial "
    "compression. Find the Euler critical buckling load in kN.",
    Pcr / 1e3, "kN", 0.02,
    "I = pi d^4/64 = 7.854e-9 m^4. Pcr = pi^2 E I / L^2 = 10.8 kN. Check slenderness: L/k = 240, Euler applies.",
    {"used fixed-free effective length 2L": math.pi**2 * E * I / (2 * Lc) ** 2 / 1e3,
     "used polar moment J instead of I": math.pi**2 * E * (2 * I) / Lc**2 / 1e3})

# 12 Thermal stress
alpha, dT, E = 12e-6, 60.0, 200e9
sig = E * alpha * dT
add("ME-012", "thermal", "easy",
    "A steel bar (E = 200 GPa, alpha = 12e-6 /K) is rigidly fixed at both ends and heated uniformly by "
    "60 K. Find the magnitude of the thermal stress in MPa.",
    sig / 1e6, "MPa", 0.01,
    "Free strain alpha dT is fully restrained: sigma = E alpha dT = 200e9(12e-6)(60) = 144 MPa (compressive).",
    {"divided by 2 (assumed half restrained)": sig / 2e6})

# 13 Helical spring rate
G, dw, Dm, Na = 79.3e9, 0.003, 0.024, 10
k = G * dw**4 / (8 * Dm**3 * Na)
add("ME-013", "machine_design", "medium",
    "A helical compression spring is wound from 3 mm music wire (G = 79.3 GPa) with a mean coil diameter "
    "of 24 mm and 10 active coils. Find the spring rate in N/mm.",
    k / 1e3, "N/mm", 0.02,
    "k = G d^4 / (8 D^3 Na) = 79.3e9(0.003)^4 / (8(0.024)^3(10)) = 5.81 N/mm.",
    {"used outside diameter 27 mm": G * dw**4 / (8 * (Dm + dw) ** 3 * Na) / 1e3,
     "used total coils 12": G * dw**4 / (8 * Dm**3 * 12) / 1e3})

# 14 Bearing life
C, Pb, rpm = 30.0, 5.0, 1200.0
L10_h = (C / Pb) ** 3 * 1e6 / (rpm * 60)
add("ME-014", "machine_design", "medium",
    "A deep-groove ball bearing has a basic dynamic load rating of 30 kN and carries an equivalent "
    "radial load of 5 kN at 1200 rpm. Find its L10 rating life in hours.",
    L10_h, "h", 0.01,
    "L10 = (C/P)^3 = 216 million revolutions. Hours = 216e6 / (1200 * 60) = 3000 h.",
    {"used roller-bearing exponent 10/3": (C / Pb) ** (10 / 3) * 1e6 / (rpm * 60),
     "forgot the 60 min/h conversion": (C / Pb) ** 3 * 1e6 / rpm})

# 15 Natural frequency
m, ks = 2.0, 50e3
fn = math.sqrt(ks / m) / (2 * math.pi)
add("ME-015", "dynamics", "easy",
    "A 2 kg mass is mounted on a spring of stiffness 50 kN/m. Find the undamped natural frequency in Hz.",
    fn, "Hz", 0.01,
    "omega_n = sqrt(k/m) = 158.1 rad/s. f_n = omega_n / 2 pi = 25.2 Hz.",
    {"reported omega_n in rad/s as Hz": math.sqrt(ks / m)})

OUT.write_text("".join(json.dumps(p) + "\n" for p in problems))
print(f"wrote {len(problems)} problems to {OUT}")
for p in problems:
    print(f"  {p['id']}  {p['answer']:>12.4f} {p['unit']:<5} {p['domain']}")
