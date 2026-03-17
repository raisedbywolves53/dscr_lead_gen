"""
Apollo Multi-Market Cohort Experiment
======================================

Structured experiment to burn Apollo credits across multiple markets and
buyer segments before subscription cancels.

Three cohorts:
  A. Branch Managers at independent brokerages (60% of credits)
  B. DSCR-specialist individual LOs (25% of credits)
  C. Wholesale lender Account Executives (15% of credits)

Five markets: Cleveland, Indianapolis, Pittsburgh, Kansas City, Philadelphia

Two phases:
  Phase 1: 25 results per cohort per market (375 credits) — measure hit rates
  Phase 2: Scale winners based on Phase 1 metrics (remaining credits)

Usage:
    # Phase 1: test all markets and cohorts (375 credits)
    python sales/scripts/apollo_experiment.py phase1

    # Phase 1 dry run (no API calls)
    python sales/scripts/apollo_experiment.py phase1 --dry-run

    # Analyze Phase 1 results
    python sales/scripts/apollo_experiment.py analyze

    # Phase 2: scale specific market+cohort cells
    python sales/scripts/apollo_experiment.py phase2 --cells "cleveland_A,indianapolis_A,pittsburgh_B"

    # Phase 2: scale all cells above threshold
    python sales/scripts/apollo_experiment.py phase2 --min-hit-rate 50

    # Tag results with research intelligence (zero credits)
    python sales/scripts/apollo_experiment.py tag

    # Check credits
    python sales/scripts/apollo_experiment.py credits

Output:
    sales/prospects/experiment/phase1_results.csv
    sales/prospects/experiment/phase2_results.csv
    sales/prospects/experiment/metrics.csv
    sales/prospects/experiment/ae_targets.csv
    sales/prospects/experiment/tagged_prospects.csv
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
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent.parent
PROSPECTS_DIR = PROJECT_DIR / "sales" / "prospects"
EXPERIMENT_DIR = PROSPECTS_DIR / "experiment"
CACHE_DIR = EXPERIMENT_DIR / "cache"

load_dotenv(PROJECT_DIR / ".env")
load_dotenv(PROJECT_DIR / "scrape" / ".env")
APOLLO_API_KEY = os.getenv("APOLLO_API_KEY", "")

APOLLO_BASE = "https://api.apollo.io/v1"
REQUEST_DELAY = 0.8  # seconds between API calls

# ---------------------------------------------------------------------------
# Market definitions
# ---------------------------------------------------------------------------
MARKETS = {
    "cleveland": {
        "city": "Cleveland",
        "state": "OH",
        "state_full": "Ohio",
        "dscr_math": "Median $139,900, DSCR 1.35x, 11.3% gross yield",
        "reia": "Great Lakes REIA (3rd Thursday), OREIA (15 chapters)",
        "score": 4.45,
    },
    "indianapolis": {
        "city": "Indianapolis",
        "state": "IN",
        "state_full": "Indiana",
        "dscr_math": "Median $230K, 6.8% yield, +7.9pp occupancy gain, 47% renters",
        "reia": "CIREIA (1st Thursday, largest in state)",
        "score": 4.35,
    },
    "pittsburgh": {
        "city": "Pittsburgh",
        "state": "PA",
        "state_full": "Pennsylvania",
        "dscr_math": "Median $250K, DSCR 1.25+, +6.1pp occupancy gain",
        "reia": "ACRE (1st Tuesday), PREIA (3rd Tuesday)",
        "score": 4.20,
    },
    "kansas_city": {
        "city": "Kansas City",
        "state": "MO",
        "state_full": "Missouri",
        "dscr_math": "Median $240K, 7.5%+ yields, MO = #1 investor buyer share (21.2%)",
        "reia": "MAREI (2nd Tuesday, ~400 members)",
        "score": 4.15,
    },
    "philadelphia": {
        "city": "Philadelphia",
        "state": "PA",
        "state_full": "Pennsylvania",
        "dscr_math": "Median $290K, strong bridge-to-DSCR 2-4 unit market",
        "reia": "DIG (Glenside), Delco Property Investors",
        "score": 4.05,
    },
}

# ---------------------------------------------------------------------------
# Cohort definitions
# ---------------------------------------------------------------------------
COHORTS = {
    "A": {
        "name": "Branch Managers",
        "weight": 0.60,
        "titles": [
            "Branch Manager",
            "Producing Branch Manager",
            "VP of Mortgage Lending",
            "Vice President Mortgage",
            "Area Manager",
            "Regional Manager",
            "Sales Manager",
            "Managing Director",
        ],
        "industry_tags": ["mortgage", "lending"],  # filter to mortgage companies
        "search_by": "city",  # search by city + state
    },
    "B": {
        "name": "DSCR Specialist LOs",
        "weight": 0.25,
        "titles": [
            "Loan Officer",
            "Mortgage Loan Originator",
            "Mortgage Broker",
            "Senior Loan Officer",
            "Loan Originator",
            "DSCR Loan Officer",
            "Non-QM Loan Officer",
            "Investment Property Loan Officer",
        ],
        "industry_tags": ["mortgage", "lending"],
        "search_by": "city",
    },
    "C": {
        "name": "Wholesale Lender AEs",
        "weight": 0.15,
        "titles": [
            "Account Executive",
            "Regional Sales Manager",
            "Wholesale Account Manager",
            "Business Development Manager",
            "Territory Manager",
        ],
        "industry_tags": ["mortgage", "lending", "financial services"],
        "search_by": "state",  # AEs cover states, not cities
    },
}

# Exclude big banks and large retail lenders
EXCLUDE_COMPANIES = [
    "Wells Fargo", "Bank of America", "JPMorgan Chase", "Chase",
    "Citibank", "US Bank", "PNC", "TD Bank", "Capital One",
    "Rocket Mortgage", "Quicken Loans", "UWM", "United Wholesale Mortgage",
    "loanDepot", "Freedom Mortgage", "Mr. Cooper", "Pennymac",
    "Caliber Home Loans", "New American Funding", "Flagstar",
]

# Known DSCR wholesale lenders (for post-search tagging)
DSCR_LENDERS = [
    "angel oak", "deephaven", "a&d mortgage", "newfi", "kiavi",
    "visio", "easy street", "rcn capital", "lima one", "civic financial",
    "corevest", "redwood", "toorak", "velocity mortgage", "griffin funding",
    "truss financial", "arc home", "acra lending", "carrington",
    "mimutual", "change lending", "sprout mortgage",
]


# ---------------------------------------------------------------------------
# Cache
# ---------------------------------------------------------------------------
def load_cache(name: str) -> dict:
    path = CACHE_DIR / f"{name}.json"
    if path.exists():
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_cache(name: str, data: dict):
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    with open(CACHE_DIR / f"{name}.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str)


# ---------------------------------------------------------------------------
# Apollo API — Two-step flow:
#   1. api_search: discover people (returns IDs + first name + org, no PII)
#   2. people/enrich: reveal full contact data per person (1 credit each)
# ---------------------------------------------------------------------------
def apollo_people_search(titles: list, location: str,
                         industry_tags: list = None,
                         page: int = 1, per_page: int = 25) -> dict:
    """Search Apollo for people (discovery only — no contact data).
    Returns IDs, first names, org names, has_email/has_phone flags."""
    payload = {
        "person_titles": titles,
        "person_locations": [location],
        "page": page,
        "per_page": per_page,
    }

    if industry_tags:
        payload["q_organization_keyword_tags"] = industry_tags

    try:
        resp = requests.post(
            f"{APOLLO_BASE}/mixed_people/api_search",
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


def apollo_enrich_person(apollo_id: str) -> dict:
    """Reveal full contact data for a person by apollo_id. Costs 1 credit."""
    try:
        resp = requests.post(
            f"{APOLLO_BASE}/people/enrich",
            json={"id": apollo_id},
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
            print("Apollo API Status: OK")
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
# Extract prospect from enriched Apollo person
# ---------------------------------------------------------------------------
def extract_prospect(person: dict, market: str, cohort: str) -> dict:
    """Extract prospect fields from an enriched Apollo person record."""
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
                    break

    linkedin = person.get("linkedin_url", "") or ""
    city = person.get("city", "") or ""
    state = person.get("state", "") or ""
    name = f"{person.get('first_name', '')} {person.get('last_name', '')}".strip()
    title = person.get("title", "") or ""
    company = org.get("name", "") or ""
    company_size = org.get("estimated_num_employees", "") or ""
    headline = person.get("headline", "") or ""

    return {
        "Name": name,
        "Company": company,
        "Title": title,
        "Headline": headline,
        "City": city,
        "State": state,
        "LinkedIn URL": linkedin,
        "Email": email,
        "Phone": phone,
        "Company Size": str(company_size),
        "Market": market,
        "Cohort": cohort,
        "Cohort Name": COHORTS[cohort]["name"],
        "Source": f"apollo_experiment_{market}_{cohort}",
        "apollo_id": person.get("id", ""),
    }


def extract_search_stub(person: dict) -> dict:
    """Extract minimal info from search result (before enrichment)."""
    org = person.get("organization", {}) or {}
    return {
        "apollo_id": person.get("id", ""),
        "first_name": person.get("first_name", ""),
        "title": person.get("title", ""),
        "company": org.get("name", ""),
        "has_email": person.get("has_email", False),
        "has_phone": person.get("has_direct_phone", ""),
    }


# ---------------------------------------------------------------------------
# Run search for one market + cohort cell (two-step: search → enrich)
# ---------------------------------------------------------------------------
def search_cell(market_key: str, cohort_key: str, max_results: int = 25,
                dry_run: bool = False) -> list:
    """Run Apollo search + enrich for a single market × cohort cell.

    Step 1: api_search discovers people (IDs + first name + org)
    Step 2: people/enrich reveals full contact data per person (1 credit each)
    """
    market = MARKETS[market_key]
    cohort = COHORTS[cohort_key]

    # Build location string
    if cohort["search_by"] == "state":
        location = f"{market['state_full']}"
    else:
        location = f"{market['city']}, {market['state']}"

    cell_id = f"{market_key}_{cohort_key}"
    print(f"\n  [{cell_id}] {cohort['name']} in {location}")
    print(f"    Titles: {cohort['titles'][:3]}...")
    if cohort.get("industry_tags"):
        print(f"    Industry: {cohort['industry_tags']}")
    print(f"    Max results: {max_results}")

    if dry_run:
        per_page = 25
        pages_needed = (max_results + per_page - 1) // per_page
        est_credits = min(pages_needed * per_page, max_results)
        print(f"    DRY RUN — would use ~{est_credits} enrich credits")
        return []

    # --- Step 1: Search (discover candidates) ---
    search_cache = load_cache(f"search_{cell_id}")
    enrich_cache = load_cache(f"enrich_{cell_id}")
    all_prospects = []
    seen_ids = set()

    per_page = 25
    # Search more than we need to account for exclusions
    search_pages = ((max_results * 2) + per_page - 1) // per_page
    candidates = []

    for page in range(1, search_pages + 1):
        cache_key = f"p{page}"
        if cache_key in search_cache:
            result = search_cache[cache_key]
        else:
            print(f"    Search page {page}...", end="", flush=True)

            result = apollo_people_search(
                titles=cohort["titles"],
                location=location,
                industry_tags=cohort.get("industry_tags") or None,
                page=page,
                per_page=per_page,
            )

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

            search_cache[cache_key] = result
            save_cache(f"search_{cell_id}", search_cache)
            time.sleep(REQUEST_DELAY)

        people = result.get("people", [])
        if not people:
            if cache_key not in search_cache:
                print(" — no more results")
            break

        for person in people:
            stub = extract_search_stub(person)
            apollo_id = stub["apollo_id"]

            if not apollo_id or apollo_id in seen_ids:
                continue

            # Skip big banks by company name
            company_lower = stub["company"].lower()
            if any(exc.lower() in company_lower for exc in EXCLUDE_COMPANIES):
                continue

            seen_ids.add(apollo_id)
            candidates.append(stub)

        if not (cache_key in search_cache and "p" not in cache_key):
            print(f" — {len(people)} found, {len(candidates)} candidates")

        if len(candidates) >= max_results:
            break

    # Trim to max_results
    candidates = candidates[:max_results]
    print(f"    Candidates to enrich: {len(candidates)}")

    if not candidates:
        print(f"    Total: 0 prospects")
        return []

    # --- Step 2: Enrich (reveal contact data, 1 credit each) ---
    enriched = 0
    skipped = 0

    for i, stub in enumerate(candidates):
        apollo_id = stub["apollo_id"]

        # Check enrich cache
        if apollo_id in enrich_cache:
            person_data = enrich_cache[apollo_id]
        else:
            print(f"    Enrich [{i+1}/{len(candidates)}] "
                  f"{stub['first_name']} @ {stub['company'][:30]}...", end="", flush=True)

            result = apollo_enrich_person(apollo_id)

            if result.get("error"):
                print(f" ERROR: {result['error']}")
                if result["error"] == "rate_limited":
                    print("    Waiting 60s...")
                    time.sleep(60)
                    # Retry once
                    result = apollo_enrich_person(apollo_id)
                    if result.get("error"):
                        skipped += 1
                        continue
                elif result["error"] == "invalid_api_key":
                    save_cache(f"enrich_{cell_id}", enrich_cache)
                    sys.exit(1)
                else:
                    skipped += 1
                    continue

            person_data = result.get("person", {}) or {}
            enrich_cache[apollo_id] = person_data

            if (i + 1) % 10 == 0:
                save_cache(f"enrich_{cell_id}", enrich_cache)

            has_e = "email" if person_data.get("email") else ""
            has_p = "phone" if person_data.get("phone_numbers") else ""
            has_l = "linkedin" if person_data.get("linkedin_url") else ""
            print(f" — {has_e} {has_p} {has_l}".rstrip())

            time.sleep(REQUEST_DELAY)

        if person_data:
            prospect = extract_prospect(person_data, market_key, cohort_key)
            all_prospects.append(prospect)
            enriched += 1

    save_cache(f"enrich_{cell_id}", enrich_cache)

    print(f"    Total: {enriched} enriched, {skipped} skipped")
    return all_prospects


# ---------------------------------------------------------------------------
# Phase 1: Test all cells
# ---------------------------------------------------------------------------
def cmd_phase1(args):
    """Run Phase 1 test across all markets and cohorts."""
    dry_run = args.dry_run
    max_per_cell = args.max_per_cell

    if not dry_run and not APOLLO_API_KEY:
        print("ERROR: APOLLO_API_KEY not set in .env")
        sys.exit(1)

    EXPERIMENT_DIR.mkdir(parents=True, exist_ok=True)

    total_credits = max_per_cell * len(MARKETS) * len(COHORTS)
    print(f"=" * 60)
    print(f"  APOLLO EXPERIMENT — PHASE 1")
    print(f"=" * 60)
    print(f"  Markets: {', '.join(MARKETS.keys())}")
    print(f"  Cohorts: {', '.join(f'{k} ({v['name']})' for k, v in COHORTS.items())}")
    print(f"  Results per cell: {max_per_cell}")
    print(f"  Total cells: {len(MARKETS) * len(COHORTS)}")
    print(f"  Est. credits: ~{total_credits}")
    if dry_run:
        print(f"  MODE: DRY RUN")

    all_prospects = []

    for market_key in MARKETS:
        for cohort_key in COHORTS:
            prospects = search_cell(market_key, cohort_key,
                                    max_results=max_per_cell,
                                    dry_run=dry_run)
            all_prospects.extend(prospects)

    if all_prospects:
        df = pd.DataFrame(all_prospects)
        output_path = EXPERIMENT_DIR / "phase1_results.csv"
        df.to_csv(output_path, index=False)
        print(f"\n{'=' * 60}")
        print(f"  PHASE 1 COMPLETE")
        print(f"{'=' * 60}")
        print(f"  Total prospects: {len(df)}")
        print(f"  Output: {output_path}")

        # Quick metrics
        print(f"\n  Hit rates by cell:")
        for market_key in MARKETS:
            for cohort_key in COHORTS:
                cell = df[(df["Market"] == market_key) & (df["Cohort"] == cohort_key)]
                if len(cell) == 0:
                    continue
                email_rate = (cell["Email"].str.strip() != "").sum() / len(cell) * 100
                phone_rate = (cell["Phone"].str.strip() != "").sum() / len(cell) * 100
                li_rate = (cell["LinkedIn URL"].str.strip() != "").sum() / len(cell) * 100
                print(f"    {market_key}_{cohort_key}: "
                      f"{len(cell)} results | "
                      f"email {email_rate:.0f}% | "
                      f"phone {phone_rate:.0f}% | "
                      f"linkedin {li_rate:.0f}%")

        print(f"\n  Run 'analyze' for detailed metrics and recommendations.")
    elif not dry_run:
        print("\nNo prospects found.")


# ---------------------------------------------------------------------------
# Analyze Phase 1 results
# ---------------------------------------------------------------------------
def cmd_analyze(args):
    """Analyze Phase 1 results and recommend Phase 2 allocation."""
    results_path = EXPERIMENT_DIR / "phase1_results.csv"
    if not results_path.exists():
        print(f"ERROR: {results_path} not found. Run phase1 first.")
        sys.exit(1)

    df = pd.read_csv(results_path, dtype=str)
    print(f"\n{'=' * 60}")
    print(f"  PHASE 1 ANALYSIS")
    print(f"{'=' * 60}")
    print(f"  Total prospects: {len(df)}")

    # Build metrics per cell
    metrics = []
    for market_key in MARKETS:
        for cohort_key in COHORTS:
            cell = df[(df["Market"] == market_key) & (df["Cohort"] == cohort_key)]
            if len(cell) == 0:
                continue

            n = len(cell)
            has_email = (cell["Email"].fillna("").str.strip() != "").sum()
            has_phone = (cell["Phone"].fillna("").str.strip() != "").sum()
            has_li = (cell["LinkedIn URL"].fillna("").str.strip() != "").sum()

            # Reachability: has email OR LinkedIn (our two outreach channels)
            reachable = ((cell["Email"].fillna("").str.strip() != "") |
                         (cell["LinkedIn URL"].fillna("").str.strip() != "")).sum()

            # Title relevance: check if titles contain mortgage/loan/lending keywords
            mortgage_keywords = ["mortgage", "loan", "lending", "branch", "originator",
                                 "broker", "account executive", "wholesale"]
            title_relevant = cell["Title"].fillna("").str.lower().apply(
                lambda t: any(kw in t for kw in mortgage_keywords)
            ).sum()

            # Independence: not at a large company (>200 employees)
            indie = cell["Company Size"].apply(
                lambda s: True if not s or s == "nan" or s == ""
                else int(s) <= 200 if s.isdigit() else True
            ).sum()

            email_rate = has_email / n * 100
            phone_rate = has_phone / n * 100
            li_rate = has_li / n * 100
            reach_rate = reachable / n * 100
            relevance_rate = title_relevant / n * 100
            indie_rate = indie / n * 100

            # Composite score for Phase 2 recommendation
            composite = (reach_rate * 0.40 + relevance_rate * 0.35 +
                         indie_rate * 0.15 + phone_rate * 0.10)

            metrics.append({
                "Cell": f"{market_key}_{cohort_key}",
                "Market": market_key,
                "Cohort": cohort_key,
                "Cohort Name": COHORTS[cohort_key]["name"],
                "Results": n,
                "Email %": f"{email_rate:.0f}%",
                "Phone %": f"{phone_rate:.0f}%",
                "LinkedIn %": f"{li_rate:.0f}%",
                "Reachable %": f"{reach_rate:.0f}%",
                "Relevant %": f"{relevance_rate:.0f}%",
                "Independent %": f"{indie_rate:.0f}%",
                "Composite": f"{composite:.1f}",
                "_composite_raw": composite,
            })

    metrics_df = pd.DataFrame(metrics)
    metrics_df = metrics_df.sort_values("_composite_raw", ascending=False)

    # Print results
    print(f"\n  Cell Performance (sorted by composite score):\n")
    print(f"  {'Cell':<25} {'N':>4} {'Email':>7} {'Phone':>7} {'LI':>7} "
          f"{'Reach':>7} {'Relev':>7} {'Indie':>7} {'Score':>7}")
    print(f"  {'-'*25} {'-'*4} {'-'*7} {'-'*7} {'-'*7} "
          f"{'-'*7} {'-'*7} {'-'*7} {'-'*7}")

    for _, row in metrics_df.iterrows():
        print(f"  {row['Cell']:<25} {row['Results']:>4} {row['Email %']:>7} "
              f"{row['Phone %']:>7} {row['LinkedIn %']:>7} "
              f"{row['Reachable %']:>7} {row['Relevant %']:>7} "
              f"{row['Independent %']:>7} {row['Composite']:>7}")

    # Recommendations
    print(f"\n  Phase 2 Recommendations:")
    top_cells = metrics_df.head(5)
    bottom_cells = metrics_df.tail(3)

    print(f"\n  SCALE (top 5):")
    for _, row in top_cells.iterrows():
        print(f"    {row['Cell']} — composite {row['Composite']}")

    print(f"\n  KILL (bottom 3):")
    for _, row in bottom_cells.iterrows():
        print(f"    {row['Cell']} — composite {row['Composite']}")

    # Save metrics
    save_df = metrics_df.drop(columns=["_composite_raw"])
    metrics_path = EXPERIMENT_DIR / "metrics.csv"
    save_df.to_csv(metrics_path, index=False)
    print(f"\n  Metrics saved: {metrics_path}")

    # Phase 2 credit allocation recommendation
    remaining_credits = 4020 - len(df)  # approximate
    print(f"\n  Estimated remaining credits: ~{remaining_credits}")
    print(f"  Suggested Phase 2 command:")
    top_cell_ids = ",".join(top_cells["Cell"].tolist())
    print(f"    python sales/scripts/apollo_experiment.py phase2 --cells \"{top_cell_ids}\"")


# ---------------------------------------------------------------------------
# Phase 2: Scale winners
# ---------------------------------------------------------------------------
def cmd_phase2(args):
    """Scale winning cells from Phase 1."""
    dry_run = args.dry_run
    max_per_cell = args.max_per_cell

    if not dry_run and not APOLLO_API_KEY:
        print("ERROR: APOLLO_API_KEY not set in .env")
        sys.exit(1)

    EXPERIMENT_DIR.mkdir(parents=True, exist_ok=True)

    # Determine which cells to scale
    cells_to_run = []
    if args.cells:
        for cell_str in args.cells.split(","):
            cell_str = cell_str.strip()
            parts = cell_str.rsplit("_", 1)
            if len(parts) == 2 and parts[1] in COHORTS:
                market_key = parts[0]
                cohort_key = parts[1]
                if market_key in MARKETS:
                    cells_to_run.append((market_key, cohort_key))
                else:
                    print(f"  Warning: unknown market '{market_key}', skipping")
            else:
                print(f"  Warning: invalid cell '{cell_str}', expected format: market_cohort")
    elif args.min_hit_rate:
        metrics_path = EXPERIMENT_DIR / "metrics.csv"
        if not metrics_path.exists():
            print("ERROR: Run 'analyze' first to generate metrics.")
            sys.exit(1)
        metrics_df = pd.read_csv(metrics_path, dtype=str)
        for _, row in metrics_df.iterrows():
            reach_pct = float(row["Reachable %"].rstrip("%"))
            if reach_pct >= args.min_hit_rate:
                parts = row["Cell"].rsplit("_", 1)
                cells_to_run.append((parts[0], parts[1]))
    else:
        print("ERROR: Specify --cells or --min-hit-rate")
        sys.exit(1)

    if not cells_to_run:
        print("No cells to run.")
        return

    total_credits = max_per_cell * len(cells_to_run)
    print(f"\n{'=' * 60}")
    print(f"  APOLLO EXPERIMENT — PHASE 2")
    print(f"{'=' * 60}")
    print(f"  Cells to scale: {len(cells_to_run)}")
    print(f"  Results per cell: {max_per_cell}")
    print(f"  Est. credits: ~{total_credits}")
    for mk, ck in cells_to_run:
        print(f"    {mk}_{ck}: {COHORTS[ck]['name']} in {MARKETS[mk]['city']}, {MARKETS[mk]['state']}")
    if dry_run:
        print(f"  MODE: DRY RUN")

    # Load Phase 1 results to deduplicate
    existing_names = set()
    phase1_path = EXPERIMENT_DIR / "phase1_results.csv"
    if phase1_path.exists():
        phase1_df = pd.read_csv(phase1_path, dtype=str)
        existing_names = set(phase1_df["Name"].str.lower().str.strip())
        print(f"  Dedup against {len(existing_names)} Phase 1 results")

    all_prospects = []

    for market_key, cohort_key in cells_to_run:
        prospects = search_cell(market_key, cohort_key,
                                max_results=max_per_cell,
                                dry_run=dry_run)
        # Deduplicate against Phase 1
        for p in prospects:
            if p["Name"].lower().strip() not in existing_names:
                all_prospects.append(p)
                existing_names.add(p["Name"].lower().strip())

    if all_prospects:
        df = pd.DataFrame(all_prospects)
        output_path = EXPERIMENT_DIR / "phase2_results.csv"
        df.to_csv(output_path, index=False)
        print(f"\n{'=' * 60}")
        print(f"  PHASE 2 COMPLETE")
        print(f"{'=' * 60}")
        print(f"  New prospects: {len(df)}")
        print(f"  Output: {output_path}")

        # Separate AE targets
        ae_df = df[df["Cohort"] == "C"]
        if len(ae_df) > 0:
            ae_path = EXPERIMENT_DIR / "ae_targets.csv"
            ae_df.to_csv(ae_path, index=False)
            print(f"  AE targets: {len(ae_df)} saved to {ae_path}")
    elif not dry_run:
        print("\nNo new prospects found.")


# ---------------------------------------------------------------------------
# Tag results with research intelligence
# ---------------------------------------------------------------------------
def cmd_tag(args):
    """Tag all experiment results with research intelligence (zero credits)."""
    # Load all results
    dfs = []
    for fname in ["phase1_results.csv", "phase2_results.csv"]:
        path = EXPERIMENT_DIR / fname
        if path.exists():
            dfs.append(pd.read_csv(path, dtype=str))

    if not dfs:
        print("ERROR: No experiment results found. Run phase1 first.")
        sys.exit(1)

    df = pd.concat(dfs, ignore_index=True)
    df = df.drop_duplicates(subset=["Name", "Company"], keep="first")
    print(f"Loaded {len(df)} unique prospects")

    # Tag 1: DSCR Lender Affiliation
    df["Tag: DSCR Lender"] = df["Company"].fillna("").str.lower().apply(
        lambda c: "Yes" if any(lender in c for lender in DSCR_LENDERS) else ""
    )

    # Tag 2: REIA Proximity
    df["Tag: REIA Info"] = df["Market"].apply(
        lambda m: MARKETS.get(m, {}).get("reia", "") if m and m != "nan" else ""
    )

    # Tag 3: Market DSCR Math
    df["Tag: DSCR Math"] = df["Market"].apply(
        lambda m: MARKETS.get(m, {}).get("dscr_math", "") if m and m != "nan" else ""
    )

    # Tag 4: Market Score
    df["Tag: Market Score"] = df["Market"].apply(
        lambda m: str(MARKETS.get(m, {}).get("score", "")) if m and m != "nan" else ""
    )

    # Tag 5: Tier assignment
    def assign_tier(row):
        title = str(row.get("Title", "")).lower()
        cohort = str(row.get("Cohort", ""))

        if cohort == "C":
            return "AE-Relationship"

        if any(k in title for k in ["branch manager", "producing branch",
               "president", "owner", "founder", "vp", "vice president",
               "area manager", "regional manager", "managing director",
               "sales manager"]):
            return "1-Priority"

        if any(k in title for k in ["senior", "sr."]):
            return "1-Priority"

        # Check for DSCR keywords in headline
        headline = str(row.get("Headline", "")).lower()
        if any(kw in headline for kw in ["dscr", "non-qm", "investor",
               "investment property", "private lending"]):
            return "1-Priority"

        return "2-Good"

    df["Tier"] = df.apply(assign_tier, axis=1)

    # Save tagged results
    output_path = EXPERIMENT_DIR / "tagged_prospects.csv"
    df.to_csv(output_path, index=False)

    # Summary
    print(f"\nTagged {len(df)} prospects:")
    print(f"  DSCR Lender affiliated: {(df['Tag: DSCR Lender'] == 'Yes').sum()}")
    print(f"  With REIA info: {(df['Tag: REIA Info'].str.strip() != '').sum()}")

    print(f"\n  By Tier:")
    for tier, count in df["Tier"].value_counts().items():
        print(f"    {tier}: {count}")

    print(f"\n  By Market:")
    for market, count in df["Market"].value_counts().items():
        print(f"    {market}: {count}")

    print(f"\n  By Cohort:")
    for cohort, count in df["Cohort Name"].value_counts().items():
        print(f"    {cohort}: {count}")

    print(f"\n  Output: {output_path}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="Apollo multi-market cohort experiment")
    subparsers = parser.add_subparsers(dest="command")

    # Phase 1
    p1 = subparsers.add_parser("phase1", help="Run Phase 1 test batches")
    p1.add_argument("--dry-run", action="store_true")
    p1.add_argument("--max-per-cell", type=int, default=25,
                     help="Max results per market × cohort cell (default: 25)")

    # Analyze
    subparsers.add_parser("analyze", help="Analyze Phase 1 results")

    # Phase 2
    p2 = subparsers.add_parser("phase2", help="Scale winning cells")
    p2.add_argument("--cells", type=str,
                     help="Comma-separated cells to scale (e.g. cleveland_A,indianapolis_A)")
    p2.add_argument("--min-hit-rate", type=float,
                     help="Auto-scale all cells above this reachability pct")
    p2.add_argument("--max-per-cell", type=int, default=200,
                     help="Max results per cell (default: 200)")
    p2.add_argument("--dry-run", action="store_true")

    # Tag
    subparsers.add_parser("tag", help="Tag results with research intelligence")

    # Credits
    subparsers.add_parser("credits", help="Check remaining Apollo credits")

    args = parser.parse_args()

    if args.command == "phase1":
        cmd_phase1(args)
    elif args.command == "analyze":
        cmd_analyze(args)
    elif args.command == "phase2":
        cmd_phase2(args)
    elif args.command == "tag":
        cmd_tag(args)
    elif args.command == "credits":
        if not APOLLO_API_KEY:
            print("ERROR: APOLLO_API_KEY not set in .env")
            sys.exit(1)
        check_credits()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
