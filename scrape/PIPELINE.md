# PIPELINE.md — DSCR Lead Gen Build Spec

## Purpose

This document is the detailed execution spec for Claude CLI. When the user says "build the pipeline" or "execute the next step," reference this document for exact implementation details.

---

## STEP 1: Download Florida Property Data (01_download_nal.py)

### What This Does
Downloads property owner records from Florida county property appraiser websites. These are PUBLIC RECORDS under Florida Statute 119 — this is legal and free.

### Primary Source: FL Dept of Revenue Statewide NAL Files
The Florida Department of Revenue publishes NAL (Name-Address-Legal) files covering all 67 counties. These are the gold standard — same data PropStream and BatchData resell for $99+/mo.

**How to obtain:** Email PTOTechnology@floridarevenue.com requesting the most recent NAL files. They will email files under 10MB or provide FTP access for larger files.

**NAL File Format:** Fixed-width text files with the following key fields:
- County code (2 digits)
- Parcel ID / Folio number
- Owner name (line 1 and line 2)
- Mailing address (street, city, state, zip)
- Property address (situs)
- Property use code (tells you if it's residential, commercial, vacant land, etc.)
- Just/market value
- Assessed value
- Sale date (most recent)
- Sale price
- Homestead exemption flag (Y/N — if N, likely investor property)

### Secondary Source: Individual County Downloads
For counties with free bulk downloads, also pull directly:

```python
COUNTY_SOURCES = {
    "seminole": {
        "url": "https://www.scpafl.org/",  # Free Excel/Access downloads
        "format": "xlsx",
        "bulk_download": True,
        "notes": "Updated daily. Check Downloads page."
    },
    "sarasota": {
        "url": "https://www.sc-pa.com/downloads/download-data/",
        "format": "csv",
        "bulk_download": True,
        "notes": "Free CSV including historical sales"
    },
    "clay": {
        "url": "https://www.ccpao.com/parcel-information/",
        "format": "csv",
        "bulk_download": True,
        "notes": "Free, updated monthly"
    },
    "martin": {
        "url": "https://www.pa.martin.fl.us/tools-resources/data-downloads",
        "format": "csv",
        "bulk_download": True,
        "notes": "Custom filters, export to CSV/Excel/mailing labels"
    },
    "volusia": {
        "url": "https://vcpa.vcgov.org/search/real-property",
        "format": "csv",
        "bulk_download": True,
        "notes": "Export to CSV or mailing list"
    }
}
```

### For Counties Without Bulk Downloads (Scraping Required)
Counties like Broward (bcpa.net), Miami-Dade, and Hillsborough require scraping their search portals. Use this approach:

1. Get list of parcel IDs (from NAL file or county GIS data)
2. For each parcel, request the property detail page
3. Parse HTML with BeautifulSoup
4. Extract: owner name, mailing address, property details, assessed value, sale history
5. **Rate limit**: 1 request per 2 seconds minimum. Run during off-peak hours (nights/weekends).
6. **Check robots.txt first** for each site

### Output
Save to `data/raw/{county_name}_raw.csv` with standardized columns:
```
parcel_id, owner_name_1, owner_name_2, mail_street, mail_city, mail_state, mail_zip, 
prop_street, prop_city, prop_zip, use_code, use_description, just_value, assessed_value,
sale_date, sale_price, homestead_flag, year_built, living_sqft, bedrooms, bathrooms
```

---

## STEP 2: Parse & Standardize (02_parse_nal.py)

### What This Does
Takes the raw data (which may be fixed-width, CSV, XLSX, or scraped HTML) and standardizes everything into a single clean format.

### Key Transformations
1. **Standardize owner names**: UPPERCASE, strip extra spaces, handle "TRUSTEE OF," "AS PERS REP," etc.
2. **Identify LLC/Corp owners**: Flag records where owner_name contains LLC, INC, CORP, TRUST, LP, LLP, PARTNERSHIP, HOLDINGS, INVESTMENTS, PROPERTIES, GROUP, CAPITAL, VENTURES, MANAGEMENT, ASSOCIATES, ENTERPRISES, FUND, REALTY
3. **Standardize addresses**: Use USPS formatting, normalize abbreviations (ST→STREET, AVE→AVENUE, etc.)
4. **Flag absentee owners**: Where mail_state ≠ "FL" OR mail_zip ≠ prop_zip
5. **Flag no-homestead**: Where homestead_flag = "N" or is empty
6. **Calculate equity indicator**: If sale_price is available and no mortgage recorded, flag as potential cash buyer
7. **Deduplicate**: Same parcel_id = same property. Same owner across parcels = portfolio landlord.

### Portfolio Detection Logic
Group by normalized owner_name (or LLC name). Count distinct parcel_ids per owner. If count >= 2, flag as portfolio landlord. If count >= 5, flag as "high-value portfolio."

### Output
Save to `data/parsed/{county_name}_parsed.csv` with additional columns:
```
...(all raw columns)..., is_llc, is_absentee, is_no_homestead, is_cash_buyer, 
portfolio_count, portfolio_tier (single|small_portfolio|large_portfolio)
```

---

## STEP 3: Filter by ICP (03_filter_icp.py)

### What This Does
Scores and filters properties based on ICP criteria. Only qualified leads move forward.

### Scoring System (0-100 points)
See ICP_CRITERIA.md for full scoring matrix. Quick summary:

| Signal | Points |
|--------|--------|
| No homestead exemption (investment property) | +20 |
| Absentee owner (out-of-county or out-of-state) | +15 |
| LLC/Corp owned | +10 |
| Portfolio landlord (2-4 properties) | +10 |
| Portfolio landlord (5+ properties) | +20 |
| Cash purchase (no mortgage) | +15 |
| Property value $150K-$1M (DSCR sweet spot) | +10 |
| Recent purchase (last 24 months) | +10 |
| Multi-family property (use code) | +10 |
| STR-eligible zip code (tourist area) | +5 |

### Minimum Score Thresholds
- **Tier 1 (Hot leads)**: 50+ points — immediate outreach
- **Tier 2 (Warm leads)**: 30-49 points — secondary outreach
- **Below 30**: Do not pursue

### Output
Save to `data/filtered/{county_name}_qualified.csv` with:
```
...(all parsed columns)..., icp_score, icp_tier, icp_signals (comma-separated list of matched signals)
```

---

## STEP 4: Resolve LLC Owners via Sunbiz (04_sunbiz_llc_resolver.py)

### What This Does
For LLC-owned properties, looks up the entity on Florida's Division of Corporations (sunbiz.org) to find the actual human behind the LLC.

### Approach
1. Take all records where `is_llc = True`
2. Search sunbiz.org for the entity name
3. Extract: registered agent name, registered agent address, officer/director names, filing date, status
4. The registered agent is often the owner or their attorney
5. Officers/directors are often the principals

### Sunbiz Search URL Pattern
```
https://search.sunbiz.org/Inquiry/CorporationSearch/SearchByName?searchNameOrder={ENTITY_NAME}&searchTypeOrder=Entity%20Name
```

### Rate Limiting
- 1 request per 3 seconds
- Sunbiz may block rapid requests — implement exponential backoff
- If blocked, wait 30 minutes and resume

### Output
Save to `data/filtered/{county_name}_llc_resolved.csv` adding:
```
...(all filtered columns)..., registered_agent_name, registered_agent_address,
officer_names (semicolon-separated), sunbiz_filing_date, sunbiz_status
```

---

## STEP 5: Enrich Contacts (05_enrich_contacts.py)

### What This Does
Appends phone numbers and email addresses to property owner records using multiple free/cheap sources.

### Source Priority (cheapest first)

#### Source A: Florida Voter Registration File (FREE)
Florida sells its voter registration file. Contains: name, address, phone, DOB, party, voter status.
- Cost: ~$5 for statewide file (or free from some political data vendors)
- Request from: Florida Division of Elections
- Match on: owner_name + (mail_city OR mail_zip)
- Hit rate: ~40-50% of individual (non-LLC) owners

#### Source B: Whitepages / FastPeopleSearch Scraping (FREE but slow)
Free people-search sites index public records. Use Selenium or requests to:
1. Search by name + city/state
2. Extract phone numbers and email addresses
3. Rate limit: 1 search per 5 seconds to avoid blocks
- Hit rate: ~30-40% additional matches

#### Source C: Email Pattern Generation (FREE)
For LLC owners where you've resolved to a human name via Sunbiz:
1. If you have their business domain, generate email candidates:
   - firstname@domain.com
   - first.last@domain.com  
   - flast@domain.com
   - firstl@domain.com
2. Validate with MillionVerifier or email-verifier.com

#### Source D: Datazapp Batch Skip Trace ($0.03/record)
For remaining unmatched records, use Datazapp.com:
- Upload CSV with name + address
- Returns: cell phone, landline, email
- No subscription — pay per record
- $30 per 1,000 records
- This is the fallback for anything the free sources miss

#### Source E: Numverify API (FREE tier: 100/month)
Validate phone numbers are active and identify carrier/line type (mobile vs landline).

### Output
Save to `data/enriched/{county_name}_enriched.csv` adding:
```
...(all previous columns)..., phone_1, phone_1_source, phone_1_type (cell|landline),
phone_2, phone_2_source, phone_2_type,
email_1, email_1_source, email_2, email_2_source,
enrichment_sources (comma-separated list of sources that matched)
```

---

## STEP 6: Validate Contacts (06_validate_contacts.py)

### What This Does
Validates email deliverability and phone number activity before outreach.

### Email Validation
Use MillionVerifier (https://millionverifier.com):
- Cost: ~$0.50 per 1,000 emails
- Upload CSV, get back validated/invalid/risky flags
- Only keep "valid" and "catch-all" emails

### Phone Validation  
Use Twilio Lookup API:
- Cost: $0.005 per lookup
- Returns: carrier name, phone type (mobile/landline/voip), validity
- Prioritize mobile numbers for SMS
- Flag DNC (Do Not Call) numbers — use the FTC's DNC list (free download from donotcall.gov)

### Output
Save to `data/validated/{county_name}_validated.csv` adding:
```
...(all previous columns)..., email_1_status (valid|invalid|risky|catch_all),
email_2_status, phone_1_valid (bool), phone_1_carrier, phone_1_dnc (bool),
phone_2_valid, phone_2_carrier, phone_2_dnc
```

---

## STEP 7: Export Campaign-Ready Lists (07_export_campaign_ready.py)

### What This Does
Generates final output files formatted for different outreach channels.

### Export Formats

#### A. Instantly.ai Email Campaign CSV
```
email, first_name, last_name, company_name, property_address, 
property_value, portfolio_size, icp_tier, custom_1 (outreach_angle)
```

#### B. SMS/Dialer CSV (for Twilio, OpenPhone, etc.)
```
phone, first_name, last_name, property_address, property_value,
portfolio_size, icp_tier, is_dnc, phone_type
```
Exclude DNC numbers. Prioritize mobile numbers.

#### C. Direct Mail CSV (for mailing house)
```
first_name, last_name, company_name, mail_street, mail_city, mail_state, mail_zip,
property_address, property_value, icp_tier
```

#### D. Apollo.io Import CSV (for enrichment/sequences)
```
first_name, last_name, email, phone, company_name, title, city, state
```

### Output
Save to `data/campaign_ready/` with separate files per channel and ICP tier:
```
campaign_ready/
├── email_tier1_{county}.csv
├── email_tier2_{county}.csv
├── sms_tier1_{county}.csv
├── sms_tier2_{county}.csv
├── directmail_tier1_{county}.csv
├── directmail_tier2_{county}.csv
└── apollo_import_{county}.csv
```

---

## Cost Summary Per 5,000 Records

| Step | Cost |
|------|------|
| FL NAL file download | $0 (free via email request) |
| County bulk downloads | $0-50 depending on county |
| Sunbiz LLC lookup | $0 (free, just time) |
| Voter file match | $0-5 |
| Datazapp skip trace (unmatched ~2,500) | ~$75 |
| MillionVerifier email validation | ~$2.50 |
| Twilio phone validation | ~$25 |
| **TOTAL** | **~$100-155** |

Compare to: PropStream ($99/mo) + BatchData ($299/mo) + NeverBounce ($99/mo) = **$497/mo minimum**
