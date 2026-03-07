"""
PBC Clerk Portal — Lender Lookup via 2Captcha
==============================================

Searches PBC Clerk of Court (erec.mypalmbeachclerk.com) for mortgage
records to identify lender names for pilot leads.

Uses NameSearch with reCAPTCHA solved via 2Captcha ($0.003/solve).
Each solve returns all documents for a name, filtered to MTG type.

For leads without ATTOM lender data, this fills the gap by finding
the most recent mortgage recording and extracting the lender name.

Input:
    scrape/data/enriched/pilot_500_enriched.csv

Output:
    scrape/data/financing/clerk_lender_results.csv

Usage:
    python scrape/scripts/11_clerk_lender_lookup.py [--max N] [--resume]

Options:
    --max N     Maximum number of leads to look up (default: all without lender)
    --resume    Resume from where we left off (skip already-looked-up names)

Cost: ~$0.003 per lead searched (~$1.10 for 367 leads)
"""

import argparse
import csv
import json
import os
import re
import sys
import time
from pathlib import Path

from curl_cffi import requests as cffi_requests
from dotenv import load_dotenv
from twocaptcha import TwoCaptcha

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent
load_dotenv(PROJECT_DIR.parent / ".env")

BASE = "https://erec.mypalmbeachclerk.com"
SITEKEY = "6LdBHOorAAAAALwRLkAZpnNsfcp7qfFS4YIGIRTU"

CAPTCHA_KEY = os.getenv("TWOCAPTCHA_API_KEY")
INPUT_CSV = PROJECT_DIR / "data" / "enriched" / "pilot_500_enriched.csv"
OUTPUT_CSV = PROJECT_DIR / "data" / "financing" / "clerk_lender_results.csv"
CACHE_DIR = PROJECT_DIR / "data" / "financing" / "clerk_cache"

HEADERS = {
    "X-Requested-With": "XMLHttpRequest",
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
}

# Hard money lender keywords
HARD_MONEY_KEYWORDS = [
    "kiavi", "lima one", "roc capital", "new silver", "civic financial",
    "visio", "easy street", "relay", "anchor loans", "fund that flip",
    "groundfloor", "haus lending", "investor's edge", "corevest",
    "american heritage", "capital express", "genesis capital",
    "temple view", "longitude", "lendingone", "rcn capital",
    "toorak capital", "velocity mortgage", "private money",
    "hard money", "bridge loan", "fix and flip",
]


def strip_html(s):
    """Remove HTML tags and control prefixes."""
    if not s:
        return ""
    s = re.sub(r'^(nobreak_|unclickable_|hidden_|legalfield_)', '', s)
    s = re.sub(r'<[^>]+>', ' ', s)
    return re.sub(r'\s+', ' ', s).strip()


def classify_lender(name):
    """Classify lender as bank, hard_money, credit_union, private, other."""
    if not name:
        return ""
    upper = name.upper()
    for kw in HARD_MONEY_KEYWORDS:
        if kw.upper() in upper:
            return "hard_money"
    if any(k in upper for k in ["CREDIT UNION", "FCU", "FEDERAL CREDIT"]):
        return "credit_union"
    if any(k in upper for k in ["BANK", "WELLS FARGO", "CHASE", "CITI",
                                 "BOA", "JPMORGAN", "US BANK", "PNC",
                                 "TD BANK", "FIFTH THIRD", "REGIONS"]):
        return "bank"
    if any(k in upper for k in ["MORTGAGE", "HOME LOAN", "LENDING",
                                 "FINANCIAL", "CAPITAL", "FUNDING"]):
        return "mortgage_company"
    if any(k in upper for k in ["LLC", "INC", "CORP", "TRUST", "LP"]):
        return "other"
    return "private"


def build_datatables_params(draw=1, start=0, length=100):
    """Build DataTables server-side processing POST parameters."""
    params = {
        "draw": str(draw), "start": str(start), "length": str(length),
        "search[value]": "", "search[regex]": "false",
        "order[0][column]": "0", "order[0][dir]": "asc",
    }
    for i in range(31):
        params[f"columns[{i}][data]"] = str(i)
        params[f"columns[{i}][name]"] = ""
        params[f"columns[{i}][searchable]"] = "true"
        params[f"columns[{i}][orderable]"] = "true" if i > 2 else "false"
        params[f"columns[{i}][search][value]"] = ""
        params[f"columns[{i}][search][regex]"] = "false"
    return params


class ClerkScraper:
    def __init__(self):
        self.session = None
        self.solver = TwoCaptcha(CAPTCHA_KEY)
        self.captcha_count = 0
        self.captcha_cost = 0.0

    def setup_session(self, max_retries=3):
        """Initialize session with disclaimer accepted."""
        for attempt in range(max_retries):
            try:
                self.session = cffi_requests.Session(impersonate="chrome")
                self.session.get(BASE, timeout=30)
                self.session.post(f"{BASE}/Search/SetDisclaimer", timeout=15)
                self.session.get(f"{BASE}/search/index", timeout=15)
                return
            except Exception as e:
                wait = 30 * (attempt + 1)
                print(f"  Session setup failed ({e}), waiting {wait}s...")
                time.sleep(wait)
        raise ConnectionError("Failed to connect after retries")

    def solve_captcha(self):
        """Solve reCAPTCHA via 2Captcha."""
        t0 = time.time()
        result = self.solver.recaptcha(
            sitekey=SITEKEY, url=f"{BASE}/search/index"
        )
        token = result["code"]
        elapsed = time.time() - t0
        self.captcha_count += 1
        self.captcha_cost += 0.003
        return token, elapsed

    def name_search(self, name, token, doc_type="MTG"):
        """Run NameSearch and return parsed records."""
        criteria = {
            "searchLikeType": "0",  # Starts With
            "type": "0",           # Both (direct and reverse)
            "name": name,
            "doctype": doc_type,
            "bookType": "0",
            "beginDate": "",
            "endDate": "",
            "recordCount": "700",
            "exclude": "false",
            "ReturnIndexGroups": "false",
            "townName": "",
            "selectedNamesIds": "",
            "includeNickNames": "false",
            "selectedNames": "",
            "mobileHomesOnly": "false",
            "g-recaptcha-response": token,
        }

        try:
            r = self.session.post(
                f"{BASE}/Search/NameSearch", data=criteria,
                headers={**HEADERS, "Referer": f"{BASE}/search/index"},
                timeout=60,
            )
        except Exception as e:
            print(f"  Request error: {type(e).__name__}")
            return None, 0

        if r.status_code != 200 or "Invalid Captcha" in r.text:
            return None, r.status_code

        # Fetch DataTables results
        all_rows = []
        for page in range(10):  # Max 10 pages = 1000 records
            try:
                dt = build_datatables_params(draw=page+1, start=page*100,
                                             length=100)
                r2 = self.session.post(
                    f"{BASE}/Search/GetSearchResults", data=dt,
                    headers={**HEADERS, "Referer": f"{BASE}/search/index"},
                    timeout=60,
                )
                if r2.status_code != 200:
                    break
                data = r2.json()
                rows = data.get("data", [])
                total = data.get("recordsTotal", 0)
                all_rows.extend(rows)
                if len(all_rows) >= total or not rows:
                    break
            except Exception:
                break

        # Parse into records
        records = []
        for row in all_rows:
            doc_id = ""
            m = re.search(r"eye_(\d+)", row.get("1", ""))
            if m:
                doc_id = m.group(1)

            records.append({
                "doc_id": doc_id,
                "direct_name": strip_html(row.get("5", "")),
                "reverse_name": strip_html(row.get("6", "")),
                "record_date": strip_html(row.get("7", "")),
                "doc_type": strip_html(row.get("9", "")),
                "instrument_num": strip_html(row.get("13", "")),
            })

        return records, 200

    def find_lender(self, name, records):
        """From a list of clerk records, find the most recent lender.

        In PBC Clerk records:
        - Direct Name = grantor (for MTG, this is the borrower)
        - Reverse Name = grantee (for MTG, this is the lender)

        We look for MTG docs where the lead is the direct name (borrower)
        and the reverse name is the lender.

        Only considers mortgages from 2000+ to avoid matching old records
        from unrelated people with the same last name.
        """
        if not records:
            return None

        # Normalize the search name for matching
        name_upper = name.upper().strip()
        # Remove common suffixes for cleaner matching
        for suffix in [" LLC", " INC", " CORP", " LTD", " LP", " LLLP",
                       " TRUST", " TRUSTEE", " ET AL", " ETAL", " H/W",
                       " &", " JR", " SR", " III", " II"]:
            name_upper = name_upper.replace(suffix, "")
        name_upper = re.sub(r'\s+', ' ', name_upper).strip()
        name_parts = set(name_upper.split())
        # Remove single-letter parts (initials that cause false matches)
        name_parts = {p for p in name_parts if len(p) > 1}

        def parse_date(d):
            try:
                parts = d.split("/")
                return int(parts[2]) * 10000 + int(parts[0]) * 100 + int(parts[1])
            except (ValueError, IndexError):
                return 0

        # Filter to MTG docs where lead appears as direct name (borrower)
        mtg_records = []
        for rec in records:
            if rec["doc_type"] not in ("MTG", "MORTGAGE"):
                continue

            # Skip records before 2000 (unlikely to be current mortgage)
            date_val = parse_date(rec["record_date"])
            if date_val < 20000101:
                continue

            direct_upper = rec["direct_name"].upper()
            # Clean direct name too
            for suffix in [" LLC", " INC", " CORP", " LTD", " LP",
                           " LLLP", " TRUST", " TRUSTEE", " ET AL",
                           " H/W", " &", " JR", " SR", " III", " II"]:
                direct_upper = direct_upper.replace(suffix, "")
            direct_upper = re.sub(r'\s+', ' ', direct_upper).strip()
            direct_parts = set(direct_upper.split())
            direct_parts = {p for p in direct_parts if len(p) > 1}

            # Require meaningful overlap:
            # - For entity names (2+ word names): at least 2 parts overlap
            # - For person names: at least last name + first name match
            overlap = name_parts & direct_parts
            if len(name_parts) >= 2 and len(overlap) >= 2:
                mtg_records.append(rec)
            elif len(name_parts) == 1 and len(overlap) >= 1:
                # Single-word entity name — exact match required
                if name_upper == direct_upper or name_upper in direct_upper:
                    mtg_records.append(rec)

        if not mtg_records:
            return None

        # Sort by date (most recent first)
        mtg_records.sort(key=lambda r: parse_date(r["record_date"]),
                         reverse=True)

        # Return most recent MTG with a lender name
        for rec in mtg_records:
            if rec["reverse_name"]:
                return {
                    "clerk_lender": rec["reverse_name"],
                    "clerk_lender_type": classify_lender(rec["reverse_name"]),
                    "clerk_loan_date": rec["record_date"],
                    "clerk_instrument": rec["instrument_num"],
                    "clerk_doc_id": rec["doc_id"],
                    "clerk_all_mtg_count": len(mtg_records),
                }

        return None


def load_cache():
    """Load cached results to support resume."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_file = CACHE_DIR / "clerk_lender_cache.json"
    if cache_file.exists():
        with open(cache_file, "r") as f:
            return json.load(f)
    return {}


def save_cache(cache):
    """Save cache to disk."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_file = CACHE_DIR / "clerk_lender_cache.json"
    with open(cache_file, "w") as f:
        json.dump(cache, f, indent=2)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--max", type=int, default=0,
                        help="Max leads to look up (0=all without lender)")
    parser.add_argument("--resume", action="store_true",
                        help="Resume from cache")
    args = parser.parse_args()

    if not CAPTCHA_KEY:
        print("ERROR: TWOCAPTCHA_API_KEY not set in .env")
        sys.exit(1)

    if not INPUT_CSV.exists():
        print(f"ERROR: Input not found: {INPUT_CSV}")
        sys.exit(1)

    # Load pilot data
    import pandas as pd
    df = pd.read_csv(INPUT_CSV, dtype=str, low_memory=False)
    print(f"Loaded {len(df)} pilot leads")

    # Find leads without lender data
    def has_lender(row):
        attom = str(row.get("attom_lender_name", "")).strip()
        return attom and attom.lower() not in ("", "nan", "none", "n/a")

    needs_lender = df[~df.apply(has_lender, axis=1)]
    print(f"Leads without ATTOM lender: {len(needs_lender)}")

    # Use resolved_person or OWN_NAME for search
    search_names = []
    for _, row in needs_lender.iterrows():
        resolved = str(row.get("resolved_person", "")).strip()
        own_name = str(row.get("OWN_NAME", "")).strip()
        # Prefer resolved person name; fall back to OWN_NAME
        name = resolved if resolved and resolved.lower() not in ("nan", "none", "") else own_name
        if name and name.lower() not in ("nan", "none", ""):
            # Extract last name for search (first token before comma or space)
            search_names.append({
                "search_name": name,
                "own_name": own_name,
            })

    print(f"Searchable leads: {len(search_names)}")

    if args.max > 0:
        search_names = search_names[:args.max]
        print(f"Limited to {args.max} leads")

    # Load cache
    cache = load_cache() if args.resume else {}
    print(f"Cache: {len(cache)} entries")

    # Initialize scraper
    scraper = ClerkScraper()
    scraper.setup_session()

    results = []
    captcha_fails = 0
    max_consecutive_fails = 3
    connection_errors = 0

    for i, entry in enumerate(search_names):
        search_name = entry["search_name"]
        own_name = entry["own_name"]

        # Check cache
        if own_name in cache:
            results.append(cache[own_name])
            continue

        # Build the search name:
        # - For entities (LLC/INC/CORP), use the full entity name
        # - For people, use "LASTNAME FIRSTNAME" to avoid common-name overload
        name_for_search = search_name.strip()
        is_entity = any(s in own_name.upper() for s in
                        [" LLC", " INC", " CORP", " LTD", " LP", " LLLP",
                         " TRUST", " ASSOCIATION", " COMPANY"])

        if is_entity:
            # Use full entity name from OWN_NAME (more specific than resolved person)
            name_for_search = own_name.split("&")[0].strip()
        else:
            # For people: use full name (LASTNAME FIRSTNAME) not just last name
            name_for_search = search_name.split("&")[0].strip()

        # Remove suffixes that the clerk doesn't need
        for suffix in [" LLC", " INC", " CORP", " LTD", " LP", " LLLP",
                       " TRUSTEE", " ET AL", " ETAL"]:
            if name_for_search.upper().endswith(suffix):
                name_for_search = name_for_search[:len(name_for_search)-len(suffix)].strip()

        print(f"\n[{i+1}/{len(search_names)}] Searching: {name_for_search} "
              f"(OWN: {own_name[:30]})")

        # Solve captcha
        try:
            token, solve_time = scraper.solve_captcha()
            print(f"  Captcha: {solve_time:.1f}s")
            captcha_fails = 0
            connection_errors = 0
        except Exception as e:
            err_str = str(e)
            if "Connection" in err_str or "Recv failure" in err_str:
                connection_errors += 1
                wait = min(60 * connection_errors, 300)
                print(f"  Connection error #{connection_errors}, waiting {wait}s...")
                time.sleep(wait)
                try:
                    scraper.setup_session()
                except Exception:
                    pass
                continue
            print(f"  Captcha error: {e}")
            captcha_fails += 1
            if captcha_fails >= max_consecutive_fails:
                print("  Too many captcha failures. Stopping.")
                break
            continue

        # Search
        records, status = scraper.name_search(name_for_search, token, doc_type="MTG")

        if records is None:
            print(f"  Search failed (status {status})")
            if status in (0, 500):
                # Timeout or server error — refresh session and retry
                print("  Refreshing session and retrying...")
                scraper.setup_session()
                try:
                    token2, t2 = scraper.solve_captcha()
                    print(f"  Retry captcha: {t2:.1f}s")
                    records, status = scraper.name_search(
                        name_for_search, token2, doc_type="MTG")
                except Exception as e:
                    print(f"  Retry failed: {e}")

        if records is None:
            result_entry = {
                "OWN_NAME": own_name,
                "clerk_search_name": name_for_search,
                "clerk_status": "error",
            }
        elif not records:
            print(f"  No records found")
            result_entry = {
                "OWN_NAME": own_name,
                "clerk_search_name": name_for_search,
                "clerk_status": "no_records",
            }
        else:
            print(f"  Found {len(records)} records")
            # Try matching with search name first, then original name
            lender_info = scraper.find_lender(name_for_search, records)
            if not lender_info:
                lender_info = scraper.find_lender(search_name, records)
            if lender_info:
                print(f"  LENDER: {lender_info['clerk_lender'][:50]} "
                      f"({lender_info['clerk_lender_type']}) "
                      f"on {lender_info['clerk_loan_date']}")
                result_entry = {
                    "OWN_NAME": own_name,
                    "clerk_search_name": name_for_search,
                    "clerk_status": "found",
                    **lender_info,
                }
            else:
                print(f"  No MTG lender found in results")
                result_entry = {
                    "OWN_NAME": own_name,
                    "clerk_search_name": name_for_search,
                    "clerk_status": "no_mtg_match",
                    "clerk_all_mtg_count": sum(1 for r in records
                                               if r["doc_type"] in ("MTG", "MORTGAGE")),
                }

        results.append(result_entry)
        cache[own_name] = result_entry
        save_cache(cache)

        # Delay between searches to avoid rate limiting
        # Longer delay every 10 searches to be respectful
        if (i + 1) % 10 == 0:
            print(f"  -- Pausing 15s after 10 searches --")
            time.sleep(15)
        else:
            time.sleep(5)

    # Save results
    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    if results:
        fieldnames = list(results[0].keys())
        # Ensure all fields are present
        all_keys = set()
        for r in results:
            all_keys.update(r.keys())
        fieldnames = sorted(all_keys)

        with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(results)

    # Summary
    found = sum(1 for r in results if r.get("clerk_status") == "found")
    no_records = sum(1 for r in results if r.get("clerk_status") == "no_records")
    no_match = sum(1 for r in results if r.get("clerk_status") == "no_mtg_match")
    errors = sum(1 for r in results if r.get("clerk_status") == "error")

    print(f"\n{'='*60}")
    print(f"  CLERK LENDER LOOKUP RESULTS")
    print(f"{'='*60}")
    print(f"  Total searched: {len(results)}")
    print(f"  Found lender:   {found} ({100*found//max(len(results),1)}%)")
    print(f"  No records:     {no_records}")
    print(f"  No MTG match:   {no_match}")
    print(f"  Errors:         {errors}")
    print(f"  Captcha solves: {scraper.captcha_count}")
    print(f"  Captcha cost:   ${scraper.captcha_cost:.2f}")
    print(f"  Output: {OUTPUT_CSV}")
    print()


if __name__ == "__main__":
    main()
