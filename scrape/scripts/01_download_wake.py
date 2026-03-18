"""
Step 1: Download Wake County, NC Property Data
================================================

Downloads property records from Wake County Tax Administration.
These are PUBLIC RECORDS — free, daily-updated XLSX files.

Source: https://services.wake.gov/realdata_extracts/
Format: XLSX (171 MB) or ZIP (42 MB fixed-width text)

We download the XLSX because it has column headers and loads
directly into pandas. The ZIP contains a headerless fixed-width
text file that requires a record layout document to parse.

Also downloads the Qualified Sales file (24 months of arms-length
transactions) for supplemental sale price data.

Usage:
    python scripts/01_download_wake.py
    python scripts/01_download_wake.py --date 03172026
    python scripts/01_download_wake.py --skip-sales
"""

import argparse
import re
import sys
from datetime import datetime
from pathlib import Path

import requests

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent
RAW_DIR = PROJECT_DIR / "data" / "raw"

# ---------------------------------------------------------------------------
# Wake County data URLs
# ---------------------------------------------------------------------------
BASE_URL = "https://services.wake.gov/realdata_extracts/"
SALES_FILE = "Qualified_Sales_Past_24Months.xlsx"


def find_current_filename():
    """
    Scrape the Wake County directory listing to find today's
    RealEstData file. The filename includes the current date
    (e.g., RealEstData03172026.xlsx).
    """
    print("  Checking Wake County data portal for current file...")
    try:
        resp = requests.get(BASE_URL, timeout=30)
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"  ERROR fetching directory: {e}")
        return None

    # Find the XLSX filename
    matches = re.findall(r'(RealEstData\d{8}\.xlsx)', resp.text)
    if matches:
        filename = matches[-1]  # Take the most recent
        print(f"  Found: {filename}")
        return filename

    print("  WARNING: Could not find RealEstData*.xlsx in directory listing")
    return None


def download_file(url: str, output_path: Path, description: str) -> bool:
    """Download a file with progress reporting."""
    if output_path.exists():
        size_mb = output_path.stat().st_size / (1024 * 1024)
        print(f"  Already downloaded: {output_path.name} ({size_mb:.1f} MB)")
        return True

    print(f"  Downloading {description}...")
    print(f"  URL: {url}")

    try:
        resp = requests.get(url, timeout=600, stream=True)
        if resp.status_code != 200:
            print(f"  ERROR: HTTP {resp.status_code}")
            return False
    except requests.RequestException as e:
        print(f"  ERROR: {e}")
        return False

    total_size = int(resp.headers.get("content-length", 0))
    downloaded = 0

    with open(output_path, "wb") as f:
        for chunk in resp.iter_content(chunk_size=65536):
            f.write(chunk)
            downloaded += len(chunk)
            if total_size > 0:
                pct = downloaded / total_size * 100
                mb = downloaded / (1024 * 1024)
                print(f"\r  {mb:.0f} MB ({pct:.0f}%)", end="", flush=True)
            elif downloaded % (5 * 1024 * 1024) < 65536:
                mb = downloaded / (1024 * 1024)
                print(f"\r  {mb:.0f} MB", end="", flush=True)

    size_mb = output_path.stat().st_size / (1024 * 1024)
    print(f"\r  Downloaded: {output_path.name} ({size_mb:.1f} MB)          ")
    return True


def main():
    parser = argparse.ArgumentParser(
        description="Download Wake County NC property data (Step 1)"
    )
    parser.add_argument(
        "--date",
        type=str,
        default=None,
        help='Date string for filename (MMDDYYYY). Auto-detected if omitted.'
    )
    parser.add_argument(
        "--skip-sales",
        action="store_true",
        help="Skip downloading the Qualified Sales file"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-download even if files exist"
    )
    args = parser.parse_args()

    RAW_DIR.mkdir(parents=True, exist_ok=True)

    print()
    print("=" * 60)
    print("  WAKE COUNTY, NC — PROPERTY DATA DOWNLOAD")
    print("=" * 60)
    print()

    # -----------------------------------------------------------------
    # 1. Download main property data (XLSX)
    # -----------------------------------------------------------------
    if args.date:
        xlsx_filename = f"RealEstData{args.date}.xlsx"
    else:
        xlsx_filename = find_current_filename()
        if not xlsx_filename:
            # Fallback: construct from today's date
            today = datetime.now().strftime("%m%d%Y")
            xlsx_filename = f"RealEstData{today}.xlsx"
            print(f"  Falling back to today's date: {xlsx_filename}")

    xlsx_url = BASE_URL + xlsx_filename
    xlsx_output = RAW_DIR / "wake_county_raw.xlsx"

    if args.force and xlsx_output.exists():
        xlsx_output.unlink()

    success = download_file(xlsx_url, xlsx_output, f"Wake County property data ({xlsx_filename})")

    if not success:
        print()
        print("  Download failed. Try manually:")
        print(f"  1. Go to {BASE_URL}")
        print(f"  2. Download the latest RealEstData*.xlsx file")
        print(f"  3. Save it as: {xlsx_output}")
        print()
        return

    # -----------------------------------------------------------------
    # 2. Download qualified sales data (supplemental)
    # -----------------------------------------------------------------
    if not args.skip_sales:
        print()
        sales_url = BASE_URL + SALES_FILE
        sales_output = RAW_DIR / "wake_county_sales_24mo.xlsx"

        if args.force and sales_output.exists():
            sales_output.unlink()

        download_file(sales_url, sales_output, "Qualified Sales (24 months)")

    # -----------------------------------------------------------------
    # Summary
    # -----------------------------------------------------------------
    print()
    print("=" * 60)
    print("  DOWNLOAD COMPLETE")
    print("=" * 60)
    print(f"  Property data: {xlsx_output}")
    if not args.skip_sales:
        print(f"  Sales data:    {RAW_DIR / 'wake_county_sales_24mo.xlsx'}")
    print()
    print("  Next step:")
    print("    python scripts/02_parse_wake.py")
    print()


if __name__ == "__main__":
    main()
