"""
Module 2: SunBiz Entity Resolution

Downloads FL Division of Corporations bulk data and resolves
entity-owned properties to human owners.

Usage:
    python scripts/02_sunbiz_resolve.py --input pipeline/output/01_investor_properties.csv --output pipeline/output/02_resolved_entities.csv
"""

import os
import csv
import argparse
import requests
import pandas as pd
from pathlib import Path
from bs4 import BeautifulSoup
import time
import re
import json

DATA_DIR = Path("pipeline/data/sunbiz")
OUTPUT_DIR = Path("pipeline/output")

# Rate limiting for web scraping
SCRAPE_DELAY = 2.0  # seconds between requests


def download_sunbiz_bulk():
    """
    Download quarterly SunBiz bulk data files.

    NOTE: The FTP credentials and exact file paths need to be verified
    against the data downloads page. The quarterly files are large
    (potentially GB+) and split into 10 files by last digit of record number.

    For initial testing, we use the web search fallback instead of bulk download.
    """
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    # Check if bulk data already exists
    bulk_file = DATA_DIR / "sunbiz_quarterly_latest.csv"
    if bulk_file.exists():
        print("Loading cached SunBiz bulk data...")
        return pd.read_csv(bulk_file, dtype=str, low_memory=False)

    # TODO: Implement FTP download
    # The FTP credentials are public (listed on the data downloads page)
    # but the exact file structure needs to be verified.
    #
    # For now, fall back to web search for entity resolution.
    print("SunBiz bulk download not yet implemented. Using web search fallback.")
    return None


def search_sunbiz_entity(entity_name: str) -> dict:
    """
    Search sunbiz.org for a specific entity and extract officer/agent info.

    Returns dict with:
    - registered_agent_name
    - registered_agent_address
    - officers (list of dicts with name, title, address)
    - status
    - filing_date
    """

    result = {
        'entity_name_searched': entity_name,
        'registered_agent_name': '',
        'registered_agent_address': '',
        'officers': [],
        'principal_address': '',
        'mailing_address': '',
        'status': '',
        'filing_date': '',
        'entity_number': '',
        'resolved_person': '',  # Best guess at the human owner
    }

    # Clean entity name for search
    search_name = entity_name.strip()
    # Remove common suffixes for broader search
    for suffix in [' LLC', ' L.L.C.', ' INC', ' INC.', ' CORP', ' CORP.', ' LP', ' LTD']:
        if search_name.upper().endswith(suffix):
            search_name = search_name[:len(search_name) - len(suffix)].strip()

    # Search URL
    search_url = "https://search.sunbiz.org/Inquiry/CorporationSearch/SearchByName"
    params = {
        'searchNameOrder': search_name,
        'searchTerm': search_name,
        'listPage': 1,
        'listPageSize': 10,
    }

    headers = {
        'User-Agent': 'DSCR-Lead-Gen-Research contact@example.com'
    }

    try:
        resp = requests.get(search_url, params=params, headers=headers, timeout=30)
        if resp.status_code != 200:
            return result

        soup = BeautifulSoup(resp.text, 'html.parser')

        # Find the first matching entity link
        results_table = soup.find('table', {'id': 'searchResultsTable'})
        if not results_table:
            # Try alternative selector
            links = soup.find_all('a', href=re.compile(r'/Inquiry/CorporationSearch/SearchResultDetail'))
            if not links:
                return result
            detail_url = 'https://search.sunbiz.org' + links[0]['href']
        else:
            rows = results_table.find_all('tr')
            if len(rows) < 2:  # header + at least one result
                return result
            first_link = rows[1].find('a')
            if not first_link:
                return result
            detail_url = 'https://search.sunbiz.org' + first_link['href']

        time.sleep(SCRAPE_DELAY)

        # Fetch detail page
        detail_resp = requests.get(detail_url, headers=headers, timeout=30)
        if detail_resp.status_code != 200:
            return result

        detail_soup = BeautifulSoup(detail_resp.text, 'html.parser')
        page_text = detail_soup.get_text()

        # Extract registered agent
        agent_section = detail_soup.find(string=re.compile(r'Registered Agent', re.I))
        if agent_section:
            # Navigate to the agent info - structure varies
            parent = agent_section.find_parent()
            if parent:
                siblings = parent.find_next_siblings()
                for sib in siblings[:3]:
                    text = sib.get_text(strip=True)
                    if text and not text.startswith('Officer') and not text.startswith('Annual'):
                        if not result['registered_agent_name']:
                            result['registered_agent_name'] = text
                        elif not result['registered_agent_address']:
                            result['registered_agent_address'] = text

        # Extract officers/directors
        officer_section = detail_soup.find(string=re.compile(r'Officer/Director', re.I))
        if officer_section:
            parent = officer_section.find_parent()
            if parent:
                # Officers are typically in a structured list after the header
                next_elements = parent.find_next_siblings()
                current_officer = {}
                for elem in next_elements:
                    text = elem.get_text(strip=True)
                    if not text:
                        continue
                    if text.startswith('Annual Report') or text.startswith('Document'):
                        break
                    # Heuristic: titles are short (Manager, President, etc.)
                    if len(text) < 30 and any(t in text.upper() for t in
                        ['MANAGER', 'MEMBER', 'PRESIDENT', 'DIRECTOR', 'SECRETARY',
                         'TREASURER', 'VP', 'CEO', 'CFO', 'OFFICER', 'AGENT']):
                        if current_officer:
                            result['officers'].append(current_officer)
                        current_officer = {'title': text}
                    elif 'name' not in current_officer:
                        current_officer['name'] = text
                    elif 'address' not in current_officer:
                        current_officer['address'] = text

                if current_officer and 'name' in current_officer:
                    result['officers'].append(current_officer)

        # Determine resolved person (best guess at human owner)
        if result['officers']:
            # Prefer Manager or Member for LLCs, President for Corps
            for officer in result['officers']:
                if officer.get('title', '').upper() in ('MANAGER', 'MANAGING MEMBER', 'MEMBER', 'PRESIDENT'):
                    result['resolved_person'] = officer.get('name', '')
                    break
            if not result['resolved_person']:
                result['resolved_person'] = result['officers'][0].get('name', '')
        elif result['registered_agent_name']:
            # Use registered agent if no officers found
            # But only if it's a person name (not another entity)
            if not any(kw in result['registered_agent_name'].upper() for kw in
                      [' LLC', ' INC', ' CORP', ' SERVICE', ' AGENT', ' REGISTERED']):
                result['resolved_person'] = result['registered_agent_name']

    except Exception as e:
        print(f"    Error searching SunBiz for '{entity_name}': {e}")

    return result


def resolve_entities(input_file: str, output_file: str, max_lookups: int = 500):
    """
    Read investor properties file, identify entity-owned properties,
    and resolve entities to human owners via SunBiz.
    """

    print("Loading investor properties...")
    df = pd.read_csv(input_file, dtype=str, low_memory=False)

    # Find entity flag column
    if 'is_entity' not in df.columns:
        # Try to detect entities from owner name
        owner_col = None
        for col in df.columns:
            if 'OWN' in col.upper() and 'NAME' in col.upper():
                owner_col = col
                break
        if owner_col:
            entity_keywords = [' LLC', ' L.L.C', ' INC', ' CORP', ' TRUST', ' LP ', ' LTD']
            df['is_entity'] = df[owner_col].apply(
                lambda x: any(kw in str(x).upper() for kw in entity_keywords)
            )

    entities = df[df['is_entity'] == True].copy() if 'is_entity' in df.columns else pd.DataFrame()

    if entities.empty:
        print("No entity-owned properties found.")
        df.to_csv(output_file, index=False)
        return

    print(f"Found {len(entities):,} entity-owned properties to resolve.")

    # Find owner name column
    owner_col = None
    for col in entities.columns:
        if 'OWN' in col.upper() and 'NAME' in col.upper():
            owner_col = col
            break

    if not owner_col:
        print("Cannot find owner name column.")
        df.to_csv(output_file, index=False)
        return

    # Get unique entity names
    unique_entities = entities[owner_col].dropna().unique()
    print(f"Unique entities: {len(unique_entities):,}")

    # Limit lookups for rate limiting
    if len(unique_entities) > max_lookups:
        print(f"Limiting to {max_lookups} lookups (of {len(unique_entities)} unique entities).")
        # Prioritize entities that appear most frequently (more properties = bigger investor)
        entity_counts = entities[owner_col].value_counts()
        unique_entities = entity_counts.head(max_lookups).index.tolist()

    # Resolve each entity
    resolution_cache = {}
    cache_file = DATA_DIR / "resolution_cache.json"

    # Load cache if exists
    if cache_file.exists():
        with open(cache_file, 'r') as f:
            resolution_cache = json.load(f)
        print(f"Loaded {len(resolution_cache)} cached resolutions.")

    resolved_count = 0
    for i, entity_name in enumerate(unique_entities):
        if entity_name in resolution_cache:
            continue

        if i > 0 and i % 50 == 0:
            print(f"  Progress: {i}/{len(unique_entities)} ({resolved_count} resolved)")
            # Save cache periodically
            with open(cache_file, 'w') as f:
                json.dump(resolution_cache, f, indent=2)

        result = search_sunbiz_entity(entity_name)
        resolution_cache[entity_name] = result

        if result['resolved_person']:
            resolved_count += 1

        time.sleep(SCRAPE_DELAY)

    # Save final cache
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(cache_file, 'w') as f:
        json.dump(resolution_cache, f, indent=2)

    print(f"\nResolved {resolved_count}/{len(unique_entities)} entities to human names.")

    # Merge resolution data back into main dataframe
    df['resolved_person'] = ''
    df['registered_agent'] = ''
    df['entity_officers'] = ''
    df['entity_status'] = ''
    df['entity_count'] = 0

    for idx, row in df.iterrows():
        owner = str(row.get(owner_col, ''))
        if owner in resolution_cache:
            res = resolution_cache[owner]
            df.at[idx, 'resolved_person'] = res.get('resolved_person', '')
            df.at[idx, 'registered_agent'] = res.get('registered_agent_name', '')
            df.at[idx, 'entity_officers'] = '; '.join(
                [f"{o.get('name','')} ({o.get('title','')})" for o in res.get('officers', [])]
            )
            df.at[idx, 'entity_status'] = res.get('status', '')

    # Count entities per resolved person
    person_entity_counts = {}
    for entity_name, res in resolution_cache.items():
        person = res.get('resolved_person', '')
        if person:
            person_entity_counts[person] = person_entity_counts.get(person, 0) + 1

    for idx, row in df.iterrows():
        person = row.get('resolved_person', '')
        if person and person in person_entity_counts:
            df.at[idx, 'entity_count'] = person_entity_counts[person]

    df.to_csv(output_file, index=False)
    print(f"\nOutput saved: {output_file}")
    print(f"Total leads: {len(df):,}")
    print(f"With resolved person: {(df['resolved_person'] != '').sum():,}")


def main():
    parser = argparse.ArgumentParser(description='Resolve entity owners via SunBiz')
    parser.add_argument('--input', type=str, default='pipeline/output/01_investor_properties.csv')
    parser.add_argument('--output', type=str, default='pipeline/output/02_resolved_entities.csv')
    parser.add_argument('--max-lookups', type=int, default=500,
                        help='Max SunBiz lookups per run (rate limiting)')

    args = parser.parse_args()
    resolve_entities(args.input, args.output, args.max_lookups)


if __name__ == '__main__':
    main()
