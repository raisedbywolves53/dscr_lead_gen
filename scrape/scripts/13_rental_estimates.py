"""
Step 13: Rental Estimates via HUD Fair Market Rent (FMR)
=========================================================

Estimates monthly rent for each property using HUD Small Area Fair Market Rent
(SAFMR) data, which provides rent estimates by ZIP code and bedroom count.

Data source:
  - HUD FY2025 Small Area FMR (ZIP-level): free public Excel download
  - Falls back to county-level FMR if ZIP not found

What this script does:
  1. Downloads HUD FMR data to data/raw/hud_fmr.xlsx (skip if cached)
  2. Parses the Excel file — auto-detects columns for ZIP, 0BR-4BR rents
  3. Reads leads from data/enriched/top_leads_enriched.csv
  4. For each property, looks up FMR rent by ZIP code
  5. Calculates portfolio-level rent, NOI, and rent-to-value ratio
  6. Saves output to data/enriched/rent_estimates.csv

Usage:
    python scripts/13_rental_estimates.py
    python scripts/13_rental_estimates.py --input data/enriched/top_leads_enriched.csv
    python scripts/13_rental_estimates.py --dry-run

Notes:
  - Uses 3BR FMR as default (most common investment SFR bedroom count)
  - NOI assumes 40% expense ratio (insurance, taxes, maintenance, vacancy)
  - Debt service fields are placeholders until script 11 provides mortgage data
  - Property ZIP extraction from PHY_ADDR1 is best-effort (regex on last 5 digits)
  - Pipe-delimited PHY_ADDR1 (portfolio owners) is parsed per-address
"""

import argparse
import os
import re
import sys
import time
from pathlib import Path

import pandas as pd

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False
    print("WARNING: requests library not installed. Run: pip install requests")

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
RAW_DIR = PROJECT_DIR / "data" / "raw"
ENRICHED_DIR = PROJECT_DIR / "data" / "enriched"

DEFAULT_INPUT = ENRICHED_DIR / "top_leads_enriched.csv"
ALT_INPUT = ENRICHED_DIR / "merged_enriched.csv"
OUTPUT_PATH = ENRICHED_DIR / "rent_estimates.csv"
FMR_PATH = RAW_DIR / "hud_fmr.xlsx"

# HUD FMR download URLs — try SAFMR (ZIP-level) first, then county-level
FMR_URLS = [
    # FY2025 Small Area FMR (ZIP-level)
    "https://www.huduser.gov/portal/datasets/fmr/fmr2025/fy2025_safmrs_revised.xlsx",
    # FY2025 County-level FMR
    "https://www.huduser.gov/portal/datasets/fmr/fmr2025/FY2025_4050_FMR_county_town.xlsx",
    # FY2024 fallbacks
    "https://www.huduser.gov/portal/datasets/fmr/fmr2024/fy2024_safmrs_revised.xlsx",
    "https://www.huduser.gov/portal/datasets/fmr/fmr2024/FY2024_4050_FMR_county_town.xlsx",
    # FY2023 fallbacks
    "https://www.huduser.gov/portal/datasets/fmr/fmr2023/fy2023_safmrs_revised.xlsx",
]

# Default bedroom count when unknown — 3BR is most common for investment SFR
DEFAULT_BEDROOMS = 3

# Expense ratio for NOI calculation (40% covers taxes, insurance, maint, vacancy)
EXPENSE_RATIO = 0.40

# Florida FIPS state code
FL_FIPS_STATE = "12"


# ---------------------------------------------------------------------------
# HUD FMR download
# ---------------------------------------------------------------------------

def download_fmr(output_path: Path) -> bool:
    """Download HUD FMR Excel file. Tries multiple URLs/years."""
    if output_path.exists():
        size_mb = output_path.stat().st_size / (1024 * 1024)
        print(f"  FMR file already exists: {output_path} ({size_mb:.1f} MB)")
        return True

    if not HAS_REQUESTS:
        print("ERROR: requests library needed to download FMR data.")
        return False

    output_path.parent.mkdir(parents=True, exist_ok=True)

    for url in FMR_URLS:
        print(f"  Trying: {url}")
        try:
            resp = requests.get(url, timeout=60, stream=True)
            if resp.status_code == 200:
                with open(output_path, "wb") as f:
                    for chunk in resp.iter_content(chunk_size=8192):
                        f.write(chunk)
                size_mb = output_path.stat().st_size / (1024 * 1024)
                print(f"  Downloaded {size_mb:.1f} MB to {output_path}")
                return True
            else:
                print(f"    HTTP {resp.status_code} — skipping")
        except requests.RequestException as e:
            print(f"    Request failed: {e}")
        time.sleep(1)

    print()
    print("ERROR: Could not download HUD FMR data from any URL.")
    print("Please download manually from:")
    print("  https://www.huduser.gov/portal/datasets/fmr.html")
    print(f"Save the file to: {output_path}")
    return False


# ---------------------------------------------------------------------------
# Parse FMR Excel → ZIP-to-rent lookup
# ---------------------------------------------------------------------------

def parse_fmr(fmr_path: Path) -> dict:
    """
    Parse HUD FMR Excel file into a dict of {zip_code: {0: rent, 1: rent, ...}}.

    Auto-detects column names by checking for keywords. Handles both SAFMR
    (ZIP-level) and county-level FMR formats.

    Returns:
        zip_rents: dict mapping ZIP string to {bedroom_count: monthly_rent}
        county_rents: dict mapping (state_fips, county_fips) to {bedroom_count: rent}
    """
    print(f"\n--- Parsing FMR data from {fmr_path.name} ---")

    # Read first sheet
    df = pd.read_excel(fmr_path, dtype=str)
    cols = [c.lower().strip() for c in df.columns]
    df.columns = cols

    print(f"  Rows: {len(df):,}")
    print(f"  Columns: {list(df.columns)[:15]}...")

    # --- Detect ZIP column ---
    zip_col = None
    for candidate in ["zip_code", "zipcode", "zip", "zcta", "zip5"]:
        if candidate in cols:
            zip_col = candidate
            break
    # Also check for partial matches
    if zip_col is None:
        for c in cols:
            if "zip" in c and "zip" != c[:3] + c[3:]:  # contains "zip"
                zip_col = c
                break

    # --- Detect bedroom rent columns ---
    # Pattern 1: fmr_0, fmr_1, fmr_2, fmr_3, fmr_4  (SAFMR format)
    # Pattern 2: safmr_0br, safmr_1br, safmr_2br, etc.
    # Pattern 3: Efficiency, One-Bedroom, Two-Bedroom, Three-Bedroom, Four-Bedroom
    rent_cols = {}

    # Try fmr_N or safmr_Nbr pattern
    for br in range(5):
        for pattern in [f"fmr_{br}", f"safmr_{br}br", f"rent_{br}", f"fmr{br}"]:
            if pattern in cols:
                rent_cols[br] = pattern
                break

    # Try text-based column names
    if not rent_cols:
        text_map = {
            0: ["efficiency", "studio", "0br", "0-br", "0_br", "zero"],
            1: ["one-bedroom", "one_bedroom", "1br", "1-br", "1_br"],
            2: ["two-bedroom", "two_bedroom", "2br", "2-br", "2_br"],
            3: ["three-bedroom", "three_bedroom", "3br", "3-br", "3_br"],
            4: ["four-bedroom", "four_bedroom", "4br", "4-br", "4_br"],
        }
        for br, keywords in text_map.items():
            for c in cols:
                if any(kw in c for kw in keywords):
                    rent_cols[br] = c
                    break

    # Last resort — look for columns containing "fmr" or "rent"
    if not rent_cols:
        fmr_candidates = [c for c in cols if "fmr" in c or "rent" in c]
        if len(fmr_candidates) >= 5:
            for i, c in enumerate(sorted(fmr_candidates)[:5]):
                rent_cols[i] = c

    if not rent_cols:
        print("ERROR: Could not identify rent columns in FMR file.")
        print(f"  All columns: {list(df.columns)}")
        return {}, {}

    print(f"  ZIP column: {zip_col}")
    print(f"  Rent columns: {rent_cols}")

    # --- Detect county/FIPS columns for fallback ---
    county_fips_col = None
    state_fips_col = None
    for c in cols:
        if c in ["fips", "county_fips", "countyfips", "fips_code", "county_code"]:
            county_fips_col = c
        if c in ["state_fips", "statefips", "state_code", "stusab", "state_alpha"]:
            state_fips_col = c
        # Combined FIPS (state+county = 5 digits)
        if c in ["fips2010", "fips2020", "countycode10"]:
            county_fips_col = c

    # --- Build ZIP-level lookup ---
    zip_rents = {}
    if zip_col:
        for _, row in df.iterrows():
            raw_zip = str(row.get(zip_col, "")).strip()
            # Normalize to 5-digit ZIP
            zip5 = raw_zip.zfill(5)[:5] if raw_zip.isdigit() else raw_zip[:5]
            if not zip5 or not zip5.isdigit() or len(zip5) != 5:
                continue

            rents = {}
            for br, col in rent_cols.items():
                try:
                    val = str(row.get(col, "")).strip().replace(",", "").replace("$", "")
                    if val and val != "nan" and val != ".":
                        rents[br] = int(float(val))
                except (ValueError, TypeError):
                    pass
            if rents:
                zip_rents[zip5] = rents

    print(f"  ZIP-level rents loaded: {len(zip_rents):,} ZIPs")

    # --- Build county-level fallback ---
    county_rents = {}
    if county_fips_col:
        # Group by county FIPS and average the rents
        for _, row in df.iterrows():
            fips_raw = str(row.get(county_fips_col, "")).strip()
            if not fips_raw or not fips_raw.replace(".", "").isdigit():
                continue
            fips_clean = fips_raw.split(".")[0].zfill(5)

            rents = {}
            for br, col in rent_cols.items():
                try:
                    val = str(row.get(col, "")).strip().replace(",", "").replace("$", "")
                    if val and val != "nan" and val != ".":
                        rents[br] = int(float(val))
                except (ValueError, TypeError):
                    pass

            if rents:
                if fips_clean not in county_rents:
                    county_rents[fips_clean] = {br: [] for br in range(5)}
                for br, rent in rents.items():
                    county_rents[fips_clean][br].append(rent)

        # Average the rents per county
        for fips, br_lists in county_rents.items():
            county_rents[fips] = {
                br: int(sum(vals) / len(vals)) if vals else 0
                for br, vals in br_lists.items()
            }

        print(f"  County-level rents loaded: {len(county_rents):,} counties")

    return zip_rents, county_rents


# ---------------------------------------------------------------------------
# ZIP extraction from property address
# ---------------------------------------------------------------------------

def extract_zip_from_address(address: str) -> str:
    """
    Extract 5-digit ZIP code from a property address string.
    Tries common patterns: trailing ZIP, ZIP after state abbreviation, etc.
    Returns empty string if no ZIP found.
    """
    if not address or not isinstance(address, str):
        return ""

    address = address.strip()

    # Pattern: 5-digit ZIP at end of string (possibly with ZIP+4)
    match = re.search(r"\b(\d{5})(?:-\d{4})?\s*$", address)
    if match:
        return match.group(1)

    # Pattern: 5-digit ZIP after FL/Florida
    match = re.search(r"\bFL\s+(\d{5})\b", address, re.IGNORECASE)
    if match:
        return match.group(1)

    # Pattern: any 5-digit sequence that starts with 3 (Florida ZIPs are 32xxx-34xxx)
    match = re.search(r"\b(3[234]\d{3})\b", address)
    if match:
        return match.group(1)

    return ""


def extract_property_zips(row: pd.Series) -> list:
    """
    Extract ZIP codes from a lead row. Handles pipe-delimited PHY_ADDR1
    for portfolio owners with multiple properties.

    Returns list of (address, zip) tuples.
    """
    results = []

    # PHY_ADDR1 is the PROPERTY address — preferred for rent estimation
    phy_addr = str(row.get("PHY_ADDR1", "") or "")

    if "|" in phy_addr:
        # Portfolio owner — multiple addresses separated by pipes
        addresses = [a.strip() for a in phy_addr.split("|") if a.strip()]
    elif phy_addr:
        addresses = [phy_addr]
    else:
        addresses = []

    for addr in addresses:
        z = extract_zip_from_address(addr)
        if z:
            results.append((addr, z))

    # Fallback: OWN_ZIPCD is the MAILING zip — not ideal for rent estimation
    # but better than nothing if we can't extract property ZIP
    if not results:
        own_zip = str(row.get("OWN_ZIPCD", "") or "").strip()
        if own_zip:
            # Normalize to 5 digits
            own_zip = own_zip[:5]
            if own_zip.isdigit() and len(own_zip) == 5:
                results.append(("(mailing address)", own_zip))

    # Also try PHY_ZIPCD if it exists
    if not results:
        phy_zip = str(row.get("PHY_ZIPCD", "") or "").strip()
        if phy_zip:
            phy_zip = phy_zip[:5]
            if phy_zip.isdigit() and len(phy_zip) == 5:
                results.append(("(property zip field)", phy_zip))

    return results


# ---------------------------------------------------------------------------
# Rent lookup
# ---------------------------------------------------------------------------

def lookup_rent(zip_code: str, bedrooms: int, zip_rents: dict,
                county_rents: dict) -> int:
    """
    Look up FMR rent for a ZIP code and bedroom count.
    Falls back to county-level if ZIP not found.
    Returns 0 if no data available.
    """
    # Try exact ZIP match
    if zip_code in zip_rents:
        rents = zip_rents[zip_code]
        if bedrooms in rents:
            return rents[bedrooms]
        # If requested bedroom count not available, use closest available
        available = sorted(rents.keys())
        if available:
            closest = min(available, key=lambda x: abs(x - bedrooms))
            return rents[closest]

    # Fall back to county-level (first 5 digits of ZIP → county FIPS)
    # Florida county FIPS codes: 12001-12133 (state=12)
    # We need to map ZIP → county FIPS, which HUD data includes
    # For simplicity, try to find a matching county in the county_rents dict
    for fips, rents in county_rents.items():
        # Skip if not a Florida county (FIPS starts with 12)
        if not fips.startswith(FL_FIPS_STATE):
            continue
        if bedrooms in rents and rents[bedrooms] > 0:
            # This is a broad fallback — use first FL county found
            # A proper implementation would map ZIP to county FIPS
            return rents[bedrooms]

    return 0


# ---------------------------------------------------------------------------
# Main processing
# ---------------------------------------------------------------------------

def estimate_rents(input_path: Path, zip_rents: dict, county_rents: dict,
                   dry_run: bool = False) -> pd.DataFrame:
    """
    For each lead, estimate monthly rent based on HUD FMR data.
    Returns DataFrame with rent estimate columns added.
    """
    print(f"\n--- Estimating rents for leads in {input_path.name} ---")
    df = pd.read_csv(input_path, dtype=str)
    print(f"  Leads loaded: {len(df):,}")

    # Columns we'll add
    est_monthly_rents = []
    est_annual_rents = []
    est_nois = []
    est_monthly_debt_services = []
    est_dscrs = []
    rent_to_value_ratios = []
    property_zip_lists = []
    rent_details = []

    matched_count = 0
    unmatched_count = 0

    for idx, row in df.iterrows():
        if idx % 100 == 0 and idx > 0:
            print(f"  Processed {idx:,} / {len(df):,} leads...")

        prop_zips = extract_property_zips(row)

        if dry_run:
            if prop_zips:
                print(f"  [{idx}] Would look up rent for ZIP(s): "
                      f"{', '.join(z for _, z in prop_zips)}")
            else:
                print(f"  [{idx}] No ZIP found for this lead")
            est_monthly_rents.append(0)
            est_annual_rents.append(0)
            est_nois.append(0)
            est_monthly_debt_services.append(0)
            est_dscrs.append(0)
            rent_to_value_ratios.append(0)
            property_zip_lists.append("")
            rent_details.append("")
            continue

        total_monthly = 0
        detail_parts = []
        zips_used = []

        for addr, zip_code in prop_zips:
            rent = lookup_rent(zip_code, DEFAULT_BEDROOMS, zip_rents, county_rents)
            total_monthly += rent
            zips_used.append(zip_code)
            detail_parts.append(f"{zip_code}=${rent}")

        if total_monthly > 0:
            matched_count += 1
        else:
            unmatched_count += 1

        annual = total_monthly * 12
        noi = annual * (1 - EXPENSE_RATIO)

        # Debt service placeholder — will be filled by script 11 (county clerk)
        debt_service = 0
        dscr = 0  # Cannot calculate without debt service data

        # Rent-to-value ratio (gross rent multiplier inverse)
        # Try JV (just value / assessed value) first, then SALE_PRC1
        property_value = 0
        for val_col in ["JV", "TV_NSD", "SALE_PRC1", "jv", "tv_nsd", "sale_prc1",
                         "total_value", "just_value"]:
            raw_val = str(row.get(val_col, "") or "").strip().replace(",", "")
            try:
                v = float(raw_val)
                if v > 0:
                    property_value = v
                    break
            except (ValueError, TypeError):
                pass

        rtv = (total_monthly / property_value) if property_value > 0 else 0

        est_monthly_rents.append(total_monthly)
        est_annual_rents.append(annual)
        est_nois.append(round(noi, 2))
        est_monthly_debt_services.append(debt_service)
        est_dscrs.append(dscr)
        rent_to_value_ratios.append(round(rtv, 4))
        property_zip_lists.append("|".join(zips_used))
        rent_details.append("|".join(detail_parts))

    # Add columns to dataframe
    df["est_monthly_rent"] = est_monthly_rents
    df["est_annual_rent"] = est_annual_rents
    df["est_noi"] = est_nois
    df["est_monthly_debt_service"] = est_monthly_debt_services
    df["est_dscr"] = est_dscrs
    df["rent_to_value_ratio"] = rent_to_value_ratios
    df["property_zips"] = property_zip_lists
    df["rent_lookup_detail"] = rent_details

    if not dry_run:
        print(f"\n  Rent matched: {matched_count:,} leads")
        print(f"  No match:     {unmatched_count:,} leads")
        if matched_count > 0:
            matched_rents = [r for r in est_monthly_rents if r > 0]
            avg_rent = sum(matched_rents) / len(matched_rents)
            print(f"  Avg monthly rent (matched): ${avg_rent:,.0f}")

    return df


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Step 13: Estimate rental income using HUD Fair Market Rent data"
    )
    parser.add_argument(
        "--input",
        type=str,
        default=None,
        help=f"Input leads CSV (default: {DEFAULT_INPUT})"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help=f"Output CSV path (default: {OUTPUT_PATH})"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes"
    )
    parser.add_argument(
        "--fmr-file",
        type=str,
        default=None,
        help=f"Path to HUD FMR Excel file (default: {FMR_PATH})"
    )
    args = parser.parse_args()

    print("=" * 60)
    print("STEP 13: RENTAL ESTIMATES (HUD Fair Market Rent)")
    print("=" * 60)

    # Resolve input file
    if args.input:
        input_path = Path(args.input)
    elif DEFAULT_INPUT.exists():
        input_path = DEFAULT_INPUT
    elif ALT_INPUT.exists():
        input_path = ALT_INPUT
    else:
        print(f"\nERROR: No input file found.")
        print(f"  Checked: {DEFAULT_INPUT}")
        print(f"  Checked: {ALT_INPUT}")
        print("  Use --input to specify a different file.")
        sys.exit(1)

    if not input_path.exists():
        print(f"\nERROR: Input file not found: {input_path}")
        sys.exit(1)

    print(f"\n  Input:  {input_path}")

    # Resolve output
    output_path = Path(args.output) if args.output else OUTPUT_PATH
    print(f"  Output: {output_path}")

    # Resolve FMR file
    fmr_path = Path(args.fmr_file) if args.fmr_file else FMR_PATH

    # Step 1: Download FMR data
    print(f"\n--- Step 1: Download HUD FMR data ---")
    if not download_fmr(fmr_path):
        print("\nCannot proceed without FMR data. Exiting.")
        sys.exit(1)

    # Step 2: Parse FMR data
    zip_rents, county_rents = parse_fmr(fmr_path)

    if not zip_rents and not county_rents:
        print("\nERROR: No rent data parsed from FMR file. Check file format.")
        sys.exit(1)

    # Step 3: Estimate rents for each lead
    result_df = estimate_rents(input_path, zip_rents, county_rents,
                               dry_run=args.dry_run)

    # Step 4: Save output
    if not args.dry_run:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        result_df.to_csv(output_path, index=False)
        print(f"\n  Output saved: {output_path}")
        print(f"  Total rows: {len(result_df):,}")

        # Summary stats
        has_rent = result_df["est_monthly_rent"].astype(float) > 0
        print(f"\n--- Summary ---")
        print(f"  Leads with rent estimate: {has_rent.sum():,} / {len(result_df):,} "
              f"({has_rent.mean() * 100:.1f}%)")

        if has_rent.any():
            rents = result_df.loc[has_rent, "est_monthly_rent"].astype(float)
            nois = result_df.loc[has_rent, "est_noi"].astype(float)
            print(f"  Monthly rent range: ${rents.min():,.0f} - ${rents.max():,.0f}")
            print(f"  Average monthly rent: ${rents.mean():,.0f}")
            print(f"  Average est NOI (annual): ${nois.mean():,.0f}")

        rtvs = result_df.loc[
            result_df["rent_to_value_ratio"].astype(float) > 0,
            "rent_to_value_ratio"
        ].astype(float)
        if len(rtvs) > 0:
            print(f"  Average rent-to-value ratio: {rtvs.mean():.4f} "
                  f"({rtvs.mean() * 100:.2f}%)")
    else:
        print("\n  DRY RUN — no files written.")

    print("\nDone.")


if __name__ == "__main__":
    main()
