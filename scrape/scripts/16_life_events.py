"""
Step 16: Life Event Detection
==============================

Searches county clerk records for life events that create urgency
signals: divorce, probate, liens, lis pendens (pre-foreclosure),
code violations, and judgment liens.

These events indicate a motivated seller, a need to refinance,
or a distressed situation — all high-value outreach triggers.

What this script does:
  1. Reads enriched leads with resolved person names
  2. For each lead, searches county clerk records by owner name
  3. Filters for non-mortgage document types (divorce, liens, etc.)
  4. Classifies each event by urgency level
  5. Outputs life_events.csv with per-lead event summary

Usage:
    python scripts/16_life_events.py
    python scripts/16_life_events.py --input data/enriched/top_leads_enriched.csv

Note: This script depends on county clerk scraping infrastructure
from script 11. Until script 11 is built, this script will attempt
direct clerk portal searches. If clerk portals block scraping,
this script gracefully reports what it cannot access.
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

try:
    from bs4 import BeautifulSoup
    HAS_BS4 = True
except ImportError:
    HAS_BS4 = False

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
except ImportError:
    pass

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent
ENRICHED_DIR = PROJECT_DIR / "data" / "enriched"
SIGNALS_DIR = PROJECT_DIR / "data" / "signals"
CACHE_DIR = SIGNALS_DIR / "life_events_cache"

DEFAULT_INPUT = ENRICHED_DIR / "top_leads_enriched.csv"

# Rate limit for clerk portal requests
CLERK_DELAY = 2.0

# ---------------------------------------------------------------------------
# Document type classification
# ---------------------------------------------------------------------------

# Document types that indicate life events (mapped to event category)
EVENT_DOC_TYPES = {
    # Divorce / Family
    "DISSOLUTION": "divorce",
    "DIVORCE": "divorce",
    "FAMILY": "divorce",
    "DOMESTIC": "divorce",
    "MARITAL": "divorce",

    # Probate / Estate
    "PROBATE": "probate",
    "ESTATE": "probate",
    "DEATH": "probate",
    "PERSONAL REP": "probate",
    "LETTERS OF ADMIN": "probate",
    "WILL": "probate",

    # Liens
    "TAX LIEN": "tax_lien",
    "FEDERAL TAX LIEN": "tax_lien",
    "STATE TAX LIEN": "tax_lien",
    "LIEN": "lien",
    "MECHANICS LIEN": "lien",
    "CONSTRUCTION LIEN": "lien",
    "CLAIM OF LIEN": "lien",

    # Judgments
    "JUDGMENT": "judgment",
    "FINAL JUDGMENT": "judgment",
    "DEFAULT JUDGMENT": "judgment",
    "SUMMARY JUDGMENT": "judgment",

    # Pre-foreclosure
    "LIS PENDENS": "lis_pendens",
    "NOTICE OF DEFAULT": "lis_pendens",
    "FORECLOSURE": "lis_pendens",

    # Code violations
    "CODE ENFORCEMENT": "code_violation",
    "CODE VIOLATION": "code_violation",
    "UNSAFE STRUCTURE": "code_violation",

    # Bankruptcy
    "BANKRUPTCY": "bankruptcy",
}

# Urgency levels for each event type
EVENT_URGENCY = {
    "lis_pendens": 5,      # Pre-foreclosure — highest urgency
    "bankruptcy": 5,
    "divorce": 4,          # Major life change
    "probate": 4,          # Estate transition
    "tax_lien": 3,         # Financial stress
    "judgment": 3,
    "lien": 2,
    "code_violation": 2,
}


def classify_document(doc_type: str) -> dict:
    """Classify a document type string into an event category."""
    doc_upper = str(doc_type).upper().strip()

    for keyword, category in EVENT_DOC_TYPES.items():
        if keyword in doc_upper:
            return {
                "category": category,
                "urgency": EVENT_URGENCY.get(category, 1),
            }

    return {"category": "", "urgency": 0}


# ---------------------------------------------------------------------------
# Cache management
# ---------------------------------------------------------------------------

def load_cache(name: str) -> dict:
    cache_path = CACHE_DIR / f"{name}.json"
    if cache_path.exists():
        with open(cache_path, "r") as f:
            return json.load(f)
    return {}


def save_cache(name: str, data: dict):
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_path = CACHE_DIR / f"{name}.json"
    with open(cache_path, "w") as f:
        json.dump(data, f, indent=2)


def make_cache_key(name: str) -> str:
    return re.sub(r"[^a-z0-9]", "_", name.strip().lower())


# ---------------------------------------------------------------------------
# County clerk search (placeholder — depends on script 11 research)
# ---------------------------------------------------------------------------

def search_clerk_records(owner_name: str, county: str, session) -> list:
    """
    Search county clerk official records for a given owner name.
    Returns list of document records found.

    NOTE: This is a placeholder that will be updated once script 11
    county clerk research determines the best scraping approach.
    For now, it returns an empty list and logs the attempt.
    """
    # This will be implemented after county clerk portal research (script 11)
    # For now, we note the search that would be performed
    return []


def search_clerk_by_parcel(parcel_id: str, county: str, session) -> list:
    """Search county clerk by parcel ID for liens/lis pendens."""
    return []


# ---------------------------------------------------------------------------
# Analyze existing data for life event signals
# ---------------------------------------------------------------------------

def check_existing_signals(row: pd.Series) -> list:
    """
    Check for life event signals already present in the lead data
    without needing to scrape clerk records.
    """
    events = []

    # Check refi signals field for relevant indicators
    refi_signals = str(row.get("refi_signals", ""))
    if "lis_pendens" in refi_signals.lower():
        events.append({
            "category": "lis_pendens",
            "urgency": 5,
            "source": "refi_signals",
            "detail": "Lis pendens detected in property data",
        })

    # High equity ratio + long hold could indicate estate/probate
    equity_ratio = 0
    try:
        equity_ratio = float(str(row.get("equity_ratio", 0)))
    except (ValueError, TypeError):
        pass

    # Check for very old purchases (possible estate situations)
    days_since = 0
    try:
        days_since = int(float(str(row.get("days_since_purchase", 0))))
    except (ValueError, TypeError):
        pass

    if equity_ratio > 0.9 and days_since > 7300:  # 20+ years, 90%+ equity
        events.append({
            "category": "possible_estate",
            "urgency": 2,
            "source": "derived",
            "detail": f"Very long hold ({days_since // 365}yr) with {equity_ratio*100:.0f}% equity — possible estate/inheritance",
        })

    return events


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Life event detection (Step 16)")
    parser.add_argument("--input", type=str, default=str(DEFAULT_INPUT),
                        help=f"Input CSV (default: {DEFAULT_INPUT})")
    parser.add_argument("--skip-clerk", action="store_true",
                        help="Skip county clerk searches (use only existing data signals)")
    args = parser.parse_args()

    SIGNALS_DIR.mkdir(parents=True, exist_ok=True)
    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    # Load leads
    input_path = Path(args.input)
    if not input_path.exists():
        for alt in [ENRICHED_DIR / "apollo_results.csv", ENRICHED_DIR / "merged_enriched.csv"]:
            if alt.exists():
                input_path = alt
                break
        else:
            print(f"\n  ERROR: Input file not found: {args.input}")
            return

    print(f"\n  Loading leads: {input_path}")
    df = pd.read_csv(input_path, dtype=str, low_memory=False)
    print(f"  Records: {len(df)}")

    # Load cache
    cache = load_cache("life_events_master")

    # Event columns
    event_cols = [
        "life_event_count", "life_event_types", "life_event_urgency_max",
        "life_event_details", "has_lis_pendens", "has_liens",
        "has_divorce", "has_probate", "life_event_score",
    ]
    for col in event_cols:
        df[col] = ""

    # ---------------------------------------------------------------------------
    # Process each lead
    # ---------------------------------------------------------------------------
    print("\n  Scanning for life event signals...")

    leads_with_events = 0
    total_events = 0

    for idx, row in df.iterrows():
        owner = str(row.get("OWN_NAME", "")).strip()
        resolved = str(row.get("resolved_person", "")).strip()
        if resolved.upper() in ("NAN", "NONE", ""):
            resolved = ""

        search_name = resolved or owner
        cache_key = make_cache_key(search_name)

        # Check cache
        if cache_key in cache:
            events = cache[cache_key]
        else:
            events = []

            # Check signals already in the data
            existing = check_existing_signals(row)
            events.extend(existing)

            # County clerk search (when implemented)
            if not args.skip_clerk and HAS_REQUESTS and HAS_BS4:
                # Placeholder — will be filled after script 11 is built
                # clerk_events = search_clerk_records(search_name, county, session)
                # events.extend(clerk_events)
                pass

            cache[cache_key] = events

        # Populate columns
        if events:
            leads_with_events += 1
            total_events += len(events)

            categories = set(e["category"] for e in events)
            max_urgency = max(e["urgency"] for e in events)
            details = "; ".join(e.get("detail", e["category"]) for e in events)

            df.at[idx, "life_event_count"] = str(len(events))
            df.at[idx, "life_event_types"] = ", ".join(sorted(categories))
            df.at[idx, "life_event_urgency_max"] = str(max_urgency)
            df.at[idx, "life_event_details"] = details
            df.at[idx, "has_lis_pendens"] = str("lis_pendens" in categories)
            df.at[idx, "has_liens"] = str(any(c in categories for c in ("lien", "tax_lien")))
            df.at[idx, "has_divorce"] = str("divorce" in categories)
            df.at[idx, "has_probate"] = str(any(c in categories for c in ("probate", "possible_estate")))

            # Score: 0-15 based on urgency and count
            score = min(max_urgency * 2 + len(events), 15)
            df.at[idx, "life_event_score"] = str(score)

            print(f"  [{idx+1}/{len(df)}] {owner[:40]} — {', '.join(sorted(categories))} (urgency {max_urgency})")
        else:
            df.at[idx, "life_event_count"] = "0"
            df.at[idx, "life_event_urgency_max"] = "0"
            df.at[idx, "life_event_score"] = "0"

    # Save cache
    save_cache("life_events_master", cache)

    # Save output
    output_path = SIGNALS_DIR / "life_events.csv"
    df.to_csv(output_path, index=False)

    # Summary
    print()
    print("=" * 60)
    print("  LIFE EVENT DETECTION RESULTS")
    print("=" * 60)
    print(f"  Total leads:          {len(df)}")
    print(f"  Leads with events:    {leads_with_events}")
    print(f"  Total events found:   {total_events}")
    print()
    if not args.skip_clerk:
        print("  NOTE: County clerk search not yet implemented.")
        print("  Currently using derived signals from existing data only.")
        print("  Full life event detection requires script 11 (county clerk).")
    print()
    print(f"  Output: {output_path}")
    print()


if __name__ == "__main__":
    main()
