"""
Step 5b: Merge Enrichment Results
==================================

After you've done manual research (research_tracker.xlsx) and/or
uploaded to Datazapp, this script merges everything into a single
enriched file ready for validation.

Input sources (uses whatever exists):
  1. data/enriched/top_leads_enriched.csv (from script 05)
  2. data/enriched/research_tracker.xlsx (your manual lookups — yellow columns)
  3. data/enriched/datazapp_results.csv (Datazapp skip trace output)

Output:
  data/enriched/merged_enriched.csv

Usage:
    python scripts/05b_merge_enrichment.py
"""

import re
from pathlib import Path

import pandas as pd

try:
    from openpyxl import load_workbook
    HAS_OPENPYXL = True
except ImportError:
    HAS_OPENPYXL = False

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent
ENRICHED_DIR = PROJECT_DIR / "data" / "enriched"

LEADS_CSV = ENRICHED_DIR / "top_leads_enriched.csv"
TRACKER_XLSX = ENRICHED_DIR / "research_tracker.xlsx"
DATAZAPP_CSV = ENRICHED_DIR / "datazapp_results.csv"
OUTPUT_CSV = ENRICHED_DIR / "merged_enriched.csv"


def normalize_phone(phone) -> str:
    """Normalize phone to 10 digits."""
    phone = re.sub(r"\D", "", str(phone))
    if len(phone) == 11 and phone.startswith("1"):
        phone = phone[1:]
    return phone if len(phone) == 10 else ""


def load_tracker_results() -> dict:
    """
    Load manual research results from the research tracker Excel.
    Returns dict: owner_name → {phone, email, source, notes}
    """
    if not TRACKER_XLSX.exists() or not HAS_OPENPYXL:
        return {}

    print("  Loading research_tracker.xlsx...")
    wb = load_workbook(TRACKER_XLSX, data_only=True)
    ws = wb.active

    results = {}
    for row in ws.iter_rows(min_row=2, values_only=False):
        # Columns: Rank, Score, LLC/Owner, Resolved Person, Properties,
        #          Portfolio Value, Mailing Address, Existing Phone, Existing Email,
        #          TPS Link, FPS Link, LinkedIn, FOUND:Phone, FOUND:Email, FOUND:Source, Notes
        if len(row) < 16:
            continue

        owner = str(row[2].value or "").strip()
        found_phone = normalize_phone(row[12].value or "")
        found_email = str(row[13].value or "").strip()
        found_source = str(row[14].value or "").strip()
        notes = str(row[15].value or "").strip()

        if owner and (found_phone or found_email):
            results[owner.upper()] = {
                "phone": found_phone,
                "email": found_email,
                "source": found_source or "manual_research",
                "notes": notes,
            }

    print(f"  Found {len(results)} manual research results.")
    return results


def load_datazapp_results() -> dict:
    """
    Load Datazapp skip trace results.
    Returns dict: (first+last+zip) → {phone, email}

    Datazapp output columns vary but typically include:
    First Name, Last Name, Address, City, State, Zip,
    Cell Phone, Landline, Email
    """
    if not DATAZAPP_CSV.exists():
        return {}

    print("  Loading datazapp_results.csv...")
    dz = pd.read_csv(DATAZAPP_CSV, dtype=str)

    # Normalize column names (Datazapp output varies)
    col_map = {}
    for col in dz.columns:
        cl = col.lower().strip()
        if "first" in cl and "name" in cl:
            col_map[col] = "first_name"
        elif "last" in cl and "name" in cl:
            col_map[col] = "last_name"
        elif "cell" in cl or ("phone" in cl and "land" not in cl):
            col_map[col] = "cell_phone"
        elif "land" in cl:
            col_map[col] = "landline"
        elif "email" in cl:
            col_map[col] = "email"
        elif "zip" in cl:
            col_map[col] = "zip"
    dz = dz.rename(columns=col_map)

    results = {}
    for _, row in dz.iterrows():
        first = str(row.get("first_name", "")).strip().upper()
        last = str(row.get("last_name", "")).strip().upper()
        zipcode = str(row.get("zip", "")).strip()[:5]

        key = f"{first}|{last}|{zipcode}"

        phone = normalize_phone(row.get("cell_phone", ""))
        if not phone:
            phone = normalize_phone(row.get("landline", ""))
        email = str(row.get("email", "")).strip()
        if email.upper() in ("NAN", "NONE", ""):
            email = ""

        if phone or email:
            results[key] = {
                "phone": phone,
                "phone_type": "mobile" if normalize_phone(row.get("cell_phone", "")) else "landline",
                "email": email,
                "source": "datazapp",
            }

    print(f"  Found {len(results)} Datazapp matches.")
    return results


def main():
    if not LEADS_CSV.exists():
        print(f"\nBase enriched file not found: {LEADS_CSV}")
        print("Run script 05 first: python scripts/05_enrich_contacts.py --limit 25")
        return

    print("\n  Merging enrichment sources...\n")

    # Load base data
    df = pd.read_csv(LEADS_CSV, dtype=str)
    print(f"  Base records: {len(df):,}")

    # Ensure contact columns exist
    for col in ["phone_1", "phone_1_source", "phone_1_type",
                 "phone_2", "phone_2_source", "phone_2_type",
                 "email_1", "email_1_source", "email_2", "email_2_source",
                 "enrichment_sources"]:
        if col not in df.columns:
            df[col] = ""

    # Pre-fill from existing phone/email columns
    for idx, row in df.iterrows():
        existing_phone = str(row.get("phone", "")).strip()
        if existing_phone and existing_phone.upper() not in ("NAN", "NONE", ""):
            df.at[idx, "phone_1"] = normalize_phone(existing_phone)
            df.at[idx, "phone_1_source"] = str(row.get("enrichment_source", "existing"))

        existing_email = str(row.get("email", "")).strip()
        if existing_email and existing_email.upper() not in ("NAN", "NONE", "") and "@" in existing_email:
            df.at[idx, "email_1"] = existing_email
            df.at[idx, "email_1_source"] = str(row.get("enrichment_source", "existing"))

    # Merge manual research results
    tracker_results = load_tracker_results()
    tracker_merged = 0
    for idx, row in df.iterrows():
        owner = str(row.get("OWN_NAME", "")).strip().upper()
        if owner in tracker_results:
            res = tracker_results[owner]
            if res["phone"] and not df.at[idx, "phone_1"]:
                df.at[idx, "phone_1"] = res["phone"]
                df.at[idx, "phone_1_source"] = res["source"]
            elif res["phone"]:
                df.at[idx, "phone_2"] = res["phone"]
                df.at[idx, "phone_2_source"] = res["source"]

            if res["email"] and not df.at[idx, "email_1"]:
                df.at[idx, "email_1"] = res["email"]
                df.at[idx, "email_1_source"] = res["source"]
            elif res["email"]:
                df.at[idx, "email_2"] = res["email"]
                df.at[idx, "email_2_source"] = res["source"]

            tracker_merged += 1

    if tracker_merged:
        print(f"  Merged {tracker_merged} manual research results.")

    # Merge Datazapp results
    datazapp_results = load_datazapp_results()
    dz_merged = 0
    if datazapp_results:
        for idx, row in df.iterrows():
            # Build lookup key from resolved person or owner name
            resolved = str(row.get("resolved_person", "")).strip()
            owner = str(row.get("OWN_NAME", "")).strip()
            zipcode = str(row.get("OWN_ZIPCD", "")).strip()[:5]

            # Try resolved person first
            person_name = resolved if resolved.upper() not in ("", "NAN", "NONE") else owner
            if "," in person_name:
                parts = person_name.split(",", 1)
                last = parts[0].strip().upper()
                first = parts[1].strip().split()[0].upper() if len(parts) > 1 else ""
            else:
                parts = person_name.split()
                first = parts[0].upper() if parts else ""
                last = parts[-1].upper() if len(parts) >= 2 else ""

            key = f"{first}|{last}|{zipcode}"
            if key in datazapp_results:
                res = datazapp_results[key]
                if res["phone"] and not df.at[idx, "phone_1"]:
                    df.at[idx, "phone_1"] = res["phone"]
                    df.at[idx, "phone_1_source"] = "datazapp"
                    df.at[idx, "phone_1_type"] = res.get("phone_type", "")
                elif res["phone"]:
                    df.at[idx, "phone_2"] = res["phone"]
                    df.at[idx, "phone_2_source"] = "datazapp"
                    df.at[idx, "phone_2_type"] = res.get("phone_type", "")

                if res["email"] and not df.at[idx, "email_1"]:
                    df.at[idx, "email_1"] = res["email"]
                    df.at[idx, "email_1_source"] = "datazapp"
                elif res["email"]:
                    df.at[idx, "email_2"] = res["email"]
                    df.at[idx, "email_2_source"] = "datazapp"

                dz_merged += 1

        print(f"  Merged {dz_merged} Datazapp results.")

    # Build enrichment_sources summary
    for idx, row in df.iterrows():
        sources = set()
        for src_col in ["phone_1_source", "phone_2_source", "email_1_source", "email_2_source"]:
            val = str(row.get(src_col, "")).strip()
            if val and val.upper() not in ("NAN", "NONE", ""):
                sources.add(val)
        df.at[idx, "enrichment_sources"] = ", ".join(sorted(sources))

    # Save
    df.to_csv(OUTPUT_CSV, index=False)

    # Summary
    has_phone = df["phone_1"].astype(str).str.len().ge(10).sum()
    has_email = df["email_1"].astype(str).str.contains("@", na=False).sum()
    total = len(df)

    print()
    print("=" * 60)
    print("  MERGE SUMMARY")
    print("=" * 60)
    print(f"  Total records:       {total}")
    print(f"  Has phone:           {has_phone}  ({has_phone/total*100:.0f}%)")
    print(f"  Has email:           {has_email}  ({has_email/total*100:.0f}%)")
    print(f"  From manual:         {tracker_merged}")
    print(f"  From Datazapp:       {dz_merged}")
    print(f"\n  Saved: {OUTPUT_CSV}")
    print()
    print("  NEXT STEPS:")
    print(f"  python scripts/06_validate_contacts.py --county merged")
    print(f"  python scripts/07_export_campaign_ready.py --county merged")
    print()


if __name__ == "__main__":
    main()
