from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from datetime import datetime


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def pdf_value(value):
    if isinstance(value, bool):
        return "Yes" if value else "No"
    if value is None:
        return "-"
    if isinstance(value, list):
        return ", ".join(str(i) for i in value) if value else "-"
    if isinstance(value, float):
        if value == 0:
            return "0"
        return f"{value:.3e}"
    return str(value)


ROSE = colors.HexColor("#e11d48")
ROSE_LIGHT = colors.HexColor("#fce7eb")
SLATE = colors.HexColor("#334155")
SLATE_LIGHT = colors.HexColor("#f1f5f9")
TEAL = colors.HexColor("#0d9488")
TEAL_LIGHT = colors.HexColor("#ccfbf1")
ROSE_BG = colors.HexColor("#fff1f2")


def make_table(data_dict, header_color=ROSE_LIGHT):
    data = [["Parameter", "Value"]]
    for k, v in data_dict.items():
        data.append([str(k), pdf_value(v)])
    t = Table(data, colWidths=[8 * cm, 8 * cm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), header_color),
        ("TEXTCOLOR", (0, 0), (-1, 0), SLATE),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cbd5e1")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, SLATE_LIGHT]),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ]))
    return t


def status_table(rows, status_ok):
    """Two-column metrics table with a status colour."""
    bg = TEAL_LIGHT if status_ok else ROSE_BG
    data = [[k, pdf_value(v)] for k, v in rows]
    t = Table(data, colWidths=[8 * cm, 8 * cm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), bg),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cbd5e1")),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("TEXTCOLOR", (0, 0), (0, -1), SLATE),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ]))
    return t


# ---------------------------------------------------------------------------
# Main PDF builder
# ---------------------------------------------------------------------------

def generate_pdf_report(filename, building_data, lines_data, zones_data,
                        risk_results, frequency_results, annex_e_results,
                        protection_recommendations, frequency_recommendations):

    doc = SimpleDocTemplate(
        filename, pagesize=A4,
        rightMargin=1.6 * cm, leftMargin=1.6 * cm,
        topMargin=1.6 * cm, bottomMargin=1.6 * cm,
    )
    styles = getSampleStyleSheet()

    h1 = ParagraphStyle("h1", parent=styles["Heading1"], textColor=ROSE, fontSize=15, spaceAfter=8)
    h2 = ParagraphStyle("h2", parent=styles["Heading2"], textColor=SLATE, fontSize=12, spaceAfter=6)
    h3 = ParagraphStyle("h3", parent=styles["Heading3"], textColor=SLATE, fontSize=10, spaceAfter=4)
    body = ParagraphStyle("body", parent=styles["BodyText"], fontSize=9, spaceAfter=3)
    small = ParagraphStyle("small", parent=styles["BodyText"], fontSize=8, textColor=colors.HexColor("#64748b"))

    el = []

    # ---------------- COVER ----------------
    el.append(Spacer(1, 4 * cm))
    el.append(Paragraph("Lightning Risk Assessment Report", ParagraphStyle(
        "cover", parent=styles["Title"], fontSize=24, textColor=ROSE)))
    el.append(Spacer(1, 0.3 * cm))
    el.append(Paragraph("Based on IEC 62305-2:2024", ParagraphStyle(
        "coversub", parent=styles["Heading2"], fontSize=13, textColor=SLATE, alignment=1)))
    el.append(Spacer(1, 1 * cm))
    el.append(Paragraph(f"Building: {building_data.get('name', 'Unnamed structure')}", body))
    el.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", body))
    el.append(Paragraph(f"Zones assessed: {len(zones_data)}  |  Service lines: {len(lines_data)}", body))
    el.append(PageBreak())

    # ---------------- 1. BUILDING ----------------
    el.append(Paragraph("1. Building Information", h1))
    el.append(make_table({
        "Building Name": building_data.get("name", "-"),
        "Length L (m)": building_data.get("L"),
        "Width W (m)": building_data.get("W"),
        "Height H (m)": building_data.get("H"),
        "Lightning Density NSG": building_data.get("NSG"),
        "Correction factor k": building_data.get("k"),
        "Relative Location": building_data.get("location_type"),
        "LPS Class": building_data.get("LPS_class") or "No LPS",
        "Thunderstorm Warning System": building_data.get("TWS"),
        "Wall Material": building_data.get("wall_material"),
        "Roof Material": building_data.get("roof_material"),
        "Structure Shielding": building_data.get("structure_shielding"),
        "Adjacent Structure": building_data.get("adjacent_structure"),
    }))
    el.append(PageBreak())

    # ---------------- 2. LINES ----------------
    el.append(Paragraph("2. Service Line Information", h1))
    if not lines_data:
        el.append(Paragraph("No service lines defined.", body))
    for i, line in enumerate(lines_data, 1):
        el.append(Paragraph(f"Line {i}: {line.get('name', '-')}", h2))
        el.append(make_table({
            "Service Type": line.get("service"),
            "External Cable": line.get("external_cable"),
            "Installation": line.get("installation"),
            "Line Type": line.get("type"),
            "Environmental Factor": line.get("environmental"),
            "Length LL (m)": line.get("LL"),
            "Impulse Withstand Uw (kV)": line.get("Uw"),
            "Equipotential Bonding Level": line.get("equipotential_bonding_level"),
            "Shielded": line.get("shielded"),
        }))
        el.append(Spacer(1, 0.3 * cm))
    el.append(PageBreak())

    # ---------------- 3. ZONES ----------------
    el.append(Paragraph("3. Risk Zone Information", h1))
    for i, zone in enumerate(zones_data, 1):
        el.append(Paragraph(f"Zone {i}: {zone.get('name', '-')}", h2))
        el.append(make_table({
            "People Present": zone.get("people_present"),
            "People Exposed on Structure": zone.get("people_exposed_on_structure"),
            "Internal System Present": zone.get("internal_system_present"),
            "Presence Time tz (h/yr)": zone.get("tz"),
            "Equipment Exposure te (h/yr)": zone.get("te"),
            "Floor Type": zone.get("floor_type"),
            "Fire Risk": zone.get("fire_risk"),
            "Power SPD Level": zone.get("power_spd_level"),
            "Telecom SPD Level": zone.get("telecom_spd_level"),
            "Power Internal Wiring (KS3)": zone.get("power_internal_wiring"),
            "Telecom Internal Wiring (KS3)": zone.get("telecom_internal_wiring"),
            "Loss Category": zone.get("loss_category"),
        }))
        el.append(Spacer(1, 0.3 * cm))
    el.append(PageBreak())

    # ---------------- 4. RISK RESULTS ----------------
    el.append(Paragraph("4. Risk Assessment Results", h1))
    for zone_name, vals in risk_results.items():
        ok = vals.get("risk_status") != "Protection required"
        status_text = "PROTECTION NOT REQUIRED" if ok else "PROTECTION REQUIRED"
        el.append(Paragraph(f"Zone: {zone_name}", h2))
        el.append(Paragraph(
            f'<b>Status:</b> <font color="{"#0d9488" if ok else "#e11d48"}">{status_text}</font>', body))
        el.append(status_table([
            ("L1 Risk (loss of life)", vals.get("RL1")),
            ("L2 Risk (physical damage)", vals.get("RL2")),
            ("Total Risk R", vals.get("R_total")),
            ("Tolerable Risk RT", vals.get("RT")),
        ], ok))
        el.append(Spacer(1, 0.2 * cm))
        el.append(Paragraph("Risk components", h3))
        comp = {k: vals.get(k, 0) for k in [
            "RAT", "RAD", "RB1", "RB2", "RC1", "RC2", "RM1", "RM2",
            "RU", "RV1", "RV2", "RW1", "RW2", "RZ1", "RZ2"
        ] if vals.get(k, 0)}
        if comp:
            el.append(make_table(comp))
        el.append(Spacer(1, 0.4 * cm))
    el.append(PageBreak())

    # ---------------- 5. RISK RECOMMENDATIONS ----------------
    el.append(Paragraph("5. Risk Protection Recommendations", h1))
    any_rec = False
    for zone_name, recs in protection_recommendations.items():
        if not recs:
            continue
        any_rec = True
        el.append(Paragraph(f"Zone: {zone_name}", h2))
        for item in recs:
            el.append(Paragraph(
                f"{item['component']} — {item['percent']:.1f}% contribution ({item['severity']})", h3))
            if item.get("summary"):
                el.append(Paragraph(item["summary"], small))
            el.append(Paragraph(f"Main adjustable factor: {item.get('probability_driver', '-')}", body))
            for action in item.get("actions", []):
                tick = "[sufficient]" if action.get("is_sufficient") else "[partial]"
                est = action.get("estimated_r")
                est_txt = f" — estimated risk after: {est:.3e}" if est is not None else ""
                el.append(Paragraph(f"&bull; {action['display']} {tick}{est_txt}", body))
            el.append(Spacer(1, 0.3 * cm))
    if not any_rec:
        el.append(Paragraph("All zones are within the tolerable risk limit. No protection measures required.", body))
    el.append(PageBreak())

    # ---------------- 6. FREQUENCY RESULTS ----------------
    el.append(Paragraph("6. Frequency Assessment Results", h1))
    for zone_name, vals in frequency_results.items():
        if vals.get("frequency_status") == "Not applicable":
            el.append(Paragraph(f"Zone: {zone_name} — no internal systems (not applicable)", body))
            continue
        ok = vals.get("frequency_status") != "Protection required"
        status_text = "WITHIN LIMIT" if ok else "PROTECTION REQUIRED"
        el.append(Paragraph(f"Zone: {zone_name}", h2))
        el.append(Paragraph(
            f'<b>Status:</b> <font color="{"#0d9488" if ok else "#e11d48"}">{status_text}</font>', body))
        el.append(status_table([
            ("FC (flash to structure)", vals.get("FC")),
            ("FM (flash near structure)", vals.get("FM")),
            ("FWP (flash to power line)", vals.get("FWP")),
            ("FWT (flash to telecom line)", vals.get("FWT")),
            ("FZP (flash near power line)", vals.get("FZP")),
            ("FZT (flash near telecom line)", vals.get("FZT")),
            ("Total Frequency F", vals.get("F_total")),
            ("Tolerable Frequency FT", vals.get("FT")),
        ], ok))
        el.append(Spacer(1, 0.4 * cm))
    el.append(PageBreak())

    # ---------------- 7. FREQUENCY RECOMMENDATIONS ----------------
    el.append(Paragraph("7. Frequency Protection Recommendations", h1))
    any_freq = False
    for zone_name, recs in frequency_recommendations.items():
        if not recs:
            continue
        any_freq = True
        el.append(Paragraph(f"Zone: {zone_name}", h2))
        for item in recs:
            el.append(Paragraph(
                f"{item['component']} — {item['percent']:.1f}% contribution ({item['severity']})", h3))
            if item.get("summary"):
                el.append(Paragraph(item["summary"], small))
            for action in item.get("actions", []):
                tick = "[sufficient]" if action.get("is_sufficient") else "[partial]"
                est = action.get("estimated_r")
                est_txt = f" — estimated frequency after: {est:.3e}" if est is not None else ""
                el.append(Paragraph(f"&bull; {action['display']} {tick}{est_txt}", body))
            el.append(Spacer(1, 0.3 * cm))
    if not any_freq:
        el.append(Paragraph("All zones are within the tolerable frequency limit. No protection measures required.", body))

    # ---------------- 8. ANNEX E ----------------
    annex_e_has_data = any(v.get("RE_total", 0) for v in annex_e_results.values())
    if annex_e_has_data:
        el.append(PageBreak())
        el.append(Paragraph("8. Environmental Risk (Annex E)", h1))
        for zone_name, vals in annex_e_results.items():
            if not vals.get("RE_total", 0):
                continue
            el.append(Paragraph(f"Zone: {zone_name}", h2))
            el.append(make_table({
                "RE1": vals.get("RE1"),
                "RE2": vals.get("RE2"),
                "RE Total": vals.get("RE_total"),
            }))
            el.append(Spacer(1, 0.3 * cm))

    # ---------------- FOOTER NOTE ----------------
    el.append(Spacer(1, 0.5 * cm))
    el.append(Paragraph(
        "This report was generated by the Web-Based Lightning Risk Assessment Tool, "
        "based on MS IEC 62305-2:2024. Values are computed using Annex A (N), Annex B (P), "
        "Annex C (L), and Annex E methods. Recommendations are derived by forward simulation "
        "of protection measures against the tolerable limits.", small))

    doc.build(el)
    return filename
