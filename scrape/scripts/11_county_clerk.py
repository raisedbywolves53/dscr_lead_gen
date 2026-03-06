"""
Step 11: County Clerk Mortgage & Lien Scraping
================================================

Searches Palm Beach and Broward county clerk official records to extract
mortgage data, liens, and lis pendens for each lead's properties.

This is the biggest intelligence unlock in the pipeline — it gives us:
  - Current lender for each property
  - Loan amount and origination date
  - Mortgage type (conventional, hard money, etc.)
  - Lien recordings, lis pendens (pre-foreclosure)
  - Satisfaction of mortgage (loan paid off = equity)

IMPORTANT: Both portals require a real browser:
  - Palm Beach (erec.mypalmbeachclerk.com): reCAPTCHA on every search
  - Broward (officialrecords.broward.org): Cloudflare challenge

Requirements:
    pip install playwright
    playwright install chromium

Usage:
    python scripts/11_county_clerk.py
    python scripts/11_county_clerk.py --county palm_beach --limit 5
    python scripts/11_county_clerk.py --dry-run

Portal Details:
    Palm Beach: "Landmark Web" system at erec.mypalmbeachclerk.com
      - Search types: Name, ParcelId, DocumentType, BookPage, etc.
      - POST to /Search/{SearchType} with AJAX
      - Requires: session cookie + disclaimer acceptance + reCAPTCHA
      - Doc type codes: MTG=50, D=25, LN=23, LP=20, ASG=31, SAT=40, JUD=36

    Broward: "AcclaimWeb" at officialrecords.broward.org
      - Behind Cloudflare challenge
      - Requires: browser to solve Cloudflare JS challenge
"""

import argparse
import json
import os
import re
import time
from datetime import datetime
from pathlib import Path

import pandas as pd

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
FINANCING_DIR = PROJECT_DIR / "data" / "financing"
CACHE_DIR = FINANCING_DIR / "clerk_cache"

DEFAULT_INPUT = ENRICHED_DIR / "top_leads_enriched.csv"

# Rate limit: 2 seconds between searches
SEARCH_DELAY = 2.0

# Document type codes for Palm Beach (Landmark Web)
PB_DOC_TYPES = {
    "MTG": 50,        # Mortgage
    "MTG_EXE": 11,    # Mortgage Executed
    "MTG_INT": 13,    # Mortgage Interest Exempt
    "MTG_REV": 329,   # Reverse Mortgage
    "D": 25,          # Deed
    "D_SMP": 21,      # Deed Simple
    "D_TR": 12,       # Deed of Trust
    "ASG": 31,        # Assignment (of mortgage)
    "SAT": 40,        # Satisfaction (mortgage paid off)
    "LN": 23,         # Lien
    "LN_TX": 66,      # Tax Lien
    "LN_HSP": 58,     # Hospital Lien
    "LP": 20,         # Lis Pendens (pre-foreclosure)
    "JUD": 36,        # Judgment
    "JUD_C": 56,      # Judgment - Civil
    "REL": 43,        # Release
    "DM": 5,          # Dissolution of Marriage
    "PRO": 8,         # Probate
}

# Relevant doc types for financing analysis
FINANCING_DOC_TYPES = [50, 11, 13, 329, 31, 40, 23, 66, 20, 36, 56, 43]

# Hard money lender keywords (from enrichment_sources.json)
HARD_MONEY_KEYWORDS = [
    "HARD MONEY", "BRIDGE", "FIX AND FLIP", "REHAB",
    "KIAVI", "LIMA ONE", "CIVIC", "ANCHOR LOANS", "GENESIS",
    "RCLENDING", "GROUNDFLOOR", "FUND THAT FLIP",
    "LENDING HOME", "VISIO", "NEW SILVER", "EASY STREET",
    "PATCH OF LAND", "COREVEST", "RENOVO", "TEMPLE VIEW",
    "AMERICAN HERITAGE", "VELOCITY", "TOORAK",
]

PRIVATE_LENDER_KEYWORDS = [
    "PRIVATE", "INDIVIDUAL", "TRUST", "FAMILY",
    "INVESTMENTS LLC", "CAPITAL LLC", "FUND LLC",
]

CREDIT_UNION_KEYWORDS = [
    "CREDIT UNION", "FCU", "CU ", "FEDERAL CREDIT",
]


# ---------------------------------------------------------------------------
# Cache
# ---------------------------------------------------------------------------

def load_cache(name: str) -> dict:
    cache_path = CACHE_DIR / f"{name}.json"
    if cache_path.exists():
        with open(cache_path, "r") as f:
            return json.load(f)
    return {}


def save_cache(name: str, data: dict):
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    with open(CACHE_DIR / f"{name}.json", "w") as f:
        json.dump(data, f, indent=2, default=str)


# ---------------------------------------------------------------------------
# Lender classification
# ---------------------------------------------------------------------------

def classify_lender(lender_name: str) -> str:
    """Classify a lender as bank, credit_union, hard_money, private, or unknown."""
    if not lender_name:
        return "unknown"

    upper = lender_name.upper()

    for kw in HARD_MONEY_KEYWORDS:
        if kw in upper:
            return "hard_money"

    for kw in CREDIT_UNION_KEYWORDS:
        if kw in upper:
            return "credit_union"

    for kw in PRIVATE_LENDER_KEYWORDS:
        if kw in upper:
            return "private"

    # Common bank indicators
    bank_keywords = ["BANK", "NATIONAL ASSOCIATION", "N.A.", "MORTGAGE CORP",
                     "MORTGAGE CO", "LENDING", "FINANCIAL", "SAVINGS",
                     "WELLS FARGO", "CHASE", "JPMORGAN", "CITIBANK",
                     "REGIONS", "TRUIST", "PNC", "US BANK", "TD BANK"]
    for kw in bank_keywords:
        if kw in upper:
            return "bank"

    return "unknown"


def estimate_balance(original_amount: float, origination_date: str,
                     rate: float = 0.065, term_years: int = 30) -> float:
    """Estimate remaining mortgage balance using simple amortization."""
    if not original_amount or original_amount <= 0:
        return 0

    try:
        orig_date = datetime.strptime(origination_date, "%m/%d/%Y")
    except (ValueError, TypeError):
        try:
            orig_date = datetime.strptime(origination_date, "%Y-%m-%d")
        except (ValueError, TypeError):
            return original_amount * 0.85  # rough estimate

    months_elapsed = (datetime.now() - orig_date).days / 30.44
    if months_elapsed < 0:
        return original_amount

    monthly_rate = rate / 12
    total_payments = term_years * 12

    if monthly_rate == 0:
        return max(0, original_amount * (1 - months_elapsed / total_payments))

    # Monthly payment
    payment = original_amount * (monthly_rate * (1 + monthly_rate) ** total_payments) / \
              ((1 + monthly_rate) ** total_payments - 1)

    # Remaining balance
    balance = original_amount * (1 + monthly_rate) ** months_elapsed - \
              payment * ((1 + monthly_rate) ** months_elapsed - 1) / monthly_rate

    return max(0, balance)


# ---------------------------------------------------------------------------
# Parse search results (Palm Beach Landmark Web format)
# ---------------------------------------------------------------------------

def parse_pb_results(html: str) -> list:
    """
    Parse search results HTML from Palm Beach clerk portal.
    Returns list of document dicts.
    """
    documents = []

    # Results are in a table with rows
    # Each row typically has: Record Date, Doc Type, Book/Page, Party Names, Amount
    rows = re.findall(r'<tr[^>]*>(.*?)</tr>', html, re.DOTALL)

    for row in rows:
        cells = re.findall(r'<td[^>]*>(.*?)</td>', row, re.DOTALL)
        if len(cells) < 3:
            continue

        # Clean cell contents
        cells = [re.sub(r'<[^>]+>', '', c).strip() for c in cells]

        doc = {
            "raw_cells": cells,
            "record_date": "",
            "doc_type": "",
            "book_page": "",
            "parties": "",
            "consideration": "",
        }

        # Assign based on typical Landmark Web column order
        # (exact order depends on the portal — may need adjustment)
        if len(cells) >= 5:
            doc["record_date"] = cells[0]
            doc["doc_type"] = cells[1]
            doc["book_page"] = cells[2]
            doc["parties"] = cells[3]
            doc["consideration"] = cells[4]

        documents.append(doc)

    return documents


# ---------------------------------------------------------------------------
# Playwright-based search (Palm Beach)
# ---------------------------------------------------------------------------

async def search_pb_clerk_playwright(owner_name: str, page) -> list:
    """
    Search Palm Beach clerk using Playwright browser.
    Returns list of document records.
    """
    results = []

    try:
        # Navigate to search page
        await page.goto("https://erec.mypalmbeachclerk.com/")
        await page.wait_for_load_state("networkidle")

        # Accept disclaimer if present
        accept_btn = page.locator("#idAcceptYes")
        if await accept_btn.is_visible():
            await accept_btn.click()
            await page.wait_for_load_state("networkidle")

        # Wait for search form
        await page.wait_for_selector("#name-Name", timeout=10000)

        # Enter name
        await page.fill("#name-Name", owner_name)

        # Select mortgage + lien document types
        # Check relevant doc type checkboxes
        for dt_id in FINANCING_DOC_TYPES:
            checkbox = page.locator(f"#dt-Name-{dt_id}")
            if await checkbox.is_visible():
                await checkbox.check()

        # Click submit
        submit = page.locator("#submit-Name, .nameSearchSubmit")
        await submit.click()

        # Wait for results or CAPTCHA
        # reCAPTCHA may appear — user needs to solve it manually in headed mode
        await page.wait_for_selector("#searchResults, .g-recaptcha", timeout=30000)

        # Check if CAPTCHA appeared
        captcha = page.locator(".g-recaptcha")
        if await captcha.is_visible():
            print("    reCAPTCHA appeared — solve it in the browser window...")
            # Wait for user to solve CAPTCHA (up to 120 seconds)
            await page.wait_for_selector("#searchResults table", timeout=120000)

        # Get results HTML
        results_html = await page.locator("#searchResults").inner_html()
        results = parse_pb_results(results_html)

    except Exception as e:
        print(f"    Error: {e}")

    return results


# ---------------------------------------------------------------------------
# Synchronous wrapper for when Playwright isn't available
# ---------------------------------------------------------------------------

def search_clerk_manual_instructions(owner_name: str, county: str):
    """Print instructions for manual clerk record search."""
    if county == "palm_beach":
        print(f"\n    MANUAL SEARCH for: {owner_name}")
        print(f"    1. Open: https://erec.mypalmbeachclerk.com/")
        print(f"    2. Accept disclaimer")
        print(f"    3. Enter name: {owner_name}")
        print(f"    4. Check: MTG, ASG, SAT, LN, LP, JUD")
        print(f"    5. Submit and record results")
    elif county == "broward":
        print(f"\n    MANUAL SEARCH for: {owner_name}")
        print(f"    1. Open: https://officialrecords.broward.org/AcclaimWeb/")
        print(f"    2. Search by name: {owner_name}")
        print(f"    3. Filter to mortgage/lien document types")
        print(f"    4. Record results")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="County clerk mortgage/lien scraping (Step 11)")
    parser.add_argument("--input", type=str, default=str(DEFAULT_INPUT))
    parser.add_argument("--county", type=str, default="palm_beach",
                        choices=["palm_beach", "broward", "both"])
    parser.add_argument("--limit", type=int, default=0,
                        help="Limit number of leads to search")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show what would be searched without running browser")
    parser.add_argument("--headed", action="store_true",
                        help="Run browser in headed mode (visible) for CAPTCHA solving")
    parser.add_argument("--manual", action="store_true",
                        help="Print manual search instructions instead of using browser")
    args = parser.parse_args()

    FINANCING_DIR.mkdir(parents=True, exist_ok=True)
    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    # Load leads
    input_path = Path(args.input)
    if not input_path.exists():
        for alt in [ENRICHED_DIR / "apollo_results.csv", ENRICHED_DIR / "merged_enriched.csv"]:
            if alt.exists():
                input_path = alt
                break
        else:
            print(f"\n  ERROR: Input not found: {args.input}")
            return

    print(f"\n  Loading leads: {input_path}")
    df = pd.read_csv(input_path, dtype=str, low_memory=False)
    print(f"  Records: {len(df)}")

    if args.limit > 0:
        df = df.head(args.limit)
        print(f"  Limited to: {len(df)}")

    # Build search list
    searches = []
    for _, row in df.iterrows():
        owner = str(row.get("OWN_NAME", "")).strip()
        if not owner or owner.upper() in ("NAN", "NONE"):
            continue
        searches.append({"owner": owner, "row": row})

    cache = load_cache("clerk_results")
    cached = sum(1 for s in searches if s["owner"] in cache)
    to_search = [s for s in searches if s["owner"] not in cache]

    print(f"\n  Leads to search:  {len(searches)}")
    print(f"  Already cached:   {cached}")
    print(f"  Need search:      {len(to_search)}")

    if args.dry_run:
        print("\n  DRY RUN — would search:")
        for s in to_search[:10]:
            print(f"    {s['owner']}")
        if len(to_search) > 10:
            print(f"    ... and {len(to_search) - 10} more")
        est_time = len(to_search) * (SEARCH_DELAY + 5)
        print(f"\n  Estimated time: {est_time:.0f}s ({est_time/60:.1f} min)")
        print(f"  NOTE: reCAPTCHA solving adds ~10-30s per search")
        return

    if args.manual:
        print("\n  MANUAL MODE — printing search instructions:")
        counties = ["palm_beach", "broward"] if args.county == "both" else [args.county]
        for s in to_search:
            for county in counties:
                search_clerk_manual_instructions(s["owner"], county)
        return

    # Try Playwright
    try:
        from playwright.async_api import async_playwright
        import asyncio
        HAS_PLAYWRIGHT = True
    except ImportError:
        HAS_PLAYWRIGHT = False
        print("\n  WARNING: Playwright not installed.")
        print("  Install with: pip install playwright && playwright install chromium")
        print("  Or use --manual flag for manual search instructions.")
        print("  Or use --dry-run to see what would be searched.")
        return

    async def run_searches():
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=not args.headed)
            context = await browser.new_context()
            page = await context.new_page()

            success = 0
            errors = 0

            for i, search in enumerate(to_search):
                owner = search["owner"]
                print(f"\n  [{i+1}/{len(to_search)}] Searching: {owner[:50]}")

                try:
                    results = await search_pb_clerk_playwright(owner, page)
                    cache[owner] = results
                    save_cache("clerk_results", cache)

                    if results:
                        success += 1
                        # Classify documents
                        mortgages = [r for r in results if "MTG" in str(r.get("doc_type", "")).upper()]
                        liens = [r for r in results if "LN" in str(r.get("doc_type", "")).upper()]
                        lp = [r for r in results if "LP" in str(r.get("doc_type", "")).upper()]
                        print(f"    Found: {len(results)} docs ({len(mortgages)} mortgages, {len(liens)} liens, {len(lp)} lis pendens)")
                    else:
                        print(f"    No results found")

                except Exception as e:
                    errors += 1
                    print(f"    ERROR: {e}")

                time.sleep(SEARCH_DELAY)

            await browser.close()
            print(f"\n  Completed: {success} found, {errors} errors")

    asyncio.run(run_searches())

    # Build output DataFrame
    print("\n  Building financing output...")
    rows = []
    for search in searches:
        owner = search["owner"]
        docs = cache.get(owner, [])

        mortgages = [d for d in docs if "MTG" in str(d.get("doc_type", "")).upper()]
        satisfactions = [d for d in docs if "SAT" in str(d.get("doc_type", "")).upper()]
        liens = [d for d in docs if "LN" in str(d.get("doc_type", "")).upper()]
        lis_pendens = [d for d in docs if "LP" in str(d.get("doc_type", "")).upper()]

        # Extract lender names from mortgage records
        lenders = []
        for m in mortgages:
            parties = str(m.get("parties", ""))
            # Lender is typically the grantee in a mortgage
            lenders.append(parties)

        # Classify lenders
        lender_types = [classify_lender(l) for l in lenders]
        hard_money_count = lender_types.count("hard_money")

        rows.append({
            "OWN_NAME": owner,
            "mortgage_count": len(mortgages),
            "satisfaction_count": len(satisfactions),
            "lien_count": len(liens),
            "lis_pendens_count": len(lis_pendens),
            "total_doc_count": len(docs),
            "lender_names": "; ".join(lenders[:5]),
            "hard_money_count": hard_money_count,
            "lender_types": "; ".join(set(lender_types)),
            "most_recent_mortgage_date": mortgages[0].get("record_date", "") if mortgages else "",
            "most_recent_mortgage_amount": mortgages[0].get("consideration", "") if mortgages else "",
        })

    out_df = pd.DataFrame(rows)
    output_path = FINANCING_DIR / f"{args.county}_mortgages.csv"
    out_df.to_csv(output_path, index=False)

    print()
    print("=" * 60)
    print("  COUNTY CLERK RESULTS")
    print("=" * 60)
    print(f"  Leads searched:    {len(searches)}")
    print(f"  With mortgages:    {sum(1 for r in rows if r['mortgage_count'] > 0)}")
    print(f"  With liens:        {sum(1 for r in rows if r['lien_count'] > 0)}")
    print(f"  With lis pendens:  {sum(1 for r in rows if r['lis_pendens_count'] > 0)}")
    print(f"  Hard money loans:  {sum(r['hard_money_count'] for r in rows)}")
    print()
    print(f"  Output: {output_path}")
    print()


if __name__ == "__main__":
    main()
