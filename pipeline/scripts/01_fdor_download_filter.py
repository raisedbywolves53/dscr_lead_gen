"""
Module 1: FDOR NAL/SDF Download and Filter

Downloads FL Department of Revenue property data files,
filters for non-owner-occupied residential investment properties,
and produces a clean investor dataset.

Usage:
    python scripts/01_fdor_download_filter.py --counties "PALM BEACH,BROWARD,MIAMI-DADE"
    python scripts/01_fdor_download_filter.py --all-counties
"""

import os
import sys
import csv
import zipfile
import argparse
import requests
import pandas as pd
from pathlib import Path
from io import BytesIO

# County codes mapping — FDOR uses codes 11-77 (alphabetical)
# County names here must match FDOR file naming (e.g., "Dade" not "Miami-Dade",
# "Saint Johns" not "St. Johns")
FL_COUNTIES = {
    "ALACHUA": "11", "BAKER": "12", "BAY": "13", "BRADFORD": "14",
    "BREVARD": "15", "BROWARD": "16", "CALHOUN": "17", "CHARLOTTE": "18",
    "CITRUS": "19", "CLAY": "20", "COLLIER": "21", "COLUMBIA": "22",
    "DADE": "23", "MIAMI-DADE": "23", "DESOTO": "24", "DIXIE": "25",
    "DUVAL": "26", "ESCAMBIA": "27", "FLAGLER": "28", "FRANKLIN": "29",
    "GADSDEN": "30", "GILCHRIST": "31", "GLADES": "32", "GULF": "33",
    "HAMILTON": "34", "HARDEE": "35", "HENDRY": "36", "HERNANDO": "37",
    "HIGHLANDS": "38", "HILLSBOROUGH": "39", "HOLMES": "40",
    "INDIAN RIVER": "41", "JACKSON": "42", "JEFFERSON": "43",
    "LAFAYETTE": "44", "LAKE": "45", "LEE": "46", "LEON": "47",
    "LEVY": "48", "LIBERTY": "49", "MADISON": "50", "MANATEE": "51",
    "MARION": "52", "MARTIN": "53", "MONROE": "54",
    "NASSAU": "55", "OKALOOSA": "56", "OKEECHOBEE": "57", "ORANGE": "58",
    "OSCEOLA": "59", "PALM BEACH": "60", "PASCO": "61", "PINELLAS": "62",
    "POLK": "63", "PUTNAM": "64", "SAINT JOHNS": "65", "ST. JOHNS": "65",
    "SAINT LUCIE": "66", "ST. LUCIE": "66", "SANTA ROSA": "67",
    "SARASOTA": "68", "SEMINOLE": "69", "SUMTER": "70", "SUWANNEE": "71",
    "TAYLOR": "72", "UNION": "73", "VOLUSIA": "74", "WAKULLA": "75",
    "WALTON": "76", "WASHINGTON": "77"
}

# Map user-friendly names to FDOR file names (FDOR uses "Dade", "Saint Johns", etc.)
FDOR_COUNTY_NAMES = {
    "MIAMI-DADE": "Dade", "ST. JOHNS": "Saint Johns", "ST. LUCIE": "Saint Lucie",
    "DESOTO": "Desoto",
}

# Target DOR use codes for residential investment properties
# FDOR files use 1-3 digit codes; we normalize to int for matching
RESIDENTIAL_USE_CODES = {1, 2, 3, 4, 8}

# Entity ownership indicators
ENTITY_KEYWORDS = [
    " LLC", " L.L.C", " INC", " CORP", " TRUST", " LP ", " LTD",
    " HOLDINGS", " PROPERTIES", " INVESTMENTS", " CAPITAL", " VENTURES",
    " PARTNERS", " PARTNERSHIP", " ASSOCIATION", " FUND", " GROUP",
    " ENTERPRISES", " REALTY", " REAL ESTATE", " MANAGEMENT"
]

DATA_DIR = Path("pipeline/data/fdor")
OUTPUT_DIR = Path("pipeline/output")


def download_nal_file(county_name: str, county_code: str) -> pd.DataFrame:
    """Download and parse NAL file for a single county."""

    base_url = "https://floridarevenue.com/property/dataportal/Documents/"
    base_url += "PTO%20Data%20Portal/Tax%20Roll%20Data%20Files/NAL/2025F/"

    # Use FDOR-canonical county name for file naming
    fdor_name = FDOR_COUNTY_NAMES.get(county_name.upper(), county_name.title())

    # FDOR naming pattern: "{County Name} {Code} Final NAL 2025.zip"
    filename_patterns = [
        f"{fdor_name} {county_code} Final NAL 2025.zip",
        f"{fdor_name}%20{county_code}%20Final%20NAL%202025.zip",
    ]

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    local_zip = DATA_DIR / f"NAL_{county_code}_{county_name.replace(' ', '_')}.zip"
    local_csv = DATA_DIR / f"NAL_{county_code}_{county_name.replace(' ', '_')}.csv"

    # If already downloaded and extracted, load from disk
    if local_csv.exists():
        print(f"  Loading cached NAL for {county_name}...")
        return pd.read_csv(local_csv, dtype=str, low_memory=False)

    # Download
    print(f"  Downloading NAL for {county_name} (code {county_code}, file: {fdor_name})...")
    downloaded = False
    for pattern in filename_patterns:
        url = base_url + pattern
        try:
            resp = requests.get(url, timeout=120, headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
            })
            if resp.status_code == 200:
                with open(local_zip, 'wb') as f:
                    f.write(resp.content)
                downloaded = True
                print(f"  Downloaded ({len(resp.content) / 1024 / 1024:.1f} MB)")
                break
            else:
                print(f"  Tried: {pattern} -> HTTP {resp.status_code}")
        except requests.RequestException as e:
            print(f"  Tried: {pattern} -> Error: {e}")
            continue

    if not downloaded:
        print(f"  WARNING: Could not download NAL for {county_name}. Skipping.")
        return pd.DataFrame()

    # Extract ZIP
    print(f"  Extracting...")
    with zipfile.ZipFile(local_zip, 'r') as z:
        csv_files = [f for f in z.namelist() if f.endswith('.csv') or f.endswith('.CSV')]
        if not csv_files:
            # Try .txt files
            csv_files = [f for f in z.namelist() if f.endswith('.txt') or f.endswith('.TXT')]

        if not csv_files:
            print(f"  WARNING: No CSV/TXT found in ZIP for {county_name}. Files: {z.namelist()}")
            return pd.DataFrame()

        z.extract(csv_files[0], DATA_DIR)
        extracted_path = DATA_DIR / csv_files[0]
        extracted_path.rename(local_csv)

    return pd.read_csv(local_csv, dtype=str, low_memory=False)


def download_sdf_file(county_name: str, county_code: str) -> pd.DataFrame:
    """Download and parse SDF (sales) file for a single county."""

    base_url = "https://floridarevenue.com/property/dataportal/Documents/"
    base_url += "PTO%20Data%20Portal/Tax%20Roll%20Data%20Files/SDF/2025F/"

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    local_csv = DATA_DIR / f"SDF_{county_code}_{county_name.replace(' ', '_')}.csv"

    if local_csv.exists():
        print(f"  Loading cached SDF for {county_name}...")
        return pd.read_csv(local_csv, dtype=str, low_memory=False)

    # Use FDOR-canonical county name for file naming
    fdor_name = FDOR_COUNTY_NAMES.get(county_name.upper(), county_name.title())

    filename_patterns = [
        f"{fdor_name} {county_code} Final SDF 2025.zip",
        f"{fdor_name}%20{county_code}%20Final%20SDF%202025.zip",
    ]

    local_zip = DATA_DIR / f"SDF_{county_code}_{county_name.replace(' ', '_')}.zip"

    downloaded = False
    for pattern in filename_patterns:
        url = base_url + pattern
        try:
            resp = requests.get(url, timeout=120)
            if resp.status_code == 200:
                with open(local_zip, 'wb') as f:
                    f.write(resp.content)
                downloaded = True
                break
        except requests.RequestException:
            continue

    if not downloaded:
        print(f"  WARNING: Could not download SDF for {county_name}. Skipping.")
        return pd.DataFrame()

    with zipfile.ZipFile(local_zip, 'r') as z:
        csv_files = [f for f in z.namelist() if f.endswith('.csv') or f.endswith('.CSV') or f.endswith('.txt')]
        if csv_files:
            z.extract(csv_files[0], DATA_DIR)
            extracted_path = DATA_DIR / csv_files[0]
            extracted_path.rename(local_csv)

    return pd.read_csv(local_csv, dtype=str, low_memory=False)


def is_entity_owned(owner_name: str) -> bool:
    """Check if property is owned by a corporate entity."""
    if not owner_name:
        return False
    upper = owner_name.upper()
    return any(kw in upper for kw in ENTITY_KEYWORDS)


def filter_investment_properties(nal_df: pd.DataFrame) -> pd.DataFrame:
    """
    Filter NAL data for non-owner-occupied residential investment properties.

    Three signals combined:
    1. Homestead exemption = 0 (not primary residence)
    2. Mailing address != site address (absentee owner)
    3. Entity ownership (LLC, Corp, Trust)
    """

    if nal_df.empty:
        return nal_df

    # Standardize column names only if they don't already exist
    # FDOR 2025 NAL files have: DOR_UC, AV_HMSTD, JV as standard columns
    col_map = {}
    cols_upper = {c.upper().strip() for c in nal_df.columns}

    if 'DOR_UC' not in cols_upper:
        for col in nal_df.columns:
            if 'DOR' in col.upper() and 'UC' in col.upper():
                col_map[col] = 'DOR_UC'
                break

    if 'AV_HMSTD' not in cols_upper:
        for col in nal_df.columns:
            if col.upper().strip() == 'HOMESTEAD_VAL':
                col_map[col] = 'AV_HMSTD'
                break

    if 'JV' not in cols_upper:
        for col in nal_df.columns:
            if col.upper().strip() in ('JUST_VAL', 'JUST_VALUE'):
                col_map[col] = 'JV'
                break

    if col_map:
        nal_df = nal_df.rename(columns=col_map)

    print(f"  Total parcels: {len(nal_df):,}")

    # Step 1: Filter to residential use codes
    if 'DOR_UC' in nal_df.columns:
        nal_df['DOR_UC_INT'] = pd.to_numeric(nal_df['DOR_UC'].astype(str).str.strip(), errors='coerce').fillna(-1).astype(int)
        residential = nal_df[nal_df['DOR_UC_INT'].isin(RESIDENTIAL_USE_CODES)].copy()
        print(f"  Residential parcels: {len(residential):,}")
    else:
        print("  WARNING: DOR_UC column not found. Using all parcels.")
        residential = nal_df.copy()

    # Step 2: Filter out homesteaded properties
    if 'AV_HMSTD' in residential.columns:
        residential['AV_HMSTD'] = pd.to_numeric(residential['AV_HMSTD'], errors='coerce').fillna(0)
        non_homestead = residential[residential['AV_HMSTD'] == 0].copy()
        print(f"  Non-homesteaded: {len(non_homestead):,}")
    else:
        print("  WARNING: Homestead column not found. Using all residential.")
        non_homestead = residential.copy()

    # Step 3: Flag entity ownership
    owner_col = None
    for col in non_homestead.columns:
        if 'OWN' in col.upper() and 'NAME' in col.upper():
            owner_col = col
            break
        elif col.upper() in ('OWN_NAME', 'OWNER', 'OWNER_NAME'):
            owner_col = col
            break

    if owner_col:
        non_homestead['is_entity'] = non_homestead[owner_col].apply(
            lambda x: is_entity_owned(str(x)) if pd.notna(x) else False
        )
        entity_count = non_homestead['is_entity'].sum()
        print(f"  Entity-owned: {entity_count:,}")

    # Step 4: Flag absentee owners (mailing != site/physical address)
    mail_cols = [c for c in non_homestead.columns if 'MAIL' in c.upper() or ('OWN' in c.upper() and 'ADDR' in c.upper())]
    site_cols = [c for c in non_homestead.columns if ('SITE' in c.upper() or 'PHY' in c.upper()) and 'ADDR' in c.upper()]

    if mail_cols and site_cols:
        non_homestead['is_absentee'] = (
            non_homestead[mail_cols[0]].astype(str).str.upper().str.strip() !=
            non_homestead[site_cols[0]].astype(str).str.upper().str.strip()
        )
        absentee_count = non_homestead['is_absentee'].sum()
        print(f"  Absentee owners: {absentee_count:,}")

    # Step 5: Flag out-of-state and foreign owners
    # Prefer OWN_STATE_DOM (2-letter codes like FL, NY, FC) over OWN_STATE (full names)
    state_col = None
    for col in non_homestead.columns:
        if col.upper().strip() == 'OWN_STATE_DOM':
            state_col = col
            break
    if not state_col:
        for col in non_homestead.columns:
            if ('OWN' in col.upper() or 'MAIL' in col.upper()) and 'STATE' in col.upper():
                state_col = col
                break

    if state_col:
        state_vals = non_homestead[state_col].astype(str).str.strip().str.upper()

        us_state_codes = {
            'AL','AK','AZ','AR','CA','CO','CT','DE','FL','GA','HI','ID','IL','IN',
            'IA','KS','KY','LA','ME','MD','MA','MI','MN','MS','MO','MT','NE','NV',
            'NH','NJ','NM','NY','NC','ND','OH','OK','OR','PA','RI','SC','SD','TN',
            'TX','UT','VT','VA','WA','WV','WI','WY','DC','PR','VI','GU','AS','MP'
        }

        non_homestead['out_of_state'] = (state_vals != 'FL') & (state_vals != '') & (state_vals != 'NAN')
        non_homestead['foreign_owner'] = ~state_vals.isin(us_state_codes) & (state_vals != '') & (state_vals != 'NAN')

        oos_count = non_homestead['out_of_state'].sum()
        foreign_count = non_homestead['foreign_owner'].sum()
        print(f"  Out-of-state owners: {oos_count:,}")
        print(f"  Foreign owners: {foreign_count:,}")

    return non_homestead


def aggregate_by_owner(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate property-level records to owner-level.
    One row per unique owner with property count and portfolio value.
    """

    # Find owner name column
    owner_col = None
    for col in df.columns:
        if 'OWN' in col.upper() and 'NAME' in col.upper():
            owner_col = col
            break

    if not owner_col:
        print("  WARNING: Cannot find owner name column for aggregation.")
        return df

    # Find value column
    value_col = None
    for col in df.columns:
        if col.upper() in ('JV', 'JUST_VAL', 'JV_HMSTD', 'JUST_VALUE'):
            value_col = col
            break

    # Find address columns
    mail_addr = [c for c in df.columns if ('OWN' in c.upper() or 'MAIL' in c.upper()) and 'ADDR' in c.upper()]
    mail_city = [c for c in df.columns if ('OWN' in c.upper() or 'MAIL' in c.upper()) and 'CITY' in c.upper()]
    mail_state = [c for c in df.columns if ('OWN' in c.upper() or 'MAIL' in c.upper()) and 'STATE' in c.upper()]
    mail_zip = [c for c in df.columns if ('OWN' in c.upper() or 'MAIL' in c.upper()) and 'ZIP' in c.upper()]

    site_addr = [c for c in df.columns if ('SITE' in c.upper() or 'PHY' in c.upper()) and 'ADDR' in c.upper()]
    county_col = [c for c in df.columns if c.upper() in ('CO_NO', 'COUNTY', 'COUNTY_CODE')]
    parcel_col = [c for c in df.columns if 'PARCEL' in c.upper()]
    dor_col = [c for c in df.columns if 'DOR' in c.upper()]

    # Build aggregation
    agg_dict = {}

    if parcel_col:
        agg_dict[parcel_col[0]] = 'count'  # property_count

    if value_col:
        df[value_col] = pd.to_numeric(df[value_col], errors='coerce').fillna(0)
        agg_dict[value_col] = 'sum'  # total_portfolio_value

    if site_addr:
        agg_dict[site_addr[0]] = lambda x: ' | '.join(x.dropna().unique()[:5])  # first 5 property addresses

    if dor_col:
        agg_dict[dor_col[0]] = lambda x: ','.join(sorted(x.dropna().unique()))  # property types

    # Group by owner
    group_cols = [owner_col]
    if mail_addr: group_cols.append(mail_addr[0])
    if mail_city: group_cols.append(mail_city[0])
    if mail_state: group_cols.append(mail_state[0])
    if mail_zip: group_cols.append(mail_zip[0])

    # Add flags to group (take max = True if any property has the flag)
    flag_cols = ['is_entity', 'is_absentee', 'out_of_state', 'foreign_owner']
    for fc in flag_cols:
        if fc in df.columns:
            agg_dict[fc] = 'max'

    if county_col:
        agg_dict[county_col[0]] = lambda x: ','.join(sorted(x.dropna().unique()))

    if not agg_dict:
        return df

    grouped = df.groupby(group_cols, dropna=False).agg(agg_dict).reset_index()

    # Rename aggregated columns
    if parcel_col:
        grouped = grouped.rename(columns={parcel_col[0]: 'property_count'})
    if value_col:
        grouped = grouped.rename(columns={value_col: 'total_portfolio_value'})

    print(f"  Unique owners: {len(grouped):,}")

    return grouped


def main():
    parser = argparse.ArgumentParser(description='Download and filter FDOR property data')
    parser.add_argument('--counties', type=str, default='PALM BEACH',
                        help='Comma-separated county names (default: PALM BEACH)')
    parser.add_argument('--all-counties', action='store_true',
                        help='Process all 67 FL counties')
    parser.add_argument('--output', type=str, default='pipeline/output/01_investor_properties.csv',
                        help='Output CSV file path')

    args = parser.parse_args()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    if args.all_counties:
        counties = list(FL_COUNTIES.items())
    else:
        county_names = [c.strip().upper() for c in args.counties.split(',')]
        counties = [(name, FL_COUNTIES.get(name, '')) for name in county_names]
        counties = [(n, c) for n, c in counties if c]

    print(f"Processing {len(counties)} counties...")

    all_investors = []

    for county_name, county_code in counties:
        print(f"\n{'='*60}")
        print(f"COUNTY: {county_name} (Code {county_code})")
        print(f"{'='*60}")

        # Download NAL
        nal_df = download_nal_file(county_name, county_code)
        if nal_df.empty:
            continue

        # Filter for investment properties
        investors = filter_investment_properties(nal_df)

        # Aggregate by owner
        owner_level = aggregate_by_owner(investors)

        all_investors.append(owner_level)

    if all_investors:
        combined = pd.concat(all_investors, ignore_index=True)

        # Sort by property count descending
        if 'property_count' in combined.columns:
            combined = combined.sort_values('property_count', ascending=False)

        combined.to_csv(args.output, index=False)
        print(f"\n{'='*60}")
        print(f"OUTPUT: {args.output}")
        print(f"Total investor leads: {len(combined):,}")
        print(f"{'='*60}")
    else:
        print("No data collected.")


if __name__ == '__main__':
    main()
