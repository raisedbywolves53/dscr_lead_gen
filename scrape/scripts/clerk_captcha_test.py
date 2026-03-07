"""
PBC Clerk Portal - 2Captcha Integration Test (v2)
==================================================

Correct parameter names discovered from search/index.js:
- doctype (not CriteriaDocumentTypes)
- beginDate / endDate (not CriteriaDateFrom/To)
- g-recaptcha-response (not CaptchaResponse)
- recordCount (200/700/3000/5000/10000)

Usage:
    python scrape/scripts/clerk_captcha_test.py
"""

import json
import os
import re
import sys
import time

from curl_cffi import requests as cffi_requests
from dotenv import load_dotenv
from twocaptcha import TwoCaptcha

load_dotenv()

CAPTCHA_KEY = os.getenv("TWOCAPTCHA_API_KEY")
if not CAPTCHA_KEY:
    print("ERROR: TWOCAPTCHA_API_KEY not set in .env")
    sys.exit(1)

BASE = "https://erec.mypalmbeachclerk.com"
SITEKEY = "6LdBHOorAAAAALwRLkAZpnNsfcp7qfFS4YIGIRTU"

solver = TwoCaptcha(CAPTCHA_KEY)


def strip_html(s):
    """Remove HTML tags and control prefixes from clerk response data."""
    if not s:
        return ""
    s = re.sub(r'^(nobreak_|unclickable_|hidden_|legalfield_)', '', s)
    s = re.sub(r'<[^>]+>', ' ', s)
    return re.sub(r'\s+', ' ', s).strip()


def build_datatables_params(draw=1, start=0, length=25, num_columns=31):
    """Build standard DataTables server-side processing POST parameters."""
    params = {
        "draw": str(draw),
        "start": str(start),
        "length": str(length),
        "search[value]": "",
        "search[regex]": "false",
        "order[0][column]": "0",
        "order[0][dir]": "asc",
    }
    for i in range(num_columns):
        params[f"columns[{i}][data]"] = str(i)
        params[f"columns[{i}][name]"] = ""
        params[f"columns[{i}][searchable]"] = "true"
        params[f"columns[{i}][orderable]"] = "true" if i > 2 else "false"
        params[f"columns[{i}][search][value]"] = ""
        params[f"columns[{i}][search][regex]"] = "false"
    return params


def setup_session():
    """Set up session with disclaimer accepted."""
    session = cffi_requests.Session(impersonate="chrome")
    print("Setting up session...")
    session.get(BASE, timeout=30)
    session.post(f"{BASE}/Search/SetDisclaimer", timeout=15)
    session.get(f"{BASE}/search/index", timeout=15)
    print("  Session ready.")
    return session


def solve_captcha():
    """Solve reCAPTCHA via 2Captcha."""
    print("Solving reCAPTCHA via 2Captcha...")
    t0 = time.time()
    result = solver.recaptcha(sitekey=SITEKEY, url=f"{BASE}/search/index")
    token = result["code"]
    print(f"  Solved in {time.time()-t0:.1f}s, token: {len(token)} chars")
    return token


def search_doc_type(session, token, doc_type="MTG", begin="01/01/2024",
                    end="03/06/2026", record_count="3000"):
    """Run DocumentTypeSearch with correct parameters."""
    criteria = {
        "doctype": doc_type,
        "beginDate": begin,
        "endDate": end,
        "recordCount": record_count,
        "exclude": "false",
        "ReturnIndexGroups": "false",
        "townName": "",
        "mobileHomesOnly": "false",
        "g-recaptcha-response": token,
    }
    headers = {
        "X-Requested-With": "XMLHttpRequest",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Referer": f"{BASE}/search/index",
    }
    print(f"DocumentTypeSearch: {doc_type}, {begin} to {end}, max {record_count}...")
    r = session.post(f"{BASE}/Search/DocumentTypeSearch", data=criteria,
                     headers=headers, timeout=30)
    print(f"  Status: {r.status_code}, Length: {len(r.text)}")

    if "Invalid Captcha" in r.text:
        print("  ERROR: Invalid Captcha!")
        return False
    if r.status_code != 200:
        print(f"  ERROR: {r.text[:200]}")
        return False

    # Save response
    with open("scrape/data/financing/clerk_doctype_response.html", "w",
              encoding="utf-8") as f:
        f.write(r.text)
    print("  Search submitted successfully!")
    return True


def fetch_results(session, max_pages=5):
    """Fetch all DataTables result pages."""
    all_rows = []
    headers = {
        "X-Requested-With": "XMLHttpRequest",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Referer": f"{BASE}/search/index",
    }

    for page in range(max_pages):
        start = page * 100
        dt_params = build_datatables_params(draw=page+1, start=start,
                                            length=100, num_columns=31)
        r = session.post(f"{BASE}/Search/GetSearchResults", data=dt_params,
                         headers=headers, timeout=30)
        if r.status_code != 200:
            print(f"  Page {page+1} error: {r.status_code}")
            break

        data = r.json()
        rows = data.get("data", [])
        total = data.get("recordsTotal", 0)

        if page == 0:
            print(f"  Total records: {total}")

        all_rows.extend(rows)
        print(f"  Page {page+1}: got {len(rows)} rows (total fetched: {len(all_rows)})")

        if len(all_rows) >= total or not rows:
            break

    return all_rows


def parse_rows(rows):
    """Parse DataTables rows into structured records.

    Column mapping from HTML:
    0: # (row number)
    3: status
    5: direct_name (borrower/property owner)
    6: reverse_name (lender)
    7: record_date
    9: doc_type
    11: book
    12: page
    13: instrument_number
    """
    records = []
    for row in rows:
        # Extract doc ID from the eye icon
        doc_id = ""
        eye_html = row.get("1", "")
        m = re.search(r"eye_(\d+)", eye_html)
        if m:
            doc_id = m.group(1)

        records.append({
            "doc_id": doc_id,
            "direct_name": strip_html(row.get("5", "")),
            "reverse_name": strip_html(row.get("6", "")),
            "record_date": strip_html(row.get("7", "")),
            "doc_type": strip_html(row.get("9", "")),
            "book": strip_html(row.get("11", "")),
            "page": strip_html(row.get("12", "")),
            "instrument_num": strip_html(row.get("13", "")),
            "legal": strip_html(row.get("15", "")),
        })
    return records


def main():
    session = setup_session()
    token = solve_captcha()

    # Search for all MTG docs in last 2 years
    ok = search_doc_type(session, token, doc_type="MTG",
                         begin="01/01/2024", end="03/06/2026",
                         record_count="3000")
    if not ok:
        print("\nSearch failed. Exiting.")
        sys.exit(1)

    # Fetch results
    print("\nFetching results...")
    rows = fetch_results(session, max_pages=30)

    if not rows:
        print("No results returned.")
        sys.exit(1)

    # Parse
    records = parse_rows(rows)

    # Display first 20
    print(f"\n{'#':>4} | {'Direct Name (Borrower)':<40} | {'Reverse Name (Lender)':<40} | {'Date':<12}")
    print("-" * 110)
    for i, rec in enumerate(records[:30]):
        print(f"{i+1:4d} | {rec['direct_name'][:40]:<40} | {rec['reverse_name'][:40]:<40} | {rec['record_date']}")

    # Stats
    with_lender = [r for r in records if r["reverse_name"]]
    print(f"\nTotal records: {len(records)}")
    print(f"With lender (reverse name): {len(with_lender)} ({100*len(with_lender)//len(records)}%)")

    # Save all records
    out_path = "scrape/data/financing/clerk_mtg_records.json"
    with open(out_path, "w") as f:
        json.dump(records, f, indent=2)
    print(f"Saved to {out_path}")

    # Also save as CSV
    import csv
    csv_path = "scrape/data/financing/clerk_mtg_records.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=records[0].keys())
        writer.writeheader()
        writer.writerows(records)
    print(f"Saved to {csv_path}")


if __name__ == "__main__":
    main()
