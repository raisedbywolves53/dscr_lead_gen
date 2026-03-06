"""
Step 8: Tracerfy Skip Trace + DNC Scrub
========================================

Sends your full lead list to Tracerfy's API for skip tracing
(phone + email discovery) and then runs DNC scrubbing on matched phones.

Tracerfy API:
  - Skip trace: $0.02/lead (up to 8 phones + 5 emails per lead)
  - DNC scrub: $0.02/phone (Federal DNC, State DNC, DMA, TCPA litigator)
  - No minimums, no subscriptions
  - Bearer token auth
  - CSV upload, async processing with webhook/polling

Flow:
  1. Read leads from data/enriched/top_leads_enriched.csv
  2. Format CSV for Tracerfy (owner name, address, city, state, zip)
  3. Upload via POST /trace/
  4. Poll GET /queue/:id until complete
  5. Download results CSV
  6. Optionally run DNC scrub on matched phones via POST /dnc/scrub/
  7. Save results to data/enriched/tracerfy_results.csv

Usage:
    python scripts/08_tracerfy_skip_trace.py
    python scripts/08_tracerfy_skip_trace.py --input data/enriched/top_leads_enriched.csv
    python scripts/08_tracerfy_skip_trace.py --skip-dnc         # skip the DNC scrub step
    python scripts/08_tracerfy_skip_trace.py --dnc-only          # only run DNC scrub on existing results
    python scripts/08_tracerfy_skip_trace.py --limit 500         # only process first N leads

Requires:
    TRACERFY_API_KEY in .env
"""

import argparse
import io
import os
import re
import time
from pathlib import Path

import pandas as pd

try:
    import requests
except ImportError:
    requests = None

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

DEFAULT_INPUT = ENRICHED_DIR / "top_leads_enriched.csv"
TRACERFY_OUTPUT = ENRICHED_DIR / "tracerfy_results.csv"
DNC_OUTPUT = ENRICHED_DIR / "tracerfy_dnc_results.csv"

TRACERFY_BASE = "https://tracerfy.com/v1/api"
TRACERFY_API_KEY = os.getenv("TRACERFY_API_KEY", "")

# Rate limit: max 10 POST trace requests per 5 minutes
POLL_INTERVAL = 15  # seconds between status checks
MAX_POLL_ATTEMPTS = 120  # 120 x 15s = 30 minutes max wait


def get_headers():
    return {
        "Authorization": f"Bearer {TRACERFY_API_KEY}",
    }


# ---------------------------------------------------------------------------
# CSV formatting for Tracerfy upload
# ---------------------------------------------------------------------------

def format_for_tracerfy(df: pd.DataFrame) -> str:
    """
    Format lead data as CSV for Tracerfy upload.
    Tracerfy needs property/owner info to match against their database.
    Uses owner mailing address since that's tied to the person, not the property.
    """
    rows = []
    for _, row in df.iterrows():
        # Use resolved person name if available, otherwise owner/entity name
        resolved = str(row.get("resolved_person", "")).strip()
        owner = str(row.get("OWN_NAME", "")).strip()

        # Priority: resolved person name > individual owner name > entity name
        # Tracerfy matches on address + name. Even LLC names can help with address matching.
        is_entity = False
        entity_keywords = ("LLC", "INC", "CORP", "CORPORATION", "TRUST",
                           "LP", "LLP", "LTD", "PARTNERSHIP", "ASSOCIATION",
                           "ASSOC", "HOLDINGS", "PROPERTIES", "INVESTMENTS",
                           "INVESTMENT", "INVESTM", "INVESTEMENTS", "VENTURES",
                           "GROUP", "ENTERPRISES", "COMPANY", "CO",
                           "REVOCABLE", "IRREVOCABLE", "LIVING", "FAMILY",
                           "REALTY", "REAL ESTATE", "APARTMENTS", "HOMES",
                           "DEVELOPMENT", "DEVELOPERS", "MANAGEMENT", "MGT",
                           "CAPITAL", "EQUITY", "FUND", "PARTNERS", "ASSETS")

        if resolved and resolved.upper() not in ("NAN", "NONE", ""):
            name = resolved
        else:
            name = owner
            # Check if this is an entity name (not a person)
            # Strip periods for matching (e.g., "INC." → "INC")
            upper = name.upper().replace(".", "")
            if any(upper.endswith(f" {s}") or f" {s} " in upper for s in entity_keywords):
                is_entity = True

        # Parse into first/last
        first, last = "", ""
        if is_entity:
            # Entity names: send empty first/last, let Tracerfy match on address only
            first, last = "", ""
        elif name and "," in name:
            # "LAST, FIRST" format
            parts = name.split(",", 1)
            last = parts[0].strip()
            first = parts[1].strip().split()[0] if len(parts) > 1 and parts[1].strip() else ""
        elif name:
            # FDOR format: "LAST FIRST" or "LAST FIRST MIDDLE"
            # Strip trailing "&" (joint ownership marker)
            clean = name.rstrip("& ").strip()
            parts = clean.split()
            if len(parts) >= 2:
                last = parts[0]
                first = parts[1]
            elif len(parts) == 1:
                last = parts[0]

        rows.append({
            "First Name": first,
            "Last Name": last,
            "Address": str(row.get("OWN_ADDR1", "")).strip(),
            "City": str(row.get("OWN_CITY", "")).strip(),
            "State": str(row.get("OWN_STATE_DOM", row.get("OWN_STATE", ""))).strip(),
            "Zip": str(row.get("OWN_ZIPCD", "")).strip()[:5],
        })

    out_df = pd.DataFrame(rows)
    return out_df.to_csv(index=False)


# ---------------------------------------------------------------------------
# Tracerfy API calls
# ---------------------------------------------------------------------------

def submit_trace(csv_content: str) -> dict:
    """Submit a skip trace job via CSV upload. Returns queue info."""
    if not requests:
        raise RuntimeError("requests library not installed. Run: pip install requests")

    url = f"{TRACERFY_BASE}/trace/"
    files = {
        "csv_file": ("leads.csv", csv_content, "text/csv"),
    }
    data = {
        "trace_type": "normal",
    }

    # Tracerfy requires column mapping parameters
    data["first_name_column"] = "First Name"
    data["last_name_column"] = "Last Name"
    data["address_column"] = "Address"
    data["city_column"] = "City"
    data["state_column"] = "State"
    data["zip_column"] = "Zip"
    # Mail address fields — use same as property owner address
    data["mail_address_column"] = "Address"
    data["mail_city_column"] = "City"
    data["mail_state_column"] = "State"

    print("  Uploading leads to Tracerfy...")
    resp = requests.post(url, headers=get_headers(), files=files, data=data, timeout=60)

    if resp.status_code not in (200, 201, 202):
        print(f"  ERROR: Tracerfy returned HTTP {resp.status_code}")
        print(f"  Response: {resp.text[:500]}")
        return {}

    result = resp.json()
    print(f"  Job submitted: {result}")
    return result


def poll_queue(queue_id: str) -> dict:
    """Poll a queue job until completion. Returns job info with download URL.

    Uses GET /queues/ (plural) which returns all jobs with pending/download_url.
    GET /queue/{id} (singular) returns individual lead records, NOT job status.
    """
    url = f"{TRACERFY_BASE}/queues/"

    for attempt in range(1, MAX_POLL_ATTEMPTS + 1):
        resp = requests.get(url, headers=get_headers(), timeout=30)
        if resp.status_code != 200:
            print(f"  Poll attempt {attempt}: HTTP {resp.status_code}")
            time.sleep(POLL_INTERVAL)
            continue

        queues = resp.json()
        if not isinstance(queues, list):
            queues = queues.get("results", [])

        # Find our queue by ID
        data = {}
        for q in queues:
            if str(q.get("id", "")) == queue_id:
                data = q
                break

        if not data:
            print(f"  Queue {queue_id} not found in response (attempt {attempt})")
            time.sleep(POLL_INTERVAL)
            continue

        pending = data.get("pending", True)

        if not pending:
            elapsed = attempt * POLL_INTERVAL
            print(f"  Job completed after {elapsed}s")
            print(f"  Credits deducted: {data.get('credits_deducted', '?')}")
            return data
        else:
            if attempt % 4 == 1:  # Print every ~60s
                print(f"  Waiting... pending=True (attempt {attempt}/{MAX_POLL_ATTEMPTS})")
            time.sleep(POLL_INTERVAL)

    print(f"  TIMEOUT: Job did not complete after {MAX_POLL_ATTEMPTS * POLL_INTERVAL}s")
    return {}


def download_results(download_url: str) -> pd.DataFrame:
    """Download completed trace results as a DataFrame."""
    print(f"  Downloading results from {download_url[:80]}...")

    # If the URL is relative, prepend base
    if download_url.startswith("/"):
        download_url = f"https://tracerfy.com{download_url}"

    # CDN URLs don't need auth headers — only use auth for API URLs
    headers = get_headers() if "tracerfy.com/v1/api" in download_url else {}
    resp = requests.get(download_url, headers=headers, timeout=120)
    if resp.status_code != 200:
        print(f"  ERROR downloading results: HTTP {resp.status_code}")
        return pd.DataFrame()

    df = pd.read_csv(io.StringIO(resp.text), dtype=str)
    print(f"  Downloaded {len(df)} result rows")
    return df


def get_all_queues() -> list:
    """Get all queue jobs to find download URLs."""
    url = f"{TRACERFY_BASE}/queues/"
    resp = requests.get(url, headers=get_headers(), timeout=30)
    if resp.status_code == 200:
        return resp.json() if isinstance(resp.json(), list) else resp.json().get("results", [])
    return []


# ---------------------------------------------------------------------------
# DNC scrub via Tracerfy API
# ---------------------------------------------------------------------------

def submit_dnc_scrub(phones: list) -> dict:
    """Submit phone numbers for DNC scrubbing. Returns queue info."""
    url = f"{TRACERFY_BASE}/dnc/scrub/"

    # Send as JSON body with phone list
    payload = {"phones": phones}

    print(f"  Submitting {len(phones)} phones for DNC scrub...")
    resp = requests.post(url, headers=get_headers(), json=payload, timeout=60)

    if resp.status_code not in (200, 201, 202):
        print(f"  ERROR: DNC scrub returned HTTP {resp.status_code}")
        print(f"  Response: {resp.text[:500]}")
        return {}

    result = resp.json()
    print(f"  DNC job submitted: {result}")
    return result


def poll_dnc_queue(queue_id: str) -> dict:
    """Poll DNC scrub job until completion."""
    url = f"{TRACERFY_BASE}/dnc/queue/{queue_id}"

    for attempt in range(1, MAX_POLL_ATTEMPTS + 1):
        resp = requests.get(url, headers=get_headers(), timeout=30)
        if resp.status_code != 200:
            time.sleep(POLL_INTERVAL)
            continue

        data = resp.json()
        status = data.get("status", "").lower()

        if status in ("completed", "complete", "done", "finished"):
            print(f"  DNC scrub completed after {attempt * POLL_INTERVAL}s")
            return data
        elif status in ("failed", "error"):
            print(f"  DNC scrub FAILED: {data}")
            return data
        else:
            if attempt % 4 == 1:
                print(f"  DNC waiting... status: {status}")
            time.sleep(POLL_INTERVAL)

    print(f"  DNC TIMEOUT after {MAX_POLL_ATTEMPTS * POLL_INTERVAL}s")
    return {}


# ---------------------------------------------------------------------------
# Result normalization
# ---------------------------------------------------------------------------

def normalize_phone(phone) -> str:
    """Normalize phone to 10 digits."""
    phone = re.sub(r"\D", "", str(phone))
    if len(phone) == 11 and phone.startswith("1"):
        phone = phone[1:]
    return phone if len(phone) == 10 else ""


def normalize_tracerfy_results(raw_df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalize Tracerfy output into our standard format.

    Tracerfy returns columns like:
      first_name, last_name, address, city, state, zip,
      primary_phone, primary_phone_type,
      Email-1 through Email-5,
      Mobile-1 through Mobile-5,
      Landline-1 through Landline-3
    """
    if raw_df.empty:
        return raw_df

    rows = []
    for _, row in raw_df.iterrows():
        # Collect all phones: primary, then mobiles, then landlines
        phones = []
        phone_types = []

        # Primary phone
        primary = normalize_phone(row.get("primary_phone", ""))
        primary_type = str(row.get("primary_phone_type", "")).lower()
        if primary:
            phones.append(primary)
            phone_types.append(primary_type if primary_type not in ("nan", "", "none") else "unknown")

        # Mobile-1 through Mobile-5
        for i in range(1, 6):
            p = normalize_phone(row.get(f"Mobile-{i}", ""))
            if p and p not in phones:
                phones.append(p)
                phone_types.append("mobile")

        # Landline-1 through Landline-3
        for i in range(1, 4):
            p = normalize_phone(row.get(f"Landline-{i}", ""))
            if p and p not in phones:
                phones.append(p)
                phone_types.append("landline")

        # Collect emails: Email-1 through Email-5
        emails = []
        for i in range(1, 6):
            e = str(row.get(f"Email-{i}", "")).strip()
            if e and "@" in e and e.upper() not in ("NAN", "NONE"):
                emails.append(e)

        # Pick best phone (prefer mobile)
        best_phone = ""
        best_phone_type = ""
        for p, t in zip(phones, phone_types):
            if t == "mobile":
                best_phone = p
                best_phone_type = "mobile"
                break
        if not best_phone and phones:
            best_phone = phones[0]
            best_phone_type = phone_types[0] if phone_types else "unknown"

        # Build matching keys
        first = str(row.get("first_name", "")).strip()
        last = str(row.get("last_name", "")).strip()
        zipcode = str(row.get("zip", "")).strip()[:5]
        address = str(row.get("address", "")).strip()

        rows.append({
            "tracerfy_first": first if first.upper() not in ("NAN", "NONE") else "",
            "tracerfy_last": last if last.upper() not in ("NAN", "NONE") else "",
            "tracerfy_zip": zipcode if zipcode.upper() not in ("NAN", "NONE") else "",
            "tracerfy_address": address if address.upper() not in ("NAN", "NONE") else "",
            "tracerfy_phone_1": best_phone,
            "tracerfy_phone_1_type": best_phone_type,
            "tracerfy_phone_2": phones[1] if len(phones) > 1 else "",
            "tracerfy_phone_2_type": phone_types[1] if len(phone_types) > 1 else "",
            "tracerfy_all_phones": "; ".join(phones),
            "tracerfy_email_1": emails[0] if emails else "",
            "tracerfy_email_2": emails[1] if len(emails) > 1 else "",
            "tracerfy_all_emails": "; ".join(emails),
            "tracerfy_match": "yes" if (best_phone or emails) else "no",
        })

    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Tracerfy skip trace + DNC scrub (Step 8)")
    parser.add_argument("--input", type=str, default=str(DEFAULT_INPUT),
                        help=f"Input CSV (default: {DEFAULT_INPUT})")
    parser.add_argument("--limit", type=int, default=0,
                        help="Limit to first N leads (0 = all)")
    parser.add_argument("--skip-dnc", action="store_true",
                        help="Skip DNC scrub (use free FTC registry instead)")
    parser.add_argument("--dnc-only", action="store_true",
                        help="Only run DNC scrub on existing tracerfy_results.csv")
    parser.add_argument("--dry-run", action="store_true",
                        help="Format CSV and show preview without uploading")
    args = parser.parse_args()

    ENRICHED_DIR.mkdir(parents=True, exist_ok=True)

    # Check API key
    if not TRACERFY_API_KEY:
        print("\n  ERROR: TRACERFY_API_KEY not set in .env")
        print("  1. Sign up at https://www.tracerfy.com")
        print("  2. Go to your dashboard, generate an API key")
        print("  3. Add to scrape/.env:")
        print("     TRACERFY_API_KEY=your_key_here")
        return

    if not requests:
        print("\n  ERROR: requests library not installed. Run: pip install requests")
        return

    # ------------------------------------------------------------------
    # DNC-only mode: scrub phones from existing results
    # ------------------------------------------------------------------
    if args.dnc_only:
        if not TRACERFY_OUTPUT.exists():
            print(f"\n  No results file found: {TRACERFY_OUTPUT}")
            print("  Run skip trace first (without --dnc-only)")
            return

        results_df = pd.read_csv(TRACERFY_OUTPUT, dtype=str)
        all_phones = []
        for col in ["tracerfy_phone_1", "tracerfy_phone_2"]:
            if col in results_df.columns:
                phones = results_df[col].dropna().apply(normalize_phone)
                all_phones.extend(phones[phones != ""].tolist())

        all_phones = list(set(all_phones))
        if not all_phones:
            print("  No phone numbers to scrub.")
            return

        print(f"\n  DNC scrub: {len(all_phones)} unique phones")
        print(f"  Estimated cost: ${len(all_phones) * 0.02:.2f}")

        dnc_result = submit_dnc_scrub(all_phones)
        queue_id = dnc_result.get("id", dnc_result.get("queue_id", ""))
        if not queue_id:
            print("  Failed to get DNC queue ID")
            return

        dnc_data = poll_dnc_queue(str(queue_id))
        download_url = dnc_data.get("download_url", dnc_data.get("results_url", ""))
        if download_url:
            dnc_df = download_results(download_url)
            dnc_df.to_csv(DNC_OUTPUT, index=False)
            print(f"  DNC results saved: {DNC_OUTPUT}")

            # Count clean vs flagged
            if "is_clean" in dnc_df.columns:
                clean = dnc_df["is_clean"].astype(str).str.lower().isin(["true", "1", "yes"]).sum()
                flagged = len(dnc_df) - clean
                print(f"  Clean phones: {clean}")
                print(f"  DNC flagged: {flagged}")
        return

    # ------------------------------------------------------------------
    # Load leads
    # ------------------------------------------------------------------
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"\n  Input file not found: {input_path}")
        print("  Run script 05 first to generate the enriched leads file.")
        return

    print(f"\n  Loading leads from: {input_path}")
    df = pd.read_csv(input_path, dtype=str, low_memory=False)
    print(f"  Total leads: {len(df):,}")

    if args.limit > 0:
        df = df.head(args.limit)
        print(f"  Limited to first {args.limit} leads")

    # ------------------------------------------------------------------
    # Format CSV
    # ------------------------------------------------------------------
    csv_content = format_for_tracerfy(df)
    lead_count = len(df)

    trace_cost = lead_count * 0.02
    print(f"\n  Skip trace cost: {lead_count} leads x $0.02 = ${trace_cost:.2f}")

    if args.dry_run:
        print("\n  DRY RUN — CSV preview (first 5 rows):")
        preview = csv_content.split("\n")[:6]
        for line in preview:
            print(f"    {line}")
        print(f"\n  Would upload {lead_count} leads to Tracerfy.")
        print(f"  Estimated cost: ${trace_cost:.2f}")
        return

    # ------------------------------------------------------------------
    # Submit trace job
    # ------------------------------------------------------------------
    trace_result = submit_trace(csv_content)
    queue_id = trace_result.get("id", trace_result.get("queue_id", ""))

    if not queue_id:
        # Try to extract from response
        print("  Trying to find queue ID from response...")
        print(f"  Full response: {trace_result}")

        # Check if there's a different key structure
        for key in ["data", "result", "job"]:
            if key in trace_result and isinstance(trace_result[key], dict):
                queue_id = trace_result[key].get("id", trace_result[key].get("queue_id", ""))
                if queue_id:
                    break

    if not queue_id:
        print("  ERROR: Could not get queue ID from Tracerfy response.")
        print("  Check your API key and try again.")
        return

    print(f"  Queue ID: {queue_id}")

    # ------------------------------------------------------------------
    # Poll for completion
    # ------------------------------------------------------------------
    job_data = poll_queue(str(queue_id))

    # Try to find download URL
    download_url = ""
    for key in ["download_url", "results_url", "file_url", "csv_url", "url"]:
        if key in job_data:
            download_url = job_data[key]
            break

    # Check nested data
    if not download_url:
        for key in ["data", "result"]:
            if key in job_data and isinstance(job_data[key], dict):
                for url_key in ["download_url", "results_url", "file_url"]:
                    if url_key in job_data[key]:
                        download_url = job_data[key][url_key]
                        break

    if not download_url:
        print("  No download URL in job response. Checking all queues...")
        queues = get_all_queues()
        for q in queues:
            qid = str(q.get("id", ""))
            if qid == str(queue_id):
                for key in ["download_url", "results_url", "file_url"]:
                    if key in q:
                        download_url = q[key]
                        break

    if not download_url:
        print("  ERROR: Could not find download URL.")
        print(f"  Job data: {job_data}")
        print("  Try checking your Tracerfy dashboard for results.")
        return

    # ------------------------------------------------------------------
    # Download and normalize results
    # ------------------------------------------------------------------
    raw_results = download_results(download_url)
    if raw_results.empty:
        print("  No results returned from Tracerfy.")
        return

    # Save raw results for debugging
    raw_path = ENRICHED_DIR / "tracerfy_raw_results.csv"
    raw_results.to_csv(raw_path, index=False)
    print(f"  Raw results saved: {raw_path}")

    # Normalize into our format
    results_df = normalize_tracerfy_results(raw_results)
    results_df.to_csv(TRACERFY_OUTPUT, index=False)

    matched = results_df["tracerfy_match"].eq("yes").sum()
    has_phone = results_df["tracerfy_phone_1"].astype(str).str.len().ge(10).sum()
    has_email = results_df["tracerfy_email_1"].astype(str).str.contains("@", na=False).sum()

    print(f"\n  Results: {matched}/{len(results_df)} matched ({matched/len(results_df)*100:.0f}%)")
    print(f"  Phones found: {has_phone}")
    print(f"  Emails found: {has_email}")
    print(f"  Saved: {TRACERFY_OUTPUT}")

    # ------------------------------------------------------------------
    # DNC scrub (optional)
    # ------------------------------------------------------------------
    if not args.skip_dnc and has_phone > 0:
        all_phones = []
        for col in ["tracerfy_phone_1", "tracerfy_phone_2"]:
            phones = results_df[col].dropna().apply(normalize_phone)
            all_phones.extend(phones[phones != ""].tolist())

        all_phones = list(set(all_phones))
        dnc_cost = len(all_phones) * 0.02

        print(f"\n  DNC scrub: {len(all_phones)} unique phones")
        print(f"  DNC cost: ${dnc_cost:.2f}")
        print(f"  Total cost (trace + DNC): ${trace_cost + dnc_cost:.2f}")

        dnc_result = submit_dnc_scrub(all_phones)
        dnc_queue_id = dnc_result.get("id", dnc_result.get("queue_id", ""))

        if dnc_queue_id:
            dnc_data = poll_dnc_queue(str(dnc_queue_id))
            dnc_download = ""
            for key in ["download_url", "results_url", "file_url"]:
                if key in dnc_data:
                    dnc_download = dnc_data[key]
                    break

            if dnc_download:
                dnc_df = download_results(dnc_download)
                dnc_df.to_csv(DNC_OUTPUT, index=False)
                print(f"  DNC results saved: {DNC_OUTPUT}")

                if "is_clean" in dnc_df.columns:
                    clean = dnc_df["is_clean"].astype(str).str.lower().isin(["true", "1", "yes"]).sum()
                    flagged = len(dnc_df) - clean
                    print(f"  Clean phones: {clean}")
                    print(f"  DNC/litigator flagged: {flagged}")
    elif args.skip_dnc:
        print("\n  DNC scrub skipped (--skip-dnc). Use free FTC registry instead.")

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------
    print()
    print("=" * 60)
    print("  TRACERFY SUMMARY")
    print("=" * 60)
    print(f"  Leads uploaded:      {lead_count:,}")
    print(f"  Matches:             {matched:,} ({matched/lead_count*100:.0f}%)")
    print(f"  Phones found:        {has_phone:,}")
    print(f"  Emails found:        {has_email:,}")
    print(f"  Trace cost:          ${trace_cost:.2f}")
    if not args.skip_dnc and has_phone > 0:
        print(f"  DNC scrub cost:      ${len(all_phones) * 0.02:.2f}")
        print(f"  Total cost:          ${trace_cost + len(all_phones) * 0.02:.2f}")
    print()
    print("  NEXT STEPS:")
    print("  python scripts/05b_merge_enrichment.py")
    print("  python scripts/06_validate_contacts.py --county merged")
    print()


if __name__ == "__main__":
    main()
