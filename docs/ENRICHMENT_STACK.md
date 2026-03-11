# Enrichment Stack — Vendors, APIs & Data Sources

## Vendor Verdicts (Tested March 2026)

### Recommended

| Vendor | Role | Cost | Verdict | Notes |
|--------|------|------|---------|-------|
| **Tracerfy** | Primary skip trace | $0.02/match | **USE THIS** | Charges per MATCH not per upload. No minimums. 45% match rate. |
| **MillionVerifier** | Email validation | $4.90/2K credits | **USE THIS** | Credits never expire. API included. |
| **Twilio Lookup v2** | Phone type detection | $0.008/lookup | **USE THIS** | Must use v2 API (v1 returns no data on free trial). $15 trial = ~1,875 lookups. |
| **FTC DNC Registry** | Federal DNC list | Free (first 5 area codes) | **USE THIS** | Must scrub every 31 days. |

### Avoid

| Vendor | Role | Cost | Verdict | Notes |
|--------|------|------|---------|-------|
| **Apollo.io** | B2B enrichment | $99/mo | **CANCEL** | Returns near-zero contact data for LLC-based RE investors. 8 emails out of 500 leads. Wrong population. |
| **Datazapp** | Batch skip trace | $125 minimum/transaction | **AVOID** | $125 minimum regardless of match count. 25 leads = $125 = $17.86/match. Only use if 2,000+ leads. |

### Optional

| Vendor | Role | Cost | When To Use |
|--------|------|------|------------|
| **Tracerfy DNC** | Comprehensive DNC scrub | $0.02/phone | Covers Federal + State + DMA + TCPA litigators. Better than FTC-only. |
| **ATTOM** | Property + mortgage data | $95-500/mo | When you need actual lender names/loan amounts beyond clerk records. 133/500 match rate in our test. |
| **Datazapp** | Second-pass skip trace | $125 minimum | For Tracerfy misses only, when you have 2,000+ unmatched leads. |

---

## Data Sources by Category

### Property Records (State-Specific, Usually Free)

| Source | What It Provides | Cost |
|--------|-----------------|------|
| State property tax rolls | Ownership, values, addresses, use codes, homestead, sale history | Free (most states) |
| State sales data files | Full purchase/sale history, deed types, transaction prices | Free |
| County property appraiser | Building characteristics (beds, baths, sqft, year built) | Free |
| County GIS | Parcel boundaries, spatial data | Free |

### Entity Resolution (State-Specific, Usually Free)

| Source | What It Provides | Cost |
|--------|-----------------|------|
| Secretary of State business registry | LLC officers, registered agents, filing dates, entity status | Free |
| SEC EDGAR | Fund managers, Form D filings, syndication partners | Free (10 req/sec) |

### Financing Intelligence (Varies by County)

| Source | What It Provides | Cost |
|--------|-----------------|------|
| County Clerk / Register of Deeds | Mortgages, liens, lis pendens, satisfactions, deeds | Free to $600/yr |
| ATTOM API | Lender name, loan amount, rate type, due date | $95-500/mo |
| CoreLogic / Black Knight | Most comprehensive mortgage data | Enterprise pricing |

### Contact Enrichment

| Source | What It Provides | Cost | Rate Limit |
|--------|-----------------|------|-----------|
| Tracerfy | Up to 8 phones + 5 emails per lead, mailing address | $0.02/match | 10 POST/5 min |
| MillionVerifier | Email validity (ok/invalid/catch-all/disposable) | $0.00245/email | Fast |
| Twilio Lookup v2 | Phone type (mobile/landline/VoIP), carrier | $0.008/lookup | 100 req/sec |

### Wealth & Life Event Signals (Nationwide, Free)

| Source | What It Provides | Cost | Rate Limit |
|--------|-----------------|------|-----------|
| FEC.gov API | Political donation records | Free | 1,000 req/hr |
| ProPublica Nonprofit Explorer | IRS 990 filings, foundation donations | Free | Reasonable |
| HUD Fair Market Rents | Rent estimates by zip + bedroom count | Free | Bulk download |

### STR / Rental (State-Specific)

| Source | What It Provides | Cost |
|--------|-----------------|------|
| State licensing agency | Vacation rental licenses, PM licenses, phone/email | Free (varies by state) |
| AirDNA | STR revenue, ADR, occupancy data | $500+/mo |
| Rental listing sites | Active listings, PM company, asking rent | Free (scraping) |

---

## Critical Gotchas (Learned the Hard Way)

### Tracerfy
- **Charges per MATCH, not per upload.** Unmatched leads cost $0. Original estimate was $150; actual cost for 7,537 leads was $57.60.
- Processing time: ~24 minutes for 7,500 records
- Max 10 POST requests per 5 minutes
- API returns async results — poll for completion

### Datazapp
- **$125 MINIMUM per transaction.** Not per-match as their site implies.
- We loaded $75, couldn't even run a single batch. Lost $75.
- Never use for small runs. Only for 2,000+ leads as a Tracerfy second-pass.

### Apollo.io
- Returns near-zero contact data for private RE investors through LLCs.
- 17/17 name matches but 0 contact data returned.
- It's a B2B tool — RE investors don't have LinkedIn/company profiles.
- **Verdict: Cancel the $99/mo subscription.**

### MillionVerifier
- If credits run out mid-run, API returns error responses that **look like "invalid" results**.
- Script must check for "Insufficient credits" error specifically.
- 2,000 credits for $4.90 is the minimum purchase.

### Twilio
- **Must use v2 API** (`/v2/PhoneNumbers/` with `Fields=line_type_intelligence`).
- v1 returns NO carrier data on free trial.
- Cost is $0.008/lookup (not $0.005 like v1).
- Only 197/1,800 returned carrier data from Twilio — Tracerfy phone_type filled the rest.

### ATTOM
- 133/500 leads had lender data. Many showed $0 loan amounts.
- Mixed results — useful as supplement, not primary source.

---

## Cost Model Per Deployment

### Typical First Run (~7,500 leads)

| Item | Cost |
|------|------|
| Property data (state records) | $0 |
| Entity resolution (SoS registry) | $0 |
| Skip trace (Tracerfy, ~45% match) | ~$60 |
| Email validation (MillionVerifier) | ~$5 |
| Phone validation (Twilio trial) | $0 |
| DNC registry (FTC, first 5 area codes) | $0 |
| **Total** | **~$65** |

### Monthly Recurring

| Item | Cost |
|------|------|
| Data sourcing (public records) | $0 |
| DNC re-scrub (every 31 days) | $0 (FTC) or ~$70 (Tracerfy) |
| **Total** | **$0-70/mo** |

### Optional Add-Ons

| Item | Cost | When |
|------|------|------|
| Tracerfy DNC scrub | ~$60 per 3,000 phones | If using Tracerfy comprehensive DNC |
| ATTOM mortgage data | $95-500/mo | When clerk records insufficient |
| Second-pass skip trace (Datazapp) | $125 one-time | For Tracerfy misses, 2,000+ leads |
| MillionVerifier top-up | $11.90/5K credits | As email volume grows |

---

## API Configuration (.env)

```bash
# Skip Trace (PRIMARY)
TRACERFY_API_KEY=

# Email Validation
MILLIONVERIFIER_API_KEY=

# Phone Validation
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=

# Property + Mortgage Data (OPTIONAL)
ATTOM_API_KEY=

# County Clerk CAPTCHA Solving (OPTIONAL)
TWOCAPTCHA_API_KEY=

# Wealth Signals (Free)
FEC_API_KEY=DEMO_KEY

# Google Sheets Export
GOOGLE_OAUTH_CREDENTIALS=

# CRM
AIRTABLE_API_TOKEN=

# DO NOT USE (waste of money for this population):
# APOLLO_API_KEY=
# DATAZAPP — web portal only, $125 minimum
```

---

## Unresolved Data Gaps

These data points have no cheap/easy source yet:

| Gap | Impact | Best Available Source | Cost |
|-----|--------|---------------------|------|
| Real estate agent (buy-side) | Referral channel | MLS data (agent-restricted) | Paid |
| Property manager | Referral channel | Rental listing scraping | Free but fragile |
| Airbnb/STR revenue | STR DSCR calculation | AirDNA | $500+/mo |
| Actual mortgage interest rate | Rate refi precision | ATTOM or CoreLogic | $95-500/mo |
| Divorce/probate filings | Life event urgency | County clerk (CAPTCHA-blocked) | $3-5 via 2Captcha |
