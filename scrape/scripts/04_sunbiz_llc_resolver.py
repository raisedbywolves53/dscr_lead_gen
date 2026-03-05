"""
Step 4: Resolve LLC Owners via Florida SunBiz
===============================================

For every LLC/Corp-owned property in the filtered leads, this script
searches sunbiz.org (FL Division of Corporations) to find:
  - Registered agent name and address
  - Officer/director names and titles
  - Filing date and entity status
  - The most likely human owner behind the LLC

This is important because DSCR loan outreach needs a real person's
name — you can't call or email "123 MAIN STREET LLC."

How it works:
  1. Loads qualified leads from data/filtered/
  2. Filters to LLC-flagged records
  3. Gets unique entity names (so we only look up each LLC once)
  4. For each LLC, POSTs to sunbiz.org search, then scrapes the detail page
  5. Saves progress every 50 records (safe to interrupt and resume)
  6. Merges results back into the full lead list

Rate limiting:
  - 3 seconds between requests (conservative to avoid blocks)
  - Exponential backoff if we get blocked (wait 30s, 60s, 120s...)
  - Run this overnight for large counties — it's slow by design

Usage:
    python scripts/04_sunbiz_llc_resolver.py --county seminole
    python scripts/04_sunbiz_llc_resolver.py --county seminole --max-lookups 100
    python scripts/04_sunbiz_llc_resolver.py --county all
"""

import argparse
import json
import re
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup
import pandas as pd

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent
FILTERED_DIR = PROJECT_DIR / "data" / "filtered"
CACHE_DIR = PROJECT_DIR / "data" / "raw"  # cache lives alongside raw data

# ---------------------------------------------------------------------------
# SunBiz config
# ---------------------------------------------------------------------------
SUNBIZ_SEARCH_URL = "https://search.sunbiz.org/Inquiry/CorporationSearch/ByName"
SUNBIZ_BASE = "https://search.sunbiz.org"

REQUEST_DELAY = 3.0       # seconds between requests
MAX_BACKOFF = 300          # max backoff wait (5 minutes)
SAVE_EVERY = 50           # save cache every N lookups
DEFAULT_MAX_LOOKUPS = 500  # max lookups per run

# Titles that indicate the actual owner/decision-maker of the LLC
PRIORITY_TITLES = [
    "MGR", "MGRM", "MANAGER", "MANAGING MEMBER", "MEMBER",
    "PRESIDENT", "PRES", "CEO", "OWNER", "PRINCIPAL",
]

# If the registered agent name contains any of these, it's probably
# a service company, not the actual owner
AGENT_SERVICE_KEYWORDS = [
    " LLC", " INC", " CORP", " SERVICE", " AGENT", " REGISTERED",
    " SOLUTIONS", " FILING", " STATUTORY",
]


# ---------------------------------------------------------------------------
# SunBiz session — needs cookies from an initial page visit
# ---------------------------------------------------------------------------

def create_session() -> requests.Session:
    """
    Create a requests session with browser-like headers.
    Visits the SunBiz search page first to pick up session cookies —
    without this, SunBiz/Cloudflare may block our requests.
    """
    session = requests.Session()
    session.headers.update({
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    })

    # Visit the search page to get cookies
    print("  Establishing SunBiz session...")
    try:
        resp = session.get(SUNBIZ_SEARCH_URL, timeout=30)
        if resp.status_code == 200:
            print("  Session established.")
        else:
            print(f"  WARNING: SunBiz returned status {resp.status_code}. May have issues.")
    except requests.RequestException as e:
        print(f"  WARNING: Could not reach SunBiz: {e}")

    return session


# ---------------------------------------------------------------------------
# Search and parse a single entity
# ---------------------------------------------------------------------------

def search_sunbiz(entity_name: str, session: requests.Session) -> dict:
    """
    Search sunbiz.org for an entity and extract owner details.

    Steps:
      1. POST search term to /ByName endpoint
      2. Find the best-matching result link
      3. GET the detail page
      4. Parse detailSection divs for agent, officers, filing info

    Returns a dict with all extracted fields.
    """
    result = {
        "entity_name_searched": entity_name,
        "registered_agent_name": "",
        "registered_agent_address": "",
        "officer_names": "",          # semicolon-separated "NAME (TITLE)" list
        "principal_address": "",
        "mailing_address": "",
        "status": "",
        "filing_date": "",
        "entity_number": "",
        "resolved_person": "",        # best guess at the human owner
    }

    # Clean the name for searching — remove trailing LLC/INC/etc
    search_name = entity_name.strip()
    for suffix in [" LLC", " L.L.C.", " L.L.C", " INC", " INC.",
                   " CORP", " CORP.", " LP", " LTD", " LTD."]:
        if search_name.upper().endswith(suffix):
            search_name = search_name[: len(search_name) - len(suffix)].strip()

    # ----- Step 1: POST search -----
    try:
        resp = session.post(
            SUNBIZ_SEARCH_URL,
            data={
                "SearchTerm": search_name,
                "InquiryType": "EntityName",
                "SearchNameOrder": "",
            },
            timeout=30,
        )
    except requests.RequestException as e:
        result["status"] = f"ERROR: {e}"
        return result

    if resp.status_code != 200:
        result["status"] = f"HTTP {resp.status_code}"
        return result

    soup = BeautifulSoup(resp.text, "html.parser")

    # ----- Step 2: find the detail link -----
    links = soup.find_all("a", href=re.compile(r"SearchResultDetail"))
    if not links:
        result["status"] = "NO RESULTS"
        return result

    # Prefer exact name match; fall back to first result
    detail_href = None
    entity_upper = entity_name.upper().strip()
    for link in links:
        if link.get_text(strip=True).upper() == entity_upper:
            detail_href = link["href"]
            break
    if not detail_href:
        detail_href = links[0]["href"]

    detail_url = SUNBIZ_BASE + detail_href

    # Small delay before hitting the detail page
    time.sleep(1)

    # ----- Step 3: GET detail page -----
    try:
        detail_resp = session.get(detail_url, timeout=30)
    except requests.RequestException as e:
        result["status"] = f"DETAIL ERROR: {e}"
        return result

    if detail_resp.status_code != 200:
        result["status"] = f"DETAIL HTTP {detail_resp.status_code}"
        return result

    detail_soup = BeautifulSoup(detail_resp.text, "html.parser")

    # ----- Step 4: parse detailSection divs -----
    sections = detail_soup.find_all("div", class_="detailSection")
    officers = []

    for section in sections:
        section_text = section.get_text(separator="\n", strip=True)
        lines = [l.strip() for l in section_text.split("\n") if l.strip()]
        if not lines:
            continue

        header = lines[0]

        # --- Filing Information ---
        if "Filing Information" in header:
            for i, line in enumerate(lines):
                if "Document Number" in line and i + 1 < len(lines):
                    result["entity_number"] = lines[i + 1]
                elif "Status" in line and "PDA" not in line and i + 1 < len(lines):
                    result["status"] = lines[i + 1]
                elif "Date Filed" in line and i + 1 < len(lines):
                    result["filing_date"] = lines[i + 1]

        # --- Principal Address ---
        elif "Principal Address" in header:
            addr_lines = [l for l in lines[1:] if not l.startswith("Changed:")]
            if addr_lines:
                result["principal_address"] = ", ".join(addr_lines)

        # --- Mailing Address ---
        elif "Mailing Address" in header:
            addr_lines = [l for l in lines[1:] if not l.startswith("Changed:")]
            if addr_lines:
                result["mailing_address"] = ", ".join(addr_lines)

        # --- Registered Agent ---
        elif "Registered Agent" in header:
            agent_lines = [
                l for l in lines[1:]
                if not l.startswith("Name Changed:") and not l.startswith("Address Changed:")
            ]
            if agent_lines:
                result["registered_agent_name"] = agent_lines[0]
            if len(agent_lines) > 1:
                result["registered_agent_address"] = ", ".join(agent_lines[1:])

        # --- Officers / Directors / Authorized Persons ---
        elif "Officer/Director" in header or "Authorized Person" in header:
            i = 1  # skip the header line
            while i < len(lines):
                line = lines[i]
                if line == "Name & Address":
                    i += 1
                    continue
                if line.startswith("Title "):
                    title_val = line.replace("Title ", "").strip()
                    officer = {"title": title_val, "name": "", "address": ""}
                    # Next line is the person's name
                    if i + 1 < len(lines) and not lines[i + 1].startswith("Title "):
                        officer["name"] = lines[i + 1]
                        i += 1
                        # Collect address lines until next Title or end
                        addr_parts = []
                        while (
                            i + 1 < len(lines)
                            and not lines[i + 1].startswith("Title ")
                            and not lines[i + 1].startswith("Annual")
                            and not lines[i + 1].startswith("Document")
                        ):
                            i += 1
                            addr_parts.append(lines[i])
                        if addr_parts:
                            officer["address"] = ", ".join(addr_parts)
                    officers.append(officer)
                i += 1

    # Format officers list as semicolon-separated string
    if officers:
        result["officer_names"] = "; ".join(
            f"{o['name']} ({o['title']})" for o in officers if o.get("name")
        )

    # ----- Determine the most likely human owner -----
    # Priority: Manager/Member/President from officers list
    for officer in officers:
        if officer.get("title", "").upper() in PRIORITY_TITLES and officer.get("name"):
            result["resolved_person"] = officer["name"]
            break

    # Fallback: first officer
    if not result["resolved_person"] and officers:
        for officer in officers:
            if officer.get("name"):
                result["resolved_person"] = officer["name"]
                break

    # Last resort: registered agent (only if it looks like a person, not a service)
    if not result["resolved_person"] and result["registered_agent_name"]:
        agent = result["registered_agent_name"].upper()
        if not any(kw in agent for kw in AGENT_SERVICE_KEYWORDS):
            result["resolved_person"] = result["registered_agent_name"]

    return result


# ---------------------------------------------------------------------------
# Cache management — save/load progress so we can resume
# ---------------------------------------------------------------------------

def load_cache(county_name: str) -> dict:
    """Load the resolution cache for a county (or create empty)."""
    cache_file = CACHE_DIR / f"sunbiz_cache_{county_name}.json"
    if cache_file.exists():
        with open(cache_file) as f:
            cache = json.load(f)
        print(f"  Loaded {len(cache)} cached resolutions from previous runs.")
        return cache
    return {}


def save_cache(county_name: str, cache: dict):
    """Save the resolution cache to disk."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_file = CACHE_DIR / f"sunbiz_cache_{county_name}.json"
    with open(cache_file, "w") as f:
        json.dump(cache, f, indent=2)


# ---------------------------------------------------------------------------
# Main processing
# ---------------------------------------------------------------------------

def resolve_county(county_name: str, max_lookups: int):
    """Resolve LLC owners for a single county."""

    # Load the qualified leads file
    input_file = FILTERED_DIR / f"{county_name}_qualified.csv"
    if not input_file.exists():
        print(f"  No qualified leads file found: {input_file}")
        print(f"  Run Step 3 first: python scripts/03_filter_icp.py --county {county_name}")
        return

    df = pd.read_csv(input_file, dtype=str, low_memory=False)
    print(f"  Loaded {len(df):,} qualified leads from {input_file.name}")

    # Filter to LLC-flagged records
    llc_mask = df["is_llc"].astype(str).str.lower().isin(["true", "1", "yes"])
    llc_count = llc_mask.sum()

    if llc_count == 0:
        print("  No LLC-flagged records found. Nothing to resolve.")
        df.to_csv(FILTERED_DIR / f"{county_name}_llc_resolved.csv", index=False)
        return

    print(f"  LLC-flagged records: {llc_count:,}")

    # Get unique entity names (no point looking up the same LLC twice)
    unique_entities = df.loc[llc_mask, "owner_name_1"].dropna().unique().tolist()
    print(f"  Unique LLC names: {len(unique_entities):,}")

    # Load cache (previous lookups)
    cache = load_cache(county_name)
    already_cached = sum(1 for e in unique_entities if e in cache)
    to_lookup = [e for e in unique_entities if e not in cache]

    if already_cached > 0:
        print(f"  Already cached: {already_cached:,}")

    if not to_lookup:
        print("  All entities already cached. Skipping lookups.")
    else:
        # Limit lookups
        if len(to_lookup) > max_lookups:
            # Prioritize entities that own the most properties
            entity_counts = (
                df.loc[llc_mask]
                .groupby("owner_name_1")
                .size()
                .sort_values(ascending=False)
            )
            priority_order = [e for e in entity_counts.index if e in to_lookup]
            to_lookup = priority_order[:max_lookups]
            print(f"  Limiting to top {max_lookups} entities (by property count).")

        print(f"  Entities to look up: {len(to_lookup):,}")
        print(f"  Estimated time: ~{len(to_lookup) * (REQUEST_DELAY + 1) / 60:.0f} minutes")
        print()

        # Create session and start lookups
        session = create_session()
        backoff = REQUEST_DELAY
        resolved_count = 0
        error_count = 0

        for i, entity_name in enumerate(to_lookup):
            # Progress update
            if i > 0 and i % 10 == 0:
                print(f"  Progress: {i}/{len(to_lookup)} "
                      f"({resolved_count} resolved, {error_count} errors)")

            # Save cache periodically
            if i > 0 and i % SAVE_EVERY == 0:
                save_cache(county_name, cache)
                print(f"  Cache saved ({len(cache)} entries).")

            # Do the lookup
            result = search_sunbiz(entity_name, session)
            cache[entity_name] = result

            if result["resolved_person"]:
                resolved_count += 1
                backoff = REQUEST_DELAY  # reset backoff on success
            elif "ERROR" in result.get("status", "") or "HTTP" in result.get("status", ""):
                error_count += 1
                # Exponential backoff on errors (likely rate limited)
                backoff = min(backoff * 2, MAX_BACKOFF)
                print(f"  Blocked/error on '{entity_name[:40]}'. "
                      f"Backing off {backoff:.0f}s...")
                time.sleep(backoff)
                continue

            # Normal rate-limit delay
            time.sleep(REQUEST_DELAY)

        # Final cache save
        save_cache(county_name, cache)
        print()
        print(f"  Lookups complete: {resolved_count}/{len(to_lookup)} resolved")
        if error_count > 0:
            print(f"  Errors: {error_count} (may need to re-run for these)")

    # -----------------------------------------------------------------
    # Merge resolution data back into the full lead list
    # -----------------------------------------------------------------
    print()
    print("  Merging resolution data into leads...")

    df["resolved_person"] = ""
    df["registered_agent_name"] = ""
    df["registered_agent_address"] = ""
    df["officer_names"] = ""
    df["sunbiz_filing_date"] = ""
    df["sunbiz_status"] = ""

    for idx, row in df.iterrows():
        owner = str(row.get("owner_name_1", ""))
        if owner in cache:
            res = cache[owner]
            df.at[idx, "resolved_person"] = res.get("resolved_person", "")
            df.at[idx, "registered_agent_name"] = res.get("registered_agent_name", "")
            df.at[idx, "registered_agent_address"] = res.get("registered_agent_address", "")
            df.at[idx, "officer_names"] = res.get("officer_names", "")
            df.at[idx, "sunbiz_filing_date"] = res.get("filing_date", "")
            df.at[idx, "sunbiz_status"] = res.get("status", "")

    # Save output
    output_file = FILTERED_DIR / f"{county_name}_llc_resolved.csv"
    df.to_csv(output_file, index=False)

    # -----------------------------------------------------------------
    # Summary
    # -----------------------------------------------------------------
    resolved_mask = df["resolved_person"].astype(str).str.strip() != ""
    total_resolved = resolved_mask.sum()

    print()
    print("=" * 60)
    print("  SUNBIZ RESOLUTION SUMMARY")
    print("=" * 60)
    print(f"  Total leads:           {len(df):,}")
    print(f"  LLC-owned:             {llc_count:,}")
    print(f"  Unique LLCs:           {len(unique_entities):,}")
    print(f"  Resolved to person:    {total_resolved:,}")
    if llc_count > 0:
        print(f"  Resolution rate:       {total_resolved / llc_count * 100:.1f}%")
    print(f"  Saved: {output_file}")
    print()

    # Show a few examples
    examples = df[resolved_mask].head(5)
    if not examples.empty:
        print("  EXAMPLE RESOLUTIONS:")
        print("  " + "-" * 55)
        for _, row in examples.iterrows():
            llc = str(row["owner_name_1"])[:35]
            person = str(row["resolved_person"])[:30]
            print(f"  {llc:35s} → {person}")
        print()


def main():
    parser = argparse.ArgumentParser(
        description="Resolve LLC owners via SunBiz (Step 4)"
    )
    parser.add_argument(
        "--county",
        type=str,
        required=True,
        help='County name (e.g. "seminole") or "all"',
    )
    parser.add_argument(
        "--max-lookups",
        type=int,
        default=DEFAULT_MAX_LOOKUPS,
        help=f"Max SunBiz lookups per run (default: {DEFAULT_MAX_LOOKUPS})",
    )
    args = parser.parse_args()

    county_arg = args.county.strip().lower()

    if county_arg == "all":
        qualified_files = sorted(FILTERED_DIR.glob("*_qualified.csv"))
        if not qualified_files:
            print(f"\nNo qualified lead files found in {FILTERED_DIR}/")
            print("Run Step 3 first: python scripts/03_filter_icp.py --county <name>")
            return
        counties = [f.stem.replace("_qualified", "") for f in qualified_files]
    else:
        counties = [county_arg.replace(" ", "_").replace("-", "_")]

    for county_name in counties:
        print()
        print("=" * 60)
        print(f"  RESOLVING LLCs: {county_name.upper()}")
        print("=" * 60)
        resolve_county(county_name, args.max_lookups)

    print("=" * 60)
    print(f"  Next step: python scripts/05_enrich_contacts.py --county {county_arg}")
    print("=" * 60)


if __name__ == "__main__":
    main()
