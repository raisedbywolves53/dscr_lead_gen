# Enrichment Data Vendor Research
## Contact Discovery, Property Intelligence & Verification Services
### Prepared for: Frank Christiano / CCM Team | February 28, 2026

---

# TABLE OF CONTENTS

1. [Executive Summary](#1-executive-summary)
2. [Skip Tracing Services (Phone + Email)](#2-skip-tracing-services)
3. [B2B Contact Enrichment (Email, LinkedIn, Business Intel)](#3-b2b-contact-enrichment)
4. [Real Estate-Specific Data Providers](#4-real-estate-specific-data-providers)
5. [Phone & Email Verification](#5-phone--email-verification)
6. [Social & Professional Enrichment](#6-social--professional-enrichment)
7. [Waterfall Enrichment Platforms](#7-waterfall-enrichment-platforms)
8. [Expected Hit Rates by Lead Segment](#8-expected-hit-rates-by-lead-segment)
9. [Recommended Stack & Cost Modeling](#9-recommended-stack--cost-modeling)
10. [Integration Architecture](#10-integration-architecture)

---

# 1. EXECUTIVE SUMMARY

## The Problem

Our pipeline currently produces 189K+ investor leads from FDOR data with 0% contact enrichment coverage. People search sites (TruePeopleSearch, FastPeopleSearch) block automated requests. Without phone numbers and emails, leads are not actionable for outreach.

## The Opportunity

The commercial data enrichment ecosystem can deliver:

| Data Point | Achievable Coverage | Best Source | Cost Per Record |
|-----------|-------------------|-------------|-----------------|
| Mobile phone | 70-80% | Skip tracing (BatchData) | $0.20/match |
| Landline phone | 85-90% | Skip tracing | included |
| Personal email | 60-70% | Skip tracing + waterfall | $0.15-0.20 |
| Business email | 30-50% (individuals), 70%+ (fund mgrs) | Apollo/Lusha | $0.05-0.50 |
| LinkedIn profile | 15-60% (varies by segment) | Apollo/RocketReach | $0.30-0.50 |
| Mortgage balance | 95%+ | ATTOM/ListSource | $0.03-0.50 |
| Actual equity (AVM) | 95%+ | ATTOM | $0.10-0.50 |
| Phone line type | 99% | Twilio Lookup | $0.008 |
| Email validity | 99% | NeverBounce | $0.003 |

## Key Insight: Waterfall Enrichment

No single provider exceeds 60-70% contact coverage. The winning strategy is sequential waterfall:

1. BatchData skip trace ($0.20/match) → 70-80% hit rate
2. Apollo.io for unmatched entities ($0.05/credit) → +10-15%
3. Clay waterfall for remaining high-value leads ($0.01/credit) → +5-10%
4. Twilio phone validation ($0.008) + NeverBounce email verify ($0.003)

**Combined achievable coverage: 80-85% with at least phone OR email.**

---

# 2. SKIP TRACING SERVICES

Skip tracing is the single most impactful enrichment category for RE investor leads. These services are purpose-built for finding contact info for property owners.

## BatchData (formerly BatchSkipTracing) — RECOMMENDED

- **Database**: 325M+ records, 99% US population coverage
- **Returns**: Up to 3 phone numbers + 3 email addresses per record
- **Match rate**: 90-95% data return rate; ~70-80% contactable rate
- **Pricing**:
  - Free membership (no subscription required)
  - $0.20 per match (pay-per-match — no charge if no data found)
  - Bulk processing supported
- **API**: Yes — full REST API for skip tracing, property data, and phone validation
- **Why recommended**: Pay-per-match eliminates waste. API enables direct pipeline integration. RE-specific database optimized for property owner records. Most established skip trace vendor in the RE investor space.

**Cost estimate for pipeline:**
- 5K top leads (score 70+): ~$1,000
- 35K actionable leads (score 50+): ~$7,000
- Full 189K pipeline: ~$37,800

## REISkip

- **Match rate**: 85-90% (proprietary "Skip Trace Triangulation Technology")
- **Pricing**: Flat $0.15/record regardless of volume. No charge for duplicates. No subscription.
- **API**: Not documented — likely manual upload/download only
- **Tradeoffs**: Cheaper per-record ($0.15 vs $0.20) but no API integration. Good budget option for manual enrichment runs.

## SkipForce

- **Match rate**: Not publicly disclosed
- **Pricing**: $49/month subscription + $0.06/match (cheapest per-match rate)
- **API**: Not documented
- **Tradeoffs**: Cheapest at volume (break-even vs REISkip at ~545 records/month). Requires subscription commitment.

## PropStream Skip Tracing

- **Match rate**: ~60-80%
- **Pricing**: FREE with PropStream subscription plans (Essentials/Pro/Elite, starting ~$99/month). 25,000 exports/month.
- **API**: No — manual export only
- **Tradeoffs**: Free skip tracing is compelling if also using PropStream for property data. Lower accuracy than dedicated skip trace vendors. No API means manual workflow.

### Skip Tracing Comparison

| Provider | Cost/Record | API | Match Rate | Subscription |
|----------|------------|-----|-----------|-------------|
| **BatchData** | $0.20/match | Yes | 70-80% contactable | None |
| REISkip | $0.15/record | No | 85-90% return | None |
| SkipForce | $0.06/match | No | Unknown | $49/month |
| PropStream | Free w/sub | No | 60-80% | ~$99/month |

---

# 3. B2B CONTACT ENRICHMENT

These providers excel at finding business emails, direct dials, and LinkedIn profiles for professionals. Best for: fund managers, corporate entity officers, syndicators, HNWIs with business profiles.

## Apollo.io — RECOMMENDED (Free Tier)

- **Database**: 210M+ contacts
- **Data points**: Business email, mobile phone, company info, job title, LinkedIn URL, technographics, intent signals
- **Match rate**: 65-80% for business emails; phone numbers often missing for non-corporate contacts. User-reported email bounce rates up to 35%.
- **Pricing**:
  - Free: 100 credits/month (5 mobile, 10 export)
  - Basic: $49/user/month (annual) — 5,000 credits, 75 mobile, 1,000 export
  - Professional: $79/user/month (annual) — 10,000 credits, 100 mobile, 2,000 export
  - Organization: $119/user/month (annual) — 15,000 credits, 200 mobile, 4,000 export
  - Credits: email reveal = 1 credit; mobile = 5-8 credits
- **API**: Full REST API on all paid plans. Enrichment costs 1-9 credits per record.
- **Best for our pipeline**: Fund Manager/Syndicator segment, SunBiz-resolved entity officers, corporate entity contacts. Already referenced in pipeline code — just needs API key.

## Lusha

- **Database**: Not disclosed (quality over quantity positioning)
- **Data points**: Direct dial phone, mobile, business email, personal email, company info, job title, LinkedIn
- **Match rate**: 95%+ email accuracy claimed; confidence scoring per record
- **Pricing**:
  - Free: 40 credits/month
  - Pro: $22.45/user/month (annual) — 250 credits
  - Premium: $52.45/user/month (annual) — 600 credits
  - Scale: Custom pricing (5+ users)
  - 1 credit = 1 contact reveal (email + phone)
- **API**: Full enrichment API with bulk processing
- **Best for**: LLC/entity officers who have LinkedIn presence. Good complement to skip tracing for professional contacts.

## RocketReach

- **Data points**: Personal email, business email, phone, social profiles (LinkedIn, Twitter, Facebook), company info
- **Pricing**:
  - Essentials: $74/month (annual) — email only
  - Pro: $149/month (annual) — email + phone
  - Ultimate: $249/month (annual) — includes API, 10,000 exports/year
  - API lookups: $0.30-$0.45 per lookup
- **Best for**: Finding personal emails and social profiles. Better than Apollo for individual investors since it includes personal email search.

## ZoomInfo

- **Database**: Enterprise-grade, industry-leading for B2B
- **Data points**: Business email, direct dial, mobile, org charts, intent signals, technographics
- **Match rate**: 95%+ for business emails
- **Pricing**: Starts at ~$15,000/year minimum. Typical: $25,000/year. API: ~$50,000/year.
- **Verdict**: Overkill and overpriced for this use case. Individual RE investors have very low match rates in ZoomInfo's database. Not recommended unless already subscribed.

## Cognism

- **Standout feature**: Phone-verified mobile numbers (highest rated in industry)
- **Pricing**: Custom/enterprise only. Estimated $15,000-$30,000+/year.
- **Verdict**: Premium pricing not justified. Phone-verified mobiles are valuable but BatchData skip tracing achieves similar coverage at a fraction of the cost.

## Seamless.AI

- **Pricing**: Basic $147/month; Pro requires 5+ users
- **Verdict**: Not recommended. Credits expire monthly, minimum user requirements, and not designed for RE investor enrichment.

## UpLead

- **Standout feature**: Real-time email verification at point of reveal (95% accuracy)
- **Database**: 155M+ contacts
- **Pricing**: Essentials $99/month — 170 credits; Plus $199/month — 400 credits
- **Verdict**: Good email accuracy but primarily B2B-focused. Better value than ZoomInfo for smaller teams.

## Clearbit (Now Breeze Intelligence / HubSpot)

- **Pricing**: Requires HubSpot ($30+/month) + Breeze Intelligence ($45/month for 100 credits)
- **Verdict**: Not recommended. Company-focused enrichment, not individual contacts. No property data.

### B2B Provider Comparison

| Provider | Monthly Cost | Credits/Month | Best Segment | API |
|----------|-------------|--------------|-------------|-----|
| **Apollo.io** | Free-$119 | 100-15,000 | Fund mgrs, entity officers | Yes |
| Lusha | Free-$52 | 40-600 | Entity officers w/ LinkedIn | Yes |
| RocketReach | $74-$249 | Varies | Personal email discovery | Yes (Ultimate) |
| UpLead | $99-$199 | 170-400 | B2B with verified email | Yes (Pro) |
| ZoomInfo | $15,000+/yr | N/A | Enterprise B2B | Yes |
| Cognism | $15,000+/yr | Unlimited | Phone-verified mobiles | Yes |

---

# 4. REAL ESTATE-SPECIFIC DATA PROVIDERS

These fill gaps in our FDOR data — particularly mortgage balances, AVM, and enhanced property attributes.

## ATTOM Data — RECOMMENDED

- **Coverage**: 158M+ US properties, 9,000+ discrete attributes
- **Data points**: Tax records, deed/mortgage records, foreclosure filings, AVM (automated valuation), sale history, property characteristics, climate/hazard risk, neighborhood demographics
- **Match rate**: 99%+ US parcel coverage
- **Pricing**:
  - API starter: $95/month (developer tier)
  - Enterprise: $10,000-$50,000+/year (custom)
  - 30-day free API trial available
- **API**: Comprehensive REST API (JSON/XML). Well-documented developer platform.
- **Why recommended**: Fixes our biggest data gap — actual mortgage balances. Currently equity ratios are estimated from JV vs sale price with no mortgage data. ATTOM provides real mortgage records, making refi detection dramatically more accurate. $95/month starter tier is accessible.

**Key data gaps ATTOM fills:**
- Actual mortgage balance → accurate equity calculation
- AVM → current market value (better than FDOR JV which lags)
- Mortgage origination date and rate → true rate refi candidate detection
- Foreclosure/pre-foreclosure status → distressed property identification
- Permit history → renovation activity (BRRRR confirmation)

## ListSource (CoreLogic)

- **Coverage**: 134M+ properties (CoreLogic's consumer-facing list builder)
- **Data points**: Property details, owner name, mailing address, mortgage info, demographic overlays, equity estimates, absentee owner flag
- **Match rate**: 94% homeowner coverage
- **Pricing**:
  - Pay-per-lead: ~$0.03-$0.31/record depending on filters/attributes
  - No subscription required (build and buy)
  - Bulk pricing available
- **API**: No — web-based list builder only
- **Best for**: Supplementing FDOR data with mortgage info and demographic overlays. Economical at $0.03/record for basic property lists.

## PropStream

- **Coverage**: 153M+ US properties
- **Data points**: Owner info, property details, tax records, mortgage data, liens, foreclosure status, estimated equity, sale history, comps, MLS data, owner mailing address, built-in skip tracing
- **Pricing**:
  - Tiered plans starting ~$99/month (Essentials, Pro, Elite)
  - 25,000 exports/month on all plans
  - Skip tracing included free on select plans
- **API**: No public API
- **Verdict**: Most feature-complete single tool for RE investor research. The combination of property data + free skip tracing is compelling. Limitation: no API means manual workflow, not pipeline-integratable.

## BatchLeads (PropStream subsidiary)

- **Coverage**: Same data as PropStream (acquired July 2025)
- **Pricing**: $119-$749/month (tiered). Skip tracing and direct mail additional.
- **Verdict**: Duplicative with PropStream. May consolidate over time.

## CoreLogic (Direct)

- **Coverage**: 200+ data sources, industry-leading
- **Pricing**: Enterprise-only, $25,000-$100,000+/year
- **Verdict**: Best data quality but enterprise pricing. Use ListSource (their consumer product) instead.

## Reonomy

- **Focus**: Commercial real estate
- **Pricing**: ~$400/month per user
- **Verdict**: Not relevant — our pipeline targets residential investment properties.

## Cherre

- **Focus**: Enterprise data aggregation platform
- **Pricing**: Custom enterprise
- **Verdict**: Institutional-grade, beyond our scope.

### RE Data Provider Comparison

| Provider | Property Coverage | Mortgage Data | AVM | API | Monthly Cost |
|----------|------------------|---------------|-----|-----|-------------|
| **ATTOM** | 158M | Yes | Yes | Yes | $95+ |
| ListSource | 134M | Yes | Partial | No | $0.03-0.31/record |
| PropStream | 153M | Yes | Yes | No | ~$99 |
| CoreLogic | 200+ sources | Yes | Yes | Enterprise | $25K+/yr |

---

# 5. PHONE & EMAIL VERIFICATION

After enrichment, verification prevents wasted outreach on bad data. Essential before calling or emailing.

## Twilio Lookup API — RECOMMENDED (Phone)

- **Data points**: Phone formatting, carrier name, line type (mobile/landline/VoIP), caller name (CNAM), identity match, line status, reassigned number detection, SIM swap detection
- **Pricing**:
  - Basic formatting/validation: FREE
  - Line Type Intelligence: $0.008/request
  - Caller Name (CNAM): $0.01/request
  - Identity Match: $0.10/request
  - Pay-as-you-go, no subscription
- **API**: Comprehensive REST API (Lookup v2)
- **Why essential**: Line type detection ($0.008) confirms mobile vs landline vs VoIP — critical for SMS/text outreach compliance (TCPA). Caller name provides identity verification. Very cost-effective.

**Cost for pipeline:**
- 5K top leads: $40
- 35K actionable leads: $280
- 189K full pipeline: $1,514

## NeverBounce — RECOMMENDED (Email)

- **Data points**: Email validity (valid/invalid/catch-all/unknown), deliverability score
- **Guarantee**: 99.9% delivery rate on verified emails
- **Pricing**:
  - 1,000 emails: $8 ($0.008/email)
  - 10,000 emails: $50 ($0.005/email)
  - Subscription: $29/month for 10K ($0.0029/email)
- **API**: Real-time single verification and bulk batch API
- **Why essential**: At $0.003-0.008/email, trivial cost to prevent bounces that damage sender reputation.

## ZeroBounce (Email Alternative)

- **Data points**: Email validity, spam trap detection, catch-all detection, gender detection, activity score
- **Pricing**: Free 100/month; 10,000 emails: $75 ($0.0075/email)
- **Extra features**: Email activity scoring, gender detection — useful for personalization

## NumVerify (Phone Alternative)

- **Data points**: Phone validation, carrier, line type, location
- **Pricing**: Free 100/month; paid from $9.99/month
- **Verdict**: Cheaper than Twilio for basic validation but fewer features. No CNAM, no identity match.

---

# 6. SOCIAL & PROFESSIONAL ENRICHMENT

## LinkedIn Sales Navigator

- **Data points**: Professional profile, job title, company, connections, activity. No direct email/phone export.
- **Pricing**:
  - Core: $99.99/month ($79.99/month annual)
  - Advanced: $179.99/month
  - Advanced Plus: ~$1,600/seat/year
  - 50 InMails/month included
- **API**: No data export. LinkedIn prohibits scraping. Third-party tools (Evaboot, PhantomBuster) extract data but violate TOS.
- **Coverage by segment**:
  - Fund managers/syndicators: 70%+ have LinkedIn profiles
  - LLC/entity officers: 40-60%
  - Individual FL property investors: 15-25%
  - Foreign nationals (Canadian): 30-40%
  - HNWIs: 50-60%
- **Best use**: Manual research on top 100 leads. Not scalable for pipeline integration.

## Pipl

- **Data points**: Identity resolution across 3B+ profiles — email, phone, social profiles, address history, employment, education
- **Pricing**: Enterprise-only ($10,000-$50,000+/year)
- **API**: Full identity resolution API
- **Best for**: Cross-border identity resolution (Canadian/foreign national leads). Strong at connecting fragmented data points. Expensive but powerful for the foreign national segment.

## BeenVerified / Spokeo / WhitePages

- **Data points**: Name, address, phone, email, social profiles, relatives, property records
- **Pricing**: $15-33/month consumer subscriptions
- **API**: WhitePages has Pro API ($0.05-0.50/lookup); others consumer-only
- **Verdict**: Consumer-grade, not scalable. No commercial API except WhitePages Pro. Useful for manual spot-checking of high-value leads only.

---

# 7. WATERFALL ENRICHMENT PLATFORMS

These orchestrate multiple data providers in sequence, dramatically improving coverage.

## Clay — RECOMMENDED (If Budget Allows)

- **How it works**: Connects 100+ data providers. Runs sequential "waterfall" enrichment — tries cheapest source first, passes failures to next source automatically.
- **Match rate**: 80%+ contact discovery via waterfall (vs 40-50% single source)
- **Pricing**:
  - Starter: $134/month (annual) — 24,000 credits/year
  - Explorer: $314/month (annual)
  - Pro: $720/month (annual)
  - Enterprise: $30,000-$154,000/year
  - Per-credit cost: $0.008-0.012 at enterprise scale
- **API**: Full API and webhook support
- **Best for**: Building a production enrichment pipeline that queries multiple sources automatically. Could replace the entire enrichment module with a single integration.

## BetterContact

- **How it works**: Email and phone waterfall across 20+ providers
- **Match rate**: ~85% email match rate
- **Pricing**: Credit-based, tiered (1K-50K credits/month)
- **Best for**: Simpler than Clay, pure contact enrichment focus

## FullEnrich

- **How it works**: Waterfall across 20+ providers (Datagma, Wiza, Hunter, PeopleDataLabs, etc.)
- **Match rate**: 91% email, 71% phone (independent benchmarks — highest tested)
- **Pricing**: ~$0.05/credit
- **Tradeoffs**: Highest match rates but most expensive per-record

---

# 8. EXPECTED HIT RATES BY LEAD SEGMENT

Based on provider capabilities and our specific lead types:

## Phone Number Discovery

| Lead Segment | Skip Trace | B2B Provider | Combined Est. |
|-------------|-----------|-------------|--------------|
| Serial Investor (10+) | 75% | 40% | 80-85% |
| Entity-Based (LLC/Trust) | 65% (via resolved person) | 35% | 75% |
| Individual Investor (2-9) | 80% | 20% | 82% |
| Foreign National | 30-40% | 15% | 40-50% |
| Fund Manager / Syndicator | 50% | 65% | 75% |
| Out-of-State Investor | 75% | 25% | 78% |
| Single Investment Property | 80% | 15% | 80% |

## Email Discovery

| Lead Segment | Skip Trace | B2B Provider | Combined Est. |
|-------------|-----------|-------------|--------------|
| Serial Investor (10+) | 60% | 45% | 70% |
| Entity-Based (LLC/Trust) | 50% | 40% | 65% |
| Individual Investor (2-9) | 65% | 20% | 68% |
| Foreign National | 20-30% | 15% | 30-40% |
| Fund Manager / Syndicator | 40% | 70% | 75% |
| Out-of-State Investor | 60% | 25% | 65% |
| Single Investment Property | 65% | 15% | 66% |

## LinkedIn Profile Discovery

| Lead Segment | Apollo/RocketReach | Sales Navigator | Est. Coverage |
|-------------|-------------------|----------------|--------------|
| Serial Investor (10+) | 35% | +10% | 40-45% |
| Entity-Based (LLC/Trust) | 40% | +15% | 50-55% |
| Individual Investor (2-9) | 15% | +5% | 15-20% |
| Foreign National | 25% | +10% | 30-35% |
| Fund Manager / Syndicator | 65% | +15% | 70-80% |
| Out-of-State Investor | 20% | +5% | 20-25% |

**Key insight**: Foreign nationals have the lowest enrichment coverage across all channels. Canadian investors are better than other foreign nationals, but still significantly below domestic leads. Pipl ($10K+/year) is the only service with strong cross-border identity resolution.

---

# 9. RECOMMENDED STACK & COST MODELING

## Tier 1: Immediate Integration (Best ROI)

These three services provide the highest impact per dollar:

| Service | Purpose | Cost Model | Pipeline Integration |
|---------|---------|-----------|---------------------|
| **BatchData** | Bulk skip tracing (phone + email) | $0.20/match | API → `05_enrich_contacts.py` |
| **Twilio Lookup** | Phone validation (line type, CNAM) | $0.008/request | API → post-enrichment step |
| **NeverBounce** | Email verification | $0.003/email | API → post-enrichment step |

### Cost by Volume

| Lead Volume | BatchData | Twilio | NeverBounce | **Total** |
|-------------|-----------|--------|-------------|-----------|
| 50 (sample) | $10 | $0.40 | $0.15 | **$10.55** |
| 5,000 (score 70+) | $1,000 | $40 | $15 | **$1,055** |
| 35,000 (score 50+) | $7,000 | $280 | $105 | **$7,385** |
| 189,000 (full) | $37,800 | $1,514 | $567 | **$39,881** |

**Expected outcome**: 70-80% of leads with phone or email. ~$0.21/lead all-in.

## Tier 2: Supplemental Enrichment

Add these for higher-value segments:

| Service | Purpose | Cost | Target Segments |
|---------|---------|------|-----------------|
| **ATTOM API** | Mortgage data, AVM, accurate equity | $95-500/month | All leads (improves refi detection) |
| **Apollo.io** | Business email for professionals | Free-$49/month | Fund managers, entity officers |
| **Clay** | Waterfall for skip-trace misses | $134/month | High-value leads missed by BatchData |

### Tier 2 Monthly Cost: $229-$683/month

## Tier 3: Premium Enhancement

| Service | Purpose | Cost | When to Add |
|---------|---------|------|-------------|
| Lusha | Entity officer direct dials | $22-52/month | SunBiz-resolved entities need phone |
| LinkedIn Sales Nav | Fund manager/HNWI outreach | $80-180/month | Targeting institutional investors |
| Pipl | Foreign national identity resolution | $10K+/year | Canadian buyer segment prioritized |
| PropStream | Property data + free skip trace | ~$99/month | Manual enrichment workflow acceptable |
| ListSource | Supplemental property lists | $0.03-0.31/record | New market expansion |

## Full Stack Annual Cost Estimate

| Configuration | Annual Cost | Expected Contact Rate |
|--------------|------------|----------------------|
| **Minimum viable** (BatchData + Twilio + NeverBounce) | ~$1,100/year for 5K leads | 70-80% |
| **Recommended** (above + ATTOM + Apollo free) | ~$2,300/year for 5K leads | 80-85% |
| **Full stack** (all Tier 1-2) | ~$11,000/year for 35K leads | 85%+ |
| **Maximum** (all tiers, full pipeline) | ~$55,000/year for 189K leads | 85-90% |

---

# 10. INTEGRATION ARCHITECTURE

## Current Pipeline (Free Only)

```
FDOR → Refi Detection → SunBiz → DBPR → EDGAR → [People Search - BLOCKED] → Scoring
                                                         ↓
                                                   0% contact rate
```

## Proposed Pipeline (With Enrichment Stack)

```
FDOR → Refi Detection → SunBiz → DBPR → EDGAR → BatchData Skip Trace
                                                         ↓
                                                   70-80% phone/email
                                                         ↓
                                              Apollo.io (entity officers)
                                                         ↓
                                              Twilio phone validation
                                                         ↓
                                              NeverBounce email verification
                                                         ↓
                                                   ICP Scoring → Excel
```

## Optional ATTOM Enhancement

```
FDOR data ──────────────┐
                        ↓
              ATTOM API enrichment
              (mortgage balance, AVM)
                        ↓
              Improved equity calculation
              Improved refi detection
                        ↓
              Rest of pipeline...
```

## API Integration Points

### BatchData (05_enrich_contacts.py)
```
POST https://api.batchdata.com/api/v1/skip-trace
Headers: Authorization: Bearer {API_KEY}
Body: { "requests": [{ "name": { "first": "John", "last": "Doe" }, "address": { "street": "123 Main St", "city": "Boca Raton", "state": "FL" } }] }
Returns: phone_numbers[], email_addresses[]
```

### Twilio Lookup (new validation step)
```
GET https://lookups.twilio.com/v2/PhoneNumbers/{phone}?Fields=line_type_intelligence
Returns: line_type (mobile/landline/voip), carrier_name
```

### NeverBounce (new validation step)
```
POST https://api.neverbounce.com/v4/single/check
Body: { "key": "{API_KEY}", "email": "test@example.com" }
Returns: result (valid/invalid/catch-all/unknown)
```

### Apollo.io (existing reference in pipeline)
```
POST https://api.apollo.io/v1/people/match
Body: { "api_key": "{KEY}", "first_name": "John", "last_name": "Doe" }
Returns: email, title, company, linkedin_url
```

### ATTOM Property API
```
GET https://api.gateway.attomdata.com/propertyapi/v1.0.0/property/detail?address1={addr}&address2={city,state,zip}
Returns: mortgage_amount, mortgage_date, mortgage_rate, avm_value, owner_info
```

---

# APPENDIX: FOREIGN NATIONAL ENRICHMENT

The foreign national segment (8,892 leads in Palm Beach alone) is our highest-value ICP for DSCR but also the hardest to enrich.

## Challenges
- US skip tracing databases have limited coverage of foreign nationals
- Canadian property owners may use Canadian phone numbers, addresses, and email providers
- LinkedIn coverage is moderate (~30-40%) for Canadian professionals investing in FL
- No single provider specializes in cross-border RE investor enrichment

## Best Available Approach
1. **BatchData skip trace**: Will find US-based contact info if they have any US presence (~30-40% hit rate for foreign nationals)
2. **Pipl identity resolution**: Cross-references international databases. Best for connecting Canadian business profiles to FL property ownership ($10K+/year)
3. **Apollo.io**: May find business email for Canadian professionals/business owners (~15-20% hit rate)
4. **FDOR mailing address**: Already captured. Canadian addresses can be used for direct mail campaigns — 100% coverage since FDOR has the mailing address
5. **Partnership approach**: Canadian real estate associations, immigration advisors, and cross-border tax firms are better referral channels than data enrichment for this segment

## Realistic Foreign National Coverage

| Channel | Coverage | Method |
|---------|----------|--------|
| Direct mail | 100% | FDOR mailing address (already in pipeline) |
| Phone (any) | 30-40% | Skip trace + Pipl |
| Email | 20-30% | Skip trace + Apollo |
| LinkedIn | 30-40% | Apollo + Sales Navigator |

**Recommendation**: For the 5 ultra-high-value Canadian leads in our sample ($38M-$72M properties), manual research + LinkedIn InMail is more effective than automated enrichment.
