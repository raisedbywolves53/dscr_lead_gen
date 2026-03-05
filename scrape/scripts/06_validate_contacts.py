"""
Step 6: Validate Contact Information
======================================

Checks that emails are deliverable and phone numbers are active
BEFORE you start outreach. This prevents:
  - Bounced emails (hurts your sender reputation)
  - Calling dead numbers (wastes time)
  - Calling DNC numbers (can result in $43,000+ fines per violation)

Services used:
  - MillionVerifier API — email validation (~$0.50 per 1,000 emails)
  - Twilio Lookup API — phone validation ($0.005 per lookup)
  - FTC DNC list — Do Not Call check (free download from donotcall.gov)

If no API keys are configured in .env, the script skips validation
and passes data through with a warning. You can validate later.

Usage:
    python scripts/06_validate_contacts.py --county seminole
    python scripts/06_validate_contacts.py --county all
"""

import argparse
import csv
import os
import re
import time
from pathlib import Path

import pandas as pd

# Try to load optional dependencies
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
except ImportError:
    pass

try:
    import requests
except ImportError:
    requests = None

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent
ENRICHED_DIR = PROJECT_DIR / "data" / "enriched"
VALIDATED_DIR = PROJECT_DIR / "data" / "validated"
DNC_FILE = PROJECT_DIR / "data" / "raw" / "dnc_list.csv"

# Also check filtered dir — if enrichment was skipped, read from there
FILTERED_DIR = PROJECT_DIR / "data" / "filtered"

# ---------------------------------------------------------------------------
# API config from environment
# ---------------------------------------------------------------------------
MILLIONVERIFIER_API_KEY = os.getenv("MILLIONVERIFIER_API_KEY", "")
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "")

# Rate limiting
TWILIO_DELAY = 0.1    # 10 requests/sec is well within Twilio limits
MV_DELAY = 0.05       # MillionVerifier single-email API is fast


# ---------------------------------------------------------------------------
# DNC list handling
# ---------------------------------------------------------------------------

def load_dnc_set() -> set:
    """
    Load the FTC Do Not Call list into a set for fast lookup.
    The DNC list is a flat file of phone numbers (one per line).
    Download from: https://www.donotcall.gov/
    Place in: data/raw/dnc_list.csv
    """
    if not DNC_FILE.exists():
        return set()

    print("  Loading DNC list...")
    dnc_numbers = set()
    with open(DNC_FILE, newline="") as f:
        reader = csv.reader(f)
        for row in reader:
            if row:
                # Normalize to 10-digit number
                phone = re.sub(r"\D", "", row[0])
                if len(phone) == 11 and phone.startswith("1"):
                    phone = phone[1:]
                if len(phone) == 10:
                    dnc_numbers.add(phone)

    print(f"  Loaded {len(dnc_numbers):,} DNC numbers.")
    return dnc_numbers


def normalize_phone(phone) -> str:
    """Normalize a phone number to 10 digits. Returns '' if invalid."""
    phone = re.sub(r"\D", "", str(phone))
    if len(phone) == 11 and phone.startswith("1"):
        phone = phone[1:]
    if len(phone) == 10:
        return phone
    return ""


# ---------------------------------------------------------------------------
# MillionVerifier email validation
# ---------------------------------------------------------------------------

def validate_email_millionverifier(email: str) -> dict:
    """
    Validate a single email via MillionVerifier API.

    Returns dict with:
      - status: "valid", "invalid", "risky", "catch_all", "unknown"
      - result: raw API result string
    """
    if not MILLIONVERIFIER_API_KEY or not requests:
        return {"status": "skipped", "result": "no_api_key"}

    url = "https://api.millionverifier.com/api/v3/"
    params = {
        "api": MILLIONVERIFIER_API_KEY,
        "email": email,
    }

    try:
        resp = requests.get(url, params=params, timeout=15)
        if resp.status_code != 200:
            return {"status": "error", "result": f"HTTP {resp.status_code}"}

        data = resp.json()
        # MillionVerifier returns: "ok", "catch_all", "unknown", "error",
        # "disposable", "invalid"
        result_code = data.get("result", "unknown").lower()

        if result_code == "ok":
            return {"status": "valid", "result": result_code}
        elif result_code == "catch_all":
            return {"status": "catch_all", "result": result_code}
        elif result_code in ("error", "invalid", "disposable"):
            return {"status": "invalid", "result": result_code}
        else:
            return {"status": "risky", "result": result_code}

    except Exception as e:
        return {"status": "error", "result": str(e)}


# ---------------------------------------------------------------------------
# Twilio phone validation
# ---------------------------------------------------------------------------

def validate_phone_twilio(phone: str) -> dict:
    """
    Validate a phone number via Twilio Lookup API.

    Returns dict with:
      - valid: True/False
      - carrier: carrier name
      - phone_type: "mobile", "landline", "voip", or "unknown"
    """
    if not TWILIO_ACCOUNT_SID or not TWILIO_AUTH_TOKEN or not requests:
        return {"valid": True, "carrier": "", "phone_type": "unknown"}

    url = f"https://lookups.twilio.com/v1/PhoneNumbers/+1{phone}"
    params = {"Type": "carrier"}

    try:
        resp = requests.get(
            url,
            params=params,
            auth=(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN),
            timeout=15,
        )
        if resp.status_code == 404:
            return {"valid": False, "carrier": "", "phone_type": "unknown"}
        if resp.status_code != 200:
            return {"valid": True, "carrier": "", "phone_type": "unknown"}

        data = resp.json()
        carrier_info = data.get("carrier", {})
        phone_type = carrier_info.get("type", "unknown")

        # Map Twilio types
        type_map = {"mobile": "mobile", "landline": "landline", "voip": "voip"}
        clean_type = type_map.get(phone_type, "unknown")

        return {
            "valid": True,
            "carrier": carrier_info.get("name", ""),
            "phone_type": clean_type,
        }

    except Exception as e:
        return {"valid": True, "carrier": "", "phone_type": "unknown"}


# ---------------------------------------------------------------------------
# Main validation logic
# ---------------------------------------------------------------------------

def find_input_file(county_name: str) -> Path:
    """
    Find the best input file — prefer enriched, fall back to LLC-resolved
    or qualified. Also checks for the merged enrichment file from 05b.
    """
    candidates = [
        ENRICHED_DIR / f"{county_name}_enriched.csv",
        ENRICHED_DIR / "merged_enriched.csv",       # from 05b_merge_enrichment
        ENRICHED_DIR / "top_leads_enriched.csv",     # from 05_enrich_contacts
        FILTERED_DIR / f"{county_name}_llc_resolved.csv",
        FILTERED_DIR / f"{county_name}_qualified.csv",
    ]
    for path in candidates:
        if path.exists():
            return path
    return candidates[0]  # return enriched path for error message


def validate_county(county_name: str):
    """Validate contacts for a single county."""

    input_file = find_input_file(county_name)
    if not input_file.exists():
        print(f"  No input file found for '{county_name}'.")
        print(f"  Looked for:")
        print(f"    - data/enriched/{county_name}_enriched.csv")
        print(f"    - data/filtered/{county_name}_llc_resolved.csv")
        print(f"    - data/filtered/{county_name}_qualified.csv")
        print(f"  Run earlier pipeline steps first.")
        return

    df = pd.read_csv(input_file, dtype=str, low_memory=False)
    print(f"  Loaded {len(df):,} records from {input_file.name}")

    # Check what APIs are available
    has_mv = bool(MILLIONVERIFIER_API_KEY)
    has_twilio = bool(TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN)

    if not has_mv and not has_twilio:
        print()
        print("  WARNING: No API keys configured.")
        print("  Set these in your .env file to enable validation:")
        print("    MILLIONVERIFIER_API_KEY=your_key_here")
        print("    TWILIO_ACCOUNT_SID=your_sid_here")
        print("    TWILIO_AUTH_TOKEN=your_token_here")
        print()
        print("  Passing data through WITHOUT validation.")
        print("  You can re-run this step later after adding API keys.")
        print()

    # Load DNC list
    dnc_set = load_dnc_set()
    has_dnc = len(dnc_set) > 0
    if not has_dnc:
        print("  No DNC list found at data/raw/dnc_list.csv")
        print("  Download from https://www.donotcall.gov/ to enable DNC checking.")

    # -------------------------------------------------------------------
    # Ensure contact columns exist (may not if enrichment was skipped)
    # -------------------------------------------------------------------
    for col in ["phone_1", "phone_2", "email_1", "email_2",
                "phone_1_source", "phone_2_source",
                "email_1_source", "email_2_source"]:
        if col not in df.columns:
            df[col] = ""

    # Initialize validation columns
    df["email_1_status"] = ""
    df["email_2_status"] = ""
    df["phone_1_valid"] = ""
    df["phone_1_carrier"] = ""
    df["phone_1_type"] = ""
    df["phone_1_dnc"] = ""
    df["phone_2_valid"] = ""
    df["phone_2_carrier"] = ""
    df["phone_2_type"] = ""
    df["phone_2_dnc"] = ""

    # -------------------------------------------------------------------
    # Validate emails
    # -------------------------------------------------------------------
    emails_to_check = df[df["email_1"].astype(str).str.contains("@", na=False)]
    email_count = len(emails_to_check)

    if email_count > 0 and has_mv:
        print(f"\n  Validating {email_count:,} emails via MillionVerifier...")
        print(f"  Estimated cost: ~${email_count / 1000 * 0.50:.2f}")

        validated = 0
        valid_count = 0
        for idx, row in emails_to_check.iterrows():
            email = str(row["email_1"]).strip()
            if "@" in email:
                result = validate_email_millionverifier(email)
                df.at[idx, "email_1_status"] = result["status"]
                if result["status"] in ("valid", "catch_all"):
                    valid_count += 1
                validated += 1
                if validated % 100 == 0:
                    print(f"    Checked {validated}/{email_count} "
                          f"({valid_count} valid so far)")
                time.sleep(MV_DELAY)

            # Also check email_2 if present
            email2 = str(row.get("email_2", "")).strip()
            if "@" in email2:
                result2 = validate_email_millionverifier(email2)
                df.at[idx, "email_2_status"] = result2["status"]
                time.sleep(MV_DELAY)

        print(f"    Done: {valid_count}/{validated} emails valid or catch-all")
    elif email_count > 0:
        print(f"\n  Skipping email validation ({email_count:,} emails) — no API key.")
        df.loc[emails_to_check.index, "email_1_status"] = "not_validated"
    else:
        print("\n  No emails to validate.")

    # -------------------------------------------------------------------
    # Validate phones
    # -------------------------------------------------------------------
    phones_to_check = df[df["phone_1"].astype(str).str.len() >= 10]
    phone_count = len(phones_to_check)

    if phone_count > 0:
        print(f"\n  Processing {phone_count:,} phone numbers...")

        validated = 0
        valid_count = 0
        dnc_count = 0

        for idx, row in phones_to_check.iterrows():
            phone = normalize_phone(row["phone_1"])
            if not phone:
                df.at[idx, "phone_1_valid"] = "False"
                continue

            # DNC check (free, no API needed)
            if has_dnc:
                is_dnc = phone in dnc_set
                df.at[idx, "phone_1_dnc"] = str(is_dnc)
                if is_dnc:
                    dnc_count += 1

            # Twilio carrier lookup
            if has_twilio:
                result = validate_phone_twilio(phone)
                df.at[idx, "phone_1_valid"] = str(result["valid"])
                df.at[idx, "phone_1_carrier"] = result["carrier"]
                df.at[idx, "phone_1_type"] = result["phone_type"]
                if result["valid"]:
                    valid_count += 1
                validated += 1
                if validated % 100 == 0:
                    print(f"    Checked {validated}/{phone_count} "
                          f"({valid_count} valid, {dnc_count} DNC)")
                time.sleep(TWILIO_DELAY)
            else:
                df.at[idx, "phone_1_valid"] = "not_validated"

            # Also check phone_2 if present
            phone2 = normalize_phone(row.get("phone_2", ""))
            if phone2:
                if has_dnc:
                    df.at[idx, "phone_2_dnc"] = str(phone2 in dnc_set)
                if has_twilio:
                    result2 = validate_phone_twilio(phone2)
                    df.at[idx, "phone_2_valid"] = str(result2["valid"])
                    df.at[idx, "phone_2_carrier"] = result2["carrier"]
                    df.at[idx, "phone_2_type"] = result2["phone_type"]
                    time.sleep(TWILIO_DELAY)

        if has_twilio:
            cost = validated * 0.005
            print(f"    Done: {valid_count}/{validated} phones valid "
                  f"(${cost:.2f} Twilio cost)")
        if has_dnc:
            print(f"    DNC flagged: {dnc_count:,}")
    else:
        print("\n  No phone numbers to validate.")

    # -------------------------------------------------------------------
    # Save output
    # -------------------------------------------------------------------
    output_file = VALIDATED_DIR / f"{county_name}_validated.csv"
    df.to_csv(output_file, index=False)

    # -------------------------------------------------------------------
    # Summary
    # -------------------------------------------------------------------
    print()
    print("=" * 60)
    print("  VALIDATION SUMMARY")
    print("=" * 60)
    print(f"  Total records:       {len(df):,}")

    # Email stats
    has_email = df["email_1"].astype(str).str.contains("@", na=False).sum()
    valid_email = df["email_1_status"].isin(["valid", "catch_all"]).sum()
    invalid_email = df["email_1_status"].eq("invalid").sum()
    print(f"  Emails found:        {has_email:,}")
    if has_mv:
        print(f"    Valid:             {valid_email:,}")
        print(f"    Invalid:           {invalid_email:,}")

    # Phone stats
    has_phone = df["phone_1"].astype(str).str.len().ge(10).sum()
    valid_phone = df["phone_1_valid"].eq("True").sum()
    dnc_flagged = df["phone_1_dnc"].eq("True").sum()
    mobile = df["phone_1_type"].eq("mobile").sum()
    landline = df["phone_1_type"].eq("landline").sum()
    print(f"  Phones found:        {has_phone:,}")
    if has_twilio:
        print(f"    Valid:             {valid_phone:,}")
        print(f"    Mobile:            {mobile:,}")
        print(f"    Landline:          {landline:,}")
    if has_dnc:
        print(f"    DNC flagged:       {dnc_flagged:,}")

    print(f"\n  Saved: {output_file}")
    print()


def main():
    parser = argparse.ArgumentParser(
        description="Validate emails and phone numbers (Step 6)"
    )
    parser.add_argument(
        "--county",
        type=str,
        required=True,
        help='County name (e.g. "seminole") or "all"',
    )
    args = parser.parse_args()

    VALIDATED_DIR.mkdir(parents=True, exist_ok=True)

    county_arg = args.county.strip().lower()

    if county_arg == "all":
        # Check enriched first, then filtered
        files = sorted(ENRICHED_DIR.glob("*_enriched.csv"))
        if not files:
            files = sorted(FILTERED_DIR.glob("*_llc_resolved.csv"))
        if not files:
            files = sorted(FILTERED_DIR.glob("*_qualified.csv"))
        if not files:
            print(f"\nNo input files found. Run earlier pipeline steps first.")
            return
        counties = [f.stem.split("_")[0] for f in files]
    else:
        counties = [county_arg.replace(" ", "_").replace("-", "_")]

    for county_name in counties:
        print()
        print("=" * 60)
        print(f"  VALIDATING: {county_name.upper()}")
        print("=" * 60)
        validate_county(county_name)

    print("=" * 60)
    print(f"  Next step: python scripts/07_export_campaign_ready.py --county {county_arg}")
    print("=" * 60)


if __name__ == "__main__":
    main()
