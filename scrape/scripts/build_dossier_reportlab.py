"""
DSCR Investor Dossier — Professional Tear Sheet (ReportLab)
============================================================

Professional single-page investor intelligence dossier using ReportLab.
Designed for branch managers, LOs, RE agents, and RE brokers.

3-Act Story Flow:
  Act 1: "Who is this?"       — Header bar + KPI cards
  Act 2: "What do they own?"  — Contact, signals, charts, property table
  Act 3: "How to win"         — Talking points + acquisition history

Usage:
    python scripts/build_dossier_reportlab.py --input data/mvp/pilot_500_master.csv
    python scripts/build_dossier_reportlab.py --input data/mvp/pilot_500_master.csv --redacted
    python scripts/build_dossier_reportlab.py --input data/mvp/pilot_500_master.csv --leads "DEMIRAY HOLDINGS INC"
"""

import argparse
import math
import os
import sys
import tempfile
from io import BytesIO
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import pandas as pd

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import mm, inch
from reportlab.pdfgen import canvas
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent
LOGO_PATH = PROJECT_DIR / "assets" / "logo.png"

# ── Try to register Inter font (fallback to Helvetica) ─────────────
FONT_REGULAR = "Helvetica"
FONT_BOLD = "Helvetica-Bold"
FONT_ITALIC = "Helvetica-Oblique"

# Check for Inter font in assets
_inter_dir = PROJECT_DIR / "assets" / "fonts"
if (_inter_dir / "Inter-Regular.ttf").exists():
    try:
        pdfmetrics.registerFont(TTFont("Inter", str(_inter_dir / "Inter-Regular.ttf")))
        pdfmetrics.registerFont(TTFont("Inter-Bold", str(_inter_dir / "Inter-Bold.ttf")))
        FONT_REGULAR = "Inter"
        FONT_BOLD = "Inter-Bold"
    except Exception:
        pass

# ── Color Palette ────────────────────────────────────────────────────
NAVY       = colors.Color(10/255, 35/255, 66/255)
TEAL       = colors.Color(26/255, 107/255, 106/255)
ACCENT     = colors.Color(0/255, 102/255, 179/255)
BLACK_SOFT  = colors.Color(33/255, 33/255, 33/255)
DARK_GRAY  = colors.Color(89/255, 89/255, 89/255)
MED_GRAY   = colors.Color(153/255, 153/255, 153/255)
LIGHT_BG   = colors.Color(237/255, 241/255, 247/255)
ALT_ROW    = colors.Color(248/255, 249/255, 251/255)
WHITE      = colors.white
GREEN_CLR  = colors.Color(34/255, 139/255, 34/255)
AMBER_CLR  = colors.Color(204/255, 136/255, 0/255)
RED_CLR    = colors.Color(191/255, 49/255, 49/255)
LIGHT_BLUE = colors.Color(220/255, 235/255, 252/255)
CARD_BG    = colors.Color(245/255, 247/255, 250/255)

# Matplotlib hex equivalents
_HEX_NAVY  = "#0a2342"
_HEX_TEAL  = "#1a6b6a"
_HEX_GREEN = "#228b22"
_HEX_AMBER = "#cc8800"
_HEX_RED   = "#bf3131"
_HEX_GRAY  = "#999999"

# ── Page Layout ─────────────────────────────────────────────────────
PW, PH = letter  # 612 x 792 pts
MARGIN_L = 28
MARGIN_R = 28
MARGIN_T = 24
MARGIN_B = 30
USABLE = PW - MARGIN_L - MARGIN_R  # ~556 pts

# ── Florida County Codes ────────────────────────────────────────────
FL_COUNTY_MAP = {
    "1": "Alachua", "5": "Brevard", "6": "Broward", "11": "Collier",
    "13": "Miami-Dade", "16": "Duval", "29": "Hillsborough", "36": "Lee",
    "48": "Orange", "50": "Palm Beach", "52": "Pinellas", "56": "Sarasota",
    "57": "Seminole", "59": "St. Lucie", "60": "Palm Beach", "65": "Volusia",
}

USE_CODE_MAP = {
    "001": "SFR", "01": "SFR", "1": "SFR",
    "002": "Mobile Home", "02": "Mobile Home",
    "003": "Multi-Family", "03": "Multi-Family",
    "004": "Condo", "04": "Condo",
    "005": "Co-op", "05": "Co-op",
    "008": "Multi-Family (10+)", "08": "Multi-Family (10+)",
}


# ═══════════════════════════════════════════════════════════════════
# FORMATTING HELPERS
# ═══════════════════════════════════════════════════════════════════

def fc(val):
    """Format currency — clean, abbreviated."""
    try:
        s = str(val).replace(",", "").replace("$", "").strip()
        if not s or s.upper() in ("NAN", "NONE", ""):
            return None
        v = float(s)
        if v == 0 or math.isnan(v):
            return None
        if abs(v) >= 1_000_000:
            return f"${v/1_000_000:.1f}M"
        if abs(v) >= 1_000:
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
        if math.isnan(v):
            return None
        if abs(v) < 1:
            return f"{v * 100:.1f}%"
        return f"{v:.1f}%"
    except (ValueError, TypeError):
        return None


def fv(val):
    """Format value — return None if empty/missing."""
    if val is None:
        return None
    s = str(val).strip()
    if not s or s.upper() in ("NAN", "NONE", "", "0", "0.0", "N/A", "--"):
        return None
    return s


def fphone(val):
    """Format phone number."""
    if val is None:
        return None
    s = str(val).strip().replace("-", "").replace("(", "").replace(")", "").replace(" ", "")
    if not s or s.upper() in ("NAN", "NONE"):
        return None
    if len(s) == 10:
        return f"({s[:3]}) {s[3:6]}-{s[6:]}"
    if len(s) == 11 and s[0] == "1":
        return f"({s[1:4]}) {s[4:7]}-{s[7:]}"
    return fv(val)


def clean_name(val):
    s = str(val).strip().rstrip("& ").rstrip(",").strip()
    return s if s and s.upper() not in ("NAN", "NONE") else None


def display_name(raw_name):
    """Convert 'LAST FIRST M &' to 'First M. Last', entities to title case."""
    if not raw_name:
        return "Unknown"
    s = str(raw_name).strip().rstrip("& ").rstrip(",").strip()
    if not s or s.upper() in ("NAN", "NONE"):
        return "Unknown"
    entity_markers = ["LLC", "L.L.C", "INC", "CORP", "TRUST", "LTD", "LP",
                      "L.P.", "REALTY", "PROPERTIES", "INVESTMENTS", "HOLDINGS",
                      "PARTNERS", "GROUP", "VENTURES", "CAPITAL", "MANAGEMENT"]
    upper = s.upper()
    if any(marker in upper for marker in entity_markers):
        result = s.title()
        for marker in ["Llc", "L.L.C", "Inc", "Corp", "Ltd", "Lp", "L.P."]:
            result = result.replace(marker, marker.upper())
        return result
    parts = s.split()
    if len(parts) <= 1:
        return parts[0].title() if parts else "Unknown"
    last = parts[0].title()
    first_middle = " ".join(parts[1:]).title()
    return f"{first_middle} {last}" if first_middle else last


def fprop_types(val):
    s = str(val).strip()
    if not s or s.upper() in ("NAN", "NONE", ""):
        return None
    codes = [c.strip() for c in s.split(",")]
    names = list(dict.fromkeys(USE_CODE_MAP.get(c, c) for c in codes))
    return ", ".join(names)


def get_county_state(row):
    state = fv(row.get("OWN_STATE_DOM", "")) or fv(row.get("OWN_STATE", ""))
    co_no = str(row.get("CO_NO", "")).strip()
    county = None
    if state and state.upper() in ("FL", "FLORIDA") and co_no:
        county = FL_COUNTY_MAP.get(co_no)
    if not county:
        county = fv(row.get("county", "")) or fv(row.get("county_name", ""))
    st = state.upper() if state else ""
    if st == "FLORIDA":
        st = "FL"
    if county and st:
        return f"{county} County, {st}"
    return st or ""


def _safe_float(val, default=0.0):
    """Safely convert to float."""
    try:
        v = float(str(val).replace(",", "").replace("$", "").replace("%", "").strip() or 0)
        return default if math.isnan(v) else v
    except (ValueError, TypeError):
        return default


# ═══════════════════════════════════════════════════════════════════
# MATPLOTLIB CHART GENERATORS
# ═══════════════════════════════════════════════════════════════════

def render_score_donut(score, tmpdir):
    """Clean partial-ring donut with score centered."""
    fig, ax = plt.subplots(figsize=(1.4, 1.4), dpi=200)
    fig.patch.set_alpha(0)
    ax.set_aspect("equal")

    if score == 0:
        color, label = _HEX_GRAY, "NEW"
    elif score >= 50:
        color, label = _HEX_GREEN, "HOT"
    elif score >= 30:
        color, label = _HEX_AMBER, "WARM"
    else:
        color, label = _HEX_RED, "ACTIVE"

    theta = np.linspace(0, 2 * np.pi, 100)
    ax.plot(np.cos(theta), np.sin(theta), color="#e0e0e0", linewidth=10,
            solid_capstyle="round")

    if score > 0:
        pct = min(score / 100, 1.0)
        theta_s = np.linspace(np.pi/2, np.pi/2 - 2*np.pi*pct, 100)
        ax.plot(np.cos(theta_s), np.sin(theta_s), color=color, linewidth=10,
                solid_capstyle="round")

    ax.text(0, 0.08, str(int(score)), ha="center", va="center",
            fontsize=28, fontweight="bold", color=color, fontfamily="sans-serif")
    ax.text(0, -0.38, label, ha="center", va="center",
            fontsize=7, color="#666666", fontweight="bold", fontfamily="sans-serif")

    ax.set_xlim(-1.5, 1.5)
    ax.set_ylim(-1.5, 1.5)
    ax.axis("off")

    path = os.path.join(tmpdir, "score_donut.png")
    fig.savefig(path, transparent=True, bbox_inches="tight", pad_inches=0.02, dpi=200)
    plt.close(fig)
    return path


def render_equity_bar(equity_pct, portfolio_val, equity_val, debt_val, tmpdir):
    """Clean horizontal equity vs debt bar with labels."""
    fig, ax = plt.subplots(figsize=(3.8, 0.9), dpi=200)
    fig.patch.set_alpha(0)

    total = abs(equity_val) + abs(debt_val)
    if total == 0:
        plt.close(fig)
        return None

    eq_frac = max(equity_val, 0) / total if total else 0
    dt_frac = max(debt_val, 0) / total if total else 0

    bar_h = 0.45
    if equity_val > 0:
        ax.barh(0, eq_frac, height=bar_h, color=_HEX_GREEN, edgecolor="none")
        if eq_frac > 0.12:
            ax.text(eq_frac / 2, 0, fc(equity_val) or "", ha="center", va="center",
                    fontsize=8, color="white", fontweight="bold", fontfamily="sans-serif")
    if debt_val > 0:
        ax.barh(0, dt_frac, height=bar_h, color=_HEX_RED, edgecolor="none", left=eq_frac)
        if dt_frac > 0.12:
            ax.text(eq_frac + dt_frac / 2, 0, fc(debt_val) or "", ha="center",
                    va="center", fontsize=8, color="white", fontweight="bold",
                    fontfamily="sans-serif")

    # Legend beneath
    ax.text(0, -0.48, f"Equity {fp(equity_pct) or ''}", fontsize=6.5,
            color=_HEX_GREEN, fontweight="bold", fontfamily="sans-serif")
    if debt_val > 0:
        ax.text(1.0, -0.48, f"Debt {fc(debt_val) or ''}", fontsize=6.5,
                color=_HEX_RED, fontweight="bold", fontfamily="sans-serif", ha="right")

    ax.set_xlim(0, 1)
    ax.set_ylim(-0.8, 0.5)
    ax.axis("off")

    path = os.path.join(tmpdir, "equity_bar.png")
    fig.savefig(path, transparent=True, bbox_inches="tight", pad_inches=0.02, dpi=200)
    plt.close(fig)
    return path


def render_dscr_gauge(dscr_val, rent_val, noi_val, tmpdir):
    """Horizontal DSCR bar gauge with colored zones and marker."""
    fig, ax = plt.subplots(figsize=(3.6, 1.8), dpi=200)
    fig.patch.set_alpha(0)

    # Color by DSCR quality
    if dscr_val >= 1.25:
        val_color = _HEX_GREEN
    elif dscr_val >= 1.0:
        val_color = _HEX_AMBER
    else:
        val_color = _HEX_RED

    # Horizontal bar gauge: 0 to 2.5 mapped to bar
    bar_y = 0.65
    bar_h = 0.22
    total_w = 2.5  # 0 to 2.5

    # Draw colored zones
    zones = [
        (0, 1.0, _HEX_RED),
        (1.0, 1.25, _HEX_AMBER),
        (1.25, 2.5, _HEX_GREEN),
    ]
    for low, high, color in zones:
        ax.barh(bar_y, high - low, height=bar_h, left=low,
                color=color, edgecolor="none", alpha=0.85)

    # Zone labels above bar
    ax.text(0.5, bar_y + bar_h + 0.08, "< 1.0", ha="center", fontsize=6.5,
            color=_HEX_RED, fontweight="bold", fontfamily="sans-serif")
    ax.text(1.125, bar_y + bar_h + 0.08, "1.0-1.25", ha="center", fontsize=6.5,
            color=_HEX_AMBER, fontweight="bold", fontfamily="sans-serif")
    ax.text(1.875, bar_y + bar_h + 0.08, "> 1.25", ha="center", fontsize=6.5,
            color=_HEX_GREEN, fontweight="bold", fontfamily="sans-serif")

    # Marker triangle below bar pointing up
    marker_x = max(0.05, min(2.45, dscr_val))
    ax.plot(marker_x, bar_y - 0.04, "^", color="#2c2c2c", markersize=9)

    # Large value display (well below the bar)
    ax.text(1.25, -0.10, f"{dscr_val:.2f}", ha="center", va="center",
            fontsize=28, fontweight="bold", color=val_color, fontfamily="sans-serif")
    ax.text(1.25, -0.45, "DSCR", ha="center", va="center",
            fontsize=8, color="#666666", fontweight="bold", fontfamily="sans-serif")

    # Rent + NOI line (clear gap below DSCR label)
    parts = []
    r_fmt = fc(rent_val)
    n_fmt = fc(noi_val)
    if r_fmt:
        parts.append(f"Rent: {r_fmt}/yr")
    if n_fmt:
        parts.append(f"NOI: {n_fmt}/yr")
    if parts:
        ax.text(1.25, -0.72, " \u2022 ".join(parts), ha="center", fontsize=6.5,
                color="#555555", fontfamily="sans-serif")

    ax.set_xlim(-0.1, 2.6)
    ax.set_ylim(-0.95, 1.15)
    ax.axis("off")

    path = os.path.join(tmpdir, "dscr_gauge.png")
    fig.savefig(path, transparent=True, bbox_inches="tight", pad_inches=0.02, dpi=200)
    plt.close(fig)
    return path


# ═══════════════════════════════════════════════════════════════════
# CANVAS DRAWING HELPERS
# ═══════════════════════════════════════════════════════════════════

def _draw_rounded_rect(c, x, y, w, h, r=4, fill=None, stroke=None, stroke_w=0.5):
    """Draw a rounded rectangle."""
    p = c.beginPath()
    p.roundRect(x, y, w, h, r)
    if fill:
        c.setFillColor(fill)
    if stroke:
        c.setStrokeColor(stroke)
        c.setLineWidth(stroke_w)
    if fill and stroke:
        c.drawPath(p, fill=1, stroke=1)
    elif fill:
        c.drawPath(p, fill=1, stroke=0)
    else:
        c.drawPath(p, fill=0, stroke=1)


def _draw_pill(c, x, y, text, bg_color, text_color=WHITE, font_size=6.5):
    """Draw a rounded pill badge with text."""
    c.setFont(FONT_BOLD, font_size)
    tw = c.stringWidth(text, FONT_BOLD, font_size)
    pw = tw + 10
    ph = 13
    _draw_rounded_rect(c, x, y, pw, ph, r=6, fill=bg_color)
    c.setFillColor(text_color)
    c.drawString(x + 5, y + 3.5, text)
    return x + pw + 5  # next x


def _draw_kpi_card(c, x, y, w, h, value, label, accent=TEAL):
    """Draw a clean KPI metric card."""
    # Card background
    _draw_rounded_rect(c, x, y, w, h, r=3, fill=CARD_BG, stroke=colors.Color(0.82, 0.85, 0.88), stroke_w=0.4)

    # Top accent bar (full width, prominent)
    c.setFillColor(accent)
    c.rect(x, y + h - 3, w, 3, fill=1, stroke=0)

    # Value (large, bold)
    c.setFont(FONT_BOLD, 16)
    c.setFillColor(NAVY)
    val_str = str(value) if value else "-"
    vw = c.stringWidth(val_str, FONT_BOLD, 16)
    c.drawString(x + (w - vw) / 2, y + h - 24, val_str)

    # Label (small, uppercase)
    c.setFont(FONT_REGULAR, 6)
    c.setFillColor(DARK_GRAY)
    lw = c.stringWidth(label.upper(), FONT_REGULAR, 6)
    c.drawString(x + (w - lw) / 2, y + 5, label.upper())


def _draw_section_header(c, x, y, text, width):
    """Draw a section label with teal accent underline. Returns new y below."""
    c.setFont(FONT_BOLD, 8.5)
    c.setFillColor(NAVY)
    c.drawString(x, y, text.upper())

    tw = min(c.stringWidth(text.upper(), FONT_BOLD, 8.5) + 4, width * 0.4)
    c.setStrokeColor(TEAL)
    c.setLineWidth(1.2)
    c.line(x, y - 3, x + tw, y - 3)
    c.setStrokeColor(colors.Color(0.82, 0.85, 0.89))
    c.setLineWidth(0.3)
    c.line(x + tw, y - 3, x + width, y - 3)

    return y - 14


def _draw_info_row(c, x, y, label, value, width, bold=True):
    """Draw label: value pair. Returns new y."""
    if value is None:
        return y
    c.setFont(FONT_REGULAR, 7)
    c.setFillColor(DARK_GRAY)
    c.drawString(x, y, label)

    font = FONT_BOLD if bold else FONT_REGULAR
    c.setFont(font, 7.5)
    c.setFillColor(BLACK_SOFT)
    c.drawString(x + 68, y, str(value)[:50])

    return y - 12


# ═══════════════════════════════════════════════════════════════════
# TALKING POINTS GENERATOR
# ═══════════════════════════════════════════════════════════════════

def build_talking_points(row):
    """Generate consulting-grade insight paragraph."""
    pts = []
    props = int(_safe_float(row.get("props", row.get("property_count", 1)), 1))
    pval = _safe_float(row.get("total_portfolio_value", 0))
    is_ent = str(row.get("is_entity", "")).upper() == "TRUE"
    oos = str(row.get("out_of_state", "")).upper() == "TRUE"
    lender = fv(row.get("clean_lender", row.get("best_lender", "")))
    rate = fv(row.get("est_interest_rate", ""))
    loan_type = fv(row.get("est_loan_type", ""))
    maturity = fv(row.get("est_maturity_date", ""))
    months_mat = _safe_float(row.get("est_months_to_maturity", 99))
    cashout = _safe_float(row.get("max_cashout_75", row.get("portfolio_cashout_75", 0)))
    brrrr = str(row.get("brrrr_exit_candidate", "")).upper() == "TRUE"
    eq_harvest = str(row.get("equity_harvest_candidate", "")).upper() == "TRUE"
    p12 = int(_safe_float(row.get("purchases_last_12mo", 0)))
    rent = _safe_float(row.get("est_annual_rent", 0))
    eq_pct = _safe_float(row.get("est_equity_pct", 0))

    if props >= 10:
        pts.append(f"Institutional-scale investor with {props} properties and a {fc(pval) or 'substantial'} portfolio.")
    elif props >= 5:
        pts.append(f"Established portfolio landlord with {props} properties worth {fc(pval) or 'significant value'}.")
    elif props >= 2:
        pts.append(f"Active investor scaling a {props}-property portfolio valued at {fc(pval) or 'growing value'}.")

    if is_ent:
        pts.append("Entity-structured ownership signals sophistication and comfort with non-QM lending products.")
    if oos:
        pts.append("Out-of-state investor managing remotely -- may prefer streamlined DSCR process.")

    if lender:
        lender_short = lender.split(" MORTGAGE")[0] if " MORTGAGE" in lender else lender[:40]
        rate_info = f" at {rate}%" if rate else ""
        type_info = f" ({loan_type.replace('_', ' ')})" if loan_type else ""
        pts.append(f"Currently financed through {lender_short}{type_info}{rate_info}.")

    if months_mat <= 12 and maturity:
        pts.append(f"Loan maturing {maturity} -- urgent refi window.")
    elif months_mat <= 24 and maturity:
        pts.append(f"Maturity approaching ({maturity}) -- proactive refi opportunity.")

    if brrrr:
        pts.append("Recent below-market acquisition indicates BRRRR strategy -- likely needs DSCR exit financing.")
    if eq_harvest and eq_pct > 40:
        pts.append(f"Long-held properties with {eq_pct:.0f}% equity -- prime candidate for cash-out refi.")
    if cashout > 100_000:
        pts.append(f"Cash-out refi potential: up to {fc(cashout)} available at 75% LTV.")
    if p12 >= 2:
        pts.append(f"Highly active: {p12} acquisitions in the past 12 months.")
    elif p12 == 1:
        pts.append("Recent acquisition indicates active investment posture.")
    if rent > 50_000:
        pts.append(f"Est. {fc(rent)}/year rental income supports strong DSCR qualification.")

    return " ".join(pts) if pts else "Confirmed investment property owner -- DSCR lending conversation opportunity."


# ═══════════════════════════════════════════════════════════════════
# MAIN PDF GENERATOR
# ═══════════════════════════════════════════════════════════════════

def generate_dossier(row, output_path, is_redacted=False):
    """Generate a professional single-page investor dossier PDF."""
    c = canvas.Canvas(str(output_path), pagesize=letter)
    c.setTitle("Investor Intelligence Dossier")

    redact = lambda v: ("X" * min(len(str(v)), 12)) if (is_redacted and v) else v

    # ── Extract & Format Data ─────────────────────────────────────
    owner_raw = clean_name(row.get("OWN_NAME", "")) or "Unknown"
    owner_display = display_name(owner_raw)
    segment = fv(row.get("_icp", row.get("selling_segment", ""))) or "Investor"
    score = _safe_float(row.get("_score", row.get("score", 0)))
    props = int(_safe_float(row.get("property_count", row.get("props", 1)), 1))
    county_state = get_county_state(row)

    portfolio_val = fc(row.get("total_portfolio_value", ""))
    avg_val = fc(row.get("avg_property_value", ""))
    equity_pct_raw = _safe_float(row.get("est_equity_pct", row.get("equity_ratio", 0)))
    equity_pct_str = fp(row.get("est_equity_pct", "")) or fp(row.get("equity_ratio", ""))

    # Portfolio equity (use est_portfolio_equity first, fall back to estimated_equity)
    portfolio_equity = _safe_float(row.get("est_portfolio_equity", row.get("estimated_equity", 0)))
    debt_val = _safe_float(row.get("est_remaining_balance", 0))
    # If we have equity pct and portfolio value but no debt, derive debt
    pval_num = _safe_float(row.get("total_portfolio_value", 0))
    if portfolio_equity > 0 and debt_val == 0 and pval_num > 0:
        debt_val = pval_num - portfolio_equity

    dscr_num = _safe_float(row.get("est_dscr", 0))
    rent_num = _safe_float(row.get("est_annual_rent", 0))
    noi_num = _safe_float(row.get("est_noi", 0))

    phone1 = fphone(row.get("phone_1", ""))
    phone1_type = fv(row.get("phone_1_type", ""))
    phone2 = fphone(row.get("phone_2", ""))
    email1 = fv(row.get("email_1", ""))
    email2 = fv(row.get("email_2", ""))

    mail_addr = fv(row.get("OWN_ADDR1", ""))
    mail_city = fv(row.get("OWN_CITY", ""))
    mail_state = fv(row.get("OWN_STATE_DOM", ""))
    mail_zip = fv(row.get("OWN_ZIPCD", ""))

    lender = fv(row.get("clean_lender", row.get("best_lender", "")))
    loan_type = fv(row.get("est_loan_type", ""))
    rate = fv(row.get("est_interest_rate", ""))
    maturity = fv(row.get("est_maturity_date", ""))
    months_mat = _safe_float(row.get("est_months_to_maturity", 99))
    loan_amt_raw = _safe_float(row.get("est_original_loan", row.get("attom_loan_amount", 0)))
    cashout = fc(row.get("max_cashout_75", row.get("portfolio_cashout_75", "")))

    is_entity = str(row.get("is_entity", "")).upper() == "TRUE"
    agent = fv(row.get("registered_agent_name", ""))
    status = fv(row.get("sunbiz_status", row.get("entity_status", "")))
    contact_name = fv(row.get("contact_name", row.get("resolved_person", "")))

    # Signals
    signals = []
    if str(row.get("brrrr_exit_candidate", "")).upper() == "TRUE":
        signals.append(("BRRRR EXIT", AMBER_CLR))
    if str(row.get("equity_harvest_candidate", "")).upper() == "TRUE":
        signals.append(("EQUITY HARVEST", GREEN_CLR))
    if str(row.get("rate_refi_candidate", "")).upper() == "TRUE":
        signals.append(("RATE REFI", ACCENT))
    if str(row.get("out_of_state", "")).upper() == "TRUE":
        signals.append(("OUT-OF-STATE", MED_GRAY))
    if months_mat <= 12:
        signals.append(("MATURITY URGENT", RED_CLR))
    if str(row.get("est_hard_money", "")).upper() == "TRUE":
        signals.append(("HARD MONEY", RED_CLR))

    # Property addresses
    phy_raw = str(row.get("PHY_ADDR1", "")).strip()
    addresses = []
    if phy_raw and phy_raw.upper() not in ("NAN", "NONE", ""):
        addresses = [a.strip().title()[:42] for a in phy_raw.split("|") if a.strip()]

    # ── Render Charts ─────────────────────────────────────────────
    tmpdir = tempfile.mkdtemp()
    score_img = render_score_donut(score, tmpdir)

    eq_img = None
    if portfolio_equity > 0 or debt_val > 0:
        eq_img = render_equity_bar(equity_pct_raw, pval_num, portfolio_equity, debt_val, tmpdir)

    dscr_img = None
    if dscr_num > 0:
        dscr_img = render_dscr_gauge(dscr_num, rent_num, noi_num, tmpdir)

    # ══════════════════════════════════════════════════════════════
    # ACT 1: HEADER BAR
    # ══════════════════════════════════════════════════════════════
    header_h = 62

    # Full-width navy header
    c.setFillColor(NAVY)
    c.rect(0, PH - header_h, PW, header_h, fill=1, stroke=0)

    # Teal accent strip
    c.setFillColor(TEAL)
    c.rect(0, PH - header_h, PW, 2, fill=1, stroke=0)

    # Logo
    logo_end_x = MARGIN_L
    if LOGO_PATH.exists():
        try:
            c.drawImage(str(LOGO_PATH), MARGIN_L, PH - header_h + 8, height=46,
                        preserveAspectRatio=True, mask='auto')
            logo_end_x = MARGIN_L + 60
        except Exception:
            pass

    # Owner name
    name_x = logo_end_x + 6
    c.setFont(FONT_BOLD, 18)
    c.setFillColor(WHITE)
    disp = redact(owner_display) if is_redacted else owner_display
    c.drawString(name_x, PH - 26, disp[:38])

    # Subtitle line
    c.setFont(FONT_REGULAR, 8)
    c.setFillColor(colors.Color(0.7, 0.78, 0.88))
    prop_type = fprop_types(row.get("property_types", "")) or ""
    sub_parts = [segment, f"{props} Properties"]
    if prop_type:
        sub_parts.append(prop_type)
    if county_state:
        sub_parts.append(county_state)
    c.drawString(name_x, PH - 40, "  |  ".join(sub_parts))

    # Contact name (if entity)
    if is_entity and contact_name:
        c.setFont(FONT_REGULAR, 7.5)
        c.setFillColor(colors.Color(0.6, 0.72, 0.84))
        cname_display = display_name(contact_name)
        c.drawString(name_x, PH - 51, f"Contact: {redact(cname_display) if is_redacted else cname_display}")

    # Score donut (top right)
    if score_img:
        c.drawImage(score_img, PW - MARGIN_R - 56, PH - header_h + 5,
                    width=52, height=52, mask='auto')

    # ══════════════════════════════════════════════════════════════
    # KPI CARDS ROW
    # ══════════════════════════════════════════════════════════════
    kpi_y = PH - header_h - 50
    card_gap = 8
    card_h = 38

    # Determine which KPI cards to show (suppress empty ones)
    kpi_items = []
    if portfolio_val:
        kpi_items.append((portfolio_val, "Portfolio Value", TEAL))
    if equity_pct_str and portfolio_equity > 0:
        kpi_items.append((equity_pct_str, "Equity Ratio", GREEN_CLR))
    elif fc(portfolio_equity):
        kpi_items.append((fc(portfolio_equity), "Total Equity", GREEN_CLR))
    if dscr_num > 0:
        kpi_items.append((f"{dscr_num:.2f}", "Est. DSCR",
                          GREEN_CLR if dscr_num >= 1.25 else (AMBER_CLR if dscr_num >= 1.0 else RED_CLR)))
    if avg_val:
        kpi_items.append((avg_val, "Avg Prop Value", ACCENT))

    # Always show at least 3 cards
    if not kpi_items:
        kpi_items = [("-", "Portfolio Value", TEAL), ("-", "Equity", GREEN_CLR),
                     ("-", "DSCR", ACCENT)]
    while len(kpi_items) < 3:
        kpi_items.append(("-", "Pending", MED_GRAY))

    kpi_items = kpi_items[:5]  # max 5 cards
    card_count = len(kpi_items)
    card_w = (USABLE - (card_count - 1) * card_gap) / card_count

    for i, (val, label, accent_c) in enumerate(kpi_items):
        cx = MARGIN_L + i * (card_w + card_gap)
        _draw_kpi_card(c, cx, kpi_y, card_w, card_h, val, label, accent=accent_c)

    # ══════════════════════════════════════════════════════════════
    # ACT 2: TWO-COLUMN BODY
    # ══════════════════════════════════════════════════════════════
    body_top = kpi_y - 14
    col_gutter = 14
    col_w = (USABLE - col_gutter) / 2
    left_x = MARGIN_L
    right_x = MARGIN_L + col_w + col_gutter

    # ── LEFT COLUMN: Contact + Entity + Signals ──────────────────
    ly = body_top

    # Contact Info
    ly = _draw_section_header(c, left_x, ly, "Contact Information", col_w)
    has_contact = False
    if phone1:
        ptype = f" ({phone1_type})" if phone1_type else ""
        ly = _draw_info_row(c, left_x, ly, "Phone:", f"{redact(phone1) if is_redacted else phone1}{ptype}", col_w)
        has_contact = True
    if phone2 and phone2 != phone1:
        ly = _draw_info_row(c, left_x, ly, "Phone 2:", redact(phone2) if is_redacted else phone2, col_w)
        has_contact = True
    if email1:
        ly = _draw_info_row(c, left_x, ly, "Email:", redact(email1) if is_redacted else email1, col_w)
        has_contact = True
    if email2 and email2 != email1:
        ly = _draw_info_row(c, left_x, ly, "Email 2:", redact(email2) if is_redacted else email2, col_w)
        has_contact = True
    if mail_addr:
        full_mail = redact(mail_addr) if is_redacted else mail_addr
        ly = _draw_info_row(c, left_x, ly, "Address:", full_mail, col_w)
        city_parts = ", ".join(filter(None, [mail_city, mail_state]))
        if mail_zip:
            city_parts += f" {mail_zip}"
        if city_parts.strip():
            ly = _draw_info_row(c, left_x, ly, "", city_parts.strip(", "), col_w, bold=False)
        has_contact = True

    if not has_contact:
        c.setFont(FONT_ITALIC, 7)
        c.setFillColor(MED_GRAY)
        c.drawString(left_x, ly, "Contact enrichment pending")
        ly -= 12

    ly -= 4

    # Entity Details
    if is_entity:
        ly = _draw_section_header(c, left_x, ly, "Entity Details", col_w)
        # Deduplicate principal vs agent (often same person in different name order)
        principal_display = display_name(contact_name) if contact_name else None
        agent_display = display_name(agent) if agent else None
        # Check if they're the same person (same words, different order)
        _same_person = False
        if principal_display and agent_display:
            p_words = set(principal_display.lower().replace(",", "").split())
            a_words = set(agent_display.lower().replace(",", "").split())
            _same_person = p_words == a_words or p_words.issubset(a_words) or a_words.issubset(p_words)

        if principal_display:
            ly = _draw_info_row(c, left_x, ly, "Principal:",
                                redact(principal_display) if is_redacted else principal_display, col_w)
        if agent_display and not _same_person:
            ly = _draw_info_row(c, left_x, ly, "Reg. Agent:",
                                redact(agent_display) if is_redacted else agent_display, col_w)
        if status:
            status_color = GREEN_CLR if "ACTIVE" in status.upper() else RED_CLR
            c.setFont(FONT_REGULAR, 7)
            c.setFillColor(DARK_GRAY)
            c.drawString(left_x, ly, "Status:")
            c.setFont(FONT_BOLD, 7.5)
            c.setFillColor(status_color)
            c.drawString(left_x + 68, ly, status.title())
            ly -= 12
        ly -= 4

    # Opportunity Signals
    if signals:
        ly = _draw_section_header(c, left_x, ly, "Opportunity Signals", col_w)
        pill_x = left_x
        pill_y = ly
        for sig_text, sig_color in signals:
            next_x = _draw_pill(c, pill_x, pill_y, sig_text, sig_color)
            if next_x > left_x + col_w - 10:
                pill_y -= 17
                pill_x = left_x
                pill_x = _draw_pill(c, pill_x, pill_y, sig_text, sig_color)
            else:
                pill_x = next_x
        ly = pill_y - 18

    # Financing Intelligence (left column, below signals)
    ly -= 2
    has_financing = any([lender, loan_type, rate, maturity, cashout])
    if has_financing:
        ly = _draw_section_header(c, left_x, ly, "Financing Intelligence", col_w)
        if lender:
            lender_short = lender.split(" MORTGAGE")[0] if " MORTGAGE" in lender else lender[:35]
            ly = _draw_info_row(c, left_x, ly, "Lender:", lender_short, col_w)
        if loan_type:
            ly = _draw_info_row(c, left_x, ly, "Loan Type:", loan_type.replace("_", " ").title(), col_w)
        if rate:
            ly = _draw_info_row(c, left_x, ly, "Rate:", f"{rate}%", col_w)
        if loan_amt_raw > 0:
            ly = _draw_info_row(c, left_x, ly, "Loan Amount:", fc(loan_amt_raw), col_w)
        if maturity:
            urgency = " (URGENT)" if months_mat <= 12 else ""
            ly = _draw_info_row(c, left_x, ly, "Maturity:", f"{maturity}{urgency}", col_w)
        if cashout:
            ly = _draw_info_row(c, left_x, ly, "Cash-Out 75%:", cashout, col_w)

    # ── RIGHT COLUMN: Charts ─────────────────────────────────────
    ry = body_top

    # Equity bar chart
    if eq_img:
        ry = _draw_section_header(c, right_x, ry, "Equity vs Debt", col_w)
        c.drawImage(eq_img, right_x, ry - 40, width=col_w - 5, height=48, mask='auto')
        ry -= 58

    # DSCR Gauge (horizontal bar style)
    if dscr_img:
        ry = _draw_section_header(c, right_x, ry, "DSCR Analysis", col_w)
        c.drawImage(dscr_img, right_x, ry - 58, width=col_w - 4, height=64, mask='auto')
        ry -= 68

    # Acquisition History (right column)
    p12 = int(_safe_float(row.get("purchases_last_12mo", 0)))
    p36 = int(_safe_float(row.get("purchases_last_36mo", 0)))
    avg_purchase = fc(row.get("avg_purchase_price", row.get("avg_sale_price", "")))
    recent_date = fv(row.get("most_recent_purchase_date", row.get("most_recent_purchase", "")))
    recent_price = fc(row.get("most_recent_purchase_price", row.get("most_recent_price", "")))
    flip_count = int(_safe_float(row.get("flip_count", 0)))

    has_acq = any([p12, p36, avg_purchase, recent_date])
    if has_acq:
        ry = _draw_section_header(c, right_x, ry, "Acquisition History", col_w)
        if p12:
            ry = _draw_info_row(c, right_x, ry, "Last 12 Mo:", f"{p12} acquisitions", col_w)
        if p36:
            ry = _draw_info_row(c, right_x, ry, "Last 36 Mo:", f"{p36} acquisitions", col_w)
        if recent_date:
            price_str = f" @ {recent_price}" if recent_price else ""
            ry = _draw_info_row(c, right_x, ry, "Most Recent:", f"{recent_date}{price_str}", col_w)
        if avg_purchase:
            ry = _draw_info_row(c, right_x, ry, "Avg Purchase:", avg_purchase, col_w)
        if flip_count:
            ry = _draw_info_row(c, right_x, ry, "Flips:", str(flip_count), col_w)

    # ══════════════════════════════════════════════════════════════
    # PROPERTY TABLE
    # ══════════════════════════════════════════════════════════════
    table_top = min(ly, ry) - 16  # Extra gap between body and table
    table_top = max(table_top, 175)  # Don't let table get too low

    # Only show table if we have addresses
    if addresses:
        c.setFont(FONT_BOLD, 8.5)
        c.setFillColor(NAVY)
        c.drawString(MARGIN_L, table_top + 12,
                     f"PROPERTY PORTFOLIO  ({props} Properties)")

        # Accent line
        tw = c.stringWidth(f"PROPERTY PORTFOLIO  ({props} Properties)", FONT_BOLD, 8.5)
        c.setStrokeColor(TEAL)
        c.setLineWidth(1.2)
        c.line(MARGIN_L, table_top + 8, MARGIN_L + min(tw + 4, USABLE * 0.4), table_top + 8)
        c.setStrokeColor(colors.Color(0.82, 0.85, 0.89))
        c.setLineWidth(0.3)
        c.line(MARGIN_L + min(tw + 4, USABLE * 0.4), table_top + 8, MARGIN_L + USABLE, table_top + 8)

        row_h = 13
        ty = table_top - 2

        # Column widths: # | Address | Est. Value
        col_widths = [22, USABLE - 22 - 90, 90]
        headers = ["#", "Property Address", "Est. Value"]

        # Header row
        c.setFillColor(NAVY)
        c.rect(MARGIN_L, ty - row_h + 2, USABLE, row_h, fill=1, stroke=0)
        c.setFont(FONT_BOLD, 7)
        c.setFillColor(WHITE)
        hx = MARGIN_L + 4
        for hdr, cw in zip(headers, col_widths):
            c.drawString(hx, ty - 7, hdr)
            hx += cw
        ty -= row_h

        # Data rows — cap to what fits
        avg_val_num = _safe_float(row.get("avg_property_value", 0))
        max_rows = min(len(addresses), int((ty - 100) / row_h))  # Leave room for Act 3
        max_rows = max(max_rows, 2)
        show_addrs = addresses[:max_rows]
        overflow = max(0, props - len(show_addrs))

        for idx, addr in enumerate(show_addrs):
            is_alt = idx % 2 == 0
            if is_alt:
                c.setFillColor(ALT_ROW)
            else:
                c.setFillColor(WHITE)
            c.rect(MARGIN_L, ty - row_h + 2, USABLE, row_h, fill=1, stroke=0)

            c.setFont(FONT_REGULAR, 7)
            c.setFillColor(BLACK_SOFT)
            rx = MARGIN_L + 4
            vals = [str(idx + 1), redact(addr) if is_redacted else addr,
                    fc(avg_val_num) or "-"]
            for val, cw in zip(vals, col_widths):
                c.drawString(rx, ty - 7, str(val)[:48])
                rx += cw
            ty -= row_h

        # Overflow row
        if overflow > 0:
            c.setFillColor(ALT_ROW)
            c.rect(MARGIN_L, ty - row_h + 2, USABLE, row_h, fill=1, stroke=0)
            c.setFont(FONT_ITALIC, 7)
            c.setFillColor(DARK_GRAY)
            c.drawString(MARGIN_L + 26, ty - 7, f"...and {overflow} more properties")
            ty -= row_h

        # Totals row
        c.setFillColor(LIGHT_BLUE)
        c.rect(MARGIN_L, ty - row_h + 2, USABLE, row_h, fill=1, stroke=0)
        c.setFont(FONT_BOLD, 7)
        c.setFillColor(NAVY)
        c.drawString(MARGIN_L + 26, ty - 7, f"TOTAL  |  {props} Properties")
        c.drawString(MARGIN_L + col_widths[0] + col_widths[1] + 4, ty - 7,
                     portfolio_val or "-")
        ty -= row_h

        table_bottom = ty
    else:
        table_bottom = table_top

    # ══════════════════════════════════════════════════════════════
    # ACT 3: HOW TO WIN THE BUSINESS
    # ══════════════════════════════════════════════════════════════
    box_top = table_bottom - 8
    box_top = max(box_top, 68)  # Don't overlap footer

    talking = build_talking_points(row)

    # Pre-built talking points from CSV (use if available)
    csv_talking = fv(row.get("talking_points", ""))
    if csv_talking and len(csv_talking) > len(talking):
        talking = csv_talking

    # Calculate box height
    c.setFont(FONT_REGULAR, 7.5)
    # Rough line wrapping estimate
    chars_per_line = int((USABLE - 24) / 3.5)
    num_lines = max(2, len(talking) // chars_per_line + 1)
    box_h = 18 + num_lines * 10

    # Refi signals line
    refi_signals = fv(row.get("est_refi_signals", row.get("refi_signals", "")))

    if refi_signals:
        box_h += 12

    # Cap box
    max_box_h = box_top - 42  # leave room for footer
    if box_h > max_box_h:
        box_h = max_box_h
        max_chars = int((box_h - 22) / 10 * chars_per_line)
        if len(talking) > max_chars:
            talking = talking[:max_chars] + "..."

    box_y = box_top - box_h

    # Background with teal left border
    c.setFillColor(CARD_BG)
    c.rect(MARGIN_L, box_y, USABLE, box_h, fill=1, stroke=0)
    c.setFillColor(TEAL)
    c.rect(MARGIN_L, box_y, 3, box_h, fill=1, stroke=0)

    # Title
    c.setFont(FONT_BOLD, 8.5)
    c.setFillColor(NAVY)
    c.drawString(MARGIN_L + 12, box_y + box_h - 14, "HOW TO WIN THE BUSINESS")

    # Talking points text (wrapped)
    text_obj = c.beginText(MARGIN_L + 12, box_y + box_h - 28)
    text_obj.setFont(FONT_REGULAR, 7.5)
    text_obj.setFillColor(BLACK_SOFT)
    text_obj.setLeading(10)

    # Simple word-wrap
    words = talking.split()
    line = ""
    max_w = USABLE - 24
    for word in words:
        test = f"{line} {word}".strip()
        if c.stringWidth(test, FONT_REGULAR, 7.5) > max_w:
            text_obj.textLine(line)
            line = word
        else:
            line = test
    if line:
        text_obj.textLine(line)

    c.drawText(text_obj)

    # Refi signals line
    if refi_signals:
        c.setFont(FONT_BOLD, 6.5)
        c.setFillColor(TEAL)
        c.drawString(MARGIN_L + 12, box_y + 5, f"SIGNALS: {refi_signals}")

    # ══════════════════════════════════════════════════════════════
    # FOOTER
    # ══════════════════════════════════════════════════════════════
    footer_y = 32
    c.setStrokeColor(MED_GRAY)
    c.setLineWidth(0.3)
    c.line(MARGIN_L, footer_y, MARGIN_L + USABLE, footer_y)

    c.setFont(FONT_REGULAR, 5.5)
    c.setFillColor(MED_GRAY)
    conf = "SAMPLE" if is_redacted else "Confidential"
    c.drawString(MARGIN_L, footer_y - 10, f"{conf}  |  Proprietary Analysis")
    c.drawCentredString(PW / 2, footer_y - 10, "Still Mind Creative")
    c.drawRightString(PW - MARGIN_R, footer_y - 10, "Source: Public Records + Enrichment APIs")

    # ── Save ──────────────────────────────────────────────────────
    c.showPage()
    c.save()

    # Cleanup temp files
    for f in Path(tmpdir).glob("*.png"):
        try:
            f.unlink()
        except Exception:
            pass
    try:
        os.rmdir(tmpdir)
    except Exception:
        pass


# ═══════════════════════════════════════════════════════════════════
# CLI ENTRY POINT
# ═══════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="Generate professional investor dossier PDFs (ReportLab)")
    parser.add_argument("--input", type=str, required=True, help="Input CSV file")
    parser.add_argument("--output-dir", type=str, default=None, help="Output directory for PDFs")
    parser.add_argument("--redacted", action="store_true", help="Redact PII")
    parser.add_argument("--leads", type=str, default=None,
                        help="Comma-separated list of owner names to generate (default: all)")
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

    # Filter to specific leads if requested
    if args.leads:
        lead_names = [n.strip().upper() for n in args.leads.split(",")]
        mask = df["OWN_NAME"].str.upper().str.strip().isin(lead_names)
        df = df[mask]
        if df.empty:
            # Try contains match
            for name in lead_names:
                mask |= df["OWN_NAME"].str.upper().str.contains(name, na=False)
            df_orig = pd.read_csv(input_path, dtype=str)
            df = df_orig[mask]
        if df.empty:
            print(f"No matching leads found for: {args.leads}")
            return

    print(f"Generating {'redacted ' if args.redacted else ''}dossiers for {len(df)} leads...\n")

    for i, (_, row) in enumerate(df.iterrows()):
        owner = clean_name(str(row.get("OWN_NAME", f"lead_{i}"))) or f"lead_{i}"
        safe = "".join(c if c.isalnum() or c in " _-" else "_" for c in owner)[:40].strip()
        suffix = "_redacted" if args.redacted else ""
        fname = f"dossier_{i+1:02d}_{safe}{suffix}.pdf"
        path = output_dir / fname
        generate_dossier(row, path, is_redacted=args.redacted)
        print(f"  [{i+1}/{len(df)}] {fname}")

    print(f"\nDone. {len(df)} PDFs saved to {output_dir}/")


if __name__ == "__main__":
    main()
