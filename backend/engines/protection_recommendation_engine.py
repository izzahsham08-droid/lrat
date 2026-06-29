"""
Protection Recommendation Engine — Forward Simulation Version

For each dominant risk contributor, this engine:
1. Identifies which adjustable P factors affect that component
2. Simulates each candidate protection level through the FULL risk engine
3. Finds the MINIMUM protection level that actually brings R_total <= RT
4. Returns structured action objects for the frontend Apply & Re-run feature

This is accurate because it uses the real N×P×L calculation,
not a linear approximation.
"""

import copy
from engines.risk_engine import RiskEngine
from engines.frequency_engine import FrequencyEngine


# ---------------------------------------------------------------------------
# Protection level definitions — ordered weakest → strongest
# ---------------------------------------------------------------------------

SPD_LEVELS = [
    ("none",        1.0,    "No SPD"),
    ("III_IV",      0.05,   "SPD Class III/IV (PSPD = 0.05)"),
    ("II",          0.02,   "SPD Class II (PSPD = 0.02)"),
    ("I",           0.01,   "SPD Class I (PSPD = 0.01)"),
    ("better_2_5",  1e-4,   "Better than LPL I — 2.5 kA (PSPD = 1×10⁻⁴)"),
    ("better_3_75", 5e-5,   "Better than LPL I — 3.75 kA (PSPD = 5×10⁻⁵)"),
    ("better_5",    1e-5,   "Better than LPL I — 5 kA (PSPD = 1×10⁻⁵)"),
]

PAM_LEVELS = [
    # Each entry: (key_to_add_to_touch_protection_list, display_label)
    ("warning_notice",            "Add warning notices on exposed parts"),
    ("electrical_insulation",     "Install electrical insulation on exposed parts"),
    ("soil_equipotentialization", "Apply soil equipotentialization"),
    ("access_restriction",        "Restrict physical access to exposed areas"),
]

PLPS_LEVELS = [
    (None,           "No LPS"),
    ("IV",           "Install LPS Class IV"),
    ("III",          "Install LPS Class III"),
    ("II",           "Install LPS Class II"),
    ("I",            "Install LPS Class I"),
    ("I_natural",    "LPS Class I with natural LPS"),
    ("I_metal_roof", "LPS Class I with metal roof"),
]

RP_MEASURES = [
    ("automatic_extinguishing", "Install automatic fire extinguishing system"),
    ("automatic_alarm",         "Install automatic fire alarm"),
    ("extinguishers",           "Provide portable fire extinguishers"),
    ("hydrants",                "Install fire hydrants"),
    ("manual_alarm",            "Install manual fire alarm"),
    ("fire_compartments",       "Create fire compartments"),
    ("escape_route",            "Provide adequate escape routes"),
]

PEB_LEVELS = [
    ("none",   "No equipotential bonding SPD"),
    ("III-IV", "Install equipotential bonding SPD Class III/IV"),
    ("II",     "Install equipotential bonding SPD Class II"),
    ("I",      "Install equipotential bonding SPD Class I"),
]


# ---------------------------------------------------------------------------
# Helper: simulate R_total for a modified zone
# ---------------------------------------------------------------------------

# Fields that belong to the LINE object, not the zone.
LINE_LEVEL_FIELDS = {"equipotential_bonding_level"}


def _apply_overrides(sim_building, zone_name, overrides):
    """Apply overrides to the correct object: line-level fields go to all
    lines, zone-level fields go to the named zone."""
    line_overrides = {k: v for k, v in overrides.items() if k in LINE_LEVEL_FIELDS}
    zone_overrides = {k: v for k, v in overrides.items() if k not in LINE_LEVEL_FIELDS}

    if line_overrides:
        for line in sim_building.lines:
            for field, value in line_overrides.items():
                setattr(line, field, value)

    if zone_overrides:
        for z in sim_building.zones:
            if z.name == zone_name:
                for field, value in zone_overrides.items():
                    setattr(z, field, value)
                break


def _simulate_r_total(building, zone_name, zone_overrides):
    """
    Run the full risk engine with a modified zone or line.
    Returns R_total for that zone, or None if zone not found.
    """
    sim_building = copy.deepcopy(building)
    _apply_overrides(sim_building, zone_name, zone_overrides)
    results = RiskEngine.calculate_R(sim_building)
    zone_result = results.get(zone_name)
    if zone_result is None:
        return None
    return zone_result.get("R_total", 0)


def _simulate_f_total(building, zone_name, zone_overrides):
    """Same but for frequency."""
    sim_building = copy.deepcopy(building)
    _apply_overrides(sim_building, zone_name, zone_overrides)
    results = FrequencyEngine.calculate_F(sim_building)
    zone_result = results.get(zone_name)
    if zone_result is None:
        return None
    return zone_result.get("F_total", 0)


# ---------------------------------------------------------------------------
# Simulation-based minimum finder
# ---------------------------------------------------------------------------

def _find_min_spd(building, zone, zone_name, rt, field):
    """
    Try each SPD level for the given field (power_spd_level or telecom_spd_level).
    Return (key, label, simulated_r_total) for the minimum level that achieves RT.
    """
    current = getattr(zone, field, "none") or "none"
    current_idx = next((i for i, (k,v,l) in enumerate(SPD_LEVELS) if k == current), 0)

    for i, (key, val, label) in enumerate(SPD_LEVELS):
        if i <= current_idx:
            continue  # don't suggest current or weaker levels
        sim_r = _simulate_r_total(building, zone_name, {field: key})
        if sim_r is not None and sim_r <= rt:
            return key, label, sim_r

    return None, None, None  # no single SPD upgrade is sufficient


def _find_min_pam(building, zone, zone_name, rt):
    """Try adding each Pam measure one by one (cumulative)."""
    current = list(getattr(zone, "touch_protection", []) or [])
    cumulative = list(current)

    for key, label in PAM_LEVELS:
        if key in cumulative:
            continue
        cumulative = cumulative + [key]
        sim_r = _simulate_r_total(building, zone_name, {"touch_protection": cumulative})
        if sim_r is not None and sim_r <= rt:
            return cumulative, label, sim_r

    return None, None, None


def _find_min_plps(building, zone, zone_name, rt, building_inputs):
    """Try upgrading LPS class one step at a time."""
    current = getattr(building_inputs, "LPS_class", None)
    current_idx = next((i for i, (k, l) in enumerate(PLPS_LEVELS) if k == current), 0)

    for i, (key, label) in enumerate(PLPS_LEVELS):
        if i <= current_idx:
            continue
        # LPS is a building-level field — we override on building
        sim_building = copy.deepcopy(building_inputs)
        sim_building.LPS_class = key
        results = RiskEngine.calculate_R(sim_building)
        zone_result = results.get(zone_name)
        if zone_result and zone_result.get("R_total", 0) <= rt:
            return key, label, zone_result.get("R_total", 0)

    return None, None, None


def _find_min_rp(building, zone, zone_name, rt):
    """Try adding each fire protection measure cumulatively."""
    current = list(getattr(zone, "fire_protection", []) or [])
    cumulative = list(current)

    for key, label in RP_MEASURES:
        if key in cumulative:
            continue
        cumulative = cumulative + [key]
        sim_r = _simulate_r_total(building, zone_name, {"fire_protection": cumulative})
        if sim_r is not None and sim_r <= rt:
            return cumulative, label, sim_r

    return None, None, None


def _find_min_peb(building, zone, zone_name, rt):
    """Try upgrading PEB level. PEB is a line-level parameter, so the current
    level is taken from the connected lines (the lowest existing level)."""
    line_levels = [getattr(l, "equipotential_bonding_level", "none") or "none"
                   for l in getattr(building, "lines", [])]
    # Use the weakest existing level as the starting point
    idx_of = lambda v: next((i for i, (k, l) in enumerate(PEB_LEVELS) if k == v), 0)
    current_idx = min((idx_of(v) for v in line_levels), default=0)

    for i, (key, label) in enumerate(PEB_LEVELS):
        if i <= current_idx:
            continue
        sim_r = _simulate_r_total(building, zone_name, {"equipotential_bonding_level": key})
        if sim_r is not None and sim_r <= rt:
            return key, label, sim_r

    return None, None, None


# ---------------------------------------------------------------------------
# Driver detection — same logic as original, kept faithful
# ---------------------------------------------------------------------------

def _detect_driver(component, zone):
    if component == "RAT":
        return "Pam"
    if component == "RAD":
        return "PLPS" if not getattr(zone, "lps_protected", False) else "Pam"
    if component == "RB":
        # Lightning protection only: recommend the LPS. Fire protection (rP)
        # is a consequence-mitigation measure and is intentionally not
        # recommended by this lightning protection tool.
        return "PLPS"
    if component in ["RC", "RM", "RW", "RZ"]:
        return "PSPD"
    if component == "RU":
        touch = getattr(zone, "touch_protection", []) or []
        return "Pam" if not touch or touch == ["none"] else "PEB"
    if component == "RV":
        # Lightning protection only: recommend equipotential bonding (PEB).
        # Fire protection (rP) is intentionally not recommended.
        return "PEB"
    return None
    return None


# ---------------------------------------------------------------------------
# Action builder — uses forward simulation
# ---------------------------------------------------------------------------

def _build_actions(driver, building, zone, zone_name, rt, building_inputs):
    """
    Return list of structured action objects with simulated estimated risk.
    Each action is confirmed to be sufficient (or marked if not).
    """
    actions = []

    if driver == "PSPD":
        for field, system_label in [
            ("power_spd_level", "Power"),
            ("telecom_spd_level", "Telecom"),
        ]:
            current = getattr(zone, field, "none") or "none"
            current_idx = next((i for i, (k,v,l) in enumerate(SPD_LEVELS) if k == current), 0)

            # Find minimum sufficient level
            min_key, min_label, min_r = _find_min_spd(building, zone, zone_name, rt, field)

            if min_key is not None:
                # Recommend the minimum level that actually brings risk within
                # the tolerable limit — no need to make the user step through
                # levels that are insufficient.
                actions.append({
                    "type": "apply_protection",
                    "display": f"Upgrade {system_label} SPD → {min_label}",
                    "field": field,
                    "value": min_key,
                    "system": system_label.lower(),
                    "estimated_r": min_r,
                    "is_sufficient": True,
                    "is_minimum_needed": True,
                    "note": f"Estimated risk after: {min_r:.3e}",
                })
            else:
                # No single SPD level is sufficient on its own — show the
                # strongest available level so the user sees the best option.
                last_key, last_val, last_label = SPD_LEVELS[-1]
                sim_r = _simulate_r_total(building, zone_name, {field: last_key})
                actions.append({
                    "type": "apply_protection",
                    "display": f"Upgrade {system_label} SPD → {last_label}",
                    "field": field,
                    "value": last_key,
                    "system": system_label.lower(),
                    "estimated_r": sim_r,
                    "is_sufficient": (sim_r is not None and sim_r <= rt),
                    "is_minimum_needed": False,
                    "note": "Strongest level; may need combining with other measures",
                })

    elif driver == "Pam":
        current = list(getattr(zone, "touch_protection", []) or [])
        for key, label in PAM_LEVELS:
            if key in current:
                continue
            new_val = current + [key]
            sim_r = _simulate_r_total(building, zone_name, {"touch_protection": new_val})
            is_sufficient = (sim_r is not None and sim_r <= rt)
            actions.append({
                "type": "apply_protection",
                "display": label,
                "field": "touch_protection",
                "value": new_val,
                "system": "touch",
                "estimated_r": sim_r,
                "is_sufficient": is_sufficient,
                "is_minimum_needed": is_sufficient,
                "note": f"Estimated risk after: {sim_r:.3e}" if sim_r else "Insufficient alone",
            })
            break  # suggest first not-yet-applied measure

    elif driver == "PLPS":
        current = getattr(building_inputs, "LPS_class", None)
        current_idx = next((i for i, (k, l) in enumerate(PLPS_LEVELS) if k == current), 0)
        for i, (key, label) in enumerate(PLPS_LEVELS):
            if i <= current_idx:
                continue
            sim_building = copy.deepcopy(building_inputs)
            sim_building.LPS_class = key
            results = RiskEngine.calculate_R(sim_building)
            zone_result = results.get(zone_name, {})
            sim_r = zone_result.get("R_total", 0)
            is_sufficient = sim_r <= rt
            actions.append({
                "type": "apply_protection",
                "display": label,
                "field": "LPS_class",
                "value": key,
                "system": "lps",
                "estimated_r": sim_r,
                "is_sufficient": is_sufficient,
                "is_minimum_needed": is_sufficient,
                "note": f"Estimated risk after: {sim_r:.3e}",
                "building_level": True,  # flag: this change is on building, not zone
            })
            break

    elif driver == "rP":
        current = list(getattr(zone, "fire_protection", []) or [])
        for key, label in RP_MEASURES:
            if key in current:
                continue
            new_val = current + [key]
            sim_r = _simulate_r_total(building, zone_name, {"fire_protection": new_val})
            is_sufficient = (sim_r is not None and sim_r <= rt)
            actions.append({
                "type": "apply_protection",
                "display": label,
                "field": "fire_protection",
                "value": new_val,
                "system": "fire",
                "estimated_r": sim_r,
                "is_sufficient": is_sufficient,
                "is_minimum_needed": is_sufficient,
                "note": f"Estimated risk after: {sim_r:.3e}" if sim_r else "Insufficient alone",
            })
            break

    elif driver == "PEB":
        line_levels = [getattr(l, "equipotential_bonding_level", "none") or "none"
                       for l in getattr(building_inputs, "lines", [])]
        idx_of = lambda v: next((i for i, (k, l) in enumerate(PEB_LEVELS) if k == v), 0)
        current_idx = min((idx_of(v) for v in line_levels), default=0)
        for i, (key, label) in enumerate(PEB_LEVELS):
            if i <= current_idx:
                continue
            sim_r = _simulate_r_total(building, zone_name, {"equipotential_bonding_level": key})
            is_sufficient = (sim_r is not None and sim_r <= rt)
            actions.append({
                "type": "apply_protection",
                "display": label,
                "field": "equipotential_bonding_level",
                "value": key,
                "system": "peb",
                "estimated_r": sim_r,
                "is_sufficient": is_sufficient,
                "is_minimum_needed": is_sufficient,
                "note": f"Estimated risk after: {sim_r:.3e}" if sim_r else "Insufficient alone",
            })
            break

    return actions

def _severity(percent):
    if percent >= 30:   return "Critical"
    if percent >= 10:   return "Significant"
    if percent >= 5:    return "Moderate"
    return "Minor"


# ---------------------------------------------------------------------------
# Grouped components
# ---------------------------------------------------------------------------

def _grouped_risk(values):
    return {
        "RAT": values.get("RAT", 0) or 0,
        "RAD": values.get("RAD", 0) or 0,
        "RB":  (values.get("RB1", 0) or 0) + (values.get("RB2", 0) or 0),
        "RC":  (values.get("RC1", 0) or 0) + (values.get("RC2", 0) or 0),
        "RM":  (values.get("RM1", 0) or 0) + (values.get("RM2", 0) or 0),
        "RU":  values.get("RU", 0) or 0,
        "RV":  (values.get("RV1", 0) or 0) + (values.get("RV2", 0) or 0),
        "RW":  (values.get("RW1", 0) or 0) + (values.get("RW2", 0) or 0),
        "RZ":  (values.get("RZ1", 0) or 0) + (values.get("RZ2", 0) or 0),
    }


def _grouped_frequency(values):
    return {
        "FC":  values.get("FC", 0) or 0,
        "FM":  values.get("FM", 0) or 0,
        "FWP": values.get("FWP", 0) or 0,
        "FWT": values.get("FWT", 0) or 0,
        "FZP": values.get("FZP", 0) or 0,
        "FZT": values.get("FZT", 0) or 0,
    }


def _top_contributors(grouped, total, min_percent=5, top_n=3):
    if total <= 0:
        return []
    items = []
    for component, value in grouped.items():
        percent = (value / total) * 100
        if percent >= min_percent:
            items.append({
                "component": component,
                "value": value,
                "percent": percent,
                "severity": _severity(percent),
            })
    return sorted(items, key=lambda x: x["percent"], reverse=True)[:top_n]


# ---------------------------------------------------------------------------
# Main engine class
# ---------------------------------------------------------------------------

class ProtectionRecommendationEngine:

    @staticmethod
    def grouped_risk_components(values):
        return _grouped_risk(values)

    @staticmethod
    def severity(percent):
        return _severity(percent)

    @staticmethod
    def get_top_risk_contributors(values, min_percent=5, top_n=3):
        grouped = _grouped_risk(values)
        total = values.get("R_total", 0) or 0
        return _top_contributors(grouped, total, min_percent, top_n)

    @staticmethod
    def generate_for_zone(zone_name, values, zone, building):
        contributors = ProtectionRecommendationEngine.get_top_risk_contributors(values)
        rt = values.get("RT", 1e-5) or 1e-5
        zone_output = []

        for item in contributors:
            component = item["component"]
            driver = _detect_driver(component, zone)

            actions = _build_actions(driver, building, zone, zone_name, rt, building)

            sufficient_exists = any(a.get("is_sufficient") for a in actions)

            summary = (
                f"{component} contributes {item['percent']:.1f}% of total risk "
                f"(value: {item['value']:.3e}). "
                f"Main adjustable factor: {driver}. "
                + ("A single protection upgrade can bring risk within limit."
                   if sufficient_exists
                   else "Combined protection measures may be needed.")
            )

            zone_output.append({
                "component": component,
                "value": item["value"],
                "percent": item["percent"],
                "severity": item["severity"],
                "probability_driver": driver,
                "summary": summary,
                "actions": actions,
            })

        return zone_output

    @staticmethod
    def generate(building, risk_results):
        output = {}
        zones_by_name = {zone.name: zone for zone in building.zones}

        for zone_name, values in risk_results.items():
            if zone_name == "Building_Total":
                continue
            zone = zones_by_name.get(zone_name)
            if zone is None:
                continue
            output[zone_name] = ProtectionRecommendationEngine.generate_for_zone(
                zone_name, values, zone, building
            )
        return output

    # ------------------------------------------------------------------ #
    # FREQUENCY
    # ------------------------------------------------------------------ #

    @staticmethod
    def get_top_frequency_contributors(values, min_percent=5, top_n=3):
        grouped = _grouped_frequency(values)
        total = values.get("F_total", 0) or 0
        return _top_contributors(grouped, total, min_percent, top_n)

    @staticmethod
    def generate_frequency_for_zone(zone_name, values, zone, building):
        contributors = ProtectionRecommendationEngine.get_top_frequency_contributors(values)
        ft = values.get("FT", 5e-2) or 5e-2
        f_total = values.get("F_total", 0) or 0
        zone_output = []

        if not contributors or f_total <= ft:
            return zone_output

        # All frequency components are driven by the same SPD protection, so a
        # single consolidated recommendation is produced rather than repeating
        # the same SPD action for every component (FC, FM, FW, FZ).
        # The dominant contributor is reported for context.
        top = contributors[0]
        dominant_list = ", ".join(c["component"] for c in contributors)

        actions = []
        for field, system_label in [
            ("power_spd_level", "Power"),
            ("telecom_spd_level", "Telecom"),
        ]:
            # Find the minimum SPD level that brings F_total within the limit
            current = getattr(zone, field, "none") or "none"
            current_idx = next((i for i, (k,v,l) in enumerate(SPD_LEVELS) if k == current), 0)
            min_action = None
            for i, (key, val, label) in enumerate(SPD_LEVELS):
                if i <= current_idx:
                    continue
                sim_f = _simulate_f_total(building, zone_name, {field: key})
                if sim_f is not None and sim_f <= ft:
                    min_action = {
                        "type": "apply_protection",
                        "display": f"Upgrade {system_label} SPD → {label}",
                        "field": field,
                        "value": key,
                        "system": system_label.lower(),
                        "estimated_r": sim_f,
                        "is_sufficient": True,
                        "is_minimum_needed": True,
                        "note": f"Estimated frequency after: {sim_f:.3e}",
                    }
                    break
            if min_action:
                actions.append(min_action)
            else:
                # No single level sufficient — show strongest available
                last_key, last_val, last_label = SPD_LEVELS[-1]
                sim_f = _simulate_f_total(building, zone_name, {field: last_key})
                actions.append({
                    "type": "apply_protection",
                    "display": f"Upgrade {system_label} SPD → {last_label}",
                    "field": field,
                    "value": last_key,
                    "system": system_label.lower(),
                    "estimated_r": sim_f,
                    "is_sufficient": (sim_f is not None and sim_f <= ft),
                    "is_minimum_needed": False,
                    "note": "Strongest level available",
                })

        sufficient_exists = any(a.get("is_sufficient") for a in actions)
        zone_output.append({
            "component": top["component"],
            "value": top["value"],
            "percent": top["percent"],
            "severity": top["severity"],
            "probability_driver": "PSPD",
            "summary": f"Frequency exceeds the tolerable limit. Main contributors: {dominant_list}. "
                       f"All are reduced by upgrading surge protection (SPD).",
            "actions": actions,
            "sufficient_exists": sufficient_exists,
        })
        return zone_output

    @staticmethod
    def generate_frequency(building, frequency_results):
        output = {}
        zones_by_name = {zone.name: zone for zone in building.zones}
        for zone_name, values in frequency_results.items():
            if zone_name == "Building_Total":
                continue
            zone = zones_by_name.get(zone_name)
            if zone is None:
                continue
            output[zone_name] = ProtectionRecommendationEngine.generate_frequency_for_zone(
                zone_name, values, zone, building
            )
        return output
