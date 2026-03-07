"""
PBC Clerk NameSearch Test
=========================
Tests NameSearch with correct parameters from index.js analysis.
"""

import json
import os
import re
import sys
import time

from curl_cffi import requests as cffi_requests
from dotenv import load_dotenv
from twocaptcha import TwoCaptcha

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", "..", ".env"))

BASE = "https://erec.mypalmbeachclerk.com"
SITEKEY = "6LdBHOorAAAAALwRLkAZpnNsfcp7qfFS4YIGIRTU"

CAPTCHA_KEY = os.getenv("TWOCAPTCHA_API_KEY")
if not CAPTCHA_KEY:
    print("ERROR: TWOCAPTCHA_API_KEY not set")
    sys.exit(1)

solver = TwoCaptcha(CAPTCHA_KEY)


def strip_html(s):
    if not s:
        return ""
    s = re.sub(r'^(nobreak_|unclickable_|hidden_|legalfield_)', '', s)
    s = re.sub(r'<[^>]+>', ' ', s)
    return re.sub(r'\s+', ' ', s).strip()


def main():
    session = cffi_requests.Session(impersonate="chrome")
    print("Setting up session...")
    session.get(BASE, timeout=30)
    session.post(f"{BASE}/Search/SetDisclaimer", timeout=15)
    session.get(f"{BASE}/search/index", timeout=15)

    print("Solving captcha...")
    t0 = time.time()
    result = solver.recaptcha(sitekey=SITEKEY, url=f"{BASE}/search/index")
    token = result["code"]
    print(f"  Solved in {time.time()-t0:.1f}s")

    # Test NameSearch
    test_name = "BATMASIAN"
    criteria = {
        "searchLikeType": "0",  # Starts With
        "type": "0",            # Both
        "name": test_name,
        "doctype": "",          # No doc type filter first
        "bookType": "0",        # All Books
        "beginDate": "",
        "endDate": "",
        "recordCount": "200",
        "exclude": "false",
        "ReturnIndexGroups": "false",
        "townName": "",
        "selectedNamesIds": "",
        "includeNickNames": "false",
        "selectedNames": "",
        "mobileHomesOnly": "false",
        "g-recaptcha-response": token,
    }

    headers = {
        "X-Requested-With": "XMLHttpRequest",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Referer": f"{BASE}/search/index",
    }

    print(f"\nNameSearch: '{test_name}'...")
    r = session.post(f"{BASE}/Search/NameSearch", data=criteria,
                     headers=headers, timeout=30)
    print(f"  Status: {r.status_code}, Length: {len(r.text)}")

    if "Invalid Captcha" in r.text:
        print("  ERROR: Invalid Captcha!")
        return
    if r.status_code != 200:
        print(f"  Error: {r.text[:500]}")
        return

    print("  NameSearch OK!")

    # Fetch DataTables results
    dt_params = {
        "draw": "1", "start": "0", "length": "100",
        "search[value]": "", "search[regex]": "false",
        "order[0][column]": "0", "order[0][dir]": "asc",
    }
    for i in range(31):
        dt_params[f"columns[{i}][data]"] = str(i)
        dt_params[f"columns[{i}][name]"] = ""
        dt_params[f"columns[{i}][searchable]"] = "true"
        dt_params[f"columns[{i}][orderable]"] = "true" if i > 2 else "false"
        dt_params[f"columns[{i}][search][value]"] = ""
        dt_params[f"columns[{i}][search][regex]"] = "false"

    r2 = session.post(f"{BASE}/Search/GetSearchResults", data=dt_params,
                      headers=headers, timeout=30)

    if r2.status_code != 200:
        print(f"  GetSearchResults error: {r2.status_code}")
        return

    data = r2.json()
    rows = data.get("data", [])
    total = data.get("recordsTotal", 0)
    print(f"  Total records: {total}, Rows fetched: {len(rows)}")

    print(f"\n  {'Direct Name':<40} | {'Reverse Name':<40} | {'Date':<12} | {'Type'}")
    print("  " + "-" * 110)
    for row in rows[:20]:
        direct = strip_html(row.get("5", ""))
        reverse = strip_html(row.get("6", ""))
        date = strip_html(row.get("7", ""))
        doc_type = strip_html(row.get("9", ""))
        print(f"  {direct[:40]:<40} | {reverse[:40]:<40} | {date:<12} | {doc_type}")


if __name__ == "__main__":
    main()
