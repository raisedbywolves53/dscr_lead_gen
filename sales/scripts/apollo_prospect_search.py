"""
Apollo Prospect Search & Enrichment
=====================================

Two modes:
  1. SEARCH — Find new LO prospects by title + location via Apollo People Search API
  2. ENRICH — Fill in missing data on existing prospect CSV via Apollo People Match API

Uses Apollo API credits efficiently:
  - Search: 1 credit per result returned
  - Match: 1 credit per lookup
  - All results cached to avoid duplicate spend

Usage:
    # Search for new prospects in a market
    python sales/scripts/apollo_prospect_search.py search \
        --titles "Loan Officer,Branch Manager,Mortgage Loan Originator" \
        --locations "Raleigh, NC" \
        --max-results 200

    # Search multiple markets
    python sales/scripts/apollo_prospect_search.py search \
        --titles "Branch Manager,Loan Officer" \
        --locations "Raleigh, NC|Charlotte, NC|Austin, TX" \
        --max-results 100

    # Enrich existing prospect list (fill missing emails/phones/LinkedIn)
    python sales/scripts/apollo_prospect_search.py enrich

    # Dry run (show what would be done, no API calls)
    python sales/scripts/apollo_prospect_search.py search --dry-run \
        --titles "Branch Manager" --locations "Raleigh, NC"

    # Check remaining credits
    python sales/scripts/apollo_prospect_search.py credits

Output:
    sales/prospects/apollo_search_results.csv  (new prospects found)
    sales/prospects/nc_loan_officers.csv       (enriched in place)
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
# Config
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent.parent
PROSPECTS_DIR = PROJECT_DIR / "sales" / "prospects"
PROSPECTS_CSV = PROSPECTS_DIR / "nc_loan_officers.csv"
SEARCH_OUTPUT = PROSPECTS_DIR / "apollo_search_results.csv"
CACHE_DIR = PROSPECTS_DIR / "apollo_cache"

load_dotenv(PROJECT_DIR / ".env")
load_dotenv(PROJECT_DIR / "scrape" / ".env")
APOLLO_API_KEY = os.getenv("APOLLO_API_KEY", "")

APOLLO_BASE = "https://api.apollo.io/v1"
REQUEST_DELAY = 0.8  # seconds between API calls

# Default search titles for mortgage LO prospecting
DEFAULT_TITLES = [
    "Loan Officer",
    "Branch Manager",
    "Mortgage Loan Originator",
    "Mortgage Broker",
    "Senior Loan Officer",
    "VP of Mortgage Lending",
    "Producing Branch Manager",
    "Mortgage Loan Officer",
]

# Exclude big banks and irrelevant companies
EXCLUDE_COMPANIES = [
    "Wells Fargo", "Bank of America", "JPMorgan Chase", "Chase",
    "Citibank", "US Bank", "PNC", "TD Bank", "Capital One",
]


# ---------------------------------------------------------------------------
# Cache
# ---------------------------------------------------------------------------
def load_cache(name: str) -> dict:
    path = CACHE_DIR / f"{name}.json"
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return {}


def save_cache(name: str, data: dict):
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    with open(CACHE_DIR / f"{name}.json", "w") as f:
        json.dump(data, f, indent=2)


# ---------------------------------------------------------------------------
# Apollo API: People Search (discover new prospects)
# ---------------------------------------------------------------------------
def apollo_people_search(titles: list, city: str, state: str,
                         page: int = 1, per_page: int = 25) -> dict:
    """
    Search Apollo for people by title and location.
    Returns API response dict.
    """
    payload = {
        "person_titles": titles,
        "person_locations": [f"{city}, {state}"] if city else [state],
        "page": page,
        "per_page": per_page,
    }

    try:
        resp = requests.post(
            f"{APOLLO_BASE}/mixed_people/search",
            json=payload,
            headers={
                "Content-Type": "application/json",
                "X-Api-Key": APOLLO_API_KEY,
            },
            timeout=30,
        )
        if resp.status_code == 200:
            return resp.json()
        elif resp.status_code == 429:
            return {"error": "rate_limited"}
        elif resp.status_code == 401:
            return {"error": "invalid_api_key"}
        else:
            return {"error": f"HTTP {resp.status_code}", "body": resp.text[:300]}
    except requests.RequestException as e:
        return {"error": str(e)}


# ---------------------------------------------------------------------------
# Apollo API: People Match (enrich existing prospect)
# ---------------------------------------------------------------------------
def apollo_people_match(first_name: str, last_name: str,
                        organization_name: str = "",
                        city: str = "", state: str = "") -> dict:
    """Match a known person to get email/phone/LinkedIn."""
    payload = {
        "first_name": first_name,
        "last_name": last_name,
        "reveal_personal_emails": True,
    }
    if organization_name:
        payload["organization_name"] = organization_name
    if state:
        payload["state"] = state
    if city:
        payload["city"] = city

    try:
        resp = requests.post(
            f"{APOLLO_BASE}/people/match",
            json=payload,
            headers={
                "Content-Type": "application/json",
                "X-Api-Key": APOLLO_API_KEY,
            },
            timeout=30,
        )
        if resp.status_code == 200:
            return resp.json()
        elif resp.status_code == 429:
            return {"error": "rate_limited"}
        else:
            return {"error": f"HTTP {resp.status_code}"}
    except requests.RequestException as e:
        return {"error": str(e)}


# ---------------------------------------------------------------------------
# Apollo API: Check credits
# ---------------------------------------------------------------------------
def check_credits():
    """Check remaining Apollo credits."""
    try:
        resp = requests.get(
            f"{APOLLO_BASE}/auth/health",
            headers={"X-Api-Key": APOLLO_API_KEY},
            timeout=10,
        )
        if resp.status_code == 200:
            data = resp.json()
            print(f"Apollo API Status: OK")
            # Try to find credit info in response
            if "credits" in data:
                print(f"Credits remaining: {data['credits']}")
            else:
                print(f"Response: {json.dumps(data, indent=2)[:500]}")
        else:
            print(f"API returned: {resp.status_code}")
            print(resp.text[:300])
    except Exception as e:
        print(f"Error: {e}")


# ---------------------------------------------------------------------------
# Extract person from search result
# ---------------------------------------------------------------------------
def extract_prospect(person: dict) -> dict:
    """Extract prospect fields from an Apollo person record."""
    org = person.get("organization", {}) or {}

    email = person.get("email", "") or ""
    if not email and person.get("personal_emails"):
        email = person["personal_emails"][0]

    phone = ""
    if person.get("phone_numbers"):
        for pn in person["phone_numbers"]:
            raw = pn.get("raw_number") or pn.get("sanitized_number", "")
            if raw:
                phone = raw
                if pn.get("type") == "mobile":
                    break  # prefer mobile

    linkedin = person.get("linkedin_url", "") or ""
    city = person.get("city", "") or ""
    state = person.get("state", "") or ""
    name = f"{person.get('first_name', '')} {person.get('last_name', '')}".strip()
    title = person.get("title", "") or ""
    company = org.get("name", "") or ""

    return {
        "Name": name,
        "Company": company,
        "Title": title,
        "City": city,
        "State": state,
        "LinkedIn URL": linkedin,
        "Email": email,
        "Phone": phone,
        "Source": "apollo_search",
        "Tier": "",  # assigned later
        "apollo_id": person.get("id", ""),
    }


# ---------------------------------------------------------------------------
# SEARCH command
# ---------------------------------------------------------------------------
def cmd_search(args):
    titles = [t.strip() for t in args.titles.split(",")]
    locations = [l.strip() for l in args.locations.split("|")]
    max_results = args.max_results
    dry_run = args.dry_run

    print(f"Apollo People Search")
    print(f"  Titles: {titles}")
    print(f"  Locations: {locations}")
    print(f"  Max results per location: {max_results}")

    if dry_run:
        per_page = 25
        pages_needed = (max_results + per_page - 1) // per_page
        total_credits = pages_needed * per_page * len(locations)
        print(f"\n  DRY RUN — would use ~{total_credits} credits")
        print(f"  ({pages_needed} pages x {per_page} results x {len(locations)} locations)")
        return

    if not APOLLO_API_KEY:
        print("ERROR: APOLLO_API_KEY not set in .env")
        sys.exit(1)

    # Load existing prospects to deduplicate
    existing_names = set()
    if PROSPECTS_CSV.exists():
        existing = pd.read_csv(PROSPECTS_CSV, dtype=str)
        existing_names = set(existing["Name"].str.lower().str.strip())
        print(f"  Existing prospects: {len(existing_names)} (will skip duplicates)")

    cache = load_cache("search_results")
    all_prospects = []

    for location in locations:
        parts = [p.strip() for p in location.split(",")]
        city = parts[0] if len(parts) >= 1 else ""
        state = parts[1] if len(parts) >= 2 else ""

        print(f"\n  Searching: {location}")
        per_page = 25
        pages_needed = (max_results + per_page - 1) // per_page
        found = 0

        for page in range(1, pages_needed + 1):
            cache_key = f"{location}|{','.join(titles)}|p{page}"
            if cache_key in cache:
                print(f"    Page {page}: cached")
                result = cache[cache_key]
            else:
                print(f"    Page {page}: calling API...", end="", flush=True)
                result = apollo_people_search(titles, city, state, page, per_page)

                if result.get("error"):
                    print(f" ERROR: {result['error']}")
                    if result["error"] == "invalid_api_key":
                        print("    Check your APOLLO_API_KEY in .env")
                        sys.exit(1)
                    if result["error"] == "rate_limited":
                        print("    Waiting 60s...")
                        time.sleep(60)
                        continue
                    break

                cache[cache_key] = result
                save_cache("search_results", cache)
                time.sleep(REQUEST_DELAY)

            people = result.get("people", [])
            if not people:
                print(f"    No more results.")
                break

            for person in people:
                prospect = extract_prospect(person)
                name_lower = prospect["Name"].lower().strip()

                # Skip if already in our list
                if name_lower in existing_names:
                    continue

                # Skip big banks
                if any(exc.lower() in prospect["Company"].lower()
                       for exc in EXCLUDE_COMPANIES):
                    continue

                existing_names.add(name_lower)
                all_prospects.append(prospect)
                found += 1

            if cache_key not in cache:
                pass  # already printed
            else:
                pass

            print(f" — {len(people)} results, {found} new")

            if found >= max_results:
                break

        print(f"  {location}: {found} new prospects found")

    if all_prospects:
        new_df = pd.DataFrame(all_prospects)
        # Assign tiers
        for idx, row in new_df.iterrows():
            title_lower = row["Title"].lower()
            if any(k in title_lower for k in ["branch manager", "president",
                   "owner", "founder", "vp", "vice president", "area manager",
                   "sales manager", "team lead"]):
                new_df.at[idx, "Tier"] = "1-Priority"
            elif any(k in title_lower for k in ["senior", "sr."]):
                new_df.at[idx, "Tier"] = "1-Priority"
            else:
                new_df.at[idx, "Tier"] = "2-Good"

        # Save search results
        new_df.to_csv(SEARCH_OUTPUT, index=False)
        print(f"\nSaved {len(new_df)} new prospects to: {SEARCH_OUTPUT}")

        # Also append to main prospect list
        if PROSPECTS_CSV.exists():
            main_df = pd.read_csv(PROSPECTS_CSV, dtype=str)
            # Drop apollo_id before merge
            append_df = new_df.drop(columns=["apollo_id"], errors="ignore")
            combined = pd.concat([main_df, append_df], ignore_index=True)
            combined.to_csv(PROSPECTS_CSV, index=False)
            print(f"Appended to main list: {PROSPECTS_CSV} ({len(combined)} total)")

        # Stats
        has_email = (new_df["Email"] != "").sum()
        has_phone = (new_df["Phone"] != "").sum()
        has_li = (new_df["LinkedIn URL"] != "").sum()
        print(f"\n  With email: {has_email}/{len(new_df)}")
        print(f"  With phone: {has_phone}/{len(new_df)}")
        print(f"  With LinkedIn: {has_li}/{len(new_df)}")
    else:
        print("\nNo new prospects found.")


# ---------------------------------------------------------------------------
# ENRICH command
# ---------------------------------------------------------------------------
def cmd_enrich(args):
    dry_run = args.dry_run

    if not PROSPECTS_CSV.exists():
        print(f"ERROR: {PROSPECTS_CSV} not found")
        sys.exit(1)

    df = pd.read_csv(PROSPECTS_CSV, dtype=str)
    print(f"Loaded {len(df)} prospects from {PROSPECTS_CSV.name}")

    # Find prospects missing email or LinkedIn
    needs_enrich = []
    for idx, row in df.iterrows():
        email = str(row.get("Email", "")).strip()
        linkedin = str(row.get("LinkedIn URL", "")).strip()
        tier = str(row.get("Tier", "")).strip()

        if tier == "3-Skip":
            continue

        if (not email or email == "nan") or (not linkedin or linkedin == "nan"):
            name = str(row.get("Name", "")).strip()
            parts = name.split()
            if len(parts) >= 2:
                needs_enrich.append({
                    "idx": idx,
                    "first": parts[0],
                    "last": parts[-1],
                    "company": str(row.get("Company", "")).strip(),
                    "city": str(row.get("City", "")).strip(),
                    "state": str(row.get("State", "")).strip(),
                })

    print(f"Need enrichment: {len(needs_enrich)} prospects (missing email or LinkedIn)")

    if dry_run:
        print(f"\nDRY RUN — would use {len(needs_enrich)} credits")
        for n in needs_enrich[:10]:
            print(f"  {n['first']} {n['last']} @ {n['company']}")
        if len(needs_enrich) > 10:
            print(f"  ... and {len(needs_enrich) - 10} more")
        return

    if not APOLLO_API_KEY:
        print("ERROR: APOLLO_API_KEY not set in .env")
        sys.exit(1)

    cache = load_cache("people_match")
    enriched = 0
    new_emails = 0
    new_phones = 0
    new_linkedin = 0

    for i, item in enumerate(needs_enrich):
        cache_key = f"{item['first']}|{item['last']}|{item['company']}".lower()

        if cache_key in cache:
            result = cache[cache_key]
        else:
            print(f"  [{i+1}/{len(needs_enrich)}] {item['first']} {item['last']} "
                  f"@ {item['company'][:30]}", end="", flush=True)
            result = apollo_people_match(
                item["first"], item["last"],
                item["company"], item["city"], item["state"]
            )
            if result.get("error"):
                print(f" — {result['error']}")
                if result["error"] == "rate_limited":
                    time.sleep(60)
                    continue
                if result["error"] == "invalid_api_key":
                    save_cache("people_match", cache)
                    sys.exit(1)
                continue

            cache[cache_key] = result
            if (i + 1) % 10 == 0:
                save_cache("people_match", cache)
            time.sleep(REQUEST_DELAY)

        # Extract and merge
        person = result.get("person", {}) or {}
        if person:
            enriched += 1
            idx = item["idx"]

            # Fill email if missing
            email = person.get("email", "") or ""
            if not email and person.get("personal_emails"):
                email = person["personal_emails"][0]
            current_email = str(df.at[idx, "Email"]).strip()
            if email and (not current_email or current_email == "nan"):
                df.at[idx, "Email"] = email
                new_emails += 1

            # Fill phone if missing
            phone = ""
            for pn in (person.get("phone_numbers") or []):
                raw = pn.get("raw_number") or pn.get("sanitized_number", "")
                if raw:
                    phone = raw
                    break
            current_phone = str(df.at[idx, "Phone"]).strip()
            if phone and (not current_phone or current_phone == "nan"):
                df.at[idx, "Phone"] = phone
                new_phones += 1

            # Fill LinkedIn if missing
            linkedin = person.get("linkedin_url", "") or ""
            current_li = str(df.at[idx, "LinkedIn URL"]).strip()
            if linkedin and (not current_li or current_li == "nan"):
                df.at[idx, "LinkedIn URL"] = linkedin
                new_linkedin += 1

            if cache_key not in cache:
                pass
            print(f" — {'email ' if email else ''}{'phone ' if phone else ''}"
                  f"{'linkedin' if linkedin else ''}")

    save_cache("people_match", cache)
    df.to_csv(PROSPECTS_CSV, index=False)

    print(f"\nEnrichment complete:")
    print(f"  Matched: {enriched}/{len(needs_enrich)}")
    print(f"  New emails: {new_emails}")
    print(f"  New phones: {new_phones}")
    print(f"  New LinkedIn: {new_linkedin}")
    print(f"  Saved: {PROSPECTS_CSV}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Apollo prospect search & enrichment")
    subparsers = parser.add_subparsers(dest="command")

    # Search subcommand
    search_p = subparsers.add_parser("search", help="Search for new prospects")
    search_p.add_argument("--titles", default=",".join(DEFAULT_TITLES),
                          help="Comma-separated job titles to search")
    search_p.add_argument("--locations", required=True,
                          help="Pipe-separated locations (e.g. 'Raleigh, NC|Charlotte, NC')")
    search_p.add_argument("--max-results", type=int, default=100,
                          help="Max results per location (default: 100)")
    search_p.add_argument("--dry-run", action="store_true")

    # Enrich subcommand
    enrich_p = subparsers.add_parser("enrich", help="Enrich existing prospect list")
    enrich_p.add_argument("--dry-run", action="store_true")

    # Credits subcommand
    subparsers.add_parser("credits", help="Check remaining Apollo credits")

    args = parser.parse_args()

    if args.command == "search":
        cmd_search(args)
    elif args.command == "enrich":
        cmd_enrich(args)
    elif args.command == "credits":
        if not APOLLO_API_KEY:
            print("ERROR: APOLLO_API_KEY not set in .env")
            sys.exit(1)
        check_credits()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
