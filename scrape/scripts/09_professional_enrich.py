"""
Step 09: Professional Enrichment
==================================

Enriches investor leads with professional context (title, company, industry)
from LinkedIn and other public sources. This data feeds into Step 18
(Outreach Playbook Generator) to create more targeted approach strategies.

HOW IT WORKS:
  1. Takes investor names from qualified/enriched data
  2. Generates LinkedIn search URLs for batch lookup
  3. Processes export CSV from Phantombuster (or any LinkedIn scraping tool)
  4. Fuzzy-matches LinkedIn profiles back to property records
  5. Outputs professional enrichment CSV

LINKEDIN DATA CONNECTOR:
  This script does NOT scrape LinkedIn directly. It generates search queries
  and processes exports from third-party tools:
  - Phantombuster (recommended): Free 14-day trial, $30-69/mo after
  - Dripify: $39-79/mo
  - Evaboot: $29-99/mo
  Any tool that exports LinkedIn search results to CSV will work.

SETUP (one-time):
  1. Sign up for Phantombuster free trial: https://phantombuster.com
  2. Install the browser extension
  3. Connect your LinkedIn session cookie (Phantombuster guides you)
  4. Use the "LinkedIn Search Export" phantom

Usage:
    # Step 1: Generate search URLs for your leads
    python scripts/09_professional_enrich.py --generate --market wake

    # Step 2: Run Phantombuster with the generated search URLs
    # (manual step — use the Phantombuster UI or API)

    # Step 3: Process the Phantombuster export
    python scripts/09_professional_enrich.py --process --market wake \\
        --linkedin-csv path/to/phantombuster_export.csv

    # Or: manually create a CSV with columns: name, title, company, industry, linkedin_url
    python scripts/09_professional_enrich.py --process --market wake \\
        --linkedin-csv path/to/manual_research.csv
"""

import argparse
import csv
import json
import re
import sys
import urllib.parse
from pathlib import Path

import pandas as pd

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent
DATA_DIR = PROJECT_DIR / "data"
DEMO_DIR = DATA_DIR / "demo"
FILTERED_DIR = DATA_DIR / "filtered"


def normalize_name(name: str) -> str:
    """Normalize a name for fuzzy matching."""
    name = name.upper().strip()
    # Remove common suffixes
    for suffix in [" LLC", " INC", " CORP", " TRUST", " TRUSTEE",
                   " LP", " LLP", " PLLC", " PA", " MD", " JR", " SR",
                   " II", " III", " IV"]:
        name = name.replace(suffix, "")
    # Remove punctuation
    name = re.sub(r'[^A-Z0-9\s]', '', name)
    # Collapse whitespace
    name = re.sub(r'\s+', ' ', name).strip()
    return name


def parse_owner_name(owner_name: str) -> dict:
    """
    Parse property record owner name into first/last for LinkedIn search.

    Formats handled:
      "LAST, FIRST"
      "LAST, FIRST MIDDLE"
      "LAST, FIRST LAST2, FIRST2" (joint ownership)
      "COMPANY NAME LLC" (entity — skip for LinkedIn)
    """
    name = str(owner_name).strip()
    if not name or name in ("nan", "None", ""):
        return {"first": "", "last": "", "is_entity": True}

    # Detect entities
    entity_keywords = ["LLC", "INC", "CORP", "TRUST", "LP", "LLP",
                       "PLLC", "PROPERTIES", "HOLDINGS", "VENTURES",
                       "GROUP", "CAPITAL", "MANAGEMENT", "INVESTMENT",
                       "CONSTRUCTION", "DEVELOPMENT", "HOMES"]
    upper = name.upper()
    if any(kw in upper for kw in entity_keywords):
        return {"first": "", "last": "", "entity_name": name, "is_entity": True}

    # Parse "LAST, FIRST" format
    parts = name.split(",")
    if len(parts) >= 2:
        last = parts[0].strip()
        first = parts[1].strip().split()[0] if parts[1].strip() else ""
        return {"first": first, "last": last, "is_entity": False}

    # Single word or unparseable
    words = name.split()
    if len(words) >= 2:
        return {"first": words[0], "last": words[-1], "is_entity": False}

    return {"first": "", "last": name, "is_entity": False}


def generate_linkedin_search_url(first: str, last: str, location: str = "Raleigh, North Carolina") -> str:
    """Generate a LinkedIn people search URL."""
    query = f"{first} {last}".strip()
    params = {
        "keywords": query,
        "origin": "GLOBAL_SEARCH_HEADER",
    }
    return f"https://www.linkedin.com/search/results/people/?{urllib.parse.urlencode(params)}"


def generate_search_queries(market: str, investors: list = None):
    """
    Generate LinkedIn search URLs for investors.
    Outputs a CSV with search URLs that can be fed to Phantombuster.
    """
    # Load investor data
    if market == "wake":
        profiles_path = DEMO_DIR / f"investment_profiles_{market}.csv"
        if profiles_path.exists():
            df = pd.read_csv(profiles_path, dtype=str)
            names = df["investor_name"].tolist()
        else:
            qualified_path = FILTERED_DIR / "wake_qualified.csv"
            df = pd.read_csv(qualified_path, dtype=str)
            names = df["owner_name_1"].unique().tolist()
        location = "Raleigh, North Carolina"
    elif market == "fl":
        profiles_path = DEMO_DIR / f"investment_profiles_{market}.csv"
        if profiles_path.exists():
            df = pd.read_csv(profiles_path, dtype=str)
            names = df["investor_name"].tolist()
        else:
            names = []
        location = "South Florida"
    else:
        print(f"  ERROR: Unknown market: {market}")
        return

    if investors:
        names = [n for n in names if n in investors]

    print(f"\n  Generating search queries for {len(names)} investors...")

    output_rows = []
    skipped_entities = 0

    for name in names:
        parsed = parse_owner_name(name)

        if parsed["is_entity"]:
            skipped_entities += 1
            output_rows.append({
                "investor_name": name,
                "first_name": "",
                "last_name": "",
                "is_entity": True,
                "search_url": "",
                "notes": "Entity — search for registered agent via NC SoS or company website",
            })
            continue

        first = parsed["first"]
        last = parsed["last"]
        url = generate_linkedin_search_url(first, last, location)

        output_rows.append({
            "investor_name": name,
            "first_name": first,
            "last_name": last,
            "is_entity": False,
            "search_url": url,
            "notes": "",
        })

    output_path = DEMO_DIR / f"linkedin_search_queries_{market}.csv"
    output_df = pd.DataFrame(output_rows)
    output_df.to_csv(output_path, index=False)

    individuals = len(output_rows) - skipped_entities
    print(f"  Individuals (searchable): {individuals}")
    print(f"  Entities (skipped):       {skipped_entities}")
    print(f"  Output saved: {output_path}")
    print(f"\n  NEXT STEPS:")
    print(f"  1. Open Phantombuster and create a 'LinkedIn Search Export' phantom")
    print(f"  2. Upload the search URLs from {output_path.name}")
    print(f"  3. Run the phantom and download the export CSV")
    print(f"  4. Process it: python scripts/09_professional_enrich.py --process --market {market} --linkedin-csv <export.csv>")


def fuzzy_match_score(name1: str, name2: str) -> float:
    """Simple fuzzy match score between two names (0-1)."""
    n1 = normalize_name(name1)
    n2 = normalize_name(name2)

    if n1 == n2:
        return 1.0

    words1 = set(n1.split())
    words2 = set(n2.split())

    if not words1 or not words2:
        return 0.0

    intersection = words1 & words2
    union = words1 | words2

    return len(intersection) / len(union)


def process_linkedin_export(market: str, linkedin_csv: str):
    """
    Process a LinkedIn export CSV and match to investor records.

    Expected columns in LinkedIn CSV (Phantombuster format):
      - firstName, lastName, fullName (or name)
      - headline (or title)
      - companyName (or company)
      - profileUrl (or linkedin_url)
      - location

    Also accepts manual CSV format:
      - name, title, company, industry, linkedin_url
    """
    linkedin_path = Path(linkedin_csv)
    if not linkedin_path.exists():
        print(f"  ERROR: LinkedIn CSV not found: {linkedin_path}")
        sys.exit(1)

    # Load LinkedIn data
    li_df = pd.read_csv(linkedin_path, dtype=str)
    print(f"  LinkedIn profiles loaded: {len(li_df)}")

    # Normalize column names (handle Phantombuster vs manual format)
    col_map = {}
    for col in li_df.columns:
        cl = col.lower().strip()
        if cl in ("fullname", "full_name", "name"):
            col_map[col] = "li_name"
        elif cl in ("firstname", "first_name"):
            col_map[col] = "li_first"
        elif cl in ("lastname", "last_name"):
            col_map[col] = "li_last"
        elif cl in ("headline", "title", "jobtitle", "job_title"):
            col_map[col] = "li_title"
        elif cl in ("companyname", "company_name", "company"):
            col_map[col] = "li_company"
        elif cl in ("profileurl", "profile_url", "linkedin_url", "url"):
            col_map[col] = "li_url"
        elif cl in ("industry",):
            col_map[col] = "li_industry"
        elif cl in ("location",):
            col_map[col] = "li_location"

    li_df = li_df.rename(columns=col_map)

    # Build full name if only first/last available
    if "li_name" not in li_df.columns:
        if "li_first" in li_df.columns and "li_last" in li_df.columns:
            li_df["li_name"] = li_df["li_first"].fillna("") + " " + li_df["li_last"].fillna("")
        else:
            print("  ERROR: Cannot find name columns in LinkedIn CSV")
            print(f"  Available columns: {list(li_df.columns)}")
            sys.exit(1)

    # Load investor names (from profiles if available, else search queries)
    profiles_path = DEMO_DIR / f"investment_profiles_{market}.csv"
    queries_path = DEMO_DIR / f"linkedin_search_queries_{market}.csv"

    if profiles_path.exists():
        inv_df = pd.read_csv(profiles_path, dtype=str)
        investor_names = inv_df["investor_name"].tolist()
    elif queries_path.exists():
        inv_df = pd.read_csv(queries_path, dtype=str)
        investor_names = inv_df["investor_name"].tolist()
    else:
        print(f"  ERROR: No investor data found for market '{market}'")
        sys.exit(1)

    # Match LinkedIn profiles to investors
    matches = []
    unmatched_investors = []

    for investor_name in investor_names:
        parsed = parse_owner_name(investor_name)
        if parsed["is_entity"]:
            continue

        best_match = None
        best_score = 0.0

        search_name = f"{parsed['first']} {parsed['last']}".strip()

        for _, li_row in li_df.iterrows():
            li_name = str(li_row.get("li_name", "")).strip()
            score = fuzzy_match_score(search_name, li_name)

            if score > best_score:
                best_score = score
                best_match = li_row

        if best_match is not None and best_score >= 0.5:
            matches.append({
                "investor_name": investor_name,
                "match_score": round(best_score, 2),
                "title": best_match.get("li_title", ""),
                "company": best_match.get("li_company", ""),
                "industry": best_match.get("li_industry", ""),
                "linkedin_url": best_match.get("li_url", ""),
                "linkedin_name": best_match.get("li_name", ""),
                "linkedin_location": best_match.get("li_location", ""),
            })
        else:
            unmatched_investors.append(investor_name)

    # Save results
    output_path = DEMO_DIR / f"professional_enrichment_{market}.csv"
    if matches:
        result_df = pd.DataFrame(matches)
        result_df.to_csv(output_path, index=False)
        print(f"\n  Matched: {len(matches)} investors")
        print(f"  Unmatched: {len(unmatched_investors)} investors")
        print(f"  Output saved: {output_path}")

        for m in matches:
            print(f"    {m['investor_name'][:35]} → {m['title']} at {m['company']} (score: {m['match_score']})")
    else:
        print(f"\n  No matches found.")

    if unmatched_investors:
        print(f"\n  Unmatched investors:")
        for name in unmatched_investors[:10]:
            print(f"    {name}")


def main():
    parser = argparse.ArgumentParser(
        description="Professional enrichment from LinkedIn data"
    )
    parser.add_argument("--market", type=str, required=True, help="Market: wake, fl")
    parser.add_argument("--generate", action="store_true",
                        help="Generate LinkedIn search URLs for investors")
    parser.add_argument("--process", action="store_true",
                        help="Process a LinkedIn export CSV")
    parser.add_argument("--linkedin-csv", type=str, default="",
                        help="Path to LinkedIn export CSV (required with --process)")
    parser.add_argument("--investors", type=str, default="",
                        help="Pipe-separated list of investor names (default: all)")
    args = parser.parse_args()

    print(f"\n{'='*60}")
    print(f"  STEP 09: PROFESSIONAL ENRICHMENT")
    print(f"  Market: {args.market.upper()}")
    print(f"{'='*60}")

    investors = [n.strip() for n in args.investors.split("|") if n.strip()] if args.investors else None

    if args.generate:
        generate_search_queries(args.market, investors)
    elif args.process:
        if not args.linkedin_csv:
            print("  ERROR: --linkedin-csv required with --process")
            sys.exit(1)
        process_linkedin_export(args.market, args.linkedin_csv)
    else:
        print("  ERROR: Must specify --generate or --process")
        print("  Example: python scripts/09_professional_enrich.py --generate --market wake")
        sys.exit(1)

    print()


if __name__ == "__main__":
    main()
