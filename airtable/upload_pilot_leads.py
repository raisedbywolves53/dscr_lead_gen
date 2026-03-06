"""
Upload Pilot Leads to Airtable Investors Table
===============================================

Reads the enriched pilot CSV and uploads the top N leads (by score)
to the Airtable Investors table. Maps CSV columns to Airtable field
names and handles type conversions.

Usage:
    python airtable/upload_pilot_leads.py                    # Top 25
    python airtable/upload_pilot_leads.py --count 100        # Top 100
    python airtable/upload_pilot_leads.py --count 500        # All 500
    python airtable/upload_pilot_leads.py --dry-run          # Preview
    python airtable/upload_pilot_leads.py --input path.csv   # Custom input
"""

import argparse
import os
import re
import sys
import time

import pandas as pd
import requests
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

load_dotenv()

API_TOKEN = os.getenv("AIRTABLE_API_TOKEN")
BASE_ID = "appJV7J1ZrNEBAWAm"
INVESTORS_TABLE = "tbla2NnrEDSFA3UFP"
HEADERS = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Content-Type": "application/json",
}

DEFAULT_INPUT = os.path.join("scrape", "data", "enriched", "pilot_500_enriched.csv")
FALLBACK_INPUT = os.path.join("scrape", "data", "enriched", "pilot_500.csv")


# ---------------------------------------------------------------------------
# Column mapping: CSV column → Airtable Investors field name
# ---------------------------------------------------------------------------

def normalize_phone(phone) -> str:
    """Normalize phone to 10 digits."""
    phone = re.sub(r"\D", "", str(phone))
    if len(phone) == 11 and phone.startswith("1"):
        phone = phone[1:]
    return phone if len(phone) == 10 else ""


def parse_name(own_name: str, resolved_person: str) -> tuple:
    """Parse OWN_NAME or resolved_person into (first, last, full)."""
    # Prefer resolved_person if available
    name = resolved_person.strip() if resolved_person and resolved_person.lower() not in ("nan", "none", "") else own_name.strip()

    if not name or name.lower() in ("nan", "none", ""):
        return "", "", ""

    # Remove trailing "&" (joint ownership)
    name = name.rstrip("& ").strip()

    if "," in name:
        # "LAST, FIRST MIDDLE" format
        parts = name.split(",", 1)
        last = parts[0].strip().title()
        first_parts = parts[1].strip().split() if len(parts) > 1 else []
        first = first_parts[0].title() if first_parts else ""
    else:
        # "LAST FIRST MIDDLE" or "FIRST LAST" — FDOR uses LAST FIRST
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


def determine_market(co_no: str, own_city: str) -> str:
    """Determine Primary Market from county code or city."""
    co = str(co_no).strip()
    if co == "60":
        return "Palm Beach County"
    if co in ("6", "06"):
        return "Broward County"

    city = own_city.strip().upper() if own_city else ""
    pb_cities = {"WEST PALM BEACH", "PALM BEACH", "BOCA RATON", "DELRAY BEACH",
                 "BOYNTON BEACH", "LAKE WORTH", "JUPITER", "PALM BEACH GARDENS",
                 "WELLINGTON", "RIVIERA BEACH"}
    broward_cities = {"FORT LAUDERDALE", "FT LAUDERDALE", "HOLLYWOOD",
                      "POMPANO BEACH", "CORAL SPRINGS", "PLANTATION",
                      "DAVIE", "SUNRISE", "DEERFIELD BEACH", "PEMBROKE PINES",
                      "MIRAMAR", "WESTON", "COCONUT CREEK"}
    if city in pb_cities:
        return "Palm Beach County"
    if city in broward_cities:
        return "Broward County"
    return "Other FL"


def determine_investor_type(props: int, is_entity: bool) -> str:
    """Map property count + entity flag to Investor Type."""
    if props >= 10:
        return "Professional Investor"
    if props >= 5:
        return "Growth Investor"
    if is_entity and props >= 2:
        return "Growth Investor"
    if props >= 2:
        return "Lifestyle Investor"
    return "Accidental Landlord"


def determine_relationship(score: float) -> str:
    """Map lead score to initial Relationship Strength."""
    if score >= 50:
        return "Warming"
    return "New Lead"


def safe_float(val) -> float:
    """Convert to float, returning 0 on failure."""
    try:
        return float(val)
    except (ValueError, TypeError):
        return 0.0


def safe_int(val) -> int:
    """Convert to int, returning 0 on failure."""
    try:
        return int(float(val))
    except (ValueError, TypeError):
        return 0


def build_airtable_record(row: pd.Series) -> dict:
    """Convert a CSV row to Airtable Investors field values."""
    own_name = str(row.get("OWN_NAME", ""))
    resolved = str(row.get("resolved_person", ""))
    is_entity = str(row.get("is_entity", "")).lower() in ("true", "1", "yes")
    props = safe_int(row.get("_props", row.get("property_count", 0)))
    score = safe_float(row.get("_score", 0))

    fields = {}

    # Core identity — handle entities vs individuals differently
    has_resolved = resolved and resolved.lower() not in ("nan", "none", "")
    if has_resolved:
        # Use resolved person name (from SunBiz)
        first, last, full = parse_name("", resolved)
        if full:
            fields["Full Name"] = full
        if first:
            fields["First Name"] = first
        if last:
            fields["Last Name"] = last
    elif is_entity:
        # Entity without resolved person — use entity name as Full Name
        entity_name = own_name.strip().title()
        fields["Full Name"] = entity_name
        # Don't set First/Last for unresolved entities
    else:
        # Individual owner
        first, last, full = parse_name(own_name, "")
        if full:
            fields["Full Name"] = full
        if first:
            fields["First Name"] = first
        if last:
            fields["Last Name"] = last

    # Contact info
    phone1 = normalize_phone(row.get("phone_1", "") or row.get("phone", "") or row.get("str_phone", ""))
    phone2 = normalize_phone(row.get("phone_2", ""))
    email1 = str(row.get("email_1", "") or row.get("email", "") or row.get("str_email", "")).strip()
    email2 = str(row.get("email_2", "")).strip()
    linkedin = str(row.get("apollo_linkedin", "")).strip()

    if phone1:
        fields["Phone (Mobile)"] = phone1
    if phone2:
        fields["Phone (Secondary)"] = phone2
    if email1 and "@" in email1 and email1.lower() not in ("nan", "none"):
        fields["Email (Primary)"] = email1
    if email2 and "@" in email2 and email2.lower() not in ("nan", "none"):
        fields["Email (Secondary)"] = email2
    if linkedin and linkedin.lower() not in ("nan", "none", ""):
        fields["LinkedIn URL"] = linkedin

    # Mailing address
    addr = str(row.get("OWN_ADDR1", "")).strip()
    city = str(row.get("OWN_CITY", "")).strip()
    state = str(row.get("OWN_STATE", "")).strip()
    zipcode = str(row.get("OWN_ZIPCD", "")).strip()[:5]

    if addr and addr.lower() not in ("nan", "none"):
        fields["Mailing Address"] = addr.title()
    if city and city.lower() not in ("nan", "none"):
        fields["Mailing City"] = city.title()
    if state and state.lower() not in ("nan", "none"):
        fields["Mailing State"] = state.upper()
    if zipcode and zipcode.lower() not in ("nan", "none"):
        fields["Mailing ZIP"] = zipcode

    # Classification
    market = determine_market(str(row.get("CO_NO", "")), city)
    fields["Primary Market"] = market
    fields["Investor Type"] = determine_investor_type(props, is_entity)
    fields["Lead Source"] = "FL DOR Records"
    fields["Relationship Strength"] = determine_relationship(score)
    fields["DNC Status"] = "Not Checked"
    fields["Consent Status"] = "No Consent"

    # Phone type
    phone_type = str(row.get("phone_1_type", "")).strip().lower()
    if phone_type in ("mobile", "cell"):
        fields["Phone Type"] = "Mobile"
    elif phone_type == "landline":
        fields["Phone Type"] = "Landline"
    elif phone_type == "voip":
        fields["Phone Type"] = "VoIP"
    elif phone1:
        fields["Phone Type"] = "Unknown"

    return fields


# ---------------------------------------------------------------------------
# API helpers
# ---------------------------------------------------------------------------

def api_call(method, url, **kwargs):
    """Airtable API call with retry on rate limits."""
    for attempt in range(5):
        resp = requests.request(method, url, headers=HEADERS, **kwargs)
        if resp.status_code == 429:
            wait = int(resp.headers.get("Retry-After", 30))
            print(f"  Rate limited, waiting {wait}s...")
            time.sleep(wait)
            continue
        if resp.status_code >= 400:
            print(f"  API error {resp.status_code}: {resp.text[:300]}")
            return None
        time.sleep(0.22)
        return resp.json()
    print("  Max retries exceeded")
    return None


def create_records(records: list) -> int:
    """Create records in batches of 10. Returns count of successfully created."""
    url = f"https://api.airtable.com/v0/{BASE_ID}/{INVESTORS_TABLE}"
    success = 0

    for i in range(0, len(records), 10):
        batch = records[i : i + 10]
        payload = {"records": [{"fields": r} for r in batch]}
        result = api_call("POST", url, json=payload)
        if result and "records" in result:
            success += len(result["records"])
            print(f"  Batch {i // 10 + 1}: created {len(result['records'])} records")
        else:
            print(f"  Batch {i // 10 + 1}: FAILED ({len(batch)} records)")

    return success


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Upload pilot leads to Airtable Investors table"
    )
    parser.add_argument(
        "--count", type=int, default=25,
        help="Number of top-scored leads to upload (default: 25, max: 500)",
    )
    parser.add_argument(
        "--input", type=str, default=None,
        help="Input CSV path (default: pilot_500_enriched.csv or pilot_500.csv)",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Preview records without uploading",
    )
    args = parser.parse_args()

    if not args.dry_run and not API_TOKEN:
        print("ERROR: AIRTABLE_API_TOKEN not set. Add it to .env")
        sys.exit(1)

    # Find input file
    if args.input:
        input_path = args.input
    elif os.path.exists(DEFAULT_INPUT):
        input_path = DEFAULT_INPUT
    elif os.path.exists(FALLBACK_INPUT):
        input_path = FALLBACK_INPUT
    else:
        print(f"No input CSV found. Expected one of:")
        print(f"  {DEFAULT_INPUT}")
        print(f"  {FALLBACK_INPUT}")
        sys.exit(1)

    df = pd.read_csv(input_path, dtype=str, low_memory=False)
    print(f"\nLoaded {len(df)} leads from {input_path}")

    # Sort by _score descending
    df["_sort_score"] = df.get("_score", pd.Series([0] * len(df))).apply(safe_float)
    df = df.sort_values("_sort_score", ascending=False).head(args.count)
    df = df.drop(columns=["_sort_score"])
    print(f"Selected top {len(df)} by score")

    # Build Airtable records
    records = []
    for _, row in df.iterrows():
        fields = build_airtable_record(row)
        if fields.get("Full Name"):
            records.append(fields)

    print(f"Built {len(records)} valid records")

    if not records:
        print("No valid records to upload.")
        return

    # Dry run preview
    if args.dry_run:
        print(f"\n{'=' * 60}")
        print(f"DRY RUN — First 5 records:")
        print(f"{'=' * 60}")
        for i, rec in enumerate(records[:5]):
            print(f"\n--- Record {i + 1} ---")
            for k, v in rec.items():
                print(f"  {k}: {v}")
        print(f"\n  Would upload {len(records)} records total.")
        return

    # Upload
    print(f"\nUploading {len(records)} records to Airtable Investors...")
    success = create_records(records)

    print(f"\n{'=' * 60}")
    print(f"UPLOAD SUMMARY")
    print(f"{'=' * 60}")
    print(f"  Attempted:  {len(records)}")
    print(f"  Succeeded:  {success}")
    print(f"  Failed:     {len(records) - success}")
    print()

    if success > 0:
        print("  NEXT STEPS:")
        print("  1. Check Airtable — records should appear in Investors table")
        print("  2. Run: python airtable/refresh_call_queue.py")
        print("  3. Open the Call Queue view in Airtable to see enriched leads")
        print()


if __name__ == "__main__":
    main()
