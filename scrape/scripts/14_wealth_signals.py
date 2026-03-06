"""
Step 14: Wealth Signals
========================

Gathers wealth-indicator data for investor leads from free public sources:
  A. FEC.gov — political donation history
  B. ProPublica Nonprofit Explorer — IRS 990 org search
  C. SunBiz Officer Reverse Lookup — all LLCs where a person is an officer

Reads enriched lead data, queries each source for every resolved person name,
caches all responses, and outputs a scored wealth signals CSV.

Usage:
    python scripts/14_wealth_signals.py
    python scripts/14_wealth_signals.py --input data/enriched/apollo_results.csv
    python scripts/14_wealth_signals.py --dry-run

Rate Limits:
    FEC.gov: 1,000/hour — we add 0.5s delay
    ProPublica: no published limit — we add 1s delay
    SunBiz: aggressive anti-bot — we add 3s delay
"""

import argparse
import json
import os
import re
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
    from bs4 import BeautifulSoup
    HAS_BS4 = True
except ImportError:
    HAS_BS4 = False
    print("WARNING: beautifulsoup4 not installed. SunBiz lookups will be skipped.")

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
SIGNALS_DIR = PROJECT_DIR / "data" / "signals"
CACHE_DIR = SIGNALS_DIR / "wealth_cache"

DEFAULT_INPUT = ENRICHED_DIR / "top_leads_enriched.csv"
ALT_INPUT = ENRICHED_DIR / "apollo_results.csv"

OUTPUT_PATH = SIGNALS_DIR / "wealth_signals.csv"

# FEC API
FEC_API_BASE = "https://api.open.fec.gov/v1"
FEC_SCHEDULE_A = f"{FEC_API_BASE}/schedules/schedule_a/"
FEC_DELAY = 0.5  # seconds between FEC calls

# ProPublica Nonprofit Explorer
PROPUBLICA_SEARCH = "https://projects.propublica.org/nonprofits/api/v2/search.json"
PROPUBLICA_DELAY = 1.0

# SunBiz Officer Reverse Lookup
SUNBIZ_OFFICER_SEARCH = "https://search.sunbiz.org/Inquiry/CorporationSearch/SearchByOfficerRA"
SUNBIZ_BASE = "https://search.sunbiz.org"
SUNBIZ_DELAY = 3.0

# Cache save interval
CACHE_SAVE_INTERVAL = 10


# ---------------------------------------------------------------------------
# Cache management
# ---------------------------------------------------------------------------

def normalize_name_key(name: str) -> str:
    """Normalize a person name into a consistent cache key."""
    return re.sub(r"[^a-z ]", "", name.lower()).strip().replace(" ", "_")


def load_cache(person_key: str) -> dict | None:
    """Load cached wealth data for a person. Returns None if not cached."""
    cache_file = CACHE_DIR / f"{person_key}.json"
    if cache_file.exists():
        with open(cache_file, "r") as f:
            return json.load(f)
    return None


def save_cache(person_key: str, data: dict):
    """Save wealth data for a person to cache."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_file = CACHE_DIR / f"{person_key}.json"
    with open(cache_file, "w") as f:
        json.dump(data, f, indent=2)


# ---------------------------------------------------------------------------
# Name parsing
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
# A. FEC.gov Political Donations
# ---------------------------------------------------------------------------

def lookup_fec(first: str, last: str, api_key: str) -> dict:
    """
    Search FEC Schedule A (individual contributions) by contributor name.
    Returns summary of donation history.
    """
    if not HAS_REQUESTS:
        return {"error": "requests not installed"}

    # FEC expects "LAST, FIRST" format for contributor_name
    contributor_name = f"{last}, {first}"

    try:
        resp = requests.get(
            FEC_SCHEDULE_A,
            params={
                "contributor_name": contributor_name,
                "contributor_state": "FL",
                "api_key": api_key,
                "per_page": 20,
                "sort": "-contribution_receipt_date",
            },
            timeout=30,
        )

        if resp.status_code == 200:
            data = resp.json()
            results = data.get("results", [])

            if not results:
                return {
                    "total_donated": 0,
                    "donation_count": 0,
                    "recipients": [],
                    "date_range": "",
                    "raw_count": 0,
                }

            total = sum(
                float(r.get("contribution_receipt_amount", 0))
                for r in results
                if r.get("contribution_receipt_amount")
            )
            recipients = list(set(
                r.get("committee", {}).get("name", "UNKNOWN")
                for r in results
                if r.get("committee")
            ))
            dates = sorted(
                r.get("contribution_receipt_date", "")
                for r in results
                if r.get("contribution_receipt_date")
            )
            date_range = ""
            if dates:
                date_range = f"{dates[0]} to {dates[-1]}" if len(dates) > 1 else dates[0]

            # Total count from pagination metadata (may exceed 20 returned)
            pagination = data.get("pagination", {})
            raw_count = pagination.get("count", len(results))

            return {
                "total_donated": round(total, 2),
                "donation_count": raw_count,
                "recipients": recipients[:10],  # cap at 10 for readability
                "date_range": date_range,
                "raw_count": raw_count,
            }

        elif resp.status_code == 429:
            return {"error": "rate_limited"}
        else:
            return {"error": f"HTTP {resp.status_code}"}

    except requests.exceptions.RequestException as e:
        return {"error": str(e)}


# ---------------------------------------------------------------------------
# B. ProPublica Nonprofit Explorer (IRS 990)
# ---------------------------------------------------------------------------

def lookup_propublica_990(person_name: str) -> dict:
    """
    Search ProPublica Nonprofit Explorer by person name.
    This searches organization names — useful if the person runs a foundation.
    """
    if not HAS_REQUESTS:
        return {"error": "requests not installed"}

    try:
        resp = requests.get(
            PROPUBLICA_SEARCH,
            params={"q": person_name},
            timeout=30,
        )

        if resp.status_code == 200:
            data = resp.json()
            orgs = data.get("organizations", [])

            if not orgs:
                return {"orgs_found": []}

            # Extract org names — filter to ones that plausibly match the person
            org_names = []
            for org in orgs[:10]:
                name = org.get("name", "")
                if name:
                    org_names.append(name)

            return {"orgs_found": org_names}

        else:
            return {"error": f"HTTP {resp.status_code}"}

    except requests.exceptions.RequestException as e:
        return {"error": str(e)}


# ---------------------------------------------------------------------------
# C. SunBiz Officer Reverse Lookup
# ---------------------------------------------------------------------------

def lookup_sunbiz_officer(person_name: str) -> dict:
    """
    Search SunBiz by officer/RA name to find all entities where they hold a position.
    POST to the SearchByOfficerRA endpoint, parse the results table.
    """
    if not HAS_REQUESTS or not HAS_BS4:
        return {"error": "requests or beautifulsoup4 not installed"}

    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
    })

    try:
        # First GET the search page to get any anti-CSRF tokens / cookies
        get_resp = session.get(
            SUNBIZ_OFFICER_SEARCH,
            timeout=30,
        )
        if get_resp.status_code != 200:
            return {"error": f"GET page failed: HTTP {get_resp.status_code}"}

        # Parse for any hidden form fields (verification tokens, etc.)
        page_soup = BeautifulSoup(get_resp.text, "html.parser")
        form_data = {}
        hidden_inputs = page_soup.find_all("input", {"type": "hidden"})
        for inp in hidden_inputs:
            name = inp.get("name")
            value = inp.get("value", "")
            if name:
                form_data[name] = value

        # Add our search parameters
        form_data["SearchTerm"] = person_name
        form_data["SearchType"] = "Officer"

        # POST the search
        post_resp = session.post(
            SUNBIZ_OFFICER_SEARCH,
            data=form_data,
            timeout=30,
            allow_redirects=True,
        )

        if post_resp.status_code != 200:
            return {"error": f"POST failed: HTTP {post_resp.status_code}"}

        soup = BeautifulSoup(post_resp.text, "html.parser")

        # Parse the results table
        # SunBiz officer search results typically appear in a table or div list
        entities = []

        # Look for search result rows — SunBiz uses divs with specific classes
        # or a table. We'll try multiple selectors.

        # Pattern 1: Table rows
        result_table = soup.find("table", {"id": "searchResultsTable"})
        if result_table:
            rows = result_table.find_all("tr")
            for row in rows[1:]:  # skip header
                cols = row.find_all("td")
                if len(cols) >= 2:
                    entity_name = cols[0].get_text(strip=True)
                    title = cols[1].get_text(strip=True) if len(cols) > 1 else ""
                    if entity_name:
                        entities.append({
                            "entity_name": entity_name,
                            "title": title,
                        })

        # Pattern 2: div-based results (SunBiz sometimes uses this)
        if not entities:
            result_divs = soup.select("div.searchResultDetail, div.corporationName")
            for div in result_divs:
                entity_name = div.get_text(strip=True)
                if entity_name and len(entity_name) > 2:
                    entities.append({
                        "entity_name": entity_name,
                        "title": "",
                    })

        # Pattern 3: Search result links
        if not entities:
            # Look for links to entity detail pages
            links = soup.find_all("a", href=re.compile(r"/Inquiry/CorporationSearch/SearchResultDetail"))
            for link in links:
                entity_name = link.get_text(strip=True)
                # Try to find the title in adjacent elements
                parent = link.find_parent("tr") or link.find_parent("div")
                title = ""
                if parent:
                    title_elem = parent.find("span", class_=re.compile(r"title|officer", re.I))
                    if title_elem:
                        title = title_elem.get_text(strip=True)
                if entity_name and len(entity_name) > 2:
                    entities.append({
                        "entity_name": entity_name,
                        "title": title,
                    })

        return {
            "entity_count": len(entities),
            "entities": entities[:50],  # cap at 50
        }

    except requests.exceptions.RequestException as e:
        return {"error": str(e)}


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------

def calculate_wealth_score(fec_data: dict, nonprofit_data: dict, sunbiz_data: dict) -> int:
    """
    Calculate wealth signal score (0-20) additively:
      +5  FEC donations found
      +5  ProPublica 990 org presence
      +5  3+ SunBiz entities
      +5  5+ SunBiz entities
    """
    score = 0

    # FEC donations
    if fec_data.get("total_donated", 0) > 0:
        score += 5

    # ProPublica 990 presence
    if nonprofit_data.get("orgs_found") and len(nonprofit_data["orgs_found"]) > 0:
        score += 5

    # SunBiz entity count
    entity_count = sunbiz_data.get("entity_count", 0)
    if entity_count >= 3:
        score += 5
    if entity_count >= 5:
        score += 5

    return score


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Wealth Signals (Step 14)")
    parser.add_argument("--input", type=str, default=None,
                        help=f"Input CSV (default: {DEFAULT_INPUT} or apollo_results.csv)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show what would be looked up without making any requests")
    parser.add_argument("--skip-fec", action="store_true",
                        help="Skip FEC lookups (useful when rate-limited with DEMO_KEY)")
    args = parser.parse_args()

    # Load FEC API key
    fec_api_key = os.environ.get("FEC_API_KEY", "DEMO_KEY")

    # Resolve input file
    if args.input:
        input_path = Path(args.input)
    else:
        # Try default, then alternate
        if DEFAULT_INPUT.exists():
            input_path = DEFAULT_INPUT
        elif ALT_INPUT.exists():
            input_path = ALT_INPUT
        else:
            print(f"\n  ERROR: No input file found.")
            print(f"  Tried: {DEFAULT_INPUT}")
            print(f"  Tried: {ALT_INPUT}")
            print(f"  Run script 05 or 10 first, or specify --input path")
            return

    if not input_path.exists():
        print(f"\n  ERROR: Input file not found: {input_path}")
        return

    # Create output directories
    SIGNALS_DIR.mkdir(parents=True, exist_ok=True)
    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    print(f"\n  Loading: {input_path}")
    df = pd.read_csv(input_path, dtype=str, low_memory=False)
    print(f"  Records: {len(df)}")
    print(f"  FEC API key: {fec_api_key[:8]}...")

    # ---------------------------------------------------------------------------
    # Identify leads with resolved person names
    # ---------------------------------------------------------------------------
    lookups = []
    for idx, row in df.iterrows():
        resolved = str(row.get("resolved_person", "")).strip()
        if resolved.upper() in ("NAN", "NONE", ""):
            # Fall back to owner name if it looks like a person
            is_entity = str(row.get("is_entity", "")).lower() in ("true", "1", "yes")
            if not is_entity:
                resolved = str(row.get("OWN_NAME", "")).strip()
            else:
                continue

        person = parse_person_name(resolved)
        if not person["first"] or not person["last"]:
            continue

        owner = str(row.get("OWN_NAME", "")).strip()
        person_key = normalize_name_key(resolved)
        cached = load_cache(person_key)

        lookups.append({
            "idx": idx,
            "resolved_person": resolved,
            "first": person["first"],
            "last": person["last"],
            "owner": owner,
            "person_key": person_key,
            "cached": cached is not None,
        })

    cached_count = sum(1 for l in lookups if l["cached"])
    to_fetch = [l for l in lookups if not l["cached"]]

    print(f"\n  Leads with person name: {len(lookups)}")
    print(f"  Already cached:        {cached_count}")
    print(f"  Need lookups:          {len(to_fetch)}")

    if args.dry_run:
        print("\n  DRY RUN — would look up:")
        for i, l in enumerate(to_fetch[:25]):
            print(f"    [{i+1}] {l['resolved_person']}")
        if len(to_fetch) > 25:
            print(f"    ... and {len(to_fetch) - 25} more")
        # Time estimate: FEC(0.5s) + ProPublica(1s) + SunBiz(3s) = ~4.5s per lead
        est_time = len(to_fetch) * 4.5
        print(f"\n  Estimated time: {est_time:.0f}s ({est_time/60:.1f} min)")
        return

    # ---------------------------------------------------------------------------
    # Run lookups for uncached leads
    # ---------------------------------------------------------------------------
    if to_fetch:
        print(f"\n  Running wealth signal lookups for {len(to_fetch)} leads...")
        est_time = len(to_fetch) * 4.5
        print(f"  Estimated time: {est_time:.0f}s ({est_time/60:.1f} min)\n")

    for i, lookup in enumerate(to_fetch):
        person_key = lookup["person_key"]
        first = lookup["first"]
        last = lookup["last"]
        full_name = lookup["resolved_person"]

        result = {
            "resolved_person": full_name,
            "fec": {},
            "nonprofit": {},
            "sunbiz": {},
        }

        # --- A. FEC Lookup ---
        if args.skip_fec:
            fec_data = {}
        else:
            fec_data = lookup_fec(first, last, fec_api_key)
            if fec_data.get("error") == "rate_limited":
                print(f"  [{i+1}/{len(to_fetch)}] {full_name} — FEC rate limited, waiting 60s...")
                time.sleep(60)
                fec_data = lookup_fec(first, last, fec_api_key)
            time.sleep(FEC_DELAY)
        result["fec"] = fec_data

        # --- B. ProPublica 990 Lookup ---
        nonprofit_data = lookup_propublica_990(full_name)
        result["nonprofit"] = nonprofit_data
        time.sleep(PROPUBLICA_DELAY)

        # --- C. SunBiz Officer Reverse Lookup ---
        sunbiz_data = lookup_sunbiz_officer(full_name)
        result["sunbiz"] = sunbiz_data
        time.sleep(SUNBIZ_DELAY)

        # Cache the result
        save_cache(person_key, result)

        # Progress output
        fec_total = fec_data.get("total_donated", 0)
        fec_count = fec_data.get("donation_count", 0)
        sb_count = sunbiz_data.get("entity_count", 0)
        np_count = len(nonprofit_data.get("orgs_found", []))

        parts = []
        if fec_total > 0:
            parts.append(f"FEC: ${fec_total:,.0f} ({fec_count} donations)")
        else:
            parts.append("FEC: none")
        if np_count > 0:
            parts.append(f"990: {np_count} orgs")
        if sb_count > 0:
            parts.append(f"SunBiz: {sb_count} entities")
        else:
            parts.append("SunBiz: none")

        print(f"  [{i+1}/{len(to_fetch)}] {full_name} — {', '.join(parts)}")

    # ---------------------------------------------------------------------------
    # Build output CSV from all cached data (cached + newly fetched)
    # ---------------------------------------------------------------------------
    print(f"\n  Building output CSV...")

    rows = []
    for lookup in lookups:
        person_key = lookup["person_key"]
        cached_data = load_cache(person_key)

        if cached_data is None:
            # Should not happen, but handle gracefully
            rows.append({
                "OWN_NAME": lookup["owner"],
                "resolved_person": lookup["resolved_person"],
                "fec_total_donated": 0,
                "fec_donation_count": 0,
                "fec_recipients": "",
                "fec_date_range": "",
                "nonprofit_orgs_found": "",
                "sunbiz_entity_count": 0,
                "sunbiz_entities": "",
                "wealth_signal_score": 0,
            })
            continue

        fec = cached_data.get("fec", {})
        nonprofit = cached_data.get("nonprofit", {})
        sunbiz = cached_data.get("sunbiz", {})

        # Format FEC recipients
        recipients = fec.get("recipients", [])
        recipients_str = ", ".join(recipients) if recipients else ""

        # Format nonprofit orgs
        np_orgs = nonprofit.get("orgs_found", [])
        np_str = ", ".join(np_orgs) if np_orgs else ""

        # Format SunBiz entities
        sb_entities = sunbiz.get("entities", [])
        sb_parts = []
        for ent in sb_entities:
            name = ent.get("entity_name", "")
            title = ent.get("title", "")
            if title:
                sb_parts.append(f"{name} ({title})")
            else:
                sb_parts.append(name)
        sb_str = "; ".join(sb_parts)

        score = calculate_wealth_score(fec, nonprofit, sunbiz)

        rows.append({
            "OWN_NAME": lookup["owner"],
            "resolved_person": lookup["resolved_person"],
            "fec_total_donated": fec.get("total_donated", 0),
            "fec_donation_count": fec.get("donation_count", 0),
            "fec_recipients": recipients_str,
            "fec_date_range": fec.get("date_range", ""),
            "nonprofit_orgs_found": np_str,
            "sunbiz_entity_count": sunbiz.get("entity_count", 0),
            "sunbiz_entities": sb_str,
            "wealth_signal_score": score,
        })

    out_df = pd.DataFrame(rows)
    out_df.to_csv(OUTPUT_PATH, index=False)

    # ---------------------------------------------------------------------------
    # Summary
    # ---------------------------------------------------------------------------
    total = len(out_df)
    fec_hits = len(out_df[out_df["fec_total_donated"].astype(float) > 0])
    np_hits = len(out_df[out_df["nonprofit_orgs_found"].astype(str).str.len() > 0])
    sb_hits = len(out_df[out_df["sunbiz_entity_count"].astype(int) > 0])
    scored = len(out_df[out_df["wealth_signal_score"].astype(int) > 0])

    print()
    print("=" * 60)
    print("  WEALTH SIGNALS RESULTS")
    print("=" * 60)
    print(f"  Total leads processed: {total}")
    print(f"  FEC donors found:     {fec_hits}")
    print(f"  990 org matches:      {np_hits}")
    print(f"  SunBiz entities:      {sb_hits}")
    print(f"  Leads with score > 0: {scored}")
    if total > 0:
        avg_score = out_df["wealth_signal_score"].astype(int).mean()
        max_score = out_df["wealth_signal_score"].astype(int).max()
        print(f"  Avg wealth score:     {avg_score:.1f} / 20")
        print(f"  Max wealth score:     {max_score} / 20")
    print()
    print(f"  Output: {OUTPUT_PATH}")
    print(f"  Cache:  {CACHE_DIR}/ ({len(list(CACHE_DIR.glob('*.json')))} entries)")
    print()
    print(f"  NEXT STEPS:")
    print(f"    1. Review wealth_signals.csv")
    print(f"    2. Run: python scripts/15_network_mapping.py")
    print(f"    3. Or:  python scripts/20_build_dossier.py")
    print()


if __name__ == "__main__":
    main()
