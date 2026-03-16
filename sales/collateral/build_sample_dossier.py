"""
Build Sample Dossier PDF — 2-page sales asset for LinkedIn DMs and cold emails.
Shows 3 redacted NC investor profiles with scoring, portfolio, and financing intel.
Contact fields redacted (████) to create the paywall effect.

Usage: python build_sample_dossier.py
Output: sales/collateral/sample_dossier.pdf
"""

import os
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether
)
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER

# Brand colors (matching pitchbook)
NAVY = HexColor("#1B2A4A")
DARK_BG = HexColor("#0F1B2D")
TEAL = HexColor("#2EC4B6")
ORANGE = HexColor("#FF6B35")
WHITE = HexColor("#FFFFFF")
LIGHT_GRAY = HexColor("#E8ECF1")
MED_GRAY = HexColor("#94A3B8")
DARK_TEXT = HexColor("#1E293B")
REDACT_BG = HexColor("#1E293B")

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_PATH = os.path.join(SCRIPT_DIR, "sample_dossier.pdf")


def build_styles():
    """Build all paragraph styles for the PDF."""
    return {
        "title": ParagraphStyle(
            "Title", fontName="Helvetica-Bold", fontSize=18,
            textColor=NAVY, spaceAfter=2, alignment=TA_CENTER,
            leading=20,
        ),
        "subtitle": ParagraphStyle(
            "Subtitle", fontName="Helvetica", fontSize=9,
            textColor=MED_GRAY, spaceAfter=2, alignment=TA_CENTER,
        ),
        "stats": ParagraphStyle(
            "Stats", fontName="Helvetica", fontSize=7.5,
            textColor=MED_GRAY, spaceAfter=4, alignment=TA_CENTER,
        ),
        "dossier_header": ParagraphStyle(
            "DossierHeader", fontName="Helvetica-Bold", fontSize=11,
            textColor=NAVY, spaceAfter=3, spaceBefore=4,
        ),
        "section_label": ParagraphStyle(
            "SectionLabel", fontName="Helvetica-Bold", fontSize=7.5,
            textColor=TEAL, spaceAfter=1, spaceBefore=4,
        ),
        "body": ParagraphStyle(
            "Body", fontName="Helvetica", fontSize=8,
            textColor=DARK_TEXT, leading=10, spaceAfter=1,
        ),
        "body_small": ParagraphStyle(
            "BodySmall", fontName="Helvetica", fontSize=7,
            textColor=DARK_TEXT, leading=9, spaceAfter=1,
        ),
        "why_text": ParagraphStyle(
            "WhyText", fontName="Helvetica-Oblique", fontSize=7,
            textColor=DARK_TEXT, leading=9, spaceAfter=3,
            leftIndent=8, rightIndent=8,
        ),
        "redacted": ParagraphStyle(
            "Redacted", fontName="Helvetica-Bold", fontSize=8,
            textColor=HexColor("#64748B"), spaceAfter=1,
        ),
        "footer": ParagraphStyle(
            "Footer", fontName="Helvetica", fontSize=6.5,
            textColor=MED_GRAY, alignment=TA_CENTER, spaceBefore=3,
        ),
        "cta_header": ParagraphStyle(
            "CTAHeader", fontName="Helvetica-Bold", fontSize=13,
            textColor=NAVY, spaceAfter=3, alignment=TA_CENTER,
        ),
        "cta_body": ParagraphStyle(
            "CTABody", fontName="Helvetica", fontSize=8.5,
            textColor=DARK_TEXT, leading=12, spaceAfter=3, alignment=TA_CENTER,
        ),
        "cta_price": ParagraphStyle(
            "CTAPrice", fontName="Helvetica-Bold", fontSize=16,
            textColor=ORANGE, spaceAfter=2, alignment=TA_CENTER,
        ),
        "process_body": ParagraphStyle(
            "ProcessBody", fontName="Helvetica", fontSize=7.5,
            textColor=DARK_TEXT, leading=10, spaceAfter=1,
        ),
    }


def hr():
    return HRFlowable(width="100%", thickness=0.5, color=LIGHT_GRAY, spaceAfter=3, spaceBefore=2)


def make_field_table(fields):
    """Create a compact field/value table for dossier metadata."""
    data = [[Paragraph(f"<b>{k}</b>", ParagraphStyle("K", fontName="Helvetica-Bold", fontSize=7, textColor=MED_GRAY)),
             Paragraph(v, ParagraphStyle("V", fontName="Helvetica", fontSize=7.5, textColor=DARK_TEXT))]
            for k, v in fields]
    t = Table(data, colWidths=[1.6 * inch, 4.8 * inch])
    t.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 1),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
        ("LEFTPADDING", (0, 0), (0, -1), 0),
        ("LEFTPADDING", (1, 0), (1, -1), 4),
    ]))
    return t


def make_contact_block(has_linkedin=False):
    """Redacted contact info block."""
    s = ParagraphStyle("R", fontName="Helvetica", fontSize=8.5, textColor=HexColor("#64748B"))
    rows = [
        ["Decision Maker", "\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588"],
        ["Phone (verified)", "\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588"],
        ["Email (verified)", "\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588"],
    ]
    if has_linkedin:
        rows.append(["LinkedIn", "\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588"])
    data = [[Paragraph(r[0], ParagraphStyle("CL", fontName="Helvetica", fontSize=7.5, textColor=MED_GRAY)),
             Paragraph(r[1], s)] for r in rows]
    t = Table(data, colWidths=[1.2 * inch, 3.0 * inch])
    t.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 1),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
        ("BACKGROUND", (1, 0), (1, -1), HexColor("#F1F5F9")),
        ("LEFTPADDING", (0, 0), (0, -1), 0),
    ]))
    return t


def build_dossier_1(s):
    """Portfolio Landlord dossier."""
    elements = []
    elements.append(Paragraph("DOSSIER #1 \u2014 Portfolio Landlord", s["dossier_header"]))
    elements.append(make_field_table([
        ("Investor Type", "Portfolio Landlord (5+ properties)"),
        ("ICP Score", '<font color="#FF6B35"><b>87 / 100 \u2014 TIER 1 (Hot)</b></font>'),
        ("Owner", "[Redacted], LLC"),
        ("Properties Owned", "12 investment properties (Wake County)"),
        ("Est. Portfolio Value", "$3.2M"),
        ("Entity Type", "LLC (registered 2020)"),
        ("Mailing Address", "Out-of-state (New York, NY)"),
        ("Key Signals", "Absentee out-of-state, LLC-owned, portfolio 5+, no homestead, multi-family"),
    ]))
    elements.append(Paragraph("PORTFOLIO SNAPSHOT", s["section_label"]))
    for line in [
        "\u2022 8 single-family rentals ($180K\u2013$340K each)",
        "\u2022 2 duplexes ($420K\u2013$510K each) \u2022 2 condos ($165K\u2013$195K each)",
        "\u2022 Most recent acquisition: Oct 2025 ($285,000) \u2022 Pace: ~3/year since 2020",
    ]:
        elements.append(Paragraph(line, s["body_small"]))
    elements.append(Paragraph("FINANCING INTELLIGENCE", s["section_label"]))
    for line in [
        "\u2022 Estimated equity: <b>$1.1M+</b> (34% ratio) \u2022 Cash-out potential (75% LTV): ~$280K",
        "\u2022 Refi signals: Rate reduction candidate (2022 vintage), equity harvest eligible",
        "\u2022 Estimated portfolio DSCR: <b>1.35</b>",
    ]:
        elements.append(Paragraph(line, s["body_small"]))
    elements.append(Paragraph(
        "Active acquirer with 12 properties, $1.1M+ in equity, and a clear scaling pattern. "
        "Out-of-state LLC structure = sophisticated investor comfortable with DSCR products. "
        "Cash-out refi potential opens immediate conversation.",
        s["why_text"]
    ))
    elements.append(make_contact_block(has_linkedin=True))
    elements.append(Paragraph("<i>Contact data included with subscription</i>", s["footer"]))
    return elements


def build_dossier_2(s):
    """Growing Investor dossier."""
    elements = []
    elements.append(Paragraph("DOSSIER #2 \u2014 Growing Investor", s["dossier_header"]))
    elements.append(make_field_table([
        ("Investor Type", "Growing Portfolio (2\u20134 properties)"),
        ("ICP Score", '<font color="#FF6B35"><b>62 / 100 \u2014 TIER 1 (Hot)</b></font>'),
        ("Owner", "[Redacted] (Individual)"),
        ("Properties Owned", "3 investment properties (Wake County)"),
        ("Est. Portfolio Value", "$890K"),
        ("Entity Type", "Individual (no entity structure yet)"),
        ("Mailing Address", "Different city, same state (Charlotte, NC)"),
        ("Key Signals", "Absentee in-state, growing portfolio, recent purchase (2025), no homestead"),
    ]))
    elements.append(Paragraph("PORTFOLIO SNAPSHOT", s["section_label"]))
    for line in [
        "\u2022 3 single-family homes ($260K\u2013$340K each) \u2022 First acquisition: 2022",
        "\u2022 Most recent: March 2025 ($315,000) \u2022 All in 27603/27610 (South Raleigh)",
    ]:
        elements.append(Paragraph(line, s["body_small"]))
    elements.append(Paragraph("FINANCING INTELLIGENCE", s["section_label"]))
    for line in [
        "\u2022 Estimated equity: <b>$195K</b> (22% ratio) \u2022 Cash-out potential: Limited \u2014 early in build",
        "\u2022 Refi signals: BRRRR exit candidate (recent below-market purchases)",
        "\u2022 Estimated portfolio DSCR: <b>1.18</b>",
    ]:
        elements.append(Paragraph(line, s["body_small"]))
    elements.append(Paragraph(
        "Classic growth-phase investor buying 1\u20132/year. No LLC yet = opportunity to advise on entity structure. "
        "Concentrated in South Raleigh rental corridor. DSCR purchase loan for property #4 is the natural next conversation.",
        s["why_text"]
    ))
    elements.append(make_contact_block(has_linkedin=False))
    elements.append(Paragraph("<i>Contact data included with subscription</i>", s["footer"]))
    return elements


def build_dossier_3(s):
    """Entity-Based / High Net Worth dossier."""
    elements = []
    elements.append(Paragraph("DOSSIER #3 \u2014 Entity-Based Investor", s["dossier_header"]))
    elements.append(make_field_table([
        ("Investor Type", "Entity-Based / High Net Worth"),
        ("ICP Score", '<font color="#FF6B35"><b>78 / 100 \u2014 TIER 1 (Hot)</b></font>'),
        ("Owner", "[Redacted] Family Trust"),
        ("Properties Owned", "7 investment properties (Wake + Mecklenburg)"),
        ("Est. Portfolio Value", "$2.8M"),
        ("Entity Type", "Trust (established 2018)"),
        ("Mailing Address", "Out-of-state (Atlanta, GA)"),
        ("Key Signals", "Trust-owned, multi-county, out-of-state, portfolio 5+, high value, long hold"),
    ]))
    elements.append(Paragraph("PORTFOLIO SNAPSHOT", s["section_label"]))
    for line in [
        "\u2022 4 properties in Wake ($320K\u2013$680K) \u2022 3 in Mecklenburg ($410K\u2013$520K)",
        "\u2022 Oldest holding: 2018 (7+ year hold) \u2022 Mix of SF and small MF \u2022 No acquisitions in 18 months",
    ]:
        elements.append(Paragraph(line, s["body_small"]))
    elements.append(Paragraph("FINANCING INTELLIGENCE", s["section_label"]))
    for line in [
        "\u2022 Estimated equity: <b>$1.4M+</b> (50% ratio) \u2022 Cash-out potential (75% LTV): <b>$500K+</b>",
        "\u2022 Refi signals: Equity harvest prime candidate, rate reduction on older loans",
        "\u2022 Estimated portfolio DSCR: <b>1.52</b>",
        "\u2022 Wealth signals: FEC donor ($8,200), connected to 2 registered entities",
    ]:
        elements.append(Paragraph(line, s["body_small"]))
    elements.append(Paragraph(
        "Sophisticated trust-based investor with $1.4M+ in harvestable equity across two markets. "
        "Long holds with no recent acquisitions suggest a cash-out refi or new acquisition is overdue. "
        "Wealth signals confirm capacity. Multi-county = comfortable scaling geographically.",
        s["why_text"]
    ))
    elements.append(make_contact_block(has_linkedin=True))
    elements.append(Paragraph("<i>Contact data included with subscription</i>", s["footer"]))
    return elements


def build_pdf():
    doc = SimpleDocTemplate(
        OUTPUT_PATH,
        pagesize=letter,
        topMargin=0.4 * inch,
        bottomMargin=0.35 * inch,
        leftMargin=0.6 * inch,
        rightMargin=0.6 * inch,
    )
    s = build_styles()
    story = []

    # ── Page 1: Header + 3 Dossiers ──
    story.append(Spacer(1, 2))
    story.append(Paragraph("DSCR INVESTOR INTELLIGENCE", s["title"]))
    story.append(Paragraph("Sample Lead Dossiers \u2014 Wake County, NC", s["subtitle"]))
    story.append(Paragraph(
        "Generated by Still Mind Creative\u2019s proprietary scoring engine  |  "
        "684,895 investment properties analyzed  |  65,942 Tier 1 leads identified",
        s["stats"]
    ))
    story.append(hr())

    # Dossier 1
    story.extend(build_dossier_1(s))
    story.append(hr())

    # Dossier 2
    story.extend(build_dossier_2(s))
    story.append(hr())

    # Dossier 3
    story.extend(build_dossier_3(s))

    # ── Page 2: How We Build + CTA ──
    story.append(hr())
    story.append(Spacer(1, 4))

    story.append(Paragraph("HOW WE BUILD THESE DOSSIERS", s["cta_header"]))
    story.append(Spacer(1, 2))

    process_steps = [
        ("1.", "Public Property Records", "All 100 NC counties"),
        ("2.", "ICP Scoring Engine", "11 investor segments, 15+ signals"),
        ("3.", "Entity Resolution", "LLC / Trust / Corp \u2192 real person"),
        ("4.", "Contact Enrichment", "Skip trace, email/phone verification"),
        ("5.", "Financing Intelligence", "Mortgage records, equity calc, refi signals"),
        ("6.", "Wealth & Behavioral Signals", "FEC, IRS 990, acquisition patterns"),
    ]
    proc_data = [[
        Paragraph(f'<font color="#2EC4B6"><b>{step[0]}</b></font>', s["process_body"]),
        Paragraph(f"<b>{step[1]}</b>", s["process_body"]),
        Paragraph(step[2], s["process_body"]),
    ] for step in process_steps]
    proc_table = Table(proc_data, colWidths=[0.3 * inch, 2.0 * inch, 3.5 * inch])
    proc_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
    ]))
    story.append(proc_table)
    story.append(Spacer(1, 6))

    # Stats row
    stat_data = [[
        Paragraph('<font color="#2EC4B6"><b>684,895</b></font><br/><font size="7">properties analyzed</font>', s["cta_body"]),
        Paragraph('<font color="#2EC4B6"><b>65,942</b></font><br/><font size="7">Tier 1 leads</font>', s["cta_body"]),
        Paragraph('<font color="#2EC4B6"><b>157</b></font><br/><font size="7">fields per dossier</font>', s["cta_body"]),
    ]]
    stat_table = Table(stat_data, colWidths=[2.3 * inch, 2.3 * inch, 2.3 * inch])
    stat_table.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("BACKGROUND", (0, 0), (-1, -1), HexColor("#F1F5F9")),
        ("BOX", (0, 0), (-1, -1), 0.5, LIGHT_GRAY),
    ]))
    story.append(stat_table)
    story.append(Spacer(1, 8))

    # CTA
    story.append(Paragraph("PILOT OFFER", s["cta_header"]))
    story.append(Paragraph("$500 \u2014 100 Tier 1 Dossiers", s["cta_price"]))
    story.append(Paragraph(
        "Fully enriched: contact data, financing intel, scoring signals<br/>"
        "Your specific county or zip codes \u2022 Delivered in 5 business days<br/>"
        "Includes 30-min strategy walkthrough",
        s["cta_body"]
    ))
    story.append(Spacer(1, 3))
    story.append(Paragraph(
        '<b>One funded DSCR deal = 6\u201325x return on your $500 pilot.</b>',
        s["cta_body"]
    ))
    story.append(Spacer(1, 6))

    # Comparison table
    comp_header = ["Feature", "Us", "PropStream", "BatchData", "Shared Lists"]
    comp_rows = [
        ["ICP scoring (11 segments)", "\u2713", "\u2717", "\u2717", "\u2717"],
        ["Entity resolution", "\u2713", "Partial", "\u2717", "\u2717"],
        ["Financing intelligence", "\u2713", "\u2717", "\u2717", "\u2717"],
        ["Wealth signals", "\u2713", "\u2717", "\u2717", "\u2717"],
        ["Refi trigger detection", "\u2713", "\u2717", "\u2717", "\u2717"],
        ["Verified contact data", "\u2713", "\u2713", "\u2713", "\u2713"],
        ["Exclusive to you", "\u2713", "\u2717", "\u2717", "\u2717"],
    ]

    s_hdr = ParagraphStyle("TH", fontName="Helvetica-Bold", fontSize=6.5, textColor=WHITE)
    s_cell = ParagraphStyle("TC", fontName="Helvetica", fontSize=6.5, textColor=DARK_TEXT, alignment=TA_CENTER)
    s_cell_l = ParagraphStyle("TCL", fontName="Helvetica", fontSize=6.5, textColor=DARK_TEXT)
    s_check = ParagraphStyle("TCK", fontName="Helvetica", fontSize=6.5, textColor=TEAL, alignment=TA_CENTER)
    s_x = ParagraphStyle("TCX", fontName="Helvetica", fontSize=6.5, textColor=HexColor("#EF4444"), alignment=TA_CENTER)

    table_data = [[Paragraph(h, s_hdr) for h in comp_header]]
    for row in comp_rows:
        table_data.append([
            Paragraph(row[0], s_cell_l),
            *[Paragraph(c, s_check if c == "\u2713" else (s_x if c == "\u2717" else s_cell)) for c in row[1:]]
        ])

    comp_table = Table(table_data, colWidths=[2.2 * inch, 0.9 * inch, 1.0 * inch, 0.9 * inch, 1.0 * inch])
    comp_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
        ("BACKGROUND", (1, 1), (1, -1), HexColor("#F0FDF9")),
        ("ALIGN", (1, 0), (-1, -1), "CENTER"),
        ("FONTSIZE", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ("GRID", (0, 0), (-1, -1), 0.25, LIGHT_GRAY),
        ("BOX", (0, 0), (-1, -1), 0.5, MED_GRAY),
    ]))
    story.append(comp_table)
    story.append(Spacer(1, 4))

    story.append(Paragraph(
        "<i>PropStream and BatchData give you bulk data. We give you intelligence.</i>  |  "
        "Zack Lewis  |  Still Mind Creative, LLC  |  "
        "linkedin.com/in/zack-lewis53  |  stillmindcreative.com",
        ParagraphStyle("ContactFooter", fontName="Helvetica", fontSize=6.5,
                       textColor=MED_GRAY, alignment=TA_CENTER, leading=9)
    ))

    doc.build(story)
    print(f"Built: {OUTPUT_PATH}")


if __name__ == "__main__":
    build_pdf()
