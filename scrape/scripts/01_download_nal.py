"""
Step 1: Download Florida Property Data
=======================================

Downloads property owner records from Florida county property appraiser sites.
These are PUBLIC RECORDS under Florida Statute 119 — legal and free.

Two data source types:
  A) FL Dept of Revenue NAL files (statewide, covers all 67 counties)
  B) Individual county bulk downloads (some counties offer free CSV/Excel)

Usage:
    python scripts/01_download_nal.py --county seminole
    python scripts/01_download_nal.py --county sarasota
    python scripts/01_download_nal.py --county all
    python scripts/01_download_nal.py --county nal   (prints NAL request instructions)
"""

import argparse
import json
import os
import sys
import time
import zipfile
from pathlib import Path

import requests

# ---------------------------------------------------------------------------
# Paths — everything is relative to the scrape/ project root
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent          # scrape/scripts/
PROJECT_DIR = SCRIPT_DIR.parent                        # scrape/
CONFIG_FILE = PROJECT_DIR / "config" / "counties.json"
RAW_DIR = PROJECT_DIR / "data" / "raw"

# ---------------------------------------------------------------------------
# FDOR NAL — statewide download from Florida Revenue
# ---------------------------------------------------------------------------
# URL pattern for the FDOR data portal (2025 Final tax roll)
FDOR_BASE_URL = (
    "https://floridarevenue.com/property/dataportal/Documents/"
    "PTO%20Data%20Portal/Tax%20Roll%20Data%20Files/NAL/2025F/"
)

# Florida county names → FDOR county codes (alphabetical order, 01-67)
FL_COUNTIES = {
    "alachua": "01", "baker": "02", "bay": "03", "bradford": "04",
    "brevard": "05", "broward": "06", "calhoun": "07", "charlotte": "08",
    "citrus": "09", "clay": "10", "collier": "11", "columbia": "12",
    "desoto": "13", "dixie": "14", "duval": "16", "escambia": "17",
    "flagler": "18", "franklin": "19", "gadsden": "20", "gilchrist": "21",
    "glades": "22", "gulf": "23", "hamilton": "24", "hardee": "25",
    "hendry": "26", "hernando": "27", "highlands": "28", "hillsborough": "29",
    "holmes": "30", "indian river": "31", "jackson": "32", "jefferson": "33",
    "lafayette": "34", "lake": "35", "lee": "36", "leon": "37",
    "levy": "38", "liberty": "39", "madison": "40", "manatee": "41",
    "marion": "42", "martin": "43", "miami-dade": "13", "monroe": "44",
    "nassau": "45", "okaloosa": "46", "okeechobee": "47", "orange": "48",
    "osceola": "49", "palm beach": "50", "pasco": "51", "pinellas": "52",
    "polk": "53", "putnam": "54", "santa rosa": "57", "sarasota": "58",
    "seminole": "59", "st. johns": "55", "st. lucie": "56",
    "sumter": "60", "suwannee": "61", "taylor": "62", "union": "63",
    "volusia": "64", "wakulla": "65", "walton": "66", "washington": "67",
}


def load_county_config():
    """Load county data sources from config/counties.json."""
    with open(CONFIG_FILE) as f:
        return json.load(f)


def print_nal_instructions():
    """Print instructions for requesting statewide NAL files from FDOR."""
    print()
    print("=" * 70)
    print("  HOW TO GET THE FL DEPT OF REVENUE NAL FILES (FREE)")
    print("=" * 70)
    print()
    print("  The NAL (Name-Address-Legal) files are the gold standard —")
    print("  they cover ALL 67 Florida counties in one dataset.")
    print()
    print("  OPTION A: Download directly from the FDOR data portal")
    print("  -------------------------------------------------------")
    print("  URL: https://floridarevenue.com/property/dataportal/")
    print("  Look for: Tax Roll Data Files > NAL > 2025F")
    print("  Each county is a separate ZIP file containing a CSV.")
    print()
    print("  OPTION B: Email request (for bulk / FTP access)")
    print("  -------------------------------------------------------")
    print("  Email: PTOTechnology@floridarevenue.com")
    print("  Subject: Request for 2025 Final NAL Files")
    print("  Body: 'I am requesting the most recent NAL files for")
    print("         [county name or ALL counties]. Please provide")
    print("         download links or FTP access.'")
    print()
    print("  Files under 10MB will be emailed directly.")
    print("  Larger files get FTP access.")
    print()
    print("  Once you have the files, place them in:")
    print(f"    {RAW_DIR}/")
    print("  Then run Step 2 (02_parse_nal.py) to process them.")
    print("=" * 70)
    print()


def download_fdor_nal(county_name: str):
    """
    Try to download a county's NAL ZIP from the FDOR data portal.
    Saves the extracted CSV to data/raw/{county_name}_raw.csv.
    """
    code = FL_COUNTIES.get(county_name.lower())
    if not code:
        print(f"  ERROR: Unknown county '{county_name}'.")
        print(f"  Known counties: {', '.join(sorted(FL_COUNTIES.keys()))}")
        return False

    output_csv = RAW_DIR / f"{county_name.lower().replace(' ', '_')}_raw.csv"

    # Skip if already downloaded
    if output_csv.exists():
        size_mb = output_csv.stat().st_size / (1024 * 1024)
        print(f"  Already downloaded: {output_csv.name} ({size_mb:.1f} MB)")
        return True

    # The FDOR portal uses this naming pattern (may need adjustment)
    # Example: "Palm Beach 50 Final NAL 2025.zip"
    title_name = county_name.replace("-", " ").title()
    zip_filename = f"{title_name} {code} Final NAL 2025.zip"
    url = FDOR_BASE_URL + zip_filename.replace(" ", "%20")

    print(f"  Trying FDOR download: {zip_filename}")
    try:
        resp = requests.get(url, timeout=120, stream=True)
        if resp.status_code != 200:
            print(f"  FDOR download returned status {resp.status_code}.")
            print(f"  The file may not be available at this URL.")
            print(f"  Try downloading manually from the FDOR data portal,")
            print(f"  or run: python scripts/01_download_nal.py --county nal")
            return False
    except requests.RequestException as e:
        print(f"  Download error: {e}")
        return False

    # Save the ZIP
    zip_path = RAW_DIR / zip_filename.replace(" ", "_")
    total_size = int(resp.headers.get("content-length", 0))
    downloaded = 0

    with open(zip_path, "wb") as f:
        for chunk in resp.iter_content(chunk_size=8192):
            f.write(chunk)
            downloaded += len(chunk)
            if total_size > 0:
                pct = downloaded / total_size * 100
                print(f"\r  Downloading... {pct:.0f}%", end="", flush=True)

    print(f"\r  Downloaded: {zip_path.name}                ")

    # Extract CSV from the ZIP
    try:
        with zipfile.ZipFile(zip_path, "r") as z:
            csv_files = [
                f for f in z.namelist()
                if f.lower().endswith(".csv") or f.lower().endswith(".txt")
            ]
            if not csv_files:
                print(f"  WARNING: No CSV/TXT found in ZIP. Files: {z.namelist()}")
                return False

            print(f"  Extracting: {csv_files[0]}")
            z.extract(csv_files[0], RAW_DIR)
            extracted = RAW_DIR / csv_files[0]
            extracted.rename(output_csv)
    except zipfile.BadZipFile:
        print(f"  ERROR: Downloaded file is not a valid ZIP.")
        zip_path.unlink(missing_ok=True)
        return False

    # Clean up ZIP to save disk space
    zip_path.unlink(missing_ok=True)

    size_mb = output_csv.stat().st_size / (1024 * 1024)
    print(f"  Saved: {output_csv.name} ({size_mb:.1f} MB)")
    return True


def download_county_direct(county_info: dict):
    """
    For counties with free bulk downloads, print instructions on how
    to download manually. (Each county's portal works differently, so
    fully automated download would require per-county scraping logic.)
    """
    name = county_info["name"]
    url = county_info["url"]
    fmt = county_info.get("format", "unknown")
    notes = county_info.get("notes", "")

    output_csv = RAW_DIR / f"{name.lower().replace('-', '_')}_raw.csv"

    if output_csv.exists():
        size_mb = output_csv.stat().st_size / (1024 * 1024)
        print(f"  Already have: {output_csv.name} ({size_mb:.1f} MB)")
        return True

    print()
    print(f"  COUNTY: {name.upper()}")
    print(f"  Format: {fmt}")
    print(f"  URL:    {url}")
    if notes:
        print(f"  Notes:  {notes}")
    print()
    print(f"  >> Download the property data file from the URL above.")
    print(f"  >> Save it as: {output_csv}")
    print(f"  >> Then run Step 2 to parse it.")
    print()

    return False


def main():
    parser = argparse.ArgumentParser(
        description="Download Florida property owner data (Step 1)"
    )
    parser.add_argument(
        "--county",
        type=str,
        required=True,
        help=(
            'County name (e.g. "seminole", "palm beach"), '
            '"all" for all counties, '
            '"nal" for NAL file request instructions'
        ),
    )
    args = parser.parse_args()

    RAW_DIR.mkdir(parents=True, exist_ok=True)

    county_arg = args.county.strip().lower()

    # ---------------------------------------------------------------
    # Special case: just print NAL request instructions
    # ---------------------------------------------------------------
    if county_arg == "nal":
        print_nal_instructions()
        return

    # ---------------------------------------------------------------
    # Load config for county-specific download info
    # ---------------------------------------------------------------
    config = load_county_config()

    # Build lookup: county name → county info dict
    county_lookup = {}
    for c in config.get("priority_counties", []) + config.get("additional_bulk_counties", []):
        county_lookup[c["name"].lower()] = c

    # ---------------------------------------------------------------
    # Determine which counties to process
    # ---------------------------------------------------------------
    if county_arg == "all":
        target_counties = list(FL_COUNTIES.keys())
    else:
        target_counties = [county_arg]

    print(f"\nProcessing {len(target_counties)} county(ies)...\n")

    success_count = 0
    manual_count = 0

    for county_name in target_counties:
        print("-" * 50)
        print(f"County: {county_name.upper()}")
        print("-" * 50)

        county_info = county_lookup.get(county_name.replace(" ", "-"))
        if not county_info:
            county_info = county_lookup.get(county_name)

        # Step A: Try FDOR NAL download (works for any county)
        if download_fdor_nal(county_name):
            success_count += 1
            continue

        # Step B: If county has a known bulk download, show instructions
        if county_info and county_info.get("bulk_download"):
            download_county_direct(county_info)
            manual_count += 1
            continue

        # Step C: County requires scraping or purchase
        if county_info:
            cost = county_info.get("cost", "free")
            notes = county_info.get("notes", "")
            print(f"  This county requires manual download or scraping.")
            print(f"  URL: {county_info['url']}")
            print(f"  Cost: {cost}")
            if notes:
                print(f"  Notes: {notes}")
        else:
            print(f"  No download source configured for this county.")
            print(f"  Try the FDOR NAL file instead:")
            print(f"    python scripts/01_download_nal.py --county nal")

        print()

    # ---------------------------------------------------------------
    # Summary
    # ---------------------------------------------------------------
    print("\n" + "=" * 50)
    print("DOWNLOAD SUMMARY")
    print("=" * 50)
    print(f"  Downloaded automatically: {success_count}")
    print(f"  Need manual download:     {manual_count}")
    print(f"  Total requested:          {len(target_counties)}")
    if success_count > 0:
        print(f"\n  Next step: python scripts/02_parse_nal.py --county {county_arg}")
    print()


if __name__ == "__main__":
    main()
