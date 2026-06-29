"""
Protection Recommendation Engine - Forward Simulation Version

For each dominant risk contributor, this engine:
1. Identifies which adjustable protection factor affects that component
2. Applies each candidate recommendation to a copied building model
3. Reruns the full risk and frequency engines
4. Returns the before/after R and F values for the frontend Apply & Re-run flow

The recommendation is simulation-based, so it uses the real N x P x L
calculation instead of a linear approximation.
"""

import copy
from engines.risk_engine import RiskEngine
from engines.frequency_engine import FrequencyEngine


# ---------------------------------------------------------------------------
# Protection level definitions - ordered weakest to strongest
# ---------------------------------------------------------------------------

SPD_LEVELS = [
    ("none",        1.0,    "No SPD"),
    ("III_IV",      0.05,   "SPD Class III/IV (PSPD = 0.05)"),
    ("II",          0.02,   "SPD Class II (PSPD = 0.02)"),
    ("I",           0.01,   "SPD Class I (PSPD = 0.01)"),
    ("better_2_5",  1e-4,   "Better than LPL I - 2.5 kA (PSPD = 1e-4)"),
    ("better_3_75", 5e-5,   "Better than LPL I - 3.75 kA (PSPD = 5e-5)"),
    ("better_5",    1e-5,   "Better than LPL I - 5 kA (PSPD = 1e-5)"),
]

PAM_LEVELS = [
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

BUILDING_LEVEL_FIELDS = {"LPS_class"}
LINE_LEVEL_FIELDS = {"equipotential_bonding_level"}


# ---------------------------------------------------------------------------
# Generic helpers
# ---------------------------------------------------------------------------

def _level_index(levels, key):
    return next((i for i, item in enumerate(levels) if item[0] == key), 0)


def _safe_number(value, default=0):
    return value if value is not None else default


def _fmt(value):
    return "n/a" if value is None else f"{value:.3e}"


def _zone_by_name(building, zone_name):
    return next((z for z in getattr(building, "zones", []) if z.name == zone_name), None)


def _service_available(building, zone, service):
    if not any(getattr(line, "service", None) == service for line in getattr(building, "lines", [])):
        return False
    if service == "power":
        return getattr(zone, "has_power_internal_system", True)
    if service == "telecom":
        return getattr(zone, "has_telecom_internal_system", True)
    return False


def _spd_fields_for_zone(building, zone):
    fields = []
    if _service_available(building, zone, "power"):
        fields.append(("power_spd_level", "Power", "power"))
    if _service_available(building, zone, "telecom"):
        fields.append(("telecom_spd_level", "Telecom", "telecom"))
    return fields


def _upgrade_lines_to_min_level(lines, target_level):
    target_idx = _level_index(PEB_LEVELS, target_level)
    for line in lines:
        current = getattr(line, "equipotential_bonding_level", "none") or "none"
        if _level_index(PEB_LEVELS, current) < target_idx:
            line.equipotential_bonding_level = target_level


def _apply_overrides(sim_building, zone_name, overrides):
    """Apply each simulated recommendation to the object that owns the field."""
    if not overrides:
        return

    zone = _zone_by_name(sim_building, zone_name)

    for field, value in overrides.items():
        if field in BUILDING_LEVEL_FIELDS:
            setattr(sim_building, field, value)
        elif field in LINE_LEVEL_FIELDS:
            if field == "equipotential_bonding_level":
                _upgrade_lines_to_min_level(sim_building.lines, value)
            else:
                for line in sim_building.lines:
                    setattr(line, field, value)
        elif zone is not None:
            setattr(zone, field, value)


def _simulate_totals(building, zone_name, overrides=None):
    """Apply overrides on a copy, then rerun the complete R and F engines."""
    sim_building = copy.deepcopy(building)
    _apply_overrides(sim_building, zone_name, overrides or {})

    risk_results = RiskEngine.calculate_R(sim_building)
    frequency_results = FrequencyEngine.calculate_F(sim_building)

    risk_zone = risk_results.get(zone_name, {})
    frequency_zone = frequency_results.get(zone_name, {})

    return {
        "building": sim_building,
        "risk_results": risk_results,
        "frequency_results": frequency_results,
        "risk_zone": risk_zone,
        "frequency_zone": frequency_zone,
        "r_total": risk_zone.get("R_total"),
        "rt": risk_zone.get("RT"),
        "f_total": frequency_zone.get("F_total"),
        "ft": frequency_zone.get("FT"),
    }


def _candidate_action(
    building,
    zone_name,
    display,
    field,
    value,
    system,
    overrides,
    current_r,
    current_f,
    rt,
    ft,
    target="risk",
    building_level=False,
):
    sim = _simulate_totals(building, zone_name, overrides)
    new_r = sim["r_total"]
    new_f = sim["f_total"]

    reduces_risk = new_r is not None and current_r is not None and new_r < current_r
    reduces_frequency = new_f is not None and current_f is not None and new_f < current_f
    risk_sufficient = new_r is not None and new_r <= rt
    frequency_sufficient = new_f is not None and new_f <= ft

    if target == "frequency":
        is_sufficient = frequency_sufficient
        is_minimum_needed = frequency_sufficient and reduces_frequency
    else:
        is_sufficient = risk_sufficient
        is_minimum_needed = risk_sufficient and reduces_risk

    action = {
        "type": "apply_protection",
        "display": display,
        "field": field,
        "value": value,
        "system": system,
        "overrides": overrides,
        "old_r": current_r,
        "new_r": new_r,
        "old_f": current_f,
        "new_f": new_f,
        "estimated_r": new_r,
        "estimated_f": new_f,
        "reduces_risk": reduces_risk,
        "reduces_frequency": reduces_frequency,
        "risk_sufficient": risk_sufficient,
        "frequency_sufficient": frequency_sufficient,
        "is_sufficient": is_sufficient,
        "is_minimum_needed": is_minimum_needed,
        "note": f"Estimated R after: {_fmt(new_r)}; estimated F after: {_fmt(new_f)}",
    }

    if building_level:
        action["building_level"] = True

    return action


def _choose_action(candidates, target="risk"):
    if not candidates:
        return None

    if target == "frequency":
        for action in candidates:
            if action.get("reduces_frequency") and action.get("frequency_sufficient"):
                return action
        reducing = [a for a in candidates if a.get("reduces_frequency")]
        if reducing:
            return min(reducing, key=lambda a: _safe_number(a.get("new_f"), float("inf")))
        return None

    for action in candidates:
        if action.get("reduces_risk") and action.get("risk_sufficient"):
            return action
    reducing = [a for a in candidates if a.get("reduces_risk")]
    if reducing:
        return min(reducing, key=lambda a: _safe_number(a.get("new_r"), float("inf")))
    return None


# Backward-compatible helpers retained for callers/tests that may import them.
def _simulate_r_total(building, zone_name, zone_overrides):
    return _simulate_totals(building, zone_name, zone_overrides).get("r_total")


def _simulate_f_total(building, zone_name, zone_overrides):
    return _simulate_totals(building, zone_name, zone_overrides).get("f_total")


# ---------------------------------------------------------------------------
# Driver detection
# ---------------------------------------------------------------------------

def _detect_driver(component, zone):
    if component == "RAT":
        return "Pam"
    if component == "RAD":
        return "PLPS" if not getattr(zone, "lps_protected", False) else "Pam"
    if component == "RB":
        return "PLPS"
    if component in ["RC", "RM", "RW", "RZ"]:
        return "PSPD"
    if component == "RU":
        touch = getattr(zone, "touch_protection", []) or []
        return "Pam" if not touch or touch == ["none"] else "PEB"
    if component == "RV":
        return "PEB"
    return None


# ---------------------------------------------------------------------------
# Action builders - all actions rerun full R and F
# ---------------------------------------------------------------------------

def _build_spd_actions(building, zone, zone_name, current_r, current_f, rt, ft, target="risk"):
    actions = []

    for field, system_label, system in _spd_fields_for_zone(building, zone):
        current = getattr(zone, field, "none") or "none"
        current_idx = _level_index(SPD_LEVELS, current)
        candidates = []

        for i, (key, _val, label) in enumerate(SPD_LEVELS):
            if i <= current_idx:
                continue
            candidates.append(_candidate_action(
                building=building,
                zone_name=zone_name,
                display=f"Upgrade {system_label} SPD -> {label}",
                field=field,
                value=key,
                system=system,
                overrides={field: key},
                current_r=current_r,
                current_f=current_f,
                rt=rt,
                ft=ft,
                target=target,
            ))

        action = _choose_action(candidates, target=target)
        if action is not None:
            actions.append(action)

    return actions


def _build_cumulative_zone_action(
    building,
    zone,
    zone_name,
    current_r,
    current_f,
    rt,
    ft,
    field,
    levels,
    system,
    target="risk",
):
    current = [v for v in (getattr(zone, field, []) or []) if v != "none"]
    cumulative = list(current)
    candidates = []

    for key, label in levels:
        if key in cumulative:
            continue
        cumulative = cumulative + [key]
        candidates.append(_candidate_action(
            building=building,
            zone_name=zone_name,
            display=label,
            field=field,
            value=list(cumulative),
            system=system,
            overrides={field: list(cumulative)},
            current_r=current_r,
            current_f=current_f,
            rt=rt,
            ft=ft,
            target=target,
        ))

    action = _choose_action(candidates, target=target)
    return [action] if action is not None else []


def _build_plps_actions(building, zone_name, current_r, current_f, rt, ft, target="risk"):
    current = getattr(building, "LPS_class", None)
    current_idx = _level_index(PLPS_LEVELS, current)
    candidates = []

    for i, (key, label) in enumerate(PLPS_LEVELS):
        if i <= current_idx:
            continue
        candidates.append(_candidate_action(
            building=building,
            zone_name=zone_name,
            display=label,
            field="LPS_class",
            value=key,
            system="lps",
            overrides={"LPS_class": key},
            current_r=current_r,
            current_f=current_f,
            rt=rt,
            ft=ft,
            target=target,
            building_level=True,
        ))

    action = _choose_action(candidates, target=target)
    return [action] if action is not None else []


def _build_peb_actions(building, zone_name, current_r, current_f, rt, ft, target="risk"):
    line_levels = [
        getattr(line, "equipotential_bonding_level", "none") or "none"
        for line in getattr(building, "lines", [])
    ]
    current_idx = min((_level_index(PEB_LEVELS, value) for value in line_levels), default=0)
    candidates = []

    for i, (key, label) in enumerate(PEB_LEVELS):
        if i <= current_idx:
            continue
        candidates.append(_candidate_action(
            building=building,
            zone_name=zone_name,
            display=label,
            field="equipotential_bonding_level",
            value=key,
            system="peb",
            overrides={"equipotential_bonding_level": key},
            current_r=current_r,
            current_f=current_f,
            rt=rt,
            ft=ft,
            target=target,
        ))

    action = _choose_action(candidates, target=target)
    return [action] if action is not None else []


def _build_actions(driver, building, zone, zone_name, rt, ft, current_r, current_f, target="risk"):
    if driver == "PSPD":
        return _build_spd_actions(building, zone, zone_name, current_r, current_f, rt, ft, target)
    if driver == "Pam":
        return _build_cumulative_zone_action(
            building, zone, zone_name, current_r, current_f, rt, ft,
            "touch_protection", PAM_LEVELS, "touch", target
        )
    if driver == "PLPS":
        return _build_plps_actions(building, zone_name, current_r, current_f, rt, ft, target)
    if driver == "rP":
        return _build_cumulative_zone_action(
            building, zone, zone_name, current_r, current_f, rt, ft,
            "fire_protection", RP_MEASURES, "fire", target
        )
    if driver == "PEB":
        return _build_peb_actions(building, zone_name, current_r, current_f, rt, ft, target)
    return []


def _severity(percent):
    if percent >= 30:
        return "Critical"
    if percent >= 10:
        return "Significant"
    if percent >= 5:
        return "Moderate"
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
        rt = values.get("RT", getattr(zone, "RT", 1e-5)) or 1e-5
        current_r = values.get("R_total", 0) or 0
        zone_output = []

        if current_r <= rt:
            return zone_output

        current = _simulate_totals(building, zone_name, {})
        current_f = current.get("f_total")
        ft = current.get("ft") or getattr(zone, "FT", 5e-2) or 5e-2

        contributors = ProtectionRecommendationEngine.get_top_risk_contributors(values)

        for item in contributors:
            component = item["component"]
            driver = _detect_driver(component, zone)
            actions = _build_actions(
                driver=driver,
                building=building,
                zone=zone,
                zone_name=zone_name,
                rt=rt,
                ft=ft,
                current_r=current_r,
                current_f=current_f,
                target="risk",
            )

            sufficient_exists = any(a.get("risk_sufficient") for a in actions)
            reduction_exists = any(a.get("reduces_risk") for a in actions)

            summary = (
                f"{component} contributes {item['percent']:.1f}% of total risk "
                f"(value: {item['value']:.3e}). "
                f"Main adjustable factor: {driver}. "
                + ("Recommended action lowers risk to the tolerable limit."
                   if sufficient_exists
                   else "Recommended action lowers risk but more protection may be needed."
                   if reduction_exists
                   else "No single available action lowered this component in simulation.")
            )

            zone_output.append({
                "component": component,
                "value": item["value"],
                "percent": item["percent"],
                "severity": item["severity"],
                "probability_driver": driver,
                "old_r": current_r,
                "old_f": current_f,
                "rt": rt,
                "ft": ft,
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
        ft = values.get("FT", getattr(zone, "FT", 5e-2)) or 5e-2
        current_f = values.get("F_total", 0) or 0
        zone_output = []

        if not contributors or current_f <= ft:
            return zone_output

        current = _simulate_totals(building, zone_name, {})
        current_r = current.get("r_total")
        rt = current.get("rt") or getattr(zone, "RT", 1e-5) or 1e-5

        top = contributors[0]
        dominant_list = ", ".join(c["component"] for c in contributors)
        actions = _build_spd_actions(
            building=building,
            zone=zone,
            zone_name=zone_name,
            current_r=current_r,
            current_f=current_f,
            rt=rt,
            ft=ft,
            target="frequency",
        )

        sufficient_exists = any(a.get("frequency_sufficient") for a in actions)

        zone_output.append({
            "component": top["component"],
            "value": top["value"],
            "percent": top["percent"],
            "severity": top["severity"],
            "probability_driver": "PSPD",
            "old_r": current_r,
            "old_f": current_f,
            "rt": rt,
            "ft": ft,
            "summary": (
                f"Frequency exceeds the tolerable limit. Main contributors: {dominant_list}. "
                f"The recommendation applies SPD, reruns risk and frequency, and reports both new values."
            ),
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
