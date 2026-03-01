# Module 5: Contact Enrichment

## Purpose
Take investor leads with name + mailing address and enrich with phone numbers and email addresses using free or low-cost data sources. This is the bridge from "we know who they are" to "we can contact them."

## Enrichment Sources (Free / Low-Cost)

| Source | Data | Free Tier | Method |
|---|---|---|---|
| **TruePeopleSearch.com** | Phone, email, age, relatives, addresses | Unlimited (ad-supported) | Web scraping |
| **FastPeopleSearch.com** | Phone, email, addresses | Unlimited (ad-supported) | Web scraping |
| **OpenCNAM** | Caller ID name from phone number | 10/month free | API |
| **Apollo.io** | Business email, company, title | 10,000 credits/month free | API |
| **Hunter.io** | Email from name + domain | 25 searches/month free | API |
| **Clearbit (free tier)** | Company info from domain | Limited | API |
| **Google Custom Search** | Find LinkedIn profiles, websites | 100 queries/day free | API |
| **NumVerify** | Phone number validation | 100/month free | API |

## Enrichment Priority Order

```
1. DBPR data (already done in Module 3 — STR operators may have phone/email)
2. SEC EDGAR (already done in Module 4 — fund managers have phone in Form D)
3. People search sites (name + address → phone + email)
4. Apollo.io (business email for entity owners / professionals)
5. Google search (find LinkedIn, website, social profiles)
```

## Script: `scripts/05_enrich_contacts.py`

```python
"""
Module 5: Contact Enrichment

Enriches investor leads with phone numbers and email addresses
from free public data sources.

Usage:
    python scripts/05_enrich_contacts.py --input pipeline/output/03_str_tagged.csv --output pipeline/output/05_enriched.csv --max-lookups 500
"""

import os
import json
import argparse
import requests
import pandas as pd
from pathlib import Path
from bs4 import BeautifulSoup
import time
import re
import urllib.parse

DATA_DIR = Path("pipeline/data/enrichment")
OUTPUT_DIR = Path("pipeline/output")

# Rate limiting
SEARCH_DELAY = 3.0  # seconds between people search requests
APOLLO_DELAY = 0.5

# Cache
ENRICHMENT_CACHE_FILE = DATA_DIR / "enrichment_cache.json"


def load_cache() -> dict:
    """Load enrichment cache from disk."""
    if ENRICHMENT_CACHE_FILE.exists():
        with open(ENRICHMENT_CACHE_FILE, 'r') as f:
            return json.load(f)
    return {}


def save_cache(cache: dict):
    """Save enrichment cache to disk."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(ENRICHMENT_CACHE_FILE, 'w') as f:
        json.dump(cache, f, indent=2)


def clean_name(name: str) -> str:
    """Clean owner name for people search lookup."""
    if not name or pd.isna(name):
        return ''

    name = str(name).strip()

    # Skip entity names — can't do people search on "ABC Holdings LLC"
    entity_indicators = [' LLC', ' INC', ' CORP', ' TRUST', ' LP', ' LTD',
                         ' HOLDINGS', ' PROPERTIES', ' INVESTMENTS', ' FUND']
    if any(ind in name.upper() for ind in entity_indicators):
        return ''

    # Handle "LAST, FIRST" format (common in county records)
    if ',' in name:
        parts = name.split(',', 1)
        if len(parts) == 2:
            last = parts[0].strip()
            first = parts[1].strip().split()[0] if parts[1].strip() else ''
            if first:
                name = f"{first} {last}"

    # Remove suffixes like JR, SR, II, III
    name = re.sub(r'\b(JR|SR|II|III|IV|V)\b\.?', '', name, flags=re.I).strip()

    # Remove extra whitespace
    name = ' '.join(name.split())

    return name


def search_truepeoplesearch(name: str, city: str = '', state: str = '') -> dict:
    """
    Search TruePeopleSearch.com for phone and email.

    NOTE: This site is ad-supported and free for manual use.
    Automated scraping may violate ToS. Use responsibly and
    consider their robots.txt.

    Returns: dict with phone, email, address fields
    """

    result = {
        'phone': '',
        'email': '',
        'source': '',
    }

    if not name:
        return result

    # Build search URL
    name_parts = name.split()
    if len(name_parts) < 2:
        return result

    search_url = f"https://www.truepeoplesearch.com/results"
    params = {
        'name': name,
    }
    if city:
        params['citystatezip'] = f"{city}, {state}" if state else city

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
    }

    try:
        resp = requests.get(search_url, params=params, headers=headers, timeout=15)

        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, 'html.parser')

            # Look for phone numbers
            phone_elements = soup.find_all(string=re.compile(r'\(\d{3}\)\s*\d{3}-\d{4}'))
            if phone_elements:
                phone_match = re.search(r'\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}', phone_elements[0])
                if phone_match:
                    result['phone'] = phone_match.group(0)
                    result['source'] = 'truepeoplesearch'

            # Look for email
            email_elements = soup.find_all(string=re.compile(r'[\w.+-]+@[\w-]+\.[\w.]+'))
            if email_elements:
                email_match = re.search(r'[\w.+-]+@[\w-]+\.[\w.]+', email_elements[0])
                if email_match:
                    result['email'] = email_match.group(0)
                    if not result['source']:
                        result['source'] = 'truepeoplesearch'

        elif resp.status_code == 403:
            print("    TruePeopleSearch blocked request (rate limit or bot detection)")
        elif resp.status_code == 429:
            print("    TruePeopleSearch rate limited. Increasing delay.")

    except Exception as e:
        print(f"    TruePeopleSearch error: {e}")

    return result


def search_fastpeoplesearch(name: str, city: str = '', state: str = '') -> dict:
    """
    Search FastPeopleSearch.com for phone and email.
    Similar structure to TruePeopleSearch.

    Returns: dict with phone, email fields
    """

    result = {
        'phone': '',
        'email': '',
        'source': '',
    }

    if not name:
        return result

    # URL encode name
    name_slug = name.lower().replace(' ', '-')

    search_url = f"https://www.fastpeoplesearch.com/name/{urllib.parse.quote(name_slug)}"

    if city and state:
        city_slug = city.lower().replace(' ', '-')
        state_slug = state.lower()
        search_url += f"_{city_slug}-{state_slug}"

    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    }

    try:
        resp = requests.get(search_url, headers=headers, timeout=15)

        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, 'html.parser')

            # Phone pattern
            phone_links = soup.find_all('a', href=re.compile(r'tel:'))
            if phone_links:
                phone = phone_links[0].get_text(strip=True)
                if re.match(r'[\d\(\)\s\-\.]{10,}', phone):
                    result['phone'] = phone
                    result['source'] = 'fastpeoplesearch'

            # Email pattern
            email_spans = soup.find_all(string=re.compile(r'[\w.+-]+@[\w-]+\.[\w.]+'))
            if email_spans:
                email_match = re.search(r'[\w.+-]+@[\w-]+\.[\w.]+', email_spans[0])
                if email_match:
                    result['email'] = email_match.group(0)
                    if not result['source']:
                        result['source'] = 'fastpeoplesearch'

    except Exception as e:
        print(f"    FastPeopleSearch error: {e}")

    return result


def search_apollo(name: str, company: str = '', api_key: str = '') -> dict:
    """
    Search Apollo.io for business email.
    Free tier: 10,000 credits/month.

    Returns: dict with email, title, company fields
    """

    result = {
        'email': '',
        'title': '',
        'company': '',
        'linkedin': '',
        'source': '',
    }

    if not api_key or not name:
        return result

    name_parts = name.split()
    if len(name_parts) < 2:
        return result

    first_name = name_parts[0]
    last_name = ' '.join(name_parts[1:])

    url = "https://api.apollo.io/v1/people/match"
    headers = {
        'Content-Type': 'application/json',
        'Cache-Control': 'no-cache',
    }

    payload = {
        'api_key': api_key,
        'first_name': first_name,
        'last_name': last_name,
    }

    if company:
        payload['organization_name'] = company

    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=15)

        if resp.status_code == 200:
            data = resp.json()
            person = data.get('person', {})
            if person:
                result['email'] = person.get('email', '')
                result['title'] = person.get('title', '')
                result['company'] = person.get('organization', {}).get('name', '')
                result['linkedin'] = person.get('linkedin_url', '')
                if result['email']:
                    result['source'] = 'apollo'

    except Exception as e:
        print(f"    Apollo error: {e}")

    return result


def enrich_leads(input_file: str, output_file: str, max_lookups: int = 500,
                 apollo_key: str = ''):
    """
    Main enrichment function. Takes filtered investor leads and
    adds phone/email via people search and Apollo.
    """

    print("Loading leads for enrichment...")
    df = pd.read_csv(input_file, dtype=str, low_memory=False)

    cache = load_cache()
    print(f"Loaded {len(cache)} cached enrichment results.")

    # Initialize enrichment columns if not present
    for col in ['phone', 'email', 'enrichment_source']:
        if col not in df.columns:
            df[col] = ''

    # Merge any existing phone/email from DBPR (Module 3)
    if 'str_phone' in df.columns:
        mask = (df['phone'] == '') & (df['str_phone'].fillna('') != '')
        df.loc[mask, 'phone'] = df.loc[mask, 'str_phone']
        df.loc[mask, 'enrichment_source'] = 'dbpr'

    if 'str_email' in df.columns:
        mask = (df['email'] == '') & (df['str_email'].fillna('') != '')
        df.loc[mask, 'email'] = df.loc[mask, 'str_email']
        df.loc[mask, 'enrichment_source'] = df.loc[mask, 'enrichment_source'].apply(
            lambda x: f"{x},dbpr" if x else 'dbpr'
        )

    # Identify leads needing enrichment
    needs_enrichment = df[
        (df['phone'].fillna('') == '') | (df['email'].fillna('') == '')
    ].copy()

    print(f"Leads needing enrichment: {len(needs_enrichment):,}")

    # Determine the name to search for
    # Priority: resolved_person (from SunBiz) > owner_name
    name_col = None
    for col in ['resolved_person', 'owner_name']:
        if col in df.columns:
            name_col = col
            break

    if not name_col:
        for col in df.columns:
            if 'OWN' in col.upper() and 'NAME' in col.upper():
                name_col = col
                break

    if not name_col:
        print("ERROR: Cannot find name column for enrichment.")
        df.to_csv(output_file, index=False)
        return

    # Find city/state columns for more precise searches
    city_col = None
    state_col = None
    for col in df.columns:
        if ('OWN' in col.upper() or 'MAIL' in col.upper()) and 'CITY' in col.upper():
            city_col = col
        elif ('OWN' in col.upper() or 'MAIL' in col.upper()) and 'STATE' in col.upper():
            state_col = col

    # Sort by priority — enrich highest-value leads first
    if 'property_count' in needs_enrichment.columns:
        needs_enrichment['_sort'] = pd.to_numeric(
            needs_enrichment['property_count'], errors='coerce'
        ).fillna(0)
        needs_enrichment = needs_enrichment.sort_values('_sort', ascending=False)

    # Limit lookups
    lookup_count = min(len(needs_enrichment), max_lookups)
    print(f"Will enrich up to {lookup_count} leads this run.")

    enriched_count = 0
    for i, (idx, row) in enumerate(needs_enrichment.head(lookup_count).iterrows()):

        # Get best available name
        name = ''
        if 'resolved_person' in row and pd.notna(row['resolved_person']) and str(row['resolved_person']).strip():
            name = clean_name(str(row['resolved_person']))
        if not name:
            name = clean_name(str(row.get(name_col, '')))

        if not name:
            continue

        city = str(row.get(city_col, '')).strip() if city_col else ''
        state = str(row.get(state_col, '')).strip() if state_col else ''

        # Check cache
        cache_key = f"{name}|{city}|{state}"
        if cache_key in cache:
            cached = cache[cache_key]
            if cached.get('phone') and not df.at[idx, 'phone']:
                df.at[idx, 'phone'] = cached['phone']
            if cached.get('email') and not df.at[idx, 'email']:
                df.at[idx, 'email'] = cached['email']
            if cached.get('source'):
                df.at[idx, 'enrichment_source'] = cached['source']
            enriched_count += 1
            continue

        if i > 0 and i % 50 == 0:
            print(f"  Progress: {i}/{lookup_count} ({enriched_count} enriched)")
            save_cache(cache)

        # Try TruePeopleSearch first
        result = search_truepeoplesearch(name, city, state)
        time.sleep(SEARCH_DELAY)

        # If no result, try FastPeopleSearch
        if not result['phone'] and not result['email']:
            result = search_fastpeoplesearch(name, city, state)
            time.sleep(SEARCH_DELAY)

        # If still no email and Apollo key available, try Apollo
        if not result['email'] and apollo_key:
            apollo_result = search_apollo(name, api_key=apollo_key)
            if apollo_result['email']:
                result['email'] = apollo_result['email']
                result['source'] = (result.get('source', '') + ',apollo').strip(',')
            time.sleep(APOLLO_DELAY)

        # Update dataframe
        if result['phone']:
            df.at[idx, 'phone'] = result['phone']
        if result['email']:
            df.at[idx, 'email'] = result['email']
        if result['phone'] or result['email']:
            df.at[idx, 'enrichment_source'] = result.get('source', 'people_search')
            enriched_count += 1

        # Cache result
        cache[cache_key] = result

    # Save final cache
    save_cache(cache)

    # Summary stats
    total = len(df)
    has_phone = (df['phone'].fillna('') != '').sum()
    has_email = (df['email'].fillna('') != '').sum()
    has_either = ((df['phone'].fillna('') != '') | (df['email'].fillna('') != '')).sum()

    print(f"\n{'='*60}")
    print(f"ENRICHMENT SUMMARY")
    print(f"{'='*60}")
    print(f"Total leads:         {total:,}")
    print(f"With phone:          {has_phone:,} ({has_phone/total*100:.1f}%)")
    print(f"With email:          {has_email:,} ({has_email/total*100:.1f}%)")
    print(f"With phone or email: {has_either:,} ({has_either/total*100:.1f}%)")
    print(f"Enriched this run:   {enriched_count:,}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_file, index=False)
    print(f"\nOutput saved: {output_file}")


def main():
    parser = argparse.ArgumentParser(description='Contact enrichment')
    parser.add_argument('--input', type=str, default='pipeline/output/03_str_tagged.csv')
    parser.add_argument('--output', type=str, default='pipeline/output/05_enriched.csv')
    parser.add_argument('--max-lookups', type=int, default=500,
                        help='Max enrichment lookups per run')
    parser.add_argument('--apollo-key', type=str, default='',
                        help='Apollo.io API key (optional, for business email enrichment)')

    args = parser.parse_args()
    enrich_leads(args.input, args.output, args.max_lookups, args.apollo_key)


if __name__ == '__main__':
    main()
```

## Expected Enrichment Rates

| Source | Phone Hit Rate | Email Hit Rate | Cost |
|---|---|---|---|
| DBPR (STR operators) | 30-50% | 10-20% | Free |
| SEC EDGAR (fund managers) | 80%+ (in filing) | Low | Free |
| TruePeopleSearch | 50-60% | 30-40% | Free |
| FastPeopleSearch | 50-60% | 30-40% | Free |
| Apollo.io | N/A | 40-50% (business) | Free tier |

**Combined expected contact rate: 40-60% of all leads will have at least phone or email after enrichment.**

## Responsible Use Notes

1. People search sites are public, ad-supported services. Excessive automated scraping may trigger rate limits or blocks.
2. Always respect `robots.txt` and ToS. The scripts include delays between requests.
3. Cache all results to minimize repeat lookups.
4. Consider CAN-SPAM and TCPA compliance before using collected contact info for outreach.
5. Apollo.io free tier requires account creation and API key — completely free up to 10K credits/month.
