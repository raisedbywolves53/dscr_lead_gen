"""
ATTOM Per-Property Mortgage Enrichment — Showcase Leads
========================================================

Calls ATTOM /property/detailmortgage for each of the 62 showcase properties
to replace estimated/divided lender data with real per-property mortgage info:
  - Lender name, city, state, type
  - Loan amount, date, type, interest rate, rate type
  - Due date, loan term
  - Title company

Prerequisites:
  - ATTOM_API_KEY set in .env
  - Zack must confirm ATTOM billing model (month-to-month vs annual)
  - Estimated cost: ~$1.05 at 5K tier ($0.017 x 62 calls)

Usage:
    python scripts/attom_showcase_mortgage.py
    python scripts/attom_showcase_mortgage.py --dry-run   # Preview API calls without making them

After running, re-run build_sales_demo.py to regenerate the demo Excel.
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path

import pandas as pd
import requests
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent
DATA_DIR = PROJECT_DIR / "data"
DEMO_DIR = DATA_DIR / "demo"
PROPS_CSV = DEMO_DIR / "showcase_properties.csv"
ENRICHED_CSV = DEMO_DIR / "showcase_enriched.csv"
CACHE_FILE = DEMO_DIR / "attom_mortgage_cache.json"

# Load .env
load_dotenv(PROJECT_DIR / ".env")
ATTOM_API_KEY = os.getenv("ATTOM_API_KEY", "")

# ---------------------------------------------------------------------------
# ATTOM API config
# ---------------------------------------------------------------------------
ATTOM_BASE = "https://api.gateway.attomdata.com/propertyapi/v1.0.0"
REQUEST_DELAY = 0.5  # seconds between requests (well within rate limits)


def attom_mortgage_lookup(address: str, zipcode: str, session: requests.Session) -> dict:
    """
    Call ATTOM /property/detailmortgage for a single property.
    Returns a dict with mortgage details or empty dict on failure.
    """
    url = f"{ATTOM_BASE}/property/detailmortgage"
    params = {
        "address1": address,
        "address2": zipcode,
    }
    headers = {
        "apikey": ATTOM_API_KEY,
        "Accept": "application/json",
    }

    try:
        resp = session.get(url, params=params, headers=headers, timeout=30)
    except requests.RequestException as e:
        return {"error": str(e)}

    if resp.status_code == 200:
        data = resp.json()
        # Extract mortgage info from response
        props = data.get("property", [])
        if not props:
            return {"error": "no property data"}

        prop = props[0]
        mortgage = prop.get("sale", {}).get("mortgage", {})
        # Also check assessment and building
        identifier = prop.get("identifier", {})
        owner = prop.get("assessment", {}).get("owner", {})

        # First mortgage (most recent)
        first = mortgage.get("FirstConcurrent", {})
        second = mortgage.get("SecondConcurrent", {})

        result = {
            "attom_lender_name": first.get("Lender", {}).get("lastNameOrCorporation", ""),
            "attom_lender_type": first.get("Lender", {}).get("Type", ""),
            "attom_loan_amount": first.get("Amount", ""),
            "attom_loan_date": first.get("Date", ""),
            "attom_loan_type": first.get("LoanType", ""),
            "attom_interest_rate": first.get("InterestRate", ""),
            "attom_rate_type": first.get("InterestRateType", ""),
            "attom_due_date": first.get("DueDate", ""),
            "attom_loan_term": first.get("Term", ""),
            "attom_title_company": mortgage.get("TitleCompany", {}).get("lastNameOrCorporation", ""),
            "attom_deed_type": mortgage.get("DeedType", ""),
            # Second mortgage if exists
            "attom_2nd_lender": second.get("Lender", {}).get("lastNameOrCorporation", ""),
            "attom_2nd_amount": second.get("Amount", ""),
        }

        # Clean empty strings
        return {k: v for k, v in result.items() if v}

    elif resp.status_code == 404:
        return {"error": "not found"}
    else:
        return {"error": f"HTTP {resp.status_code}: {resp.text[:200]}"}


def load_cache() -> dict:
    """Load cached ATTOM results."""
    if CACHE_FILE.exists():
        with open(CACHE_FILE) as f:
            return json.load(f)
    return {}


def save_cache(cache: dict):
    """Save ATTOM results cache."""
    with open(CACHE_FILE, "w") as f:
        json.dump(cache, f, indent=2)


def main():
    parser = argparse.ArgumentParser(description="ATTOM mortgage enrichment for showcase properties")
    parser.add_argument("--dry-run", action="store_true", help="Preview calls without making them")
    args = parser.parse_args()

    if not ATTOM_API_KEY and not args.dry_run:
        print("ERROR: ATTOM_API_KEY not set in .env")
        print("Set it and re-run, or use --dry-run to preview.")
        sys.exit(1)

    if not PROPS_CSV.exists():
        print(f"ERROR: {PROPS_CSV} not found")
        print("Run enrich_showcase_leads.py first.")
        sys.exit(1)

    props = pd.read_csv(PROPS_CSV, dtype=str)
    print(f"Loaded {len(props)} properties from {PROPS_CSV.name}")

    cache = load_cache()
    print(f"Cache has {len(cache)} existing lookups")

    session = requests.Session()
    new_lookups = 0
    matched = 0
    errors = 0

    for i, (_, row) in enumerate(props.iterrows()):
        address = str(row.get("address", "")).strip()
        if not address or address == "nan":
            continue

        # Extract just the street address (before first comma)
        street = address.split(",")[0].strip()
        # Extract zip from address or use county default
        parts = address.split(",")
        zipcode = ""
        for part in parts:
            part = part.strip()
            if len(part) == 5 and part.isdigit():
                zipcode = part
                break
            # Check for "FL 33xxx" pattern
            if "FL" in part:
                zip_candidate = part.replace("FL", "").strip()
                if len(zip_candidate) >= 5 and zip_candidate[:5].isdigit():
                    zipcode = zip_candidate[:5]
                    break

        cache_key = f"{street}|{zipcode}"

        if args.dry_run:
            status = "CACHED" if cache_key in cache else "WOULD CALL"
            print(f"  [{i+1}/{len(props)}] {status}: {street}, {zipcode}")
            continue

        if cache_key in cache:
            print(f"  [{i+1}/{len(props)}] CACHED: {street}")
            continue

        print(f"  [{i+1}/{len(props)}] Calling ATTOM: {street}, {zipcode}")
        result = attom_mortgage_lookup(street, zipcode, session)
        cache[cache_key] = result
        new_lookups += 1

        if "error" in result:
            print(f"    ERROR: {result['error']}")
            errors += 1
        else:
            lender = result.get("attom_lender_name", "N/A")
            amount = result.get("attom_loan_amount", "N/A")
            print(f"    Lender: {lender}, Amount: {amount}")
            matched += 1

        # Save cache periodically
        if new_lookups % 10 == 0:
            save_cache(cache)

        time.sleep(REQUEST_DELAY)

    if not args.dry_run:
        save_cache(cache)
        print(f"\nResults: {new_lookups} API calls, {matched} matched, {errors} errors")

        # Update properties CSV with ATTOM data
        attom_cols = [
            "attom_lender_name", "attom_lender_type", "attom_loan_amount",
            "attom_loan_date", "attom_loan_type", "attom_interest_rate",
            "attom_rate_type", "attom_due_date", "attom_loan_term",
            "attom_title_company", "attom_deed_type",
        ]

        for col in attom_cols:
            if col not in props.columns:
                props[col] = ""

        updated = 0
        for idx, row in props.iterrows():
            address = str(row.get("address", "")).strip()
            street = address.split(",")[0].strip()
            parts = address.split(",")
            zipcode = ""
            for part in parts:
                part = part.strip()
                if len(part) == 5 and part.isdigit():
                    zipcode = part
                    break
                if "FL" in part:
                    zip_candidate = part.replace("FL", "").strip()
                    if len(zip_candidate) >= 5 and zip_candidate[:5].isdigit():
                        zipcode = zip_candidate[:5]
                        break

            cache_key = f"{street}|{zipcode}"
            if cache_key in cache and "error" not in cache[cache_key]:
                for col in attom_cols:
                    props.at[idx, col] = cache[cache_key].get(col, "")
                updated += 1

        props.to_csv(PROPS_CSV, index=False)
        print(f"Updated {updated}/{len(props)} properties with ATTOM data in {PROPS_CSV.name}")
        print(f"\nNext step: Re-run build_sales_demo.py to regenerate the demo Excel")
    else:
        uncached = sum(1 for _, row in props.iterrows()
                      if f"{str(row.get('address', '')).split(',')[0].strip()}|" not in
                      "|".join(cache.keys()))
        print(f"\nDry run complete. Would make ~{uncached} new API calls.")
        print(f"Estimated cost: ${uncached * 0.017:.2f}")


if __name__ == "__main__":
    main()
