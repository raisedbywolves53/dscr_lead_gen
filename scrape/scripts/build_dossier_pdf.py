"""
DSCR Investor Dossier — PDF Generator (fpdf2)
===============================================

Generates professionally designed investor dossier PDFs using fpdf2.
Pure Python — no system dependencies (GTK, Pango, etc.).

Usage:
    python scripts/build_dossier_pdf.py --input data/enriched/fl_client_samples.csv
    python scripts/build_dossier_pdf.py --input data/enriched/fl_client_samples.csv --redacted
"""

import argparse
import sys
from pathlib import Path

import pandas as pd
from fpdf import FPDF

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent

# Colors
NAVY = (30, 64, 175)
DARK = (15, 23, 42)
GRAY = (100, 116, 139)
LIGHT_GRAY = (148, 163, 184)
LIGHT_BG = (240, 249, 255)
WHITE = (255, 255, 255)
GREEN = (34, 197, 94)
AMBER = (245, 158, 11)
RED = (239, 68, 68)
BORDER = (226, 232, 240)
ROW_ALT = (248, 250, 252)

# Use code lookup
USE_CODE_MAP = {
    "001": "Single Family", "01": "Single Family", "1": "Single Family",
    "002": "Mobile Home", "02": "Mobile Home",
    "003": "Multi-Family (2-9)", "03": "Multi-Family (2-9)",
    "004": "Condominium", "04": "Condominium",
    "005": "Cooperative", "05": "Cooperative",
    "008": "Multi-Family (10+)", "08": "Multi-Family (10+)",
}


def fmt_currency(val):
    try:
        s = str(val).replace(",", "").replace("$", "").strip()
        if not s or s.upper() in ("NAN", "NONE", ""):
            return "--"
        v = float(s)
        if v == 0 or pd.isna(v):
            return "--"
        return f"${v:,.0f}"
    except (ValueError, TypeError):
        return "--"


def fmt_pct(val):
    try:
        v = float(str(val).replace(",", "").replace("%", ""))
        if v == 0:
            return "--"
        if v < 1:
            return f"{v * 100:.1f}%"
        return f"{v:.1f}%"
    except (ValueError, TypeError):
        return "--"


def fmt_val(val, default="--"):
    s = str(val).strip()
    if not s or s.upper() in ("NAN", "NONE", "", "0", "0.0", "N/A"):
        return default
    return s


def fmt_phone(val):
    s = str(val).strip().replace("-", "").replace("(", "").replace(")", "").replace(" ", "")
    if len(s) == 10:
        return f"({s[:3]}) {s[3:6]}-{s[6:]}"
    if len(s) == 11 and s[0] == "1":
        return f"({s[1:4]}) {s[4:7]}-{s[7:]}"
    return fmt_val(val)


def fmt_prop_types(val):
    """Convert raw property type codes to human-readable."""
    s = str(val).strip()
    if not s or s.upper() in ("NAN", "NONE", ""):
        return "--"
    codes = [c.strip() for c in s.split(",")]
    names = []
    seen = set()
    for code in codes:
        name = USE_CODE_MAP.get(code, code)
        if name not in seen:
            names.append(name)
            seen.add(name)
    return ", ".join(names)


def clean_owner_name(val):
    """Clean owner name — remove trailing & and other artifacts."""
    s = str(val).strip()
    if not s or s.upper() in ("NAN", "NONE", ""):
        return "--"
    s = s.rstrip("& ").strip()
    s = s.rstrip(",").strip()
    return s


def redact(val):
    s = str(val).strip()
    if not s or s.upper() in ("NAN", "NONE", "", "--"):
        return "--"
    return "X" * min(len(s), 14)


def build_talking_points(row):
    """Generate rich, specific talking points from the data."""
    points = []
    props = int(float(str(row.get("props", row.get("property_count", 1)))))
    portfolio_val = float(str(row.get("total_portfolio_value", 0)).replace(",", ""))
    is_entity = str(row.get("is_entity", "")).upper() == "TRUE"
    refi_priority = str(row.get("refi_priority", "")).lower()
    out_of_state = str(row.get("out_of_state", "")).upper() == "TRUE"
    cashout = float(str(row.get("max_cashout_75", row.get("portfolio_cashout_75", 0))).replace(",", "").replace("$", "") or 0)
    lender = fmt_val(row.get("attom_lender_name", row.get("best_lender", "")))
    rate_type = fmt_val(row.get("attom_rate_type", ""))
    recent = fmt_val(row.get("most_recent_purchase_date", row.get("most_recent_purchase", "")))
    purchases_12 = int(float(str(row.get("purchases_last_12mo", 0)) or 0))
    equity = float(str(row.get("estimated_equity", 0)).replace(",", "").replace("$", "") or 0)
    rent = float(str(row.get("est_annual_rent", 0)).replace(",", "").replace("$", "") or 0)
    brrrr = str(row.get("brrrr_exit_candidate", "")).upper() == "TRUE"
    equity_harvest = str(row.get("equity_harvest_candidate", "")).upper() == "TRUE"

    # Portfolio size context
    if props >= 10:
        points.append(f"Institutional-scale investor with {props} properties and a ${portfolio_val:,.0f} portfolio.")
    elif props >= 5:
        points.append(f"Established portfolio landlord managing {props} investment properties worth ${portfolio_val:,.0f}.")
    elif props >= 2:
        points.append(f"Active investor building a {props}-property portfolio valued at ${portfolio_val:,.0f} -- likely looking to scale.")

    # Entity structure
    if is_entity:
        points.append("Entity-structured ownership (LLC/Trust) indicates sophistication and familiarity with non-QM lending.")

    # Geographic signal
    if out_of_state:
        points.append("Out-of-state investor managing remotely -- values efficiency and may prefer streamlined DSCR process over conventional.")

    # Financing opportunities
    if lender != "--" and rate_type != "--":
        points.append(f"Current financing through {lender} ({rate_type.lower()}).")
    elif lender != "--":
        points.append(f"Current financing through {lender}.")

    if cashout > 100000:
        points.append(f"Significant cash-out refi potential: up to ${cashout:,.0f} available at 75% LTV.")
    elif equity > 200000:
        points.append(f"Substantial equity position (${equity:,.0f}) across portfolio -- cash-out refi conversation opportunity.")

    if brrrr:
        points.append("Recent below-market acquisition suggests BRRRR strategy -- may need DSCR exit financing.")

    if equity_harvest:
        points.append("Long-held properties with accumulated equity -- prime candidate for equity harvest via DSCR cash-out refi.")

    # Activity signals
    if purchases_12 >= 2:
        points.append(f"Highly active: {purchases_12} acquisitions in the past 12 months -- likely needs ongoing acquisition financing.")
    elif purchases_12 == 1:
        points.append("Recent acquisition indicates active investment posture -- acquisition financing conversation timely.")

    # Rental income
    if rent > 50000:
        points.append(f"Estimated ${rent:,.0f}/year rental income supports strong DSCR qualification.")

    if refi_priority in ("high",):
        points.append("Flagged as HIGH refinance priority based on rate environment and portfolio characteristics.")
    elif refi_priority in ("medium",):
        points.append("Moderate refinance opportunity based on current rate environment.")

    if not points:
        points.append("Confirmed investment property owner with active portfolio -- DSCR lending conversation opportunity.")

    return " ".join(points)


class DossierPDF(FPDF):

    def __init__(self):
        super().__init__(orientation="P", unit="mm", format="letter")
        self.set_auto_page_break(auto=True, margin=18)

    def _section_title(self, title):
        self.ln(0.5)
        self.set_font("Helvetica", "B", 8.5)
        self.set_text_color(*NAVY)
        self.cell(0, 5, title.upper(), new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(*NAVY)
        self.set_line_width(0.3)
        self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
        self.ln(2)

    def _data_row(self, label, value, alt=False):
        if alt:
            self.set_fill_color(*ROW_ALT)
            fill = True
        else:
            fill = False
        self.set_font("Helvetica", "", 8)
        self.set_text_color(*GRAY)
        self.cell(55, 5, label, fill=fill, new_x="END")
        self.set_font("Helvetica", "B", 8)
        self.set_text_color(*DARK)
        self.cell(0, 5, str(value)[:80], fill=fill, new_x="LMARGIN", new_y="NEXT")

    def _two_col_row(self, l1, v1, l2, v2, alt=False):
        if alt:
            self.set_fill_color(*ROW_ALT)
            fill = True
        else:
            fill = False
        col_w = (self.w - self.l_margin - self.r_margin) / 2

        # Left column
        self.set_font("Helvetica", "", 8)
        self.set_text_color(*GRAY)
        self.cell(38, 5, l1, fill=fill, new_x="END")
        self.set_font("Helvetica", "B", 8.5)
        self.set_text_color(*DARK)
        self.cell(col_w - 38, 5, str(v1)[:35], fill=fill, new_x="END")

        # Right column
        self.set_font("Helvetica", "", 8)
        self.set_text_color(*GRAY)
        self.cell(38, 5, l2, fill=fill, new_x="END")
        self.set_font("Helvetica", "B", 8.5)
        self.set_text_color(*DARK)
        self.cell(0, 5, str(v2)[:35], fill=fill, new_x="LMARGIN", new_y="NEXT")


def generate_dossier(row, output_path, is_redacted=False):
    pdf = DossierPDF()
    pdf.add_page()
    pdf.set_margins(18, 15, 18)
    pdf.set_x(18)

    r = lambda v: redact(v) if is_redacted else v

    owner = clean_owner_name(row.get("OWN_NAME", ""))
    segment = fmt_val(row.get("selling_segment", row.get("_icp", "")))
    tier = fmt_val(row.get("selling_tier", ""))
    score = float(str(row.get("score", row.get("_score", 0))) or 0)
    props = fmt_val(row.get("props", row.get("property_count", "")))
    portfolio_val = fmt_currency(row.get("total_portfolio_value", ""))

    # === HEADER BAR ===
    # Navy header bar
    pdf.set_fill_color(*NAVY)
    pdf.rect(0, 0, pdf.w, 28, style="F")

    # Title text on navy
    pdf.set_xy(18, 6)
    pdf.set_font("Helvetica", "B", 16)
    pdf.set_text_color(*WHITE)
    pdf.cell(0, 8, "DSCR INVESTOR INTELLIGENCE", new_x="LMARGIN", new_y="NEXT")
    pdf.set_x(18)
    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(180, 200, 255)
    pdf.cell(0, 4, "Investor Dossier  |  Palm Beach County, FL  |  Confidential", new_x="LMARGIN", new_y="NEXT")

    # Score badge (right side of header)
    score_color = GREEN if score >= 50 else AMBER if score >= 30 else RED
    badge_size = 20
    badge_x = pdf.w - 18 - badge_size
    badge_y = 4
    pdf.set_fill_color(*score_color)
    pdf.rect(badge_x, badge_y, badge_size, badge_size, style="F")
    pdf.set_xy(badge_x, badge_y + 2)
    pdf.set_font("Helvetica", "B", 18)
    pdf.set_text_color(*WHITE)
    pdf.cell(badge_size, 10, str(int(score)), align="C")

    # Tier label below score
    tier_short = "HOT" if "Hot" in str(tier) or "1" in str(tier) else "WARM"
    pdf.set_xy(badge_x - 2, badge_y + badge_size + 1)
    pdf.set_font("Helvetica", "B", 7)
    pdf.set_text_color(*WHITE)
    pdf.cell(badge_size + 4, 4, tier_short, align="C")

    # Move below header
    pdf.set_y(32)
    pdf.set_x(18)

    # === OWNER NAME + SEGMENT ===
    pdf.set_font("Helvetica", "B", 16)
    pdf.set_text_color(*DARK)
    display_name = r(owner) if is_redacted else owner
    pdf.cell(0, 9, display_name, new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("Helvetica", "", 8.5)
    pdf.set_text_color(*GRAY)
    pdf.cell(0, 4, f"{segment}  |  {props} Properties  |  {portfolio_val} Portfolio", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    # === CONTACT INFORMATION ===
    pdf._section_title("Contact Information")
    phone1 = fmt_phone(row.get("phone_1", ""))
    phone1_type_raw = str(row.get("phone_1_type", "")).strip()
    phone1_type = phone1_type_raw if phone1_type_raw and phone1_type_raw.upper() not in ("NAN", "NONE", "", "--") else ""
    phone_display = f"{r(phone1)}" + (f"  ({phone1_type})" if phone1_type else "")
    email1 = fmt_val(row.get("email_1", ""))
    email2 = fmt_val(row.get("email_2", ""))
    phone2_raw = fmt_phone(row.get("phone_2", ""))
    # Deduplicate phones
    phone2 = phone2_raw if phone2_raw != phone1 and phone2_raw != "--" else "--"

    pdf._data_row("Primary Phone", phone_display)
    if phone2 != "--":
        pdf._data_row("Secondary Phone", r(phone2), alt=True)
    pdf._data_row("Email", r(email1), alt=(phone2 == "--"))
    if email2 != "--":
        pdf._data_row("Email 2", r(email2), alt=True)

    mail_addr = fmt_val(row.get("OWN_ADDR1", row.get("mail_street", "")))
    mail_city = fmt_val(row.get("OWN_CITY", row.get("mail_city", "")))
    mail_state = fmt_val(row.get("OWN_STATE_DOM", row.get("mail_state", "")))
    mail_zip = fmt_val(row.get("OWN_ZIPCD", row.get("mail_zip", "")))
    full_mail = f"{r(mail_addr)}, {mail_city}, {mail_state} {mail_zip}"
    pdf._data_row("Mailing Address", full_mail, alt=True)
    pdf.ln(0.5)

    # === PORTFOLIO OVERVIEW ===
    pdf._section_title("Portfolio Overview")
    pdf._two_col_row("Properties Owned", props, "Portfolio Value", portfolio_val)
    pdf._two_col_row("Avg Property Value", fmt_currency(row.get("avg_property_value", "")),
                     "Property Types", fmt_prop_types(row.get("property_types", "")), alt=True)
    pdf._two_col_row("Estimated Equity", fmt_currency(row.get("estimated_equity", "")),
                     "Equity Ratio", fmt_pct(row.get("equity_ratio", "")))
    pdf.ln(0.5)

    # === FINANCING INTELLIGENCE ===
    pdf._section_title("Financing Intelligence")
    lender = fmt_val(row.get("attom_lender_name", row.get("best_lender", "")))
    loan_amt = fmt_currency(row.get("attom_loan_amount", ""))
    rate_type = fmt_val(row.get("attom_rate_type", ""))
    loan_date = fmt_val(row.get("attom_loan_date", ""))
    due_date = fmt_val(row.get("attom_due_date", row.get("est_maturity_date", "")))
    cashout = fmt_currency(row.get("max_cashout_75", row.get("portfolio_cashout_75", "")))
    est_rate_raw = fmt_val(row.get("est_interest_rate", ""))
    # Add % to interest rate if it's a number
    try:
        est_rate = f"{float(est_rate_raw):.1f}%" if est_rate_raw != "--" else "--"
    except (ValueError, TypeError):
        est_rate = est_rate_raw
    est_balance = fmt_currency(row.get("est_remaining_balance", ""))

    fin_rows = [
        ("Current Lender", lender, "Loan Amount", loan_amt, False),
        ("Rate Type", rate_type, "Origination Date", loan_date, True),
        ("Est. Interest Rate", est_rate, "Maturity Date", due_date, False),
        ("Est. Remaining Balance", est_balance, "Cash-Out (75% LTV)", cashout, True),
    ]
    for l1, v1, l2, v2, alt in fin_rows:
        if v1 != "--" or v2 != "--":
            pdf._two_col_row(l1, v1, l2, v2, alt=alt)
    pdf.ln(0.5)

    # === ACQUISITION BEHAVIOR ===
    pdf._section_title("Acquisition Behavior")
    pdf._two_col_row("Most Recent Purchase", fmt_val(row.get("most_recent_purchase_date", row.get("most_recent_purchase", ""))),
                     "Purchase Price", fmt_currency(row.get("most_recent_purchase_price", row.get("most_recent_price", ""))))
    pdf._two_col_row("Purchases (12 mo)", fmt_val(row.get("purchases_last_12mo", "")),
                     "Purchases (36 mo)", fmt_val(row.get("purchases_last_36mo", "")), alt=True)
    pdf._two_col_row("Avg Purchase Price", fmt_currency(row.get("avg_purchase_price", row.get("avg_sale_price", ""))),
                     "Cash Purchase %", fmt_pct(row.get("cash_purchase_pct", "")))

    # Hold period info
    hold_period = fmt_val(row.get("avg_hold_period_months", ""))
    flip_count = fmt_val(row.get("flip_count", ""))
    hold_count = fmt_val(row.get("hold_count", ""))
    if hold_period != "--":
        flip_hold = f"{flip_count} flips / {hold_count} holds" if flip_count != "--" else "--"
        pdf._two_col_row("Avg Hold Period", f"{hold_period} months", "Flip vs Hold", flip_hold, alt=True)
    pdf.ln(0.5)

    # === ENTITY DETAILS (if applicable) ===
    is_entity = str(row.get("is_entity", "")).upper() == "TRUE"
    if is_entity:
        pdf._section_title("Entity Details")
        officers = fmt_val(row.get("entity_officers", row.get("officer_names", "")))
        agent = fmt_val(row.get("registered_agent_name", row.get("registered_agent", "")))
        status = fmt_val(row.get("entity_status", row.get("sunbiz_status", "")))
        entity_count = fmt_val(row.get("entity_count", row.get("sunbiz_entity_count", "")))

        pdf._data_row("Officers / Directors", r(officers))
        pdf._data_row("Registered Agent", r(agent), alt=True)
        pdf._two_col_row("Entity Status", status, "Related Entities", entity_count)
        pdf.ln(0.5)

    # === RENTAL & DSCR ANALYSIS ===
    rent = fmt_currency(row.get("est_annual_rent", ""))
    noi = fmt_currency(row.get("est_noi", ""))
    dscr = fmt_val(row.get("est_dscr", ""))
    debt_svc = fmt_currency(row.get("est_monthly_debt_service", ""))

    if rent != "--" or dscr != "--":
        pdf._section_title("Rental & DSCR Analysis")
        pdf._two_col_row("Est. Annual Rent", rent, "Est. NOI", noi)
        pdf._two_col_row("Est. Monthly Debt Service", debt_svc, "Est. DSCR", dscr, alt=True)
        pdf.ln(0.5)

    # === OPPORTUNITY SIGNALS ===
    pdf._section_title("Opportunity Signals")
    refi_priority = fmt_val(row.get("refi_priority", ""))
    refi_signals = fmt_val(row.get("refi_signals", row.get("est_refi_signals", "")))

    # Color-code refi priority
    pdf._data_row("Refinance Priority", refi_priority)
    if refi_signals != "--":
        pdf._data_row("Signal Details", refi_signals[:100], alt=True)

    # Boolean signals
    signals = []
    if str(row.get("brrrr_exit_candidate", "")).upper() == "TRUE":
        signals.append("BRRRR Exit Candidate")
    if str(row.get("equity_harvest_candidate", "")).upper() == "TRUE":
        signals.append("Equity Harvest Candidate")
    if str(row.get("rate_refi_candidate", "")).upper() == "TRUE":
        signals.append("Rate Refi Candidate")
    if str(row.get("probable_cash_buyer", "")).upper() == "TRUE":
        signals.append("Probable Cash Buyer")
    if str(row.get("str_licensed", "")).upper() == "TRUE":
        signals.append("STR Licensed")
    if signals:
        pdf._data_row("Active Signals", " | ".join(signals), alt=True)
    pdf.ln(0.5)

    # === WEALTH SIGNALS (if available) ===
    fec = fmt_currency(row.get("fec_total_donated", ""))
    if fec != "--":
        pdf._section_title("Wealth Signals")
        pdf._data_row("Political Donations (FEC)", fec)
        pdf._data_row("Recipients", fmt_val(row.get("fec_recipients", "")), alt=True)
        pdf.ln(0.5)

    # === WHY THIS LEAD MATTERS ===
    talking = build_talking_points(row)

    # Check if we need a new page
    if pdf.get_y() > 230:
        pdf.add_page()

    y_start = pdf.get_y() + 2
    pdf.set_fill_color(*LIGHT_BG)
    pdf.set_draw_color(*NAVY)

    # Calculate height needed
    pdf.set_font("Helvetica", "", 8.5)
    content_w = pdf.w - pdf.l_margin - pdf.r_margin - 8
    # Estimate lines needed
    words = talking.split()
    line_chars = int(content_w / 1.8)
    est_lines = max(2, len(talking) // line_chars + 2)
    box_h = 8 + (est_lines * 4.5)

    pdf.rect(pdf.l_margin, y_start, pdf.w - pdf.l_margin - pdf.r_margin, box_h, style="F")
    pdf.set_line_width(0.5)
    pdf.line(pdf.l_margin, y_start, pdf.l_margin, y_start + box_h)

    pdf.set_xy(pdf.l_margin + 4, y_start + 2)
    pdf.set_font("Helvetica", "B", 8.5)
    pdf.set_text_color(*NAVY)
    pdf.cell(0, 5, "WHY THIS LEAD MATTERS", new_x="LMARGIN", new_y="NEXT")
    pdf.set_x(pdf.l_margin + 4)
    pdf.set_font("Helvetica", "", 8.5)
    pdf.set_text_color(*DARK)
    pdf.multi_cell(content_w, 4.5, talking, new_x="LMARGIN", new_y="NEXT")

    # === FOOTER ===
    pdf.set_y(max(pdf.get_y() + 8, 255))
    pdf.set_draw_color(*BORDER)
    pdf.set_line_width(0.2)
    pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())
    pdf.ln(2)
    pdf.set_font("Helvetica", "", 6.5)
    pdf.set_text_color(*LIGHT_GRAY)
    footer = "SAMPLE -- Contact data available with subscription" if is_redacted else "Confidential -- Prepared for authorized recipient only"
    pdf.cell(0, 3, f"DSCR Investor Intelligence  |  Proprietary Scoring & Analysis  |  {footer}", align="C")

    pdf.output(str(output_path))


def build_csv_export(df, output_path):
    """Build a clean CRM-ready CSV export."""
    export_cols = {
        "OWN_NAME": "Owner Name",
        "selling_segment": "Investor Segment",
        "selling_tier": "Lead Tier",
        "score": "ICP Score",
        "property_count": "Properties Owned",
        "total_portfolio_value": "Portfolio Value",
        "avg_property_value": "Avg Property Value",
        "estimated_equity": "Est Equity",
        "equity_ratio": "Equity Ratio",
        "phone_1": "Phone 1",
        "phone_1_type": "Phone 1 Type",
        "phone_2": "Phone 2",
        "email_1": "Email 1",
        "email_2": "Email 2",
        "OWN_ADDR1": "Mailing Street",
        "OWN_CITY": "Mailing City",
        "OWN_STATE_DOM": "Mailing State",
        "OWN_ZIPCD": "Mailing Zip",
        "PHY_ADDR1": "Property Address",
        "property_types": "Property Types",
        "attom_lender_name": "Current Lender",
        "attom_loan_amount": "Loan Amount",
        "attom_rate_type": "Rate Type",
        "attom_loan_date": "Loan Date",
        "attom_due_date": "Maturity Date",
        "est_interest_rate": "Est Interest Rate",
        "est_remaining_balance": "Est Remaining Balance",
        "most_recent_purchase_date": "Last Purchase Date",
        "most_recent_purchase_price": "Last Purchase Price",
        "purchases_last_12mo": "Purchases (12 mo)",
        "purchases_last_36mo": "Purchases (36 mo)",
        "avg_purchase_price": "Avg Purchase Price",
        "cash_purchase_pct": "Cash Purchase %",
        "max_cashout_75": "Cash-Out Potential (75% LTV)",
        "refi_priority": "Refi Priority",
        "refi_signals": "Refi Signals",
        "est_dscr": "Est DSCR",
        "est_annual_rent": "Est Annual Rent",
        "est_noi": "Est NOI",
        "is_entity": "Entity Owned",
        "entity_officers": "Entity Officers",
        "registered_agent_name": "Registered Agent",
        "entity_status": "Entity Status",
        "fec_total_donated": "FEC Donations",
        "brrrr_exit_candidate": "BRRRR Candidate",
        "equity_harvest_candidate": "Equity Harvest Candidate",
        "rate_refi_candidate": "Rate Refi Candidate",
        "str_licensed": "STR Licensed",
    }

    export = pd.DataFrame()
    for src_col, dst_col in export_cols.items():
        if src_col in df.columns:
            export[dst_col] = df[src_col]
        else:
            export[dst_col] = ""

    # Clean owner names in export
    if "Owner Name" in export.columns:
        export["Owner Name"] = export["Owner Name"].apply(clean_owner_name)

    # Format property types
    if "Property Types" in export.columns:
        export["Property Types"] = export["Property Types"].apply(fmt_prop_types)

    export.to_csv(output_path, index=False)
    return export


def main():
    parser = argparse.ArgumentParser(description="Generate DSCR investor dossier PDFs + CRM CSV")
    parser.add_argument("--input", type=str, required=True, help="Input CSV with enriched lead data")
    parser.add_argument("--output-dir", type=str, default=None, help="Output directory")
    parser.add_argument("--redacted", action="store_true", help="Redact PII for sales samples")
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.is_absolute():
        input_path = PROJECT_DIR / args.input

    if not input_path.exists():
        print(f"Input file not found: {input_path}")
        return

    if args.output_dir:
        output_dir = Path(args.output_dir)
    else:
        output_dir = PROJECT_DIR / "data" / "dossiers"
    output_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(input_path, dtype=str)
    print(f"Generating {'redacted ' if args.redacted else ''}dossiers for {len(df)} leads...")
    print()

    for i, (_, row) in enumerate(df.iterrows()):
        owner = clean_owner_name(str(row.get("OWN_NAME", f"lead_{i}")))
        safe_name = "".join(c if c.isalnum() or c in " _-" else "_" for c in owner)[:40].strip()
        suffix = "_redacted" if args.redacted else ""
        filename = f"dossier_{i+1:02d}_{safe_name}{suffix}.pdf"
        pdf_path = output_dir / filename

        generate_dossier(row, pdf_path, is_redacted=args.redacted)
        print(f"  [{i+1}/{len(df)}] {pdf_path.name}")

    # Also generate CRM CSV
    csv_path = output_dir / ("crm_export_redacted.csv" if args.redacted else "crm_export.csv")
    export = build_csv_export(df, csv_path)
    print(f"\n  CRM CSV: {csv_path.name} ({len(export)} leads, {len(export.columns)} columns)")

    print(f"\nDone. {len(df)} PDFs + 1 CSV saved to {output_dir}/")


if __name__ == "__main__":
    main()
