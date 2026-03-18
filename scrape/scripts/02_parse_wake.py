"""
Step 2: Parse & Standardize Wake County, NC Property Data
==========================================================

Takes the raw Wake County XLSX from Step 1 and standardizes it
into the same format as the Florida parser output. Downstream
scripts (03_filter_icp.py, 05_enrich, etc.) work unchanged.

Wake County XLSX specifics:
  - 87 columns, ~434K parcels
  - Mailing address: street in Mailing_address1, city/state/zip
    combined in Mailing_Address2 (e.g., "RALEIGH NC 27615-4964")
  - Property address: separate fields (Street_Number, Street_Name, etc.)
  - Use codes: same numeric system as FL (01=SFR, 02=MH, 03=MF, etc.)
  - No homestead flag (NC doesn't have universal homestead exemption)
  - No bedrooms column, but has NUM_of_Rooms and BATH_FIXTURES
  - HEATED_AREA = total living sqft

Usage:
    python scripts/02_parse_wake.py
    python scripts/02_parse_wake.py --limit 1000
"""

import argparse
import json
import re
import sys
from pathlib import Path

import pandas as pd

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent
RAW_DIR = PROJECT_DIR / "data" / "raw"
PARSED_DIR = PROJECT_DIR / "data" / "parsed"

# Try NC config first, fall back to default
NC_CONFIG = PROJECT_DIR / "config" / "nc_scoring_weights.json"
DEFAULT_CONFIG = PROJECT_DIR / "config" / "scoring_weights.json"

# ---------------------------------------------------------------------------
# Standard output columns (must match 02_parse_nal.py output)
# ---------------------------------------------------------------------------
STANDARD_COLUMNS = [
    "parcel_id",
    "owner_name_1",
    "owner_name_2",
    "mail_street",
    "mail_city",
    "mail_state",
    "mail_zip",
    "prop_street",
    "prop_city",
    "prop_zip",
    "use_code",
    "use_description",
    "just_value",
    "assessed_value",
    "sale_date",
    "sale_price",
    "homestead_flag",
    "year_built",
    "living_sqft",
    "bedrooms",
    "bathrooms",
    "is_llc",
    "is_absentee",
    "is_no_homestead",
    "is_cash_buyer",
    "portfolio_count",
    "portfolio_tier",
]

# Use code descriptions (same as FL — Wake County uses same numbering)
USE_CODE_DESCRIPTIONS = {
    "01": "Single Family Residential",
    "02": "Mobile Home",
    "03": "Multi-Family (2-9 units)",
    "04": "Condominium",
    "05": "Cooperatives",
    "06": "Retirement Homes",
    "07": "Miscellaneous Residential",
    "08": "Multi-Family (10+ units)",
    "09": "Residential Common Elements",
}

# Target use codes — DSCR-relevant residential types
TARGET_USE_CODES = {"01", "02", "03", "04", "05", "08"}

# Home state for absentee detection
HOME_STATE = "NC"


def load_llc_keywords():
    """Load LLC/Corp keywords from scoring config."""
    config_file = NC_CONFIG if NC_CONFIG.exists() else DEFAULT_CONFIG
    with open(config_file) as f:
        config = json.load(f)
    return config.get("llc_keywords", [
        "LLC", "INC", "CORP", "TRUST", "LP", "LLP", "PARTNERSHIP",
        "HOLDINGS", "INVESTMENTS", "PROPERTIES", "GROUP", "CAPITAL",
        "VENTURES", "MANAGEMENT", "ASSOCIATES", "ENTERPRISES", "FUND", "REALTY"
    ])


def clean_name(name: str) -> str:
    """Standardize owner name."""
    if not name or str(name).strip().upper() in ("NAN", "NONE", ""):
        return ""
    name = str(name).upper().strip()
    name = re.sub(r"\s+", " ", name)
    for suffix in [" AS PERS REP", " AS PERSONAL REP", " PERS REP",
                   " TRUSTEE OF", " AS TRUSTEE", " TRUSTEES",
                   " ET AL", " ET UX", " ET VIR"]:
        name = name.replace(suffix, "")
    return name.strip()


def clean_address(addr: str) -> str:
    """Standardize a street address."""
    if not addr or str(addr).strip().upper() in ("NAN", "NONE", ""):
        return ""
    addr = str(addr).upper().strip()
    addr = re.sub(r"\s+", " ", addr)
    return addr


def parse_mailing_address2(addr2: str) -> tuple:
    """
    Parse Wake County Mailing_Address2 which contains city, state, zip
    combined in one field. Format: "RALEIGH NC 27615-4964"

    Returns: (city, state, zip5)
    """
    if not addr2 or str(addr2).strip().upper() in ("NAN", "NONE", ""):
        return ("", "", "")

    addr2 = str(addr2).strip()

    # Pattern: CITY STATE ZIP (state is always 2 letters, zip is 5 or 5-4)
    match = re.match(r'^(.+?)\s+([A-Z]{2})\s+(\d{5}(?:-\d{4})?)$', addr2.upper())
    if match:
        city = match.group(1).strip()
        state = match.group(2).strip()
        zip_code = match.group(3)[:5]  # Take first 5 digits only
        return (city, state, zip_code)

    # Fallback: try to extract zip from end
    zip_match = re.search(r'(\d{5})(?:-\d{4})?$', addr2)
    if zip_match:
        zip_code = zip_match.group(1)
        before_zip = addr2[:zip_match.start()].strip()
        # Try to find 2-letter state code
        state_match = re.search(r'\b([A-Z]{2})\s*$', before_zip.upper())
        if state_match:
            state = state_match.group(1)
            city = before_zip[:state_match.start()].strip()
            return (city.upper(), state, zip_code)
        return (before_zip.upper(), "", zip_code)

    return (addr2.upper(), "", "")


def build_prop_street(row: pd.Series) -> str:
    """
    Build property street address from Wake County's separate fields:
    Street_Number + Street_Prefix + Street_Name + Street_Type + Street_Suffix
    """
    parts = []
    for field in ["Street_Number", "Street_Prefix", "Street_Name",
                   "Street_Type", "Street_Suffix"]:
        val = str(row.get(field, "")).strip()
        if val and val.upper() not in ("NAN", "NONE", ""):
            parts.append(val.upper())
    return " ".join(parts)


def is_llc(name: str, keywords: list) -> bool:
    """Check if owner name is a corporate entity."""
    if not name:
        return False
    upper = name.upper()
    return any(kw in upper for kw in keywords)


def main():
    parser = argparse.ArgumentParser(
        description="Parse Wake County NC property data (Step 2)"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Only process first N rows (for testing)"
    )
    args = parser.parse_args()

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    PARSED_DIR.mkdir(parents=True, exist_ok=True)

    llc_keywords = load_llc_keywords()

    # -----------------------------------------------------------------
    # Load raw file
    # -----------------------------------------------------------------
    raw_file = RAW_DIR / "wake_county_raw.xlsx"
    if not raw_file.exists():
        print(f"\nNo raw file found at {raw_file}")
        print("Run Step 1 first: python scripts/01_download_wake.py")
        return

    print()
    print("=" * 60)
    print("  PARSING: WAKE COUNTY, NC")
    print("=" * 60)
    print()

    print("  Loading XLSX (this takes 1-2 minutes for 434K rows)...")
    nrows = args.limit if args.limit else None
    df = pd.read_excel(raw_file, dtype=str, nrows=nrows)
    print(f"  Loaded {len(df):,} rows, {len(df.columns)} columns")

    # -----------------------------------------------------------------
    # Map columns to standard schema
    # -----------------------------------------------------------------
    print("  Mapping Wake County columns to standard schema...")

    # Parcel ID
    df["parcel_id"] = df["REAL_ESTATE_ID"].astype(str).str.strip()

    # Owner names
    df["owner_name_1"] = df["OWNER1"].apply(clean_name)
    df["owner_name_2"] = df["OWNER2"].apply(clean_name) if "OWNER2" in df.columns else ""

    # Mailing address — street is in Mailing_address1,
    # city/state/zip combined in Mailing_Address2
    df["mail_street"] = df["Mailing_address1"].apply(clean_address)

    # Parse city/state/zip from Mailing_Address2
    parsed_addr = df["Mailing_Address2"].apply(parse_mailing_address2)
    df["mail_city"] = parsed_addr.apply(lambda x: x[0])
    df["mail_state"] = parsed_addr.apply(lambda x: x[1])
    df["mail_zip"] = parsed_addr.apply(lambda x: x[2])

    # Property address — build from separate fields
    df["prop_street"] = df.apply(build_prop_street, axis=1)
    df["prop_city"] = df["PHYSICAL_CITY"].apply(clean_address) if "PHYSICAL_CITY" in df.columns else ""
    df["prop_zip"] = df["PHYSICAL_ZIP_CODE"].astype(str).str.strip().str[:5] if "PHYSICAL_ZIP_CODE" in df.columns else ""

    # Use code
    df["use_code"] = df["TYPE_AND_USE"].astype(str).str.strip().str.zfill(2)
    df["use_description"] = df["use_code"].map(USE_CODE_DESCRIPTIONS).fillna("")

    # Values
    df["assessed_value"] = (
        pd.to_numeric(df.get("Assessed_Building_Value", 0), errors="coerce").fillna(0) +
        pd.to_numeric(df.get("Assessed_Land_Value", 0), errors="coerce").fillna(0)
    ).astype(int)
    df["just_value"] = df["assessed_value"]  # Wake County doesn't distinguish just vs assessed

    # Sale data
    df["sale_price"] = pd.to_numeric(df.get("Total_sale_Price", 0), errors="coerce").fillna(0).astype(int)
    df["sale_date"] = df.get("Total_Sale_Date", "").astype(str).str[:10]
    df.loc[df["sale_date"].isin(["nan", "None", "NaT", ""]), "sale_date"] = ""

    # Building characteristics
    df["year_built"] = pd.to_numeric(df.get("Year_Built", 0), errors="coerce").fillna(0).astype(int)
    df["living_sqft"] = pd.to_numeric(df.get("HEATED_AREA", 0), errors="coerce").fillna(0).astype(int)
    df["bedrooms"] = ""  # Not available in Wake County tax data
    df["bathrooms"] = pd.to_numeric(df.get("BATH_FIXTURES", 0), errors="coerce").fillna(0).astype(int)

    # Homestead — NC does not have universal homestead. Set all to N.
    df["homestead_flag"] = "N"

    print(f"  Column mapping complete.")

    # -----------------------------------------------------------------
    # Filter to residential use codes
    # -----------------------------------------------------------------
    before = len(df)
    df = df[df["use_code"].isin(TARGET_USE_CODES)].copy()
    print(f"  Filtered to residential use codes: {len(df):,} rows (dropped {before - len(df):,})")

    # -----------------------------------------------------------------
    # Flag LLC / corporate owners
    # -----------------------------------------------------------------
    print("  Detecting LLC/Corp owners...")
    df["is_llc"] = df["owner_name_1"].apply(lambda x: is_llc(x, llc_keywords))
    print(f"    LLC/Corp/Trust owners: {df['is_llc'].sum():,}")

    # -----------------------------------------------------------------
    # Flag absentee owners
    # -----------------------------------------------------------------
    print("  Detecting absentee owners...")
    df["is_absentee"] = False

    # Out-of-state: mailing state is not NC (and not blank)
    state_vals = df["mail_state"].astype(str).str.strip().str.upper()
    out_of_state = (state_vals != HOME_STATE) & (state_vals != "") & (state_vals != "NAN")
    df.loc[out_of_state, "is_absentee"] = True

    # In-state but different zip
    mail_zips = df["mail_zip"].astype(str).str.strip()
    prop_zips = df["prop_zip"].astype(str).str.strip()
    diff_zip = (mail_zips != prop_zips) & (mail_zips != "") & (prop_zips != "")
    df.loc[diff_zip, "is_absentee"] = True

    print(f"    Absentee owners: {df['is_absentee'].sum():,}")
    print(f"    Out-of-state:    {out_of_state.sum():,}")

    # -----------------------------------------------------------------
    # Non-homesteaded (all NC properties — no universal exemption)
    # -----------------------------------------------------------------
    df["is_no_homestead"] = True
    print(f"  Non-homesteaded: {df['is_no_homestead'].sum():,} (all — NC has no universal homestead)")

    # -----------------------------------------------------------------
    # Flag potential cash buyers
    # -----------------------------------------------------------------
    print("  Flagging potential cash buyers...")
    df["is_cash_buyer"] = df["sale_price"] > 50000
    print(f"    Potential cash buyers: {df['is_cash_buyer'].sum():,}")

    # -----------------------------------------------------------------
    # Portfolio detection
    # -----------------------------------------------------------------
    print("  Detecting portfolio landlords...")
    owner_counts = (
        df[df["owner_name_1"] != ""]
        .groupby("owner_name_1")["parcel_id"]
        .nunique()
        .reset_index()
        .rename(columns={"parcel_id": "portfolio_count"})
    )
    df = df.merge(owner_counts, on="owner_name_1", how="left")
    df["portfolio_count"] = df["portfolio_count"].fillna(1).astype(int)

    df["portfolio_tier"] = "single"
    df.loc[df["portfolio_count"].between(2, 4), "portfolio_tier"] = "small_portfolio"
    df.loc[df["portfolio_count"] >= 5, "portfolio_tier"] = "large_portfolio"

    print(f"    Portfolio 2-4 properties: {(df['portfolio_tier'] == 'small_portfolio').sum():,}")
    print(f"    Portfolio 5+ properties:  {(df['portfolio_tier'] == 'large_portfolio').sum():,}")

    # -----------------------------------------------------------------
    # Deduplicate by parcel_id
    # -----------------------------------------------------------------
    before_dedup = len(df)
    df = df.drop_duplicates(subset=["parcel_id"], keep="first")
    dupes = before_dedup - len(df)
    if dupes > 0:
        print(f"  Removed {dupes:,} duplicate parcels")

    # -----------------------------------------------------------------
    # Ensure all standard columns exist and save
    # -----------------------------------------------------------------
    for col in STANDARD_COLUMNS:
        if col not in df.columns:
            df[col] = ""

    output_file = PARSED_DIR / "wake_county_parsed.csv"
    df[STANDARD_COLUMNS].to_csv(output_file, index=False)

    # -----------------------------------------------------------------
    # Summary
    # -----------------------------------------------------------------
    print()
    print("=" * 60)
    print("  WAKE COUNTY PARSE COMPLETE")
    print("=" * 60)
    print(f"  Total residential properties: {len(df):,}")
    print(f"  LLC/Corp owned:              {df['is_llc'].sum():,}")
    print(f"  Absentee owners:             {df['is_absentee'].sum():,}")
    print(f"  Potential cash buyers:       {df['is_cash_buyer'].sum():,}")
    print(f"  Portfolio (2-4 props):       {(df['portfolio_tier'] == 'small_portfolio').sum():,}")
    print(f"  Portfolio (5+ props):        {(df['portfolio_tier'] == 'large_portfolio').sum():,}")
    print()
    print(f"  Saved: {output_file}")
    print()
    print("  Next step:")
    print("    python scripts/03_filter_icp.py --county wake_county --state NC")
    print()


if __name__ == "__main__":
    main()
