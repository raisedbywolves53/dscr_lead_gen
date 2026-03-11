# DSCR Loan Prospect Intelligence System
## Complete Data Acquisition & Outreach Strategy
### Palm Beach & Broward County, Florida

**Prepared by:** Zack's Data Science Partner
**Date:** March 2026
**Version:** 1.0

---

## Executive Summary

This document outlines a complete, actionable strategy to build a DSCR (Debt Service Coverage Ratio) loan prospect intelligence engine targeting real estate investors in Palm Beach and Broward County, Florida. The system is designed to be built incrementally — starting with free public data sources and scaling up with commercial providers as ROI is proven.

**Total estimated cost to reach production:**
- Phase 1 (Foundation): $0–$700/year using only free public data
- Phase 2 (Enrichment): $200–$500/month adding skip tracing + rent estimation
- Phase 3 (Full Intelligence): $800–$2,000/month at scale with all signals active

**Estimated universe size:** 80,000–120,000 non-owner-occupied residential properties across both counties, owned by approximately 40,000–60,000 unique investor entities/individuals.

---

## Table of Contents

1. [Phase 1: The Foundation Layer (Free Public Data)](#phase-1-the-foundation-layer)
2. [Phase 2: Contact Enrichment & Skip Tracing](#phase-2-contact-enrichment)
3. [Phase 3: Financing Intelligence](#phase-3-financing-intelligence)
4. [Phase 4: Rental Performance & DSCR Estimation](#phase-4-rental-performance)
5. [Phase 5: Behavioral & Intent Signals](#phase-5-behavioral-signals)
6. [Phase 6: Wealth & Financial Strength Signals](#phase-6-wealth-signals)
7. [Phase 7: Relationship Graph & Network Mapping](#phase-7-relationship-graph)
8. [Phase 8: Opportunity Scoring](#phase-8-opportunity-scoring)
9. [DNC/TCPA Compliance Framework](#compliance-framework)
10. [Cost Summary & Build Timeline](#cost-summary)
11. [Data Architecture Recommendation](#data-architecture)

---

## Phase 1: The Foundation Layer (Free Public Data) {#phase-1-the-foundation-layer}

This is where you start. All of this data is free and gives you 60–70% of what you need to identify DSCR prospects.

### 1A. Florida Department of Revenue — NAL & SDF Files (FREE)

**What it is:** The Florida Department of Revenue publishes free statewide assessment roll data for every county in CSV/DBF format. This is the single most important free data source.

**URL:** https://floridarevenue.com/property/Pages/DataPortal_RequestAssessmentRollGISData.aspx

**County codes:** Palm Beach = 50, Broward = 06

**Files to download:**
- **NAL (Name-Address-Legal):** 158+ fields per parcel — owner name, mailing address, property address, assessed/market/taxable values, exemption status, land use codes, sale history
- **SDF (Sale Data File):** Detailed transaction data — sale price, deed type, sale date, qualification codes

**Key fields for DSCR prospecting:**
- Owner name(s) — individual or entity
- Mailing address vs. property address (absentee owner identification)
- Homestead exemption status (no exemption = likely investor)
- Property use code (SFR, multifamily, condo, commercial)
- Market/assessed value
- Most recent sale price and date
- Exemption types applied

**What you can derive from this data alone:**
- Complete list of all non-homesteaded properties (investment properties)
- Absentee owner identification (mailing address ≠ property address)
- Out-of-state investor identification
- LLC/entity-owned properties
- Portfolio investors (same owner name across multiple parcels)
- Estimated property values
- Purchase timeline and frequency
- Geographic concentration of portfolios

**Action steps:**
1. Download NAL and SDF files for counties 50 and 06
2. Parse CSV files into a database (PostgreSQL recommended)
3. Filter for non-homesteaded residential properties
4. Group by owner name/entity to build portfolio profiles
5. Flag absentee owners (different mailing and property addresses)
6. Flag entity owners (LLC, Corp, Trust in owner name field)

**Cost: $0**

---

### 1B. Florida Division of Corporations — Sunbiz.org (FREE)

**What it is:** Florida's official business entity registry. Every LLC, corporation, LP, and trust registered in Florida is here, including officer names, registered agent, addresses, and formation dates.

**Bulk data access:** Free FTP download
- URL: https://dos.fl.gov/sunbiz/other-services/data-downloads/
- FTP credentials: Username `Public`, Password `PubAccess1845!`
- Quarterly full data dumps (all 3.5M+ active entities) in fixed-width ASCII format (1,440 chars/record)
- Daily incremental files also available

**Key fields:**
- Entity name and document number
- Filing date and status (active/inactive/dissolved)
- Principal office address
- Mailing address
- Registered agent name and Florida street address
- Up to 6 officer/member names with titles and addresses
- Federal Employer ID Number (FEIN)
- Entity email address (public record)

**What you do with this:**
1. Download quarterly data dump
2. Parse the fixed-width file into a database
3. Cross-reference every LLC/Corp/Trust owner found in the property records
4. Extract officer names, registered agent names, and addresses
5. Handle nested LLCs (where officers are themselves entities) by recursive lookup
6. Build the individual-to-entity mapping

**Important limitation:** Bulk files only include up to 6 officers per entity. Entities with more require individual web lookups or use of FloridaBiz Scraper ($, 3-day free trial) or Apify ($0.02–$0.05/100 records).

**Cost: $0 for bulk data; $0–$50 for supplemental scraping tools**

---

### 1C. County Clerk of Court — Recorded Documents (FREE to LOW COST)

**What it is:** Deeds, mortgages, liens, satisfactions, and other recorded instruments. This is where mortgage/financing data lives.

**Palm Beach County:**
- Online search (free): https://erec.mypalmbeachclerk.com/
- FTP subscription (bulk index data): $600/year or $50/month
- Searchable by: party name, document type, book/page, instrument number, consideration amount, parcel ID
- Images available from January 1968 to present

**Broward County:**
- Online search (free): https://officialrecords.broward.org/AcclaimWeb
- FTP bulk data: **FREE** (10 rolling days of index + images)
- Records from 1978 forward fully searchable

**Key data from recorded documents:**
- Grantor (seller) and Grantee (buyer) names on deeds
- Mortgage amount, lender name (grantee on mortgage docs)
- Recording date
- Document type (warranty deed, quit claim, mortgage, satisfaction, assignment)
- Consideration/sale amount (on deeds)
- Parcel ID cross-reference

**What you can derive:**
- Current lender for each property (most recent unsatisfied mortgage)
- Original mortgage amount
- Origination date
- Whether a mortgage has been satisfied (paid off)
- Cash purchases (deed recorded with no accompanying mortgage)
- Hard money loans (non-bank lender names)
- Assignment of mortgage (loan was sold/transferred)
- Lien positions
- Refinance history

**Action steps:**
1. Start with Broward's free FTP data (10 days rolling)
2. Subscribe to PBC Clerk FTP ($600/year) for bulk index data
3. Build a pipeline to match mortgage documents to property records via parcel ID
4. Track mortgage origination dates, amounts, and lender names
5. Flag properties with no active mortgage (high equity / cash purchase)
6. Flag non-bank lenders (hard money / private lending indicators)

**Cost: $0–$600/year**

---

### 1D. County Property Appraiser — Direct Access (FREE)

**Palm Beach County Property Appraiser (PBCPAO):**
- Website: https://pbcpao.gov
- Online search (PAPA system): free per-parcel lookups
- Bulk data: Standard flat files are free from Public Services dept; custom formatting $33/file; custom programming $66/hour
- GIS Open Data: https://opendata2-pbcgov.opendata.arcgis.com/ (free parcel boundaries + attributes)
- ArcGIS REST API available for programmatic queries (max 1,000 records per query)

**Broward County Property Appraiser (BCPA):**
- Website: https://bcpa.net
- Online search: https://web.bcpa.net/BcpaClient/
- Tax Roll data: Annual files at bcpa.net/2025TaxRollInfo.asp
- GIS data: https://geohub-bcgis.opendata.arcgis.com/
- Bulk data requests: Contact (954) 357-6830

**Why use this in addition to FL DOR data:** County appraiser data may be more current than the annual state rollup, and includes building characteristics (beds, baths, sqft, year built, construction type) essential for rent estimation and property analysis.

**Cost: $0–$100**

---

### PHASE 1 OUTPUT: The Investor Master List

After Phase 1, you will have:

| Data Point | Source | Cost |
|-----------|--------|------|
| Owner name (individual or entity) | FL DOR NAL | Free |
| Mailing address | FL DOR NAL | Free |
| Property address(es) owned | FL DOR NAL | Free |
| Property count per owner | FL DOR NAL (derived) | Free |
| Total portfolio value (estimated) | FL DOR NAL | Free |
| Property type mix (SFR, MF, condo) | FL DOR NAL use codes | Free |
| Homestead status (investor flag) | FL DOR NAL | Free |
| Absentee owner flag | FL DOR NAL (derived) | Free |
| Out-of-state investor flag | FL DOR NAL (derived) | Free |
| Entity ownership flag | FL DOR NAL + Sunbiz | Free |
| LLC officer/agent names | Sunbiz FTP | Free |
| LLC registered agent address | Sunbiz FTP | Free |
| Entity formation date | Sunbiz FTP | Free |
| Entity email (public record) | Sunbiz FTP | Free |
| Most recent sale price/date | FL DOR SDF | Free |
| Purchase history timeline | FL DOR SDF | Free |
| Current lender name | County Clerk records | Free–$600/yr |
| Mortgage amount | County Clerk records | Free–$600/yr |
| Mortgage origination date | County Clerk records | Free–$600/yr |
| Cash purchase flag | County Clerk (derived) | Free–$600/yr |
| Hard money lender flag | County Clerk (derived) | Free–$600/yr |
| Building characteristics | County Appraiser | Free |

**Estimated records:** 80,000–120,000 properties → 40,000–60,000 unique owners/entities

---

## Phase 2: Contact Enrichment & Skip Tracing {#phase-2-contact-enrichment}

You have the investor list. Now you need phone numbers and emails to actually reach them.

### 2A. Skip Tracing Services

This is the bridge between property records and actionable contact data.

**Recommended providers by volume:**

| Volume | Provider | Cost/Record | Monthly Commitment |
|--------|----------|-------------|-------------------|
| < 5,000/mo | PropStream | $0.10–$0.12 | $99/mo platform + per-record |
| < 5,000/mo | REISkip | $0.15–$0.22 | Pay-per-match (no match = free) |
| 5K–50K/mo | BatchData Growth | $0.02–$0.10 | $500–$2,000/mo |
| 50K–100K/mo | BatchData Enterprise | $0.006–$0.02 | $5,000–$20,000/mo |
| Any volume | Geopoint | $0.03–$0.10 | $300/mo for 10K |

**What skip tracing returns:**
- Up to 4–10 phone numbers per person (mobile prioritized)
- Up to 3–5 email addresses per person
- Landline vs. mobile classification
- Mailing address verification
- Relative/associate connections
- Social media profile matches (varies by provider)

**Expected hit rates:** 75–90% for phone numbers, 60–80% for email addresses.

### 2B. Email Enrichment (Supplemental)

For business-domain emails (investors with company websites):

| Tool | Cost/Email | Monthly Cost | Best For |
|------|-----------|-------------|----------|
| Snov.io Pro 50K | $0.005 | $249 | Bulk business email finding |
| Hunter.io Growth | $0.015 | $149 | Domain-based email discovery |
| Apollo.io | Free–$0.20/credit | Free–$49/mo | LinkedIn-based enrichment |

### 2C. LinkedIn Profile Matching

For investors who are active professionals or have business profiles:

| Tool | Cost | Notes |
|------|------|-------|
| Apollo.io (free tier) | $0 | 50 contacts/month, 275M database |
| Lusha | $0–$14.95/mo | 70 free credits/month; LinkedIn integration |
| PhantomBuster | $56/mo | LinkedIn scraping automations |

### 2D. Phone Validation & DNC Scrubbing (MANDATORY)

Before making a single call, every phone number must be:

1. **Validated for line type** (mobile vs. landline vs. VoIP):
   - Twilio Lookup: $0.005–$0.008/number
   - NumVerify: $0.002–$0.003/number

2. **Scrubbed against DNC registries:**
   - Federal DNC: FTC registry subscription (first 5 area codes free, then $82/area code/year)
   - Florida State DNC: Maintained by FDACS, updated quarterly
   - MyFreeDNC: $0.0008/record for combined scrubbing
   - DNCScrub: Volume-based, includes federal + state + wireless + litigator lists

3. **Scrubbed against known litigator lists:**
   - Many skip trace providers (BatchData, etc.) include this
   - The DNC Project: $599/mo unlimited with litigator scrub

### PHASE 2 COST SUMMARY

| Component | Monthly Cost (5K records) | Monthly Cost (50K records) |
|-----------|--------------------------|---------------------------|
| Skip tracing | $500–$750 | $1,000–$5,000 |
| Email enrichment | $39–$149 | $149–$249 |
| Phone validation | $25–$40 | $100–$150 |
| DNC scrubbing | $4–$25 | $25–$100 |
| **Total** | **$568–$964** | **$1,274–$5,499** |

---

## Phase 3: Financing Intelligence {#phase-3-financing-intelligence}

This is where the DSCR opportunity signals live. You need to understand each investor's current debt structure.

### 3A. Mortgage Data from County Records (Phase 1 continuation)

From the clerk of court records, you already have:
- Lender name
- Mortgage amount (original)
- Recording/origination date
- Document type (mortgage, assignment, satisfaction)

### 3B. Deriving Key Financing Metrics

**Estimated remaining balance:** Apply standard amortization to the original loan amount using the origination date and estimated interest rate (based on prevailing rates at time of origination).

**Estimated LTV:** Remaining balance ÷ current market value (from property appraiser).

**Estimated equity:** Current market value – estimated remaining balance.

**Loan maturity estimation:** Standard 30-year for conventional; 15-year for some; hard money = 1–5 years.

**Interest rate estimation:** Use the Federal Reserve FRED data for historical mortgage rate benchmarks at origination date. Add 1–2% for DSCR/investor loans, 3–5% for hard money.

### 3C. Commercial Data Providers for Enhanced Mortgage Data

For more precise mortgage data (actual interest rates, loan terms, balloon dates):

| Provider | Data | Cost |
|----------|------|------|
| ATTOM Data | Mortgage data, deed data, lender info, rate estimates | $95–$500+/mo |
| CoreLogic | Most comprehensive mortgage data (rate, term, type) | Enterprise pricing (expensive) |
| BatchData | 140+ mortgage fields per record | $500–$5,000/mo |
| Black Knight (ICE) | Institutional-grade mortgage analytics | Enterprise only |

**Recommendation:** Start with county clerk data + amortization estimates (free). Graduate to ATTOM or BatchData when the business justifies the spend.

### 3D. Opportunity Signal Flags

Flag properties where:

| Signal | How to Identify | Why It Matters |
|--------|----------------|---------------|
| Rate > current market | Origination date + historical rate lookup | Refinance opportunity |
| Loan maturing in 12–24 months | Origination date + estimated term | Forced refinance |
| Hard money loan | Non-bank lender name in mortgage record | Must refinance within 1–5 years |
| Bridge loan | Short-term non-bank lender | Must refinance |
| Recent cash purchase | Deed with no accompanying mortgage | May want leverage now |
| High equity (60%+) | Estimated balance vs. market value | Cash-out refi opportunity |
| Portfolio consolidation | Multiple loans across multiple properties | Blanket DSCR opportunity |
| Loan assignment | Assignment of mortgage recorded | Loan was sold; borrower may be unhappy |

---

## Phase 4: Rental Performance & DSCR Estimation {#phase-4-rental-performance}

### 4A. Rent Estimation

**For long-term rentals:**

| Tool | Cost | Method |
|------|------|--------|
| Rentometer | $199/year (API with 200 credits) | Address-based rent comps |
| Mashvisor API | $129/mo | Combined MLS + LTR + STR data |
| Zillow Rent Zestimate API | Free–$5,000/mo | Requires approval (lengthy process) |
| Manual estimation | Free | County appraiser sqft/beds × local $/sqft rent |

**For short-term rentals (Airbnb/VRBO):**

| Tool | Cost | Data |
|------|------|------|
| AirDNA | $34–$125/mo (individual); API = custom | ADR, occupancy, revenue per listing |
| Mashvisor | $129/mo | STR revenue estimation + comps |
| AllTheRooms | $19–$49/mo | Market-level STR data |

### 4B. Identifying STR Properties

- **DBPR License Search:** https://www.myfloridalicense.com/wl11.asp — search for "Vacation Rental" licenses by county (free)
- **DBPR Weekly Bulk Downloads:** Free CSV of all active/inactive licensees at https://www2.myfloridalicense.com/instant-public-records/
- **Palm Beach County Tourist Development Tax:** Registration records via PBC Tax Collector
- **Broward County Tourist Development Tax:** Registration via county
- **Hollywood, FL:** Publicly accessible vacation rental license database (PDF + Excel) at hollywoodfl.org
- **Cross-reference with AirDNA/Mashvisor listing data**

### 4C. DSCR Calculation

```
DSCR = Net Operating Income (NOI) / Annual Debt Service (ADS)

Where:
NOI = Gross Rental Income × (1 - Vacancy Rate) - Operating Expenses
ADS = Monthly Mortgage Payment × 12

Operating Expenses typically = 35–50% of gross rent, including:
  - Property taxes (from county appraiser — exact)
  - Insurance (estimate based on value + location)
  - Maintenance (5–10% of rent)
  - Management fees (8–12% of rent)
  - HOA/COA dues (from listing data if available)
```

**Most DSCR lenders require 1.15x–1.35x minimum.**

Properties with estimated DSCR above 1.25x are strong candidates for DSCR financing. Properties below 1.0x need restructuring (rate reduction, longer amortization, or additional equity).

### 4D. Occupancy & Management Data

- **Property management companies:** SFPMA directory (sfpma.com), ManageMyProperty.com, NARPM membership lists
- **Listing presence:** Check Airbnb, VRBO, Zillow Rentals for active listings matching property addresses
- **Occupancy estimation:** Use AirDNA data for STRs; assume 92–95% for well-managed LTRs in South Florida

---

## Phase 5: Behavioral & Intent Signals {#phase-5-behavioral-signals}

### 5A. Acquisition Behavior (From Public Records — FREE)

Using the FL DOR Sale Data Files and county recorder data:

| Metric | How to Calculate |
|--------|-----------------|
| Purchase frequency | Count transactions per owner over time |
| Average purchase price | Mean of all acquisition prices |
| Markets entered | Geographic distribution of purchases |
| Cash vs. financed purchases | Cross-reference deeds with mortgages |
| Flip vs. hold behavior | Time between purchase and resale |
| Scaling trajectory | Purchases per year trending up/down |
| Time since last purchase | Days since most recent acquisition |

### 5B. Investor Psychology Segmentation

Based on portfolio size and behavior patterns:

| Segment | Portfolio Size | Characteristics | DSCR Relevance |
|---------|---------------|-----------------|----------------|
| Accidental Landlord | 1–2 properties | Passive, often inherited or couldn't sell | Low — may not know about DSCR |
| Growth Investor | 3–10 properties | Actively buying, leverage-friendly | High — sweet spot for DSCR |
| Professional Investor | 10–50 properties | Sophisticated, shops rates | Very High — DSCR core market |
| Operator/Fund | 50+ properties | Runs like a business, may use agency | Medium — may use larger commercial products |

### 5C. Online & Social Intent Signals

| Signal Source | How to Monitor | Cost |
|--------------|---------------|------|
| BiggerPockets forums | Manual monitoring of Palm Beach/Broward posts | Free |
| Facebook RE groups | Join local investor groups, monitor discussions | Free |
| LinkedIn activity | Search for "real estate investor" + location | Free |
| Meetup.com | Attend/monitor local REIA meetups | Free |
| Brand24 (social listening) | Keyword monitoring across platforms | $79–$399/mo |

**Important note:** Do NOT scrape these platforms. Engage organically. Monitor manually or use approved social listening tools.

### 5D. Intent Data Providers (Advanced)

| Provider | What It Does | Cost | Best For |
|----------|-------------|------|----------|
| Jornaya/Verisk | Detects mortgage shopping behavior 100+ days before credit triggers | Enterprise pricing | High-value lead identification |
| ATTOM Data | Property sale likelihood scoring | $95–$500/mo+ | Predicting which properties will transact |
| Homebot | Client-level intent signals for homeowners | Contact for pricing | Existing relationship nurturing |

---

## Phase 6: Wealth & Financial Strength Signals {#phase-6-wealth-signals}

### 6A. Free Public Data Sources

| Data Source | URL | What It Reveals | Cost |
|-------------|-----|-----------------|------|
| FEC Political Donations | api.open.fec.gov | Donor name, address, employer, occupation, amount | Free API |
| Florida DBPR Licenses | myfloridalicense.com | Professional licenses (RE agent, contractor, CPA, etc.) | Free (weekly bulk CSV) |
| FAA Aircraft Registry | registry.faa.gov | Aircraft owners by name/LLC with full address | Free (daily bulk CSV) |
| SEC EDGAR Form D | sec.gov/cgi-bin/browse-edgar | Syndication filings: issuer, officers, offering size | Free API |
| UCC Filings | floridaucc.com | Business debt/collateral, secured parties | Free search |
| Court Records (PBC) | appsgp.mypalmbeachclerk.com/eCaseView/ | Divorce, probate, civil suits | Free online |
| Court Records (Broward) | browardclerk.org | Divorce, probate, civil suits | Free (registered users for family/probate) |

**Important legal note on FEC data:** Donor data may NOT be used for commercial solicitation or sold. You can use it as an enrichment signal (e.g., to estimate net worth or identify high-value prospects), but you cannot cold-call someone solely because they donated to a political campaign.

### 6B. Boat Registration (FLHSMV)

Florida vessel registration data is available but owner PII is restricted. Individual lookups possible via FLHSMV portals using hull identification numbers. Bulk access requires formal public records request. Best used as a supplemental wealth indicator when you already have a prospect name.

### 6C. Life Event Signals

| Event | Public Record Source | DSCR Implication |
|-------|---------------------|------------------|
| Divorce filing | County Clerk of Court | Forced property division/sale/refi |
| Probate/estate | County Clerk of Court | Inherited properties need financing |
| Business dissolution | Sunbiz.org | Portfolio restructuring |
| Recent migration to FL | Mailing address change in appraiser records | Out-of-state investor entering market |
| Recent entity formation | Sunbiz (formation date) | New investor scaling up |

---

## Phase 7: Relationship Graph & Network Mapping {#phase-7-relationship-graph}

### 7A. Connections from Public Data

| Connection Type | How to Identify | Data Source |
|----------------|----------------|-------------|
| Co-owners | Multiple names on same deed | County Clerk |
| Business partners | Officers/members on same LLC | Sunbiz |
| Same registered agent | Shared agent across multiple LLCs | Sunbiz |
| Same lender | Same mortgage lender across properties | County Clerk |
| Same property manager | Rental listing data cross-reference | AirDNA/Mashvisor |
| Same RE agent | MLS transaction data | PropStream/ATTOM |
| Syndication partners | Co-signers on Form D filings | SEC EDGAR |
| Same meetup groups | Attendance at local REIA events | Manual/organic |

### 7B. Network Prospecting Strategy

When you close one investor, ask:
1. "Who else in your network invests in this area?"
2. "Who manages your properties?"
3. "Who referred you to your current lender?"

Cross-reference their LLC officer lists on Sunbiz — other officers on their entities are likely co-investors.

---

## Phase 8: Opportunity Scoring {#phase-8-opportunity-scoring}

### DSCR Opportunity Score Model

Build a composite score (0–100) using weighted variables:

| Variable | Weight | Scoring Logic |
|----------|--------|--------------|
| Portfolio size (3–50 properties) | 15% | 3–10 = 60pts, 10–50 = 100pts, 1–2 = 20pts, 50+ = 40pts |
| Estimated equity > 40% | 10% | >60% = 100pts, 40–60% = 70pts, 20–40% = 30pts |
| Hard money/bridge exposure | 15% | Any hard money = 100pts |
| Cash purchase in last 24 months | 10% | Yes = 100pts |
| Loan maturing within 24 months | 15% | <12 months = 100pts, 12–24 = 70pts |
| Interest rate above market | 10% | >1.5% above = 100pts, 0.5–1.5% = 50pts |
| Recent acquisition activity | 10% | Purchased in last 12 months = 100pts, 12–24 = 50pts |
| Absentee/out-of-state owner | 5% | Out-of-state = 100pts, absentee in-state = 50pts |
| Entity ownership | 5% | LLC/Corp = 100pts (indicates sophistication) |
| STR operator | 5% | Confirmed STR = 100pts (DSCR works well for STRs) |

**Score tiers:**
- 80–100: **Hot Lead** — multiple urgent signals, prioritize for immediate outreach
- 60–79: **Warm Lead** — strong fit, include in first wave campaigns
- 40–59: **Nurture** — good prospect, add to drip campaigns
- < 40: **Monitor** — not urgent, check quarterly for changes

---

## DNC/TCPA Compliance Framework {#compliance-framework}

### THIS IS NOT OPTIONAL. Violations carry $500–$1,500 per call/text penalties.

### Required Licenses & Registrations

| Requirement | Cost | Frequency |
|-------------|------|-----------|
| Florida Telemarketing Business License (FDACS) | $1,500/year | Annual |
| Florida Telemarketing Salesperson License | $50/year per person | Annual |
| Surety Bond | $50,000 face value (~$500–$1,500 premium) | Annual |
| FTC DNC Registry SAN (Subscription Account Number) | Free for first 5 area codes; $82/area code after | Annual |
| 10DLC SMS Campaign Registration | Varies by provider (~$4–$15/campaign) | One-time + monthly |
| Fingerprint/background check per salesperson | ~$50–$75 per person | Initial |

### Mandatory Pre-Outreach Steps

**Before every phone call:**
1. Scrub against Federal DNC registry (minimum every 31 days)
2. Scrub against Florida State DNC list (updated quarterly)
3. Verify phone line type (mobile vs. landline)
4. Check against known TCPA litigator lists
5. Maintain internal DNC/opt-out list
6. Verify calling hours: **8 AM – 8 PM local time** (Florida = two time zones: ET and CT)

**Before every text message:**
1. All phone scrubbing steps above, PLUS
2. Must have **prior express written consent** for any automated/bulk texting
3. Register through 10DLC Campaign Registry
4. Include opt-out instructions in every message

**Before every email:**
1. Include physical mailing address
2. Include clear unsubscribe mechanism
3. Honest subject line (no deception)
4. Honor opt-outs within 10 business days
5. No purchased email lists without verified opt-in consent

### Florida-Specific Rules (Stricter Than Federal)

| Rule | Florida Requirement |
|------|-------------------|
| Calling hours | 8 AM – 8 PM local time (federal is 8 AM – 9 PM) |
| Call frequency | Max 3 calls per 24 hours, same person, same subject |
| Caller ID | Must display accurate number — blocking/spoofing prohibited (criminal penalties) |
| Autodialer consent | Prior express written consent required even with existing business relationship |
| STOP reply (texts) | Consumer must reply STOP before they can sue (15-day safe harbor) |
| B2B calls | Florida calling hour, frequency, and caller ID rules ALSO apply to B2B |

### Critical New Law: Homebuyers Privacy Protection Act (HPPA)

**Effective March 5, 2026 (NOW)**

This law bans the purchase and use of mortgage trigger leads (credit bureau data showing someone is shopping for a mortgage) except in three narrow cases:
1. Consumer explicitly opted in
2. Existing lender/servicer relationship
3. Firm offer of credit (not general marketing)

**Impact on your operation:** You CANNOT purchase mortgage inquiry trigger leads. Your prospecting must be based on property records, public data, and opt-in channels — exactly what this strategy document describes.

### Record Retention Requirements

| Record Type | Retention Period |
|-------------|-----------------|
| Consent records | 6 years minimum |
| DNC scrub logs | 6 years minimum |
| Call/text logs | 6 years minimum |
| Opt-out records | 6 years minimum |
| Lead source documentation | 6 years minimum |

---

## Cost Summary & Build Timeline {#cost-summary}

### Phase-by-Phase Cost Breakdown

| Phase | Data Sources | Monthly Cost | One-Time Setup |
|-------|-------------|-------------|----------------|
| **1: Foundation** | FL DOR, Sunbiz, County Clerk, County Appraiser | $0–$50/mo | $0 (DIY) or $2K–$5K (developer) |
| **2: Contact Enrichment** | Skip tracing, email, phone validation, DNC | $568–$964/mo (5K records) | $200–$500 |
| **3: Financing Intelligence** | County records + ATTOM/BatchData | $0–$500/mo | Included in Phase 1 |
| **4: Rental/DSCR** | Rentometer + AirDNA/Mashvisor | $163–$324/mo | $0 |
| **5: Behavioral/Intent** | Public records + Brand24 | $0–$399/mo | $0 |
| **6: Wealth Signals** | FEC, FAA, DBPR, SEC, court records | $0/mo | $0 |
| **7: Network Mapping** | Derived from Sunbiz + county records | $0/mo | $0 |
| **8: Scoring** | Custom algorithm | $0/mo | Developer time |

### Compliance Costs

| Item | Annual Cost |
|------|------------|
| FL Telemarketing License | $1,500 |
| Salesperson licenses (assume 3) | $150 |
| Surety bond premium | $500–$1,500 |
| DNC registry subscription | $0–$500 |
| Background checks | $150–$225 |
| Compliance software/CRM | $0–$200/mo |
| **Total annual compliance** | **$2,300–$4,275** |

### Recommended Build Timeline

| Month | Focus | Milestone |
|-------|-------|-----------|
| Month 1 | Download and parse all free public data (FL DOR, Sunbiz, County records) | Investor Master List with 40K–60K records |
| Month 2 | Build database, cross-reference entities, identify portfolios | Portfolio Intelligence complete |
| Month 3 | Skip trace first 5,000 highest-value prospects, DNC scrub | First outreach-ready leads |
| Month 4 | Add financing intelligence layer (mortgage matching) | Opportunity signals active |
| Month 5 | Add rent estimation and DSCR scoring | Full scoring model live |
| Month 6 | Launch outreach campaigns, begin optimization | First DSCR deals closing |

---

## Data Architecture Recommendation {#data-architecture}

### For a Non-Developer (Vibe Coder) Approach

**Option A: PropStream + CRM (Simplest)**
- PropStream ($99/mo) handles property data, skip tracing, and list building in one platform
- Export to a CRM (HubSpot free tier, GoHighLevel, or Follow Up Boss)
- Manual enrichment from free public sources as needed
- Total: ~$99–$200/month

**Option B: Google Sheets + Zapier + APIs (Low-Code)**
- Download public data into Google Sheets or Airtable
- Use Zapier/Make to connect skip tracing APIs
- Build scoring formulas in spreadsheets
- Total: ~$200–$500/month

**Option C: PostgreSQL Database + Python Scripts (Technical)**
- Store all data in PostgreSQL
- Python scripts for data ingestion, matching, and scoring
- Dashboard via Metabase (free/open-source) or Retool
- Total: ~$50–$200/month (mostly API costs)
- Requires: Developer help for initial setup ($2K–$5K)

**Recommendation for Zack:** Start with Option A (PropStream + CRM) to prove the concept and close deals. Graduate to Option B or C when volume justifies the investment. The free public data sources can supplement PropStream to fill gaps it doesn't cover (Sunbiz entity data, FAA records, FEC donations, SEC filings, court records).

---

## The Ultimate DSCR Lead Record (Target Schema)

When your system is fully built, each prospect record should contain:

```
=== CONTACT ===
Investor Name:
Primary Entity (LLC):
Phone (mobile):
Phone (secondary):
Email (personal):
Email (business):
LinkedIn:
Mailing Address:

=== PORTFOLIO ===
Property Count:
Total Estimated Value:
Total Estimated Debt:
Total Estimated Equity:
Estimated Portfolio DSCR:
Property Type Mix: [SFR: X, MF: X, STR: X]
Primary Markets:

=== FINANCING ===
Number of Active Loans:
Lenders: [list]
Average Estimated Interest Rate:
Loans Maturing Within 24 Months:
Hard Money Exposure: [Yes/No, count]
Cash Purchases (last 24 mo):

=== ACQUISITION BEHAVIOR ===
Purchases Last 12 Months:
Purchases Last 36 Months:
Average Purchase Price:
Last Purchase Date:
Scaling Trajectory: [Accelerating/Steady/Paused]

=== OPPORTUNITY SIGNALS ===
Refinance Opportunities: [count]
Recent Cash Purchases: [count]
Hard Money Loans: [count]
Balloon Maturities: [count]
Above-Market Rates: [count]
High Equity Properties: [count]

=== NETWORK ===
Property Managers Used:
RE Agents Used:
Known Co-Investors:
Shared Entities:

=== COMPLIANCE ===
DNC Status: [Clear/On List]
Phone Type: [Mobile/Landline/VoIP]
Last DNC Scrub Date:
Consent Status:
Opt-Out Status:

=== SCORING ===
DSCR Opportunity Score: [0-100]
Score Tier: [Hot/Warm/Nurture/Monitor]
Last Score Date:
Priority Outreach Channel: [Phone/Email/LinkedIn/Mail]
```

---

## Key Takeaways

1. **60–70% of the data you need is completely free** from Florida public records (FL DOR, Sunbiz, County Clerk, County Appraiser, DBPR, FEC, FAA, SEC).

2. **The biggest expense is skip tracing** (phone + email enrichment), which runs $0.02–$0.15 per record depending on volume.

3. **DNC/TCPA compliance is non-negotiable.** Budget $2,300–$4,275/year for licenses, bonds, and scrubbing. The Florida Telemarketing License alone is $1,500/year.

4. **Start with PropStream + free public data** for the fastest path to deals. Graduate to a custom database as you scale.

5. **The HPPA (effective March 2026) makes this approach even more valuable** — you can't buy trigger leads anymore, so building your own intelligence from public records is now the competitive advantage.

6. **Every data point in the dream enrichment model has a solution.** Some are free, some cost money, but none are impossible. The data exists — you just have to connect the dots.

---

*Document generated March 2026. Data sources, pricing, and regulations should be verified before implementation as they may change.*
