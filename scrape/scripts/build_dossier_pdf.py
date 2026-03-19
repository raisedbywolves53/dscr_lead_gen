"""
DSCR Investor Dossier — Visual Sales Brief PDF Generator
=========================================================

Professional single-page investor intelligence dossier using fpdf2 + matplotlib.
Redesigned for clean, professional presentation to branch managers and loan officers.

3-Act Story Flow:
  Act 1: "Who is this?" — Header bar + KPI cards (skipped for sparse data)
  Act 2: "What do they own?" — Contact/signals + charts + property table
  Act 3: "How to win the business" — Talking points + acquisition history

Usage:
    python scripts/build_dossier_pdf.py --input data/enriched/fl_client_samples.csv
    python scripts/build_dossier_pdf.py --input data/enriched/fl_client_samples.csv --redacted
"""

import argparse
import math
import os
import sys
import tempfile
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyArrow
import numpy as np
import pandas as pd
from fpdf import FPDF

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent

# ── Logo Path ───────────────────────────────────────────────────────
LOGO_PATH = PROJECT_DIR / "assets" / "logo.png"

# ── Color Palette ────────────────────────────────────────────────────
NAVY = (10, 35, 66)           # Deep navy — header, section titles
TEAL = (26, 107, 106)         # Teal from brand logo — accent color
ACCENT = (0, 102, 179)        # Bright blue — metric numbers, highlights
BLACK = (33, 33, 33)          # Body text (soft black)
DARK_GRAY = (89, 89, 89)      # Labels, captions
MED_GRAY = (153, 153, 153)    # Dividers, borders
LIGHT_BG = (237, 241, 247)    # Card backgrounds (visible against white)
ALT_ROW = (248, 249, 251)     # Alternating table rows
WHITE = (255, 255, 255)
GREEN = (34, 139, 34)         # Positive / equity
AMBER = (204, 136, 0)         # Caution / medium
RED = (191, 49, 49)           # Negative / debt
LIGHT_TEAL_BG = (240, 248, 247)    # Teal-tinted background for sparse data
LIGHT_BLUE_ROW = (220, 235, 252)  # Totals row

# ── Page Layout ─────────────────────────────────────────────────────
L_MARGIN = 10
R_MARGIN = 10
PAGE_W = 215.9
PAGE_H = 279.4
USABLE_W = PAGE_W - L_MARGIN - R_MARGIN  # 195.9mm
COL_GUTTER = 5
COL_W = (USABLE_W - COL_GUTTER) / 2     # ~95.45mm each

# ── Florida County Codes → Names ───────────────────────────────────
FL_COUNTY_MAP = {
    "1": "Alachua", "2": "Baker", "3": "Bay", "4": "Bradford", "5": "Brevard",
    "6": "Broward", "7": "Calhoun", "8": "Charlotte", "9": "Citrus", "10": "Clay",
    "11": "Collier", "12": "Columbia", "13": "Dade", "14": "DeSoto", "15": "Dixie",
    "16": "Duval", "17": "Escambia", "18": "Flagler", "19": "Franklin", "20": "Gadsden",
    "21": "Gilchrist", "22": "Glades", "23": "Gulf", "24": "Hamilton", "25": "Hardee",
    "26": "Hendry", "27": "Hernando", "28": "Highlands", "29": "Hillsborough",
    "30": "Holmes", "31": "Indian River", "32": "Jackson", "33": "Jefferson",
    "34": "Lafayette", "35": "Lake", "36": "Lee", "37": "Leon", "38": "Levy",
    "39": "Liberty", "40": "Madison", "41": "Manatee", "42": "Marion", "43": "Martin",
    "44": "Monroe", "45": "Nassau", "46": "Okaloosa", "47": "Okeechobee",
    "48": "Orange", "49": "Osceola", "50": "Palm Beach", "51": "Pasco",
    "52": "Pinellas", "53": "Polk", "54": "Putnam", "55": "Santa Rosa",
    "56": "Sarasota", "57": "Seminole", "58": "St. Johns", "59": "St. Lucie",
    "60": "Palm Beach", "61": "Sumter", "62": "Suwannee", "63": "Taylor",
    "64": "Union", "65": "Volusia", "66": "Wakulla", "67": "Walton",
    "68": "Washington",
}

NC_COUNTY_MAP = {
    "wake": "Wake", "mecklenburg": "Mecklenburg", "durham": "Durham",
    "guilford": "Guilford", "forsyth": "Forsyth", "cumberland": "Cumberland",
}

STATE_ABBREV = {
    "FL": "Florida", "NC": "North Carolina", "GA": "Georgia", "TX": "Texas",
    "CA": "California", "NY": "New York", "SC": "South Carolina",
}

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


def display_name(raw_name):
    """
    Convert "LAST FIRST M &" to "First M. Last" display format.
    Entity names (LLC, Corp, Trust, Inc, etc.) are kept as-is in title case.
    """
    if not raw_name:
        return "Unknown"

    # Clean: remove trailing &, commas, extra whitespace
    s = str(raw_name).strip().rstrip("& ").rstrip(",").strip()
    if not s or s.upper() in ("NAN", "NONE"):
        return "Unknown"

    # Detect entity names — don't reorder these, just title case
    entity_markers = ["LLC", "L.L.C", "INC", "CORP", "TRUST", "LTD", "LP",
                      "L.P.", "REALTY", "PROPERTIES", "INVESTMENTS", "HOLDINGS",
                      "PARTNERS", "GROUP", "VENTURES", "CAPITAL", "MANAGEMENT",
                      "ASSOCIATES", "ENTERPRISES", "DEVELOPMENT", "FOUNDATION"]
    upper = s.upper()
    if any(marker in upper for marker in entity_markers):
        # Title case but preserve LLC, INC, etc. as uppercase
        result = s.title()
        for marker in ["Llc", "L.L.C", "Inc", "Corp", "Ltd", "Lp", "L.P."]:
            result = result.replace(marker, marker.upper())
        return result

    # Split by whitespace
    parts = s.split()
    if not parts:
        return "Unknown"

    # If only one part, return as-is (title cased)
    if len(parts) == 1:
        return parts[0].title()

    # Person name: LAST FIRST or LAST FIRST M
    last = parts[0].title()
    first_middle = " ".join(parts[1:]).title()

    # Condense middle initials: "Todd S" stays "Todd S."
    first_middle_parts = first_middle.split()
    if len(first_middle_parts) > 1:
        result = first_middle_parts[0]
        for p in first_middle_parts[1:]:
            if len(p) == 1:
                result += f" {p}."
            else:
                result += f" {p}"
        first_middle = result

    return f"{first_middle} {last}" if first_middle else last


def redact(val):
    if not val:
        return None
    return "X" * min(len(str(val)), 12)


def sanitize_for_pdf(val):
    """Remove characters that fpdf2 Helvetica font cannot render."""
    if not val:
        return val
    s = str(val)
    # Replace em-dashes and other problematic characters with ASCII equivalents
    s = s.replace("—", "-")  # em-dash
    s = s.replace("–", "-")  # en-dash
    s = s.replace("…", "...")  # ellipsis
    return s


def get_county_state(row):
    """Derive county + state string dynamically from row data."""
    state = fv(row.get("OWN_STATE_DOM", "")) or fv(row.get("OWN_STATE", ""))
    co_no = str(row.get("CO_NO", "")).strip()

    county = None
    if state and state.upper() == "FL" and co_no:
        county = FL_COUNTY_MAP.get(co_no)
    # Try NC county field if present
    if not county:
        county_raw = fv(row.get("county", "")) or fv(row.get("county_name", ""))
        if county_raw:
            county = county_raw.title()

    if county and state:
        return f"{county} County, {state.upper()}"
    elif state:
        return state.upper()
    return ""


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


# ════════════════════════════════════════════════════════════════════
# CHART GENERATORS (matplotlib → temp PNG → embed in PDF)
# ════════════════════════════════════════════════════════════════════

def _hex(rgb):
    """Convert (r,g,b) tuple to hex string for matplotlib."""
    return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"


def render_score_donut(score, tmpdir, size_px=220):
    """Render a clean partial-ring donut chart with score centered."""
    fig, ax = plt.subplots(figsize=(1.8, 1.8), dpi=150)
    fig.patch.set_alpha(0)
    ax.set_aspect("equal")

    # Color by tier — use navy for new/pending leads
    if score == 0:
        color = _hex(MED_GRAY)
        label = "NEW"
    elif score >= 50:
        color = _hex(GREEN)
        label = "HOT"
    elif score >= 30:
        color = _hex(AMBER)
        label = "WARM"
    else:
        color = _hex(RED)
        label = "ACTIVE"

    # Background ring (light gray)
    theta = np.linspace(0, 2 * np.pi, 100)
    ax.plot(np.cos(theta), np.sin(theta), color="#d9d9d9", linewidth=11, solid_capstyle="round")

    # Score arc (0-100 maps to 0-360 degrees)
    if score > 0:
        pct = min(score / 100, 1.0)
        theta_score = np.linspace(np.pi/2, np.pi/2 - 2*np.pi*pct, 100)
        ax.plot(np.cos(theta_score), np.sin(theta_score), color=color, linewidth=11, solid_capstyle="round")

    # Center text
    ax.text(0, 0.05, str(int(score)), ha="center", va="center",
            fontsize=26, fontweight="bold", color=color, fontfamily="sans-serif")
    ax.text(0, -0.35, "SCORE", ha="center", va="center",
            fontsize=7.5, color="#555555", fontfamily="sans-serif", fontweight="bold")

    ax.set_xlim(-1.5, 1.5)
    ax.set_ylim(-1.5, 1.5)
    ax.axis("off")

    path = os.path.join(tmpdir, "score_donut.png")
    fig.savefig(path, transparent=True, bbox_inches="tight", pad_inches=0.05)
    plt.close(fig)
    return path


def render_equity_debt_bar(equity_val, debt_val, cashout_val, tmpdir):
    """Render a clean horizontal stacked bar: equity (green) vs debt (red)."""
    fig, ax = plt.subplots(figsize=(3.5, 1.1), dpi=150)
    fig.patch.set_alpha(0)

    total = equity_val + debt_val
    if total == 0:
        return None

    eq_pct = equity_val / total
    dt_pct = debt_val / total

    # Bars — no borders, clean colors
    bar_h = 0.5
    if equity_val > 0:
        ax.barh(0, eq_pct, height=bar_h, color=_hex(GREEN), edgecolor="none", left=0)
        if eq_pct > 0.15:
            ax.text(eq_pct / 2, 0, fc(equity_val) or "", ha="center", va="center",
                    fontsize=8.5, color="white", fontweight="bold", fontfamily="sans-serif")
    if debt_val > 0:
        ax.barh(0, dt_pct, height=bar_h, color=_hex(RED), edgecolor="none", left=eq_pct)
        if dt_pct > 0.15:
            ax.text(eq_pct + dt_pct / 2, 0, fc(debt_val) or "", ha="center", va="center",
                    fontsize=8.5, color="white", fontweight="bold", fontfamily="sans-serif")

    # Legend with percentages
    ax.text(0, -0.50, f"Equity ({eq_pct*100:.0f}%)", fontsize=6.5, color=_hex(GREEN),
            fontweight="bold", fontfamily="sans-serif")
    if debt_val > 0:
        ax.text(1.0, -0.50, f"Debt ({dt_pct*100:.0f}%)", fontsize=6.5, color=_hex(RED),
                fontweight="bold", fontfamily="sans-serif", ha="right")

    # Cash-out callout (if significant)
    if cashout_val and cashout_val > 0:
        ax.text(0.5, -0.88, f"Cash-out potential (75% LTV): {fc(cashout_val)}",
                ha="center", fontsize=7, color=_hex(NAVY), fontweight="bold",
                fontfamily="sans-serif")

    ax.set_xlim(0, 1)
    ax.set_ylim(-1.2, 0.5)
    ax.axis("off")

    path = os.path.join(tmpdir, "equity_debt.png")
    fig.savefig(path, transparent=True, bbox_inches="tight", pad_inches=0.05)
    plt.close(fig)
    return path


def render_dscr_gauge(dscr_val, rent_val, noi_val, tmpdir):
    """Render a professional semicircle gauge: red (<1.0) / amber (1.0-1.25) / green (>1.25)."""
    fig, ax = plt.subplots(figsize=(3.2, 1.6), dpi=150)
    fig.patch.set_alpha(0)
    ax.set_aspect("equal")

    # Draw zones as wedges
    # Map DSCR 0.5 to 2.5 across 180 degrees
    zones = [
        (0, 1.0, _hex(RED), "< 1.0"),
        (1.0, 1.25, _hex(AMBER), "1.0-1.25"),
        (1.25, 2.5, _hex(GREEN), "> 1.25"),
    ]

    for low, high, color, _ in zones:
        a1 = 180 - (low - 0.5) / 2.0 * 180
        a2 = 180 - (high - 0.5) / 2.0 * 180
        wedge = mpatches.Wedge((0, 0), 1.0, min(a1, a2), max(a1, a2),
                               width=0.3, facecolor=color, edgecolor="none")
        ax.add_patch(wedge)

    # Needle — clean dark line
    clamped = max(0.5, min(2.5, dscr_val))
    angle_deg = 180 - (clamped - 0.5) / 2.0 * 180
    angle_rad = math.radians(angle_deg)
    nx = 0.65 * math.cos(angle_rad)
    ny = 0.65 * math.sin(angle_rad)
    ax.plot([0, nx], [0, ny], color="#2c2c2c", linewidth=2.5, solid_capstyle="round")
    ax.plot(0, 0, "o", color="#2c2c2c", markersize=4)

    # Value display
    ax.text(0, -0.25, f"{dscr_val:.2f}", ha="center", va="center",
            fontsize=20, fontweight="bold", color=_hex(NAVY), fontfamily="sans-serif")
    ax.text(0, -0.5, "DSCR", ha="center", va="center",
            fontsize=7.5, color="#555555", fontfamily="sans-serif", fontweight="bold")

    # Rent + NOI summary (clean, subtle)
    parts = []
    if rent_val:
        parts.append(f"Rent: {fc(rent_val)}/yr")
    if noi_val:
        parts.append(f"NOI: {fc(noi_val)}/yr")
    if parts:
        ax.text(0, -0.72, " • ".join(parts), ha="center", fontsize=6.5,
                color="#555555", fontfamily="sans-serif")

    ax.set_xlim(-1.3, 1.3)
    ax.set_ylim(-0.85, 1.15)
    ax.axis("off")

    path = os.path.join(tmpdir, "dscr_gauge.png")
    fig.savefig(path, transparent=True, bbox_inches="tight", pad_inches=0.05)
    plt.close(fig)
    return path


# ════════════════════════════════════════════════════════════════════
# PDF BUILDER
# ════════════════════════════════════════════════════════════════════

class DossierPDF(FPDF):
    def __init__(self):
        super().__init__(orientation="P", unit="mm", format="letter")
        self.set_auto_page_break(auto=False)

    def _rounded_rect(self, x, y, w, h, r, style="F"):
        """Draw a rectangle with rounded corners."""
        self.set_line_width(0.1)
        # Use built-in rounded_rect if available (fpdf2 >= 2.7.6)
        if hasattr(self, 'rounded_rect'):
            self.rounded_rect(x, y, w, h, r, style=style)
        else:
            self.rect(x, y, w, h, style)

    def _kpi_card(self, x, y, w, h, value, label, accent_color=TEAL):
        """Draw a professional KPI metric card with colored top accent border."""
        # Card background fill
        self.set_fill_color(*LIGHT_BG)
        self.set_draw_color(200, 208, 218)
        self.set_line_width(0.3)
        self.rect(x, y, w, h, "FD")

        # Accent top border (thick, prominent)
        self.set_fill_color(*accent_color)
        self.rect(x, y, w, 2.0, "F")

        # Value (large, bold, navy for readability)
        self.set_font("Helvetica", "B", 20)
        self.set_text_color(*NAVY)
        self.set_xy(x, y + 3)
        self.cell(w, 8, str(value) if value else "-", align="C")

        # Label (small, uppercase, dark gray)
        self.set_font("Helvetica", "", 6.5)
        self.set_text_color(*DARK_GRAY)
        self.set_xy(x, y + 12.5)
        self.cell(w, 4, label.upper(), align="C")

    def _kpi_card_pending(self, x, y, w, h, label):
        """Draw a subtle 'data pending' KPI card."""
        # Card background
        self.set_fill_color(250, 250, 250)
        self.set_draw_color(220, 220, 220)
        self.set_line_width(0.2)
        self.rect(x, y, w, h, "FD")

        # Subtle accent
        self.set_fill_color(220, 225, 230)
        self.rect(x, y, w, 1.0, "F")

        # "Pending" text
        self.set_font("Helvetica", "", 7.5)
        self.set_text_color(180, 180, 180)
        self.set_xy(x, y + 5)
        self.cell(w, 5, "Pending", align="C")

        # Label
        self.set_font("Helvetica", "", 7)
        self.set_text_color(*DARK_GRAY)
        self.set_xy(x, y + 11)
        self.cell(w, 4, label.upper(), align="C")

    def _section_label(self, x, y, text, width):
        """Draw a section label with teal accent underline."""
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(*NAVY)
        self.set_xy(x, y)
        self.cell(width, 4.5, text.upper())
        # Teal accent line (short) + light gray line (rest of width)
        text_w = min(self.get_string_width(text) + 2, width * 0.4)
        self.set_draw_color(*TEAL)
        self.set_line_width(0.6)
        self.line(x, y + 5.5, x + text_w, y + 5.5)
        self.set_draw_color(210, 218, 228)
        self.set_line_width(0.2)
        self.line(x + text_w, y + 5.5, x + width, y + 5.5)
        return y + 8

    def _info_row(self, x, y, label, value, width, bold=True):
        """Draw a compact label: value row."""
        if value is None:
            return y
        self.set_font("Helvetica", "", 7)
        self.set_text_color(*DARK_GRAY)
        self.set_xy(x, y)
        lbl_w = 32
        self.cell(lbl_w, 3.8, label)
        style = "B" if bold else ""
        self.set_font("Helvetica", style, 7.5)
        self.set_text_color(*BLACK)
        self.set_xy(x + lbl_w, y)
        # Show "-" instead of "--" for missing values
        display_val = "-" if value == "--" else str(value)[:48]
        self.cell(width - lbl_w, 3.8, display_val)
        return y + 4.5

    def _signal_pill(self, x, y, text, color=ACCENT):
        """Draw a rounded colored signal pill badge."""
        self.set_font("Helvetica", "B", 6)
        tw = self.get_string_width(text) + 4.5
        pill_h = 4.5
        self.set_fill_color(*color)
        self.set_draw_color(*color)
        self.set_line_width(0)
        self.rect(x, y, tw, pill_h, "F")
        self.set_text_color(*WHITE)
        self.set_xy(x + 0.5, y + 0.3)
        self.cell(tw - 1, pill_h - 0.5, text, align="C")
        return x + tw + 2.5  # Return next x position with slight gap


def generate_dossier(row, output_path, is_redacted=False):
    """Generate a single professional visual sales brief PDF for one investor."""
    pdf = DossierPDF()
    pdf.add_page()

    r = lambda v: redact(v) if is_redacted and v else v

    # ── Extract Data ────────────────────────────────────────────
    owner_raw = clean_name(row.get("OWN_NAME", "")) or "Unknown"
    owner_display = display_name(owner_raw)  # Convert "LAST FIRST M" to "First M. Last"
    segment = fv(row.get("selling_segment", row.get("_icp", ""))) or "Investor"
    tier = fv(row.get("selling_tier", "")) or ""
    score = float(str(row.get("score", row.get("_score", 0))) or 0)
    props_str = fv(row.get("props", row.get("property_count", "")))
    props = int(float(props_str)) if props_str else 1
    portfolio_val = fc(row.get("total_portfolio_value", ""))
    avg_val = fc(row.get("avg_property_value", ""))
    equity_str = row.get("estimated_equity", "")
    equity = fc(equity_str)
    equity_pct = fp(row.get("equity_ratio", ""))

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
    dscr = fv(row.get("est_dscr", ""))
    rent = fc(row.get("est_annual_rent", ""))
    noi = fc(row.get("est_noi", ""))
    cashout = fc(row.get("max_cashout_75", row.get("portfolio_cashout_75", "")))

    is_entity = str(row.get("is_entity", "")).upper() == "TRUE"
    officers = fv(row.get("entity_officers", row.get("officer_names", "")))
    agent = fv(row.get("registered_agent_name", row.get("registered_agent", "")))
    entity_status = fv(row.get("entity_status", row.get("sunbiz_status", "")))

    # Numeric values for charts
    equity_num = 0
    try:
        equity_num = float(str(equity_str).replace(",", "").replace("$", "").strip() or 0)
        if math.isnan(equity_num):
            equity_num = 0
    except (ValueError, TypeError):
        pass

    loan_num = 0
    try:
        loan_num = float(str(row.get("attom_loan_amount", 0)).replace(",", "").replace("$", "").strip() or 0)
        if math.isnan(loan_num):
            loan_num = 0
    except (ValueError, TypeError):
        pass

    cashout_num = 0
    try:
        cashout_num = float(str(row.get("max_cashout_75", row.get("portfolio_cashout_75", 0))).replace(",", "").replace("$", "").strip() or 0)
        if math.isnan(cashout_num):
            cashout_num = 0
    except (ValueError, TypeError):
        pass

    dscr_num = 0
    try:
        dscr_num = float(str(row.get("est_dscr", 0)).strip() or 0)
        if math.isnan(dscr_num):
            dscr_num = 0
    except (ValueError, TypeError):
        pass

    rent_num = 0
    try:
        rent_num = float(str(row.get("est_annual_rent", 0)).replace(",", "").replace("$", "").strip() or 0)
        if math.isnan(rent_num):
            rent_num = 0
    except (ValueError, TypeError):
        pass

    noi_num = 0
    try:
        noi_num = float(str(row.get("est_noi", 0)).replace(",", "").replace("$", "").strip() or 0)
        if math.isnan(noi_num):
            noi_num = 0
    except (ValueError, TypeError):
        pass

    # Signals
    signals = []
    if str(row.get("brrrr_exit_candidate", "")).upper() == "TRUE":
        signals.append(("BRRRR EXIT", AMBER))
    if str(row.get("equity_harvest_candidate", "")).upper() == "TRUE":
        signals.append(("EQUITY HARVEST", GREEN))
    if str(row.get("rate_refi_candidate", "")).upper() == "TRUE":
        signals.append(("RATE REFI", ACCENT))
    if str(row.get("out_of_state", "")).upper() == "TRUE":
        signals.append(("OUT-OF-STATE", MED_GRAY))
    if str(row.get("str_licensed", "")).upper() == "TRUE":
        signals.append(("STR LICENSED", (100, 50, 150)))
    refi_priority = fv(row.get("refi_priority", ""))
    if refi_priority and refi_priority.lower() == "high":
        signals.append(("REFI PRIORITY", RED))

    county_state = get_county_state(row)
    display_name_final = r(owner_display) if is_redacted else owner_display

    # ── Determine if lead is sparse (new/enrichment-pending) ────
    has_contact = any([fphone(row.get(f, "")) for f in ["phone_1", "phone_2"]] +
                      [fv(row.get(f, "")) for f in ["email_1", "email_2"]])
    has_portfolio = bool(portfolio_val and portfolio_val != "-")
    is_sparse = score == 0 or (not has_contact and not has_portfolio)

    # ── Parse property addresses ────────────────────────────────
    phy_addr_raw = str(row.get("PHY_ADDR1", "")).strip()
    addresses = []
    if phy_addr_raw and phy_addr_raw.upper() not in ("NAN", "NONE", ""):
        addresses = [a.strip().title()[:40] for a in phy_addr_raw.split("|") if a.strip()]

    # ATTOM match address
    attom_addr = str(row.get("attom_property_address", "")).strip().upper()

    # ── Render charts to temp dir ───────────────────────────────
    tmpdir = tempfile.mkdtemp()
    score_chart = render_score_donut(score, tmpdir)

    eq_chart = None
    if equity_num > 0 or loan_num > 0:
        eq_chart = render_equity_debt_bar(equity_num, loan_num, cashout_num, tmpdir)

    dscr_chart = None
    if dscr_num > 0:
        dscr_chart = render_dscr_gauge(dscr_num, rent_num, noi_num, tmpdir)

    # ════════════════════════════════════════════════════════════
    # ACT 1: "WHO IS THIS?" — Header + KPI Cards (skip if sparse)
    # ════════════════════════════════════════════════════════════

    # Navy header band
    header_h = 24
    pdf.set_fill_color(*NAVY)
    pdf.rect(0, 0, PAGE_W, header_h, "F")
    # Thin teal accent strip below
    pdf.set_fill_color(*TEAL)
    pdf.rect(0, header_h, PAGE_W, 0.8, "F")

    # Logo (left)
    logo_end_x = L_MARGIN
    if LOGO_PATH.exists():
        try:
            pdf.image(str(LOGO_PATH), x=L_MARGIN, y=1.5, h=21)
            logo_end_x = L_MARGIN + 24
        except Exception:
            pass

    # Owner name (large, white, title case)
    pdf.set_xy(logo_end_x + 2, 2.5)
    pdf.set_font("Helvetica", "B", 16)
    pdf.set_text_color(*WHITE)
    pdf.cell(120, 7, display_name_final[:40])

    # Subtitle
    pdf.set_xy(logo_end_x + 2, 10.5)
    pdf.set_font("Helvetica", "", 7)
    pdf.set_text_color(180, 200, 225)
    subtitle = f"{segment}  |  {props} Properties  |  {county_state}"
    pdf.cell(130, 3.5, subtitle[:80])

    # Score donut + tier badge (top right)
    if score_chart:
        pdf.image(score_chart, x=PAGE_W - R_MARGIN - 42, y=0.5, h=23)

    # Tier badge (next to score donut)
    tier_label = "HOT" if "Hot" in str(tier) or "1" in str(tier) else ("NEW" if score == 0 else "WARM")
    if tier_label != "NEW":
        tier_bg = GREEN if tier_label == "HOT" else AMBER
        tier_x = PAGE_W - R_MARGIN - 14
        pdf.set_fill_color(*tier_bg)
        pdf.rect(tier_x, 4, 14, 16, "F")
        pdf.set_xy(tier_x, 5)
        pdf.set_font("Helvetica", "B", 8)
        pdf.set_text_color(*WHITE)
        pdf.cell(14, 13, tier_label, align="C")

    # ── KPI Cards Row (skip if sparse data) ───────────────────
    if not is_sparse:
        y_kpi = header_h + 3
        card_gap = 3
        card_count = 4
        card_w = (USABLE_W - (card_count - 1) * card_gap) / card_count
        card_h = 18

        metrics = [
            (portfolio_val or "-", "Portfolio Value"),
            (equity or "-", "Total Equity"),
            (equity_pct or "-", "Equity Ratio"),
            (dscr or "-", "Est. DSCR"),
        ]
        for i, (val, label) in enumerate(metrics):
            cx = L_MARGIN + i * (card_w + card_gap)
            if val == "-":
                pdf._kpi_card_pending(cx, y_kpi, card_w, card_h, label)
            else:
                pdf._kpi_card(cx, y_kpi, card_w, card_h, val, label, accent_color=TEAL)
        y_start = y_kpi + card_h + 4
    else:
        y_start = header_h + 3

    # ════════════════════════════════════════════════════════════
    # ACT 2: "WHAT DO THEY OWN?" — Contact + Charts + Table
    # ════════════════════════════════════════════════════════════

    y = y_start
    left_x = L_MARGIN
    right_x = L_MARGIN + COL_W + COL_GUTTER

    # ── LEFT PANEL: Contact + Entity + Signals ──────────────────
    ly = y
    ly = pdf._section_label(left_x, ly, "Contact Information", COL_W)

    has_contact_info = False
    if phone1:
        ptype = f" ({phone1_type})" if phone1_type else ""
        ly = pdf._info_row(left_x, ly, "Phone", f"{r(phone1)}{ptype}", COL_W)
        has_contact_info = True
    if phone2 and phone2 != phone1:
        ly = pdf._info_row(left_x, ly, "Phone 2", r(phone2), COL_W)
        has_contact_info = True
    if email1:
        ly = pdf._info_row(left_x, ly, "Email", r(email1), COL_W)
        has_contact_info = True
    if email2 and email2 != email1:
        ly = pdf._info_row(left_x, ly, "Email 2", r(email2), COL_W)
        has_contact_info = True
    if mail_addr:
        full_mail = f"{r(mail_addr)}"
        city_line = ", ".join(filter(None, [mail_city, mail_state]))
        if mail_zip:
            city_line += f" {mail_zip}"
        ly = pdf._info_row(left_x, ly, "Address", r(full_mail), COL_W)
        if city_line.strip():
            ly = pdf._info_row(left_x, ly, "", city_line.strip(", "), COL_W, bold=False)
        has_contact_info = True

    if not has_contact_info:
        # Show subtle "pending" message for sparse leads
        pdf.set_xy(left_x, ly + 1)
        pdf.set_font("Helvetica", "", 7)
        pdf.set_text_color(180, 180, 180)
        pdf.cell(COL_W, 3.5, "Contact enrichment pending")
        ly += 5

    ly += 2

    # Entity details
    if is_entity:
        ly = pdf._section_label(left_x, ly, "Entity Details", COL_W)
        ly = pdf._info_row(left_x, ly, "Agent", r(agent), COL_W)
        ly = pdf._info_row(left_x, ly, "Officers", r(officers), COL_W)
        ly = pdf._info_row(left_x, ly, "Status", entity_status, COL_W)
        ly += 2

    # Signal pills
    if signals:
        ly = pdf._section_label(left_x, ly, "Opportunity Signals", COL_W)
        pill_x = left_x
        pill_y = ly
        for sig_text, sig_color in signals:
            next_x = pdf._signal_pill(pill_x, pill_y, sig_text, sig_color)
            if next_x > left_x + COL_W - 5:
                pill_y += 6
                pill_x = left_x
                pill_x = pdf._signal_pill(pill_x, pill_y, sig_text, sig_color)
            else:
                pill_x = next_x
        ly = pill_y + 7

    # ── RIGHT PANEL: Charts or Financing Details ────────────────
    ry = y

    # Equity vs Debt bar
    if eq_chart:
        ry = pdf._section_label(right_x, ry, "Equity vs Debt", COL_W)
        pdf.image(eq_chart, x=right_x, y=ry, w=COL_W - 2, h=21)
        ry += 23

    # DSCR Gauge
    if dscr_chart:
        ry = pdf._section_label(right_x, ry, "DSCR Analysis", COL_W)
        pdf.image(dscr_chart, x=right_x + 8, y=ry, w=COL_W - 18, h=27)
        ry += 29

    # If no charts, show financing details as text
    if not eq_chart and not dscr_chart:
        ry = pdf._section_label(right_x, ry, "Financing Intelligence", COL_W)
        if lender:
            ry = pdf._info_row(right_x, ry, "Lender", lender, COL_W)
        if loan_amt:
            ry = pdf._info_row(right_x, ry, "Loan Amount", loan_amt, COL_W)
        if rate_type:
            ry = pdf._info_row(right_x, ry, "Rate Type", rate_type, COL_W)
        if dscr:
            ry = pdf._info_row(right_x, ry, "DSCR", dscr, COL_W)
        if rent:
            ry = pdf._info_row(right_x, ry, "Annual Rent", rent, COL_W)
        if cashout:
            ry = pdf._info_row(right_x, ry, "Cash-Out (75%)", cashout, COL_W)
        if not (lender or loan_amt or rate_type or dscr or rent or cashout):
            pdf.set_xy(right_x, ry + 1)
            pdf.set_font("Helvetica", "", 7)
            pdf.set_text_color(180, 180, 180)
            pdf.cell(COL_W, 3.5, "Enrichment pending")
            ry += 5

    # ── PROPERTY PORTFOLIO TABLE ────────────────────────────────
    table_y = max(ly, ry) + 3

    # Dynamic sizing based on portfolio
    if props <= 8:
        font_sz = 7
        row_h = 5.2
        max_rows = props
    elif props <= 15:
        font_sz = 6.5
        row_h = 4.5
        max_rows = props
    else:
        font_sz = 6
        row_h = 4
        max_rows = 10

    # Determine how many addresses we can show
    show_addrs = addresses[:max_rows]
    overflow = max(0, props - len(show_addrs))

    # Column widths: # | Address | Est. Value | Lender | Rate | Loan | Equity
    col_widths = [7, 68, 22, 30, 16, 22, USABLE_W - 7 - 68 - 22 - 30 - 16 - 22]
    headers = ["#", "Property Address", "Est. Value", "Lender", "Rate", "Loan", "Equity"]

    # Check if table fits on page
    needed = len(show_addrs) + 2  # header + rows + totals
    if overflow > 0:
        needed += 1
    table_bottom = table_y + 6 + needed * row_h

    # Ensure everything fits on one page (leave room for Act 3 + footer)
    max_table_bottom = 232
    if table_bottom > max_table_bottom:
        available_rows = int((max_table_bottom - table_y - 6 - row_h * 2) / row_h)
        show_addrs = addresses[:max(1, available_rows)]
        overflow = max(0, props - len(show_addrs))

    # Section label
    pdf._section_label(L_MARGIN, table_y, f"Property Portfolio ({props} Properties)", USABLE_W)
    table_y += 6

    # Header row (navy background)
    pdf.set_fill_color(*NAVY)
    pdf.set_font("Helvetica", "B", font_sz)
    pdf.set_text_color(*WHITE)
    x = L_MARGIN
    for i, (hdr, cw) in enumerate(zip(headers, col_widths)):
        pdf.set_xy(x, table_y)
        pdf.cell(cw, row_h, f" {hdr}", fill=True)
        x += cw
    table_y += row_h

    # Avg property value for per-property estimate
    avg_val_num = 0
    try:
        avg_val_num = float(str(row.get("avg_property_value", 0)).replace(",", "").replace("$", "").strip() or 0)
        if math.isnan(avg_val_num):
            avg_val_num = 0
    except (ValueError, TypeError):
        pass

    # Data rows
    total_value = 0
    total_loan = 0
    total_equity_table = 0

    for idx, addr in enumerate(show_addrs):
        is_alt = idx % 2 == 1
        if is_alt:
            pdf.set_fill_color(*ALT_ROW)
        else:
            pdf.set_fill_color(*WHITE)

        pdf.set_font("Helvetica", "", font_sz)
        pdf.set_text_color(*BLACK)

        # Check if this address matches ATTOM record
        is_attom_match = False
        if attom_addr:
            addr_upper = addr.upper().replace(",", "").strip()
            if addr_upper in attom_addr or attom_addr in addr_upper:
                is_attom_match = True

        prop_val = avg_val_num
        prop_lender = lender if is_attom_match else "—"
        prop_rate = rate_type if is_attom_match else "—"
        prop_loan = loan_num if is_attom_match else 0
        prop_equity = prop_val - prop_loan if prop_val > 0 else prop_val

        total_value += prop_val
        total_loan += prop_loan
        total_equity_table += prop_equity

        vals = [
            str(idx + 1),
            r(addr) if is_redacted else addr,
            fc(prop_val) or "-",
            prop_lender or "-",
            prop_rate or "-",
            fc(prop_loan) if prop_loan > 0 else "-",
            fc(prop_equity) if prop_equity > 0 else "-",
        ]

        x = L_MARGIN
        for i, (val, cw) in enumerate(zip(vals, col_widths)):
            pdf.set_xy(x, table_y)
            pdf.cell(cw, row_h, f" {sanitize_for_pdf(val)}", fill=True)
            x += cw
        table_y += row_h

    # Overflow row
    if overflow > 0:
        pdf.set_fill_color(*ALT_ROW)
        pdf.set_font("Helvetica", "I", font_sz)
        pdf.set_text_color(*DARK_GRAY)
        pdf.set_xy(L_MARGIN, table_y)
        pdf.cell(USABLE_W, row_h, f"  ...and {overflow} more properties", fill=True)
        table_y += row_h

    # Totals row — always use portfolio-level figures from the CSV
    # (visible row sums undercount when rows overflow)
    portfolio_val_total = fc(row.get("total_portfolio_value", "")) or fc(total_value) or "-"
    portfolio_equity_total = fc(equity_str) or fc(total_equity_table) or "-"
    portfolio_loan_total = fc(total_loan) if total_loan > 0 else "-"

    pdf.set_fill_color(*LIGHT_BLUE_ROW)
    pdf.set_font("Helvetica", "B", font_sz)
    pdf.set_text_color(*NAVY)

    totals = [
        "",
        f"TOTAL  |  {props} Properties",
        portfolio_val_total,
        "",
        "",
        portfolio_loan_total,
        portfolio_equity_total,
    ]

    x = L_MARGIN
    for i, (val, cw) in enumerate(zip(totals, col_widths)):
        pdf.set_xy(x, table_y)
        pdf.cell(cw, row_h + 0.5, f" {sanitize_for_pdf(val)}", fill=True)
        x += cw
    table_y += row_h + 1

    # ════════════════════════════════════════════════════════════
    # ACT 3: "HOW TO WIN THE BUSINESS"
    # ════════════════════════════════════════════════════════════

    box_y = table_y + 3
    if box_y > 248:
        box_y = 248

    talking = build_talking_points(row)

    # Acquisition history line
    p12 = fv(row.get("purchases_last_12mo", ""))
    p36 = fv(row.get("purchases_last_36mo", ""))
    avg_purchase = fc(row.get("avg_purchase_price", row.get("avg_sale_price", "")))
    flip_count = fv(row.get("flip_count", ""))
    acq_parts = []
    if p12:
        acq_parts.append(f"12mo: {p12}")
    if p36:
        acq_parts.append(f"36mo: {p36}")
    if avg_purchase:
        acq_parts.append(f"Avg: {avg_purchase}")
    if flip_count and flip_count != "0":
        acq_parts.append(f"Flips: {flip_count}")
    acq_line = "Purchases: " + " | ".join(acq_parts) if acq_parts else ""

    # Estimate box height
    pdf.set_font("Helvetica", "", 7.5)
    talking_lines = max(2, len(talking) // 100 + 1)
    box_h = 10 + talking_lines * 4
    if acq_line:
        box_h += 5

    # Cap box to fit on page
    max_box_bottom = 264
    if box_y + box_h > max_box_bottom:
        box_h = max_box_bottom - box_y
        # Truncate talking points if needed
        max_chars = int((box_h - 14) / 4 * 100)
        if len(talking) > max_chars:
            talking = talking[:max_chars] + "..."

    # Light gray box with teal left border
    pdf.set_fill_color(245, 247, 250)
    pdf.rect(L_MARGIN, box_y, USABLE_W, box_h, "F")
    pdf.set_fill_color(*TEAL)
    pdf.rect(L_MARGIN, box_y, 1.5, box_h, "F")

    # Title
    pdf.set_xy(L_MARGIN + 5, box_y + 2)
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_text_color(*NAVY)
    pdf.cell(USABLE_W - 10, 4, "HOW TO WIN THE BUSINESS")

    # Talking points
    pdf.set_xy(L_MARGIN + 5, box_y + 7)
    pdf.set_font("Helvetica", "", 7.5)
    pdf.set_text_color(*BLACK)
    pdf.multi_cell(USABLE_W - 10, 3.8, talking)

    # Acquisition history line
    if acq_line:
        acq_y = box_y + box_h - 5
        pdf.set_xy(L_MARGIN + 5, acq_y)
        pdf.set_font("Helvetica", "B", 6.5)
        pdf.set_text_color(*DARK_GRAY)
        pdf.cell(USABLE_W - 10, 3, acq_line)

    # ════════════════════════════════════════════════════════════
    # FOOTER
    # ════════════════════════════════════════════════════════════
    footer_y = 268
    pdf.set_draw_color(*MED_GRAY)
    pdf.set_line_width(0.2)
    pdf.line(L_MARGIN, footer_y, L_MARGIN + USABLE_W, footer_y)

    pdf.set_xy(L_MARGIN, footer_y + 1.5)
    pdf.set_font("Helvetica", "", 5.5)
    pdf.set_text_color(*MED_GRAY)
    conf = "SAMPLE" if is_redacted else "Confidential"
    pdf.cell(USABLE_W / 3, 3, f"{conf} | Proprietary Analysis")
    pdf.cell(USABLE_W / 3, 3, "Still Mind Creative", align="C")
    pdf.cell(USABLE_W / 3, 3, "Source: Public Records + Enrichment APIs", align="R")

    # ── Save ────────────────────────────────────────────────────
    pdf.output(str(output_path))

    # Cleanup temp chart files
    for f in Path(tmpdir).glob("*.png"):
        try:
            f.unlink()
        except Exception:
            pass
    try:
        os.rmdir(tmpdir)
    except Exception:
        pass


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
    parser = argparse.ArgumentParser(description="Generate visual sales brief investor dossier PDFs")
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
