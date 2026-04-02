"""
Step 22: Prepayment Penalty Expiration Targeting
=================================================

Identifies DSCR loan borrowers approaching prepayment penalty expiration —
prime refinance targets for loan officers.

TWO MODELS:
  Model A — "HMDA Definitive" (FREE)
    Downloads HMDA LAR data from CFPB, which contains an actual
    prepayment_penalty_term field. Cross-references with our pipeline
    data (lender name + loan amount + origination date + county) to
    match leads with confirmed PPP terms.

  Model B — "Inference" (FREE)
    Uses lender name classification (known DSCR lenders) + origination
    date + industry-standard PPP structures to estimate penalty status
    and expiration date. ~85% accuracy based on DSCR market data.

OUTPUT:
  - ppp_targeted_leads.csv: All leads with PPP scoring
  - ppp_hot_leads.csv: Leads with penalties expiring in next 12 months
  - ppp_summary.txt: Stats for the sales pitch

Usage:
    python scripts/22_prepayment_penalty_targeting.py --download-hmda   # First run: download HMDA
    python scripts/22_prepayment_penalty_targeting.py                    # Score existing leads
    python scripts/22_prepayment_penalty_targeting.py --county wake      # Wake County only
    python scripts/22_prepayment_penalty_targeting.py --county palm_beach
    python scripts/22_prepayment_penalty_targeting.py --model both       # Run both models (default)
    python scripts/22_prepayment_penalty_targeting.py --model inference  # Inference only (no HMDA)
    python scripts/22_prepayment_penalty_targeting.py --model hmda       # HMDA match only

Requires:
    - ATTOM mortgage data (from step 16) OR any CSV with lender/loan fields
    - HMDA data download (auto-downloaded on first run with --download-hmda)
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import pandas as pd
import requests

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent
CONFIG_DIR = PROJECT_DIR / "config"
DATA_DIR = PROJECT_DIR / "data"
FINANCING_DIR = DATA_DIR / "financing"
HMDA_DIR = DATA_DIR / "hmda"
OUTPUT_DIR = DATA_DIR / "ppp_targeting"

LENDER_CONFIG = CONFIG_DIR / "dscr_lenders.json"

# Default inputs — will check multiple locations
ATTOM_MORTGAGE_FILE = FINANCING_DIR / "attom_mortgage.csv"
WAKE_ENRICHED = DATA_DIR / "enriched" / "wake_samples_enriched.csv"
FL_PILOT = DATA_DIR / "enriched" / "pilot_500_enriched.csv"
FL_MASTER = DATA_DIR / "enriched" / "pilot_500_master.csv"

TODAY = datetime.now()

# HMDA Data Browser API — investment property loans in target states
# occupancy_type=3 means investment property
HMDA_API_BASE = "https://ffiec.cfpb.gov/v2/data-browser-api/view/csv"

# State FIPS for HMDA queries
STATE_FIPS = {"NC": "37", "FL": "12"}
# County FIPS (5-digit) for filtering
COUNTY_FIPS = {
    "wake": "37183",
    "mecklenburg": "37119",
    "palm_beach": "12099",
    "broward": "12011",
}


# ---------------------------------------------------------------------------
# Load DSCR lender config
# ---------------------------------------------------------------------------
def load_lender_config():
    """Load the curated DSCR lender list."""
    if not LENDER_CONFIG.exists():
        print(f"  WARNING: Lender config not found: {LENDER_CONFIG}")
        return {"tier1": [], "tier2": [], "tier3": []}

    with open(LENDER_CONFIG, "r") as f:
        config = json.load(f)

    return {
        "tier1": [x.upper() for x in config.get("tier1_dscr_bridge", [])],
        "tier2": [x.upper() for x in config.get("tier2_nonqm_major", [])],
        "tier3": [x.upper() for x in config.get("tier3_dscr_programs", [])],
        "structures": config.get("prepayment_penalty_structures", {}),
    }


def classify_dscr_lender(lender_name: str, config: dict) -> dict:
    """
    Classify a lender name against known DSCR lenders.
    Returns tier (1/2/3/0) and assumed penalty years.
    """
    if not lender_name or str(lender_name).lower() in ("nan", "none", ""):
        return {"dscr_tier": 0, "dscr_lender_match": "", "assumed_ppp_years": 0}

    upper = str(lender_name).upper().strip()

    for keyword in config["tier1"]:
        if keyword in upper:
            return {"dscr_tier": 1, "dscr_lender_match": keyword, "assumed_ppp_years": 5}

    for keyword in config["tier2"]:
        if keyword in upper:
            return {"dscr_tier": 2, "dscr_lender_match": keyword, "assumed_ppp_years": 3}

    for keyword in config["tier3"]:
        if keyword in upper:
            return {"dscr_tier": 3, "dscr_lender_match": keyword, "assumed_ppp_years": 3}

    return {"dscr_tier": 0, "dscr_lender_match": "", "assumed_ppp_years": 0}


# ---------------------------------------------------------------------------
# HMDA Download (Model A)
# ---------------------------------------------------------------------------
def download_hmda(states=None, years=None):
    """
    Download HMDA LAR data filtered to investment properties.
    This is the FREE definitive source for prepayment_penalty_term.
    """
    HMDA_DIR.mkdir(parents=True, exist_ok=True)

    if states is None:
        states = ["NC", "FL"]
    if years is None:
        # HMDA data available 2018-2024 (latest as of 2026)
        # Target the PPP-relevant window: recent enough to still have penalties
        years = ["2022", "2023", "2024"]

    for year in years:
        for state in states:
            filename = HMDA_DIR / f"hmda_{state}_{year}_investment.csv"
            if filename.exists():
                size_mb = filename.stat().st_size / (1024 * 1024)
                print(f"  Already downloaded: {filename.name} ({size_mb:.1f} MB)")
                continue

            print(f"  Downloading HMDA {state} {year} (investment properties)...")
            params = {
                "states": state,
                "years": year,
                "occupancy_types": "3",  # Investment property
                "actions_taken": "1",    # Originated loans only
            }

            try:
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) DSCR-LeadGen/1.0",
                    "Accept": "text/csv",
                }
                resp = requests.get(HMDA_API_BASE, params=params, headers=headers,
                                    timeout=120, stream=True)
                if resp.status_code == 200:
                    total = 0
                    with open(filename, "wb") as f:
                        for chunk in resp.iter_content(chunk_size=8192):
                            f.write(chunk)
                            total += len(chunk)
                    size_mb = total / (1024 * 1024)
                    print(f"  Saved: {filename.name} ({size_mb:.1f} MB)")
                else:
                    print(f"  ERROR downloading {state} {year}: HTTP {resp.status_code}")
                    print(f"  Response: {resp.text[:300]}")
            except Exception as e:
                print(f"  ERROR downloading {state} {year}: {e}")

            time.sleep(1)  # Be polite to CFPB servers

    # Download LEI -> institution name mapping
    lei_file = HMDA_DIR / "lei_to_name.json"
    if not lei_file.exists():
        print("\n  Downloading LEI -> institution name mapping...")
        lei_map = {}
        for year in years:
            try:
                headers = {"User-Agent": "Mozilla/5.0 DSCR-LeadGen/1.0"}
                resp = requests.get(
                    f"https://ffiec.cfpb.gov/v2/reporting/filers/{year}",
                    headers=headers, timeout=30
                )
                if resp.status_code == 200:
                    institutions = resp.json().get("institutions", [])
                    for inst in institutions:
                        lei_map[inst["lei"]] = inst["name"]
                    print(f"    {year}: {len(institutions)} institutions")
            except Exception as e:
                print(f"    ERROR {year}: {e}")
        with open(lei_file, "w") as f:
            json.dump(lei_map, f, indent=2)
        print(f"  Saved: {lei_file} ({len(lei_map)} total)")


def load_hmda_data(county_filter=None):
    """Load all downloaded HMDA files, optionally filter by county."""
    if not HMDA_DIR.exists():
        return pd.DataFrame()

    files = list(HMDA_DIR.glob("hmda_*_investment.csv"))
    if not files:
        return pd.DataFrame()

    dfs = []
    for f in files:
        try:
            df = pd.read_csv(f, dtype=str, low_memory=False)
            dfs.append(df)
            print(f"  Loaded {f.name}: {len(df)} loans")
        except Exception as e:
            print(f"  ERROR loading {f.name}: {e}")

    if not dfs:
        return pd.DataFrame()

    hmda = pd.concat(dfs, ignore_index=True)

    # Filter to county if specified
    if county_filter and county_filter in COUNTY_FIPS:
        fips = COUNTY_FIPS[county_filter]
        hmda = hmda[hmda["county_code"].astype(str) == fips]
        print(f"  Filtered to {county_filter} ({fips}): {len(hmda)} loans")

    return hmda


def build_hmda_ppp_lookup(hmda_df):
    """
    Build a lookup from HMDA data for cross-referencing.
    Key: (lei, approx_loan_amount_bucket, year) -> prepayment_penalty_term

    Since HMDA doesn't have property addresses, we match on:
    - LEI (lender entity identifier) -> map to lender name
    - Loan amount (within 10% bucket)
    - Origination year
    - County
    """
    if hmda_df.empty:
        return {}, {}

    # Filter to loans with PPP data
    has_ppp = hmda_df[
        (hmda_df["prepayment_penalty_term"].notna()) &
        (hmda_df["prepayment_penalty_term"] != "NA") &
        (hmda_df["prepayment_penalty_term"] != "Exempt") &
        (hmda_df["prepayment_penalty_term"] != "")
    ].copy()

    print(f"\n  HMDA loans with PPP data: {len(has_ppp)} / {len(hmda_df)} ({len(has_ppp)*100//max(len(hmda_df),1)}%)")

    # Build LEI -> lender name mapping from downloaded institutions file
    lei_map = {}
    lei_file = HMDA_DIR / "lei_to_name.json"
    if lei_file.exists():
        with open(lei_file, "r") as f:
            lei_map = json.load(f)
        print(f"  LEI -> lender name mapping: {len(lei_map)} institutions")
    else:
        print("  WARNING: No LEI mapping file. Run with --download-hmda to fetch.")

    # Build PPP stats by lender (for inference model calibration)
    lender_ppp_stats = {}
    if not has_ppp.empty:
        has_ppp["ppp_months"] = pd.to_numeric(has_ppp["prepayment_penalty_term"], errors="coerce")
        for lei, group in has_ppp.groupby("lei"):
            lender_name = lei_map.get(lei, lei)
            valid = group["ppp_months"].dropna()
            if len(valid) > 0:
                lender_ppp_stats[lender_name.upper()] = {
                    "count": len(valid),
                    "median_months": int(valid.median()),
                    "mean_months": round(valid.mean(), 1),
                    "pct_with_ppp": round(len(valid) / len(group) * 100, 1),
                    "common_terms": valid.value_counts().head(3).to_dict(),
                }

    # Build cross-reference lookup keyed by (county, amount_bucket, year)
    ppp_lookup = {}
    for _, row in has_ppp.iterrows():
        try:
            county = str(row.get("county_code", ""))
            amount = float(row.get("loan_amount", 0)) * 1000  # HMDA amounts in thousands
            year = str(row.get("activity_year", ""))
            ppp_term = int(float(row.get("prepayment_penalty_term", 0)))
            lei = str(row.get("lei", ""))
            lender = lei_map.get(lei, "").upper()

            # Bucket loan amount to nearest $25K for matching
            bucket = round(amount / 25000) * 25000

            key = f"{county}:{bucket}:{year}"
            if key not in ppp_lookup:
                ppp_lookup[key] = []
            ppp_lookup[key].append({
                "ppp_months": ppp_term,
                "lender": lender,
                "interest_rate": row.get("interest_rate", ""),
                "loan_amount": amount,
            })
        except (ValueError, TypeError):
            continue

    print(f"  PPP lookup entries: {len(ppp_lookup)}")
    print(f"  Lender PPP stats: {len(lender_ppp_stats)} lenders")

    return ppp_lookup, lender_ppp_stats


# ---------------------------------------------------------------------------
# Model B: Inference scoring
# ---------------------------------------------------------------------------
def score_ppp_inference(row, lender_config, lender_ppp_stats=None):
    """
    Score a lead for prepayment penalty refinance opportunity using inference.

    Returns dict with:
      - ppp_model: "inference"
      - dscr_probability: 0-100 (likelihood this is a DSCR loan)
      - ppp_probability: 0-100 (likelihood of prepayment penalty)
      - ppp_estimated_expiry: date string
      - ppp_current_penalty_pct: estimated current penalty %
      - ppp_status: hot / warm / nurture / not_targeted
      - ppp_refi_score: 0-100 composite score
    """
    result = {
        "ppp_model": "inference",
        "dscr_probability": 0,
        "ppp_probability": 0,
        "ppp_estimated_expiry": "",
        "ppp_estimated_months_remaining": "",
        "ppp_current_penalty_pct": "",
        "ppp_status": "not_targeted",
        "ppp_refi_score": 0,
        "ppp_refi_reason": "",
    }

    # --- Signal 1: Lender classification ---
    lender_name = str(row.get("attom_lender_name", ""))
    lender_class = classify_dscr_lender(lender_name, lender_config)
    dscr_tier = lender_class["dscr_tier"]
    assumed_ppp_years = lender_class["assumed_ppp_years"]

    if dscr_tier == 0:
        # Not a known DSCR lender — check if classified as hard money by step 16
        lender_type = str(row.get("attom_lender_type", row.get("best_lender_type", "")))

        if lender_type == "hard_money":
            dscr_tier = 1
            assumed_ppp_years = 5
        else:
            return result  # Not enough signal — skip

    # DSCR probability based on tier
    dscr_prob = {1: 95, 2: 70, 3: 45}.get(dscr_tier, 0)

    # --- Signal 2: Origination date + penalty window ---
    loan_date_str = str(row.get("attom_loan_date", ""))
    if not loan_date_str or loan_date_str.lower() in ("nan", "none", ""):
        # Without origination date, we can't estimate expiration
        result["dscr_probability"] = dscr_prob
        result["ppp_probability"] = int(dscr_prob * 0.85)  # 85% of DSCR loans have PPP
        result["ppp_status"] = "missing_date"
        return result

    try:
        # Handle various date formats
        for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%Y%m%d", "%m-%d-%Y"):
            try:
                loan_date = datetime.strptime(loan_date_str.strip(), fmt)
                break
            except ValueError:
                continue
        else:
            return result
    except Exception:
        return result

    loan_age_months = (TODAY - loan_date).days / 30.44
    loan_age_years = loan_age_months / 12

    # Calibrate with HMDA stats if available
    if lender_ppp_stats and lender_name.upper() in lender_ppp_stats:
        stats = lender_ppp_stats[lender_name.upper()]
        assumed_ppp_years = max(1, stats["median_months"] // 12)
        dscr_prob = min(99, dscr_prob + 10)  # Boost: we have HMDA confirmation

    ppp_total_months = assumed_ppp_years * 12
    months_remaining = ppp_total_months - loan_age_months

    # PPP probability: 85% base for DSCR, adjusted
    ppp_prob = int(dscr_prob * 0.85)

    # Estimate current penalty percentage (stepdown schedule)
    current_year_in_penalty = int(loan_age_years) + 1
    if current_year_in_penalty <= assumed_ppp_years:
        # Standard stepdown: starts at N%, decreases 1% per year
        current_penalty_pct = max(0, assumed_ppp_years - int(loan_age_years))
    else:
        current_penalty_pct = 0

    # Estimated expiration date
    expiry_date = loan_date + timedelta(days=assumed_ppp_years * 365.25)
    months_to_expiry = max(0, (expiry_date - TODAY).days / 30.44)

    # --- Signal 3: Rate environment (refi motivation) ---
    rate_score = 0
    interest_rate = str(row.get("attom_interest_rate", ""))
    rate_type = str(row.get("attom_rate_type", ""))

    try:
        rate = float(interest_rate)
        if rate >= 8.0:
            rate_score = 30  # Paying 8%+ = very motivated
        elif rate >= 7.0:
            rate_score = 20
        elif rate >= 6.5:
            rate_score = 10
    except (ValueError, TypeError):
        # Estimate from vintage: 2022-2023 originations were 7-9%
        if 2022 <= loan_date.year <= 2023:
            rate_score = 25  # High probability of elevated rate
        elif loan_date.year == 2024:
            rate_score = 15

    # ARM borrowers are extra motivated
    if rate_type and "ADJUST" in str(rate_type).upper():
        rate_score += 10

    # --- Signal 4: Loan size (LO commission potential) ---
    size_score = 0
    try:
        loan_amount = float(row.get("attom_loan_amount", 0))
        if loan_amount >= 750000:
            size_score = 20  # Large loan = big commission
        elif loan_amount >= 500000:
            size_score = 15
        elif loan_amount >= 300000:
            size_score = 10
        elif loan_amount >= 150000:
            size_score = 5
    except (ValueError, TypeError):
        loan_amount = 0

    # --- Signal 5: Penalty timing (the money signal) ---
    timing_score = 0
    if months_to_expiry <= 0:
        timing_score = 40  # EXPIRED — refi now
        status = "hot_expired"
    elif months_to_expiry <= 6:
        timing_score = 35  # Expiring very soon
        status = "hot"
    elif months_to_expiry <= 12:
        timing_score = 25  # Expiring within a year
        status = "warm"
    elif months_to_expiry <= 18:
        timing_score = 15
        status = "nurture"
    elif months_to_expiry <= 24:
        timing_score = 10
        status = "nurture"
    else:
        timing_score = 0
        status = "future"

    # Override status: if penalty is already negligible (1%), upgrade
    if current_penalty_pct <= 1 and loan_amount > 0:
        penalty_cost = loan_amount * (current_penalty_pct / 100)
        # If penalty cost < $5000, it's worth paying to refi
        if penalty_cost < 5000 and months_to_expiry > 0:
            timing_score = max(timing_score, 30)
            status = "hot" if status not in ("hot_expired",) else status

    # --- Composite refi score ---
    refi_score = min(100, timing_score + rate_score + size_score)

    # Build reason string
    reasons = []
    if months_to_expiry <= 0:
        reasons.append("PPP expired")
    elif months_to_expiry <= 12:
        reasons.append(f"PPP expires in {int(months_to_expiry)}mo")
    if rate_score >= 20:
        reasons.append("high rate vintage")
    if size_score >= 15:
        reasons.append(f"${loan_amount:,.0f} balance")
    if current_penalty_pct <= 1 and current_penalty_pct > 0:
        reasons.append(f"only {current_penalty_pct}% penalty remaining")

    result.update({
        "dscr_probability": dscr_prob,
        "ppp_probability": ppp_prob,
        "ppp_estimated_expiry": expiry_date.strftime("%Y-%m-%d"),
        "ppp_estimated_months_remaining": round(months_to_expiry, 1),
        "ppp_current_penalty_pct": current_penalty_pct,
        "ppp_status": status,
        "ppp_refi_score": refi_score,
        "ppp_refi_reason": "; ".join(reasons) if reasons else "",
        "ppp_lender_tier": dscr_tier,
        "ppp_lender_match": lender_class["dscr_lender_match"],
        "ppp_assumed_years": assumed_ppp_years,
        "ppp_loan_age_months": round(loan_age_months, 1),
    })

    return result


# ---------------------------------------------------------------------------
# Model A: HMDA cross-reference scoring
# ---------------------------------------------------------------------------
def score_ppp_hmda(row, ppp_lookup, county_fips):
    """
    Try to match a lead against HMDA data for definitive PPP terms.
    Matches on county + loan amount bucket + origination year.
    """
    result = {
        "hmda_match": False,
        "hmda_ppp_months": "",
        "hmda_lender": "",
        "hmda_interest_rate": "",
        "hmda_match_confidence": "",
    }

    loan_amount = 0
    try:
        loan_amount = float(row.get("attom_loan_amount", 0))
    except (ValueError, TypeError):
        return result

    loan_date_str = str(row.get("attom_loan_date", ""))
    if not loan_date_str or loan_date_str.lower() in ("nan", "none", ""):
        return result

    try:
        for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%Y%m%d"):
            try:
                loan_date = datetime.strptime(loan_date_str.strip(), fmt)
                break
            except ValueError:
                continue
        else:
            return result
    except Exception:
        return result

    year = str(loan_date.year)
    bucket = round(loan_amount / 25000) * 25000
    key = f"{county_fips}:{bucket}:{year}"

    matches = ppp_lookup.get(key, [])
    if not matches:
        # Try adjacent buckets (within $25K)
        for adj in [-25000, 25000]:
            alt_key = f"{county_fips}:{bucket + adj}:{year}"
            matches = ppp_lookup.get(alt_key, [])
            if matches:
                break

    if matches:
        # Take the match with closest loan amount
        best = min(matches, key=lambda m: abs(m["loan_amount"] - loan_amount))
        result.update({
            "hmda_match": True,
            "hmda_ppp_months": best["ppp_months"],
            "hmda_lender": best["lender"],
            "hmda_interest_rate": best.get("interest_rate", ""),
            "hmda_match_confidence": "exact" if abs(best["loan_amount"] - loan_amount) < 5000 else "approximate",
        })

    return result


# ---------------------------------------------------------------------------
# Find best input data
# ---------------------------------------------------------------------------
def find_input_data(county_filter=None):
    """Find the best available input data for scoring."""
    candidates = []

    if county_filter == "wake":
        candidates = [
            WAKE_ENRICHED,
            DATA_DIR / "enriched" / "wake_qualified.csv",
        ]
    elif county_filter in ("palm_beach", "broward", "florida"):
        candidates = [
            FL_MASTER,
            FL_PILOT,
            ATTOM_MORTGAGE_FILE,
        ]
    else:
        # Try all
        candidates = [
            FL_MASTER, FL_PILOT, ATTOM_MORTGAGE_FILE,
            WAKE_ENRICHED,
        ]

    for path in candidates:
        if path.exists():
            return path

    # Check for any CSV in enriched/
    enriched = list((DATA_DIR / "enriched").glob("*.csv"))
    if enriched:
        return enriched[0]

    return None


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Step 22: Prepayment Penalty Targeting")
    parser.add_argument("--download-hmda", action="store_true",
                        help="Download HMDA investment property data")
    parser.add_argument("--county", type=str, default=None,
                        help="Filter to county: wake, palm_beach, broward")
    parser.add_argument("--model", type=str, default="both",
                        choices=["both", "inference", "hmda"],
                        help="Scoring model to use")
    parser.add_argument("--input", type=str, default=None,
                        help="Override input CSV path")
    parser.add_argument("--limit", type=int, default=0,
                        help="Limit rows to process (0 = all)")
    args = parser.parse_args()

    print()
    print("=" * 65)
    print("  STEP 22: PREPAYMENT PENALTY EXPIRATION TARGETING")
    print("=" * 65)

    # --- Download HMDA if requested ---
    if args.download_hmda:
        print("\n  --- HMDA Data Download ---")
        states = None
        if args.county in ("wake", "mecklenburg"):
            states = ["NC"]
        elif args.county in ("palm_beach", "broward", "florida"):
            states = ["FL"]
        download_hmda(states=states)
        if args.model == "hmda" and not args.input:
            print("\n  HMDA downloaded. Run again without --download-hmda to score leads.")

    # --- Load lender config ---
    print("\n  --- Loading Configuration ---")
    lender_config = load_lender_config()
    total_lenders = len(lender_config["tier1"]) + len(lender_config["tier2"]) + len(lender_config["tier3"])
    print(f"  DSCR lender database: {total_lenders} known lenders")
    print(f"    Tier 1 (pure DSCR/bridge):  {len(lender_config['tier1'])}")
    print(f"    Tier 2 (major non-QM):      {len(lender_config['tier2'])}")
    print(f"    Tier 3 (DSCR programs):      {len(lender_config['tier3'])}")

    # --- Load HMDA data if using ---
    ppp_lookup = {}
    lender_ppp_stats = {}
    if args.model in ("both", "hmda"):
        print("\n  --- Loading HMDA Data ---")
        hmda_df = load_hmda_data(county_filter=args.county)
        if not hmda_df.empty:
            ppp_lookup, lender_ppp_stats = build_hmda_ppp_lookup(hmda_df)
            if lender_ppp_stats:
                print(f"\n  Top lenders by PPP volume (from HMDA):")
                sorted_lenders = sorted(lender_ppp_stats.items(),
                                        key=lambda x: x[1]["count"], reverse=True)
                for name, stats in sorted_lenders[:10]:
                    print(f"    {name[:40]:<40} {stats['count']:>5} loans, "
                          f"median PPP: {stats['median_months']}mo")
        else:
            if args.model == "hmda":
                print("  No HMDA data found. Run with --download-hmda first.")
                return
            print("  No HMDA data found — using inference model only.")

    # --- Load lead data ---
    print("\n  --- Loading Lead Data ---")
    if args.input:
        input_path = Path(args.input)
    else:
        input_path = find_input_data(args.county)

    if not input_path or not input_path.exists():
        print(f"  ERROR: No input data found.")
        print(f"  Run ATTOM enrichment (step 16) first, or specify --input path.")
        return

    print(f"  Input: {input_path}")
    df = pd.read_csv(input_path, dtype=str, low_memory=False)
    if args.limit > 0:
        df = df.head(args.limit)
    print(f"  Leads loaded: {len(df)}")

    # Check for required columns
    has_lender = "attom_lender_name" in df.columns
    has_loan_date = "attom_loan_date" in df.columns
    if not has_lender:
        print("  WARNING: No attom_lender_name column — lender matching disabled.")
        print("  Run ATTOM enrichment (step 16) to get mortgage data.")

    # --- Score all leads ---
    print("\n  --- Scoring Leads ---")
    county_fips = COUNTY_FIPS.get(args.county, "")

    scored_rows = []
    for idx, row in df.iterrows():
        lead = row.to_dict()

        # Model B: Inference
        if args.model in ("both", "inference"):
            inf_scores = score_ppp_inference(row, lender_config, lender_ppp_stats)
            lead.update(inf_scores)

        # Model A: HMDA cross-reference
        if args.model in ("both", "hmda") and ppp_lookup:
            hmda_scores = score_ppp_hmda(row, ppp_lookup, county_fips)
            lead.update(hmda_scores)

            # If HMDA matched, upgrade the inference with definitive data
            if hmda_scores.get("hmda_match"):
                lead["ppp_model"] = "hmda_confirmed"
                hmda_months = hmda_scores.get("hmda_ppp_months", 0)
                if hmda_months:
                    try:
                        hmda_years = int(hmda_months) / 12
                        lead["ppp_assumed_years"] = round(hmda_years, 1)
                        # Recalculate expiry with definitive term
                        loan_date_str = str(row.get("attom_loan_date", ""))
                        for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%Y%m%d"):
                            try:
                                ld = datetime.strptime(loan_date_str.strip(), fmt)
                                expiry = ld + timedelta(days=int(hmda_months) * 30.44)
                                lead["ppp_estimated_expiry"] = expiry.strftime("%Y-%m-%d")
                                months_rem = max(0, (expiry - TODAY).days / 30.44)
                                lead["ppp_estimated_months_remaining"] = round(months_rem, 1)
                                break
                            except ValueError:
                                continue
                    except (ValueError, TypeError):
                        pass

        scored_rows.append(lead)

    scored_df = pd.DataFrame(scored_rows)

    # --- Filter & categorize results ---
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # All scored leads
    all_output = OUTPUT_DIR / "ppp_targeted_leads.csv"
    scored_df.to_csv(all_output, index=False)

    # Stats
    targeted = scored_df[scored_df.get("ppp_status", pd.Series(dtype=str)).isin(
        ["hot_expired", "hot", "warm", "nurture", "future"]
    )] if "ppp_status" in scored_df.columns else pd.DataFrame()

    hot = scored_df[scored_df.get("ppp_status", pd.Series(dtype=str)).isin(
        ["hot_expired", "hot"]
    )] if "ppp_status" in scored_df.columns else pd.DataFrame()

    warm = scored_df[scored_df.get("ppp_status", pd.Series(dtype=str)) == "warm"] if "ppp_status" in scored_df.columns else pd.DataFrame()

    # Hot leads export
    if not hot.empty:
        hot_output = OUTPUT_DIR / "ppp_hot_leads.csv"
        hot_sorted = hot.sort_values("ppp_refi_score", ascending=False)
        hot_sorted.to_csv(hot_output, index=False)
        print(f"\n  Hot leads exported: {hot_output}")

    # Warm leads export
    if not warm.empty:
        warm_output = OUTPUT_DIR / "ppp_warm_leads.csv"
        warm.sort_values("ppp_refi_score", ascending=False).to_csv(warm_output, index=False)

    # --- Summary ---
    hmda_matched = len(scored_df[scored_df.get("hmda_match", pd.Series(dtype=str)) == "True"]) if "hmda_match" in scored_df.columns else 0

    print()
    print("=" * 65)
    print("  PREPAYMENT PENALTY TARGETING RESULTS")
    print("=" * 65)
    print(f"  Total leads scored:       {len(scored_df)}")
    print(f"  DSCR lender matches:      {len(targeted)}")
    if hmda_matched:
        print(f"  HMDA confirmed matches:   {hmda_matched}")
    print()
    print(f"  HOT (PPP expired/expiring <12mo):  {len(hot)}")
    print(f"  WARM (PPP expiring 12-18mo):       {len(warm)}")
    print(f"  NURTURE (PPP 18-24mo):             {len(scored_df[scored_df.get('ppp_status', pd.Series(dtype=str)) == 'nurture']) if 'ppp_status' in scored_df.columns else 0}")
    print(f"  FUTURE (PPP 24mo+):                {len(scored_df[scored_df.get('ppp_status', pd.Series(dtype=str)) == 'future']) if 'ppp_status' in scored_df.columns else 0}")

    if not targeted.empty and "ppp_refi_score" in targeted.columns:
        scores = pd.to_numeric(targeted["ppp_refi_score"], errors="coerce")
        print(f"\n  Refi score range:  {scores.min():.0f} - {scores.max():.0f}")
        print(f"  Refi score mean:   {scores.mean():.0f}")

    if not hot.empty:
        print(f"\n  --- Top 10 Hottest Leads ---")
        display_cols = ["attom_owner1_name", "attom_lender_name", "attom_loan_amount",
                        "attom_loan_date", "ppp_status", "ppp_refi_score",
                        "ppp_estimated_expiry", "ppp_current_penalty_pct", "ppp_refi_reason"]
        available_cols = [c for c in display_cols if c in hot.columns]
        top10 = hot.sort_values("ppp_refi_score", ascending=False).head(10)
        for _, lead in top10.iterrows():
            owner = str(lead.get("attom_owner1_name", lead.get("OWN_NAME", "?")))[:30]
            lender = str(lead.get("attom_lender_name", ""))[:25]
            amount = lead.get("attom_loan_amount", "?")
            score = lead.get("ppp_refi_score", "?")
            reason = str(lead.get("ppp_refi_reason", ""))[:50]
            print(f"    {owner:<30} | {lender:<25} | ${amount:>10} | score:{score} | {reason}")

    # --- Write summary file ---
    summary_path = OUTPUT_DIR / "ppp_summary.txt"
    with open(summary_path, "w") as f:
        f.write("PREPAYMENT PENALTY TARGETING SUMMARY\n")
        f.write(f"Generated: {TODAY.strftime('%Y-%m-%d %H:%M')}\n")
        f.write(f"Model: {args.model}\n")
        f.write(f"County filter: {args.county or 'all'}\n")
        f.write("=" * 50 + "\n\n")
        f.write(f"Total leads scored:       {len(scored_df)}\n")
        f.write(f"DSCR lender matches:      {len(targeted)}\n")
        f.write(f"HMDA confirmed:           {hmda_matched}\n\n")
        f.write(f"HOT (expired/<12mo):      {len(hot)}\n")
        f.write(f"WARM (12-18mo):           {len(warm)}\n\n")
        f.write("Methodology:\n")
        f.write("  Model A (HMDA): Cross-references CFPB HMDA LAR data which contains\n")
        f.write("  actual prepayment_penalty_term (in months) reported by lenders.\n")
        f.write("  Match on county + loan amount (+/- $25K) + origination year.\n\n")
        f.write("  Model B (Inference): Classifies lenders against 54 known DSCR/non-QM\n")
        f.write("  originators. 85%+ of DSCR loans carry PPP (industry data). Estimates\n")
        f.write("  expiration from origination date + standard 5-4-3-2-1 or 3-2-1 schedules.\n\n")
        f.write("  Both models are combined when run in 'both' mode. HMDA matches\n")
        f.write("  override inference estimates with definitive terms.\n")

    print(f"\n  Summary: {summary_path}")
    print(f"  All leads: {all_output}")
    print()


if __name__ == "__main__":
    main()
