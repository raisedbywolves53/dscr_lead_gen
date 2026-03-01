# Module 3: DBPR Vacation Rental License Data

## Purpose
Download FL Department of Business & Professional Regulation (DBPR) lodging license data, extract vacation rental operators, and cross-reference with property records from Module 1 to tag STR operators.

## Data Source

**DBPR Lodging Public Records:**
- Portal: https://www2.myfloridalicense.com/hotels-restaurants/lodging-public-records/
- Format: CSV files organized by county/district
- Updates: Weekly
- License types of interest:
  - **Vacation Rental - Dwelling** (standalone houses/units)
  - **Vacation Rental - Condo** (condo units)

**DBPR License Search (Fallback):**
- URL: https://www.myfloridalicense.com/wl11.asp?mode=1&brd=H&typ=
- Board: Hotels & Restaurants
- Filter by license type: Vacation Rental

## Fields Available in DBPR CSV

| Field | Description | Use |
|---|---|---|
| License Number | DBPR license ID | Unique identifier |
| Licensee Name | Individual or entity name | Match to FDOR owner |
| DBA Name | "Doing Business As" name | Additional identifier |
| License Type | Vacation Rental - Dwelling/Condo | STR classification |
| Status | Active, Inactive, Expired | Filter for active |
| Facility Address | Physical location of rental | Match to property address |
| Facility City | City | Geographic matching |
| Facility County | County name | County matching |
| Mailing Address | Owner mailing address | Contact info |
| Phone | Business phone number | **Direct contact** |
| Email | Contact email (sometimes available) | **Direct contact** |
| Expiration Date | License expiry | Activity indicator |
| Number of Units | Rental unit count | Scale indicator |

## Script: `scripts/03_dbpr_str.py`

```python
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
    addr_col = None
    for col in dbpr_df.columns:
        if 'FACILITY' in col.upper() and 'ADDR' in col.upper():
            addr_col = col
            break
        elif 'ADDRESS' in col.upper() and 'MAIL' not in col.upper():
            addr_col = col
            break

    name_col = None
    for col in dbpr_df.columns:
        if 'LICENSEE' in col.upper() or ('NAME' in col.upper() and 'DBA' not in col.upper()):
            name_col = col
            break

    phone_col = None
    for col in dbpr_df.columns:
        if 'PHONE' in col.upper():
            phone_col = col
            break

    email_col = None
    for col in dbpr_df.columns:
        if 'EMAIL' in col.upper() or 'MAIL' in col.upper():
            if 'ADDRESS' not in col.upper():
                email_col = col
                break

    if addr_col:
        dbpr_df['norm_addr'] = dbpr_df[addr_col].apply(normalize_address)
    if name_col:
        dbpr_df['norm_name'] = dbpr_df[name_col].apply(normalize_name)

    # Normalize in investor data
    site_addr_col = None
    for col in investor_df.columns:
        if 'SITE' in col.upper() and 'ADDR' in col.upper():
            site_addr_col = col
            break

    owner_name_col = None
    for col in investor_df.columns:
        if 'OWN' in col.upper() and 'NAME' in col.upper():
            owner_name_col = col
            break

    if site_addr_col:
        investor_df['norm_site_addr'] = investor_df[site_addr_col].apply(normalize_address)
    if owner_name_col:
        investor_df['norm_owner_name'] = investor_df[owner_name_col].apply(normalize_name)

    # Build lookup sets for fast matching
    str_addresses = set(dbpr_df['norm_addr'].dropna().unique()) if 'norm_addr' in dbpr_df.columns else set()
    str_names = set(dbpr_df['norm_name'].dropna().unique()) if 'norm_name' in dbpr_df.columns else set()

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
    for idx, row in investor_df.iterrows():
        matched = False

        # Try address match
        if 'norm_site_addr' in investor_df.columns:
            site = row.get('norm_site_addr', '')
            if site and site in str_addresses:
                matched = True

        # Try name match
        if not matched and 'norm_owner_name' in investor_df.columns:
            name = row.get('norm_owner_name', '')
            if name and name in str_names:
                matched = True

        if matched:
            investor_df.at[idx, 'str_licensed'] = True
            match_count += 1

            # Add phone/email from DBPR if available
            name = row.get('norm_owner_name', '')
            if name in name_to_phone:
                investor_df.at[idx, 'str_phone'] = name_to_phone[name]
            if name in name_to_email:
                investor_df.at[idx, 'str_email'] = name_to_email[name]

    # Count licenses per owner
    if name_col:
        license_counts = dbpr_df.groupby('norm_name').size().to_dict()
        for idx, row in investor_df.iterrows():
            name = row.get('norm_owner_name', '')
            if name in license_counts:
                investor_df.at[idx, 'str_license_count'] = license_counts[name]

    # Clean up temp columns
    for col in ['norm_site_addr', 'norm_owner_name']:
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
```

## Expected Output

- **60,000+ licensed vacation rentals** in FL DBPR system
- Cross-reference match rate against property records: **30-50%** (many STR operators own the property through entities or have slight address variations)
- **DBPR is the only free source that sometimes includes phone numbers** — this is a significant enrichment win for STR operators specifically
- STR operators are Tier 1 ICP — every match is a high-value lead

## Notes

1. DBPR CSV structure may change. First run should dump raw column names for mapping verification.
2. Address matching is fuzzy — the normalize function handles common variations but won't catch all mismatches.
3. Some vacation rental licenses are held by property management companies, not individual owners. These are still valuable (the PM company manages investor-owned properties).
