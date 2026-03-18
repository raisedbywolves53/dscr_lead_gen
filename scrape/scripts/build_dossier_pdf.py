"""
DSCR Investor Dossier — McKinsey-Style PDF Generator
=====================================================

Professional single-page investor intelligence dossier using fpdf2.
Design principles: McKinsey/BCG-style consulting brief.
- Extreme white space discipline
- Information hierarchy through size contrast
- Grid-based alignment (2-column main content)
- Data elevated, narrative minimized
- Restrained color palette (one accent blue + grays)

Usage:
    python scripts/build_dossier_pdf.py --input data/enriched/fl_client_samples.csv
    python scripts/build_dossier_pdf.py --input data/enriched/fl_client_samples.csv --redacted
"""

import argparse
import math
import sys
from pathlib import Path

import pandas as pd
from fpdf import FPDF

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent

# ── Logo Path ───────────────────────────────────────────────────────
LOGO_PATH = PROJECT_DIR / "assets" / "logo.png"

# ── McKinsey Color Palette ──────────────────────────────────────────
PRIMARY = (0, 51, 102)        # Deep navy — header, section titles
ACCENT = (0, 102, 179)        # Bright blue — metric numbers, highlights
BLACK = (33, 33, 33)          # Body text (soft black)
DARK_GRAY = (89, 89, 89)      # Labels, captions
MED_GRAY = (153, 153, 153)    # Dividers, borders
LIGHT_BG = (242, 242, 242)    # Card backgrounds, alt rows
WHITE = (255, 255, 255)
GREEN = (39, 137, 68)         # Positive signals
AMBER = (204, 136, 0)         # Caution
RED = (191, 49, 49)           # Negative

# ── Page Layout ─────────────────────────────────────────────────────
L_MARGIN = 15
R_MARGIN = 15
USABLE_W = 215.9 - L_MARGIN - R_MARGIN  # 185.9mm
COL_GUTTER = 5
COL_W = (USABLE_W - COL_GUTTER) / 2     # ~90.45mm each

# ── Use Code Map ────────────────────────────────────────────────────
USE_CODE_MAP = {
    "001": "Single Family", "01": "Single Family", "1": "Single Family",
    "002": "Mobile Home", "02": "Mobile Home",
    "003": "Multi-Family", "03": "Multi-Family",
    "004": "Condominium", "04": "Condominium",
    "005": "Cooperative", "05": "Cooperative",
    "008": "Multi-Family (10+)", "08": "Multi-Family (10+)",
}


# ── Formatting Helpers ──────────────────────────────────────────────
def fc(val):
    """Format currency."""
    try:
        s = str(val).replace(",", "").replace("$", "").strip()
        if not s or s.upper() in ("NAN", "NONE", ""):
            return None
        v = float(s)
        if v == 0 or (isinstance(v, float) and math.isnan(v)):
            return None
        if v >= 1_000_000:
            return f"${v/1_000_000:.1f}M"
        if v >= 1_000:
            return f"${v:,.0f}"
        return f"${v:,.0f}"
    except (ValueError, TypeError):
        return None


def fp(val):
    """Format percentage."""
    try:
        s = str(val).replace(",", "").replace("%", "").strip()
        if not s or s.upper() in ("NAN", "NONE", ""):
            return None
        v = float(s)
        if v == 0 or math.isnan(v):
            return None
        if v < 1:
            return f"{v * 100:.0f}%"
        return f"{v:.0f}%"
    except (ValueError, TypeError):
        return None


def fv(val):
    """Format value — return None if empty."""
    s = str(val).strip()
    if not s or s.upper() in ("NAN", "NONE", "", "0", "0.0", "N/A", "--"):
        return None
    return s


def fphone(val):
    s = str(val).strip().replace("-", "").replace("(", "").replace(")", "").replace(" ", "")
    if len(s) == 10:
        return f"({s[:3]}) {s[3:6]}-{s[6:]}"
    if len(s) == 11 and s[0] == "1":
        return f"({s[1:4]}) {s[4:7]}-{s[7:]}"
    return fv(val)


def fprop_types(val):
    s = str(val).strip()
    if not s or s.upper() in ("NAN", "NONE", ""):
        return None
    codes = [c.strip() for c in s.split(",")]
    names = list(dict.fromkeys(USE_CODE_MAP.get(c, c) for c in codes))
    return ", ".join(names)


def clean_name(val):
    s = str(val).strip().rstrip("& ").rstrip(",").strip()
    return s if s and s.upper() not in ("NAN", "NONE") else None


def redact(val):
    if not val:
        return None
    return "X" * min(len(str(val)), 12)


def build_talking_points(row):
    """Generate consulting-grade insight paragraph."""
    pts = []
    props = int(float(str(row.get("props", row.get("property_count", 1)))))
    pval = float(str(row.get("total_portfolio_value", 0)).replace(",", ""))
    is_ent = str(row.get("is_entity", "")).upper() == "TRUE"
    oos = str(row.get("out_of_state", "")).upper() == "TRUE"
    lender = fv(row.get("attom_lender_name", row.get("best_lender", "")))
    rate = fv(row.get("attom_rate_type", ""))
    cashout = float(str(row.get("max_cashout_75", row.get("portfolio_cashout_75", 0))).replace(",", "").replace("$", "") or 0)
    refi = str(row.get("refi_priority", "")).lower()
    brrrr = str(row.get("brrrr_exit_candidate", "")).upper() == "TRUE"
    equity_harv = str(row.get("equity_harvest_candidate", "")).upper() == "TRUE"
    p12 = int(float(str(row.get("purchases_last_12mo", 0)) or 0))
    rent = float(str(row.get("est_annual_rent", 0)).replace(",", "").replace("$", "") or 0)

    if props >= 10:
        pts.append(f"Institutional-scale investor with {props} properties and a ${pval:,.0f} portfolio.")
    elif props >= 5:
        pts.append(f"Established portfolio landlord with {props} properties worth ${pval:,.0f}.")
    elif props >= 2:
        pts.append(f"Active investor scaling a {props}-property portfolio valued at ${pval:,.0f}.")

    if is_ent:
        pts.append("Entity-structured ownership signals sophistication and comfort with non-QM lending products.")
    if oos:
        pts.append("Out-of-state investor managing remotely -- may prefer streamlined DSCR process.")
    if lender and rate:
        pts.append(f"Currently financed through {lender} ({rate.lower()}).")
    elif lender:
        pts.append(f"Currently financed through {lender}.")
    if cashout > 100000:
        pts.append(f"Cash-out refi potential: up to ${cashout:,.0f} available at 75% LTV.")
    if brrrr:
        pts.append("Recent below-market acquisition indicates BRRRR strategy -- may need DSCR exit financing.")
    if equity_harv:
        pts.append("Long-held properties with accumulated equity -- prime candidate for cash-out refi.")
    if p12 >= 2:
        pts.append(f"Highly active: {p12} acquisitions in the past 12 months.")
    elif p12 == 1:
        pts.append("Recent acquisition indicates active investment posture.")
    if rent > 50000:
        pts.append(f"Est. ${rent:,.0f}/year rental income supports strong DSCR qualification.")
    if refi == "high":
        pts.append("Flagged as HIGH refinance priority.")

    return " ".join(pts) if pts else "Confirmed investment property owner -- DSCR lending conversation opportunity."


# ── PDF Builder ─────────────────────────────────────────────────────
class DossierPDF(FPDF):
    def __init__(self):
        super().__init__(orientation="P", unit="mm", format="letter")
        self.set_auto_page_break(auto=False)

    def _metric_card(self, x, y, w, h, value, label):
        """Draw a metric highlight card."""
        self.set_fill_color(*LIGHT_BG)
        self.rect(x, y, w, h, "F")
        # Value
        self.set_font("Helvetica", "B", 20)
        self.set_text_color(*ACCENT)
        self.set_xy(x, y + 2)
        self.cell(w, 10, str(value) if value else "--", align="C")
        # Label
        self.set_font("Helvetica", "", 7)
        self.set_text_color(*DARK_GRAY)
        self.set_xy(x, y + 13)
        self.cell(w, 4, label.upper(), align="C")

    def _section_header(self, x, y, text, width):
        """Draw a section header with underline."""
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(*PRIMARY)
        self.set_xy(x, y)
        self.cell(width, 5, text.upper())
        self.set_draw_color(*PRIMARY)
        self.set_line_width(0.3)
        self.line(x, y + 5.5, x + width, y + 5.5)
        return y + 8

    def _label_value(self, x, y, label, value, width, bold_value=True):
        """Draw a label: value pair."""
        if value is None:
            return y  # Skip if no value
        self.set_font("Helvetica", "", 7.5)
        self.set_text_color(*DARK_GRAY)
        self.set_xy(x, y)
        self.cell(35, 4, label)
        style = "B" if bold_value else ""
        self.set_font("Helvetica", style, 8)
        self.set_text_color(*BLACK)
        self.set_xy(x + 35, y)
        self.cell(width - 35, 4, str(value)[:50])
        return y + 5

    def _signal_dot(self, x, y, text, status="positive"):
        """Draw a colored dot + text signal."""
        colors = {"positive": GREEN, "caution": AMBER, "negative": RED, "neutral": MED_GRAY}
        r, g, b = colors.get(status, MED_GRAY)
        self.set_fill_color(r, g, b)
        self.ellipse(x, y + 0.5, 2.5, 2.5, "F")
        self.set_font("Helvetica", "", 8)
        self.set_text_color(*BLACK)
        self.set_xy(x + 4, y)
        self.cell(0, 4, text)
        return y + 5.5


def generate_dossier(row, output_path, is_redacted=False):
    pdf = DossierPDF()
    pdf.add_page()

    r = lambda v: redact(v) if is_redacted and v else v

    # ── Extract Data ────────────────────────────────────────────
    owner = clean_name(row.get("OWN_NAME", "")) or "Unknown"
    segment = fv(row.get("selling_segment", row.get("_icp", ""))) or "Investor"
    tier = fv(row.get("selling_tier", "")) or ""
    score = float(str(row.get("score", row.get("_score", 0))) or 0)
    props = fv(row.get("props", row.get("property_count", "")))
    portfolio_val = fc(row.get("total_portfolio_value", ""))
    avg_val = fc(row.get("avg_property_value", ""))
    equity = fc(row.get("estimated_equity", ""))
    equity_pct = fp(row.get("equity_ratio", ""))
    prop_types = fprop_types(row.get("property_types", ""))

    phone1 = fphone(row.get("phone_1", ""))
    phone1_type = fv(row.get("phone_1_type", ""))
    phone2 = fphone(row.get("phone_2", ""))
    email1 = fv(row.get("email_1", ""))
    email2 = fv(row.get("email_2", ""))

    mail_addr = fv(row.get("OWN_ADDR1", row.get("mail_street", "")))
    mail_city = fv(row.get("OWN_CITY", row.get("mail_city", "")))
    mail_state = fv(row.get("OWN_STATE_DOM", row.get("mail_state", "")))
    mail_zip = fv(row.get("OWN_ZIPCD", row.get("mail_zip", "")))

    lender = fv(row.get("attom_lender_name", row.get("best_lender", "")))
    loan_amt = fc(row.get("attom_loan_amount", ""))
    rate_type = fv(row.get("attom_rate_type", ""))
    loan_date = fv(row.get("attom_loan_date", ""))
    due_date = fv(row.get("attom_due_date", row.get("est_maturity_date", "")))
    est_rate = fv(row.get("est_interest_rate", ""))
    if est_rate:
        try:
            est_rate = f"{float(est_rate):.1f}%"
        except (ValueError, TypeError):
            pass
    remaining = fc(row.get("est_remaining_balance", ""))
    cashout = fc(row.get("max_cashout_75", row.get("portfolio_cashout_75", "")))
    dscr = fv(row.get("est_dscr", ""))
    rent = fc(row.get("est_annual_rent", ""))
    noi = fc(row.get("est_noi", ""))
    debt_svc = fc(row.get("est_monthly_debt_service", ""))

    recent_date = fv(row.get("most_recent_purchase_date", row.get("most_recent_purchase", "")))
    recent_price = fc(row.get("most_recent_purchase_price", row.get("most_recent_price", "")))
    p12 = fv(row.get("purchases_last_12mo", ""))
    p36 = fv(row.get("purchases_last_36mo", ""))
    avg_purchase = fc(row.get("avg_purchase_price", row.get("avg_sale_price", "")))

    is_entity = str(row.get("is_entity", "")).upper() == "TRUE"
    officers = fv(row.get("entity_officers", row.get("officer_names", "")))
    agent = fv(row.get("registered_agent_name", row.get("registered_agent", "")))
    entity_status = fv(row.get("entity_status", row.get("sunbiz_status", "")))

    refi_priority = fv(row.get("refi_priority", ""))
    refi_signals = fv(row.get("refi_signals", row.get("est_refi_signals", "")))

    # Collect active signals
    signals = []
    if str(row.get("brrrr_exit_candidate", "")).upper() == "TRUE":
        signals.append(("BRRRR Exit Candidate", "caution"))
    if str(row.get("equity_harvest_candidate", "")).upper() == "TRUE":
        signals.append(("Equity Harvest Opportunity", "positive"))
    if str(row.get("rate_refi_candidate", "")).upper() == "TRUE":
        signals.append(("Rate Refinance Candidate", "positive"))
    if str(row.get("str_licensed", "")).upper() == "TRUE":
        signals.append(("STR Licensed Property", "neutral"))
    if str(row.get("out_of_state", "")).upper() == "TRUE":
        signals.append(("Out-of-State Investor", "neutral"))

    tier_label = "HOT" if "Hot" in str(tier) or "1" in str(tier) else "WARM"

    # ════════════════════════════════════════════════════════════
    # A. HEADER BAR
    # ════════════════════════════════════════════════════════════
    pdf.set_fill_color(*PRIMARY)
    pdf.rect(0, 0, 215.9, 22, "F")
    # Accent strip
    pdf.set_fill_color(*ACCENT)
    pdf.rect(0, 22, 215.9, 0.6, "F")

    # Logo (left side)
    if LOGO_PATH.exists():
        pdf.image(str(LOGO_PATH), x=L_MARGIN, y=2.5, h=17)
        title_x = L_MARGIN + 20
    else:
        title_x = L_MARGIN

    # Title
    pdf.set_xy(title_x, 4)
    pdf.set_font("Helvetica", "B", 14)
    pdf.set_text_color(*WHITE)
    pdf.cell(110, 6, "INVESTOR INTELLIGENCE DOSSIER")

    # Subtitle
    pdf.set_xy(title_x, 11)
    pdf.set_font("Helvetica", "", 7.5)
    pdf.set_text_color(180, 200, 230)
    county = "Palm Beach County, FL"
    pdf.cell(110, 4, f"Still Mind Creative  |  {county}  |  Confidential")

    # Score badge (right side)
    score_bg = GREEN if score >= 50 else AMBER if score >= 30 else RED
    badge_x = 215.9 - R_MARGIN - 28
    pdf.set_fill_color(*score_bg)
    pdf.rect(badge_x, 3, 14, 16, "F")
    pdf.set_xy(badge_x, 3.5)
    pdf.set_font("Helvetica", "B", 16)
    pdf.set_text_color(*WHITE)
    pdf.cell(14, 10, str(int(score)), align="C")
    # Score label
    pdf.set_xy(badge_x, 12)
    pdf.set_font("Helvetica", "", 5.5)
    pdf.cell(14, 4, "SCORE", align="C")

    # Tier badge
    tier_bg = (0, 71, 122) if tier_label == "HOT" else AMBER
    pdf.set_fill_color(*tier_bg)
    tier_x = badge_x + 16
    pdf.rect(tier_x, 4.5, 12, 12, "F")
    pdf.set_xy(tier_x, 5.5)
    pdf.set_font("Helvetica", "B", 7)
    pdf.set_text_color(*WHITE)
    pdf.cell(12, 8, tier_label, align="C")

    # ════════════════════════════════════════════════════════════
    # B. SUBJECT IDENTITY
    # ════════════════════════════════════════════════════════════
    y = 27
    pdf.set_xy(L_MARGIN, y)
    pdf.set_font("Helvetica", "B", 18)
    pdf.set_text_color(*PRIMARY)
    display_name = r(owner) if is_redacted else owner
    pdf.cell(USABLE_W, 9, display_name)

    y += 10
    pdf.set_xy(L_MARGIN, y)
    pdf.set_font("Helvetica", "", 8.5)
    pdf.set_text_color(*DARK_GRAY)
    summary = f"{segment}  |  {props or '?'} Properties  |  {portfolio_val or 'Portfolio'}"
    pdf.cell(USABLE_W, 4, summary)

    y += 7
    # Thin divider
    pdf.set_draw_color(*MED_GRAY)
    pdf.set_line_width(0.2)
    pdf.line(L_MARGIN, y, L_MARGIN + USABLE_W, y)

    # ════════════════════════════════════════════════════════════
    # C. KEY METRICS ROW (4 cards)
    # ════════════════════════════════════════════════════════════
    y += 3
    card_w = (USABLE_W - 9) / 4  # 4 cards with 3mm gaps
    card_h = 20

    metrics = [
        (props or "--", "PROPERTIES"),
        (portfolio_val or "--", "PORTFOLIO VALUE"),
        (equity or "--", "EST. EQUITY"),
        (dscr or "--", "EST. DSCR"),
    ]
    for i, (val, label) in enumerate(metrics):
        cx = L_MARGIN + i * (card_w + 3)
        pdf._metric_card(cx, y, card_w, card_h, val, label)

    # ════════════════════════════════════════════════════════════
    # D. MAIN CONTENT — TWO COLUMNS
    # ════════════════════════════════════════════════════════════
    y += card_h + 5
    left_x = L_MARGIN
    right_x = L_MARGIN + COL_W + COL_GUTTER

    # ── LEFT COLUMN ─────────────────────────────────────────
    ly = y

    # Contact Information
    ly = pdf._section_header(left_x, ly, "Contact Information", COL_W)
    if phone1:
        ptype = f" ({phone1_type})" if phone1_type else ""
        ly = pdf._label_value(left_x, ly, "Phone", f"{r(phone1)}{ptype}", COL_W)
    if phone2 and phone2 != phone1:
        ly = pdf._label_value(left_x, ly, "Phone 2", r(phone2), COL_W)
    if email1:
        ly = pdf._label_value(left_x, ly, "Email", r(email1), COL_W)
    if email2:
        ly = pdf._label_value(left_x, ly, "Email 2", r(email2), COL_W)
    if mail_addr:
        full_mail = f"{r(mail_addr)}, {mail_city or ''}, {mail_state or ''} {mail_zip or ''}"
        ly = pdf._label_value(left_x, ly, "Mailing Address", full_mail.strip(", "), COL_W)
    ly += 3

    # Portfolio Overview
    ly = pdf._section_header(left_x, ly, "Portfolio Overview", COL_W)
    ly = pdf._label_value(left_x, ly, "Properties", props, COL_W)
    ly = pdf._label_value(left_x, ly, "Portfolio Value", portfolio_val, COL_W)
    ly = pdf._label_value(left_x, ly, "Avg Property Value", avg_val, COL_W)
    ly = pdf._label_value(left_x, ly, "Property Types", prop_types, COL_W)
    ly = pdf._label_value(left_x, ly, "Estimated Equity", equity, COL_W)
    ly = pdf._label_value(left_x, ly, "Equity Ratio", equity_pct, COL_W)
    ly += 3

    # Acquisition Behavior
    ly = pdf._section_header(left_x, ly, "Acquisition Behavior", COL_W)
    ly = pdf._label_value(left_x, ly, "Last Purchase", recent_date, COL_W)
    ly = pdf._label_value(left_x, ly, "Purchase Price", recent_price, COL_W)
    ly = pdf._label_value(left_x, ly, "Purchases (12 mo)", p12, COL_W)
    ly = pdf._label_value(left_x, ly, "Purchases (36 mo)", p36, COL_W)
    ly = pdf._label_value(left_x, ly, "Avg Purchase Price", avg_purchase, COL_W)

    # ── RIGHT COLUMN ────────────────────────────────────────
    ry = y

    # Financing Intelligence
    ry = pdf._section_header(right_x, ry, "Financing Intelligence", COL_W)
    ry = pdf._label_value(right_x, ry, "Current Lender", lender, COL_W)
    ry = pdf._label_value(right_x, ry, "Loan Amount", loan_amt, COL_W)
    ry = pdf._label_value(right_x, ry, "Rate Type", rate_type, COL_W)
    ry = pdf._label_value(right_x, ry, "Est. Rate", est_rate, COL_W)
    ry = pdf._label_value(right_x, ry, "Origination", loan_date, COL_W)
    ry = pdf._label_value(right_x, ry, "Maturity", due_date, COL_W)
    ry = pdf._label_value(right_x, ry, "Est. Balance", remaining, COL_W)
    ry = pdf._label_value(right_x, ry, "Cash-Out (75% LTV)", cashout, COL_W)
    ry += 3

    # Rental & DSCR
    if rent or dscr:
        ry = pdf._section_header(right_x, ry, "Rental & DSCR Analysis", COL_W)
        ry = pdf._label_value(right_x, ry, "Est. Annual Rent", rent, COL_W)
        ry = pdf._label_value(right_x, ry, "Est. NOI", noi, COL_W)
        ry = pdf._label_value(right_x, ry, "Monthly Debt Svc", debt_svc, COL_W)
        ry = pdf._label_value(right_x, ry, "Est. DSCR", dscr, COL_W)
        ry += 3

    # Entity Details (if applicable)
    if is_entity:
        ry = pdf._section_header(right_x, ry, "Entity Details", COL_W)
        ry = pdf._label_value(right_x, ry, "Registered Agent", r(agent), COL_W)
        ry = pdf._label_value(right_x, ry, "Officers", r(officers), COL_W)
        ry = pdf._label_value(right_x, ry, "Entity Status", entity_status, COL_W)
        ry += 3

    # Opportunity Signals
    if signals or refi_priority:
        ry = pdf._section_header(right_x, ry, "Opportunity Signals", COL_W)
        if refi_priority:
            status = "positive" if refi_priority.lower() == "high" else "caution" if refi_priority.lower() == "medium" else "neutral"
            ry = pdf._signal_dot(right_x, ry, f"Refi Priority: {refi_priority}", status)
        for sig_text, sig_status in signals:
            ry = pdf._signal_dot(right_x, ry, sig_text, sig_status)
        if refi_signals:
            pdf.set_font("Helvetica", "", 7)
            pdf.set_text_color(*DARK_GRAY)
            pdf.set_xy(right_x + 4, ry)
            pdf.multi_cell(COL_W - 4, 3.5, refi_signals[:120])
            ry = pdf.get_y() + 2

    # ════════════════════════════════════════════════════════════
    # E. BOTTOM INSIGHT BAR
    # ════════════════════════════════════════════════════════════
    talking = build_talking_points(row)
    bar_y = max(ly, ry) + 4

    # If we're running too long, truncate talking points
    if bar_y > 235:
        bar_y = 235

    pdf.set_fill_color(*LIGHT_BG)
    pdf.set_draw_color(*ACCENT)

    # Estimate height
    pdf.set_font("Helvetica", "", 8)
    lines = max(3, len(talking) // 90 + 2)
    bar_h = 8 + lines * 4

    pdf.rect(L_MARGIN, bar_y, USABLE_W, bar_h, "F")
    pdf.set_line_width(0.6)
    pdf.line(L_MARGIN, bar_y, L_MARGIN, bar_y + bar_h)

    pdf.set_xy(L_MARGIN + 4, bar_y + 2)
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_text_color(*PRIMARY)
    pdf.cell(USABLE_W - 8, 4, "RECOMMENDED APPROACH")
    pdf.set_xy(L_MARGIN + 4, bar_y + 7)
    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(*BLACK)
    pdf.multi_cell(USABLE_W - 8, 4, talking)

    # ════════════════════════════════════════════════════════════
    # F. FOOTER
    # ════════════════════════════════════════════════════════════
    footer_y = 265
    pdf.set_draw_color(*MED_GRAY)
    pdf.set_line_width(0.2)
    pdf.line(L_MARGIN, footer_y, L_MARGIN + USABLE_W, footer_y)

    pdf.set_xy(L_MARGIN, footer_y + 1.5)
    pdf.set_font("Helvetica", "", 6)
    pdf.set_text_color(*MED_GRAY)
    conf = "SAMPLE" if is_redacted else "Confidential"
    pdf.cell(USABLE_W / 3, 3, f"{conf} | Proprietary Analysis")
    pdf.cell(USABLE_W / 3, 3, "Still Mind Creative", align="C")
    pdf.cell(USABLE_W / 3, 3, "Source: Public Records + Enrichment APIs", align="R")

    pdf.output(str(output_path))


def build_csv_export(df, output_path):
    """Build clean CRM-ready CSV."""
    cols = {
        "OWN_NAME": "Owner Name", "selling_segment": "Segment", "selling_tier": "Tier",
        "score": "Score", "property_count": "Properties", "total_portfolio_value": "Portfolio Value",
        "avg_property_value": "Avg Value", "estimated_equity": "Equity", "equity_ratio": "Equity %",
        "phone_1": "Phone 1", "phone_1_type": "Phone Type", "phone_2": "Phone 2",
        "email_1": "Email 1", "email_2": "Email 2",
        "OWN_ADDR1": "Mail Street", "OWN_CITY": "Mail City",
        "OWN_STATE_DOM": "Mail State", "OWN_ZIPCD": "Mail Zip",
        "PHY_ADDR1": "Property Address", "property_types": "Property Types",
        "attom_lender_name": "Lender", "attom_loan_amount": "Loan Amount",
        "attom_rate_type": "Rate Type", "est_interest_rate": "Est Rate",
        "attom_loan_date": "Loan Date", "attom_due_date": "Maturity",
        "est_remaining_balance": "Est Balance", "max_cashout_75": "Cash-Out (75%)",
        "most_recent_purchase_date": "Last Purchase", "most_recent_purchase_price": "Purchase Price",
        "purchases_last_12mo": "Purchases 12mo", "purchases_last_36mo": "Purchases 36mo",
        "avg_purchase_price": "Avg Purchase", "est_dscr": "DSCR",
        "est_annual_rent": "Annual Rent", "est_noi": "NOI",
        "refi_priority": "Refi Priority", "refi_signals": "Refi Signals",
        "is_entity": "Entity", "registered_agent_name": "Agent",
        "entity_officers": "Officers", "entity_status": "Entity Status",
    }
    export = pd.DataFrame()
    for src, dst in cols.items():
        export[dst] = df[src] if src in df.columns else ""
    if "Owner Name" in export.columns:
        export["Owner Name"] = export["Owner Name"].apply(lambda x: clean_name(x) or x)
    if "Property Types" in export.columns:
        export["Property Types"] = export["Property Types"].apply(lambda x: fprop_types(x) or x)
    export.to_csv(output_path, index=False)
    return export


def main():
    parser = argparse.ArgumentParser(description="Generate McKinsey-style investor dossier PDFs")
    parser.add_argument("--input", type=str, required=True)
    parser.add_argument("--output-dir", type=str, default=None)
    parser.add_argument("--redacted", action="store_true")
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.is_absolute():
        input_path = PROJECT_DIR / args.input
    if not input_path.exists():
        print(f"Input not found: {input_path}")
        return

    output_dir = Path(args.output_dir) if args.output_dir else PROJECT_DIR / "data" / "dossiers"
    output_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(input_path, dtype=str)
    print(f"Generating {'redacted ' if args.redacted else ''}dossiers for {len(df)} leads...\n")

    for i, (_, row) in enumerate(df.iterrows()):
        owner = clean_name(str(row.get("OWN_NAME", f"lead_{i}"))) or f"lead_{i}"
        safe = "".join(c if c.isalnum() or c in " _-" else "_" for c in owner)[:40].strip()
        suffix = "_redacted" if args.redacted else ""
        fname = f"dossier_{i+1:02d}_{safe}{suffix}.pdf"
        path = output_dir / fname
        generate_dossier(row, path, is_redacted=args.redacted)
        print(f"  [{i+1}/{len(df)}] {fname}")

    csv_path = output_dir / ("crm_export_redacted.csv" if args.redacted else "crm_export.csv")
    export = build_csv_export(df, csv_path)
    print(f"\n  CRM CSV: {csv_path.name} ({len(export)} leads, {len(export.columns)} columns)")
    print(f"\nDone. {len(df)} PDFs + CSV saved to {output_dir}/")


if __name__ == "__main__":
    main()
