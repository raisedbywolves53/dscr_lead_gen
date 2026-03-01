# Module 4: SEC EDGAR Form D — FL Real Estate Fund Identification

## Purpose
Query SEC EDGAR for Florida-based real estate fund Form D filings to identify fund managers, syndicators, and institutional investors who may benefit from DSCR lending for their portfolio acquisitions.

## Data Source

**EDGAR Full-Text Search (EFTS):**
- Endpoint: `https://efts.sec.gov/LATEST/search-index`
- Free, no API key required
- Must set User-Agent header: `"CompanyName email@domain.com"`
- Rate limit: 10 requests/second
- Max 100 results per page, paginate with `from` parameter

**Legacy Company Search:**
- Endpoint: `https://www.sec.gov/cgi-bin/browse-edgar`
- Filters: State=FL, SIC=6726 (Investment Offices), type=D
- Returns HTML, needs parsing

## Relevant SIC Codes

| SIC | Description | Relevance |
|---|---|---|
| 6500 | Real Estate | Direct match |
| 6510 | Real Estate Operators | Direct match |
| 6512 | Operators of Apartment Buildings | Multi-family investors |
| 6552 | Land Subdividers & Developers | Development funds |
| 6726 | Investment Offices, NEC | Catch-all for investment funds |
| 6798 | Real Estate Investment Trusts | REITs |

## Script: `scripts/04_sec_edgar.py`

```python
"""
Module 4: SEC EDGAR Form D — FL Real Estate Funds

Queries SEC EDGAR for Florida-based real estate fund
Form D filings and extracts fund manager contact info.

Usage:
    python scripts/04_sec_edgar.py --output pipeline/output/04_fund_managers.csv
"""

import os
import json
import argparse
import requests
import pandas as pd
from pathlib import Path
import time
import re
import xml.etree.ElementTree as ET

DATA_DIR = Path("pipeline/data/edgar")
OUTPUT_DIR = Path("pipeline/output")

# SEC requires identifying User-Agent
SEC_HEADERS = {
    'User-Agent': 'DSCRLeadGenResearch admin@example.com',
    'Accept': 'application/json',
}

# Rate limiting
SEC_DELAY = 0.15  # 10 req/sec max, use ~7/sec to be safe

# Relevant SIC codes for real estate
RE_SIC_CODES = ['6500', '6510', '6512', '6552', '6726', '6798']


def search_edgar_form_d(query: str = "real estate", state: str = "FL",
                         start_date: str = "2023-01-01",
                         end_date: str = "2026-03-01",
                         max_results: int = 500) -> list:
    """
    Search EDGAR EFTS for Form D filings matching criteria.
    Returns list of filing metadata dicts.
    """

    base_url = "https://efts.sec.gov/LATEST/search-index"

    all_results = []
    offset = 0
    page_size = 100  # Max allowed

    while offset < max_results:
        params = {
            'q': f'"{query}"',
            'forms': 'D',
            'dateRange': 'custom',
            'startdt': start_date,
            'enddt': end_date,
        }

        # Add state filter if supported
        # Note: These parameters are undocumented but observed in the EDGAR UI
        if state:
            params['locationType'] = 'business'
            params['locationCode'] = state

        params['from'] = offset

        try:
            resp = requests.get(base_url, params=params, headers=SEC_HEADERS, timeout=30)

            if resp.status_code == 200:
                data = resp.json()
                hits = data.get('hits', {}).get('hits', [])

                if not hits:
                    break

                for hit in hits:
                    source = hit.get('_source', {})
                    all_results.append({
                        'accession_number': source.get('adsh', ''),
                        'display_name': '; '.join(source.get('display_names', [])),
                        'cik': '; '.join([str(c) for c in source.get('ciks', [])]),
                        'form_type': source.get('root_form', ''),
                        'file_date': source.get('file_date', ''),
                        'sic_codes': '; '.join([str(s) for s in source.get('sics', [])]),
                        'biz_location': '; '.join(source.get('biz_locations', [])),
                        'inc_state': '; '.join(source.get('inc_states', [])),
                    })

                offset += page_size
                print(f"  Fetched {len(all_results)} results so far...")
                time.sleep(SEC_DELAY)

            elif resp.status_code == 429:
                print("  Rate limited. Waiting 60 seconds...")
                time.sleep(60)
            else:
                print(f"  EDGAR returned {resp.status_code}. Stopping.")
                break

        except Exception as e:
            print(f"  Error querying EDGAR: {e}")
            break

    return all_results


def fetch_form_d_details(accession_number: str, cik: str) -> dict:
    """
    Fetch actual Form D XML filing to extract detailed information:
    - Issuer name, address, phone
    - Industry group
    - Offering amount
    - Total amount sold
    - Investment fund type
    - Related persons (executives, directors, promoters)
    """

    result = {
        'issuer_name': '',
        'issuer_street': '',
        'issuer_city': '',
        'issuer_state': '',
        'issuer_zip': '',
        'issuer_phone': '',
        'industry_group': '',
        'offering_amount': '',
        'total_sold': '',
        'fund_type': '',
        'related_persons': [],
    }

    # Format accession number for URL
    accession_clean = accession_number.replace('-', '')
    cik_clean = cik.split(';')[0].strip().lstrip('0') if cik else ''

    if not cik_clean:
        return result

    # Fetch filing index
    index_url = f"https://www.sec.gov/Archives/edgar/data/{cik_clean}/{accession_clean}/"

    try:
        resp = requests.get(index_url, headers=SEC_HEADERS, timeout=30)
        time.sleep(SEC_DELAY)

        if resp.status_code != 200:
            return result

        # Find the Form D XML file
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(resp.text, 'html.parser')

        xml_link = None
        for link in soup.find_all('a', href=True):
            href = link['href']
            if href.endswith('.xml') and 'primary_doc' in href.lower():
                xml_link = f"https://www.sec.gov{href}"
                break
            elif href.endswith('.xml'):
                xml_link = f"https://www.sec.gov{href}"

        if not xml_link:
            return result

        # Fetch and parse XML
        xml_resp = requests.get(xml_link, headers=SEC_HEADERS, timeout=30)
        time.sleep(SEC_DELAY)

        if xml_resp.status_code != 200:
            return result

        # Parse Form D XML
        root = ET.fromstring(xml_resp.content)

        # Handle namespace
        ns = {'': root.tag.split('}')[0] + '}'} if '}' in root.tag else {}
        prefix = ns.get('', '')

        def find_text(element, tag):
            """Find text in element, handling namespaces."""
            el = element.find(f'{prefix}{tag}')
            if el is None:
                el = element.find(tag)
            return el.text.strip() if el is not None and el.text else ''

        # Issuer info
        issuer = root.find(f'{prefix}primaryIssuer') or root.find('primaryIssuer')
        if issuer is not None:
            result['issuer_name'] = find_text(issuer, 'entityName')
            result['issuer_street'] = find_text(issuer, 'street1')
            result['issuer_city'] = find_text(issuer, 'city')
            result['issuer_state'] = find_text(issuer, 'stateOrCountry')
            result['issuer_zip'] = find_text(issuer, 'zipCode')
            result['issuer_phone'] = find_text(issuer, 'phoneNumber')
            result['industry_group'] = find_text(issuer, 'industryGroup')

        # Offering info
        offering = root.find(f'{prefix}offeringData') or root.find('offeringData')
        if offering is not None:
            amounts = offering.find(f'{prefix}offeringSalesAmounts') or offering.find('offeringSalesAmounts')
            if amounts is not None:
                result['offering_amount'] = find_text(amounts, 'totalOfferingAmount')
                result['total_sold'] = find_text(amounts, 'totalAmountSold')

            fund_info = offering.find(f'{prefix}typesOfSecuritiesOffered') or offering.find('typesOfSecuritiesOffered')
            if fund_info is not None:
                result['fund_type'] = find_text(fund_info, 'isEquityType')

        # Related persons (executives, directors, promoters)
        for person in root.iter():
            if 'relatedPerson' in person.tag.lower() or 'relatedperson' in person.tag:
                person_info = {
                    'name': '',
                    'title': '',
                    'address': '',
                }
                name_el = person.find(f'{prefix}relatedPersonName') or person.find('relatedPersonName')
                if name_el is not None:
                    first = find_text(name_el, 'firstName')
                    last = find_text(name_el, 'lastName')
                    person_info['name'] = f"{first} {last}".strip()

                addr_el = person.find(f'{prefix}relatedPersonAddress') or person.find('relatedPersonAddress')
                if addr_el is not None:
                    street = find_text(addr_el, 'street1')
                    city = find_text(addr_el, 'city')
                    state = find_text(addr_el, 'stateOrCountry')
                    person_info['address'] = f"{street}, {city}, {state}".strip(', ')

                relationship = person.find(f'{prefix}relatedPersonRelationsList') or person.find('relatedPersonRelationsList')
                if relationship is not None:
                    titles = []
                    for rel in relationship:
                        if rel.text and rel.text.strip().lower() not in ('false', '0', 'no'):
                            titles.append(rel.tag.split('}')[-1] if '}' in rel.tag else rel.tag)
                    person_info['title'] = ', '.join(titles)

                if person_info['name']:
                    result['related_persons'].append(person_info)

    except Exception as e:
        print(f"    Error fetching Form D details: {e}")

    return result


def main():
    parser = argparse.ArgumentParser(description='SEC EDGAR Form D FL RE fund search')
    parser.add_argument('--output', type=str, default='pipeline/output/04_fund_managers.csv')
    parser.add_argument('--max-results', type=int, default=500)
    parser.add_argument('--fetch-details', action='store_true',
                        help='Fetch full Form D XML details (slower, more data)')

    args = parser.parse_args()
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Search for FL real estate Form D filings
    print("Searching EDGAR for FL real estate Form D filings...")

    # Run multiple searches to cover different query terms
    search_queries = [
        "real estate",
        "rental property",
        "investment property",
        "residential fund",
        "real estate fund",
    ]

    all_filings = []
    seen_accessions = set()

    for query in search_queries:
        print(f"\n  Query: '{query}'")
        results = search_edgar_form_d(
            query=query,
            state="FL",
            start_date="2023-01-01",
            max_results=args.max_results
        )

        for r in results:
            if r['accession_number'] not in seen_accessions:
                seen_accessions.add(r['accession_number'])
                all_filings.append(r)

    print(f"\nTotal unique Form D filings found: {len(all_filings)}")

    if not all_filings:
        print("No filings found.")
        return

    # Optionally fetch detailed Form D data
    if args.fetch_details and all_filings:
        print("\nFetching Form D details (this may take a while)...")
        for i, filing in enumerate(all_filings):
            if i > 0 and i % 20 == 0:
                print(f"  Progress: {i}/{len(all_filings)}")

            details = fetch_form_d_details(
                filing['accession_number'],
                filing['cik']
            )

            filing.update({
                'issuer_name': details['issuer_name'],
                'issuer_phone': details['issuer_phone'],
                'issuer_city': details['issuer_city'],
                'issuer_state': details['issuer_state'],
                'industry_group': details['industry_group'],
                'offering_amount': details['offering_amount'],
                'total_sold': details['total_sold'],
                'fund_type': details['fund_type'],
                'related_persons': '; '.join(
                    [f"{p['name']} ({p['title']})" for p in details['related_persons']]
                ),
                'gp_name': details['related_persons'][0]['name'] if details['related_persons'] else '',
                'gp_address': details['related_persons'][0]['address'] if details['related_persons'] else '',
            })

    # Create output DataFrame
    df = pd.DataFrame(all_filings)
    df.to_csv(args.output, index=False)

    print(f"\nOutput saved: {args.output}")
    print(f"Total fund/issuer records: {len(df):,}")

    if 'issuer_phone' in df.columns:
        print(f"With phone number: {(df['issuer_phone'].fillna('') != '').sum():,}")


if __name__ == '__main__':
    main()
```

## Expected Output

- **200-500 unique FL real estate fund/issuer Form D filings** per year
- Each filing includes: fund name, GP name, contact info, offering amount
- Related persons list provides individual fund manager names and titles
- Phone numbers available directly from Form D XML filings

## Notes

1. Form D filings are amended frequently (D/A forms). Same fund may have multiple filings.
2. SIC code 6726 (Investment Offices) is a catch-all — not all will be real estate. The text search for "real estate" helps filter.
3. The `--fetch-details` flag parses full Form D XML. Much richer data but 3-5x slower due to additional API calls.
4. These are Tier 2 ICP leads but high-value — fund managers represent repeat, high-volume borrowers.
