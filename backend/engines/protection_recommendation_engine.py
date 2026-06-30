"""
Protection Recommendation Engine - Planner V1

This version treats recommendation as a planning problem:
1. Analyse the current dominant risk contributors.
2. Generate candidate protection measures from the editable protection fields.
3. Simulate each candidate with the full RiskEngine and FrequencyEngine.
4. Apply the best improving candidate to a copied building.
5. Repeat until R_total <= RT or no further improvement is possible.

The calculation engines and mapping tables remain the source of truth.
"""

import copy
from engines.risk_engine import RiskEngine
from engines.frequency_engine import FrequencyEngine


# ---------------------------------------------------------------------------
# Protection definitions
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
    ("warning_notice",            "Add warning notices on exposed parts", 1),
    ("electrical_insulation",     "Install electrical insulation on exposed parts", 2),
    ("soil_equipotentialization", "Apply soil equipotentialization", 2),
    ("access_restriction",        "Restrict physical access to exposed areas", 3),
]

PLPS_LEVELS = [
    (None, "No LPS", 0),
    ("IV", "Install LPS Class IV", 3),
    ("III", "Install LPS Class III", 4),
    ("II", "Install LPS Class II", 5),
    ("I", "Install LPS Class I", 6),
]

PEB_LEVELS = [
    ("none",   "No equipotential bonding SPD", 0),
    ("III-IV", "Install equipotential bonding SPD Class III/IV", 2),
    ("II",     "Install equipotential bonding SPD Class II", 3),
    ("I",      "Install equipotential bonding SPD Class I", 4),
]

BETTER_THAN_SPD_KEYS = {"better_2_5", "better_3_75", "better_5"}
# Per IEC 62305-2 Annex B table guidance used by this project, do not
# auto-recommend better-than-LPL-I SPD for S1/RC. Keep those cases at LPL I
# unless the user enters a custom Annex-D/design value.
SOURCES_ALLOWING_BETTER_THAN_SPD = {"S2", "S4"}

RISK_COMPONENT_SOURCES = {
    "RC": "S1",
    "RM": "S2",
    "RW": "S3",
    "RZ": "S4",
}

FREQUENCY_COMPONENT_SOURCES = {
    "FC": "S1",
    "FM": "S2",
    "FWP": "S3",
    "FWT": "S3",
    "FZP": "S4",
    "FZT": "S4",
}

BUILDING_LEVEL_FIELDS = {"LPS_class"}
LINE_LEVEL_FIELDS = {"equipotential_bonding_level"}
LIST_ZONE_FIELDS = {"touch_protection", "fire_protection"}

MAX_PLAN_STEPS = 6
MIN_IMPROVEMENT = 1e-15

PROTECTION_FACTORS = {
    "PSPD": {
        "label": "Coordinated SPD",
        "controls": ["RC", "RM", "RW", "RZ"],
        "priority": 1,
        "reason": (
            "RC, RM, RW and RZ are controlled through probability terms that depend "
            "on PSPD. Coordinated SPD is therefore evaluated as one protection group."
        ),
    },
    "PLPS": {
        "label": "Lightning protection system",
        "controls": ["RAT", "RAD", "RB"],
        "priority": 2,
        "reason": (
            "RAT, RAD and RB are influenced by direct-flash protection. LPS levels "
            "are evaluated as a protection group instead of treating each component alone."
        ),
    },
    "Pam": {
        "label": "Touch/contact protection",
        "controls": ["RAT", "RAD", "RU"],
        "priority": 3,
        "reason": (
            "RAT, RAD and RU can be reduced by measures that lower Pam, such as warning "
            "notices, insulation, equipotentialization, or access restriction."
        ),
    },
    "PEB": {
        "label": "Equipotential bonding",
        "controls": ["RU", "RV", "RW"],
        "priority": 4,
        "reason": (
            "RU, RV and RW can be reduced by service-line equipotential bonding. Bonding "
            "is evaluated as a shared protection group."
        ),
    },
    "rP": {
        "label": "Fire protection",
        "controls": ["RB", "RV"],
        "priority": 5,
        "reason": "RB and RV can also be influenced by fire protection measures through rP.",
    },
}

RP_MEASURES = [
    ("automatic_extinguishing", "Install automatic fire extinguishing system", 3),
    ("automatic_alarm", "Install automatic fire alarm", 2),
    ("extinguishers", "Provide portable fire extinguishers", 1),
    ("hydrants", "Install fire hydrants", 2),
    ("manual_alarm", "Install manual fire alarm", 1),
    ("fire_compartments", "Create fire compartments", 3),
    ("escape_route", "Provide adequate escape routes", 1),
]


# ---------------------------------------------------------------------------
# Basic utilities
# ---------------------------------------------------------------------------

def _level_index(levels, key):
    return next((i for i, item in enumerate(levels) if item[0] == key), 0)


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


def _spd_levels_for_source(source):
    if source in SOURCES_ALLOWING_BETTER_THAN_SPD:
        return SPD_LEVELS
    return [item for item in SPD_LEVELS if item[0] not in BETTER_THAN_SPD_KEYS]


def _upgrade_lines_to_min_level(lines, target_level):
    target_idx = _level_index(PEB_LEVELS, target_level)
    for line in lines:
        current = getattr(line, "equipotential_bonding_level", "none") or "none"
        if _level_index(PEB_LEVELS, current) < target_idx:
            line.equipotential_bonding_level = target_level


def _apply_overrides(building, zone_name, overrides):
    zone = _zone_by_name(building, zone_name)
    for field, value in (overrides or {}).items():
        if field in BUILDING_LEVEL_FIELDS:
            setattr(building, field, value)
        elif field in LINE_LEVEL_FIELDS:
            if field == "equipotential_bonding_level":
                _upgrade_lines_to_min_level(building.lines, value)
            else:
                for line in building.lines:
                    setattr(line, field, value)
        elif zone is not None:
            setattr(zone, field, value)


def _simulate_totals(building, zone_name, overrides=None):
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


def _merge_overrides(base, extra):
    merged = dict(base or {})
    for field, value in (extra or {}).items():
        merged[field] = value
    return merged


def _dedupe_candidates(candidates):
    seen = set()
    unique = []
    for candidate in candidates:
        marker = tuple(sorted((k, repr(v)) for k, v in candidate["overrides"].items()))
        if marker in seen:
            continue
        seen.add(marker)
        unique.append(candidate)
    return unique


# ---------------------------------------------------------------------------
# Component grouping and severity
# ---------------------------------------------------------------------------


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
# Candidate generation
# ---------------------------------------------------------------------------

def _candidate(display, overrides, system, complexity, reason, components=None):
    return {
        "display": display,
        "overrides": overrides,
        "system": system,
        "complexity": complexity,
        "reason": reason,
        "components": components or [],
    }


def _pam_candidates(zone, components):
    current = [v for v in (getattr(zone, "touch_protection", []) or []) if v != "none"]
    candidates = []
    for key, label, complexity in PAM_LEVELS:
        if key in current:
            continue
        new_value = current + [key]
        candidates.append(_candidate(
            label,
            {"touch_protection": new_value},
            "touch",
            complexity,
            "Reduces Pam for touch/contact risk components.",
            components,
        ))
    return candidates


def _plps_candidates(building, components):
    current = getattr(building, "LPS_class", None)
    current_idx = _level_index(PLPS_LEVELS, current)
    candidates = []
    for i, (key, label, complexity) in enumerate(PLPS_LEVELS):
        if i <= current_idx:
            continue
        candidates.append(_candidate(
            label,
            {"LPS_class": key},
            "lps",
            complexity,
            "Reduces PLPS for direct-strike risk components.",
            components,
        ))
    return candidates


def _peb_candidates(building, components):
    line_levels = [
        getattr(line, "equipotential_bonding_level", "none") or "none"
        for line in getattr(building, "lines", [])
    ]
    current_idx = min((_level_index(PEB_LEVELS, value) for value in line_levels), default=0)
    candidates = []
    for i, (key, label, complexity) in enumerate(PEB_LEVELS):
        if i <= current_idx:
            continue
        candidates.append(_candidate(
            label,
            {"equipotential_bonding_level": key},
            "peb",
            complexity,
            "Reduces PEB for service-line shock/fire components.",
            components,
        ))
    return candidates


def _lps_peb_package_candidates(building, components):
    package_levels = [
        ("IV", "III-IV"),
        ("III", "III-IV"),
        ("II", "II"),
        ("I", "I"),
    ]

    current_lps = getattr(building, "LPS_class", None)
    current_lps_idx = _level_index(PLPS_LEVELS, current_lps)
    line_levels = [
        getattr(line, "equipotential_bonding_level", "none") or "none"
        for line in getattr(building, "lines", [])
    ]
    current_peb_idx = min((_level_index(PEB_LEVELS, value) for value in line_levels), default=0)

    candidates = []
    for lps_key, peb_key in package_levels:
        lps_idx = _level_index(PLPS_LEVELS, lps_key)
        peb_idx = _level_index(PEB_LEVELS, peb_key)
        lps_label = next((item[1] for item in PLPS_LEVELS if item[0] == lps_key), f"LPS Class {lps_key}")
        peb_label = next((item[1] for item in PEB_LEVELS if item[0] == peb_key), f"PEB Class {peb_key}")

        overrides = {}
        if lps_idx > current_lps_idx:
            overrides["LPS_class"] = lps_key
        if peb_idx > current_peb_idx:
            overrides["equipotential_bonding_level"] = peb_key
        if not overrides:
            continue

        candidates.append(_candidate(
            f"{lps_label} + {peb_label}",
            overrides,
            "lps_peb_package",
            lps_idx + peb_idx + max(0, len(overrides) - 1),
            "Annex-F-style package: reduce PLPS-related damage and PEB-related service-line risk together.",
            components,
        ))

    return candidates


def _fire_candidates(zone, components):
    current = [v for v in (getattr(zone, "fire_protection", []) or []) if v != "none"]
    candidates = []
    for key, label, complexity in RP_MEASURES:
        if key in current:
            continue
        new_value = current + [key]
        candidates.append(_candidate(
            label,
            {"fire_protection": new_value},
            "fire",
            complexity,
            "Reduces rP for fire-related physical damage risk.",
            components,
        ))
    return candidates


def _spd_candidates(building, zone, source, components, prefix="Upgrade"):
    candidates = []
    spd_levels = _spd_levels_for_source(source)
    for field, system_label, system in _spd_fields_for_zone(building, zone):
        current = getattr(zone, field, "none") or "none"
        current_idx = _level_index(spd_levels, current)
        for i, (key, _value, label) in enumerate(spd_levels):
            if i <= current_idx:
                continue
            candidates.append(_candidate(
                f"{prefix} {system_label} SPD -> {label}",
                {field: key},
                system,
                2 + i,
                f"Reduces PSPD for source {source}.",
                components,
            ))
    return candidates


def _spd_levels_for_components(components):
    sources = [
        RISK_COMPONENT_SOURCES.get(component) or FREQUENCY_COMPONENT_SOURCES.get(component)
        for component in components
        if RISK_COMPONENT_SOURCES.get(component) or FREQUENCY_COMPONENT_SOURCES.get(component)
    ]
    if sources and all(source in SOURCES_ALLOWING_BETTER_THAN_SPD for source in sources):
        return SPD_LEVELS
    return [item for item in SPD_LEVELS if item[0] not in BETTER_THAN_SPD_KEYS]


def _coordinated_spd_candidates(building, zone, components):
    fields = _spd_fields_for_zone(building, zone)
    if not fields:
        return []

    spd_levels = _spd_levels_for_components(components)
    candidates = []
    for i, (key, _value, label) in enumerate(spd_levels):
        if i == 0:
            continue

        overrides = {}
        systems = []
        for field, system_label, _system in fields:
            current = getattr(zone, field, "none") or "none"
            current_idx = _level_index(spd_levels, current)
            if i > current_idx:
                overrides[field] = key
                systems.append(system_label.lower())

        if not overrides:
            continue

        systems_label = " and ".join(systems) if systems else "available"
        candidates.append(_candidate(
            f"Install coordinated SPD for {systems_label} systems -> {label}",
            overrides,
            "coordinated_spd",
            2 + i + max(0, len(overrides) - 1),
            "Reduces PSPD-controlled risk components together.",
            components,
        ))

    return candidates


def _rc_package_candidates(building, zone, components):
    """RC uses PC. In this implementation PC uses PSPD only after LPS/natural LPS
    exists, so RC may need an LPS + SPD package to show any reduction."""
    candidates = []
    current_lps = getattr(building, "LPS_class", None)
    current_lps_idx = _level_index(PLPS_LEVELS, current_lps)
    spd_levels = _spd_levels_for_source("S1")

    for lps_i, (lps_key, lps_label, lps_complexity) in enumerate(PLPS_LEVELS):
        if lps_i <= current_lps_idx:
            continue
        for field, system_label, system in _spd_fields_for_zone(building, zone):
            current_spd = getattr(zone, field, "none") or "none"
            current_spd_idx = _level_index(spd_levels, current_spd)
            for spd_i, (spd_key, _value, spd_label) in enumerate(spd_levels):
                if spd_i <= current_spd_idx:
                    continue
                candidates.append(_candidate(
                    f"{lps_label} + upgrade {system_label} SPD -> {spd_label}",
                    {"LPS_class": lps_key, field: spd_key},
                    f"lps_{system}_spd",
                    lps_complexity + 2 + spd_i,
                    "RC is reduced by PC; in this model PC needs LPS plus coordinated SPD.",
                    components,
                ))
    return candidates


def _components_to_candidate_groups(building, zone, contributors):
    candidates = []
    components = [item["component"] for item in contributors]

    for component in components:
        if component == "RAD":
            candidates += _pam_candidates(zone, [component])
            candidates += _plps_candidates(building, [component])
        elif component == "RAT":
            candidates += _plps_candidates(building, [component])
            candidates += _pam_candidates(zone, [component])
        elif component == "RB":
            candidates += _plps_candidates(building, [component])
        elif component == "RC":
            candidates += _spd_candidates(building, zone, "S1", [component])
            candidates += _rc_package_candidates(building, zone, [component])
        elif component == "RM":
            candidates += _spd_candidates(building, zone, "S2", [component])
        elif component == "RU":
            candidates += _pam_candidates(zone, [component])
            candidates += _peb_candidates(building, [component])
        elif component == "RV":
            candidates += _peb_candidates(building, [component])
        elif component == "RW":
            candidates += _spd_candidates(building, zone, "S3", [component])
        elif component == "RZ":
            candidates += _spd_candidates(building, zone, "S4", [component])

    return _dedupe_candidates(candidates)


def _ranked_protection_factors(values, min_percent=5, top_n=5):
    grouped = _grouped_risk(values)
    total = values.get("R_total", 0) or 0
    if total <= 0:
        return []

    factors = []
    for key, config in PROTECTION_FACTORS.items():
        controlled = []
        value = 0
        for component in config["controls"]:
            component_value = grouped.get(component, 0) or 0
            if component_value <= 0:
                continue
            controlled.append({
                "component": component,
                "value": component_value,
                "percent": (component_value / total) * 100,
            })
            value += component_value

        if value <= 0:
            continue

        percent = (value / total) * 100
        if percent < min_percent:
            continue

        factors.append({
            "factor": key,
            "label": config["label"],
            "value": value,
            "percent": percent,
            "severity": _severity(percent),
            "components": controlled,
            "component_names": [item["component"] for item in controlled],
            "priority": config["priority"],
            "reason": config["reason"],
        })

    return sorted(
        factors,
        key=lambda item: (-item["percent"], item["priority"], item["factor"])
    )[:top_n]


def _tag_factor_candidates(candidates, factor):
    tagged = []
    component_names = factor.get("component_names", [])
    for candidate in candidates:
        tagged.append({
            **candidate,
            "factor": factor["factor"],
            "factor_label": factor["label"],
            "factor_percent": factor["percent"],
            "factor_value": factor["value"],
            "factor_rank": factor["priority"],
            "controlled_components": component_names,
            "engineering_reason": factor["reason"],
        })
    return tagged


def _candidates_for_factor(building, zone, factor):
    component_names = factor.get("component_names", [])
    factor_key = factor["factor"]

    if factor_key == "PSPD":
        candidates = _coordinated_spd_candidates(building, zone, component_names)
        if "RC" in component_names:
            candidates += _rc_package_candidates(building, zone, component_names)
        return _tag_factor_candidates(_dedupe_candidates(candidates), factor)

    if factor_key == "PLPS":
        candidates = _plps_candidates(building, component_names)
        if "RB" in component_names:
            candidates += _lps_peb_package_candidates(building, component_names)
        return _tag_factor_candidates(_dedupe_candidates(candidates), factor)

    if factor_key == "Pam":
        return _tag_factor_candidates(_pam_candidates(zone, component_names), factor)

    if factor_key == "PEB":
        candidates = _peb_candidates(building, component_names)
        if "RV" in component_names:
            candidates += _lps_peb_package_candidates(building, component_names)
        return _tag_factor_candidates(_dedupe_candidates(candidates), factor)

    if factor_key == "rP":
        candidates = _fire_candidates(zone, component_names)
        if "RB" in component_names or "RV" in component_names:
            candidates += _lps_peb_package_candidates(building, component_names)
        return _tag_factor_candidates(_dedupe_candidates(candidates), factor)

    return []


def _factors_to_candidates(building, zone, factors):
    candidates = []
    for index, factor in enumerate(factors):
        for candidate in _candidates_for_factor(building, zone, factor):
            candidate["factor_order"] = index
            candidates.append(candidate)
    return _dedupe_candidates(candidates)


def _display_factors_without_double_counting(factors, total):
    used_components = set()
    display = []
    for factor in factors:
        components = [
            component for component in factor["components"]
            if component["component"] not in used_components
        ]
        if not components:
            continue
        value = sum(component["value"] for component in components)
        percent = (value / total) * 100 if total > 0 else 0
        display_factor = dict(factor)
        display_factor["components"] = components
        display_factor["component_names"] = [component["component"] for component in components]
        display_factor["value"] = value
        display_factor["percent"] = percent
        display_factor["severity"] = _severity(percent)
        display.append(display_factor)
        used_components.update(display_factor["component_names"])
    return display


# ---------------------------------------------------------------------------
# Planner
# ---------------------------------------------------------------------------

COMPONENTS_BY_OVERRIDE_FIELD = {
    "LPS_class": {"RAT", "RAD", "RB"},
    "touch_protection": {"RAT", "RAD", "RU"},
    "equipotential_bonding_level": {"RU", "RV", "RW"},
    "fire_protection": {"RB", "RV"},
    "power_spd_level": {"RC", "RM", "RW", "RZ"},
    "telecom_spd_level": {"RC", "RM", "RW", "RZ"},
}


def _candidate_component_coverage(candidate):
    """Count how many dominant components this candidate can physically affect."""
    controlled = set(candidate.get("controlled_components") or candidate.get("components") or [])
    if not controlled:
        return 0

    addressed = set()
    for field in (candidate.get("overrides") or {}):
        addressed.update(COMPONENTS_BY_OVERRIDE_FIELD.get(field, set()))
    return len(controlled & addressed)


def _simulate_candidate(building, zone_name, candidate, current_r, current_f, rt, ft):
    sim = _simulate_totals(building, zone_name, candidate["overrides"])
    new_r = sim["r_total"]
    new_f = sim["f_total"]
    reduction = (current_r - new_r) if current_r is not None and new_r is not None else 0
    frequency_reduction = (current_f - new_f) if current_f is not None and new_f is not None else 0

    return {
        **candidate,
        "old_r": current_r,
        "new_r": new_r,
        "old_f": current_f,
        "new_f": new_f,
        "rt": rt,
        "ft": ft,
        "risk_reduction": reduction,
        "frequency_reduction": frequency_reduction,
        "reduces_risk": reduction > MIN_IMPROVEMENT,
        "reduces_frequency": frequency_reduction > MIN_IMPROVEMENT,
        "risk_sufficient": new_r is not None and new_r <= rt,
        "frequency_sufficient": new_f is not None and ft is not None and new_f <= ft,
        "component_coverage": _candidate_component_coverage(candidate),
    }


def _choose_best_candidate(simulated):
    improving = [item for item in simulated if item["reduces_risk"]]
    if not improving:
        return None

    sufficient = [item for item in improving if item["risk_sufficient"]]
    if sufficient:
        return sorted(
            sufficient,
            key=lambda item: (
                -item.get("component_coverage", 0),
                0 if item.get("system") == "lps_peb_package" else 1,
                item["complexity"],
                len(item["overrides"]),
                abs(item["new_r"] - item["rt"]) if item.get("new_r") is not None else float("inf"),
                item["new_r"],
            )
        )[0]

    return sorted(
        improving,
        key=lambda item: (
            -item.get("component_coverage", 0),
            item.get("factor_order", 99),
            item.get("factor_rank", 99),
            item["new_r"],
            len(item["overrides"]),
            item["complexity"],
            -item["risk_reduction"],
        )
    )[0]


def _build_action_from_step(step, target="risk"):
    risk_sufficient = step["risk_sufficient"]
    frequency_sufficient = step["frequency_sufficient"]
    is_sufficient = frequency_sufficient if target == "frequency" else risk_sufficient
    controlled_components = step.get("controlled_components", [])
    needs_engineering_review = (
        target == "risk"
        and not risk_sufficient
        and "RC" in controlled_components
    )

    return {
        "type": "apply_protection",
        "display": step["display"],
        "field": "protection_plan",
        "value": step["overrides"],
        "system": step["system"],
        "overrides": step["overrides"],
        "old_r": step["old_r"],
        "new_r": step["new_r"],
        "old_f": step["old_f"],
        "new_f": step["new_f"],
        "rt": step["rt"],
        "ft": step["ft"],
        "estimated_r": step["new_r"],
        "estimated_f": step["new_f"],
        "reduces_risk": step["reduces_risk"],
        "reduces_frequency": step["reduces_frequency"],
        "risk_sufficient": risk_sufficient,
        "frequency_sufficient": frequency_sufficient,
        "is_sufficient": is_sufficient,
        "is_minimum_needed": is_sufficient,
        "note": f"Estimated R after: {_fmt(step['new_r'])}; estimated F after: {_fmt(step['new_f'])}",
        "reason": step["reason"],
        "probability_factor": step.get("factor"),
        "probability_factor_label": step.get("factor_label"),
        "protection_factor": step.get("factor"),
        "protection_factor_label": step.get("factor_label"),
        "protection_group": step.get("factor_label"),
        "controlled_components": controlled_components,
        "component_coverage": step.get("component_coverage", 0),
        "requires_engineering_review": needs_engineering_review,
        "engineering_reason": step.get("engineering_reason"),
        "engineering_basis": step.get("engineering_reason") or step.get("reason"),
        "selected_because": (
            "Selected because it is the minimum sufficient simulated option for F <= FT."
            if target == "frequency" and is_sufficient
            else "Selected because it is the minimum sufficient simulated option for R <= RT."
            if target == "risk" and is_sufficient
            else (
                "Normal IEC table candidates up to LPL I reduced the risk, but did not reach RT. "
                "Because RC/S1 remains involved, better-than-LPL-I PSPD is not auto-selected; Annex D/custom engineering review is required."
            )
            if needs_engineering_review
            else "Selected because it produced the strongest simulated improvement among available options."
        ),
    }


def _build_plan_action(initial, final, steps, cumulative_overrides, target="risk"):
    if not steps:
        return None

    risk_sufficient = final["r_total"] is not None and final["r_total"] <= initial["rt"]
    frequency_sufficient = (
        final["f_total"] is not None
        and initial["ft"] is not None
        and final["f_total"] <= initial["ft"]
    )
    is_sufficient = frequency_sufficient if target == "frequency" else risk_sufficient

    display = steps[0]["display"] if len(steps) == 1 else f"Recommended protection plan ({len(steps)} steps)"
    controlled_components = sorted({
        component
        for step in steps
        for component in step.get("controlled_components", [])
    })
    needs_engineering_review = (
        target == "risk"
        and not risk_sufficient
        and "RC" in controlled_components
    )

    return {
        "type": "apply_protection",
        "display": display,
        "field": "protection_plan",
        "value": cumulative_overrides,
        "system": "plan",
        "overrides": cumulative_overrides,
        "old_r": initial["r_total"],
        "new_r": final["r_total"],
        "old_f": initial["f_total"],
        "new_f": final["f_total"],
        "rt": initial["rt"],
        "ft": initial["ft"],
        "estimated_r": final["r_total"],
        "estimated_f": final["f_total"],
        "reduces_risk": final["r_total"] is not None and final["r_total"] < initial["r_total"],
        "reduces_frequency": final["f_total"] is not None and final["f_total"] < initial["f_total"],
        "risk_sufficient": risk_sufficient,
        "frequency_sufficient": frequency_sufficient,
        "is_sufficient": is_sufficient,
        "is_minimum_needed": is_sufficient,
        "note": f"Plan result R: {_fmt(initial['r_total'])} -> {_fmt(final['r_total'])}; F: {_fmt(initial['f_total'])} -> {_fmt(final['f_total'])}",
        "probability_factor": steps[0].get("factor"),
        "probability_factor_label": steps[0].get("factor_label"),
        "protection_factor": steps[0].get("factor"),
        "protection_factor_label": steps[0].get("factor_label"),
        "protection_group": steps[0].get("factor_label"),
        "controlled_components": controlled_components,
        "component_coverage": max((step.get("component_coverage", 0) for step in steps), default=0),
        "requires_engineering_review": needs_engineering_review,
        "engineering_reason": steps[0].get("engineering_reason"),
        "engineering_basis": steps[0].get("engineering_reason") or steps[0].get("reason"),
        "selected_because": (
            "Selected because the simulated plan reaches F <= FT with the minimum sufficient protection."
            if target == "frequency" and is_sufficient
            else "Selected because the simulated plan reaches R <= RT with the minimum sufficient protection."
            if target == "risk" and is_sufficient
            else (
                "The simulated plan reduces risk, but R is still above RT. RC/S1 remains involved, so better-than-LPL-I PSPD is not auto-selected; Annex D/custom engineering review is required."
            )
            if needs_engineering_review
            else "Selected because the simulated plan reduces risk, although more engineering measures may still be needed."
        ),
        "plan": {
            "steps": [_build_action_from_step(step, target=target) for step in steps],
            "factor_sequence": [
                {
                    "factor": step.get("factor"),
                    "label": step.get("factor_label"),
                    "components": step.get("controlled_components", []),
                    "display": step.get("display"),
                }
                for step in steps
            ],
            "old_r": initial["r_total"],
            "new_r": final["r_total"],
            "old_f": initial["f_total"],
            "new_f": final["f_total"],
            "rt": initial["rt"],
            "ft": initial["ft"],
            "risk_sufficient": risk_sufficient,
            "frequency_sufficient": frequency_sufficient,
        },
    }


def _plan_for_zone(building, zone_name):
    working = copy.deepcopy(building)
    initial = _simulate_totals(working, zone_name, {})
    rt = initial["rt"] or 1e-5
    ft = initial["ft"] or 5e-2
    initial["rt"] = rt
    initial["ft"] = ft

    steps = []
    factor_history = []
    cumulative_overrides = {}
    current = initial

    for _ in range(MAX_PLAN_STEPS):
        if current["r_total"] is None:
            break
        if current["r_total"] <= rt:
            break

        zone = _zone_by_name(working, zone_name)
        if zone is None:
            break

        factors = _ranked_protection_factors(
            current["risk_zone"],
            min_percent=5,
            top_n=5,
        )
        if not factors:
            break
        factor_history.append(factors)

        candidates = _factors_to_candidates(working, zone, factors)
        simulated = [
            _simulate_candidate(
                working,
                zone_name,
                candidate,
                current["r_total"],
                current["f_total"],
                rt,
                ft,
            )
            for candidate in candidates
        ]
        best = _choose_best_candidate(simulated)
        if best is None:
            break

        steps.append(best)
        cumulative_overrides = _merge_overrides(cumulative_overrides, best["overrides"])
        _apply_overrides(working, zone_name, best["overrides"])
        current = _simulate_totals(working, zone_name, {})
        current["rt"] = current["rt"] or rt
        current["ft"] = current["ft"] or ft

    action = _build_plan_action(initial, current, steps, cumulative_overrides)
    return {
        "initial": initial,
        "final": current,
        "steps": steps,
        "factor_history": factor_history,
        "initial_factors": factor_history[0] if factor_history else [],
        "action": action,
    }


# ---------------------------------------------------------------------------
# Public engine
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
    def get_top_protection_factors(values, min_percent=5, top_n=5):
        return _ranked_protection_factors(values, min_percent, top_n)

    @staticmethod
    def generate_for_zone(zone_name, values, zone, building):
        rt = values.get("RT", getattr(zone, "RT", 1e-5)) or 1e-5
        current_r = values.get("R_total", 0) or 0
        if current_r <= rt:
            return []

        contributors = ProtectionRecommendationEngine.get_top_risk_contributors(values)
        plan = _plan_for_zone(building, zone_name)
        plan_action = plan["action"]
        factors = plan.get("initial_factors") or _ranked_protection_factors(values)
        display_factors = _display_factors_without_double_counting(factors, current_r)

        output = []
        dominant_names = ", ".join(item["component"] for item in contributors)
        dominant_factor_names = ", ".join(
            f"{item['factor']} ({item['label']})" for item in factors
        ) or "none"
        plan_suffix = ""
        if plan_action:
            if plan_action["risk_sufficient"]:
                plan_suffix = "The generated protection plan brings risk within the tolerable limit."
            elif plan_action["reduces_risk"]:
                plan_suffix = "The generated protection plan reduces risk, but further engineering measures may be needed."
        else:
            plan_suffix = "No available protection plan reduced total risk in simulation."

        if display_factors:
            for index, item in enumerate(display_factors):
                controlled = ", ".join(item["component_names"])
                main_component = max(
                    item["components"],
                    key=lambda component: component["value"],
                )["component"] if item["components"] else None
                actions = [plan_action] if index == 0 and plan_action else []
                output.append({
                    "component": controlled,
                    "value": item["value"],
                    "percent": item["percent"],
                    "severity": item["severity"],
                    "protection_factor": item["factor"],
                    "protection_factor_label": item["label"],
                    "probability_driver": f"{item['factor']} ({item['label']})",
                    "protection_group": item["label"],
                    "dominant_components": item["component_names"],
                    "main_component": main_component,
                    "engineering_basis": item["reason"],
                    "old_r": current_r,
                    "old_f": plan["initial"].get("f_total"),
                    "rt": rt,
                    "ft": plan["initial"].get("ft"),
                    "summary": (
                        f"Dominant risk components {controlled} together contribute "
                        f"{item['percent']:.1f}% of the total risk "
                        f"(combined value: {item['value']:.3e}). "
                        f"These components are mainly controlled by {item['factor']} "
                        f"({item['label']}). {item['reason']} "
                        f"Dominant risk components considered: {dominant_names}. {plan_suffix}"
                    ),
                    "actions": actions,
                    "controlled_components": item["component_names"],
                    "selected_because": (
                        plan_action.get("selected_because")
                        if index == 0 and plan_action
                        else "Shown as a dominant protection-factor group for engineering context."
                    ),
                })
            return output

        for index, item in enumerate(contributors):
            component = item["component"]
            actions = [plan_action] if index == 0 and plan_action else []
            output.append({
                "component": component,
                "value": item["value"],
                "percent": item["percent"],
                "severity": item["severity"],
                "probability_driver": "Protection plan" if index == 0 else "Context",
                "dominant_components": [component],
                "main_component": component,
                "protection_factor": None,
                "protection_factor_label": None,
                "protection_group": None,
                "engineering_basis": "Fallback component-level recommendation when no protection-factor group is available.",
                "old_r": current_r,
                "old_f": plan["initial"].get("f_total"),
                "rt": rt,
                "ft": plan["initial"].get("ft"),
                "summary": (
                    f"{component} contributes {item['percent']:.1f}% of total risk "
                    f"(value: {item['value']:.3e}). Dominant contributors considered: "
                    f"{dominant_names}. Dominant protection factors considered: "
                    f"{dominant_factor_names}. {plan_suffix}"
                ),
                "actions": actions,
                "controlled_components": [component],
                "selected_because": (
                    plan_action.get("selected_because")
                    if index == 0 and plan_action
                    else "Shown as a dominant component for engineering context."
                ),
            })

        return output

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

        if not contributors or current_f <= ft:
            return []

        current = _simulate_totals(building, zone_name, {})
        current_r = current.get("r_total")
        rt = current.get("rt") or getattr(zone, "RT", 1e-5) or 1e-5
        top = contributors[0]
        contributor_names = [item["component"] for item in contributors]

        candidates = _coordinated_spd_candidates(building, zone, contributor_names)
        simulated = [
            _simulate_candidate(building, zone_name, candidate, current_r, current_f, rt, ft)
            for candidate in candidates
        ]
        best = None
        improving = [item for item in simulated if item["reduces_frequency"]]
        sufficient = [item for item in improving if item["frequency_sufficient"]]
        if sufficient:
            best = sorted(
                sufficient,
                key=lambda item: (
                    item["complexity"],
                    len(item["overrides"]),
                    abs(item["new_f"] - ft) if item.get("new_f") is not None else float("inf"),
                    item["new_f"],
                )
            )[0]
        elif improving:
            best = sorted(improving, key=lambda item: item["new_f"])[0]

        actions = [_build_action_from_step(best, target="frequency")] if best else []
        dominant_list = ", ".join(c["component"] for c in contributors)
        selected_because = (
            actions[0].get("selected_because")
            if actions
            else "No coordinated SPD candidate reduced frequency in simulation."
        )

        return [{
            "component": top["component"],
            "value": top["value"],
            "percent": top["percent"],
            "severity": top["severity"],
            "protection_factor": "PSPD",
            "protection_factor_label": PROTECTION_FACTORS["PSPD"]["label"],
            "probability_driver": f"PSPD ({PROTECTION_FACTORS['PSPD']['label']})",
            "protection_group": PROTECTION_FACTORS["PSPD"]["label"],
            "dominant_components": contributor_names,
            "main_component": top["component"],
            "engineering_basis": (
                "Frequency planning is handled separately from risk planning. "
                "Available internal systems are evaluated with coordinated SPD candidates."
            ),
            "old_r": current_r,
            "old_f": current_f,
            "rt": rt,
            "ft": ft,
            "summary": (
                f"Frequency exceeds the tolerable limit. Main contributors: {dominant_list}. "
                f"Coordinated SPD candidates for all available internal systems were simulated "
                f"against the full risk and frequency engines."
            ),
            "actions": actions,
            "controlled_components": contributor_names,
            "selected_because": selected_because,
            "sufficient_exists": any(a.get("frequency_sufficient") for a in actions),
        }]

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


# Backward-compatible helper names retained for imports/tests.
def _simulate_r_total(building, zone_name, zone_overrides):
    return _simulate_totals(building, zone_name, zone_overrides).get("r_total")


def _simulate_f_total(building, zone_name, zone_overrides):
    return _simulate_totals(building, zone_name, zone_overrides).get("f_total")
