"""
Step 10b: Wiza Contact Enrichment
==================================

Enriches pilot leads via Wiza's bulk list API to find emails, phones,
LinkedIn profiles, and company info.

Wiza works best when you provide a person name + company/domain. For our
leads this means:
  - Entity owners with resolved person → full_name + entity as company
  - Leads with existing email → email-based lookup (fills phone gaps)
  - Individuals → full_name only (lower match rate)

API docs: https://docs.wiza.co/api-reference/

Usage:
    python scrape/scripts/10b_wiza_enrich.py --input scrape/data/enriched/pilot_500.csv
    python scrape/scripts/10b_wiza_enrich.py --dry-run
"""

import argparse
import json
import os
import time
from pathlib import Path

import pandas as pd
import requests
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent
ENRICHED_DIR = PROJECT_DIR / "data" / "enriched"
CACHE_DIR = ENRICHED_DIR / "wiza_cache"

DEFAULT_INPUT = ENRICHED_DIR / "pilot_500.csv"
OUTPUT_CSV = ENRICHED_DIR / "wiza_results.csv"

WIZA_API_KEY = os.getenv("WIZA_API_KEY", "")
WIZA_BASE = "https://wiza.co"
WIZA_HEADERS = {
    "Authorization": f"Bearer {WIZA_API_KEY}",
    "Content-Type": "application/json",
}

# Max contacts per bulk list request
MAX_LIST_SIZE = 2500
# Poll interval when waiting for list enrichment to complete
POLL_INTERVAL = 10  # seconds
POLL_TIMEOUT = 1800  # 30 minutes max wait


# ---------------------------------------------------------------------------
# API helpers
# ---------------------------------------------------------------------------

def wiza_request(method, path, **kwargs):
    """Make a Wiza API request with retry on rate limits."""
    url = f"{WIZA_BASE}{path}"
    for attempt in range(5):
        resp = requests.request(method, url, headers=WIZA_HEADERS, **kwargs)
        if resp.status_code == 429:
            wait = 15
            print(f"  Rate limited, waiting {wait}s...")
            time.sleep(wait)
            continue
        if resp.status_code == 401:
            print("  ERROR: Unauthorized — check WIZA_API_KEY in .env")
            return None
        if resp.status_code >= 400:
            print(f"  API error {resp.status_code}: {resp.text[:300]}")
            return None
        return resp.json()
    print("  Max retries exceeded")
    return None


ENTITY_KEYWORDS = {
    "LLC", "INC", "CORP", "LP", "LTD", "TRUST", "HOLDINGS", "PROPERTIES",
    "INVESTMENTS", "REALTY", "CAPITAL", "GROUP", "PARTNERS", "ASSOCIATES",
    "VENTURES", "MANAGEMENT", "ENTERPRISES", "SOLUTIONS", "DEVELOPMENT",
    "REAL ESTATE", "HOMES", "RENTALS", "ADVISORS", "ASSOCIATION", "AUTHORITY",
    "UNIVERSITY", "COMMUNITY", "HOUSING", "COUNTY", "CHURCH", "VILLAGE",
    "CONDO", "HOA", "CLUB", "OWNERS", "PROPERTY OWNERS", "CRA", "LAND TR",
    "INVESTMENT", "BEACH", "FUND", "FOUNDATION", "SOCIETY",
}


def looks_like_entity(name: str) -> bool:
    """Check if a name looks like a business entity, not a person."""
    upper = name.upper()
    return any(kw in upper for kw in ENTITY_KEYWORDS)


def parse_person_name(name: str) -> str:
    """Parse FDOR 'LAST FIRST' or 'LAST, FIRST' into 'First Last'."""
    name = name.rstrip("& ").strip()
    if not name:
        return ""
    if "," in name:
        parts = name.split(",", 1)
        last = parts[0].strip().title()
        first = parts[1].strip().split()[0].title() if parts[1].strip() else ""
        return f"{first} {last}".strip()
    parts = name.split()
    if len(parts) >= 2:
        return f"{parts[1].title()} {parts[0].title()}"
    return parts[0].title() if parts else ""


def build_wiza_item(row):
    """Build a Wiza list item from a CSV row. Returns (item_dict, input_type) or (None, None)."""
    resolved = str(row.get("resolved_person", "")).strip()
    own_name = str(row.get("OWN_NAME", "")).strip()
    is_entity = str(row.get("is_entity", "")).lower() in ("true", "1", "yes")
    email = str(row.get("email_1", "") or row.get("email", "")).strip()
    linkedin = str(row.get("apollo_linkedin", "")).strip()

    # Clean up NaN/None values
    if resolved.lower() in ("nan", "none", ""):
        resolved = ""
    if email.lower() in ("nan", "none", "") or "@" not in email:
        email = ""
    if linkedin.lower() in ("nan", "none", ""):
        linkedin = ""

    # Priority 1: LinkedIn URL (best match rate)
    if linkedin and "linkedin.com" in linkedin:
        return {"profile_url": linkedin}, "linkedin"

    # Priority 2: Email lookup (fills phone gaps)
    if email:
        return {"email": email}, "email"

    # Priority 3: Entity with resolved person → name + company
    if is_entity and resolved:
        entity_name = own_name
        for suffix in (" LLC", " INC", " CORP", " LP", " LTD", " L.L.C."):
            if entity_name.upper().endswith(suffix):
                entity_name = entity_name[:len(entity_name) - len(suffix)].strip()
        person_name = parse_person_name(resolved)
        if person_name:
            return {
                "full_name": person_name,
                "company": entity_name.title(),
            }, "name+company"

    # Priority 4: Individual name (skip anything that looks like an entity)
    if not is_entity and own_name and not looks_like_entity(own_name):
        person_name = parse_person_name(own_name)
        if person_name and len(person_name.split()) >= 2:
            return {"full_name": person_name}, "name_only"

    return None, None


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Wiza contact enrichment")
    parser.add_argument("--input", type=str, default=str(DEFAULT_INPUT),
                        help="Input CSV path")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show what would be submitted without calling API")
    parser.add_argument("--enrichment-level", type=str, default="full",
                        choices=["none", "partial", "phone", "full"],
                        help="Enrichment level (default: full)")
    args = parser.parse_args()

    if not args.dry_run and not WIZA_API_KEY:
        print("ERROR: WIZA_API_KEY not set. Add it to .env")
        print("Get your API key from Wiza: Settings → API → Generate")
        return

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Input file not found: {input_path}")
        return

    df = pd.read_csv(input_path, dtype=str, low_memory=False)
    print(f"Loaded {len(df)} leads from {input_path.name}")

    # Build Wiza items
    items = []
    item_rows = []  # Track which row each item came from
    type_counts = {"linkedin": 0, "email": 0, "name+company": 0, "name_only": 0}
    skipped = 0

    for idx, row in df.iterrows():
        item, input_type = build_wiza_item(row)
        if item:
            items.append(item)
            item_rows.append(idx)
            type_counts[input_type] += 1
        else:
            skipped += 1

    print(f"\nWiza lookup candidates: {len(items)}")
    print(f"  LinkedIn URL:   {type_counts['linkedin']}")
    print(f"  Email lookup:   {type_counts['email']}")
    print(f"  Name+Company:   {type_counts['name+company']}")
    print(f"  Name only:      {type_counts['name_only']}")
    print(f"  Skipped:        {skipped}")

    if not items:
        print("No candidates for Wiza enrichment.")
        return

    if args.dry_run:
        print(f"\nDRY RUN — would submit {len(items)} contacts to Wiza")
        print("\nSample items (first 10):")
        for i, item in enumerate(items[:10]):
            print(f"  {i+1}. {item}")
        return

    # Submit bulk list
    print(f"\nSubmitting {len(items)} contacts to Wiza bulk list...")
    payload = {
        "list": {
            "name": f"DSCR Pilot 500 - {time.strftime('%Y%m%d_%H%M')}",
            "enrichment_level": args.enrichment_level,
            "email_options": {
                "accept_work": True,
                "accept_personal": True,
            },
            "items": items[:MAX_LIST_SIZE],
        }
    }

    result = wiza_request("POST", "/api/lists", json=payload)
    if not result or "data" not in result:
        print("Failed to create Wiza list.")
        return

    list_id = result["data"]["id"]
    list_status = result["data"].get("status", "queued")
    credits = result["data"].get("stats", {}).get("credits", {})
    api_credits = credits.get("api_credits", {}).get("total", "?")

    print(f"  List created: ID={list_id}, status={list_status}")
    print(f"  API credits to be used: {api_credits}")

    # Save list ID for resume
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_file = CACHE_DIR / "last_list.json"
    with open(cache_file, "w") as f:
        json.dump({"list_id": list_id, "item_count": len(items)}, f)

    # Poll for completion
    print(f"\nWaiting for enrichment to complete (polling every {POLL_INTERVAL}s)...")
    start_time = time.time()
    while True:
        elapsed = time.time() - start_time
        if elapsed > POLL_TIMEOUT:
            print(f"  Timeout after {POLL_TIMEOUT}s. Check status manually:")
            print(f"  List ID: {list_id}")
            break

        time.sleep(POLL_INTERVAL)
        status_resp = wiza_request("GET", f"/api/lists/{list_id}")
        if not status_resp or "data" not in status_resp:
            print("  Error checking status, retrying...")
            continue

        status = status_resp["data"].get("status", "unknown")
        stats = status_resp["data"].get("stats", {})
        people = stats.get("people", "?")

        minutes = int(elapsed // 60)
        seconds = int(elapsed % 60)
        print(f"  [{minutes:02d}:{seconds:02d}] Status: {status}, People found: {people}")

        if status in ("finished", "complete", "done"):
            print("  Enrichment complete!")
            break
        if status == "failed":
            print("  Enrichment failed.")
            return

    # Fetch results
    print("\nFetching enriched contacts...")
    contacts_resp = wiza_request("GET", f"/api/lists/{list_id}/contacts",
                                  params={"segment": "people"})
    if not contacts_resp or "data" not in contacts_resp:
        print("Failed to fetch contacts.")
        return

    contacts = contacts_resp["data"]
    print(f"  Retrieved {len(contacts)} enriched contacts")

    if not contacts:
        print("  No contacts returned. Wiza may not have found matches.")
        return

    # Build results dataframe
    results = []
    for contact in contacts:
        results.append({
            "wiza_full_name": contact.get("full_name", ""),
            "wiza_email": contact.get("email", ""),
            "wiza_email_type": contact.get("email_type", ""),
            "wiza_email_status": contact.get("email_status", ""),
            "wiza_phone": contact.get("mobile_phone", "") or contact.get("phone_number", ""),
            "wiza_title": contact.get("title", ""),
            "wiza_company": contact.get("company", ""),
            "wiza_location": contact.get("location", ""),
            "wiza_linkedin": contact.get("linkedin", ""),
            "wiza_company_industry": contact.get("company_industry", ""),
            "wiza_company_size": contact.get("company_size", ""),
        })

    results_df = pd.DataFrame(results)

    # Also build the merge-compatible format (First Name, Last Name, Email, Phone)
    # for 05b_merge_enrichment.py compatibility
    merge_rows = []
    for contact in contacts:
        full = contact.get("full_name", "").strip()
        email = contact.get("email", "").strip()
        phone = contact.get("mobile_phone", "") or contact.get("phone_number", "")

        # Parse name into first/last
        parts = full.split() if full else []
        first = parts[0] if parts else ""
        last = " ".join(parts[1:]) if len(parts) > 1 else ""

        merge_rows.append({
            "First Name": first,
            "Last Name": last,
            "Email": email,
            "Phone": str(phone).strip() if phone else "",
            "LinkedIn URL": contact.get("linkedin", ""),
            "Company": contact.get("company", ""),
            "Title": contact.get("title", ""),
        })

    merge_df = pd.DataFrame(merge_rows)

    # Save both formats
    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    merge_df.to_csv(OUTPUT_CSV, index=False)
    results_df.to_csv(ENRICHED_DIR / "wiza_results_full.csv", index=False)

    # Summary
    has_email = results_df["wiza_email"].fillna("").str.contains("@", na=False).sum()
    has_phone = results_df["wiza_phone"].fillna("").astype(str).str.len().ge(10).sum()
    has_linkedin = results_df["wiza_linkedin"].fillna("").str.contains("linkedin", na=False).sum()

    print()
    print("=" * 60)
    print("  WIZA ENRICHMENT SUMMARY")
    print("=" * 60)
    print(f"  Submitted:       {len(items)}")
    print(f"  Contacts found:  {len(contacts)}")
    print(f"  Match rate:      {len(contacts) / len(items) * 100:.0f}%")
    print(f"  Has email:       {has_email}")
    print(f"  Has phone:       {has_phone}")
    print(f"  Has LinkedIn:    {has_linkedin}")
    print(f"\n  Saved: {OUTPUT_CSV}")
    print(f"  Full results: {ENRICHED_DIR / 'wiza_results_full.csv'}")
    print()
    print("  NEXT STEPS:")
    print("  python scrape/scripts/05b_merge_enrichment.py")
    print()


if __name__ == "__main__":
    main()
