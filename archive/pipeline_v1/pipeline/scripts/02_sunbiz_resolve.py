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

# Shared session for SunBiz (needs cookies for Cloudflare)
_sunbiz_session = None

def _get_sunbiz_session():
    """Get or create a requests session with SunBiz cookies."""
    global _sunbiz_session
    if _sunbiz_session is None:
        _sunbiz_session = requests.Session()
        _sunbiz_session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        })
        # Visit the search page to establish session cookies
        try:
            _sunbiz_session.get(
                'https://search.sunbiz.org/Inquiry/CorporationSearch/ByName',
                timeout=30
            )
        except Exception:
            pass
    return _sunbiz_session


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

    Uses POST to the ByName endpoint and parses detailSection divs.

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
    for suffix in [' LLC', ' L.L.C.', ' INC', ' INC.', ' CORP', ' CORP.', ' LP', ' LTD']:
        if search_name.upper().endswith(suffix):
            search_name = search_name[:len(search_name) - len(suffix)].strip()

    session = _get_sunbiz_session()

    try:
        # POST search to ByName endpoint
        search_url = "https://search.sunbiz.org/Inquiry/CorporationSearch/ByName"
        search_data = {
            'SearchTerm': search_name,
            'InquiryType': 'EntityName',
            'SearchNameOrder': '',
        }

        resp = session.post(search_url, data=search_data, timeout=30)
        if resp.status_code != 200:
            return result

        soup = BeautifulSoup(resp.text, 'html.parser')

        # Find detail page links in results
        links = soup.find_all('a', href=re.compile(r'SearchResultDetail'))
        if not links:
            return result

        # Pick the best match — prefer exact entity name match
        detail_url = None
        entity_upper = entity_name.upper().strip()
        for link in links:
            link_text = link.get_text(strip=True).upper()
            if link_text == entity_upper:
                detail_url = 'https://search.sunbiz.org' + link['href']
                break
        if not detail_url:
            # Fall back to first result
            detail_url = 'https://search.sunbiz.org' + links[0]['href']

        time.sleep(SCRAPE_DELAY)

        # Fetch detail page
        detail_resp = session.get(detail_url, timeout=30)
        if detail_resp.status_code != 200:
            return result

        detail_soup = BeautifulSoup(detail_resp.text, 'html.parser')

        # Parse detailSection divs
        sections = detail_soup.find_all('div', class_='detailSection')
        for section in sections:
            section_text = section.get_text(separator='\n', strip=True)
            lines = [l.strip() for l in section_text.split('\n') if l.strip()]

            if not lines:
                continue

            header = lines[0]

            # Filing Information section
            if 'Filing Information' in header:
                for i, line in enumerate(lines):
                    if 'Document Number' in line and i + 1 < len(lines):
                        result['entity_number'] = lines[i + 1]
                    elif 'Status' in line and 'PDA' not in line and i + 1 < len(lines):
                        result['status'] = lines[i + 1]
                    elif 'Date Filed' in line and i + 1 < len(lines):
                        result['filing_date'] = lines[i + 1]

            # Principal Address section
            elif 'Principal Address' in header:
                addr_lines = [l for l in lines[1:] if not l.startswith('Changed:')]
                if addr_lines:
                    result['principal_address'] = ', '.join(addr_lines)

            # Mailing Address section
            elif 'Mailing Address' in header:
                addr_lines = [l for l in lines[1:] if not l.startswith('Changed:')]
                if addr_lines:
                    result['mailing_address'] = ', '.join(addr_lines)

            # Registered Agent section
            elif 'Registered Agent' in header:
                # First non-header, non-"Changed:" line is the agent name
                agent_lines = [l for l in lines[1:] if not l.startswith('Name Changed:') and not l.startswith('Address Changed:')]
                if agent_lines:
                    result['registered_agent_name'] = agent_lines[0]
                if len(agent_lines) > 1:
                    result['registered_agent_address'] = ', '.join(agent_lines[1:])

            # Officers/Directors or Authorized Persons section
            elif 'Officer/Director' in header or 'Authorized Person' in header:
                # Parse title/name pairs from spans
                title_spans = section.find_all('span', string=re.compile(r'^Title\s'))
                for title_span in title_spans:
                    title_text = title_span.get_text(strip=True)
                    # Extract title value (e.g., "Title MGR" -> "MGR")
                    title_val = title_text.replace('Title', '').strip()

                    # The name and address follow the title span as text nodes
                    # Navigate to next sibling text content
                    officer = {'title': title_val}
                    next_node = title_span
                    collected = []
                    while True:
                        next_node = next_node.next_sibling
                        if next_node is None:
                            break
                        if hasattr(next_node, 'name') and next_node.name == 'span':
                            break  # Hit next title span
                        text = next_node.get_text(strip=True) if hasattr(next_node, 'get_text') else str(next_node).strip()
                        if text:
                            collected.append(text)

                    if collected:
                        officer['name'] = collected[0]
                        if len(collected) > 1:
                            officer['address'] = ', '.join(collected[1:])
                        result['officers'].append(officer)

                # Fallback: if no title spans found, parse from text
                if not result['officers']:
                    name_addr_lines = [l for l in lines if l != header and l != 'Name & Address'
                                       and not l.startswith('Title')]
                    # Try to extract from "Title XXX\nNAME\nADDRESS" pattern
                    i = 1  # skip header
                    while i < len(lines):
                        line = lines[i]
                        if line == 'Name & Address':
                            i += 1
                            continue
                        if line.startswith('Title '):
                            title_val = line.replace('Title ', '').strip()
                            officer = {'title': title_val}
                            if i + 1 < len(lines) and not lines[i + 1].startswith('Title '):
                                officer['name'] = lines[i + 1]
                                i += 1
                                # Collect address lines until next Title or section
                                addr_parts = []
                                while i + 1 < len(lines) and not lines[i + 1].startswith('Title ') and not lines[i + 1].startswith('Annual') and not lines[i + 1].startswith('Document'):
                                    i += 1
                                    addr_parts.append(lines[i])
                                if addr_parts:
                                    officer['address'] = ', '.join(addr_parts)
                            result['officers'].append(officer)
                        i += 1

        # Determine resolved person (best guess at human owner)
        if result['officers']:
            # Prefer Manager/Member for LLCs, President for Corps
            priority_titles = ['MGR', 'MGRM', 'MANAGER', 'MANAGING MEMBER', 'MEMBER',
                               'PRESIDENT', 'PRES', 'CEO']
            for officer in result['officers']:
                if officer.get('title', '').upper() in priority_titles:
                    result['resolved_person'] = officer.get('name', '')
                    break
            if not result['resolved_person'] and result['officers']:
                result['resolved_person'] = result['officers'][0].get('name', '')
        elif result['registered_agent_name']:
            # Use registered agent if no officers found (only if it's a person)
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

    entities = df[df['is_entity'].astype(str).str.lower().isin(['true', '1', 'yes'])].copy() if 'is_entity' in df.columns else pd.DataFrame()

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
