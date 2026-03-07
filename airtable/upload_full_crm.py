"""
Full CRM Upload — Self-Contained Investors + Linked Records
============================================================

Reads the enriched pilot CSV and uploads ALL data into Airtable.
The Investors table is the single source of truth — every data point
Frank needs for a call lives directly on the Investor record (no
reliance on rollup chains from linked tables).

Order of operations:
  1. Delete all existing records (clean slate for pilot)
  2. Create Investor records with ALL fields populated (portfolio,
     financing, scoring, triggers)
  3. Create Property records linked to Investors
  4. Create Financing records linked to Properties
  5. Create Ownership Entity records linked to Investors

Usage:
    python airtable/upload_full_crm.py                # Top 25 leads
    python airtable/upload_full_crm.py --count 50     # Top 50
    python airtable/upload_full_crm.py --count 500    # All 500
    python airtable/upload_full_crm.py --dry-run      # Preview only
    python airtable/upload_full_crm.py --no-delete    # Don't delete existing
"""

import argparse
import os
import re
import sys
import time
from datetime import date

import pandas as pd
import requests
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
API_TOKEN = os.getenv("AIRTABLE_API_TOKEN")
BASE_ID = "appJV7J1ZrNEBAWAm"
TABLES = {
    "investors": "tbla2NnrEDSFA3UFP",
    "entities": "tblSwOPMuzEWRBVcF",
    "properties": "tblVXwCSkubWp30UO",
    "financing": "tblh4OgGSpyf6hSfX",
}
HEADERS = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Content-Type": "application/json",
}
DEFAULT_INPUT = os.path.join("scrape", "data", "enriched", "pilot_500_enriched.csv")

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def api_call(method, url, retries=5, **kwargs):
    """Airtable API call with rate-limit retry."""
    for attempt in range(retries):
        resp = requests.request(method, url, headers=HEADERS, **kwargs)
        if resp.status_code == 429:
            wait = int(resp.headers.get("Retry-After", 30))
            print(f"    Rate limited, waiting {wait}s...")
            time.sleep(wait)
            continue
        if resp.status_code >= 400:
            print(f"    API error {resp.status_code}: {resp.text[:300]}")
            return None
        time.sleep(0.22)  # stay under 5 req/s
        return resp.json()
    return None


def safe_float(val) -> float:
    try:
        return float(val)
    except (ValueError, TypeError):
        return 0.0


def safe_int(val) -> int:
    try:
        return int(float(val))
    except (ValueError, TypeError):
        return 0


def clean_str(val) -> str:
    """Return stripped string or empty."""
    s = str(val).strip() if val is not None else ""
    return "" if s.lower() in ("nan", "none", "") else s


def clean_mers_lender(name: str) -> str:
    """Strip MERS nominee prefix to show the actual lender."""
    upper = name.upper()
    if "MORTGAGE ELECTRONIC REGISTRATION" not in upper:
        return name.title()
    mers_phrases = [
        "MORTGAGE ELECTRONIC REGISTRATION SYSTEMS INC",
        "MORTGAGE ELECTRONIC REGISTRATION SYSTEMS, INC.",
        "MORTGAGE ELECTRONIC REGISTRATION SYSTEMS, INC",
    ]
    cleaned = name
    for phrase in mers_phrases:
        cleaned = cleaned.upper().replace(phrase, "").strip()
    cleaned = re.sub(r"^[\s,/\-]+|[\s,/\-]+$", "", cleaned)
    return cleaned.title() if cleaned else name.title()


def normalize_phone(phone) -> str:
    phone = re.sub(r"\D", "", str(phone))
    if len(phone) == 11 and phone.startswith("1"):
        phone = phone[1:]
    return phone if len(phone) == 10 else ""


def parse_name(own_name: str, resolved_person: str) -> tuple:
    """Parse into (first, last, full)."""
    name = resolved_person if resolved_person else own_name
    if not name:
        return "", "", ""
    name = name.rstrip("& ").strip()
    if "," in name:
        parts = name.split(",", 1)
        last = parts[0].strip().title()
        first_parts = parts[1].strip().split() if len(parts) > 1 else []
        first = first_parts[0].title() if first_parts else ""
    else:
        parts = name.split()
        if len(parts) >= 2:
            last = parts[0].title()
            first = parts[1].title()
        elif len(parts) == 1:
            last = parts[0].title()
            first = ""
        else:
            return "", "", ""
    full = f"{first} {last}".strip() if first else last
    return first, last, full


def parse_address(addr_str: str) -> dict:
    """Parse 'STREET, CITY, ST ZIP' into components."""
    parts = [p.strip() for p in addr_str.split(",")]
    result = {"street": "", "city": "", "state": "FL", "zip": ""}
    if len(parts) >= 1:
        result["street"] = parts[0].title()
    if len(parts) >= 2:
        result["city"] = parts[1].title()
    if len(parts) >= 3:
        st_zip = parts[2].strip().split()
        if st_zip:
            result["state"] = st_zip[0].upper()
        if len(st_zip) >= 2:
            result["zip"] = st_zip[1][:5]
    return result


# ---------------------------------------------------------------------------
# Opportunity Score computation
# ---------------------------------------------------------------------------

def compute_opportunity_score(row: pd.Series) -> tuple:
    """Compute Opportunity Score (0-100) and Priority Tier from CSV row.

    Returns (score: int, tier: str).
    """
    # --- Contact Score (0-15) ---
    phone1 = normalize_phone(row.get("phone_1") or row.get("phone") or row.get("str_phone") or "")
    phone2 = normalize_phone(row.get("phone_2") or "")
    apollo_phone = normalize_phone(row.get("apollo_phone") or row.get("apollo_mobile") or "")
    has_phone = bool(phone1 or phone2 or apollo_phone)

    email1 = clean_str(row.get("email_1") or row.get("email") or row.get("str_email") or "")
    email2 = clean_str(row.get("email_2"))
    apollo_email = clean_str(row.get("apollo_email"))
    has_email = bool((email1 and "@" in email1) or (email2 and "@" in email2)
                     or (apollo_email and "@" in apollo_email))

    contact_score = 0
    if has_phone:
        contact_score += 10
    if has_email:
        contact_score += 5

    # --- Portfolio Score (0-25) ---
    props = safe_int(row.get("_props", row.get("property_count", 0)))
    if props >= 20:
        portfolio_score = 25
    elif props >= 10:
        portfolio_score = 20
    elif props >= 5:
        portfolio_score = 15
    elif props >= 2:
        portfolio_score = 8
    else:
        portfolio_score = 3

    # --- Financing Score (0-30) ---
    financing_score = 0
    hard_money = clean_str(row.get("est_hard_money")).lower() in ("true", "1")
    rate = safe_float(row.get("est_interest_rate") or row.get("attom_interest_rate"))
    months_to_mat = safe_float(row.get("est_months_to_maturity"))
    best_lender = clean_str(row.get("best_lender"))

    if hard_money:
        financing_score += 15
    if rate >= 9.0:
        financing_score += 10
    elif rate >= 7.0:
        financing_score += 5
    if 0 < months_to_mat <= 6:
        financing_score += 15
    elif 6 < months_to_mat <= 12:
        financing_score += 10
    elif 12 < months_to_mat <= 24:
        financing_score += 5
    if best_lender:
        financing_score += 5
    financing_score = min(financing_score, 30)

    # --- Activity Score (0-15) ---
    p12 = safe_int(row.get("purchases_last_12mo"))
    p36 = safe_int(row.get("purchases_last_36mo"))
    if p12 >= 3:
        activity_score = 15
    elif p12 >= 1:
        activity_score = 10
    elif p36 >= 1:
        activity_score = 5
    else:
        activity_score = 0

    # --- Trigger Bonus (0-15) ---
    trigger_bonus = 0
    has_refi = clean_str(row.get("_has_refi")).lower() in ("true", "1")
    cash_purchase = clean_str(row.get("est_cash_purchase")).lower() in ("true", "1")
    probable_cash = clean_str(row.get("probable_cash_buyer")).lower() in ("true", "1")
    equity_pct = safe_float(row.get("est_equity_pct"))

    if has_refi:
        trigger_bonus += 10
    if (cash_purchase or probable_cash) and equity_pct >= 50:
        trigger_bonus += 5
    trigger_bonus = min(trigger_bonus, 15)

    # --- Total ---
    score = min(contact_score + portfolio_score + financing_score
                + activity_score + trigger_bonus, 100)

    # --- Priority Tier ---
    if score >= 75:
        tier = "Tier 1 — Call Now"
    elif score >= 55:
        tier = "Tier 2 — High Priority"
    elif score >= 35:
        tier = "Tier 3 — Standard"
    else:
        tier = "Tier 4 — Nurture"

    return score, tier


# ---------------------------------------------------------------------------
# Record builders
# ---------------------------------------------------------------------------

def build_investor(row: pd.Series) -> dict:
    """Build Airtable Investors record from CSV row.

    Includes ALL fields: identity, contact, classification, portfolio,
    financing, activity, scoring, and call intel — so the Investor
    record is fully self-contained for prospecting.
    """
    own_name = clean_str(row.get("OWN_NAME"))
    resolved = clean_str(row.get("resolved_person"))
    is_entity = clean_str(row.get("is_entity")).lower() in ("true", "1", "yes")
    props = safe_int(row.get("_props", row.get("property_count", 0)))

    fields = {}

    # === IDENTITY ===
    if resolved:
        first, last, full = parse_name("", resolved)
        if full:
            fields["Full Name"] = full
        if first:
            fields["First Name"] = first
        if last:
            fields["Last Name"] = last
    elif is_entity:
        fields["Full Name"] = own_name.strip().title()
    else:
        first, last, full = parse_name(own_name, "")
        if full:
            fields["Full Name"] = full
        if first:
            fields["First Name"] = first
        if last:
            fields["Last Name"] = last

    # === CONTACT ===
    phone1 = normalize_phone(row.get("phone_1") or row.get("phone") or row.get("str_phone") or "")
    phone2 = normalize_phone(row.get("phone_2") or "")
    email1 = clean_str(row.get("email_1") or row.get("email") or row.get("str_email") or "")
    email2 = clean_str(row.get("email_2"))
    apollo_email = clean_str(row.get("apollo_email"))
    apollo_phone = normalize_phone(row.get("apollo_phone") or row.get("apollo_mobile") or "")
    linkedin = clean_str(row.get("apollo_linkedin"))

    if not phone1 and apollo_phone:
        phone1 = apollo_phone
    if not email1 and apollo_email and "@" in apollo_email:
        email1 = apollo_email

    if phone1:
        fields["Phone (Mobile)"] = phone1
    if phone2:
        fields["Phone (Secondary)"] = phone2
    if email1 and "@" in email1:
        fields["Email (Primary)"] = email1
    if email2 and "@" in email2:
        fields["Email (Secondary)"] = email2
    if linkedin:
        fields["LinkedIn URL"] = linkedin

    # === MAILING ADDRESS ===
    addr = clean_str(row.get("OWN_ADDR1"))
    city = clean_str(row.get("OWN_CITY"))
    state = clean_str(row.get("OWN_STATE"))
    zipcode = clean_str(row.get("OWN_ZIPCD"))[:5]

    if addr:
        fields["Mailing Address"] = addr.title()
    if city:
        fields["Mailing City"] = city.title()
    if state:
        fields["Mailing State"] = state.upper() if len(state) <= 2 else state.title()
    if zipcode:
        fields["Mailing ZIP"] = zipcode

    # === CLASSIFICATION ===
    co_no = clean_str(row.get("CO_NO"))
    if co_no == "60":
        fields["Primary Market"] = "Palm Beach County"
    elif co_no in ("6", "06"):
        fields["Primary Market"] = "Broward County"
    else:
        fields["Primary Market"] = "Other FL"

    if props >= 10:
        fields["Investor Type"] = "Professional Investor"
    elif props >= 5:
        fields["Investor Type"] = "Growth Investor"
    elif is_entity and props >= 2:
        fields["Investor Type"] = "Growth Investor"
    elif props >= 2:
        fields["Investor Type"] = "Lifestyle Investor"
    else:
        fields["Investor Type"] = "Accidental Landlord"

    fields["Lead Source"] = "FL DOR Records"
    fields["Lead Status"] = "New"
    fields["DNC Status"] = "Not Checked"
    fields["Consent Status"] = "No Consent"
    fields["Import Date"] = date.today().isoformat()

    phone_type = clean_str(row.get("phone_1_type")).lower()
    if phone_type in ("mobile", "cell"):
        fields["Phone Type"] = "Mobile"
    elif phone_type == "landline":
        fields["Phone Type"] = "Landline"
    elif phone_type == "voip":
        fields["Phone Type"] = "VoIP"
    elif phone1:
        fields["Phone Type"] = "Unknown"

    # === ICP SEGMENT ===
    hard_money = clean_str(row.get("est_hard_money")).lower() in ("true", "1")
    maturity_urgent = clean_str(row.get("est_maturity_urgent")).lower() in ("true", "1")
    cash_purchase = clean_str(row.get("est_cash_purchase")).lower() in ("true", "1")
    probable_cash = clean_str(row.get("probable_cash_buyer")).lower() in ("true", "1")

    if hard_money:
        fields["ICP Segment"] = "Hard Money Refi"
    elif maturity_urgent:
        fields["ICP Segment"] = "Maturity Refi"
    elif cash_purchase or probable_cash:
        fields["ICP Segment"] = "Cash Purchase Refi"
    elif props >= 5:
        fields["ICP Segment"] = "Portfolio Investor"
    else:
        fields["ICP Segment"] = "General DSCR"

    # === CAMPAIGN TAG ===
    market_prefix = "PB" if co_no == "60" else "Broward"
    if hard_money:
        fields["Campaign Tag"] = f"{market_prefix} Hard Money Q1"
    elif maturity_urgent:
        fields["Campaign Tag"] = f"{market_prefix} Maturity Q1"
    elif cash_purchase or probable_cash:
        fields["Campaign Tag"] = f"{market_prefix} Cash Purchase Q1"
    else:
        fields["Campaign Tag"] = "Manual Import"

    # === HAS TRIGGER ===
    has_refi = clean_str(row.get("_has_refi")).lower() in ("true", "1")
    fields["Has Trigger"] = has_refi

    # === CURRENT LENDERS ===
    best_lender = clean_str(row.get("best_lender"))
    if best_lender:
        fields["Current Lenders"] = clean_mers_lender(best_lender)[:100]

    # =================================================================
    # NEW SELF-CONTAINED FIELDS (bypass broken rollup chain)
    # =================================================================

    # --- Portfolio Fields ---
    if props:
        fields["Portfolio Properties"] = props
    total_val = safe_float(row.get("total_portfolio_value"))
    if total_val > 0:
        fields["Portfolio Value"] = total_val
    portfolio_equity = safe_float(row.get("est_portfolio_equity"))
    if portfolio_equity > 0:
        fields["Portfolio Equity"] = portfolio_equity
    equity_pct = safe_float(row.get("est_equity_pct"))
    if equity_pct > 0:
        fields["Equity Pct"] = equity_pct / 100  # Airtable percent is 0-1
    rent = safe_float(row.get("est_monthly_rent"))
    if rent > 0:
        fields["Est Monthly Rent"] = rent

    # --- Financing Fields ---
    rate = safe_float(row.get("est_interest_rate") or row.get("attom_interest_rate"))
    if rate > 0:
        fields["Loan Rate"] = rate / 100  # Airtable percent is 0-1
    loan_type = clean_str(row.get("est_loan_type") or row.get("attom_loan_type"))
    if loan_type:
        fields["Loan Type"] = loan_type.replace("_", " ").title()
    mat_date = clean_str(row.get("est_maturity_date") or row.get("attom_due_date"))
    if mat_date:
        if len(mat_date) == 7:
            mat_date += "-01"
        if len(mat_date) >= 10:
            fields["Loan Maturity"] = mat_date[:10]
    months_to_mat = safe_int(row.get("est_months_to_maturity"))
    if months_to_mat > 0:
        fields["Months to Maturity"] = months_to_mat
    if hard_money:
        fields["Hard Money"] = True

    # --- Activity Fields ---
    p12 = safe_int(row.get("purchases_last_12mo"))
    if p12 > 0:
        fields["Purchases Last 12mo"] = p12
    p36 = safe_int(row.get("purchases_last_36mo"))
    if p36 > 0:
        fields["Purchases Last 36mo"] = p36
    avg_price = safe_float(row.get("avg_purchase_price"))
    if avg_price > 0:
        fields["Avg Purchase Price"] = avg_price

    # --- Opportunity Score & Priority Tier ---
    opp_score, priority_tier = compute_opportunity_score(row)
    fields["Opportunity Score"] = opp_score
    fields["Priority Tier"] = priority_tier

    # =================================================================
    # CALL INTEL (text summaries — same as before)
    # =================================================================

    # --- Trigger Summary ---
    triggers = []
    refi_signals = clean_str(row.get("est_refi_signals") or row.get("refi_signals"))
    if refi_signals:
        triggers.append(refi_signals)
    if hard_money:
        if "Hard money" not in (refi_signals or ""):
            triggers.append("Hard money loan detected")
    if maturity_urgent:
        months = clean_str(row.get("est_months_to_maturity"))
        if months:
            triggers.append(f"Maturity in {months} months")
    if rate >= 7.0:
        triggers.append(f"High rate: {rate:.1f}%")
    if cash_purchase or probable_cash:
        eq = safe_float(row.get("est_portfolio_equity"))
        triggers.append(f"Cash purchase — ${eq:,.0f} equity, no leverage" if eq else "Cash purchase — unleveraged")

    if triggers:
        fields["Trigger Summary"] = "\n".join(triggers)[:1000]

    # --- Portfolio Snapshot ---
    snapshot_parts = []
    if props:
        val_str = f"${total_val:,.0f}" if total_val else "unknown value"
        snapshot_parts.append(f"{props} properties, {val_str} portfolio")
    if equity_pct > 0:
        eq_str = f"${portfolio_equity:,.0f}" if portfolio_equity else ""
        snapshot_parts.append(f"Est. equity: {equity_pct:.0f}% {eq_str}")
    acq = safe_int(row.get("total_acquisitions"))
    if acq:
        snapshot_parts.append(f"Acquisitions: {acq} total, {p12} last 12mo, {p36} last 36mo")
    if rent:
        snapshot_parts.append(f"Est. rent: ${rent:,.0f}/mo")
    dscr = safe_float(row.get("est_dscr"))
    if dscr:
        snapshot_parts.append(f"Est. DSCR: {dscr:.2f}")

    if snapshot_parts:
        fields["Portfolio Snapshot"] = "\n".join(snapshot_parts)

    # --- Estimated Monthly Savings ---
    if rate >= 7.0:
        balance = safe_float(row.get("est_remaining_balance") or row.get("attom_loan_amount"))
        if balance > 0:
            target_rate = 7.0
            monthly_savings = (rate - target_rate) / 100 * balance / 12
            if monthly_savings > 0:
                fields["Estimated Monthly Savings"] = round(monthly_savings, 2)

    # --- Years Investing ---
    freq = safe_float(row.get("purchase_frequency_months"))
    total_acq = safe_int(row.get("total_acquisitions"))
    if total_acq >= 2 and freq > 0:
        years = max(1, int(total_acq * freq / 12))
        fields["Years Investing"] = min(years, 50)

    return fields


def build_property(row: pd.Series) -> dict:
    """Build Airtable Properties record from CSV row."""
    fields = {}

    attom_addr = clean_str(row.get("attom_property_address"))
    if attom_addr:
        parsed = parse_address(attom_addr)
        fields["Property Address"] = parsed["street"]
        fields["City"] = parsed["city"]
        fields["State"] = parsed["state"]
        fields["ZIP"] = parsed["zip"]
    else:
        phy = clean_str(row.get("PHY_ADDR1"))
        if phy:
            first_addr = phy.split("|")[0].strip()
            fields["Property Address"] = first_addr.title()
        fields["State"] = "FL"

    co_no = clean_str(row.get("CO_NO"))
    if co_no == "60":
        fields["County"] = "Palm Beach"
    elif co_no in ("6", "06"):
        fields["County"] = "Broward"

    attom_type = clean_str(row.get("attom_property_type")).upper()
    prop_types = clean_str(row.get("property_types"))
    if "CONDOMINIUM" in attom_type or "CONDO" in attom_type:
        fields["Property Type"] = "Condo"
    elif "TOWNHOUSE" in attom_type:
        fields["Property Type"] = "Townhouse"
    elif "DUPLEX" in attom_type or "002" in prop_types:
        fields["Property Type"] = "Duplex"
    elif "TRIPLEX" in attom_type:
        fields["Property Type"] = "Triplex"
    elif "FOURPLEX" in attom_type or "QUADPLEX" in attom_type:
        fields["Property Type"] = "Fourplex"
    elif "SFR" in attom_type or "SINGLE" in attom_type or "001" in prop_types:
        fields["Property Type"] = "SFR"
    elif "MULTI" in attom_type or "APARTMENT" in attom_type or "004" in prop_types:
        fields["Property Type"] = "Multi 5-10"
    elif "COMMERCIAL" in attom_type:
        fields["Property Type"] = "Commercial"

    year = safe_int(row.get("attom_year_built"))
    if 1800 < year < 2030:
        fields["Year Built"] = year

    price = safe_float(row.get("most_recent_purchase_price") or row.get("most_recent_price"))
    avg_val = safe_float(row.get("avg_property_value"))
    if price > 0:
        fields["Estimated Property Value"] = price
        fields["Purchase Price"] = price
    elif avg_val > 0:
        fields["Estimated Property Value"] = avg_val

    purchase_date = clean_str(row.get("most_recent_purchase_date") or row.get("most_recent_purchase"))
    if purchase_date and len(purchase_date) >= 7:
        if len(purchase_date) == 7:
            purchase_date += "-01"
        fields["Purchase Date"] = purchase_date[:10]

    rent = safe_float(row.get("est_monthly_rent"))
    if rent > 0:
        fields["Estimated Monthly Rent"] = rent

    absentee = clean_str(row.get("attom_absentee")).upper()
    if absentee == "A":
        fields["Occupancy Status"] = "Tenant Occupied"
    elif absentee == "O":
        fields["Occupancy Status"] = "Owner Occupied"

    fields["Homestead Exempt"] = False

    return fields


def build_financing(row: pd.Series) -> dict:
    """Build Airtable Financing record from CSV row."""
    fields = {}

    best_lender = clean_str(row.get("best_lender"))
    if not best_lender:
        return {}

    fields["Current Lender"] = clean_mers_lender(best_lender)[:100]

    loan_type = clean_str(row.get("est_loan_type") or row.get("attom_loan_type")).lower()
    type_map = {
        "hard_money": "Hard Money",
        "conventional": "Conventional",
        "portfolio": "Bank Portfolio",
        "agency": "Conventional",
        "fha": "FHA",
        "va": "VA",
        "private": "Private Lender",
        "bridge": "Bridge",
        "heloc": "HELOC",
        "commercial": "Commercial",
    }
    mapped = type_map.get(loan_type, "")
    if mapped:
        fields["Loan Type"] = mapped
    else:
        lender_type = clean_str(row.get("best_lender_type")).lower()
        if "hard" in lender_type:
            fields["Loan Type"] = "Hard Money"
        elif "private" in lender_type:
            fields["Loan Type"] = "Private Lender"
        elif "bank" in lender_type:
            fields["Loan Type"] = "Bank Portfolio"
        elif "credit_union" in lender_type:
            fields["Loan Type"] = "Bank Portfolio"
        else:
            fields["Loan Type"] = "Unknown"

    fields["Loan Purpose"] = "Purchase"

    original = safe_float(row.get("est_original_loan") or row.get("attom_loan_amount"))
    if original > 0:
        fields["Original Loan Amount"] = original

    balance = safe_float(row.get("est_remaining_balance"))
    if balance > 0:
        fields["Estimated Loan Balance"] = balance

    rate = safe_float(row.get("est_interest_rate") or row.get("attom_interest_rate"))
    if rate > 0:
        fields["Interest Rate"] = rate / 100  # Airtable percent is 0-1

    attom_rate = clean_str(row.get("attom_rate_type")).upper()
    if "FIXED" in attom_rate:
        fields["Rate Type"] = "Fixed"
    elif "ARM" in attom_rate or "ADJ" in attom_rate or "VARIABLE" in attom_rate:
        fields["Rate Type"] = "ARM 5/1"
    elif rate > 0:
        fields["Rate Type"] = "Unknown"

    orig_date = clean_str(row.get("est_loan_origination") or row.get("attom_loan_date") or row.get("clerk_loan_date"))
    if orig_date:
        if "/" in orig_date:
            parts = orig_date.split("/")
            if len(parts) == 3:
                orig_date = f"{parts[2]}-{parts[0].zfill(2)}-{parts[1].zfill(2)}"
        if len(orig_date) == 7:
            orig_date += "-01"
        if len(orig_date) >= 10:
            fields["Loan Origination Date"] = orig_date[:10]

    mat_date = clean_str(row.get("est_maturity_date") or row.get("attom_due_date"))
    if mat_date:
        if len(mat_date) == 7:
            mat_date += "-01"
        if len(mat_date) >= 10:
            fields["Loan Maturity Date"] = mat_date[:10]

    term = safe_int(row.get("attom_loan_term"))
    if term > 0:
        fields["Loan Term (Months)"] = term

    payment = safe_float(row.get("est_monthly_payment"))
    if payment > 0:
        fields["Monthly Payment Estimate"] = payment

    clerk_doc = clean_str(row.get("clerk_instrument"))
    if clerk_doc:
        fields["Mortgage Document Number"] = clerk_doc

    return fields


def build_entity(row: pd.Series) -> dict:
    """Build Airtable Ownership Entities record from CSV row."""
    own_name = clean_str(row.get("OWN_NAME"))
    is_entity = clean_str(row.get("is_entity")).lower() in ("true", "1", "yes")
    if not is_entity or not own_name:
        return {}

    fields = {"Entity Name": own_name.title()}

    name_upper = own_name.upper()
    if " LLC" in name_upper or "L.L.C" in name_upper:
        fields["Entity Type"] = "LLC"
    elif " INC" in name_upper or " CORP" in name_upper:
        fields["Entity Type"] = "Corporation"
    elif " TRUST" in name_upper:
        fields["Entity Type"] = "Trust"
    elif " LP" in name_upper or "LIMITED PARTNER" in name_upper:
        fields["Entity Type"] = "Limited Partnership"
    else:
        fields["Entity Type"] = "LLC"

    fields["State of Incorporation"] = "Florida"

    status = clean_str(row.get("sunbiz_status"))
    status_map = {"ACTIVE": "Active", "INACTIVE": "Inactive",
                  "DISSOLVED": "Dissolved", "ADMIN DISSOLVED": "Admin Dissolved"}
    if status.upper() in status_map:
        fields["Status"] = status_map[status.upper()]

    agent = clean_str(row.get("registered_agent_name"))
    if agent:
        fields["Registered Agent"] = agent.title()

    agent_addr = clean_str(row.get("registered_agent_address"))
    if agent_addr:
        fields["Registered Address"] = agent_addr.title()

    return fields


# ---------------------------------------------------------------------------
# Batch API operations
# ---------------------------------------------------------------------------

def delete_all_records(table_id: str, table_name: str):
    """Delete all records from a table."""
    url = f"https://api.airtable.com/v0/{BASE_ID}/{table_id}"
    total_deleted = 0

    while True:
        # Fetch up to 100 record IDs (no fields param — just get IDs)
        resp = api_call("GET", f"{url}?pageSize=100")
        if not resp or not resp.get("records"):
            break

        ids = [r["id"] for r in resp["records"]]
        if not ids:
            break

        # Delete in batches of 10
        for i in range(0, len(ids), 10):
            batch = ids[i:i + 10]
            params = "&".join(f"records[]={rid}" for rid in batch)
            result = api_call("DELETE", f"{url}?{params}")
            if result:
                total_deleted += len(batch)

    print(f"  Deleted {total_deleted} records from {table_name}")
    return total_deleted


def create_records_batch(table_id: str, records: list) -> list:
    """Create records in batches of 10. Returns list of created record IDs."""
    url = f"https://api.airtable.com/v0/{BASE_ID}/{table_id}"
    created_ids = []

    for i in range(0, len(records), 10):
        batch = records[i:i + 10]
        payload = {"records": [{"fields": r} for r in batch]}
        result = api_call("POST", url, json=payload)
        if result and "records" in result:
            batch_ids = [r["id"] for r in result["records"]]
            created_ids.extend(batch_ids)
        else:
            created_ids.extend([None] * len(batch))

    return created_ids


def update_records_batch(table_id: str, updates: list):
    """Update records in batches of 10. Each update is {id, fields}."""
    url = f"https://api.airtable.com/v0/{BASE_ID}/{table_id}"
    success = 0

    for i in range(0, len(updates), 10):
        batch = updates[i:i + 10]
        payload = {"records": [{"id": u["id"], "fields": u["fields"]} for u in batch]}
        result = api_call("PATCH", url, json=payload)
        if result and "records" in result:
            success += len(result["records"])

    return success


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Full CRM upload to Airtable")
    parser.add_argument("--count", type=int, default=25)
    parser.add_argument("--input", type=str, default=DEFAULT_INPUT)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--no-delete", action="store_true")
    args = parser.parse_args()

    if not args.dry_run and not API_TOKEN:
        print("ERROR: AIRTABLE_API_TOKEN not set")
        sys.exit(1)

    # Load data
    df = pd.read_csv(args.input, dtype=str, low_memory=False)
    print(f"\nLoaded {len(df)} leads from {args.input}")

    # Sort by score, take top N
    df["_sort"] = df.get("_score", pd.Series([0] * len(df))).apply(safe_float)
    df = df.sort_values("_sort", ascending=False).head(args.count)
    df = df.drop(columns=["_sort"])
    print(f"Selected top {len(df)} by score")

    # Build all records
    investors = []
    properties = []
    financing = []
    entities = []

    for idx, (_, row) in enumerate(df.iterrows()):
        inv = build_investor(row)
        if not inv.get("Full Name"):
            continue

        prop = build_property(row)
        fin = build_financing(row)
        ent = build_entity(row)

        investors.append(inv)
        properties.append(prop if prop.get("Property Address") or prop.get("County") else {})
        financing.append(fin)
        entities.append(ent)

    print(f"\nBuilt records:")
    print(f"  Investors:  {len(investors)}")
    print(f"  Properties: {sum(1 for p in properties if p)}")
    print(f"  Financing:  {sum(1 for f in financing if f)}")
    print(f"  Entities:   {sum(1 for e in entities if e)}")

    # Show score distribution
    tier_counts = {}
    for inv in investors:
        tier = inv.get("Priority Tier", "Unknown")
        tier_counts[tier] = tier_counts.get(tier, 0) + 1
    print(f"\n  Score distribution:")
    for tier in sorted(tier_counts.keys()):
        print(f"    {tier}: {tier_counts[tier]}")

    if args.dry_run:
        print(f"\n{'='*60}")
        print("DRY RUN — Sample records:")
        print(f"{'='*60}")
        for i in range(min(3, len(investors))):
            print(f"\n--- Investor {i+1}: {investors[i].get('Full Name', '?')} ---")
            print(f"  Opportunity Score: {investors[i].get('Opportunity Score')}")
            print(f"  Priority Tier: {investors[i].get('Priority Tier')}")
            print(f"  Portfolio Properties: {investors[i].get('Portfolio Properties')}")
            print(f"  Portfolio Value: {investors[i].get('Portfolio Value')}")
            print(f"  Hard Money: {investors[i].get('Hard Money')}")
            print(f"  Loan Rate: {investors[i].get('Loan Rate')}")
            print(f"  Months to Maturity: {investors[i].get('Months to Maturity')}")
            print(f"  Phone: {investors[i].get('Phone (Mobile)', 'NONE')}")
            print(f"  ICP Segment: {investors[i].get('ICP Segment')}")
            trigger = investors[i].get('Trigger Summary', '')
            if trigger:
                # Replace Unicode arrows with ASCII for Windows console
                safe_trigger = trigger[:120].encode('ascii', 'replace').decode('ascii')
                print(f"  Trigger Summary: {safe_trigger}")
            if properties[i]:
                print(f"  --- Property ---")
                for k, v in properties[i].items():
                    print(f"    {k}: {v}")
            if financing[i]:
                print(f"  --- Financing ---")
                for k, v in financing[i].items():
                    print(f"    {k}: {v}")
        return

    # ---- STEP 1: Clean existing records ----
    if not args.no_delete:
        print(f"\n{'='*60}")
        print("Step 1: Cleaning existing records")
        print(f"{'='*60}")
        for name, tid in TABLES.items():
            delete_all_records(tid, name)

    # ---- STEP 2: Create Investors ----
    print(f"\n{'='*60}")
    print(f"Step 2: Creating {len(investors)} Investors")
    print(f"{'='*60}")
    investor_ids = create_records_batch(TABLES["investors"], investors)
    inv_ok = sum(1 for x in investor_ids if x)
    print(f"  Created: {inv_ok}/{len(investors)}")

    # ---- STEP 3: Create Properties (linked to Investors) ----
    prop_records = []
    prop_index_map = []
    for i, prop in enumerate(properties):
        if prop and investor_ids[i]:
            prop["Owner Investor"] = [investor_ids[i]]
            prop_records.append(prop)
            prop_index_map.append(i)

    print(f"\n{'='*60}")
    print(f"Step 3: Creating {len(prop_records)} Properties")
    print(f"{'='*60}")
    property_ids_list = create_records_batch(TABLES["properties"], prop_records)
    prop_ok = sum(1 for x in property_ids_list if x)
    print(f"  Created: {prop_ok}/{len(prop_records)}")

    property_ids = [None] * len(investors)
    for j, orig_idx in enumerate(prop_index_map):
        property_ids[orig_idx] = property_ids_list[j] if j < len(property_ids_list) else None

    # ---- STEP 4: Create Financing (linked to Properties) ----
    fin_records = []
    for i, fin in enumerate(financing):
        if fin and property_ids[i]:
            fin["Property"] = [property_ids[i]]
            fin_records.append(fin)

    print(f"\n{'='*60}")
    print(f"Step 4: Creating {len(fin_records)} Financing records")
    print(f"{'='*60}")
    fin_ids = []
    if fin_records:
        fin_ids = create_records_batch(TABLES["financing"], fin_records)
        fin_ok = sum(1 for x in fin_ids if x)
        print(f"  Created: {fin_ok}/{len(fin_records)}")
    else:
        print("  No financing records to create")

    # ---- STEP 5: Create Ownership Entities (linked to Investors) ----
    ent_records = []
    for i, ent in enumerate(entities):
        if ent and investor_ids[i]:
            ent["Investor (Owner)"] = [investor_ids[i]]
            ent_records.append(ent)

    print(f"\n{'='*60}")
    print(f"Step 5: Creating {len(ent_records)} Ownership Entities")
    print(f"{'='*60}")
    ent_ids = []
    if ent_records:
        ent_ids = create_records_batch(TABLES["entities"], ent_records)
        ent_ok = sum(1 for x in ent_ids if x)
        print(f"  Created: {ent_ok}/{len(ent_records)}")
    else:
        print("  No entity records to create")

    # ---- SUMMARY ----
    print(f"\n{'='*60}")
    print("UPLOAD COMPLETE")
    print(f"{'='*60}")
    print(f"  Investors:  {inv_ok}")
    print(f"  Properties: {prop_ok}")
    print(f"  Financing:  {sum(1 for x in fin_ids if x)}")
    print(f"  Entities:   {sum(1 for x in ent_ids if x)}")
    print()
    print("  Score distribution:")
    for tier in sorted(tier_counts.keys()):
        print(f"    {tier}: {tier_counts[tier]}")
    print()
    print("  NEXT: Open Airtable and verify data")
    print("  Then run: python airtable/refresh_call_queue.py")
    print()


if __name__ == "__main__":
    main()
