"""
Step 10: Apollo.io API Enrichment
==================================

Takes the top leads CSV (from script 05) and enriches each person via
Apollo's People Match API. Returns email, phone, LinkedIn, employer,
and social profiles.

What this script does:
  1. Reads top_leads_enriched.csv (output of script 05)
  2. For each lead with a resolved person name, calls Apollo People Match
  3. Optionally tries Apollo Organization Enrich for LLC/entity names
  4. Caches every API response in JSON (never pay twice)
  5. Writes merged results to data/enriched/apollo_results.csv

Usage:
    python scripts/10_apollo_enrich.py
    python scripts/10_apollo_enrich.py --input data/enriched/top_leads_enriched.csv
    python scripts/10_apollo_enrich.py --dry-run   # show what would be looked up

Rate Limits:
    Apollo $100/mo plan: 100 requests/minute
    We add a 0.7s delay between calls to stay safely under.

API Docs:
    People Match: POST /v1/people/match
    Org Enrich:   GET  /v1/organizations/enrich
"""

import argparse
import json
import os
import time
from pathlib import Path

import pandas as pd

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False
    print("WARNING: requests library not installed. Run: pip install requests")

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
except ImportError:
    pass

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent
ENRICHED_DIR = PROJECT_DIR / "data" / "enriched"
CACHE_DIR = PROJECT_DIR / "data" / "enriched" / "apollo_cache"

DEFAULT_INPUT = ENRICHED_DIR / "top_leads_enriched.csv"

APOLLO_API_BASE = "https://api.apollo.io/v1"
APOLLO_PEOPLE_MATCH = f"{APOLLO_API_BASE}/people/match"
APOLLO_ORG_ENRICH = f"{APOLLO_API_BASE}/organizations/enrich"

# Stay under 100 req/min — 0.7s gap = ~85 req/min
REQUEST_DELAY = 0.7

# Save cache every N lookups
CACHE_SAVE_INTERVAL = 10


# ---------------------------------------------------------------------------
# Cache management
# ---------------------------------------------------------------------------

def load_cache(cache_path: Path) -> dict:
    """Load JSON cache from disk."""
    if cache_path.exists():
        with open(cache_path, "r") as f:
            return json.load(f)
    return {}


def save_cache(cache: dict, cache_path: Path):
    """Write JSON cache to disk."""
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    with open(cache_path, "w") as f:
        json.dump(cache, f, indent=2)


def make_cache_key(first: str, last: str, domain: str = "", org: str = "") -> str:
    """Deterministic cache key from lookup params."""
    parts = [first.strip().lower(), last.strip().lower()]
    if domain:
        parts.append(domain.strip().lower())
    if org:
        parts.append(org.strip().lower())
    return "|".join(parts)


# ---------------------------------------------------------------------------
# Name parsing (reused from script 05)
# ---------------------------------------------------------------------------

def parse_person_name(name: str) -> dict:
    """Parse a person name into first, last components."""
    if not name or str(name).upper() in ("NAN", "NONE", ""):
        return {"first": "", "last": ""}

    name = str(name).strip()

    # "LAST, FIRST MIDDLE" format
    if "," in name:
        parts = name.split(",", 1)
        last = parts[0].strip()
        rest = parts[1].strip() if len(parts) > 1 else ""
        first = rest.split()[0] if rest else ""
        return {"first": first, "last": last}

    # "FIRST LAST" or "FIRST MIDDLE LAST"
    parts = name.split()
    if len(parts) >= 2:
        return {"first": parts[0], "last": parts[-1]}
    elif len(parts) == 1:
        return {"first": parts[0], "last": ""}

    return {"first": "", "last": ""}


# ---------------------------------------------------------------------------
# Apollo API calls
# ---------------------------------------------------------------------------

def apollo_people_match(first_name: str, last_name: str, api_key: str,
                        domain: str = "", organization_name: str = "",
                        state: str = "", city: str = "") -> dict:
    """
    Call Apollo People Match API.
    Returns the full API response dict, or an error dict.
    """
    if not HAS_REQUESTS:
        return {"error": "requests library not installed"}

    payload = {
        "first_name": first_name,
        "last_name": last_name,
        "reveal_personal_emails": True,
    }

    # Add optional fields that improve match accuracy
    if domain:
        payload["domain"] = domain
    if organization_name:
        payload["organization_name"] = organization_name
    if state:
        payload["state"] = state
    if city:
        payload["city"] = city

    try:
        resp = requests.post(
            APOLLO_PEOPLE_MATCH,
            json=payload,
            headers={
                "Content-Type": "application/json",
                "X-Api-Key": api_key,
            },
            timeout=30,
        )

        if resp.status_code == 200:
            return resp.json()
        elif resp.status_code == 429:
            return {"error": "rate_limited", "status_code": 429}
        elif resp.status_code == 401:
            return {"error": "invalid_api_key", "status_code": 401}
        else:
            return {"error": f"HTTP {resp.status_code}", "body": resp.text[:500]}

    except requests.exceptions.Timeout:
        return {"error": "timeout"}
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}


def apollo_org_enrich(domain: str, api_key: str) -> dict:
    """
    Call Apollo Organization Enrich API.
    Useful when we have an LLC website domain.
    """
    if not HAS_REQUESTS:
        return {"error": "requests library not installed"}

    try:
        resp = requests.get(
            APOLLO_ORG_ENRICH,
            params={"domain": domain},
            headers={"X-Api-Key": api_key},
            timeout=30,
        )

        if resp.status_code == 200:
            return resp.json()
        else:
            return {"error": f"HTTP {resp.status_code}"}

    except requests.exceptions.RequestException as e:
        return {"error": str(e)}


# ---------------------------------------------------------------------------
# Extract useful fields from Apollo response
# ---------------------------------------------------------------------------

def extract_person_fields(response: dict) -> dict:
    """Pull the fields we care about from an Apollo People Match response."""
    person = response.get("person") or {}

    if not person:
        return {
            "apollo_match": False,
            "apollo_email": "",
            "apollo_phone": "",
            "apollo_mobile": "",
            "apollo_linkedin": "",
            "apollo_title": "",
            "apollo_employer": "",
            "apollo_city": "",
            "apollo_state": "",
            "apollo_twitter": "",
            "apollo_facebook": "",
        }

    # Email: prefer personal, then work
    email = ""
    if person.get("email"):
        email = person["email"]
    elif person.get("personal_emails"):
        email = person["personal_emails"][0]

    # Phone: prefer mobile
    phone = ""
    mobile = ""
    if person.get("phone_numbers"):
        for pn in person["phone_numbers"]:
            raw = pn.get("raw_number") or pn.get("sanitized_number", "")
            ptype = pn.get("type", "")
            if ptype == "mobile" and not mobile:
                mobile = raw
            if not phone:
                phone = raw
    if person.get("organization", {}).get("phone"):
        if not phone:
            phone = person["organization"]["phone"]

    # LinkedIn
    linkedin = person.get("linkedin_url", "")

    # Employer / title
    title = person.get("title", "")
    employer = person.get("organization", {}).get("name", "") if person.get("organization") else ""

    # Location
    city = person.get("city", "")
    state = person.get("state", "")

    # Social
    twitter = person.get("twitter_url", "")
    facebook = person.get("facebook_url", "")

    return {
        "apollo_match": True,
        "apollo_email": email or "",
        "apollo_phone": phone or "",
        "apollo_mobile": mobile or "",
        "apollo_linkedin": linkedin or "",
        "apollo_title": title or "",
        "apollo_employer": employer or "",
        "apollo_city": city or "",
        "apollo_state": state or "",
        "apollo_twitter": twitter or "",
        "apollo_facebook": facebook or "",
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Apollo.io API enrichment (Step 10)")
    parser.add_argument("--input", type=str, default=str(DEFAULT_INPUT),
                        help=f"Input CSV (default: {DEFAULT_INPUT})")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show what would be looked up without calling the API")
    args = parser.parse_args()

    # Load API key
    api_key = os.environ.get("APOLLO_API_KEY", "")
    if not api_key and not args.dry_run:
        print("\n  ERROR: APOLLO_API_KEY not set in .env or environment")
        print("  Add it to scrape/.env or export APOLLO_API_KEY=your_key")
        return

    # Load input
    input_path = Path(args.input)
    if not input_path.exists():
        # Try alternate locations
        alt_paths = [
            ENRICHED_DIR / "top_leads_enriched.csv",
            ENRICHED_DIR / "merged_enriched.csv",
        ]
        for alt in alt_paths:
            if alt.exists():
                input_path = alt
                break
        else:
            print(f"\n  ERROR: Input file not found: {args.input}")
            print("  Run script 05 first, or specify --input path")
            return

    ENRICHED_DIR.mkdir(parents=True, exist_ok=True)
    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    print(f"\n  Loading: {input_path}")
    df = pd.read_csv(input_path, dtype=str, low_memory=False)
    print(f"  Records: {len(df)}")

    # Load cache
    cache_path = CACHE_DIR / "people_match_cache.json"
    cache = load_cache(cache_path)
    print(f"  Cache: {len(cache)} previous lookups loaded")

    # Identify leads that have a resolved person name
    lookups = []
    for idx, row in df.iterrows():
        resolved = str(row.get("resolved_person", "")).strip()
        if resolved.upper() in ("NAN", "NONE", ""):
            # Fall back to owner name if it's a person (not LLC)
            is_entity = str(row.get("is_entity", "")).lower() in ("true", "1", "yes")
            if not is_entity:
                resolved = str(row.get("OWN_NAME", "")).strip()
            else:
                continue

        person = parse_person_name(resolved)
        if not person["first"] or not person["last"]:
            continue

        owner = str(row.get("OWN_NAME", "")).strip()
        city = str(row.get("OWN_CITY", "")).strip()
        state = str(row.get("OWN_STATE_DOM", row.get("OWN_STATE", ""))).strip()

        # Use LLC name as organization_name for better matching
        is_entity = str(row.get("is_entity", "")).lower() in ("true", "1", "yes")
        org_name = owner if is_entity else ""

        cache_key = make_cache_key(person["first"], person["last"], org=org_name)

        lookups.append({
            "idx": idx,
            "first": person["first"],
            "last": person["last"],
            "org": org_name,
            "city": city,
            "state": state,
            "cache_key": cache_key,
            "cached": cache_key in cache,
        })

    cached_count = sum(1 for l in lookups if l["cached"])
    to_fetch = [l for l in lookups if not l["cached"]]

    print(f"\n  Leads with person name: {len(lookups)}")
    print(f"  Already cached:        {cached_count}")
    print(f"  Need API call:         {len(to_fetch)}")

    if args.dry_run:
        print("\n  DRY RUN — would look up:")
        for l in to_fetch[:10]:
            print(f"    {l['first']} {l['last']}"
                  + (f" (org: {l['org']})" if l['org'] else "")
                  + f" — {l['city']}, {l['state']}")
        if len(to_fetch) > 10:
            print(f"    ... and {len(to_fetch) - 10} more")
        est_time = len(to_fetch) * REQUEST_DELAY
        print(f"\n  Estimated time: {est_time:.0f}s ({est_time/60:.1f} min)")
        print(f"  Credits used: {len(to_fetch)} (from your monthly allowance)")
        return

    # Fetch from API
    if to_fetch:
        print(f"\n  Calling Apollo People Match API for {len(to_fetch)} leads...")
        print(f"  Estimated time: {len(to_fetch) * REQUEST_DELAY:.0f}s")

        success = 0
        errors = 0
        rate_limited = 0

        for i, lookup in enumerate(to_fetch):
            print(f"  [{i+1}/{len(to_fetch)}] {lookup['first']} {lookup['last']}"
                  + (f" ({lookup['org'][:30]})" if lookup['org'] else ""), end="")

            response = apollo_people_match(
                first_name=lookup["first"],
                last_name=lookup["last"],
                api_key=api_key,
                organization_name=lookup["org"],
                state=lookup["state"],
                city=lookup["city"],
            )

            if response.get("error") == "rate_limited":
                rate_limited += 1
                print(" — RATE LIMITED, waiting 60s...")
                time.sleep(60)
                # Retry once
                response = apollo_people_match(
                    first_name=lookup["first"],
                    last_name=lookup["last"],
                    api_key=api_key,
                    organization_name=lookup["org"],
                    state=lookup["state"],
                    city=lookup["city"],
                )

            if response.get("error") == "invalid_api_key":
                print(" — INVALID API KEY")
                print("\n  ERROR: Apollo API key is invalid. Check your .env file.")
                save_cache(cache, cache_path)
                return

            if response.get("error"):
                errors += 1
                print(f" — ERROR: {response['error']}")
            else:
                # Cache the response
                cache[lookup["cache_key"]] = response
                fields = extract_person_fields(response)
                if fields["apollo_match"] and (fields["apollo_email"] or fields["apollo_phone"]):
                    success += 1
                    hits = []
                    if fields["apollo_email"]:
                        hits.append(f"email={fields['apollo_email']}")
                    if fields["apollo_phone"]:
                        hits.append(f"phone={fields['apollo_phone']}")
                    if fields["apollo_linkedin"]:
                        hits.append("linkedin")
                    print(f" — {', '.join(hits)}")
                elif fields["apollo_match"]:
                    success += 1
                    print(" — matched (no contact info)")
                else:
                    print(" — no match")

            # Save cache periodically
            if (i + 1) % CACHE_SAVE_INTERVAL == 0:
                save_cache(cache, cache_path)

            time.sleep(REQUEST_DELAY)

        # Final cache save
        save_cache(cache, cache_path)

        print(f"\n  API Results: {success} matches, {errors} errors"
              + (f", {rate_limited} rate limits" if rate_limited else ""))

    # Merge Apollo data into dataframe
    print("\n  Merging Apollo results into lead data...")

    apollo_cols = [
        "apollo_match", "apollo_email", "apollo_phone", "apollo_mobile",
        "apollo_linkedin", "apollo_title", "apollo_employer",
        "apollo_city", "apollo_state", "apollo_twitter", "apollo_facebook",
    ]
    for col in apollo_cols:
        df[col] = ""

    matched = 0
    has_email = 0
    has_phone = 0
    has_linkedin = 0

    for lookup in lookups:
        cache_key = lookup["cache_key"]
        if cache_key in cache:
            fields = extract_person_fields(cache[cache_key])
            for col, val in fields.items():
                df.at[lookup["idx"], col] = str(val)

            if fields["apollo_match"]:
                matched += 1
            if fields["apollo_email"]:
                has_email += 1
            if fields["apollo_phone"] or fields["apollo_mobile"]:
                has_phone += 1
            if fields["apollo_linkedin"]:
                has_linkedin += 1

    # Save output
    output_path = ENRICHED_DIR / "apollo_results.csv"
    df.to_csv(output_path, index=False)

    print()
    print("=" * 60)
    print("  APOLLO ENRICHMENT RESULTS")
    print("=" * 60)
    print(f"  Total leads:       {len(df)}")
    print(f"  Lookups attempted: {len(lookups)}")
    print(f"  Apollo matched:    {matched}")
    print(f"  Got email:         {has_email}")
    print(f"  Got phone:         {has_phone}")
    print(f"  Got LinkedIn:      {has_linkedin}")
    print()
    print(f"  Hit rates:")
    if lookups:
        print(f"    Email:    {has_email}/{len(lookups)} = {has_email/len(lookups)*100:.0f}%")
        print(f"    Phone:    {has_phone}/{len(lookups)} = {has_phone/len(lookups)*100:.0f}%")
        print(f"    LinkedIn: {has_linkedin}/{len(lookups)} = {has_linkedin/len(lookups)*100:.0f}%")
    print()
    print(f"  Output: {output_path}")
    print(f"  Cache:  {cache_path} ({len(cache)} entries)")
    print()
    print(f"  NEXT STEPS:")
    print(f"    1. Review apollo_results.csv for quality")
    print(f"    2. Run: python scripts/05b_merge_enrichment.py")
    print(f"    3. Then: python scripts/06_validate_contacts.py")
    print()


if __name__ == "__main__":
    main()
