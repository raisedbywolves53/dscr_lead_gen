"""
Step 2: Parse & Standardize Property Data
==========================================

Takes the raw data from Step 1 (which may be FDOR NAL CSV, county CSV,
or county XLSX) and standardizes everything into a single clean format.

What this does:
  1. Loads raw file(s) from data/raw/
  2. Maps columns to a standard schema
  3. Cleans owner names, addresses
  4. Flags LLC/Corp owners
  5. Flags absentee owners (mail address != property address)
  6. Flags non-homesteaded properties
  7. Detects portfolio landlords (same owner, multiple properties)
  8. Saves clean output to data/parsed/

Usage:
    python scripts/02_parse_nal.py --county seminole
    python scripts/02_parse_nal.py --county palm_beach
    python scripts/02_parse_nal.py --county all
"""

import argparse
import json
import re
from pathlib import Path

import pandas as pd

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent
RAW_DIR = PROJECT_DIR / "data" / "raw"
PARSED_DIR = PROJECT_DIR / "data" / "parsed"
CONFIG_FILE = PROJECT_DIR / "config" / "scoring_weights.json"

# ---------------------------------------------------------------------------
# Entity keywords — if any of these appear in the owner name, it's an
# LLC / corporation / trust, not a regular person.
# Loaded from config so you can edit without touching code.
# ---------------------------------------------------------------------------
def load_llc_keywords():
    """Load LLC/Corp keywords from scoring_weights.json."""
    with open(CONFIG_FILE) as f:
        config = json.load(f)
    return config.get("llc_keywords", [
        "LLC", "INC", "CORP", "TRUST", "LP", "LLP", "PARTNERSHIP",
        "HOLDINGS", "INVESTMENTS", "PROPERTIES", "GROUP", "CAPITAL",
        "VENTURES", "MANAGEMENT", "ASSOCIATES", "ENTERPRISES", "FUND", "REALTY"
    ])

# ---------------------------------------------------------------------------
# Standard output columns (what we want every parsed file to have)
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
    # Flags added by this script
    "is_llc",
    "is_absentee",
    "is_no_homestead",
    "is_cash_buyer",
    "portfolio_count",
    "portfolio_tier",
]

# ---------------------------------------------------------------------------
# FDOR NAL column mapping
#
# The FDOR NAL CSV has specific column names. This maps them to our
# standard schema. We handle multiple possible column names because
# FDOR files can vary slightly year to year.
# ---------------------------------------------------------------------------
FDOR_COLUMN_MAP = {
    # Parcel / property ID
    "PARCEL_ID": "parcel_id",
    "PARCEL": "parcel_id",
    # Owner info
    "OWN_NAME": "owner_name_1",
    "OWNER_NAME": "owner_name_1",
    "OWN_ADDR1": "mail_street",
    "OWN_ADDR2": "owner_name_2",    # FDOR often puts c/o or 2nd name here
    "OWN_CITY": "mail_city",
    "OWN_STATE_DOM": "mail_state",   # 2-letter code (preferred over OWN_STATE)
    "OWN_STATE": "mail_state_full",  # Full name (fallback)
    "OWN_ZIPCD": "mail_zip",
    "OWN_ZIP": "mail_zip",
    # Property physical address
    "PHY_ADDR1": "prop_street",
    "SITE_ADDR": "prop_street",
    "PHY_CITY": "prop_city",
    "SITE_CITY": "prop_city",
    "PHY_ZIPCD": "prop_zip",
    "SITE_ZIP": "prop_zip",
    # Property characteristics
    "DOR_UC": "use_code",
    "JV": "just_value",
    "JUST_VAL": "just_value",
    "AV_HMSTD": "assessed_hmstd",    # 0 = not homesteaded
    "AV_NHM": "assessed_value",      # assessed value (non-homestead)
    # Sale data
    "SALE_YR1": "sale_year",
    "SALE_MO1": "sale_month",
    "SALE_PRC1": "sale_price",
    # Building info (may not exist in all NAL files)
    "ACT_YR_BLT": "year_built",
    "YR_BLT": "year_built",
    "TOT_LVG_AREA": "living_sqft",
    "LVG_AREA": "living_sqft",
    "NO_BDRM": "bedrooms",
    "NO_BATH": "bathrooms",
}

# Use code descriptions
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

# Target use codes — only these are DSCR-relevant
TARGET_USE_CODES = {"01", "02", "03", "04", "05", "08"}

# USPS address abbreviation standardization
ADDRESS_ABBREVS = {
    r"\bST\b": "STREET",
    r"\bAVE\b": "AVENUE",
    r"\bBLVD\b": "BOULEVARD",
    r"\bDR\b": "DRIVE",
    r"\bLN\b": "LANE",
    r"\bCT\b": "COURT",
    r"\bPL\b": "PLACE",
    r"\bRD\b": "ROAD",
    r"\bCIR\b": "CIRCLE",
    r"\bPKWY\b": "PARKWAY",
    r"\bHWY\b": "HIGHWAY",
    r"\bTRL\b": "TRAIL",
    r"\bTER\b": "TERRACE",
    r"\bWY\b": "WAY",
    r"\bAPT\b": "APT",
    r"\bSTE\b": "SUITE",
    r"\bFL\b": "FLOOR",
    r"\bBLDG\b": "BUILDING",
    r"\bN\b": "NORTH",
    r"\bS\b": "SOUTH",
    r"\bE\b": "EAST",
    r"\bW\b": "WEST",
    r"\bNE\b": "NORTHEAST",
    r"\bNW\b": "NORTHWEST",
    r"\bSE\b": "SOUTHEAST",
    r"\bSW\b": "SOUTHWEST",
}


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def clean_name(name: str) -> str:
    """
    Standardize an owner name:
    - Uppercase
    - Strip extra whitespace
    - Remove common suffixes like 'TRUSTEE OF', 'AS PERS REP'
    """
    if not name or str(name).strip().upper() in ("NAN", "NONE", ""):
        return ""

    name = str(name).upper().strip()
    # Collapse multiple spaces
    name = re.sub(r"\s+", " ", name)
    # Remove common legal suffixes that don't help with matching
    for suffix in [" AS PERS REP", " AS PERSONAL REP", " PERS REP",
                   " TRUSTEE OF", " AS TRUSTEE", " TRUSTEES",
                   " ET AL", " ET UX", " ET VIR"]:
        name = name.replace(suffix, "")
    return name.strip()


def clean_address(addr: str) -> str:
    """Standardize a street address to USPS format."""
    if not addr or str(addr).strip().upper() in ("NAN", "NONE", ""):
        return ""

    addr = str(addr).upper().strip()
    addr = re.sub(r"\s+", " ", addr)
    # Note: we do NOT expand abbreviations by default — USPS actually
    # prefers abbreviations. We just normalize spacing and case.
    return addr


def is_llc(name: str, keywords: list) -> bool:
    """Check if an owner name is a corporate entity (LLC, Corp, Trust, etc.)."""
    if not name:
        return False
    upper = name.upper()
    return any(kw in upper for kw in keywords)


def detect_columns(df: pd.DataFrame) -> dict:
    """
    Auto-detect which column mapping to use based on the columns
    present in the raw file. Returns a mapping dict.
    """
    existing_cols = set(df.columns)
    mapping = {}

    # Check for FDOR NAL columns
    fdor_matches = sum(1 for c in existing_cols if c in FDOR_COLUMN_MAP)
    if fdor_matches >= 3:
        # This looks like an FDOR NAL file
        for raw_col, std_col in FDOR_COLUMN_MAP.items():
            if raw_col in existing_cols and std_col not in mapping.values():
                mapping[raw_col] = std_col
        return mapping

    # Generic column detection — try common patterns
    for col in existing_cols:
        col_upper = col.upper().strip()

        if "PARCEL" in col_upper and "parcel_id" not in mapping.values():
            mapping[col] = "parcel_id"
        elif "FOLIO" in col_upper and "parcel_id" not in mapping.values():
            mapping[col] = "parcel_id"
        elif "OWNER" in col_upper and "NAME" in col_upper and "owner_name_1" not in mapping.values():
            mapping[col] = "owner_name_1"
        elif "MAIL" in col_upper and "ADDR" in col_upper and "mail_street" not in mapping.values():
            mapping[col] = "mail_street"
        elif "MAIL" in col_upper and "CITY" in col_upper and "mail_city" not in mapping.values():
            mapping[col] = "mail_city"
        elif "MAIL" in col_upper and "STATE" in col_upper and "mail_state" not in mapping.values():
            mapping[col] = "mail_state"
        elif "MAIL" in col_upper and "ZIP" in col_upper and "mail_zip" not in mapping.values():
            mapping[col] = "mail_zip"
        elif ("SITE" in col_upper or "PROP" in col_upper) and "ADDR" in col_upper and "prop_street" not in mapping.values():
            mapping[col] = "prop_street"
        elif ("SITE" in col_upper or "PROP" in col_upper) and "CITY" in col_upper and "prop_city" not in mapping.values():
            mapping[col] = "prop_city"
        elif ("SITE" in col_upper or "PROP" in col_upper) and "ZIP" in col_upper and "prop_zip" not in mapping.values():
            mapping[col] = "prop_zip"
        elif "USE" in col_upper and "CODE" in col_upper and "use_code" not in mapping.values():
            mapping[col] = "use_code"
        elif "MARKET" in col_upper and "VALUE" in col_upper and "just_value" not in mapping.values():
            mapping[col] = "just_value"
        elif "JUST" in col_upper and "VALUE" in col_upper and "just_value" not in mapping.values():
            mapping[col] = "just_value"
        elif "ASSESSED" in col_upper and "assessed_value" not in mapping.values():
            mapping[col] = "assessed_value"
        elif "SALE" in col_upper and "DATE" in col_upper and "sale_date" not in mapping.values():
            mapping[col] = "sale_date"
        elif "SALE" in col_upper and "PRICE" in col_upper and "sale_price" not in mapping.values():
            mapping[col] = "sale_price"
        elif "HOMESTEAD" in col_upper and "homestead_flag" not in mapping.values():
            mapping[col] = "homestead_flag"
        elif "YR" in col_upper and "BLT" in col_upper and "year_built" not in mapping.values():
            mapping[col] = "year_built"

    return mapping


def load_raw_file(filepath: Path) -> pd.DataFrame:
    """Load a raw data file (CSV or XLSX) into a DataFrame."""
    suffix = filepath.suffix.lower()

    print(f"  Loading: {filepath.name}")

    if suffix == ".csv":
        # Load everything as strings to avoid type issues
        df = pd.read_csv(filepath, dtype=str, low_memory=False)
    elif suffix in (".xlsx", ".xls"):
        df = pd.read_excel(filepath, dtype=str)
    else:
        print(f"  WARNING: Unknown file format '{suffix}'. Trying CSV...")
        df = pd.read_csv(filepath, dtype=str, low_memory=False)

    print(f"  Loaded {len(df):,} rows, {len(df.columns)} columns")
    return df


def parse_and_standardize(df: pd.DataFrame, county_name: str, llc_keywords: list) -> pd.DataFrame:
    """
    Main parsing logic. Takes a raw DataFrame and produces a clean,
    standardized DataFrame with all the flags we need.
    """

    # ---------------------------------------------------------------
    # 1. Map columns to standard names
    # ---------------------------------------------------------------
    print("  Detecting column format...")
    col_map = detect_columns(df)

    if len(col_map) < 3:
        print(f"  WARNING: Only matched {len(col_map)} columns. File format may not be recognized.")
        print(f"  Matched: {col_map}")
        print(f"  Available columns: {list(df.columns)[:20]}")

    # Rename matched columns
    df = df.rename(columns=col_map)
    mapped_cols = list(col_map.values())
    print(f"  Mapped {len(col_map)} columns: {', '.join(mapped_cols)}")

    # ---------------------------------------------------------------
    # 2. Handle FDOR-specific quirks
    # ---------------------------------------------------------------

    # FDOR uses OWN_STATE_DOM for 2-letter state codes (preferred)
    # and OWN_STATE for full state names (fallback)
    if "mail_state" not in df.columns and "mail_state_full" in df.columns:
        df["mail_state"] = df["mail_state_full"]

    # FDOR sale year + month → sale_date
    if "sale_year" in df.columns and "sale_month" in df.columns:
        df["sale_date"] = (
            df["sale_year"].astype(str).str.strip() + "-" +
            df["sale_month"].astype(str).str.strip().str.zfill(2)
        )

    # FDOR assessed_hmstd = 0 means NOT homesteaded
    if "assessed_hmstd" in df.columns and "homestead_flag" not in df.columns:
        hmstd_val = pd.to_numeric(df["assessed_hmstd"], errors="coerce").fillna(0)
        df["homestead_flag"] = (hmstd_val > 0).map({True: "Y", False: "N"})

    # ---------------------------------------------------------------
    # 3. Clean owner names
    # ---------------------------------------------------------------
    print("  Cleaning owner names...")
    if "owner_name_1" in df.columns:
        df["owner_name_1"] = df["owner_name_1"].apply(clean_name)
    else:
        df["owner_name_1"] = ""

    if "owner_name_2" in df.columns:
        df["owner_name_2"] = df["owner_name_2"].apply(clean_name)
    else:
        df["owner_name_2"] = ""

    # ---------------------------------------------------------------
    # 4. Clean addresses
    # ---------------------------------------------------------------
    print("  Standardizing addresses...")
    for col in ["mail_street", "prop_street"]:
        if col in df.columns:
            df[col] = df[col].apply(clean_address)

    # Clean zip codes (keep first 5 digits only)
    for col in ["mail_zip", "prop_zip"]:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip().str[:5]
            # Remove non-numeric
            df[col] = df[col].str.replace(r"[^0-9]", "", regex=True)

    # Standardize state to 2-letter code
    if "mail_state" in df.columns:
        df["mail_state"] = df["mail_state"].astype(str).str.strip().str.upper()
        # If it's a full state name, the scoring step will handle it.
        # For now, just clean it up.

    # ---------------------------------------------------------------
    # 5. Use code description
    # ---------------------------------------------------------------
    if "use_code" in df.columns:
        # Normalize use codes to 2-digit strings
        df["use_code"] = df["use_code"].astype(str).str.strip().str.zfill(2)
        df["use_description"] = df["use_code"].map(USE_CODE_DESCRIPTIONS).fillna("")
    else:
        df["use_code"] = ""
        df["use_description"] = ""

    # ---------------------------------------------------------------
    # 6. Filter to residential investment property use codes
    # ---------------------------------------------------------------
    before_count = len(df)
    if "use_code" in df.columns and df["use_code"].ne("").any():
        df = df[df["use_code"].isin(TARGET_USE_CODES)].copy()
        print(f"  Filtered to residential use codes: {len(df):,} rows (dropped {before_count - len(df):,})")

    # ---------------------------------------------------------------
    # 7. Numeric conversions
    # ---------------------------------------------------------------
    for col in ["just_value", "assessed_value", "sale_price"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)

    # ---------------------------------------------------------------
    # 8. Flag LLC / corporate owners
    # ---------------------------------------------------------------
    print("  Detecting LLC/Corp owners...")
    df["is_llc"] = df["owner_name_1"].apply(lambda x: is_llc(x, llc_keywords))
    llc_count = df["is_llc"].sum()
    print(f"    LLC/Corp/Trust owners: {llc_count:,}")

    # ---------------------------------------------------------------
    # 9. Flag absentee owners
    #    Absentee = mailing state is not FL, OR mailing zip != property zip
    # ---------------------------------------------------------------
    print("  Detecting absentee owners...")
    df["is_absentee"] = False

    if "mail_state" in df.columns:
        state_vals = df["mail_state"].astype(str).str.strip().str.upper()
        # Out-of-state: mailing state is not FL (and not blank)
        out_of_state = (state_vals != "FL") & (state_vals != "") & (state_vals != "NAN")
        df.loc[out_of_state, "is_absentee"] = True

    if "mail_zip" in df.columns and "prop_zip" in df.columns:
        # In-state but different zip
        diff_zip = (
            (df["mail_zip"].astype(str).str.strip() != df["prop_zip"].astype(str).str.strip()) &
            (df["mail_zip"].astype(str).str.strip() != "") &
            (df["prop_zip"].astype(str).str.strip() != "")
        )
        df.loc[diff_zip, "is_absentee"] = True

    absentee_count = df["is_absentee"].sum()
    print(f"    Absentee owners: {absentee_count:,}")

    # ---------------------------------------------------------------
    # 10. Flag non-homesteaded properties
    # ---------------------------------------------------------------
    print("  Checking homestead status...")
    if "homestead_flag" in df.columns:
        df["is_no_homestead"] = df["homestead_flag"].astype(str).str.upper().isin(["N", "", "NAN", "NONE", "0"])
    else:
        # If no homestead column, assume all are non-homesteaded
        # (we already filtered to non-homesteaded in FDOR processing)
        df["is_no_homestead"] = True

    no_hmstd_count = df["is_no_homestead"].sum()
    print(f"    Non-homesteaded: {no_hmstd_count:,}")

    # ---------------------------------------------------------------
    # 11. Flag potential cash buyers
    #     If sale_price > 0 but no mortgage data, flag as possible cash buyer.
    #     Note: NAL files don't have mortgage data, so this is a rough signal.
    #     We flag any sale > $50K as potential cash (conservative).
    # ---------------------------------------------------------------
    print("  Flagging potential cash buyers...")
    if "sale_price" in df.columns:
        df["is_cash_buyer"] = df["sale_price"] > 50000
    else:
        df["is_cash_buyer"] = False

    cash_count = df["is_cash_buyer"].sum()
    print(f"    Potential cash buyers: {cash_count:,}")

    # ---------------------------------------------------------------
    # 12. Portfolio detection — how many properties does each owner have?
    # ---------------------------------------------------------------
    print("  Detecting portfolio landlords...")

    # Group by owner name (normalized) and count parcels
    owner_counts = (
        df[df["owner_name_1"] != ""]
        .groupby("owner_name_1")["parcel_id"]
        .nunique()
        .reset_index()
        .rename(columns={"parcel_id": "portfolio_count"})
    )

    # Merge counts back
    df = df.merge(owner_counts, on="owner_name_1", how="left")
    df["portfolio_count"] = df["portfolio_count"].fillna(1).astype(int)

    # Assign portfolio tier
    df["portfolio_tier"] = "single"
    df.loc[df["portfolio_count"].between(2, 4), "portfolio_tier"] = "small_portfolio"
    df.loc[df["portfolio_count"] >= 5, "portfolio_tier"] = "large_portfolio"

    portfolio_2_4 = (df["portfolio_tier"] == "small_portfolio").sum()
    portfolio_5_plus = (df["portfolio_tier"] == "large_portfolio").sum()
    print(f"    Portfolio 2-4 properties: {portfolio_2_4:,}")
    print(f"    Portfolio 5+ properties:  {portfolio_5_plus:,}")

    # ---------------------------------------------------------------
    # 13. Deduplicate — same parcel_id = same property, keep first
    # ---------------------------------------------------------------
    before_dedup = len(df)
    if "parcel_id" in df.columns and df["parcel_id"].ne("").any():
        df = df.drop_duplicates(subset=["parcel_id"], keep="first")
        dupes = before_dedup - len(df)
        if dupes > 0:
            print(f"  Removed {dupes:,} duplicate parcels")

    # ---------------------------------------------------------------
    # 14. Ensure all standard columns exist
    # ---------------------------------------------------------------
    for col in STANDARD_COLUMNS:
        if col not in df.columns:
            df[col] = ""

    return df


def main():
    parser = argparse.ArgumentParser(
        description="Parse & standardize property data (Step 2)"
    )
    parser.add_argument(
        "--county",
        type=str,
        required=True,
        help='County name (e.g. "seminole") or "all" to process all files in data/raw/'
    )
    args = parser.parse_args()

    PARSED_DIR.mkdir(parents=True, exist_ok=True)

    llc_keywords = load_llc_keywords()
    county_arg = args.county.strip().lower()

    # ---------------------------------------------------------------
    # Find raw files to process
    # ---------------------------------------------------------------
    if county_arg == "all":
        raw_files = list(RAW_DIR.glob("*_raw.csv")) + list(RAW_DIR.glob("*_raw.xlsx"))
    else:
        county_slug = county_arg.replace(" ", "_").replace("-", "_")
        raw_files = list(RAW_DIR.glob(f"{county_slug}_raw.*"))

    if not raw_files:
        print(f"\nNo raw files found for '{county_arg}' in {RAW_DIR}/")
        print(f"Run Step 1 first: python scripts/01_download_nal.py --county {county_arg}")
        return

    print(f"\nFound {len(raw_files)} file(s) to parse.\n")

    # ---------------------------------------------------------------
    # Process each file
    # ---------------------------------------------------------------
    for filepath in raw_files:
        county_name = filepath.stem.replace("_raw", "")

        print("=" * 60)
        print(f"  PARSING: {county_name.upper()}")
        print("=" * 60)

        # Load the raw file
        df = load_raw_file(filepath)

        if df.empty:
            print(f"  WARNING: File is empty. Skipping.")
            continue

        # Parse and standardize
        parsed = parse_and_standardize(df, county_name, llc_keywords)

        # Save output
        output_file = PARSED_DIR / f"{county_name}_parsed.csv"
        parsed.to_csv(output_file, index=False)

        print()
        print(f"  SAVED: {output_file}")
        print(f"  Total records: {len(parsed):,}")
        print()

        # Print summary stats
        print("  SUMMARY")
        print("  " + "-" * 40)
        print(f"  Total properties:      {len(parsed):,}")
        if "is_llc" in parsed.columns:
            print(f"  LLC/Corp owned:        {parsed['is_llc'].sum():,}")
        if "is_absentee" in parsed.columns:
            print(f"  Absentee owners:       {parsed['is_absentee'].sum():,}")
        if "is_no_homestead" in parsed.columns:
            print(f"  Non-homesteaded:       {parsed['is_no_homestead'].sum():,}")
        if "is_cash_buyer" in parsed.columns:
            print(f"  Potential cash buyers:  {parsed['is_cash_buyer'].sum():,}")
        if "portfolio_tier" in parsed.columns:
            print(f"  Portfolio (2-4 props):  {(parsed['portfolio_tier'] == 'small_portfolio').sum():,}")
            print(f"  Portfolio (5+ props):   {(parsed['portfolio_tier'] == 'large_portfolio').sum():,}")
        print()

    print("=" * 60)
    print(f"  Next step: python scripts/03_filter_icp.py --county {county_arg}")
    print("=" * 60)


if __name__ == "__main__":
    main()
