"""
Step 16: ATTOM Mortgage & Owner Lookup
=======================================

Uses the ATTOM Data Solutions API to pull actual mortgage/lender data
and resolved owner names for each lead's properties.

This is the single most valuable enrichment step — it gives us:
  - Current lender name (e.g., "WELLS FARGO BANK NA")
  - Loan amount, date, type (conventional, ARM, commercial)
  - Interest rate type (fixed vs adjustable)
  - Due date / maturity
  - Title company used
  - Resolved owner name (person behind LLC)
  - Absentee owner status

Strategy: One lookup per owner using their first parcel ID.
  - Uses PAO parcel cache (owner → parcel IDs) built by script 12
  - Formats PBC APNs as XX-XX-XX-XX-XX-XXX-XXXX for ATTOM
  - Caches all results to avoid duplicate API calls
  - 500 calls/day limit on free tier

Usage:
    python scripts/16_attom_mortgage.py
    python scripts/16_attom_mortgage.py --limit 50
    python scripts/16_attom_mortgage.py --dry-run

Requires:
    ATTOM_API_KEY in .env (root or scrape/)
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import pandas as pd
import requests

try:
    from dotenv import load_dotenv
    # Try scrape/.env first, then root .env
    scrape_env = Path(__file__).resolve().parent.parent / ".env"
    root_env = Path(__file__).resolve().parent.parent.parent / ".env"
    load_dotenv(scrape_env)
    load_dotenv(root_env)
except ImportError:
    pass

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent
ENRICHED_DIR = PROJECT_DIR / "data" / "enriched"
FINANCING_DIR = PROJECT_DIR / "data" / "financing"
CACHE_DIR = FINANCING_DIR / "attom_cache"
PARCEL_CACHE = PROJECT_DIR / "data" / "history" / "sdf_cache" / "pao_parcel_cache.json"

DEFAULT_INPUT = ENRICHED_DIR / "pilot_500_enriched.csv"
OUTPUT_FILE = FINANCING_DIR / "attom_mortgage.csv"

ATTOM_BASE = "https://api.gateway.attomdata.com/propertyapi/v1.0.0"
ENDPOINT = "/property/detailmortgageowner"

# FIPS codes for target counties
FIPS_CODES = {
    "60": "12099",   # Palm Beach
    "16": "12011",   # Broward
}

# Rate limiting
REQUEST_DELAY = 0.5  # seconds between requests (conservative)


# ---------------------------------------------------------------------------
# APN formatting
# ---------------------------------------------------------------------------
def format_apn_pbc(raw_pcn: str) -> str:
    """Format PBC raw PCN (17 digits) to ATTOM APN format: XX-XX-XX-XX-XX-XXX-XXXX"""
    pcn = raw_pcn.strip().strip('"')
    if len(pcn) >= 17:
        return f"{pcn[0:2]}-{pcn[2:4]}-{pcn[4:6]}-{pcn[6:8]}-{pcn[8:10]}-{pcn[10:13]}-{pcn[13:17]}"
    elif len(pcn) >= 15:
        return f"{pcn[0:2]}-{pcn[2:4]}-{pcn[4:6]}-{pcn[6:8]}-{pcn[8:10]}-{pcn[10:13]}-{pcn[13:]}"
    return pcn  # return as-is if format unknown


def format_apn_broward(raw_folio: str) -> str:
    """Format Broward folio number for ATTOM. Broward uses 13-digit folios."""
    folio = raw_folio.strip().strip('"')
    # Broward folios are typically 13 digits, ATTOM may accept as-is
    return folio


# ---------------------------------------------------------------------------
# Cache
# ---------------------------------------------------------------------------
def load_cache() -> dict:
    cache_path = CACHE_DIR / "attom_mortgage_cache.json"
    if cache_path.exists():
        with open(cache_path, "r") as f:
            return json.load(f)
    return {}


def save_cache(cache: dict):
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    with open(CACHE_DIR / "attom_mortgage_cache.json", "w") as f:
        json.dump(cache, f, indent=2, default=str)


# ---------------------------------------------------------------------------
# ATTOM API call
# ---------------------------------------------------------------------------
def lookup_property(api_key: str, apn: str, fips: str) -> dict:
    """Look up a single property by APN + FIPS code."""
    headers = {"apikey": api_key, "Accept": "application/json"}
    params = {"apn": apn, "fips": fips}

    resp = requests.get(
        f"{ATTOM_BASE}{ENDPOINT}",
        params=params,
        headers=headers,
        timeout=20,
    )

    if resp.status_code == 200:
        data = resp.json()
        properties = data.get("property", [])
        if properties:
            return properties[0]
    elif resp.status_code == 429:
        print("    RATE LIMITED - stopping to preserve quota")
        return {"_rate_limited": True}

    return {}


def extract_mortgage_data(prop: dict) -> dict:
    """Extract mortgage + owner fields from ATTOM property response."""
    mortgage = prop.get("mortgage", {})
    owner = prop.get("owner", {})
    address = prop.get("address", {})
    summary = prop.get("summary", {})

    lender = mortgage.get("lender", {})
    title = mortgage.get("title", {})
    owner1 = owner.get("owner1", {})
    owner2 = owner.get("owner2", {})

    return {
        # Lender data
        "attom_lender_name": lender.get("lastname", ""),
        "attom_lender_city": lender.get("city", ""),
        "attom_lender_state": lender.get("state", ""),
        "attom_title_company": title.get("companyname", ""),
        "attom_loan_amount": mortgage.get("amount", ""),
        "attom_loan_date": mortgage.get("date", ""),
        "attom_loan_type": mortgage.get("loantypecode", ""),
        "attom_interest_rate": mortgage.get("interestrate", ""),
        "attom_rate_type": mortgage.get("interestratetype", ""),
        "attom_deed_type": mortgage.get("deedtype", ""),
        "attom_due_date": mortgage.get("duedate", ""),
        "attom_loan_term": mortgage.get("term", ""),
        # Owner data
        "attom_owner1_name": owner1.get("fullname", ""),
        "attom_owner1_last": owner1.get("lastname", ""),
        "attom_owner1_first": owner1.get("firstnameandmi", ""),
        "attom_owner2_name": owner2.get("fullname", ""),
        "attom_corporate": owner.get("corporateindicator", ""),
        "attom_absentee": owner.get("absenteeownerstatus", ""),
        "attom_mail_address": owner.get("mailingaddressoneline", ""),
        # Property address
        "attom_property_address": address.get("oneLine", ""),
        "attom_property_type": summary.get("proptype", ""),
        "attom_year_built": summary.get("yearbuilt", ""),
    }


# ---------------------------------------------------------------------------
# Lender classification
# ---------------------------------------------------------------------------
HARD_MONEY_KEYWORDS = [
    "KIAVI", "LIMA ONE", "CIVIC", "ANCHOR LOANS", "GENESIS",
    "RCLENDING", "GROUNDFLOOR", "FUND THAT FLIP",
    "LENDING HOME", "VISIO", "NEW SILVER", "EASY STREET",
    "COREVEST", "RENOVO", "TEMPLE VIEW", "VELOCITY", "TOORAK",
    "HARD MONEY", "BRIDGE", "FIX AND FLIP", "REHAB",
]

def classify_lender(name: str) -> str:
    if not name:
        return ""
    upper = name.upper()
    for kw in HARD_MONEY_KEYWORDS:
        if kw in upper:
            return "hard_money"
    for kw in ["CREDIT UNION", "FCU", "FEDERAL CREDIT"]:
        if kw in upper:
            return "credit_union"
    for kw in ["PRIVATE", "INDIVIDUAL"]:
        if kw in upper:
            return "private"
    for kw in ["BANK", "NATIONAL ASSOCIATION", "N.A.", "MORTGAGE",
               "WELLS FARGO", "CHASE", "JPMORGAN", "CITIBANK",
               "REGIONS", "TRUIST", "PNC", "US BANK", "TD BANK",
               "LENDING", "FINANCIAL", "SAVINGS"]:
        if kw in upper:
            return "bank"
    return "other"


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="ATTOM mortgage/owner lookup (Step 16)")
    parser.add_argument("--input", type=str, default=str(DEFAULT_INPUT))
    parser.add_argument("--limit", type=int, default=0,
                        help="Limit lookups (0 = all, respecting 500/day)")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--max-parcels", type=int, default=1,
                        help="Max parcels to check per owner (default: 1)")
    args = parser.parse_args()

    # Get API key
    api_key = os.getenv("ATTOM_API_KEY", "")
    if not api_key:
        print("\n  ERROR: ATTOM_API_KEY not found in .env")
        print("  Add to .env: ATTOM_API_KEY=your_key_here")
        return

    FINANCING_DIR.mkdir(parents=True, exist_ok=True)
    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    # Load leads
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"\n  ERROR: Input not found: {args.input}")
        return

    print(f"\n  Loading leads: {input_path}")
    df = pd.read_csv(input_path, dtype=str, low_memory=False)
    print(f"  Total leads: {len(df)}")

    # Load parcel cache
    if not PARCEL_CACHE.exists():
        print(f"\n  ERROR: Parcel cache not found: {PARCEL_CACHE}")
        print("  Run script 12 first to build the owner-to-parcel mapping.")
        return

    with open(PARCEL_CACHE, "r") as f:
        parcel_cache = json.load(f)
    print(f"  Parcel cache: {len(parcel_cache)} owners, {sum(len(v) for v in parcel_cache.values())} parcels")

    # Load ATTOM cache
    cache = load_cache()
    print(f"  ATTOM cache: {len(cache)} previous lookups")

    # Build lookup list: one entry per owner, with their first parcel
    lookups = []
    for _, row in df.iterrows():
        own_name = str(row.get("OWN_NAME", "")).strip()
        co_no = str(row.get("CO_NO", "")).strip()
        if not own_name or own_name.lower() == "nan":
            continue

        # Find parcels for this owner
        cache_key = f"{co_no}:{own_name}" if co_no else own_name
        parcels = parcel_cache.get(cache_key, [])

        if not parcels:
            # Try without county prefix
            parcels = parcel_cache.get(own_name, [])

        if not parcels:
            continue

        # Get FIPS code
        fips = FIPS_CODES.get(co_no, "12099")  # default PBC

        # Take first N parcels
        selected_parcels = parcels[:args.max_parcels]

        for pcn in selected_parcels:
            pcn_str = str(pcn).strip().strip('"')
            if not pcn_str or len(pcn_str) < 10:
                continue

            # Format APN
            if co_no == "60":
                apn = format_apn_pbc(pcn_str)
            elif co_no == "16":
                apn = format_apn_broward(pcn_str)
            else:
                apn = format_apn_pbc(pcn_str)

            # Check cache
            cache_lookup_key = f"{fips}:{apn}"
            if cache_lookup_key in cache:
                continue

            lookups.append({
                "own_name": own_name,
                "co_no": co_no,
                "fips": fips,
                "apn": apn,
                "raw_pcn": pcn_str,
                "cache_key": cache_lookup_key,
            })

    # Deduplicate by APN
    seen_apns = set()
    unique_lookups = []
    for lk in lookups:
        if lk["apn"] not in seen_apns:
            seen_apns.add(lk["apn"])
            unique_lookups.append(lk)
    lookups = unique_lookups

    # Apply limit (respect 500/day)
    max_calls = min(len(lookups), 500)
    if args.limit > 0:
        max_calls = min(max_calls, args.limit)
    lookups = lookups[:max_calls]

    already_cached = len(parcel_cache) - len(lookups)

    print(f"\n  Lookups needed:   {len(lookups)}")
    print(f"  Already cached:   {len(cache)}")
    print(f"  Daily limit:      500")
    print(f"  Est. time:        {len(lookups) * REQUEST_DELAY / 60:.1f} min")

    if args.dry_run:
        print("\n  DRY RUN — would look up:")
        for lk in lookups[:10]:
            print(f"    {lk['own_name'][:40]} -> APN {lk['apn']}")
        if len(lookups) > 10:
            print(f"    ... and {len(lookups) - 10} more")
        return

    if len(lookups) == 0:
        print("\n  All lookups already cached. Building output...")
    else:
        # Run lookups
        print(f"\n  Starting ATTOM lookups...")
        found_lender = 0
        found_owner = 0
        no_data = 0
        errors = 0

        for i, lk in enumerate(lookups):
            prop = lookup_property(api_key, lk["apn"], lk["fips"])

            if prop.get("_rate_limited"):
                print(f"\n  RATE LIMITED after {i} calls. Saving cache and stopping.")
                save_cache(cache)
                break

            if prop:
                data = extract_mortgage_data(prop)
                data["OWN_NAME"] = lk["own_name"]
                data["raw_pcn"] = lk["raw_pcn"]
                data["apn"] = lk["apn"]
                data["fips"] = lk["fips"]

                cache[lk["cache_key"]] = data

                lender = data.get("attom_lender_name", "")
                owner1 = data.get("attom_owner1_name", "")

                if lender:
                    found_lender += 1
                    ltype = classify_lender(lender)
                    print(f"  [{i+1}/{len(lookups)}] {lk['own_name'][:30]:<30} -> {lender[:35]} ({ltype})")
                elif owner1:
                    found_owner += 1
                    if (i + 1) % 25 == 0:
                        print(f"  [{i+1}/{len(lookups)}] {lk['own_name'][:30]:<30} -> no mortgage (owner: {owner1})")
                else:
                    no_data += 1
            else:
                errors += 1

            # Save cache periodically
            if (i + 1) % 50 == 0:
                save_cache(cache)
                print(f"  ... saved cache ({i+1} done, {found_lender} lenders found)")

            time.sleep(REQUEST_DELAY)

        save_cache(cache)
        print(f"\n  Lookups complete: {found_lender} lenders, {found_owner} owners (no mortgage), {no_data} no data, {errors} errors")

    # Build output CSV from cache
    print("\n  Building output CSV...")
    rows = []
    for _, row in df.iterrows():
        own_name = str(row.get("OWN_NAME", "")).strip()
        co_no = str(row.get("CO_NO", "")).strip()
        fips = FIPS_CODES.get(co_no, "12099")

        cache_key_prefix = f"{co_no}:{own_name}" if co_no else own_name
        parcels = parcel_cache.get(cache_key_prefix, parcel_cache.get(own_name, []))

        # Find best cached result for this owner (prefer one with lender data)
        best = {}
        for pcn in parcels[:args.max_parcels]:
            pcn_str = str(pcn).strip().strip('"')
            if co_no == "60":
                apn = format_apn_pbc(pcn_str)
            else:
                apn = pcn_str
            lookup_key = f"{fips}:{apn}"
            cached = cache.get(lookup_key, {})
            if cached:
                if cached.get("attom_lender_name") or not best:
                    best = cached

        result = {"OWN_NAME": own_name}
        if best:
            for k, v in best.items():
                if k not in ("OWN_NAME", "raw_pcn", "apn", "fips"):
                    result[k] = v
            # Add lender classification
            lender = best.get("attom_lender_name", "")
            result["attom_lender_type"] = classify_lender(lender) if lender else ""
        rows.append(result)

    out_df = pd.DataFrame(rows)
    out_df.to_csv(OUTPUT_FILE, index=False)

    # Summary
    with_lender = out_df["attom_lender_name"].apply(
        lambda x: bool(str(x).strip()) and str(x).strip().lower() not in ("", "nan", "none")
    ).sum() if "attom_lender_name" in out_df.columns else 0

    with_owner = out_df["attom_owner1_name"].apply(
        lambda x: bool(str(x).strip()) and str(x).strip().lower() not in ("", "nan", "none")
    ).sum() if "attom_owner1_name" in out_df.columns else 0

    print()
    print("=" * 60)
    print("  ATTOM MORTGAGE & OWNER RESULTS")
    print("=" * 60)
    print(f"  Total leads:          {len(df)}")
    print(f"  With lender name:     {with_lender}/{len(df)} ({with_lender*100//len(df)}%)")
    print(f"  With resolved owner:  {with_owner}/{len(df)} ({with_owner*100//len(df)}%)")

    if with_lender > 0:
        # Lender breakdown
        lender_types = out_df["attom_lender_type"].value_counts()
        print(f"\n  Lender type breakdown:")
        for lt, count in lender_types.items():
            if lt and str(lt).lower() not in ("nan", "none", ""):
                print(f"    {lt}: {count}")

        # Top lenders
        top_lenders = out_df["attom_lender_name"].value_counts().head(10)
        print(f"\n  Top lenders:")
        for lender, count in top_lenders.items():
            if lender and str(lender).lower() not in ("nan", "none", ""):
                print(f"    {lender}: {count}")

    print(f"\n  Output: {OUTPUT_FILE}")
    print(f"  Cache: {CACHE_DIR / 'attom_mortgage_cache.json'}")
    print()


if __name__ == "__main__":
    main()
