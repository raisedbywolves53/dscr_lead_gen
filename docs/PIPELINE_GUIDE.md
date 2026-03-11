# Pipeline Execution Guide

## Overview

Two-phase pipeline: **Foundation** (scripts 01-08) and **Intelligence** (scripts 10-20).

Foundation builds the lead list with contact info and scoring.
Intelligence layers on financing data, purchase history, wealth signals, network mapping, and deep profiling.

---

## Phase 1: Foundation Pipeline

```
01_download       → data/raw/{county}_raw.csv
02_parse          → data/parsed/{county}_parsed.csv
03_filter_icp     → data/filtered/{county}_qualified.csv
04_entity_resolve → data/filtered/{county}_resolved.csv
05_enrich         → data/enriched/top_leads_enriched.csv
05b_merge         → data/enriched/merged_enriched.csv
06_validate       → data/validated/{county}_validated.csv
07_export         → data/campaign_ready/
08_skip_trace     → data/enriched/tracerfy_results.csv
```

### Step 01: Download Property Data
- Downloads bulk property tax/ownership records from state source
- **State-specific:** Each state has different data portal and format
- Florida: FDOR NAL files from floridarevenue.com
- NC: County GIS/tax data downloads
- Save to `data/raw/`

### Step 02: Parse & Standardize
- Standardize column names, clean addresses, uppercase owner names
- Flag: LLC/Corp owners, absentee owners, non-homesteaded, cash buyers
- Detect portfolio landlords (group by owner, count properties)
- Filter to residential use codes only
- **State-specific:** Column names and use codes vary
- Save to `data/parsed/`

### Step 03: Score & Filter by ICP
- Score 0-100 using `config/scoring_weights.json`
- Assign ICP segment labels and tier (1/2/3)
- See `docs/ICP_PLAYBOOK.md` for scoring details
- **Mostly generic** — scoring logic applies to any market
- Save to `data/filtered/`

### Step 04: Entity Resolution (LLC → Person)
- Search state business registry for each LLC/Corp/Trust
- Extract officers, registered agent, filing date, status
- Pick most likely decision maker (Manager > President > first officer)
- Cache results in JSON for resume capability
- **State-specific:** Each state has different SoS registry
- Rate limit: varies (FL SunBiz: 3 sec/request)
- Save to `data/filtered/`

### Step 05: Contact Enrichment
- Score and rank leads, select top N
- Filter by target counties
- Email pattern generation from resolved names
- Save to `data/enriched/`

### Step 05b: Merge Enrichment Sources
- Merges: Tracerfy results, manual enrichment, Apollo results, DBPR data
- Consolidates phone/email from all sources into best available
- **State-agnostic**
- Save to `data/enriched/merged_enriched.csv`

### Step 06: Validate Contacts
- Email: MillionVerifier API → valid/invalid/risky/catch-all
- Phone: Twilio Lookup v2 → carrier, type (mobile/landline/VoIP)
- DNC check against FTC list
- Graceful skip if no API keys configured
- **State-agnostic**
- Save to `data/validated/`

### Step 07: Export Campaign-Ready
- Instantly.ai format (email campaigns)
- SMS/Dialer format (mobile phones, DNC-excluded)
- Direct mail format
- Split by Tier 1 and Tier 2
- **State-agnostic**
- Save to `data/campaign_ready/`

### Step 08: Tracerfy Skip Trace
- Upload leads to Tracerfy API ($0.02/match)
- Returns: up to 8 phones + 5 emails per lead
- Optional DNC scrub ($0.02/phone)
- **State-agnostic**
- Rate limit: 10 POST/5 minutes, ~24 min for 7,500 records
- Save to `data/enriched/tracerfy_results.csv`

---

## Phase 2: Intelligence Pipeline

```
10_apollo_enrich     → data/enriched/apollo_results.csv
11_clerk_records     → data/financing/{county}_mortgages.csv
12_purchase_history  → data/history/{county}_purchases.csv
13_rental_estimates  → data/enriched/rent_estimates.csv
14_wealth_signals    → data/signals/wealth_signals.csv
15_network_mapping   → data/signals/network_map.csv
16_life_events       → data/signals/life_events.csv
20_build_dossier     → data/dossiers/investor_dossiers.xlsx
```

### Step 10: Apollo.io Enrichment (**NOT RECOMMENDED**)
- Returns near-zero data for LLC-based RE investors
- Keep script for reference but don't run on new deployments

### Step 11: County Clerk / Register of Deeds
- Search by owner name for mortgage recordings
- Extract: lender name, loan amount, recording date, document type
- Classify lender type (bank, credit union, hard money, private)
- Calculate: estimated balance, LTV, maturity date
- **State/county-specific:** Every county has different portal
- Rate limit: ~1 request per 2 seconds

### Step 12: Purchase History (SDF/Deed Records)
- Full acquisition timeline per owner
- Calculate: flip vs hold, cash vs financed, purchase frequency
- **State-specific:** Different data format per state

### Step 13: Rental Estimates
- HUD Fair Market Rents by zip + bedroom count
- **State-agnostic** (HUD data is nationwide)

### Step 14: Wealth Signals
- FEC political donations, ProPublica IRS 990, SEC EDGAR
- SunBiz/SoS reverse lookup (all LLCs per person)
- **Mostly state-agnostic** (FEC/990/SEC are federal)

### Step 15: Network Mapping
- Co-investors (shared LLC officers), shared lenders, shared PMs
- **State-agnostic** logic, state-specific data sources

### Step 16: Life Events
- County clerk: liens, lis pendens, divorce, probate
- **County-specific:** Same portal as Step 11

### Step 20: Build Dossier
- Merge all sources into comprehensive investor profile
- Calculate final opportunity score (0-100)
- Output: multi-tab Excel + JSON + Airtable upload
- **State-agnostic**

---

## Execution Commands

### Full Market Run (example: Florida PB/Broward)

```bash
# Phase 1: Foundation
python scrape/scripts/01_download_nal.py --county "palm beach"
python scrape/scripts/02_parse_nal.py --county palm_beach
python scrape/scripts/03_filter_icp.py --county palm_beach
python scrape/scripts/04_sunbiz_llc_resolver.py --county palm_beach
python scrape/scripts/05_enrich_contacts.py --counties "palm beach,broward"
python scrape/scripts/08_tracerfy_skip_trace.py
python scrape/scripts/05b_merge_enrichment.py
python scrape/scripts/06_validate_contacts.py --county merged
python scrape/scripts/07_export_campaign_ready.py --county merged

# Phase 2: Intelligence
python scrape/scripts/11_clerk_lender_lookup.py
python scrape/scripts/12_sdf_purchase_history.py --county palm_beach
python scrape/scripts/13_rental_estimates.py
python scrape/scripts/14_wealth_signals.py
python scrape/scripts/15_network_mapping.py
python scrape/scripts/16_life_events.py
python scrape/scripts/20_build_dossier.py
```

### MVP Quick Run (skip intelligence, get callable leads fast)

```bash
python scrape/scripts/05_enrich_contacts.py --counties "palm beach,broward"
python scrape/scripts/08_tracerfy_skip_trace.py --skip-dnc
python scrape/scripts/05b_merge_enrichment.py
python scrape/scripts/06_validate_contacts.py --county merged --max-phones 1800
python scrape/scripts/07_export_campaign_ready.py --county merged
python scrape/scripts/build_google_sheets.py
```

---

## Dependencies

```bash
pip install pandas openpyxl requests beautifulsoup4 python-dotenv
# Optional: selenium (for some clerk portals), twilio, lxml
```

---

## Rate Limits Reference

| Service | Limit | Delay |
|---------|-------|-------|
| SunBiz (FL) | Cloudflare-protected | 3 sec/request |
| Tracerfy | 10 POST/5 minutes | Built into script |
| SEC EDGAR | 10 req/sec | 7 req/sec recommended |
| FEC API | 1,000 req/hr | Reasonable |
| County Clerk portals | Varies | 2 sec/request |
| Twilio Lookup | 100 req/sec | No delay needed |
| MillionVerifier | Fast | No delay needed |

---

## Known Issues

| Issue | Impact | Workaround |
|-------|--------|-----------|
| Sale date aggregation uses max() | Rate refi detection undercounts for multi-property owners | Run refi detection at property level before aggregation |
| No mortgage balance in most state records | Equity is estimated from value vs purchase price | Supplement with clerk/ATTOM data |
| SunBiz/SoS may block after many requests | Can't resolve all LLCs in one run | Use caching, batch over days, consider bulk FTP data |
| People search sites may require CAPTCHA | Enrichment is best-effort | Use Tracerfy as primary, people search as supplement |
| County clerk portals vary wildly | Each county needs custom scraper | Start with the most accessible, use 2Captcha where needed |
| Institutional owners (50+ properties) | Inflate serial investor counts | Filter out property_count > 50 as institutional |

---

## Performance Benchmarks (Florida PB/Broward, 7,537 leads)

| Step | Runtime | Memory | Cost |
|------|---------|--------|------|
| Download + Parse | 5-10 min | ~300MB | $0 |
| Score + Filter | 2-3 min | ~200MB | $0 |
| SunBiz Resolve (500) | ~17 min | ~400MB | $0 |
| Tracerfy Skip Trace | ~24 min | minimal | $57.60 |
| Merge + Validate | 5-10 min | ~200MB | ~$14 |
| Export + Sheets | 5 min | ~200MB | $0 |
| **Total Foundation** | **~65 min** | **~400MB peak** | **~$72** |
