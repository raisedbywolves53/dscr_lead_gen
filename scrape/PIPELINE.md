# PIPELINE.md — Investor Intelligence Pipeline Execution Spec

## Pipeline Overview

Two-phase pipeline: **Foundation** (scripts 01-07) and **Intelligence** (scripts 10-20).

Foundation builds the lead list with basic contact info and scoring.
Intelligence layers on financing data, purchase history, wealth signals,
network mapping, and deep profiling to create full investor dossiers.

---

## Phase 1: Foundation Pipeline (Built)

```
01_download_nal.py       → data/raw/{county}_raw.csv
02_parse_nal.py          → data/parsed/{county}_parsed.csv
03_filter_icp.py         → data/filtered/{county}_qualified.csv
04_sunbiz_resolver.py    → data/filtered/{county}_llc_resolved.csv
05_enrich_contacts.py    → data/enriched/top_leads_enriched.csv
05b_merge_enrichment.py  → data/enriched/merged_enriched.csv
06_validate_contacts.py  → data/validated/{county}_validated.csv
07_export_campaign_ready.py → data/campaign_ready/
```

### Step 1: Download FDOR Property Data (01_download_nal.py)
- Downloads NAL (Name-Address-Legal) files from FL Dept of Revenue
- Covers all 67 counties — one ZIP per county containing CSV
- Also downloads from individual county property appraiser sites
- Save to `data/raw/{county}_raw.csv`

### Step 2: Parse & Standardize (02_parse_nal.py)
- Standardize column names, clean addresses, uppercase owner names
- Flag: LLC/Corp owners, absentee owners, non-homesteaded, cash buyers
- Detect portfolio landlords (group by owner, count properties)
- Filter to residential use codes only (01, 02, 03, 04, 05, 08)
- Save to `data/parsed/{county}_parsed.csv`

### Step 3: Score & Filter by ICP (03_filter_icp.py)
- Score 0-100 using config/scoring_weights.json
- Tier 1 (50+): Hot. Tier 2 (30-49): Warm. Tier 3 (15-29): Nurture. <15: Discard
- Assign ICP segment labels
- Save to `data/filtered/{county}_qualified.csv`

### Step 4: SunBiz LLC Resolution (04_sunbiz_resolver.py)
- For each LLC, POST to sunbiz.org search endpoint
- Extract ALL officers/directors (not just first match)
- Extract registered agent, filing date, entity status
- Pick most likely decision maker (Manager > President > first officer)
- Cache results in JSON for resume capability
- Save to `data/filtered/{county}_llc_resolved.csv`

### Step 5: Contact Enrichment (05_enrich_contacts.py)
- Score and rank leads, select top N (default 25 for testing)
- Filter by `--counties` flag (Palm Beach + Broward)
- SunBiz re-resolution for unresolved LLCs
- Email pattern generation from resolved names
- Datazapp CSV export for batch skip trace
- Research tracker Excel with people search URLs
- Save to `data/enriched/`

### Step 5b: Merge Enrichment (05b_merge_enrichment.py)
- Merges: research tracker (manual), Datazapp results, Apollo results
- Consolidates into single enriched file
- Save to `data/enriched/merged_enriched.csv`

### Step 6: Validate Contacts (06_validate_contacts.py)
- Email: MillionVerifier API → valid/invalid/risky/catch-all
- Phone: Twilio Lookup → carrier, type (mobile/landline/voip), validity
- DNC check against FTC list if available
- Graceful skip if no API keys configured
- Save to `data/validated/`

### Step 7: Export Campaign-Ready (07_export_campaign_ready.py)
- Instantly.ai format (email campaigns)
- SMS/Dialer format (Twilio, OpenPhone) — DNC excluded, mobile first
- Direct mail format (mailing house)
- Apollo.io import format
- Split by Tier 1 and Tier 2
- Save to `data/campaign_ready/`

---

## Phase 2: Intelligence Pipeline (To Build)

```
10_apollo_enrich.py          → data/enriched/apollo_results.csv
11_county_clerk.py           → data/financing/{county}_mortgages.csv
12_sdf_purchase_history.py   → data/history/{county}_purchases.csv
13_rental_estimates.py       → data/enriched/rent_estimates.csv
14_wealth_signals.py         → data/signals/wealth_signals.csv
15_network_mapping.py        → data/signals/network_map.csv
16_life_events.py            → data/signals/life_events.csv
20_build_dossier.py          → data/dossiers/investor_dossiers.xlsx
```

### Step 10: Apollo.io Enrichment (10_apollo_enrich.py)
**Source:** Apollo.io API ($100/mo plan)
**What it returns per person:**
- Email (validated)
- Phone (with mobile flag)
- LinkedIn profile URL
- Current employer and title
- Social media profiles (Twitter, Facebook)
- Company info (if business owner)

**Implementation:**
- Accept list of person names + company names from SunBiz resolution
- Call Apollo People Enrichment API
- Also try Apollo Company Enrichment for LLC names
- Cache all responses (never pay twice for same lookup)
- Rate limit: 100 requests/minute
- Save to `data/enriched/apollo_results.csv`

### Step 11: County Clerk Mortgage Scraping (11_county_clerk.py)
**Source:** Palm Beach County Clerk (mypalmbeachclerk.com), Broward County Clerk (browardclerk.org)
**What it returns per property:**
- All recorded mortgages (deed of trust recordings)
- Lender name
- Original loan amount
- Recording date (≈ origination date)
- Document type (mortgage, modification, assignment, satisfaction)
- Lien recordings
- Lis pendens (pre-foreclosure)

**Implementation:**
- For each parcel ID in our lead list, search county clerk records
- Parse mortgage recordings: extract lender, amount, date
- Parse lien recordings: extract type, amount, date
- Classify lender type: bank, credit union, hard money, private
- Calculate: estimated balance (amortization), LTV, maturity date
- Detect: hard money exposure, balloon maturities, high-rate vintage loans
- Rate limit: 1 request per 2 seconds
- Save to `data/financing/{county}_mortgages.csv`

**Derived fields:**
- Total debt across portfolio
- Total equity (portfolio value - total debt)
- Portfolio DSCR (estimated rent / estimated debt service)
- Loans maturing within 24 months
- Hard money exposure count and amount
- Average interest rate estimate

### Step 12: Purchase History via SDF (12_sdf_purchase_history.py)
**Source:** FDOR SDF (Sales Data File) — same portal as NAL
**What it returns:**
- Every recorded sale for every parcel in Florida
- Sale price, sale date, buyer, seller, deed type
- Qualification code (arms-length vs non-arms-length)

**Implementation:**
- Download SDF files for target counties
- For each lead, extract full purchase timeline
- Identify: acquisitions, dispositions, flips, holds
- Calculate: purchase frequency, avg price, cash vs financed (cross-ref with Step 11)
- Detect: off-market purchases (sale price = $0 or $100)
- Save to `data/history/{county}_purchases.csv`

### Step 13: Rental Estimates (13_rental_estimates.py)
**Source:** HUD Fair Market Rents (free bulk download), Zillow (scrape)
**What it returns:**
- Estimated monthly rent per property (by zip + bedroom count)
- STR revenue estimate (from DBPR + Airbnb listing data if available)

**Implementation:**
- Download HUD FMR tables (updated annually, free)
- Match each property by zip code + bedroom count → monthly rent estimate
- For STR-licensed properties, attempt Airbnb listing lookup for revenue data
- Calculate: portfolio gross rent, estimated NOI, portfolio DSCR
- Save to `data/enriched/rent_estimates.csv`

### Step 14: Wealth Signals (14_wealth_signals.py)
**Source:** FEC.gov API, IRS 990 (ProPublica), SEC EDGAR, DBPR
**What it returns:**
- Political donation history (amount, recipient, date)
- Foundation/nonprofit contributions
- Board seats and officer positions
- Professional licenses held
- Other LLCs owned (SunBiz reverse lookup by officer name)

**Implementation:**
- FEC API: search by name + state → donation records
- ProPublica Nonprofit Explorer: search by name → 990 filings
- SEC EDGAR: search by name → officer positions
- SunBiz reverse: search by person name → all LLCs where they're an officer
- Save to `data/signals/wealth_signals.csv`

### Step 15: Network Mapping (15_network_mapping.py)
**Source:** Cross-referencing SunBiz, county clerk, DBPR
**What it returns:**
- Co-investors (shared LLC officers)
- Property managers managing their properties
- Real estate agents from closing documents
- Shared lenders across leads
- Syndication partners

**Implementation:**
- SunBiz cross-reference: which of our leads share officers/agents?
- DBPR: which PM companies manage properties at lead addresses?
- County clerk: which agents/title companies appear in closings?
- Build relationship graph: lead → shared connection → other leads
- Save to `data/signals/network_map.csv`

### Step 16: Life Events (16_life_events.py)
**Source:** County clerk records
**What it returns:**
- Divorce filings
- Probate/estate proceedings
- Lis pendens (pre-foreclosure)
- Tax liens
- Code violations
- Judgment liens

**Implementation:**
- Search county clerk by owner name for non-mortgage recordings
- Classify document types into life event categories
- Flag urgency level (divorce + investment property = motivated seller/refi candidate)
- Save to `data/signals/life_events.csv`

### Step 20: Build Investor Dossier (20_build_dossier.py)
**Assembles everything into the final investor profile.**

Takes all outputs from steps 01-16 and merges into a single comprehensive
profile per investor. Calculates the final opportunity score.

**Output:** Multi-tab Excel workbook per county + JSON for programmatic access
- Tab 1: Investor Summary (contact, entity, score)
- Tab 2: Portfolio Detail (per-property breakdown)
- Tab 3: Financing Analysis (per-property mortgages, LTV, maturity)
- Tab 4: Purchase History Timeline
- Tab 5: Opportunity Signals
- Tab 6: Network & Relationships
- Tab 7: Wealth Indicators

Save to `data/dossiers/`

---

## Execution Order

### 25-Record Proof of Concept
```bash
# Already have data from existing pipeline (pipeline/output/06_enriched.csv)

# 1. Select top 25 + resolve LLCs + generate research materials
python scripts/05_enrich_contacts.py --limit 25 --counties "palm beach,broward"

# 2. Apollo enrichment (needs API key in .env)
python scripts/10_apollo_enrich.py

# 3. County clerk mortgage data (for 25 leads' properties)
python scripts/11_county_clerk.py --limit 25

# 4. Merge all enrichment sources
python scripts/05b_merge_enrichment.py

# 5. Validate contacts
python scripts/06_validate_contacts.py --county merged

# 6. Build dossiers
python scripts/20_build_dossier.py --limit 25
```

### Full County Run (after POC validated)
```bash
python scripts/01_download_nal.py --county "palm beach"
python scripts/02_parse_nal.py --county palm_beach
python scripts/03_filter_icp.py --county palm_beach
python scripts/04_sunbiz_resolver.py --county palm_beach
python scripts/10_apollo_enrich.py --county palm_beach
python scripts/11_county_clerk.py --county palm_beach
python scripts/12_sdf_purchase_history.py --county palm_beach
python scripts/13_rental_estimates.py --county palm_beach
python scripts/14_wealth_signals.py --county palm_beach
python scripts/15_network_mapping.py --county palm_beach
python scripts/16_life_events.py --county palm_beach
python scripts/20_build_dossier.py --county palm_beach
python scripts/06_validate_contacts.py --county palm_beach
python scripts/07_export_campaign_ready.py --county palm_beach
```

---

## Cost Estimate Per 1,000 Leads

| Step | Cost |
|------|------|
| FDOR NAL/SDF download | $0 |
| SunBiz LLC resolution | $0 (time only) |
| County clerk scraping | $0 (time only) |
| Apollo enrichment | Included in $100/mo plan |
| Datazapp skip trace (unmatched) | ~$15 |
| MillionVerifier email validation | ~$0.50 |
| Twilio phone validation | ~$5 |
| FEC / IRS 990 / HUD FMR | $0 |
| **TOTAL** | **~$20 + $100/mo Apollo** |

Compare to: PropStream ($99/mo) + Reonomy ($249/mo) + BatchData ($299/mo) = **$647/mo minimum**, and none of them give you the financing intelligence or network mapping we build.
