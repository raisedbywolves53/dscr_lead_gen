"""
NC Step 1: Download North Carolina Parcel Data
================================================

Downloads property parcel records from NC OneMap (statewide parcel database).
This is the NC equivalent of Florida's FDOR NAL files.

Source: NC OneMap ArcGIS FeatureServer
URL:    https://services.nconemap.gov/secure/rest/services/NC1Map_Parcels/FeatureServer/1
Cost:   Free
Format: JSON → CSV

Downloads are paginated (5,000 records per request). The script handles
pagination automatically and saves raw CSV to data/raw/.

County FIPS codes:
  Wake (Raleigh):        183
  Mecklenburg (Charlotte): 119

Usage:
    python scripts/nc_01_download_parcels.py --county wake
    python scripts/nc_01_download_parcels.py --county mecklenburg
    python scripts/nc_01_download_parcels.py --county wake,mecklenburg
"""

import argparse
import sys
import time
from pathlib import Path

import pandas as pd
import requests

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent
RAW_DIR = PROJECT_DIR / "data" / "raw"

# ---------------------------------------------------------------------------
# NC OneMap ArcGIS FeatureServer endpoint
# ---------------------------------------------------------------------------
FEATURE_SERVER_URL = (
    "https://services.nconemap.gov/secure/rest/services/"
    "NC1Map_Parcels/FeatureServer/1/query"
)

# Records per API request (max allowed by ArcGIS is typically 5000)
PAGE_SIZE = 5000

# Delay between API requests (seconds) — be polite
REQUEST_DELAY = 1.0

# ---------------------------------------------------------------------------
# NC county name → FIPS code mapping (3-digit string)
# Phase 1 targets + common expansion counties
# ---------------------------------------------------------------------------
NC_COUNTIES = {
    "wake":         "183",   # Raleigh
    "mecklenburg":  "119",   # Charlotte
    "durham":       "063",   # Durham
    "guilford":     "081",   # Greensboro
    "forsyth":      "067",   # Winston-Salem
    "buncombe":     "021",   # Asheville
    "new hanover":  "129",   # Wilmington
    "dare":         "055",   # Outer Banks
    "cumberland":   "051",   # Fayetteville
    "union":        "179",   # Monroe (Charlotte suburb)
    "cabarrus":     "025",   # Concord (Charlotte suburb)
    "iredell":      "097",   # Statesville (Charlotte area)
    "gaston":       "071",   # Gastonia (Charlotte area)
    "johnston":     "101",   # Smithfield (Raleigh suburb)
    "orange":       "135",   # Chapel Hill
}

# Fields we care about from NC OneMap (reduces payload size)
# Using * for now to get everything, but can restrict later
FIELDS_TO_FETCH = [
    "parno", "altparno", "ownname", "ownfrst", "ownlast", "ownname2", "owntype",
    "mailadd", "munit", "mcity", "mstate", "mzip",
    "maddpref", "maddrno", "maddstname", "maddstr", "maddstsuf", "maddsttyp",
    "siteadd", "sunit", "scity", "sstate", "szip",
    "saddno", "saddpref", "saddstname", "saddstr", "saddstsuf", "saddsttyp",
    "cntyname", "cntyfips",
    "parval", "landval", "improvval", "presentval", "parvaltype",
    "parusecode", "parusedesc",
    "saledate", "saledatetx",
    "gisacres", "struct", "structno", "structyear",
    "subdivisio", "legdecfull",
]


def download_county(county_name: str, fips_code: str) -> bool:
    """
    Download all parcels for a single NC county via the OneMap API.
    Handles pagination automatically. Saves to data/raw/{county}_raw.csv.
    """
    output_csv = RAW_DIR / f"{county_name.lower().replace(' ', '_')}_raw.csv"

    # Skip if already downloaded
    if output_csv.exists():
        size_mb = output_csv.stat().st_size / (1024 * 1024)
        print(f"  Already downloaded: {output_csv.name} ({size_mb:.1f} MB)")
        return True

    print(f"\n  Downloading {county_name.title()} County (FIPS {fips_code})...")
    print(f"  Source: NC OneMap FeatureServer")
    print(f"  Page size: {PAGE_SIZE} records per request")

    all_records = []
    offset = 0
    page = 0

    while True:
        page += 1
        params = {
            "where": f"cntyfips='{fips_code}'",
            "outFields": ",".join(FIELDS_TO_FETCH),
            "returnGeometry": "false",
            "resultOffset": offset,
            "resultRecordCount": PAGE_SIZE,
            "f": "json",
        }

        try:
            resp = requests.get(FEATURE_SERVER_URL, params=params, timeout=120)
            resp.raise_for_status()
        except requests.RequestException as e:
            print(f"\n  ERROR on page {page}: {e}")
            if all_records:
                print(f"  Saving {len(all_records)} records collected so far...")
                break
            return False

        data = resp.json()

        # Check for API errors
        if "error" in data:
            print(f"\n  API ERROR: {data['error']}")
            if all_records:
                print(f"  Saving {len(all_records)} records collected so far...")
                break
            return False

        features = data.get("features", [])
        if not features:
            break

        # Extract attribute dicts from features
        records = [f["attributes"] for f in features]
        all_records.extend(records)

        print(f"\r  Page {page}: fetched {len(features)} records "
              f"(total: {len(all_records):,})", end="", flush=True)

        # Check if there are more records
        if not data.get("exceededTransferLimit", False):
            break

        offset += PAGE_SIZE
        time.sleep(REQUEST_DELAY)

    print()  # newline after progress

    if not all_records:
        print(f"  WARNING: No records found for {county_name} (FIPS {fips_code}).")
        print(f"  The FIPS code may be wrong or the data may not be available.")
        return False

    # Convert to DataFrame and save
    df = pd.DataFrame(all_records)

    # Clean up null values from JSON
    df = df.where(df.notna(), "")

    df.to_csv(output_csv, index=False)
    size_mb = output_csv.stat().st_size / (1024 * 1024)

    print(f"  SAVED: {output_csv.name}")
    print(f"    Records: {len(df):,}")
    print(f"    Columns: {len(df.columns)}")
    print(f"    Size:    {size_mb:.1f} MB")

    return True


def main():
    parser = argparse.ArgumentParser(
        description="Download NC property parcel data from NC OneMap (NC Step 1)"
    )
    parser.add_argument(
        "--county",
        type=str,
        required=True,
        help=(
            'County name(s), comma-separated (e.g. "wake", "wake,mecklenburg"). '
            'Use "all" for all configured counties, "list" to show available counties.'
        ),
    )
    args = parser.parse_args()

    RAW_DIR.mkdir(parents=True, exist_ok=True)

    county_arg = args.county.strip().lower()

    # Show available counties
    if county_arg == "list":
        print("\nAvailable NC counties:")
        for name, fips in sorted(NC_COUNTIES.items()):
            print(f"  {name:20s}  FIPS: {fips}")
        print(f"\nTotal: {len(NC_COUNTIES)} counties configured")
        return

    # Determine which counties to process
    if county_arg == "all":
        targets = list(NC_COUNTIES.items())
    else:
        targets = []
        for name in county_arg.split(","):
            name = name.strip()
            if name in NC_COUNTIES:
                targets.append((name, NC_COUNTIES[name]))
            else:
                print(f"  WARNING: Unknown county '{name}'. Skipping.")
                print(f"  Run with --county list to see available counties.")

    if not targets:
        print("No valid counties specified.")
        sys.exit(1)

    print(f"\nDownloading {len(targets)} county(ies) from NC OneMap...\n")

    success = 0
    failed = 0

    for county_name, fips_code in targets:
        print("-" * 50)
        print(f"County: {county_name.upper()} (FIPS {fips_code})")
        print("-" * 50)

        if download_county(county_name, fips_code):
            success += 1
        else:
            failed += 1

    # Summary
    print("\n" + "=" * 50)
    print("DOWNLOAD SUMMARY")
    print("=" * 50)
    print(f"  Successful: {success}")
    print(f"  Failed:     {failed}")
    print(f"  Total:      {len(targets)}")

    if success > 0:
        county_names = ",".join(name for name, _ in targets)
        print(f"\n  Next step: python scripts/nc_02_parse_parcels.py --county {county_names}")
    print()


if __name__ == "__main__":
    main()
