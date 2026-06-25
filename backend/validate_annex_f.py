"""
Annex F Validation Script
Runs the office example directly through the backend engines
and prints all results so you can compare against the IEC Annex F reference.

Usage (from the backend folder):
    python validate_annex_f.py
"""

from examples.office_annex_f import create_office_annex_f
from engines.risk_engine import RiskEngine
from engines.frequency_engine import FrequencyEngine
from engines.annex_e_risk_engine import AnnexERiskEngine


def fmt(v):
    if v is None:
        return "-"
    if isinstance(v, (int, float)):
        return f"{v:.4e}"
    return str(v)


def main():
    print("=" * 70)
    print("ANNEX F OFFICE EXAMPLE — VALIDATION RUN")
    print("=" * 70)

    building = create_office_annex_f()

    # ------------------------------------------------------------------
    # RISK
    # ------------------------------------------------------------------
    risk_results = RiskEngine.calculate_R(building)

    print("\n" + "=" * 70)
    print("RISK RESULTS (per zone)")
    print("=" * 70)
    R1_total = 0
    R2_total = 0
    for zone_name, vals in risk_results.items():
        print(f"\n--- {zone_name} ---")
        print(f"  RL1 (loss of life)     = {fmt(vals.get('RL1'))}")
        print(f"  RL2 (physical damage)  = {fmt(vals.get('RL2'))}")
        print(f"  R_total                = {fmt(vals.get('R_total'))}")
        print(f"  RT                     = {fmt(vals.get('RT'))}")
        print(f"  Status                 = {vals.get('risk_status', '-')}")
        # detailed components
        comps = ["RAT","RAD","RB1","RB2","RC1","RC2","RM1","RM2",
                 "RU","RV1","RV2","RW1","RW2","RZ1","RZ2"]
        comp_str = "  ".join(f"{c}={fmt(vals.get(c))}" for c in comps if vals.get(c) is not None)
        if comp_str:
            print(f"  components: {comp_str}")
        R1_total += vals.get("RL1", 0) or 0
        R2_total += vals.get("RL2", 0) or 0

    print("\n" + "-" * 70)
    print(f"TOTAL R1 (all zones) = {fmt(R1_total)}")
    print(f"TOTAL R2 (all zones) = {fmt(R2_total)}")
    print("-" * 70)

    # ------------------------------------------------------------------
    # FREQUENCY
    # ------------------------------------------------------------------
    frequency_results = FrequencyEngine.calculate_F(building)

    print("\n" + "=" * 70)
    print("FREQUENCY RESULTS (per zone)")
    print("=" * 70)
    for zone_name, vals in frequency_results.items():
        print(f"\n--- {zone_name} ---")
        for k in ["FC","FM","FWP","FWT","FZP","FZT","F_total","FT","frequency_status"]:
            print(f"  {k:18s} = {fmt(vals.get(k)) if k != 'frequency_status' else vals.get(k,'-')}")

    # ------------------------------------------------------------------
    # ANNEX E
    # ------------------------------------------------------------------
    annex_e_results = AnnexERiskEngine.calculate_RE(building)

    print("\n" + "=" * 70)
    print("ANNEX E RESULTS (per zone)")
    print("=" * 70)
    for zone_name, vals in annex_e_results.items():
        if vals.get("RE_total", 0):
            print(f"\n--- {zone_name} ---")
            for k in ["RE1","RE2","RE_total"]:
                print(f"  {k:10s} = {fmt(vals.get(k))}")

    print("\n" + "=" * 70)
    print("DONE — compare the values above against the Annex F reference.")
    print("=" * 70)


if __name__ == "__main__":
    main()
    