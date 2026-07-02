"""
pdf_generator.py — Lightning Risk Assessment Report

Builds a formal, section-numbered engineering PDF report following the
IEC 62305-2:2024 risk management methodology, using the tool's own
calculation output (risk_results, frequency_results, annex_e_results,
protection_recommendations, frequency_recommendations, protection_plan).

No calculation logic lives here — this module only formats numbers that
were already produced by RiskEngine / FrequencyEngine / NModule /
ProtectionRecommendationEngine. Collection-area and dangerous-event values
(Section 4) are recomputed from the same building/line inputs using
NModule, since those intermediate Annex A values are not stored on the
final risk_results dict.
"""

import math
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, HRFlowable
)
from reportlab.graphics.shapes import Drawing, Polygon
from reportlab.platypus.flowables import Flowable

from services.building_builder import build_building_from_session
from modules.n_module import NModule


# ---------------------------------------------------------------------------
# Palette / styles
# ---------------------------------------------------------------------------

BRAND = colors.HexColor("#4338CA")      # indigo
TEAL = colors.HexColor("#0D9488")
DANGER = colors.HexColor("#DC2626")
SLATE = colors.HexColor("#334155")
SLATE_LIGHT = colors.HexColor("#F8FAFC")
BORDER = colors.HexColor("#E2E8F0")

STYLES = getSampleStyleSheet()

STYLES.add(ParagraphStyle(
    "ReportTitle", parent=STYLES["Title"], fontSize=22, leading=26,
    textColor=SLATE, spaceAfter=4, alignment=TA_CENTER,
))
STYLES.add(ParagraphStyle(
    "ReportSubtitle", parent=STYLES["Normal"], fontSize=10.5, leading=14,
    textColor=BRAND, alignment=TA_CENTER, spaceAfter=18,
))
STYLES.add(ParagraphStyle(
    "H1", parent=STYLES["Heading1"], fontSize=14, leading=18,
    textColor=colors.white, spaceBefore=0, spaceAfter=0,
    backColor=BRAND, borderPadding=(6, 8, 6, 8),
))
STYLES.add(ParagraphStyle(
    "H2", parent=STYLES["Heading2"], fontSize=11.5, leading=15,
    textColor=BRAND, spaceBefore=12, spaceAfter=6,
))
STYLES.add(ParagraphStyle(
    "Body", parent=STYLES["Normal"], fontSize=9.5, leading=14,
    textColor=SLATE, spaceAfter=6, alignment=TA_LEFT,
))
STYLES.add(ParagraphStyle(
    "Caption", parent=STYLES["Normal"], fontSize=8.5, leading=11,
    textColor=colors.HexColor("#64748B"), spaceAfter=10, spaceBefore=2,
    fontName="Helvetica-Oblique",
))
STYLES.add(ParagraphStyle(
    "TableHeader", parent=STYLES["Normal"], fontSize=8.3, leading=10,
    textColor=colors.white, fontName="Helvetica-Bold", alignment=TA_CENTER,
))
STYLES.add(ParagraphStyle(
    "TableCell", parent=STYLES["Normal"], fontSize=8.3, leading=10.5,
    textColor=SLATE, alignment=TA_CENTER,
))
STYLES.add(ParagraphStyle(
    "TableCellLeft", parent=STYLES["Normal"], fontSize=8.3, leading=10.5,
    textColor=SLATE, alignment=TA_LEFT,
))
STYLES.add(ParagraphStyle(
    "TocItem", parent=STYLES["Normal"], fontSize=10, leading=17,
    textColor=SLATE,
))
STYLES.add(ParagraphStyle(
    "KeyFinding", parent=STYLES["Normal"], fontSize=9.5, leading=14,
    textColor=SLATE, spaceAfter=4, leftIndent=10,
))
STYLES.add(ParagraphStyle(
    "SummaryLabel", parent=STYLES["Normal"], fontSize=9.5, leading=13,
    textColor=colors.HexColor("#64748B"),
))
STYLES.add(ParagraphStyle(
    "SummaryValue", parent=STYLES["Normal"], fontSize=9.5, leading=13,
    textColor=SLATE, fontName="Helvetica-Bold",
))


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------

def sci(value, digits=3):
    """Format a number in scientific notation with a proper <super> exponent
    for use inside a reportlab Paragraph, e.g. '1.793 &times; 10<super>-5</super>'."""
    if value is None:
        return "—"
    try:
        value = float(value)
    except (TypeError, ValueError):
        return str(value)
    if value == 0:
        return "0"
    exponent = math.floor(math.log10(abs(value)))
    mantissa = value / (10 ** exponent)
    return f"{mantissa:.{digits}f} &times; 10<super>{exponent}</super>"


def p(text, style="TableCell"):
    return Paragraph(text if text is not None else "—", STYLES[style])


def fnum(value, digits=2):
    if value is None:
        return "—"
    try:
        return f"{float(value):.{digits}f}"
    except (TypeError, ValueError):
        return str(value)


def status_badge(text, kind="pass"):
    color = {
        "pass": TEAL, "fail": DANGER, "warn": colors.HexColor("#D97706"),
    }.get(kind, SLATE)
    style = ParagraphStyle(
        "Badge", parent=STYLES["Normal"], fontSize=11, leading=14,
        textColor=colors.white, alignment=TA_CENTER, fontName="Helvetica-Bold",
        backColor=color, borderPadding=(6, 10, 6, 10),
    )
    return Paragraph(text, style)


def section_heading(number, title):
    label = f"{number}&nbsp;&nbsp;{title}" if number else title
    return Paragraph(label, STYLES["H1"])


def table_caption(text):
    return Paragraph(text, STYLES["Caption"])


class LightningBolt(Flowable):
    """A small self-contained lightning-bolt glyph, drawn as a polygon so the
    report doesn't depend on an external image asset."""
    def __init__(self, size=16, color=BRAND):
        Flowable.__init__(self)
        self.size = size
        self.color = color
        self.width = size
        self.height = size

    def draw(self):
        s = self.size
        pts = [
            0.58 * s, 1.0 * s,
            0.10 * s, 0.42 * s,
            0.40 * s, 0.42 * s,
            0.30 * s, 0.0,
            0.90 * s, 0.60 * s,
            0.55 * s, 0.60 * s,
        ]
        d = Drawing(s, s)
        d.add(Polygon(pts, fillColor=self.color, strokeColor=None))
        d.drawOn(self.canv, 0, 0)


def std_table(data, col_widths, header_rows=1, align_first_left=True):
    """Build a table with a brand-colored header row and light zebra rows."""
    t = Table(data, colWidths=col_widths, repeatRows=header_rows)
    style = [
        ("BACKGROUND", (0, 0), (-1, header_rows - 1), BRAND),
        ("TEXTCOLOR", (0, 0), (-1, header_rows - 1), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
    ]
    for row in range(header_rows, len(data)):
        if (row - header_rows) % 2 == 1:
            style.append(("BACKGROUND", (0, row), (-1, row), SLATE_LIGHT))
    if align_first_left:
        style.append(("ALIGN", (0, header_rows), (0, -1), "LEFT"))
    t.setStyle(TableStyle(style))
    return t


def status_cell(status_text):
    ok = status_text not in ("Protection required", "Fail", "FAIL")
    color = TEAL if ok else DANGER
    label = "PASS" if ok else "PROTECTION REQUIRED"
    style = ParagraphStyle(
        "StatusCell", parent=STYLES["TableCell"], textColor=colors.white,
        fontName="Helvetica-Bold", backColor=color, borderPadding=(2, 4, 2, 4),
    )
    return Paragraph(label, style)


def comparison_status_cell(status_text):
    if status_text in ("Protection not applied", "Not applied"):
        color = colors.HexColor("#64748B")
        label = "NOT APPLIED"
    elif status_text in ("Protection required", "Further protection required", "Fail", "FAIL"):
        color = DANGER
        label = "FURTHER PROTECTION REQUIRED"
    else:
        color = TEAL
        label = "PASS"
    style = ParagraphStyle(
        "CompareStatusCell", parent=STYLES["TableCell"], textColor=colors.white,
        fontName="Helvetica-Bold", backColor=color, borderPadding=(2, 4, 2, 4),
    )
    return Paragraph(label, style)


def input_label(key):
    return str(key).replace("_", " ").strip().title()


def input_value(value):
    if value is None or value == "":
        return "-"
    if isinstance(value, bool):
        return "Yes" if value else "No"
    if isinstance(value, (list, tuple)):
        if not value:
            return "-"
        return ", ".join(input_value(item) for item in value)
    if isinstance(value, dict):
        if not value:
            return "-"
        return "; ".join(f"{input_label(k)}: {input_value(v)}" for k, v in value.items())
    return str(value).replace("_", " ")


def _complete_input_rows(item_name, payload):
    rows = []
    for key in sorted((payload or {}).keys()):
        rows.append([item_name, input_label(key), input_value(payload.get(key))])
    return rows


def _append_complete_input_table(story, title, rows):
    story.append(Paragraph(title, STYLES["H2"]))
    if not rows:
        story.append(Paragraph("No input records were provided.", STYLES["Body"]))
        return
    data = [[p("Item", "TableHeader"), p("Field", "TableHeader"), p("Submitted value", "TableHeader")]]
    for item, field, value in rows:
        data.append([p(item, "TableCellLeft"), p(field, "TableCellLeft"), p(value, "TableCellLeft")])
    story.append(std_table(data, [35 * mm, 50 * mm, 80 * mm]))


# ---------------------------------------------------------------------------
# Section builders
# ---------------------------------------------------------------------------

def _cover_and_summary(story, meta):
    story.append(Spacer(1, 10 * mm))
    bolt_row = Table(
        [[LightningBolt(20), Paragraph("Lightning Risk Assessment Report", STYLES["ReportTitle"])]],
        colWidths=[10 * mm, None],
    )
    bolt_row.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 0), (0, 0), "CENTER"),
    ]))
    story.append(bolt_row)
    story.append(Paragraph(
        "Compliant with IEC 62305-2:2024 — Protection against lightning &middot; Risk management",
        STYLES["ReportSubtitle"],
    ))
    story.append(HRFlowable(width="100%", thickness=1, color=BORDER, spaceAfter=14))

    rows = [
        ["Subject structure / assessed building", meta["structure_name"]],
        ["Case study / project name", meta["project_name"]],
        ["Assessment standard", "IEC 62305-2:2024"],
        ["Tool / solution used", "Web-Based Lightning Risk Assessment Tool (LRAT)"],
        ["Tolerable risk RT", meta["rt_text"]],
        ["Tolerable frequency FT", meta["ft_text"]],
        ["Report date", meta["report_date"]],
    ]
    table_data = [[Paragraph(k, STYLES["SummaryLabel"]), Paragraph(v, STYLES["SummaryValue"])] for k, v in rows]
    summary_table = Table(table_data, colWidths=[70 * mm, 95 * mm])
    summary_table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
        ("BACKGROUND", (0, 0), (0, -1), SLATE_LIGHT),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 8 * mm))

    status_row = Table(
        [[Paragraph("Overall status", STYLES["SummaryLabel"]), status_badge(meta["overall_status_text"], meta["overall_status_kind"])]],
        colWidths=[70 * mm, 95 * mm],
    )
    status_row.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE")]))
    story.append(status_row)
    story.append(PageBreak())


def _toc(story):
    story.append(section_heading("", "Table of Contents"))
    story.append(Spacer(1, 6))
    items = [
        "1&nbsp;&nbsp;&nbsp;Executive Summary",
        "2&nbsp;&nbsp;&nbsp;Assessment Methodology",
        "3&nbsp;&nbsp;&nbsp;Input Data",
        "&nbsp;&nbsp;&nbsp;&nbsp;3.1&nbsp;&nbsp;Structure and Environment",
        "&nbsp;&nbsp;&nbsp;&nbsp;3.2&nbsp;&nbsp;Incoming Lines",
        "&nbsp;&nbsp;&nbsp;&nbsp;3.3&nbsp;&nbsp;Risk Zones",
        "4&nbsp;&nbsp;&nbsp;Collection Areas and Expected Dangerous Events",
        "5&nbsp;&nbsp;&nbsp;Risk Assessment Results",
        "6&nbsp;&nbsp;&nbsp;Frequency of Damage Results",
        "7&nbsp;&nbsp;&nbsp;Recommended Protection and Verified Result",
        "8&nbsp;&nbsp;&nbsp;Validation Against IEC Annex F",
        "9&nbsp;&nbsp;&nbsp;Recommendations and Observations",
        "10&nbsp;&nbsp;Final Statement",
    ]
    for item in items:
        story.append(Paragraph(item, STYLES["TocItem"]))
    story.append(PageBreak())


def _executive_summary(story, ctx):
    story.append(section_heading("1", "Executive Summary"))
    story.append(Spacer(1, 8))

    protected = ctx["protection_applied"]
    zone_word = "zone" if len(ctx["failed_risk_zones"]) == 1 else "zones"

    summary_text = (
        f"This report presents the lightning risk assessment of {ctx['structure_name']}, "
        f"carried out in accordance with IEC 62305-2:2024. The assessment evaluates the "
        f"probability and consequence of lightning-related damage across {ctx['zone_count']} "
        f"defined risk zone(s), and compares the calculated risk R and, where internal systems "
        f"are present, the frequency of damage F, against their respective tolerable limits "
        f"RT and FT."
    )
    story.append(Paragraph(summary_text, STYLES["Body"]))

    if ctx["failed_risk_zones"] or ctx["failed_freq_zones"]:
        unprotected_text = (
            f"In the unprotected condition, {len(ctx['failed_risk_zones'])} {zone_word} "
            f"exceeded the tolerable risk limit"
            + (f" ({', '.join(ctx['failed_risk_zones'])})" if ctx["failed_risk_zones"] else "")
            + ". "
        )
        if ctx["failed_freq_zones"]:
            unprotected_text += (
                f"Frequency of damage exceeded the tolerable limit in "
                f"{len(ctx['failed_freq_zones'])} zone(s) "
                f"({', '.join(ctx['failed_freq_zones'])})."
            )
        story.append(Paragraph(unprotected_text, STYLES["Body"]))
    else:
        story.append(Paragraph(
            "In the assessed condition, all zones fall within the tolerable risk and "
            "frequency limits and no protection measures are strictly required.",
            STYLES["Body"],
        ))

    if protected:
        story.append(Paragraph(
            "Protection measures were applied in the website session and the assessment was "
            "rerun. The results after protection are presented in Section 7 "
            "and reflect the verified, recalculated condition of the structure.",
            STYLES["Body"],
        ))
    elif ctx["has_comparison"]:
        story.append(Paragraph(
            "Protection recommendations were generated, but no protection has been applied "
            "in the website session. Section 7 therefore records the protected condition as "
            "'Protection not applied'.",
            STYLES["Body"],
        ))

    story.append(Paragraph("Key Findings", STYLES["H2"]))
    findings = []
    findings.append(
        "Unprotected condition — " + (
            "protection required." if ctx["failed_risk_zones"] or ctx["failed_freq_zones"]
            else "all zones within tolerable limits."
        )
    )
    if ctx["dominant_components_text"]:
        findings.append(f"Dominant contributors — {ctx['dominant_components_text']}.")
    if ctx["recommended_measures_text"]:
        findings.append(f"Recommended protection — {ctx['recommended_measures_text']}.")
    findings.append(
        "Verified result — " + (
            "after applying the recommended protection, the recalculated risk and frequency "
            "values fall within the tolerable limits." if protected and ctx["final_all_pass"]
            else "protection has been applied; some zones may still require further engineering review."
            if protected
            else "no protection has been applied in this report; values shown are for the unprotected condition."
        )
    )
    for i, f in enumerate(findings, start=1):
        story.append(Paragraph(f"{i}. {f}", STYLES["KeyFinding"]))

    story.append(PageBreak())


def _methodology(story):
    story.append(section_heading("2", "Assessment Methodology"))
    story.append(Spacer(1, 8))
    story.append(Paragraph(
        "This report follows the IEC 62305-2:2024 risk management methodology. Each risk "
        "component is calculated as the product of three factors:",
        STYLES["Body"],
    ))
    story.append(Paragraph("R = N &times; P &times; L", ParagraphStyle(
        "Formula", parent=STYLES["Body"], fontName="Helvetica-Bold", fontSize=12,
        alignment=TA_CENTER, spaceBefore=4, spaceAfter=8,
    )))
    story.append(Paragraph(
        "where N is the annual number of dangerous events, P is the probability of damage, "
        "and L is the resulting loss factor for the relevant type of loss.",
        STYLES["Body"],
    ))
    story.append(Paragraph(
        "Frequency of damage to internal systems, where applicable, is calculated separately:",
        STYLES["Body"],
    ))
    story.append(Paragraph("F = FC + FM + FW + FZ", ParagraphStyle(
        "Formula2", parent=STYLES["Body"], fontName="Helvetica-Bold", fontSize=12,
        alignment=TA_CENTER, spaceBefore=4, spaceAfter=8,
    )))
    story.append(Paragraph(
        "Both R and F are evaluated against four sources of lightning damage defined by the "
        "standard:",
        STYLES["Body"],
    ))
    sources = [
        "S1 — flashes to the structure",
        "S2 — flashes near the structure",
        "S3 — flashes to a connected line",
        "S4 — flashes near a connected line",
    ]
    for s in sources:
        story.append(Paragraph(f"• {s}", STYLES["KeyFinding"]))

    story.append(Paragraph("Tool Workflow", STYLES["H2"]))
    steps = [
        "User enters building information.",
        "User configures incoming service lines.",
        "User defines risk zones.",
        "Backend converts inputs into IEC parameters (Annexes A, B, C, E).",
        "Risk and frequency engines calculate results for each zone.",
        "Recommendation engine simulates candidate protection measures.",
        "PDF report is generated.",
    ]
    for i, s in enumerate(steps, start=1):
        story.append(Paragraph(f"{i}. {s}", STYLES["KeyFinding"]))
    story.append(PageBreak())


def nice_text(value):
    if value is None or value == "":
        return "not specified"
    if isinstance(value, bool):
        return "yes" if value else "no"
    return str(value).replace("_", " ").replace("-", " ").strip()


def title_text(value):
    return nice_text(value).title()


def _line_summary_sentence(line):
    service = title_text(line.get("service") or "service")
    name = line.get("name") or "unnamed"
    cable = "metal-free fibre optic" if line.get("external_cable") == "fibre_optic" else title_text(line.get("external_cable") or "metallic")
    uw = f"{fnum(line.get('Uw'), 2)} kV" if line.get("Uw") is not None else "not specified"
    bonding = title_text(line.get("equipotential_bonding_level") or "none")

    if line.get("has_line_sections"):
        sections = line.get("sections") or []
        total_length = sum((s.get("LL") or 0) for s in sections)
        section_text = f"{len(sections)} section(s)"
        if total_length:
            section_text += f", total length approximately {fnum(total_length, 0)} m"
        return (
            f"{service} line '{name}' uses a {cable} external cable and is modelled using "
            f"{section_text}. Equipment withstand voltage Uw is {uw}. Equipotential bonding "
            f"SPD level is {bonding}."
        )

    length = "IEC assumed 1000 m" if line.get("length_known") is False else (
        f"{fnum(line.get('LL'), 0)} m" if line.get("LL") is not None else "not specified"
    )
    return (
        f"{service} line '{name}' uses a {cable} external cable, {title_text(line.get('installation'))} "
        f"installation, {title_text(line.get('type'))} line type, {title_text(line.get('environmental'))} "
        f"environment, and length {length}. Equipment withstand voltage Uw is {uw}. "
        f"Equipotential bonding SPD level is {bonding}."
    )


def _line_sections_table(story, line):
    sections = line.get("sections") or []
    if not line.get("has_line_sections") or not sections:
        return
    data = [[
        p("Section", "TableHeader"), p("Length", "TableHeader"),
        p("Installation", "TableHeader"), p("Line type", "TableHeader"),
        p("Environment", "TableHeader"), p("Shield", "TableHeader"),
    ]]
    for i, sec in enumerate(sections, start=1):
        data.append([
            p(sec.get("name") or f"Section {i}", "TableCellLeft"),
            p(f"{fnum(sec.get('LL'), 0)} m" if sec.get("LL") is not None else "not specified"),
            p(title_text(sec.get("installation"))),
            p(title_text(sec.get("type"))),
            p(title_text(sec.get("environmental"))),
            p(title_text(sec.get("shield_resistance") or "unshielded")),
        ])
    story.append(std_table(data, [25 * mm, 22 * mm, 28 * mm, 38 * mm, 25 * mm, 27 * mm]))
    story.append(table_caption(f"Line sections for {line.get('name') or 'incoming line'}.")) 


def _input_data(story, building_data, lines_data, zones_data):
    story.append(section_heading("3", "Input Data"))
    story.append(Spacer(1, 8))
    story.append(Paragraph("3.1&nbsp;&nbsp;Structure and Environment", STYLES["H2"]))

    density_method = building_data.get("density_method", "NSG")
    density_val = building_data.get("NSG") if density_method == "NSG" else (
        building_data.get("NG") if density_method == "NG" else building_data.get("NT")
    )
    rows = [
        ["Parameter", "Value", "Basis / IEC reference"],
        ["Lightning ground strike-point density NSG", fnum(density_val, 2) + " /km2/yr", "Annex A.1"],
        ["Building dimensions L x W x H", f"{fnum(building_data.get('L'),1)} x {fnum(building_data.get('W'),1)} x {fnum(building_data.get('H'),1)} m", "Annex A.2.1"],
        ["Structure shape", str(building_data.get("structure_shape", "—")).title(), "Annex A.2.1"],
        ["Relative location factor CD", str(building_data.get("location_type", "—")).replace("_", " ").title(), "Table A.1"],
        ["Wall material", str(building_data.get("wall_material", "—")).replace("_", " ").title(), "Table B.4 / B.5"],
        ["Roof material", str(building_data.get("roof_material", "—")).replace("_", " ").title(), "Table B.4 / B.5"],
        ["LPS class installed", str(building_data.get("LPS_class") or "None"), "IEC 62305-3"],
        ["Thunderstorm warning system (TWS)", "Yes" if building_data.get("TWS") else "No", "Table B.2"],
        ["Structure electromagnetic shielding (KS1)", "Yes" if building_data.get("structure_shielding") else "No", "Annex B"],
    ]
    data = [[p(rows[0][0], "TableHeader"), p(rows[0][1], "TableHeader"), p(rows[0][2], "TableHeader")]]
    for r in rows[1:]:
        data.append([p(r[0], "TableCellLeft"), p(r[1]), p(r[2], "TableCellLeft")])
    story.append(std_table(data, [75 * mm, 45 * mm, 45 * mm]))
    story.append(table_caption("Table 1 — Structure and environment parameters."))

    story.append(Paragraph("3.2&nbsp;&nbsp;Incoming Lines", STYLES["H2"]))
    if not lines_data:
        story.append(Paragraph("No incoming service lines were defined for this assessment.", STYLES["Body"]))
    for line in lines_data:
        service = str(line.get("service", "—")).title()
        story.append(Paragraph(f"{service} line — {line.get('name') or 'unnamed'}", ParagraphStyle(
            "LineHead", parent=STYLES["Body"], fontName="Helvetica-Bold", fontSize=9.5, spaceBefore=6,
        )))
        is_fibre = line.get("external_cable") == "fibre_optic"
        lrows = [
            ["Installation type", str(line.get("installation") or "—").replace("_", " ").title()],
            ["Line type / environment", f"{str(line.get('type') or '—').replace('_',' ').title()} / {str(line.get('environmental') or '—').title()}"],
            ["Line length", f"{fnum(line.get('LL'),0)} m" if line.get("LL") else "Per section"],
            ["Withstand voltage Uw", f"{fnum(line.get('Uw'),2)} kV"],
            ["External cable condition", "Fibre optic (metal-free)" if is_fibre else str(line.get("external_cable") or "—").title()],
            ["Equipotential bonding SPD", str(line.get("equipotential_bonding_level") or "none").title()],
        ]
        ldata = [[p(k, "TableCellLeft"), p(v, "TableCellLeft")] for k, v in lrows]
        t = Table(ldata, colWidths=[55 * mm, 110 * mm])
        t.setStyle(TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.4, BORDER),
            ("BACKGROUND", (0, 0), (0, -1), SLATE_LIGHT),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ]))
        story.append(Paragraph(_line_summary_sentence(line), STYLES["Body"]))
        story.append(t)
        _line_sections_table(story, line)
        if is_fibre:
            story.append(Paragraph(
                "A metal-free fibre optic external line does not contribute to line-borne surge "
                "propagation. Internal copper wiring downstream of the fibre termination may "
                "still be considered at zone level where applicable.",
                STYLES["Caption"],
            ))
        story.append(Spacer(1, 4))

    story.append(Paragraph("3.3&nbsp;&nbsp;Risk Zones", STYLES["H2"]))
    zrows = [["Zone", "Use / function", "Occupancy", "Fire risk", "Fire protection", "Internal systems", "Loss category"]]
    for z in zones_data:
        fire_prot = z.get("fire_protection") or []
        internal = []
        if z.get("has_power_internal_system"):
            internal.append("Power")
        if z.get("has_telecom_internal_system"):
            internal.append("Telecom")
        zrows.append([
            z.get("name", "—"),
            "—",
            "Present" if z.get("people_present") else "Absent",
            str(z.get("fire_risk") or "—").title(),
            ", ".join(x.replace("_", " ").title() for x in fire_prot) if fire_prot else "None",
            ", ".join(internal) if internal else "None",
            str(z.get("loss_category") or "—").title(),
        ])
    zdata = [[p(c, "TableHeader") for c in zrows[0]]]
    for r in zrows[1:]:
        zdata.append([p(r[0], "TableCellLeft")] + [p(c) for c in r[1:]])
    story.append(std_table(zdata, [22 * mm, 20 * mm, 18 * mm, 18 * mm, 30 * mm, 25 * mm, 22 * mm]))
    story.append(table_caption("Table 2 — Risk zone summary."))
    story.append(PageBreak())


def _collection_areas(story, building_data, lines_data, zones_data):
    story.append(section_heading("4", "Collection Areas and Expected Dangerous Events"))
    story.append(Spacer(1, 8))
    story.append(Paragraph(
        "The following quantities are computed per IEC 62305-2:2024 Annex A, from the same "
        "structure and line inputs used in the risk and frequency assessment.",
        STYLES["Body"],
    ))

    try:
        building = build_building_from_session(building_data, lines_data, zones_data)
        AD = NModule.AD(building)
        ND = NModule.ND(building)
        AM = NModule.AM(building)
        NM = NModule.NM(building)
        NModule.NL(building)
        NModule.NI(building)
        NModule.NDJ(building)
        computed_ok = True
    except Exception:
        AD = ND = AM = NM = None
        building = None
        computed_ok = False

    arows = [["Quantity", "Tool output", "Description"]]
    arows.append(["AD", (fnum(AD, 1) + " m2") if AD is not None else "—", "Collection area — flashes to the structure"])
    arows.append(["AM", (fnum(AM, 1) + " m2") if AM is not None else "—", "Collection area — flashes near the structure"])
    adata = [[p(c, "TableHeader") for c in arows[0]]]
    for r in arows[1:]:
        adata.append([p(r[0], "TableCellLeft")] + [p(c) for c in r[1:]])
    story.append(std_table(adata, [55 * mm, 40 * mm, 70 * mm]))
    story.append(table_caption("Table 3 — Collection areas."))

    nrows = [["Quantity", "Tool output", "Description"]]
    nrows.append(["ND", sci(ND) if ND is not None else "—", "Dangerous events — flashes to the structure"])
    nrows.append(["NM", sci(NM) if NM is not None else "—", "Dangerous events — flashes near the structure"])
    if computed_ok:
        for line in building.lines:
            label = getattr(line, "name", "") or str(getattr(line, "service", "line")).title()
            nl_val = getattr(line, "NL", None)
            ni_val = getattr(line, "NI", None)
            nrows.append([f"NL ({label})", sci(nl_val) if nl_val is not None else "—", "Dangerous events — flashes to the line"])
            nrows.append([f"NI ({label})", sci(ni_val) if ni_val is not None else "—", "Dangerous events — flashes near the line"])
            ndj_val = getattr(line, "NDJ", 0)
            if ndj_val:
                nrows.append([f"NDJ ({label})", sci(ndj_val), "Dangerous events — flashes to adjacent structure"])
    ndata = [[p(c, "TableHeader") for c in nrows[0]]]
    for r in nrows[1:]:
        ndata.append([p(r[0], "TableCellLeft"), Paragraph(r[1], STYLES["TableCell"]), p(r[2], "TableCellLeft")])
    story.append(std_table(ndata, [55 * mm, 40 * mm, 70 * mm]))
    story.append(table_caption("Table 4 — Expected annual number of dangerous events."))
    story.append(PageBreak())


def _risk_results(story, risk_results):
    story.append(section_heading("5", "Risk Assessment Results"))
    story.append(Spacer(1, 8))

    cols = ["Zone", "RAT", "RAD", "RB", "RC", "RM", "RU", "RV", "RW", "RZ", "Total R", "RT", "Status"]
    header = [p(c, "TableHeader") for c in cols]
    data = [header]
    zone_names = [z for z in risk_results.keys() if z != "Building_Total"]
    worst = None
    for zn in zone_names:
        v = risk_results[zn]
        rb = (v.get("RB1", 0) or 0) + (v.get("RB2", 0) or 0)
        rc = (v.get("RC1", 0) or 0) + (v.get("RC2", 0) or 0)
        rm = (v.get("RM1", 0) or 0) + (v.get("RM2", 0) or 0)
        rv = (v.get("RV1", 0) or 0) + (v.get("RV2", 0) or 0)
        rw = (v.get("RW1", 0) or 0) + (v.get("RW2", 0) or 0)
        rz = (v.get("RZ1", 0) or 0) + (v.get("RZ2", 0) or 0)
        row = [
            p(zn, "TableCellLeft"),
            Paragraph(sci(v.get("RAT")), STYLES["TableCell"]),
            Paragraph(sci(v.get("RAD")), STYLES["TableCell"]),
            Paragraph(sci(rb), STYLES["TableCell"]),
            Paragraph(sci(rc), STYLES["TableCell"]),
            Paragraph(sci(rm), STYLES["TableCell"]),
            Paragraph(sci(v.get("RU")), STYLES["TableCell"]),
            Paragraph(sci(rv), STYLES["TableCell"]),
            Paragraph(sci(rw), STYLES["TableCell"]),
            Paragraph(sci(rz), STYLES["TableCell"]),
            Paragraph(sci(v.get("R_total")), STYLES["TableCell"]),
            Paragraph(sci(v.get("RT")), STYLES["TableCell"]),
            status_cell(v.get("risk_status")),
        ]
        data.append(row)
        rt = v.get("RT") or 1e-5
        ratio = (v.get("R_total") or 0) / rt if rt else 0
        if worst is None or ratio > worst[1]:
            worst = (zn, ratio, v)

    widths = [20 * mm] + [11 * mm] * 9 + [16 * mm, 14 * mm, 22 * mm]
    story.append(std_table(data, widths))
    story.append(table_caption("Table 5 — Risk components by zone (R = N x P x L)."))

    failing = [zn for zn in zone_names if risk_results[zn].get("risk_status") == "Protection required"]
    if failing:
        wz, _, wv = worst
        comps = {
            "RAT": wv.get("RAT", 0) or 0, "RAD": wv.get("RAD", 0) or 0,
            "RB": (wv.get("RB1", 0) or 0) + (wv.get("RB2", 0) or 0),
            "RC": (wv.get("RC1", 0) or 0) + (wv.get("RC2", 0) or 0),
            "RM": (wv.get("RM1", 0) or 0) + (wv.get("RM2", 0) or 0),
            "RU": wv.get("RU", 0) or 0,
            "RV": (wv.get("RV1", 0) or 0) + (wv.get("RV2", 0) or 0),
            "RW": (wv.get("RW1", 0) or 0) + (wv.get("RW2", 0) or 0),
            "RZ": (wv.get("RZ1", 0) or 0) + (wv.get("RZ2", 0) or 0),
        }
        dom = max(comps, key=comps.get) if any(comps.values()) else "—"
        interpretation = (
            f"The results show that {', '.join(failing)} exceed{'s' if len(failing)==1 else ''} "
            f"the tolerable risk limit. The most critical zone is {wz}, where the dominant "
            f"contributor is {dom}. Protection measures are required to reduce the total risk "
            f"below the tolerable limit RT."
        )
    else:
        interpretation = (
            "All assessed zones fall within the tolerable risk limit RT in the evaluated "
            "condition. No mandatory protection measures are indicated by the risk assessment."
        )
    story.append(Paragraph(interpretation, STYLES["Body"]))
    story.append(PageBreak())


def _frequency_results(story, frequency_results):
    story.append(section_heading("6", "Frequency of Damage Results"))
    story.append(Spacer(1, 8))

    applicable = {zn: v for zn, v in frequency_results.items() if zn != "Building_Total" and v.get("frequency_status") != "Not applicable"}
    if not applicable:
        story.append(Paragraph(
            "No zones in this assessment have internal systems requiring a frequency-of-damage "
            "evaluation.", STYLES["Body"],
        ))
        story.append(PageBreak())
        return

    cols = ["Zone", "FC", "FM", "FW", "FZ", "Total F", "FT", "Status"]
    data = [[p(c, "TableHeader") for c in cols]]
    failing = []
    for zn, v in applicable.items():
        fw = (v.get("FWP", 0) or 0) + (v.get("FWT", 0) or 0)
        fz = (v.get("FZP", 0) or 0) + (v.get("FZT", 0) or 0)
        row = [
            p(zn, "TableCellLeft"),
            Paragraph(sci(v.get("FC")), STYLES["TableCell"]),
            Paragraph(sci(v.get("FM")), STYLES["TableCell"]),
            Paragraph(sci(fw), STYLES["TableCell"]),
            Paragraph(sci(fz), STYLES["TableCell"]),
            Paragraph(sci(v.get("F_total")), STYLES["TableCell"]),
            Paragraph(sci(v.get("FT")), STYLES["TableCell"]),
            status_cell(v.get("frequency_status")),
        ]
        data.append(row)
        if v.get("frequency_status") == "Protection required":
            failing.append(zn)

    story.append(std_table(data, [24 * mm, 20 * mm, 20 * mm, 20 * mm, 20 * mm, 22 * mm, 20 * mm, 28 * mm]))
    story.append(table_caption("Table 6 — Frequency of damage to internal systems by zone."))

    if failing:
        interpretation = (
            f"Frequency of damage exceeds the tolerable limit FT in {', '.join(failing)}. "
            f"Internal systems in these zones require coordinated SPD protection to reduce the "
            f"frequency of dangerous overvoltages below the tolerable limit."
        )
    else:
        interpretation = (
            "Frequency of damage to internal systems is within the tolerable limit FT in all "
            "applicable zones."
        )
    story.append(Paragraph(interpretation, STYLES["Body"]))
    story.append(PageBreak())


def _protection_and_verification(story, ctx):
    story.append(section_heading("7", "Recommended Protection and Verified Result"))
    story.append(Spacer(1, 8))
    story.append(Paragraph(
        "The recommendation engine identifies the dominant risk and frequency components, maps "
        "them to adjustable protection factors (PLPS, PSPD, Pam, PEB, rP), simulates candidate "
        "protection measures against the full risk and frequency engines, and recalculates the "
        "assessment to verify whether the proposed measure is sufficient.",
        STYLES["Body"],
    ))

    if ctx["recommended_steps"]:
        story.append(Paragraph("Recommended protection measures:", STYLES["Body"]))
        for i, step in enumerate(ctx["recommended_steps"], start=1):
            story.append(Paragraph(f"{i}. {step}", STYLES["KeyFinding"]))
    else:
        story.append(Paragraph(
            "No protection measures were required for the assessed condition.", STYLES["Body"],
        ))

    if ctx["has_comparison"]:
        story.append(Paragraph("Risk Comparison (Unprotected / Protected)", STYLES["H2"]))
        cols = ["Zone", "Unprotected R", "Recommended / applied measure", "Protected R", "RT", "Status"]
        data = [[p(c, "TableHeader") for c in cols]]
        for row in ctx["risk_before_after"]:
            data.append([
                p(row["zone"], "TableCellLeft"),
                Paragraph(sci(row["old"]), STYLES["TableCell"]),
                p(row["measure"], "TableCellLeft"),
                p(row.get("new_text") or sci(row["new"])),
                Paragraph(sci(row["limit"]), STYLES["TableCell"]),
                comparison_status_cell(row["status"]),
            ])
        story.append(std_table(data, [22 * mm, 22 * mm, 55 * mm, 22 * mm, 20 * mm, 28 * mm]))
        story.append(table_caption("Table 7 — Risk before and after recommended protection."))

        if ctx["freq_before_after"]:
            story.append(Paragraph("Frequency Comparison (Unprotected / Protected)", STYLES["H2"]))
            cols = ["Zone", "Unprotected F", "Recommended / applied measure", "Protected F", "FT", "Status"]
            data = [[p(c, "TableHeader") for c in cols]]
            for row in ctx["freq_before_after"]:
                data.append([
                    p(row["zone"], "TableCellLeft"),
                    Paragraph(sci(row["old"]), STYLES["TableCell"]),
                    p(row["measure"], "TableCellLeft"),
                    p(row.get("new_text") or sci(row["new"])),
                    Paragraph(sci(row["limit"]), STYLES["TableCell"]),
                    comparison_status_cell(row["status"]),
                ])
            story.append(std_table(data, [22 * mm, 22 * mm, 55 * mm, 22 * mm, 20 * mm, 28 * mm]))
            story.append(table_caption("Table 8 — Frequency before and after recommended protection."))

        if not ctx["protection_applied"]:
            story.append(Paragraph(
                "Protection recommendations have been generated, but no protection action has "
                "been applied in the website session. Therefore, the protected-value column is "
                "reported as 'Protection not applied'.",
                STYLES["Body"],
            ))
        elif ctx["final_all_pass"]:
            story.append(Paragraph(
                "After the applied protection is recalculated, all applicable zones fall below "
                "the tolerable risk and frequency limits. Therefore, the protected condition is "
                "considered acceptable according to IEC 62305-2:2024.",
                STYLES["Body"],
            ))
        else:
            story.append(Paragraph(
                "Protection has been applied and recalculated, but at least one zone still "
                "exceeds the tolerable limit. This indicates that the applied recommendation is "
                "not sufficient yet, or that only part of the recommended protection plan has "
                "been applied. Further measures are required before the protected condition can "
                "be accepted.",
                STYLES["Body"],
            ))
    else:
        story.append(Paragraph(
            "The unprotected condition already satisfies IEC 62305-2:2024: all applicable "
            "zones fall within the tolerable risk and frequency limits, so no comparison "
            "against a protected condition is required.",
            STYLES["Body"],
        ))
    story.append(PageBreak())


def _annex_f_validation(story, ctx):
    story.append(section_heading("8", "Validation Against IEC Annex F"))
    story.append(Spacer(1, 8))
    if not ctx.get("annex_f_reference"):
        story.append(Paragraph(
            "This assessment was not configured against a specific IEC 62305-2:2024 Annex F "
            "reference case study. This section is provided for completeness and would be "
            "populated when the input configuration corresponds to a documented Annex F "
            "worked example.",
            STYLES["Body"],
        ))
        story.append(PageBreak())
        return
    cols = ["Quantity group", "Items checked", "Agreement"]
    data = [[p(c, "TableHeader") for c in cols]]
    for row in ctx["annex_f_reference"]:
        data.append([p(row["group"], "TableCellLeft"), p(row["items"], "TableCellLeft"), p(row["agreement"])])
    story.append(std_table(data, [45 * mm, 75 * mm, 30 * mm]))
    story.append(table_caption("Table 9 — Validation against IEC Annex F reference case."))
    story.append(Paragraph(
        "The validation was performed at component level rather than only at total-risk "
        "level. This is important because matching only the final value may hide errors in "
        "individual component calculations.",
        STYLES["Body"],
    ))
    story.append(PageBreak())


def _recommendations_observations(story):
    story.append(section_heading("9", "Recommendations and Observations"))
    story.append(Spacer(1, 8))
    story.append(Paragraph("Engineering recommendations:", STYLES["Body"]))
    recs = [
        "Install the recommended protection measures before final approval.",
        "Prioritise zones with the highest calculated risk contribution.",
        "Reassess the structure if occupancy, building use, fire load, line configuration, "
        "or lightning density changes.",
        "Ensure SPD and fire protection systems are properly installed and maintained.",
        "Treat this result as engineering decision support, not a replacement for "
        "professional judgement.",
    ]
    for r in recs:
        story.append(Paragraph(f"• {r}", STYLES["KeyFinding"]))

    story.append(Paragraph("Modelling observations:", STYLES["H2"]))
    obs = [
        "Fibre optic and metallic lines must be selected carefully, as this affects the "
        "line collection area and dangerous event calculation.",
        "Internal copper wiring downstream of a fibre optic termination may still affect "
        "internal system risk.",
        "Loss category selection strongly affects the resulting risk value.",
        "Simplified PSPD values from IEC 62305-2:2024 Annex B Table B.7 are used unless a "
        "full Annex D evaluation is implemented.",
    ]
    for o in obs:
        story.append(Paragraph(f"• {o}", STYLES["KeyFinding"]))
    story.append(PageBreak())


def _final_statement(story):
    story.append(section_heading("10", "Final Statement"))
    story.append(Spacer(1, 10))
    story.append(Paragraph(
        "This report was generated using the Web-Based Lightning Risk Assessment Tool for "
        "Building Protection. The calculation procedure follows IEC 62305-2:2024 risk "
        "management methodology. The results are intended to support engineering assessment "
        "and should be reviewed by a competent lightning protection engineer before final "
        "implementation.",
        STYLES["Body"],
    ))
    story.append(Spacer(1, 6))
    story.append(Paragraph(
        "The tool performs IEC 62305-2:2024 risk management assessment. It does not perform "
        "full Annex D SPD evaluation, physical LPS design, earthing design, or electromagnetic "
        "transient simulation, unless explicitly stated otherwise for a given case.",
        STYLES["Caption"],
    ))


# ---------------------------------------------------------------------------
# Context assembly
# ---------------------------------------------------------------------------

def _collect_recommended_steps_text(protection_plan, protection_recommendations, frequency_recommendations):
    steps = []
    if protection_plan and protection_plan.get("recommended_steps"):
        for s in protection_plan["recommended_steps"]:
            steps.append(s.get("display", ""))
        return steps
    # Fallback to per-zone recommendation actions if no whole-building plan exists.
    seen = set()
    for zone_recs in (protection_recommendations or {}).values():
        for rec in zone_recs:
            for action in rec.get("actions", []):
                d = action.get("display")
                if d and d not in seen:
                    seen.add(d)
                    steps.append(d)
    for zone_recs in (frequency_recommendations or {}).values():
        for rec in zone_recs:
            for action in rec.get("actions", []):
                d = action.get("display")
                if d and d not in seen:
                    seen.add(d)
                    steps.append(d)
    return steps


def _dominant_components_text(risk_results):
    comps_count = {}
    for zn, v in risk_results.items():
        if zn == "Building_Total" or v.get("risk_status") != "Protection required":
            continue
        comps = {
            "RAT": v.get("RAT", 0) or 0, "RAD": v.get("RAD", 0) or 0,
            "RB": (v.get("RB1", 0) or 0) + (v.get("RB2", 0) or 0),
            "RC": (v.get("RC1", 0) or 0) + (v.get("RC2", 0) or 0),
            "RM": (v.get("RM1", 0) or 0) + (v.get("RM2", 0) or 0),
            "RU": v.get("RU", 0) or 0,
            "RV": (v.get("RV1", 0) or 0) + (v.get("RV2", 0) or 0),
            "RW": (v.get("RW1", 0) or 0) + (v.get("RW2", 0) or 0),
            "RZ": (v.get("RZ1", 0) or 0) + (v.get("RZ2", 0) or 0),
        }
        total = v.get("R_total") or 0
        if total <= 0:
            continue
        for k, val in comps.items():
            if val / total >= 0.2:
                comps_count[k] = comps_count.get(k, 0) + 1
    if not comps_count:
        return ""
    top = sorted(comps_count, key=comps_count.get, reverse=True)[:3]
    return ", ".join(top)


def _build_before_after(risk_results_before, risk_results_after, plan_steps):
    rows = []
    for zn, before in risk_results_before.items():
        if zn == "Building_Total":
            continue
        after = risk_results_after.get(zn, {})
        measure = "—"
        for step in plan_steps or []:
            affected = step.get("affected_zones") or step.get("target_zones") or []
            if zn in affected:
                measure = step.get("display", "—")
                break
        rows.append({
            "zone": zn,
            "old": before.get("R_total"),
            "new": after.get("R_total", before.get("R_total")),
            "limit": before.get("RT"),
            "measure": measure,
            "status": after.get("risk_status", before.get("risk_status")),
        })
    return rows


def _build_freq_before_after(freq_before, freq_after, plan_steps):
    rows = []
    for zn, before in freq_before.items():
        if zn == "Building_Total" or before.get("frequency_status") == "Not applicable":
            continue
        after = freq_after.get(zn, {})
        measure = "—"
        for step in plan_steps or []:
            affected = step.get("affected_zones") or step.get("target_zones") or []
            if zn in affected:
                measure = step.get("display", "—")
                break
        rows.append({
            "zone": zn,
            "old": before.get("F_total"),
            "new": after.get("F_total", before.get("F_total")),
            "limit": before.get("FT"),
            "measure": measure,
            "status": after.get("frequency_status", before.get("frequency_status")),
        })
    return rows


# Corrected comparison helpers. They intentionally override the earlier helper
# definitions so reports reflect what the user actually applied in the app.
def _measure_for_zone(zone_name, plan_steps):
    for step in plan_steps or []:
        affected = step.get("affected_zones") or step.get("target_zones") or []
        if zone_name in affected:
            return step.get("display") or "Recommended protection measure"
    return "No zone-specific measure listed"


def _build_before_after(risk_results_before, risk_results_after, plan_steps, protection_applied=False):
    rows = []
    for zn, before in risk_results_before.items():
        if zn == "Building_Total":
            continue
        after = risk_results_after.get(zn, {})
        measure = _measure_for_zone(zn, plan_steps)
        if not protection_applied:
            rows.append({
                "zone": zn,
                "old": before.get("R_total"),
                "new": None,
                "new_text": "Protection not applied",
                "limit": before.get("RT"),
                "measure": measure,
                "status": "Protection not applied",
            })
            continue
        rows.append({
            "zone": zn,
            "old": before.get("R_total"),
            "new": after.get("R_total", before.get("R_total")),
            "new_text": None,
            "limit": before.get("RT"),
            "measure": measure,
            "status": after.get("risk_status", before.get("risk_status")),
        })
    return rows


def _build_freq_before_after(freq_before, freq_after, plan_steps, protection_applied=False):
    rows = []
    for zn, before in freq_before.items():
        if zn == "Building_Total" or before.get("frequency_status") == "Not applicable":
            continue
        after = freq_after.get(zn, {})
        measure = _measure_for_zone(zn, plan_steps)
        if not protection_applied:
            rows.append({
                "zone": zn,
                "old": before.get("F_total"),
                "new": None,
                "new_text": "Protection not applied",
                "limit": before.get("FT"),
                "measure": measure,
                "status": "Protection not applied",
            })
            continue
        rows.append({
            "zone": zn,
            "old": before.get("F_total"),
            "new": after.get("F_total", before.get("F_total")),
            "new_text": None,
            "limit": before.get("FT"),
            "measure": measure,
            "status": after.get("frequency_status", before.get("frequency_status")),
        })
    return rows


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def generate_pdf_report(
    output_path,
    building_data, lines_data, zones_data,
    risk_before, frequency_before, annex_e_before,
    risk_after, frequency_after, annex_e_after,
    protection_recommendations, frequency_recommendations,
    protection_plan=None,
    applied_protection_history=None,
):
    failed_risk_zones = [
        zn for zn, v in risk_before.items()
        if zn != "Building_Total" and v.get("risk_status") == "Protection required"
    ]
    failed_freq_zones = [
        zn for zn, v in frequency_before.items()
        if zn != "Building_Total" and v.get("frequency_status") == "Protection required"
    ]
    unprotected_ok = not failed_risk_zones and not failed_freq_zones
    protection_applied = bool(applied_protection_history)

    final_risk_failing = [
        zn for zn, v in risk_after.items()
        if zn != "Building_Total" and v.get("risk_status") == "Protection required"
    ]
    final_freq_failing = [
        zn for zn, v in frequency_after.items()
        if zn != "Building_Total" and v.get("frequency_status") == "Protection required"
    ]
    final_all_pass = not final_risk_failing and not final_freq_failing

    # If protection is required, the report should always show a before/protected
    # comparison. When the user has not clicked Apply, protected values are
    # explicitly marked as not applied.
    has_comparison = not unprotected_ok

    if unprotected_ok:
        overall_status_text, overall_kind = "PASS", "pass"
    elif not protection_applied:
        overall_status_text, overall_kind = "PROTECTION NOT APPLIED", "warn"
    elif has_comparison and final_all_pass:
        overall_status_text, overall_kind = "PASS AFTER PROTECTION", "pass"
    else:
        overall_status_text, overall_kind = "PROTECTION REQUIRED", "fail" if not has_comparison else "warn"

    plan_steps = (protection_plan or {}).get("recommended_steps", [])
    recommended_steps_text = _collect_recommended_steps_text(
        protection_plan, protection_recommendations, frequency_recommendations
    )

    rt_values = {v.get("RT") for zn, v in risk_before.items() if zn != "Building_Total" and v.get("RT")}
    ft_values = {v.get("FT") for zn, v in frequency_before.items() if zn != "Building_Total" and v.get("FT")}
    rt_text = sci(sorted(rt_values)[0]).replace("&times;", "x").replace("<super>", "^").replace("</super>", "") if rt_values else "1 x 10^-5"
    ft_text = sci(sorted(ft_values)[0]).replace("&times;", "x").replace("<super>", "^").replace("</super>", "") if ft_values else "5 x 10^-2"

    structure_name = building_data.get("name") or "Assessed structure"

    ctx = {
        "structure_name": structure_name,
        "zone_count": len(zones_data),
        "failed_risk_zones": failed_risk_zones,
        "failed_freq_zones": failed_freq_zones,
        "protection_applied": protection_applied,
        "applied_protection_history": applied_protection_history or [],
        "has_comparison": has_comparison,
        "final_all_pass": final_all_pass,
        "dominant_components_text": _dominant_components_text(risk_before),
        "recommended_measures_text": "; ".join(recommended_steps_text[:3]) if recommended_steps_text else "",
        "recommended_steps": recommended_steps_text,
        "risk_before_after": _build_before_after(risk_before, risk_after, plan_steps, protection_applied) if has_comparison else [],
        "freq_before_after": _build_freq_before_after(frequency_before, frequency_after, plan_steps, protection_applied) if has_comparison else [],
        "annex_f_reference": None,
    }

    meta = {
        "structure_name": structure_name,
        "project_name": building_data.get("project_name") or structure_name,
        "rt_text": rt_text,
        "ft_text": ft_text,
        "report_date": datetime.now().strftime("%d %B %Y"),
        "overall_status_text": overall_status_text,
        "overall_status_kind": overall_kind,
    }

    doc = SimpleDocTemplate(
        output_path, pagesize=A4,
        leftMargin=18 * mm, rightMargin=18 * mm,
        topMargin=16 * mm, bottomMargin=16 * mm,
        title="Lightning Risk Assessment Report",
    )

    story = []
    _cover_and_summary(story, meta)
    _toc(story)
    _executive_summary(story, ctx)
    _methodology(story)
    _input_data(story, building_data, lines_data, zones_data)
    _collection_areas(story, building_data, lines_data, zones_data)
    _risk_results(story, risk_before)
    _frequency_results(story, frequency_before)
    _protection_and_verification(story, ctx)
    _annex_f_validation(story, ctx)
    _recommendations_observations(story)
    _final_statement(story)

    doc.build(story)
    return output_path
