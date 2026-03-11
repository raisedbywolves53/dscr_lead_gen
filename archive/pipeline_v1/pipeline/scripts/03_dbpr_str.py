"""
Module 3: DBPR Vacation Rental License Data

Downloads FL DBPR lodging data, extracts vacation rental operators,
and cross-references with property records to tag STR operators.

Usage:
    python scripts/03_dbpr_str.py --input pipeline/output/02_resolved_entities.csv --output pipeline/output/03_str_tagged.csv
"""

import os
import csv
import argparse
import requests
import pandas as pd
from pathlib import Path
from bs4 import BeautifulSoup
import re
import time

DATA_DIR = Path("pipeline/data/dbpr")
OUTPUT_DIR = Path("pipeline/output")


def download_dbpr_data() -> pd.DataFrame:
    """
    Download DBPR lodging public records CSV files.

    The DBPR provides CSV extracts on their lodging public records page.
    This function attempts to download and parse those files.
    """

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    cached_file = DATA_DIR / "dbpr_vacation_rentals.csv"

    if cached_file.exists():
        print("Loading cached DBPR data...")
        return pd.read_csv(cached_file, dtype=str, low_memory=False)

    print("Downloading DBPR lodging data...")

    # The DBPR lodging public records page has download links
    # We need to scrape the page to find the CSV download URLs
    base_url = "https://www2.myfloridalicense.com/hotels-restaurants/lodging-public-records/"

    headers = {
        'User-Agent': 'DSCR-Lead-Gen-Research contact@example.com'
    }

    try:
        resp = requests.get(base_url, headers=headers, timeout=30)
        if resp.status_code != 200:
            print(f"  Failed to access DBPR page: {resp.status_code}")
            return try_dbpr_license_search()

        soup = BeautifulSoup(resp.text, 'html.parser')

        # Find CSV download links
        csv_links = []
        for link in soup.find_all('a', href=True):
            href = link['href']
            if href.endswith('.csv') or 'csv' in href.lower() or 'extract' in href.lower():
                if not href.startswith('http'):
                    href = 'https://www2.myfloridalicense.com' + href
                csv_links.append(href)

        if not csv_links:
            print("  No CSV links found on DBPR page. Trying license search...")
            return try_dbpr_license_search()

        # Download each CSV and combine
        all_dfs = []
        for link in csv_links:
            print(f"  Downloading: {link}")
            try:
                csv_resp = requests.get(link, headers=headers, timeout=60)
                if csv_resp.status_code == 200:
                    # Parse CSV from response text
                    from io import StringIO
                    df = pd.read_csv(StringIO(csv_resp.text), dtype=str, low_memory=False)
                    all_dfs.append(df)
                time.sleep(1)
            except Exception as e:
                print(f"    Failed: {e}")
                continue

        if all_dfs:
            combined = pd.concat(all_dfs, ignore_index=True)
            combined.to_csv(cached_file, index=False)
            return combined

    except Exception as e:
        print(f"  Error accessing DBPR: {e}")

    return try_dbpr_license_search()


def try_dbpr_license_search() -> pd.DataFrame:
    """
    Fallback: Use DBPR license search to find vacation rental licenses.
    This is slower but more reliable than trying to find CSV links.
    """

    print("Using DBPR license search fallback...")

    # Search for vacation rental licenses by county
    # This approach queries the DBPR search API
    search_url = "https://www.myfloridalicense.com/wl11.asp"

    all_records = []

    # Search for vacation rental dwelling and condo licenses
    license_types = [
        ('2010', 'Vacation Rental - Dwelling'),
        ('2011', 'Vacation Rental - Condo'),
    ]

    headers = {
        'User-Agent': 'DSCR-Lead-Gen-Research contact@example.com'
    }

    for lic_type_code, lic_type_name in license_types:
        print(f"  Searching for: {lic_type_name}")

        params = {
            'mode': '1',
            'brd': 'H',  # Hotels & Restaurants board
            'typ': lic_type_code,
            'SRV': '',
            'cnty': '',  # All counties
            'status': 'Active',
        }

        try:
            resp = requests.get(search_url, params=params, headers=headers, timeout=60)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, 'html.parser')

                # Parse results table
                tables = soup.find_all('table')
                for table in tables:
                    rows = table.find_all('tr')
                    for row in rows[1:]:  # Skip header
                        cells = row.find_all('td')
                        if len(cells) >= 4:
                            record = {
                                'license_number': cells[0].get_text(strip=True),
                                'licensee_name': cells[1].get_text(strip=True),
                                'facility_address': cells[2].get_text(strip=True) if len(cells) > 2 else '',
                                'license_type': lic_type_name,
                                'status': 'Active',
                            }
                            all_records.append(record)

            time.sleep(2)
        except Exception as e:
            print(f"    Error: {e}")
            continue

    if all_records:
        df = pd.DataFrame(all_records)
        cached_file = DATA_DIR / "dbpr_vacation_rentals.csv"
        df.to_csv(cached_file, index=False)
        print(f"  Found {len(df):,} vacation rental licenses")
        return df

    print("  No DBPR data retrieved. Creating empty dataset.")
    return pd.DataFrame()


def normalize_address(addr: str) -> str:
    """Normalize address for matching."""
    if not addr or pd.isna(addr):
        return ''
    addr = str(addr).upper().strip()
    # Remove common abbreviation variations
    replacements = {
        ' STREET': ' ST', ' AVENUE': ' AVE', ' BOULEVARD': ' BLVD',
        ' DRIVE': ' DR', ' ROAD': ' RD', ' LANE': ' LN',
        ' COURT': ' CT', ' CIRCLE': ' CIR', ' PLACE': ' PL',
        ' TERRACE': ' TER', ' TRAIL': ' TRL', ' WAY': ' WAY',
        ' NORTH': ' N', ' SOUTH': ' S', ' EAST': ' E', ' WEST': ' W',
        ' APARTMENT': ' APT', ' SUITE': ' STE', ' UNIT': ' UNIT',
        '.': '', ',': '', '#': ' ',
    }
    for old, new in replacements.items():
        addr = addr.replace(old, new)
    # Collapse whitespace
    addr = ' '.join(addr.split())
    return addr


def normalize_name(name: str) -> str:
    """Normalize owner/licensee name for matching."""
    if not name or pd.isna(name):
        return ''
    name = str(name).upper().strip()
    # Remove common entity suffixes for matching
    for suffix in [' LLC', ' L.L.C.', ' INC', ' INC.', ' CORP', ' CORP.', ' LP', ' LTD', ' CO']:
        name = name.replace(suffix, '')
    name = ' '.join(name.split())
    return name


def match_str_to_properties(investor_df: pd.DataFrame, dbpr_df: pd.DataFrame) -> pd.DataFrame:
    """
    Cross-reference DBPR vacation rental licenses with investor property records.

    Matching strategy (in priority order):
    1. Exact address match (facility address = property site address)
    2. Owner name match (licensee name = property owner name)
    3. Address + name fuzzy match
    """

    if dbpr_df.empty:
        print("No DBPR data to match. Skipping STR tagging.")
        investor_df['str_licensed'] = False
        investor_df['str_license_count'] = 0
        investor_df['str_phone'] = ''
        investor_df['str_email'] = ''
        return investor_df

    print(f"Matching {len(dbpr_df):,} STR licenses against {len(investor_df):,} investor records...")

    # Normalize addresses and names in DBPR data
    # Prefer 'Location Street Address' (200K rows) over 'Location Address' (17K rows)
    addr_col = None
    for col in dbpr_df.columns:
        if col.strip().upper() == 'LOCATION STREET ADDRESS':
            addr_col = col
            break
    if not addr_col:
        for col in dbpr_df.columns:
            if 'FACILITY' in col.upper() and 'ADDR' in col.upper():
                addr_col = col
                break
            elif 'STREET' in col.upper() and 'ADDRESS' in col.upper() and 'MAIL' not in col.upper():
                addr_col = col
                break
            elif 'ADDRESS' in col.upper() and 'MAIL' not in col.upper() and 'LINE' not in col.upper():
                addr_col = col
                break

    # Prefer 'Licensee Name' (206K) over other name columns
    name_col = None
    for col in dbpr_df.columns:
        if col.strip().upper() == 'LICENSEE NAME':
            name_col = col
            break
    if not name_col:
        for col in dbpr_df.columns:
            if 'LICENSEE' in col.upper() or ('NAME' in col.upper() and 'DBA' not in col.upper() and 'COUNTY' not in col.upper()):
                name_col = col
                break

    print(f"  DBPR addr column: {addr_col} ({dbpr_df[addr_col].notna().sum():,} non-null)" if addr_col else "  DBPR addr column: NOT FOUND")
    print(f"  DBPR name column: {name_col} ({dbpr_df[name_col].notna().sum():,} non-null)" if name_col else "  DBPR name column: NOT FOUND")

    phone_col = None
    for col in dbpr_df.columns:
        if col.strip().upper() == 'PRIMARY PHONE NUMBER':
            phone_col = col
            break
    if not phone_col:
        for col in dbpr_df.columns:
            if 'PHONE' in col.upper():
                phone_col = col
                break

    email_col = None
    for col in dbpr_df.columns:
        if 'EMAIL' in col.upper():
            email_col = col
            break

    print(f"  DBPR phone column: {phone_col} ({dbpr_df[phone_col].notna().sum():,} non-null)" if phone_col else "  DBPR phone column: NOT FOUND")
    print(f"  DBPR email column: {email_col}" if email_col else "  DBPR email column: NOT FOUND")

    if addr_col:
        dbpr_df['norm_addr'] = dbpr_df[addr_col].apply(normalize_address)
    if name_col:
        dbpr_df['norm_name'] = dbpr_df[name_col].apply(normalize_name)

    # Normalize in investor data
    # PHY_ADDR1 may contain pipe-delimited addresses from aggregation
    site_addr_col = None
    for col in investor_df.columns:
        if col.upper() in ('PHY_ADDR1', 'PHY_ADDR'):
            site_addr_col = col
            break
    if not site_addr_col:
        for col in investor_df.columns:
            if ('SITE' in col.upper() or 'PHY' in col.upper()) and 'ADDR' in col.upper():
                site_addr_col = col
                break

    owner_name_col = None
    for col in investor_df.columns:
        if 'OWN' in col.upper() and 'NAME' in col.upper():
            owner_name_col = col
            break

    # For investor data, build a set of normalized addresses per row
    # PHY_ADDR1 may contain "addr1 | addr2 | addr3" pipe-delimited
    if site_addr_col:
        def normalize_multi_addr(val):
            if not val or pd.isna(val):
                return []
            addrs = str(val).split(' | ')
            return [normalize_address(a) for a in addrs if a.strip()]
        investor_df['_norm_addrs'] = investor_df[site_addr_col].apply(normalize_multi_addr)

    if owner_name_col:
        investor_df['norm_owner_name'] = investor_df[owner_name_col].apply(normalize_name)

    # Build lookup sets for fast matching
    str_addresses = set(dbpr_df['norm_addr'].dropna().unique()) if 'norm_addr' in dbpr_df.columns else set()
    str_names = set(dbpr_df['norm_name'].dropna().unique()) if 'norm_name' in dbpr_df.columns else set()

    print(f"  DBPR normalized addresses: {len(str_addresses):,}")
    print(f"  DBPR normalized names: {len(str_names):,}")

    # Build name-to-contact lookup
    name_to_phone = {}
    name_to_email = {}
    if name_col and phone_col:
        for _, row in dbpr_df.iterrows():
            nm = normalize_name(str(row.get(name_col, '')))
            ph = str(row.get(phone_col, '')).strip()
            if nm and ph and ph != 'nan':
                name_to_phone[nm] = ph
    if name_col and email_col:
        for _, row in dbpr_df.iterrows():
            nm = normalize_name(str(row.get(name_col, '')))
            em = str(row.get(email_col, '')).strip()
            if nm and em and em != 'nan':
                name_to_email[nm] = em

    # Match
    investor_df['str_licensed'] = False
    investor_df['str_license_count'] = 0
    investor_df['str_phone'] = ''
    investor_df['str_email'] = ''

    match_count = 0
    addr_matches = 0
    name_matches = 0
    for idx, row in investor_df.iterrows():
        matched = False

        # Try address match (check each property address in pipe-delimited list)
        if '_norm_addrs' in investor_df.columns:
            addrs = row.get('_norm_addrs', [])
            if isinstance(addrs, list):
                for addr in addrs:
                    if addr and addr in str_addresses:
                        matched = True
                        addr_matches += 1
                        break

        # Try name match
        if not matched and 'norm_owner_name' in investor_df.columns:
            name = row.get('norm_owner_name', '')
            if name and name in str_names:
                matched = True
                name_matches += 1

        if matched:
            investor_df.at[idx, 'str_licensed'] = True
            match_count += 1

            # Add phone/email from DBPR if available
            name = row.get('norm_owner_name', '')
            if name in name_to_phone:
                investor_df.at[idx, 'str_phone'] = name_to_phone[name]
            if name in name_to_email:
                investor_df.at[idx, 'str_email'] = name_to_email[name]

    print(f"  Address matches: {addr_matches:,}")
    print(f"  Name matches: {name_matches:,}")

    # Count licenses per owner
    if name_col:
        license_counts = dbpr_df.groupby('norm_name').size().to_dict()
        for idx, row in investor_df.iterrows():
            name = row.get('norm_owner_name', '')
            if name in license_counts:
                investor_df.at[idx, 'str_license_count'] = license_counts[name]

    # Clean up temp columns
    for col in ['norm_site_addr', 'norm_owner_name', '_norm_addrs']:
        if col in investor_df.columns:
            investor_df.drop(columns=[col], inplace=True)

    print(f"  STR matches found: {match_count:,}")
    print(f"  With phone from DBPR: {(investor_df['str_phone'] != '').sum():,}")
    print(f"  With email from DBPR: {(investor_df['str_email'] != '').sum():,}")

    return investor_df


def main():
    parser = argparse.ArgumentParser(description='DBPR STR operator identification')
    parser.add_argument('--input', type=str, default='pipeline/output/02_resolved_entities.csv')
    parser.add_argument('--output', type=str, default='pipeline/output/03_str_tagged.csv')

    args = parser.parse_args()

    # Download DBPR data
    dbpr_df = download_dbpr_data()
    print(f"DBPR records loaded: {len(dbpr_df):,}")

    # Load investor data and match
    investor_df = pd.read_csv(args.input, dtype=str, low_memory=False)
    result = match_str_to_properties(investor_df, dbpr_df)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    result.to_csv(args.output, index=False)
    print(f"\nOutput saved: {args.output}")


if __name__ == '__main__':
    main()
