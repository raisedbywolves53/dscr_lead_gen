"""
Build One-Pager PDF — front+back printable for meetups and email attachments.
Front: value prop, stats, pilot offer. Back: sample lead, how it works, pricing.

Usage: python build_one_pager.py
Output: sales/collateral/one_pager.pdf
"""

import os
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak
)
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER

# Brand colors
NAVY = HexColor("#1B2A4A")
TEAL = HexColor("#2EC4B6")
ORANGE = HexColor("#FF6B35")
WHITE = HexColor("#FFFFFF")
LIGHT_GRAY = HexColor("#E8ECF1")
MED_GRAY = HexColor("#94A3B8")
DARK_TEXT = HexColor("#1E293B")
SOFT_BG = HexColor("#F1F5F9")

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_PATH = os.path.join(SCRIPT_DIR, "one_pager.pdf")


def hr():
    return HRFlowable(width="100%", thickness=0.5, color=LIGHT_GRAY, spaceAfter=8, spaceBefore=6)


def build_pdf():
    doc = SimpleDocTemplate(
        OUTPUT_PATH,
        pagesize=letter,
        topMargin=0.4 * inch,
        bottomMargin=0.35 * inch,
        leftMargin=0.65 * inch,
        rightMargin=0.65 * inch,
    )

    # Styles
    s_title = ParagraphStyle("Title", fontName="Helvetica-Bold", fontSize=22, textColor=NAVY, alignment=TA_CENTER, spaceAfter=2, leading=24)
    s_tagline = ParagraphStyle("Tagline", fontName="Helvetica", fontSize=10, textColor=MED_GRAY, alignment=TA_CENTER, spaceAfter=8)
    s_section = ParagraphStyle("Section", fontName="Helvetica-Bold", fontSize=13, textColor=NAVY, spaceAfter=6, spaceBefore=10)
    s_body = ParagraphStyle("Body", fontName="Helvetica", fontSize=10, textColor=DARK_TEXT, leading=14, spaceAfter=6)
    s_body_sm = ParagraphStyle("BodySm", fontName="Helvetica", fontSize=9, textColor=DARK_TEXT, leading=13, spaceAfter=4)
    s_bullet = ParagraphStyle("Bullet", fontName="Helvetica", fontSize=10, textColor=DARK_TEXT, leading=14, spaceAfter=4, leftIndent=12)
    s_cta = ParagraphStyle("CTA", fontName="Helvetica-Bold", fontSize=16, textColor=ORANGE, alignment=TA_CENTER, spaceAfter=4)
    s_cta_body = ParagraphStyle("CTABody", fontName="Helvetica", fontSize=10, textColor=DARK_TEXT, alignment=TA_CENTER, leading=14, spaceAfter=4)
    s_footer = ParagraphStyle("Footer", fontName="Helvetica", fontSize=8, textColor=MED_GRAY, alignment=TA_CENTER, spaceBefore=8)
    s_italic = ParagraphStyle("Italic", fontName="Helvetica-Oblique", fontSize=9, textColor=MED_GRAY, alignment=TA_CENTER, spaceAfter=6)
    s_mono = ParagraphStyle("Mono", fontName="Courier", fontSize=8.5, textColor=DARK_TEXT, leading=12, spaceAfter=2, leftIndent=12)
    s_th = ParagraphStyle("TH", fontName="Helvetica-Bold", fontSize=9, textColor=WHITE)
    s_td = ParagraphStyle("TD", fontName="Helvetica", fontSize=9, textColor=DARK_TEXT)
    s_td_c = ParagraphStyle("TDC", fontName="Helvetica", fontSize=9, textColor=DARK_TEXT, alignment=TA_CENTER)
    s_section_back = ParagraphStyle("SectionBack", fontName="Helvetica-Bold", fontSize=12, textColor=NAVY, spaceAfter=6, spaceBefore=10)

    story = []

    # ══════════════════════════════════════════════
    # FRONT PAGE
    # ══════════════════════════════════════════════
    story.append(Spacer(1, 12))
    story.append(Paragraph("DSCR Lead Intelligence", s_title))
    story.append(Paragraph("Scored investor dossiers for loan officers who close deals", s_tagline))
    story.append(hr())

    # Problem / Solution
    story.append(Paragraph("The Problem", s_section))
    story.append(Paragraph(
        "You\u2019re working off the same recycled property lists as every other LO in your market. "
        "No scoring. No signals. No way to know who\u2019s actually worth calling.",
        s_body
    ))

    story.append(Paragraph("The Solution", s_section))
    story.append(Paragraph(
        "We analyze every investment property in your market and deliver ranked dossiers on the owners "
        "most likely to need a DSCR loan \u2014 with verified contact data, financing intelligence, "
        "and conversation starters.",
        s_body
    ))
    story.append(hr())

    # What You Get
    story.append(Paragraph("What You Get", s_section))
    bullets = [
        ('<font color="#2EC4B6"><b>Scored Leads</b></font> \u2014 '
         'Every lead ranked by 11 investor profiles and 15+ signals '
         '(portfolio size, entity structure, equity, acquisition velocity, absentee status)'),
        ('<font color="#2EC4B6"><b>Verified Contact</b></font> \u2014 '
         'Phone and email validated through skip trace, carrier lookup, and email verification'),
        ('<font color="#2EC4B6"><b>Financing Intel</b></font> \u2014 '
         'Estimated equity, cash-out potential, refi signals, current lender, DSCR estimate'),
        ('<font color="#2EC4B6"><b>Exclusive</b></font> \u2014 '
         'Your leads are yours. No shared lists, no lead recycling.'),
    ]
    for b in bullets:
        story.append(Paragraph(f"\u25b8  {b}", s_bullet))
    story.append(hr())

    # By the Numbers
    story.append(Paragraph("By the Numbers", s_section))
    num_data = [
        ["NC properties analyzed", "684,895"],
        ["Tier 1 (highest score) leads", "65,942"],
        ["Data fields per dossier", "157"],
        ["Avg cost per enriched lead", "$2\u2013$6"],
        ["Your ROI on one closed DSCR deal", "6\u201325x"],
    ]
    num_table_data = [[Paragraph(r[0], s_body_sm), Paragraph(f"<b>{r[1]}</b>", s_body_sm)] for r in num_data]
    num_table = Table(num_table_data, colWidths=[3.5 * inch, 2.5 * inch])
    num_table.setStyle(TableStyle([
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("BACKGROUND", (0, 0), (-1, -1), SOFT_BG),
        ("BOX", (0, 0), (-1, -1), 0.5, LIGHT_GRAY),
        ("LINEBELOW", (0, 0), (-1, -2), 0.25, LIGHT_GRAY),
    ]))
    story.append(num_table)
    story.append(hr())

    # Pilot CTA
    story.append(Spacer(1, 6))
    story.append(Paragraph("Pilot Offer: $500", s_cta))
    story.append(Paragraph(
        "100 Tier 1 investor dossiers for your county. Delivered in 5 business days.<br/>"
        "If one converts, you\u2019ve made $3K\u2013$12K.",
        s_cta_body
    ))
    story.append(Spacer(1, 12))

    # Contact
    story.append(Paragraph(
        "Zack Lewis  |  Still Mind Creative, LLC<br/>"
        "linkedin.com/in/zack-lewis53  |  stillmindcreative.com",
        s_footer
    ))
    story.append(Paragraph(
        "<i>Built by a former marketing lead for the largest mortgage team in the US.</i>",
        s_italic
    ))

    # ══════════════════════════════════════════════
    # BACK PAGE
    # ══════════════════════════════════════════════
    story.append(PageBreak())
    story.append(Spacer(1, 10))

    # Sample Lead Profile
    story.append(Paragraph("Sample Lead Profile", s_section_back))
    sample_lines = [
        "INVESTOR:  [Redacted], LLC",
        "TYPE:      Portfolio Landlord (12 properties)",
        "SCORE:     87/100 \u2014 Tier 1",
        "PORTFOLIO: $3.2M",
        "EQUITY:    $1.1M+ (34%)",
        "CASH-OUT:  $280K at 75% LTV",
        "SIGNALS:   Out-of-state, LLC, 3 acquisitions/year",
        "REFI:      Rate reduction, equity harvest",
        "EST DSCR:  1.35",
        "CONTACT:   Verified phone + email included",
    ]
    sample_data = [[Paragraph(line, s_mono)] for line in sample_lines]
    sample_table = Table(sample_data, colWidths=[6.0 * inch])
    sample_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), HexColor("#0F1B2D")),
        ("TEXTCOLOR", (0, 0), (-1, -1), HexColor("#E2E8F0")),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("BOX", (0, 0), (-1, -1), 1, NAVY),
    ]))
    # Override mono style color for dark bg
    s_mono_light = ParagraphStyle("MonoLight", fontName="Courier", fontSize=8.5, textColor=HexColor("#E2E8F0"), leading=12)
    sample_data2 = [[Paragraph(line, s_mono_light)] for line in sample_lines]
    sample_table2 = Table(sample_data2, colWidths=[6.0 * inch])
    sample_table2.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), HexColor("#0F1B2D")),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("BOX", (0, 0), (-1, -1), 1, NAVY),
    ]))
    story.append(sample_table2)
    story.append(hr())

    # How It Works
    story.append(Paragraph("How It Works", s_section_back))
    steps = [
        ("1.", "We pull property records from public sources (county assessors, state registries)"),
        ("2.", "Our scoring engine identifies investment property owners and ranks by deal probability"),
        ("3.", "We resolve entities (LLCs, trusts) back to real decision makers"),
        ("4.", "We enrich with skip trace, phone/email validation, mortgage data, and wealth signals"),
        ("5.", "You get a ranked spreadsheet of the best investors in your market \u2014 ready to call"),
    ]
    for num, text in steps:
        story.append(Paragraph(
            f'<font color="#2EC4B6"><b>{num}</b></font>  {text}',
            s_body_sm
        ))
    story.append(hr())

    # Pricing Table
    story.append(Paragraph("Pricing", s_section_back))
    price_header = ["Plan", "Leads/mo", "Price"]
    price_rows = [
        ["Pilot (one-time)", "100", "$500"],
        ["Starter", "250/mo", "$1,500/mo"],
        ["Pro", "750/mo", "$3,000/mo"],
        ["Enterprise", "Full state", "$5,000/mo"],
    ]
    price_data = [[Paragraph(h, s_th) for h in price_header]]
    for row in price_rows:
        price_data.append([Paragraph(row[0], s_td), Paragraph(row[1], s_td_c), Paragraph(row[2], s_td_c)])
    price_table = Table(price_data, colWidths=[2.5 * inch, 1.5 * inch, 1.5 * inch])
    price_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
        ("BACKGROUND", (0, 1), (-1, 1), HexColor("#FFF7ED")),  # Highlight pilot row
        ("ALIGN", (1, 0), (-1, -1), "CENTER"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("GRID", (0, 0), (-1, -1), 0.25, LIGHT_GRAY),
        ("BOX", (0, 0), (-1, -1), 0.5, MED_GRAY),
    ]))
    story.append(price_table)

    story.append(Spacer(1, 8))

    # Differentiator table
    story.append(Paragraph("What Makes This Different", s_section_back))
    diff_header = ["Feature", "Us", "PropStream", "BatchData", "Shared Lists"]
    diff_rows = [
        ["ICP scoring (11 segments)", "\u2713", "\u2717", "\u2717", "\u2717"],
        ["Entity resolution", "\u2713", "Partial", "\u2717", "\u2717"],
        ["Portfolio analysis", "\u2713", "Limited", "\u2717", "\u2717"],
        ["Financing intelligence", "\u2713", "\u2717", "\u2717", "\u2717"],
        ["Wealth signals", "\u2713", "\u2717", "\u2717", "\u2717"],
        ["Verified contact data", "\u2713", "\u2713", "\u2713", "\u2713"],
        ["Exclusive to you", "\u2713", "\u2717", "\u2717", "\u2717"],
        ["Price per lead", "$2\u2013$6", "~$0.10", "~$0.05", "$20\u2013$75"],
    ]
    s_check = ParagraphStyle("Chk", fontName="Helvetica", fontSize=8, textColor=TEAL, alignment=TA_CENTER)
    s_xmark = ParagraphStyle("Xmk", fontName="Helvetica", fontSize=8, textColor=HexColor("#EF4444"), alignment=TA_CENTER)
    s_dc = ParagraphStyle("DC", fontName="Helvetica", fontSize=8, textColor=DARK_TEXT, alignment=TA_CENTER)
    s_dl = ParagraphStyle("DL", fontName="Helvetica", fontSize=8, textColor=DARK_TEXT)
    s_dh = ParagraphStyle("DH", fontName="Helvetica-Bold", fontSize=7.5, textColor=WHITE)

    diff_data = [[Paragraph(h, s_dh) for h in diff_header]]
    for row in diff_rows:
        cells = [Paragraph(row[0], s_dl)]
        for c in row[1:]:
            if c == "\u2713":
                cells.append(Paragraph(c, s_check))
            elif c == "\u2717":
                cells.append(Paragraph(c, s_xmark))
            else:
                cells.append(Paragraph(c, s_dc))
        diff_data.append(cells)
    diff_table = Table(diff_data, colWidths=[2.0 * inch, 0.85 * inch, 1.0 * inch, 0.9 * inch, 1.0 * inch])
    diff_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
        ("BACKGROUND", (1, 1), (1, -1), HexColor("#F0FDF9")),
        ("ALIGN", (1, 0), (-1, -1), "CENTER"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("GRID", (0, 0), (-1, -1), 0.25, LIGHT_GRAY),
        ("BOX", (0, 0), (-1, -1), 0.5, MED_GRAY),
    ]))
    story.append(diff_table)

    story.append(Spacer(1, 4))
    story.append(Paragraph(
        "<i>PropStream and BatchData give you bulk data. We give you intelligence.</i>",
        s_italic
    ))
    story.append(Spacer(1, 4))
    story.append(Paragraph(
        "Client Reference Available Upon Request  |  "
        "Zack Lewis  |  Still Mind Creative, LLC  |  stillmindcreative.com",
        s_footer
    ))

    doc.build(story)
    print(f"Built: {OUTPUT_PATH}")


if __name__ == "__main__":
    build_pdf()
