"""
Step 4c: SunBiz LLC Resolution via Selenium
=============================================

Same goal as 04_sunbiz_llc_resolver.py but uses Selenium (real Chrome browser)
to bypass Cloudflare blocking that prevents requests-based scraping.

For every LLC/entity-owned property in the pilot 500, this script:
  1. Opens SunBiz search in a headless Chrome browser
  2. Searches for the entity name
  3. Clicks the detail page
  4. Extracts officers, registered agent, filing info
  5. Determines the most likely human owner

Caches all results so it's safe to interrupt and resume.

Usage:
    python scrape/scripts/04c_sunbiz_selenium.py
    python scrape/scripts/04c_sunbiz_selenium.py --input scrape/data/enriched/pilot_500.csv
    python scrape/scripts/04c_sunbiz_selenium.py --max-lookups 50
    python scrape/scripts/04c_sunbiz_selenium.py --headed   # show browser window
"""

import argparse
import json
import re
import sys
import time
from pathlib import Path

import pandas as pd

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import (
        TimeoutException, NoSuchElementException, WebDriverException
    )
except ImportError:
    print("ERROR: Selenium required. Install: pip install selenium")
    sys.exit(1)

try:
    from bs4 import BeautifulSoup
except ImportError:
    print("ERROR: BeautifulSoup required. Install: pip install beautifulsoup4")
    sys.exit(1)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent
ENRICHED_DIR = PROJECT_DIR / "data" / "enriched"
FILTERED_DIR = PROJECT_DIR / "data" / "filtered"
CACHE_DIR = PROJECT_DIR / "data" / "raw" / "sunbiz_cache"
DEFAULT_INPUT = ENRICHED_DIR / "pilot_500.csv"
OUTPUT_CSV = FILTERED_DIR / "pilot_llc_resolved.csv"

# SunBiz config
SUNBIZ_SEARCH_URL = "https://search.sunbiz.org/Inquiry/CorporationSearch/ByName"
SUNBIZ_BASE = "https://search.sunbiz.org"
REQUEST_DELAY = 3.0
SAVE_EVERY = 25

# Titles that indicate the actual owner/decision-maker
PRIORITY_TITLES = [
    "MGR", "MGRM", "MANAGER", "MANAGING MEMBER", "MEMBER",
    "PRESIDENT", "PRES", "CEO", "OWNER", "PRINCIPAL",
]

# Registered agent service companies (not real owners)
AGENT_SERVICE_KEYWORDS = [
    " LLC", " INC", " CORP", " SERVICE", " AGENT", " REGISTERED",
    " SOLUTIONS", " FILING", " STATUTORY",
]


# ---------------------------------------------------------------------------
# Cache
# ---------------------------------------------------------------------------

def load_cache() -> dict:
    cache_file = CACHE_DIR / "sunbiz_selenium_cache.json"
    if cache_file.exists():
        with open(cache_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_cache(cache: dict):
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_file = CACHE_DIR / "sunbiz_selenium_cache.json"
    with open(cache_file, "w", encoding="utf-8") as f:
        json.dump(cache, f, indent=2, ensure_ascii=False)


# ---------------------------------------------------------------------------
# Parse a SunBiz detail page (reuses logic from 04_sunbiz_llc_resolver.py)
# ---------------------------------------------------------------------------

def parse_detail_page(html: str, entity_name: str) -> dict:
    """Parse a SunBiz entity detail page and extract owner info."""
    result = {
        "entity_name_searched": entity_name,
        "registered_agent_name": "",
        "registered_agent_address": "",
        "officer_names": "",
        "principal_address": "",
        "mailing_address": "",
        "status": "",
        "filing_date": "",
        "entity_number": "",
        "resolved_person": "",
    }

    soup = BeautifulSoup(html, "html.parser")
    sections = soup.find_all("div", class_="detailSection")
    officers = []

    for section in sections:
        section_text = section.get_text(separator="\n", strip=True)
        lines = [l.strip() for l in section_text.split("\n") if l.strip()]
        if not lines:
            continue

        header = lines[0]

        if "Filing Information" in header:
            for i, line in enumerate(lines):
                if "Document Number" in line and i + 1 < len(lines):
                    result["entity_number"] = lines[i + 1]
                elif "Status" in line and "PDA" not in line and i + 1 < len(lines):
                    result["status"] = lines[i + 1]
                elif "Date Filed" in line and i + 1 < len(lines):
                    result["filing_date"] = lines[i + 1]

        elif "Principal Address" in header:
            addr_lines = [l for l in lines[1:] if not l.startswith("Changed:")]
            if addr_lines:
                result["principal_address"] = ", ".join(addr_lines)

        elif "Mailing Address" in header:
            addr_lines = [l for l in lines[1:] if not l.startswith("Changed:")]
            if addr_lines:
                result["mailing_address"] = ", ".join(addr_lines)

        elif "Registered Agent" in header:
            agent_lines = [
                l for l in lines[1:]
                if not l.startswith("Name Changed:") and not l.startswith("Address Changed:")
            ]
            if agent_lines:
                result["registered_agent_name"] = agent_lines[0]
            if len(agent_lines) > 1:
                result["registered_agent_address"] = ", ".join(agent_lines[1:])

        elif "Officer/Director" in header or "Authorized Person" in header:
            i = 1
            while i < len(lines):
                line = lines[i]
                if line == "Name & Address":
                    i += 1
                    continue
                if line.startswith("Title "):
                    title_val = line.replace("Title ", "").strip()
                    officer = {"title": title_val, "name": "", "address": ""}
                    if i + 1 < len(lines) and not lines[i + 1].startswith("Title "):
                        officer["name"] = lines[i + 1]
                        i += 1
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

    if officers:
        result["officer_names"] = "; ".join(
            f"{o['name']} ({o['title']})" for o in officers if o.get("name")
        )

    # Determine the most likely human owner
    for officer in officers:
        if officer.get("title", "").upper() in PRIORITY_TITLES and officer.get("name"):
            result["resolved_person"] = officer["name"]
            break

    if not result["resolved_person"] and officers:
        for officer in officers:
            if officer.get("name"):
                result["resolved_person"] = officer["name"]
                break

    if not result["resolved_person"] and result["registered_agent_name"]:
        agent = result["registered_agent_name"].upper()
        if not any(kw in agent for kw in AGENT_SERVICE_KEYWORDS):
            result["resolved_person"] = result["registered_agent_name"]

    return result


# ---------------------------------------------------------------------------
# Selenium-based SunBiz search
# ---------------------------------------------------------------------------

def create_driver(headed: bool = False) -> webdriver.Chrome:
    """Create a Chrome WebDriver instance."""
    opts = Options()
    if not headed:
        opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-blink-features=AutomationControlled")
    opts.add_argument("--window-size=1920,1080")
    opts.add_argument(
        "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
    # Suppress logging
    opts.add_experimental_option("excludeSwitches", ["enable-logging"])

    driver = webdriver.Chrome(options=opts)
    driver.set_page_load_timeout(30)

    # Remove webdriver flag
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    })

    return driver


def search_entity_selenium(driver: webdriver.Chrome, entity_name: str) -> dict:
    """
    Search SunBiz for an entity using Selenium and extract owner details.
    """
    # Clean name for search
    search_name = entity_name.strip()
    for suffix in [" LLC", " L.L.C.", " L.L.C", " INC", " INC.",
                   " CORP", " CORP.", " LP", " LTD", " LTD.",
                   " LLLP", " L.P."]:
        if search_name.upper().endswith(suffix):
            search_name = search_name[: len(search_name) - len(suffix)].strip()

    try:
        # Navigate to search page
        driver.get(SUNBIZ_SEARCH_URL)
        time.sleep(1)

        # Find and fill the search box
        search_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "SearchTerm"))
        )
        search_input.clear()
        search_input.send_keys(search_name)

        # Click search button
        submit_btn = driver.find_element(By.CSS_SELECTOR, "input[type='submit'][value='Search Now']")
        submit_btn.click()

        # Wait for results
        time.sleep(2)

        # Check for results
        page_source = driver.page_source

        # Look for Cloudflare challenge
        if "cf-browser-verification" in page_source or "Checking your browser" in page_source:
            print("    Cloudflare challenge detected, waiting...")
            time.sleep(10)
            page_source = driver.page_source

        # Find result links
        soup = BeautifulSoup(page_source, "html.parser")
        links = soup.find_all("a", href=re.compile(r"SearchResultDetail"))

        if not links:
            return {
                "entity_name_searched": entity_name,
                "status": "NO RESULTS",
                "resolved_person": "",
                "registered_agent_name": "",
                "registered_agent_address": "",
                "officer_names": "",
                "principal_address": "",
                "mailing_address": "",
                "filing_date": "",
                "entity_number": "",
            }

        # Find best match (prefer exact name match)
        detail_href = None
        entity_upper = entity_name.upper().strip()
        for link in links:
            if link.get_text(strip=True).upper() == entity_upper:
                detail_href = link["href"]
                break
        if not detail_href:
            # Also try matching without suffix
            for link in links:
                link_text = link.get_text(strip=True).upper()
                if search_name.upper() in link_text:
                    detail_href = link["href"]
                    break
        if not detail_href:
            detail_href = links[0]["href"]

        detail_url = SUNBIZ_BASE + detail_href

        # Navigate to detail page
        time.sleep(1)
        driver.get(detail_url)
        time.sleep(2)

        # Parse the detail page
        return parse_detail_page(driver.page_source, entity_name)

    except TimeoutException:
        return {
            "entity_name_searched": entity_name,
            "status": "TIMEOUT",
            "resolved_person": "",
            "registered_agent_name": "",
            "registered_agent_address": "",
            "officer_names": "",
            "principal_address": "",
            "mailing_address": "",
            "filing_date": "",
            "entity_number": "",
        }
    except Exception as e:
        return {
            "entity_name_searched": entity_name,
            "status": f"ERROR: {str(e)[:100]}",
            "resolved_person": "",
            "registered_agent_name": "",
            "registered_agent_address": "",
            "officer_names": "",
            "principal_address": "",
            "mailing_address": "",
            "filing_date": "",
            "entity_number": "",
        }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="SunBiz LLC Resolution via Selenium")
    parser.add_argument("--input", type=str, default=str(DEFAULT_INPUT),
                        help=f"Input CSV (default: {DEFAULT_INPUT})")
    parser.add_argument("--max-lookups", type=int, default=500,
                        help="Max entities to look up (default: 500)")
    parser.add_argument("--headed", action="store_true",
                        help="Show browser window (not headless)")
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"ERROR: Input file not found: {input_path}")
        sys.exit(1)

    print()
    print("=" * 60)
    print("  SUNBIZ LLC RESOLUTION (Selenium)")
    print("=" * 60)

    # Load leads
    df = pd.read_csv(input_path, dtype=str, low_memory=False)
    print(f"\n  Loaded {len(df)} leads from {input_path.name}")

    # Filter to entity-owned leads
    entity_mask = df["is_entity"].astype(str).str.lower().isin(["true", "1", "yes"])
    entity_leads = df[entity_mask].copy()
    print(f"  Entity-owned leads: {len(entity_leads)}")

    # Check which already have a resolved person
    already_resolved = entity_leads[
        entity_leads["resolved_person"].fillna("").astype(str).str.strip().str.lower()
        .apply(lambda x: x not in ("", "nan", "none"))
    ]
    print(f"  Already resolved:   {len(already_resolved)}")

    # Get unique entity names needing resolution
    needs_resolution = entity_leads[
        ~entity_leads.index.isin(already_resolved.index)
    ]
    unique_entities = needs_resolution["OWN_NAME"].unique().tolist()

    # Load cache
    cache = load_cache()
    cached_count = sum(1 for e in unique_entities if e in cache)
    to_lookup = [e for e in unique_entities if e not in cache]

    print(f"  Unique entities:    {len(unique_entities)}")
    print(f"  Already cached:     {cached_count}")
    print(f"  Need lookup:        {len(to_lookup)}")

    if not to_lookup:
        print("\n  All entities already resolved or cached!")
    else:
        # Limit lookups
        if len(to_lookup) > args.max_lookups:
            print(f"  Limiting to {args.max_lookups} lookups (use --max-lookups to change)")
            to_lookup = to_lookup[:args.max_lookups]

        est_time = len(to_lookup) * (REQUEST_DELAY + 4)  # ~7s per lookup
        print(f"\n  Looking up {len(to_lookup)} entities...")
        print(f"  Estimated time: ~{est_time/60:.0f} minutes")

        # Create browser
        print("\n  Starting Chrome browser...")
        driver = create_driver(headed=args.headed)

        try:
            # Initial page load to establish session
            driver.get(SUNBIZ_SEARCH_URL)
            time.sleep(3)

            # Check for Cloudflare
            if "Checking your browser" in driver.page_source:
                print("  Waiting for Cloudflare challenge...")
                time.sleep(10)

            if "Search" not in driver.page_source:
                print("  WARNING: SunBiz may be blocking. Trying to proceed...")

            resolved_count = 0
            error_count = 0
            consecutive_errors = 0

            for i, entity_name in enumerate(to_lookup):
                result = search_entity_selenium(driver, entity_name)
                cache[entity_name] = result

                person = result.get("resolved_person", "")
                status = result.get("status", "")

                if person:
                    resolved_count += 1
                    consecutive_errors = 0
                    print(f"  [{i+1}/{len(to_lookup)}] {entity_name[:40]:<40} -> {person}")
                elif "ERROR" in status or "TIMEOUT" in status:
                    error_count += 1
                    consecutive_errors += 1
                    print(f"  [{i+1}/{len(to_lookup)}] {entity_name[:40]:<40} -> {status}")
                else:
                    consecutive_errors = 0
                    officers = result.get("officer_names", "")
                    if officers:
                        print(f"  [{i+1}/{len(to_lookup)}] {entity_name[:40]:<40} -> officers: {officers[:60]}")
                    else:
                        print(f"  [{i+1}/{len(to_lookup)}] {entity_name[:40]:<40} -> {status or 'no match'}")

                # Save cache periodically
                if (i + 1) % SAVE_EVERY == 0:
                    save_cache(cache)
                    print(f"    [saved cache: {len(cache)} entries]")

                # Back off on consecutive errors
                if consecutive_errors >= 5:
                    print(f"\n  5 consecutive errors. Waiting 30s before retrying...")
                    time.sleep(30)
                    # Refresh the browser
                    driver.get(SUNBIZ_SEARCH_URL)
                    time.sleep(5)
                    consecutive_errors = 0

                time.sleep(REQUEST_DELAY)

            print(f"\n  Lookups complete: {resolved_count} resolved, {error_count} errors")

        finally:
            driver.quit()
            save_cache(cache)
            print(f"  Cache saved: {len(cache)} entries")

    # -----------------------------------------------------------------------
    # Merge results back into leads
    # -----------------------------------------------------------------------
    print()
    print("-" * 60)
    print("  MERGING RESULTS")
    print("-" * 60)

    merge_cols = [
        "resolved_person", "registered_agent_name", "registered_agent_address",
        "officer_names", "filing_date", "status",
    ]

    # For each entity lead, pull from cache
    for col in merge_cols:
        if col not in df.columns:
            df[col] = ""

    resolved_total = 0
    for idx, row in df.iterrows():
        own_name = str(row.get("OWN_NAME", "")).strip()
        if own_name in cache:
            cached_result = cache[own_name]
            for col in merge_cols:
                val = cached_result.get(col, "")
                existing = str(row.get(col, "")).strip()
                if val and existing.lower() in ("", "nan", "none"):
                    df.at[idx, col] = val
            if cached_result.get("resolved_person"):
                resolved_total += 1

    # Rename status column to avoid conflict
    if "sunbiz_status" not in df.columns:
        df.rename(columns={"status": "sunbiz_status"}, inplace=True, errors="ignore")

    # Save output
    FILTERED_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT_CSV, index=False)

    # Summary
    print()
    print("=" * 60)
    print("  SUNBIZ RESOLUTION RESULTS")
    print("=" * 60)

    entity_count = entity_mask.sum()
    resolved_in_output = df["resolved_person"].fillna("").astype(str).str.strip()
    resolved_in_output = resolved_in_output[~resolved_in_output.isin(["", "nan", "none"])]

    print(f"  Total leads:          {len(df)}")
    print(f"  Entity-owned:         {entity_count}")
    print(f"  Resolved to person:   {len(resolved_in_output)}")
    print(f"  Resolution rate:      {len(resolved_in_output)/entity_count*100:.0f}%" if entity_count else "  N/A")
    print(f"\n  Output: {OUTPUT_CSV}")
    print(f"  Cache:  {CACHE_DIR / 'sunbiz_selenium_cache.json'}")

    print("\n  NEXT STEPS:")
    print("    1. Re-run Apollo enrichment with resolved names")
    print("    2. Run: python scrape/scripts/merge_pilot_enrichment.py")
    print()


if __name__ == "__main__":
    main()
