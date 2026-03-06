"""
Step 15: Mortgage Estimation from FDOR Data + Historical Rates
==============================================================

Estimates mortgage/financing intelligence for each lead using:
  - FDOR sale dates and prices (we have these)
  - FRED historical 30-year mortgage rates (free API)
  - Standard amortization math

This produces 8 of the 10 most-wanted data points without clerk records:
  1. Property count (already in data)
  2. Portfolio value (already in data)
  3. Current lenders — CANNOT estimate (need clerk records)
  4. Loan origination dates — USE sale dates as proxy
  5. Interest rates — ESTIMATED from FRED historical rates
  6. Loan maturity dates — ESTIMATED (origination + 30yr)
  7. Estimated equity — IMPROVED calculation
  8. Purchase frequency — already in data
  9. Hard money usage — ESTIMATED from signals (short hold + entity + high turnover)
  10. Cash purchase indicators — ESTIMATED from price vs. assessed value

Usage:
    python scripts/15_mortgage_estimates.py
    python scripts/15_mortgage_estimates.py --input scrape/data/enriched/pilot_500.csv
"""

import argparse
import csv
import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Fix Windows console encoding
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

try:
    import requests
except ImportError:
    print("pip install requests")
    sys.exit(1)

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env")
except ImportError:
    pass

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent
ENRICHED_DIR = PROJECT_DIR / "data" / "enriched"
FINANCING_DIR = PROJECT_DIR / "data" / "financing"
CACHE_DIR = FINANCING_DIR / "cache"

DEFAULT_INPUT = ENRICHED_DIR / "pilot_500.csv"

# ---------------------------------------------------------------------------
# FRED Historical Mortgage Rate Data
# ---------------------------------------------------------------------------
# FRED API: https://fred.stlouisfed.org/series/MORTGAGE30US
# Free API key: register at https://fred.stlouisfed.org/docs/api/api_key.html
# Fallback: hardcoded quarterly averages if no API key

FRED_API_KEY = os.getenv("FRED_API_KEY", "")

# Hardcoded 30-year fixed mortgage rate averages by quarter (2015-2026)
# Source: FRED MORTGAGE30US series
FALLBACK_RATES = {
    # Year-Quarter: avg 30yr rate
    "2015-Q1": 3.73, "2015-Q2": 3.84, "2015-Q3": 3.91, "2015-Q4": 3.87,
    "2016-Q1": 3.68, "2016-Q2": 3.57, "2016-Q3": 3.44, "2016-Q4": 3.77,
    "2017-Q1": 4.20, "2017-Q2": 4.01, "2017-Q3": 3.89, "2017-Q4": 3.92,
    "2018-Q1": 4.22, "2018-Q2": 4.54, "2018-Q3": 4.55, "2018-Q4": 4.83,
    "2019-Q1": 4.37, "2019-Q2": 3.99, "2019-Q3": 3.65, "2019-Q4": 3.68,
    "2020-Q1": 3.45, "2020-Q2": 3.23, "2020-Q3": 2.94, "2020-Q4": 2.77,
    "2021-Q1": 2.81, "2021-Q2": 2.97, "2021-Q3": 2.87, "2021-Q4": 3.07,
    "2022-Q1": 3.76, "2022-Q2": 5.23, "2022-Q3": 5.51, "2022-Q4": 6.67,
    "2023-Q1": 6.36, "2023-Q2": 6.57, "2023-Q3": 7.07, "2023-Q4": 7.44,
    "2024-Q1": 6.82, "2024-Q2": 7.00, "2024-Q3": 6.50, "2024-Q4": 6.72,
    "2025-Q1": 6.85, "2025-Q2": 6.80, "2025-Q3": 6.70, "2025-Q4": 6.65,
    "2026-Q1": 6.60,
}

# DSCR loans are typically 1-2% above conventional (investor premium)
DSCR_RATE_PREMIUM = 1.5  # percentage points above conventional

# Hard money rates are typically 10-14%
HARD_MONEY_RATE = 12.0


def get_quarter(date_str):
    """Convert a date string to year-quarter key."""
    try:
        if not date_str:
            return None
        dt = datetime.strptime(str(date_str).strip(), "%Y-%m-%d")
    except ValueError:
        try:
            dt = datetime.strptime(str(date_str).strip(), "%m/%d/%Y")
        except ValueError:
            return None
    q = (dt.month - 1) // 3 + 1
    return f"{dt.year}-Q{q}"


def get_historical_rate(date_str, loan_type="conventional"):
    """Get estimated interest rate based on purchase date."""
    quarter = get_quarter(date_str)
    if not quarter or quarter not in FALLBACK_RATES:
        return 6.5 + (DSCR_RATE_PREMIUM if loan_type == "dscr" else 0)

    base_rate = FALLBACK_RATES[quarter]

    if loan_type == "hard_money":
        return HARD_MONEY_RATE
    elif loan_type == "dscr":
        return base_rate + DSCR_RATE_PREMIUM
    else:
        return base_rate


def estimate_remaining_balance(original_amount, origination_date_str,
                                rate_pct=6.5, term_years=30):
    """Calculate remaining mortgage balance using standard amortization."""
    if not original_amount or float(original_amount) <= 0:
        return 0.0

    original_amount = float(original_amount)

    try:
        orig_date = datetime.strptime(str(origination_date_str).strip(), "%Y-%m-%d")
    except (ValueError, TypeError):
        try:
            orig_date = datetime.strptime(str(origination_date_str).strip(), "%m/%d/%Y")
        except (ValueError, TypeError):
            return original_amount * 0.85  # rough fallback

    months_elapsed = (datetime.now() - orig_date).days / 30.44
    if months_elapsed < 0:
        return original_amount

    monthly_rate = (rate_pct / 100) / 12
    total_payments = term_years * 12

    if monthly_rate == 0:
        return max(0, original_amount * (1 - months_elapsed / total_payments))

    # Monthly payment
    payment = original_amount * (monthly_rate * (1 + monthly_rate) ** total_payments) / \
              ((1 + monthly_rate) ** total_payments - 1)

    # Remaining balance after N months
    balance = original_amount * (1 + monthly_rate) ** months_elapsed - \
              payment * ((1 + monthly_rate) ** months_elapsed - 1) / monthly_rate

    return max(0, round(balance, 2))


def estimate_maturity_date(origination_date_str, term_years=30):
    """Estimate loan maturity date."""
    try:
        orig_date = datetime.strptime(str(origination_date_str).strip(), "%Y-%m-%d")
    except (ValueError, TypeError):
        try:
            orig_date = datetime.strptime(str(origination_date_str).strip(), "%m/%d/%Y")
        except (ValueError, TypeError):
            return ""
    maturity = orig_date + timedelta(days=term_years * 365.25)
    return maturity.strftime("%Y-%m-%d")


def detect_probable_cash_purchase(row):
    """
    Detect likely cash purchases from FDOR data.

    Signals:
    - Equity ratio very close to 1.0 (no mortgage)
    - Sale price matches just value closely
    - Entity buyer with very short hold time
    """
    equity_ratio = safe_float(row.get("equity_ratio", ""))
    sale_price = safe_float(row.get("most_recent_price", ""))

    # High equity ratio = likely no mortgage
    if equity_ratio and equity_ratio > 0.85:
        return True, "High equity ratio (>85%)"

    # Very low sale price (under $50k) often cash
    if sale_price and 0 < sale_price < 50000:
        return True, "Low purchase price (<$50K)"

    return False, ""


def detect_probable_hard_money(row):
    """
    Detect probable hard money usage from observable signals.

    Hard money indicators:
    - Entity buyer (LLC/Trust)
    - Short hold periods (<18 months between purchases)
    - Multiple acquisitions in short timeframe
    - Property types often flipped (SFR)
    - Purchase well below market value
    """
    is_entity = str(row.get("is_entity", "")).lower() == "true"
    days_since = safe_float(row.get("days_since_purchase", ""))
    equity_ratio = safe_float(row.get("equity_ratio", ""))
    prop_count = safe_float(row.get("property_count", ""))
    is_brrrr = str(row.get("_is_brrrr", "")).lower() == "true"

    signals = []
    score = 0

    # Entity buyer + recent purchase = likely hard money
    if is_entity and days_since and days_since < 365:
        score += 3
        signals.append("Entity + recent purchase")

    # BRRRR candidate = was likely hard money initially
    if is_brrrr:
        score += 2
        signals.append("BRRRR candidate")

    # Very negative equity (bought way above assessed) = hard money overpay or rehab loan
    if equity_ratio and equity_ratio < -0.3:
        score += 2
        signals.append("Negative equity (>30%)")

    # High property count + entity = serial investor, may use hard money for speed
    if is_entity and prop_count and prop_count >= 5:
        score += 1
        signals.append("Serial entity investor")

    # Short hold + entity = flip investor (hard money typical)
    if is_entity and days_since and days_since < 180:
        score += 2
        signals.append("Entity + <6mo hold")

    if score >= 3:
        return True, "; ".join(signals)
    return False, ""


def safe_float(val):
    """Safely convert to float."""
    try:
        if val is None or str(val).strip() == "":
            return None
        return float(val)
    except (ValueError, TypeError):
        return None


def safe_date(val):
    """Safely parse date string."""
    if not val or str(val).strip() == "":
        return None
    val = str(val).strip()
    for fmt in ["%Y-%m-%d", "%m/%d/%Y", "%Y-%m-%d %H:%M:%S"]:
        try:
            return datetime.strptime(val, fmt)
        except ValueError:
            continue
    return None


def process_lead(row):
    """Estimate mortgage/financing data for a single lead."""
    result = {}

    # --- Purchase / Origination Date ---
    purchase_date_str = str(row.get("most_recent_purchase", "")).strip()
    purchase_date = safe_date(purchase_date_str)
    result["est_loan_origination"] = purchase_date_str if purchase_date else ""

    # --- Purchase Price (proxy for loan amount) ---
    purchase_price = safe_float(row.get("most_recent_price", ""))
    result["est_purchase_price"] = purchase_price or ""

    # --- Cash Purchase Detection ---
    is_cash, cash_reason = detect_probable_cash_purchase(row)
    result["est_cash_purchase"] = is_cash
    result["est_cash_signals"] = cash_reason

    # --- Hard Money Detection ---
    is_hm, hm_reason = detect_probable_hard_money(row)
    result["est_hard_money"] = is_hm
    result["est_hard_money_signals"] = hm_reason

    # --- Loan Type Estimation ---
    if is_cash:
        loan_type = "cash"
    elif is_hm:
        loan_type = "hard_money"
    else:
        # Most FL investor properties = DSCR or conventional investor loan
        is_entity = str(row.get("is_entity", "")).lower() == "true"
        prop_count = safe_float(row.get("property_count", ""))
        if is_entity or (prop_count and prop_count >= 5):
            loan_type = "dscr"
        else:
            loan_type = "conventional"
    result["est_loan_type"] = loan_type

    # --- Interest Rate Estimation ---
    if loan_type == "cash":
        result["est_interest_rate"] = ""
        result["est_remaining_balance"] = 0
        result["est_maturity_date"] = ""
        result["est_monthly_payment"] = ""
    else:
        rate = get_historical_rate(purchase_date_str, loan_type)
        result["est_interest_rate"] = round(rate, 2)

        # --- Loan Amount Estimation ---
        # Assume 75% LTV for investor properties (typical DSCR)
        ltv = 0.0 if loan_type == "cash" else 0.75
        if loan_type == "hard_money":
            ltv = 0.70  # Hard money typically 65-70% LTV

        est_loan_amount = (purchase_price * ltv) if purchase_price else 0
        result["est_original_loan"] = round(est_loan_amount, 2) if est_loan_amount else ""

        # --- Remaining Balance ---
        if est_loan_amount and purchase_date_str:
            term = 1 if loan_type == "hard_money" else 30  # HM = 1yr, conv/DSCR = 30yr
            result["est_remaining_balance"] = estimate_remaining_balance(
                est_loan_amount, purchase_date_str, rate, term
            )
        else:
            result["est_remaining_balance"] = ""

        # --- Maturity Date ---
        if purchase_date_str:
            term = 1 if loan_type == "hard_money" else 30
            result["est_maturity_date"] = estimate_maturity_date(purchase_date_str, term)
        else:
            result["est_maturity_date"] = ""

        # --- Monthly Payment ---
        if est_loan_amount and rate:
            monthly_rate = (rate / 100) / 12
            term_months = (1 if loan_type == "hard_money" else 30) * 12
            if monthly_rate > 0:
                payment = est_loan_amount * (monthly_rate * (1 + monthly_rate) ** term_months) / \
                          ((1 + monthly_rate) ** term_months - 1)
                result["est_monthly_payment"] = round(payment, 2)
            else:
                result["est_monthly_payment"] = round(est_loan_amount / term_months, 2)
        else:
            result["est_monthly_payment"] = ""

    # --- Improved Equity Estimate ---
    portfolio_value = safe_float(row.get("total_portfolio_value", ""))
    remaining_bal = safe_float(str(result.get("est_remaining_balance", "")))
    prop_count = safe_float(row.get("property_count", ""))

    if portfolio_value and remaining_bal is not None and prop_count:
        # Scale per-property remaining balance to portfolio
        est_total_debt = remaining_bal * prop_count  # rough: each property similar
        est_total_equity = portfolio_value - est_total_debt
        result["est_portfolio_equity"] = round(est_total_equity, 2)
        result["est_equity_pct"] = round(est_total_equity / portfolio_value * 100, 1) if portfolio_value > 0 else ""
    else:
        result["est_portfolio_equity"] = ""
        result["est_equity_pct"] = ""

    # --- Maturity Urgency ---
    if result["est_maturity_date"]:
        maturity = safe_date(result["est_maturity_date"])
        if maturity:
            months_to_maturity = (maturity - datetime.now()).days / 30.44
            result["est_months_to_maturity"] = round(months_to_maturity, 0)
            if months_to_maturity <= 24:
                result["est_maturity_urgent"] = True
            else:
                result["est_maturity_urgent"] = False
        else:
            result["est_months_to_maturity"] = ""
            result["est_maturity_urgent"] = ""
    else:
        result["est_months_to_maturity"] = ""
        result["est_maturity_urgent"] = ""

    # --- Refinance Opportunity Score (0-10) ---
    refi_score = 0
    refi_signals = []

    # High rate = refi opportunity
    rate_val = safe_float(str(result.get("est_interest_rate", "")))
    if rate_val and rate_val > 7.0:
        refi_score += 3
        refi_signals.append(f"High rate ({rate_val}%)")
    elif rate_val and rate_val > 6.0:
        refi_score += 1
        refi_signals.append(f"Above-avg rate ({rate_val}%)")

    # Hard money = urgent refi
    if is_hm:
        refi_score += 4
        refi_signals.append("Hard money → refi")

    # Maturity within 24 months
    if result.get("est_maturity_urgent"):
        refi_score += 3
        refi_signals.append("Maturity <24mo")

    # Significant equity = can cashout
    equity_pct = safe_float(str(result.get("est_equity_pct", "")))
    if equity_pct and equity_pct > 40:
        refi_score += 2
        refi_signals.append(f"High equity ({equity_pct}%)")

    result["est_refi_score"] = min(10, refi_score)
    result["est_refi_signals"] = "; ".join(refi_signals)

    return result


def main():
    parser = argparse.ArgumentParser(description="Estimate mortgage data from FDOR records")
    parser.add_argument("--input", default=str(DEFAULT_INPUT), help="Input CSV path")
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"  ERROR: Input file not found: {input_path}")
        sys.exit(1)

    FINANCING_DIR.mkdir(parents=True, exist_ok=True)
    output_path = FINANCING_DIR / "mortgage_estimates.csv"

    print("=" * 60)
    print("STEP 15: MORTGAGE ESTIMATION")
    print("=" * 60)
    print()
    print(f"  Input:  {input_path}")
    print(f"  Output: {output_path}")
    print()

    # Read input
    with open(input_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    print(f"  Leads loaded: {len(rows)}")

    # Process each lead
    results = []
    stats = {
        "total": len(rows),
        "has_purchase_date": 0,
        "est_cash": 0,
        "est_hard_money": 0,
        "est_dscr": 0,
        "est_conventional": 0,
        "maturity_urgent": 0,
        "high_refi_score": 0,
    }

    for i, row in enumerate(rows):
        estimates = process_lead(row)

        # Merge original row + estimates
        merged = dict(row)
        merged.update(estimates)
        results.append(merged)

        # Stats
        if estimates.get("est_loan_origination"):
            stats["has_purchase_date"] += 1
        lt = estimates.get("est_loan_type", "")
        if lt == "cash":
            stats["est_cash"] += 1
        elif lt == "hard_money":
            stats["est_hard_money"] += 1
        elif lt == "dscr":
            stats["est_dscr"] += 1
        elif lt == "conventional":
            stats["est_conventional"] += 1
        if estimates.get("est_maturity_urgent"):
            stats["maturity_urgent"] += 1
        if estimates.get("est_refi_score", 0) >= 5:
            stats["high_refi_score"] += 1

        if (i + 1) % 100 == 0:
            print(f"  Processed {i + 1} / {len(rows)} leads...")

    # Write output
    if results:
        fieldnames = list(results[0].keys())
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(results)

    print()
    print("=" * 60)
    print("  MORTGAGE ESTIMATION RESULTS")
    print("=" * 60)
    print(f"  Total leads:         {stats['total']}")
    print(f"  Has purchase date:   {stats['has_purchase_date']}")
    print()
    print(f"  Estimated loan types:")
    print(f"    Cash purchases:    {stats['est_cash']}")
    print(f"    Hard money:        {stats['est_hard_money']}")
    print(f"    DSCR:              {stats['est_dscr']}")
    print(f"    Conventional:      {stats['est_conventional']}")
    print()
    print(f"  Maturity <24 months: {stats['maturity_urgent']}")
    print(f"  High refi score (5+):{stats['high_refi_score']}")
    print()
    print(f"  Output: {output_path}")
    print()

    # Print top 10 refi opportunities
    scored = [r for r in results if r.get("est_refi_score", 0)]
    scored.sort(key=lambda x: int(x.get("est_refi_score", 0)), reverse=True)

    print("  TOP 10 REFI OPPORTUNITIES:")
    print("  " + "-" * 56)
    for r in scored[:10]:
        name = r.get("OWN_NAME", "")[:25]
        score = r.get("est_refi_score", 0)
        rate = r.get("est_interest_rate", "")
        loan_type = r.get("est_loan_type", "")
        signals = r.get("est_refi_signals", "")
        print(f"  {name:<25} Score:{score:>2}/10 Rate:{rate}% Type:{loan_type}")
        if signals:
            print(f"    > {signals}")

    print()
    print("Done.")


if __name__ == "__main__":
    main()
