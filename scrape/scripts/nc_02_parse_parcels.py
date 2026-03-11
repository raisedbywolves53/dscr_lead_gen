"""
NC Step 2: Parse & Standardize NC Parcel Data
===============================================

Takes raw NC OneMap data from nc_01_download_parcels.py and standardizes
it into the same schema as the FL pipeline's 02_parse_nal.py output.

This means Scripts 03-08 can run on NC data without modification.

NC-specific differences from FL:
  - No homestead exemption → is_no_homestead always True (not a useful signal)
  - Different column names (NC OneMap vs FDOR NAL)
  - NC has parusedesc (text descriptions) instead of just numeric use codes
  - Absentee detection: mail_state != "NC" instead of != "FL"
  - NC provides ownfrst/ownlast separately (FDOR gives "LAST FIRST" combined)

Usage:
    python scripts/nc_02_parse_parcels.py --county wake
    python scripts/nc_02_parse_parcels.py --county mecklenburg
    python scripts/nc_02_parse_parcels.py --county wake,mecklenburg
    python scripts/nc_02_parse_parcels.py --county all
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
# NC OneMap → Standard schema column mapping
# ---------------------------------------------------------------------------
NC_COLUMN_MAP = {
    # Parcel ID
    "parno": "parcel_id",
    "altparno": "alt_parcel_id",
    # Owner info
    "ownname": "owner_name_1",
    "ownname2": "owner_name_2",
    "ownfrst": "owner_first",
    "ownlast": "owner_last",
    "owntype": "owner_type",
    # Mailing address (composite field or components)
    "mailadd": "mail_street",
    "mcity": "mail_city",
    "mstate": "mail_state",
    "mzip": "mail_zip",
    # Property / site address
    "siteadd": "prop_street",
    "scity": "prop_city",
    "szip": "prop_zip",
    # County
    "cntyname": "county_name",
    "cntyfips": "county_fips",
    # Values
    "parval": "just_value",       # parcel assessed value
    "landval": "land_value",
    "improvval": "improvement_value",
    "presentval": "present_value",
    # Use codes
    "parusecode": "use_code",
    "parusedesc": "use_description",
    # Sale info
    "saledate": "sale_date_raw",
    "saledatetx": "sale_date_text",
    # Building info
    "structyear": "year_built",
    "gisacres": "lot_acres",
}

# ---------------------------------------------------------------------------
# NC use code → DSCR-relevant residential classification
#
# NC OneMap parusedesc contains text descriptions. We map these to our
# standard categories. The exact codes vary by county, so we match on
# description keywords as the primary method.
# ---------------------------------------------------------------------------
RESIDENTIAL_KEYWORDS = [
    "SINGLE FAMILY",
    "RESIDENTIAL",
    "DUPLEX",
    "TRIPLEX",
    "QUADRUPLEX",
    "MULTI-FAMILY",
    "MULTIFAMILY",
    "MULTI FAMILY",
    "APARTMENT",
    "CONDO",
    "CONDOMINIUM",
    "TOWNHOUSE",
    "TOWNHOME",
    "MOBILE HOME",
    "MANUFACTURED",
    "DWELLING",
]

# Keywords that EXCLUDE a record (commercial, vacant land, etc.)
EXCLUDE_KEYWORDS = [
    "VACANT",
    "COMMERCIAL",
    "INDUSTRIAL",
    "AGRICULTURAL",
    "FARM",
    "CHURCH",
    "GOVERNMENT",
    "EXEMPT",
    "UTILITY",
    "RAILROAD",
    "MINING",
    "TIMBER",
    "FOREST",
    "PARKING",
    "OFFICE",
    "RETAIL",
    "WAREHOUSE",
    "HOSPITAL",
    "SCHOOL",
]

# ---------------------------------------------------------------------------
# NC OneMap use codes — vary by county
#
# Some counties use short codes (Wake: RHS/R, COM/C, VAC/V)
# Others use detailed codes (Mecklenburg: R100/SINGLE FAMILY RESIDENTIAL)
#
# parusecode → code like RHS, R100, COM, VAC
# parusedesc → short desc like R, C, V or full like SINGLE FAMILY RESIDENTIAL
# ---------------------------------------------------------------------------
# Short code residential indicators (parusecode)
RESIDENTIAL_CODES = {
    "RHS",   # Residential (Wake)
    "R100",  # Single Family Residential (Mecklenburg)
    "R200",  # Multi-Family (Mecklenburg)
    "R300",  # Condominium (Mecklenburg)
    "R400",  # Townhouse (Mecklenburg)
    "R500",  # Mobile Home (Mecklenburg)
    "R600",  # Mixed Use Residential (Mecklenburg)
    "R700",  # Residential (Mecklenburg)
    "R800",  # Residential (Mecklenburg)
    "R900",  # Residential (Mecklenburg)
    "AHS",   # Accessory Housing Structure (Wake — could be rental)
}

# Short description codes (parusedesc single-letter)
RESIDENTIAL_DESC_CODES = {"R", "B"}  # R = Residential, B = AHS/accessory

# Non-residential codes to exclude
NON_RESIDENTIAL_CODES = {
    "COM", "IND", "VAC", "AGR", "CEM", "HOA", "MFG",
    "PTX", "STA", "WSS", "XMT", "AWI",
}
NON_RESIDENTIAL_DESC_CODES = {"C", "D", "V", "F", "I", "J", "M", "P", "S", "W", "E", "A"}

# Standard output columns — must match FL pipeline's 02_parse_nal.py output
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
    # Flags
    "is_llc",
    "is_absentee",
    "is_no_homestead",
    "is_cash_buyer",
    "portfolio_count",
    "portfolio_tier",
]


def load_llc_keywords():
    """Load LLC/Corp keywords from scoring_weights.json."""
    with open(CONFIG_FILE) as f:
        config = json.load(f)
    return config.get("llc_keywords", [
        "LLC", "INC", "CORP", "TRUST", "LP", "LLP", "PARTNERSHIP",
        "HOLDINGS", "INVESTMENTS", "PROPERTIES", "GROUP", "CAPITAL",
        "VENTURES", "MANAGEMENT", "ASSOCIATES", "ENTERPRISES", "FUND", "REALTY"
    ])


def clean_name(name: str) -> str:
    """Standardize an owner name."""
    if not name or str(name).strip().upper() in ("NAN", "NONE", "", "NULL"):
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
    if not addr or str(addr).strip().upper() in ("NAN", "NONE", "", "NULL"):
        return ""
    addr = str(addr).upper().strip()
    addr = re.sub(r"\s+", " ", addr)
    return addr


def is_llc(name: str, keywords: list) -> bool:
    """Check if an owner name is a corporate entity."""
    if not name:
        return False
    upper = name.upper()
    return any(kw in upper for kw in keywords)


def is_residential(use_code: str, use_desc: str) -> bool:
    """
    Determine if a parcel is residential based on use code/description.

    NC OneMap use codes vary by county:
      - Wake uses short codes: RHS (residential), COM (commercial), VAC (vacant)
        with single-letter descriptions: R, C, V
      - Mecklenburg uses detailed codes: R100 (SFR), R300 (condo)
        with full descriptions: SINGLE FAMILY RESIDENTIAL
    """
    code_upper = str(use_code).strip().upper() if use_code else ""
    desc_upper = str(use_desc).strip().upper() if use_desc else ""

    # 1. Check by code — fastest and most reliable
    if code_upper in RESIDENTIAL_CODES:
        return True
    if code_upper in NON_RESIDENTIAL_CODES:
        return False

    # 2. Check by short description code (single-letter)
    if len(desc_upper) == 1:
        return desc_upper in RESIDENTIAL_DESC_CODES

    # 3. Check exclusion keywords in full descriptions
    for kw in EXCLUDE_KEYWORDS:
        if kw in desc_upper:
            return False

    # 4. Check inclusion keywords in full descriptions
    for kw in RESIDENTIAL_KEYWORDS:
        if kw in desc_upper:
            return True

    # 5. Codes starting with R are generally residential
    if code_upper and code_upper.startswith("R"):
        return True

    return False


def classify_use(use_code: str, use_desc: str) -> str:
    """
    Map NC use descriptions to standardized categories for ICP scoring.
    Returns a simple description string.
    """
    desc_upper = str(use_desc).upper() if use_desc else ""

    if any(kw in desc_upper for kw in ["DUPLEX", "TRIPLEX", "QUADRUPLEX",
                                         "MULTI-FAMILY", "MULTIFAMILY",
                                         "MULTI FAMILY"]):
        return "Multi-Family (2-9 units)"
    elif "APARTMENT" in desc_upper:
        return "Multi-Family (10+ units)"
    elif any(kw in desc_upper for kw in ["CONDO", "CONDOMINIUM"]):
        return "Condominium"
    elif any(kw in desc_upper for kw in ["TOWNHOUSE", "TOWNHOME"]):
        return "Townhouse"
    elif any(kw in desc_upper for kw in ["MOBILE", "MANUFACTURED"]):
        return "Mobile Home"
    elif any(kw in desc_upper for kw in ["SINGLE FAMILY", "RESIDENTIAL", "DWELLING"]):
        return "Single Family Residential"
    else:
        return use_desc if use_desc else "Residential"


def parse_sale_date(raw_date) -> str:
    """
    Parse NC OneMap sale date into YYYY-MM format.
    NC may provide epoch milliseconds, ISO dates, or text dates.
    """
    if not raw_date or str(raw_date).strip() in ("", "NAN", "NONE", "NULL", "0"):
        return ""

    raw = str(raw_date).strip()

    # Epoch milliseconds (common in ArcGIS JSON)
    try:
        ts = int(float(raw))
        if ts > 1_000_000_000_000:  # milliseconds
            ts = ts // 1000
        if 946684800 <= ts <= 2524608000:  # 2000-01-01 to 2050-01-01
            from datetime import datetime
            dt = datetime.utcfromtimestamp(ts)
            return dt.strftime("%Y-%m")
    except (ValueError, TypeError, OverflowError):
        pass

    # ISO date or similar
    for fmt in ["%Y-%m-%d", "%Y/%m/%d", "%m/%d/%Y", "%m-%d-%Y", "%Y%m%d"]:
        try:
            from datetime import datetime
            dt = datetime.strptime(raw[:10], fmt)
            return dt.strftime("%Y-%m")
        except (ValueError, IndexError):
            continue

    # Just a year
    if re.match(r"^\d{4}$", raw) and 1900 <= int(raw) <= 2030:
        return raw

    return ""


def parse_and_standardize(df: pd.DataFrame, county_name: str, llc_keywords: list) -> pd.DataFrame:
    """
    Main parsing logic for NC data. Produces output identical in schema
    to FL's 02_parse_nal.py so downstream scripts work unchanged.
    """

    # ---------------------------------------------------------------
    # 1. Rename columns using NC mapping
    # ---------------------------------------------------------------
    print("  Mapping NC OneMap columns to standard schema...")
    existing = set(df.columns)
    col_map = {k: v for k, v in NC_COLUMN_MAP.items() if k in existing}
    df = df.rename(columns=col_map)
    print(f"  Mapped {len(col_map)} columns")

    # ---------------------------------------------------------------
    # 1b. Fix composite address fields
    #     Some NC counties (Wake) embed city+state+zip in mcity field
    #     e.g. "HOLLY SPRINGS NC 27540-4452" instead of separate fields
    # ---------------------------------------------------------------
    print("  Fixing composite address fields...")

    if "mail_city" in df.columns:
        # Check if mail_state/mail_zip are mostly empty
        has_state = df.get("mail_state", pd.Series(dtype=str)).notna()
        state_fill = has_state.sum() if hasattr(has_state, 'sum') else 0
        total = len(df)

        if "mail_state" not in df.columns or df["mail_state"].isna().sum() > total * 0.5:
            # mcity likely contains "CITY STATE ZIP" format
            print("  Detected composite mcity field — parsing city/state/zip...")

            import re as _re

            def parse_composite_city(val):
                """Parse 'HOLLY SPRINGS NC 27540-4452' → (city, state, zip)"""
                if not val or str(val).strip().upper() in ("NAN", "NONE", "", "NULL"):
                    return "", "", ""
                s = str(val).strip()
                # Match: CITY_NAME STATE ZIP (with optional zip+4)
                m = _re.match(r'^(.+?)\s+([A-Z]{2})\s+(\d{5}(?:-\d{4})?)$', s)
                if m:
                    return m.group(1).strip(), m.group(2), m.group(3)[:5]
                # Match: CITY_NAME STATE (no zip)
                m = _re.match(r'^(.+?)\s+([A-Z]{2})$', s)
                if m:
                    return m.group(1).strip(), m.group(2), ""
                # No match — treat whole thing as city
                return s, "", ""

            parsed_cities = df["mail_city"].apply(parse_composite_city)
            df["mail_city"] = parsed_cities.apply(lambda x: x[0])
            df["mail_state"] = parsed_cities.apply(lambda x: x[1])

            # Only overwrite mail_zip if it was empty
            parsed_zips = parsed_cities.apply(lambda x: x[2])
            if "mail_zip" not in df.columns or df["mail_zip"].isna().all():
                df["mail_zip"] = parsed_zips
            else:
                empty_zips = df["mail_zip"].isna() | (df["mail_zip"].astype(str).str.strip() == "")
                df.loc[empty_zips, "mail_zip"] = parsed_zips[empty_zips]

            filled = (df["mail_state"] != "").sum()
            print(f"    Parsed {filled:,} mail state values from composite field")

    # ---------------------------------------------------------------
    # 2. Clean owner names
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
    # 3. Clean addresses
    # ---------------------------------------------------------------
    print("  Standardizing addresses...")
    for col in ["mail_street", "prop_street"]:
        if col in df.columns:
            df[col] = df[col].apply(clean_address)

    # Clean zip codes (first 5 digits)
    for col in ["mail_zip", "prop_zip"]:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip().str[:5]
            df[col] = df[col].str.replace(r"[^0-9]", "", regex=True)

    # Standardize state to 2-letter code
    if "mail_state" in df.columns:
        df["mail_state"] = df["mail_state"].astype(str).str.strip().str.upper()

    # ---------------------------------------------------------------
    # 4. Filter to residential properties
    # ---------------------------------------------------------------
    print("  Filtering to residential properties...")
    before_count = len(df)

    use_code_col = "use_code" if "use_code" in df.columns else None
    use_desc_col = "use_description" if "use_description" in df.columns else None

    if use_code_col or use_desc_col:
        mask = df.apply(
            lambda row: is_residential(
                row.get("use_code", ""),
                row.get("use_description", "")
            ),
            axis=1
        )
        df = df[mask].copy()
        print(f"  Filtered: {len(df):,} residential (dropped {before_count - len(df):,} non-residential)")

        # Standardize use descriptions
        df["use_description"] = df.apply(
            lambda row: classify_use(
                row.get("use_code", ""),
                row.get("use_description", "")
            ),
            axis=1
        )

    # ---------------------------------------------------------------
    # 5. Parse sale dates
    # ---------------------------------------------------------------
    print("  Parsing sale dates...")
    if "sale_date_raw" in df.columns:
        df["sale_date"] = df["sale_date_raw"].apply(parse_sale_date)
    elif "sale_date_text" in df.columns:
        df["sale_date"] = df["sale_date_text"].apply(parse_sale_date)
    else:
        df["sale_date"] = ""

    # ---------------------------------------------------------------
    # 6. Numeric conversions
    # ---------------------------------------------------------------
    for col in ["just_value", "present_value", "land_value", "improvement_value"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)

    # Use present_value as assessed_value (NC equivalent)
    if "present_value" in df.columns:
        df["assessed_value"] = df["present_value"]
    elif "just_value" in df.columns:
        df["assessed_value"] = df["just_value"]
    else:
        df["assessed_value"] = 0

    # NC OneMap doesn't have sale_price directly — leave blank
    # (can be enriched from county Register of Deeds later)
    if "sale_price" not in df.columns:
        df["sale_price"] = 0

    # ---------------------------------------------------------------
    # 7. NC does NOT have homestead exemption
    #    Set homestead_flag = "N" for all records
    # ---------------------------------------------------------------
    df["homestead_flag"] = "N"

    # ---------------------------------------------------------------
    # 8. Flag LLC / corporate owners
    # ---------------------------------------------------------------
    print("  Detecting LLC/Corp owners...")
    df["is_llc"] = df["owner_name_1"].apply(lambda x: is_llc(x, llc_keywords))
    llc_count = df["is_llc"].sum()
    print(f"    LLC/Corp/Trust owners: {llc_count:,}")

    # ---------------------------------------------------------------
    # 9. Flag absentee owners (NC-specific: mail_state != "NC")
    # ---------------------------------------------------------------
    print("  Detecting absentee owners...")
    df["is_absentee"] = False

    if "mail_state" in df.columns:
        state_vals = df["mail_state"].astype(str).str.strip().str.upper()
        out_of_state = (state_vals != "NC") & (state_vals != "") & (state_vals != "NAN")
        df.loc[out_of_state, "is_absentee"] = True

    if "mail_zip" in df.columns and "prop_zip" in df.columns:
        diff_zip = (
            (df["mail_zip"].astype(str).str.strip() != df["prop_zip"].astype(str).str.strip()) &
            (df["mail_zip"].astype(str).str.strip() != "") &
            (df["prop_zip"].astype(str).str.strip() != "")
        )
        df.loc[diff_zip, "is_absentee"] = True

    absentee_count = df["is_absentee"].sum()
    print(f"    Absentee owners: {absentee_count:,}")

    # ---------------------------------------------------------------
    # 10. No homestead in NC — always True (not a useful signal)
    # ---------------------------------------------------------------
    df["is_no_homestead"] = True

    # ---------------------------------------------------------------
    # 11. Flag potential cash buyers
    #     NC OneMap doesn't have sale_price, so we can't detect this
    #     from parcel data alone. Set False for now.
    # ---------------------------------------------------------------
    df["is_cash_buyer"] = False
    print("  Cash buyer detection: skipped (NC data lacks sale prices)")

    # ---------------------------------------------------------------
    # 12. Portfolio detection
    # ---------------------------------------------------------------
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

    portfolio_2_4 = (df["portfolio_tier"] == "small_portfolio").sum()
    portfolio_5_plus = (df["portfolio_tier"] == "large_portfolio").sum()
    print(f"    Portfolio 2-4 properties: {portfolio_2_4:,}")
    print(f"    Portfolio 5+ properties:  {portfolio_5_plus:,}")

    # ---------------------------------------------------------------
    # 13. Deduplicate by parcel_id
    # ---------------------------------------------------------------
    before_dedup = len(df)
    if "parcel_id" in df.columns and df["parcel_id"].ne("").any():
        df = df.drop_duplicates(subset=["parcel_id"], keep="first")
        dupes = before_dedup - len(df)
        if dupes > 0:
            print(f"  Removed {dupes:,} duplicate parcels")

    # ---------------------------------------------------------------
    # 14. Fill missing columns and select standard output
    # ---------------------------------------------------------------
    for col in STANDARD_COLUMNS:
        if col not in df.columns:
            df[col] = ""

    # NC doesn't have living_sqft/bedrooms/bathrooms in OneMap
    # These could come from county-specific downloads later
    for col in ["living_sqft", "bedrooms", "bathrooms"]:
        if col not in df.columns:
            df[col] = ""

    return df


def main():
    parser = argparse.ArgumentParser(
        description="Parse & standardize NC parcel data (NC Step 2)"
    )
    parser.add_argument(
        "--county",
        type=str,
        required=True,
        help='County name(s), comma-separated (e.g. "wake", "wake,mecklenburg") or "all"',
    )
    args = parser.parse_args()

    PARSED_DIR.mkdir(parents=True, exist_ok=True)

    llc_keywords = load_llc_keywords()
    county_arg = args.county.strip().lower()

    # Find raw files to process
    if county_arg == "all":
        raw_files = sorted(RAW_DIR.glob("*_raw.csv"))
    else:
        raw_files = []
        for name in county_arg.split(","):
            slug = name.strip().replace(" ", "_").replace("-", "_")
            matches = list(RAW_DIR.glob(f"{slug}_raw.*"))
            raw_files.extend(matches)

    if not raw_files:
        print(f"\nNo raw files found for '{county_arg}' in {RAW_DIR}/")
        print(f"Run NC Step 1 first: python scripts/nc_01_download_parcels.py --county {county_arg}")
        return

    print(f"\nFound {len(raw_files)} file(s) to parse.\n")

    for filepath in raw_files:
        county_name = filepath.stem.replace("_raw", "")

        print("=" * 60)
        print(f"  PARSING: {county_name.upper()}")
        print("=" * 60)

        # Load raw file
        print(f"  Loading: {filepath.name}")
        df = pd.read_csv(filepath, dtype=str, low_memory=False)
        print(f"  Loaded {len(df):,} rows, {len(df.columns)} columns")

        if df.empty:
            print("  WARNING: File is empty. Skipping.")
            continue

        # Parse and standardize
        parsed = parse_and_standardize(df, county_name, llc_keywords)

        # Save
        output_file = PARSED_DIR / f"{county_name}_parsed.csv"
        parsed.to_csv(output_file, index=False)

        print()
        print(f"  SAVED: {output_file}")
        print(f"  Total records: {len(parsed):,}")
        print()

        # Summary
        print("  SUMMARY")
        print("  " + "-" * 40)
        print(f"  Total properties:      {len(parsed):,}")
        print(f"  LLC/Corp owned:        {parsed['is_llc'].sum():,}")
        print(f"  Absentee owners:       {parsed['is_absentee'].sum():,}")
        print(f"  Non-homesteaded:       {parsed['is_no_homestead'].sum():,} (all — NC has no homestead)")
        print(f"  Portfolio (2-4 props):  {(parsed['portfolio_tier'] == 'small_portfolio').sum():,}")
        print(f"  Portfolio (5+ props):   {(parsed['portfolio_tier'] == 'large_portfolio').sum():,}")
        print()

    print("=" * 60)
    print(f"  Next step: python scripts/03_filter_icp.py --county {county_arg} --state NC")
    print("=" * 60)


if __name__ == "__main__":
    main()
