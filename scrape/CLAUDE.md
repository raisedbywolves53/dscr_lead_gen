# DSCR Lead Gen — Investor Intelligence Pipeline

## Project Overview

Portable investor intelligence platform for DSCR mortgage loan originators. Aggregates public data to build deep investor profiles — replacing $700+/mo platforms like BatchData, PropStream, and Reonomy. Deployable in any U.S. market.

See `docs/SYSTEM_OVERVIEW.md` for full architecture. See `deployments/` for market-specific configs.

## Tech Stack

- **Language:** Python 3.10+
- **Key Libraries:** requests, beautifulsoup4, pandas, openpyxl, python-dotenv
- **Skip Trace:** Tracerfy ($0.02/match) — see `docs/ENRICHMENT_STACK.md`
- **Validation:** MillionVerifier (email), Twilio v2 (phone)
- **Data Storage:** CSV files in `data/` subdirectories

## Architecture

```
scrape/
├── CLAUDE.md                          # This file — project spec
├── PIPELINE.md                        # Detailed pipeline execution spec
├── DATA_SOURCES.md                    # Every data source mapped to every field
├── ICP_CRITERIA.md                    # ICP definitions and scoring logic
├── requirements.txt
├── .env.example
├── scripts/
│   ├── 01_download_nal.py             # Download FDOR NAL + SDF files
│   ├── 02_parse_nal.py                # Parse & standardize property data
│   ├── 03_filter_icp.py              # Score and filter by ICP criteria
│   ├── 04_sunbiz_resolver.py         # Resolve LLCs → people via SunBiz
│   ├── 05_enrich_contacts.py         # Multi-source contact enrichment
│   ├── 05b_merge_enrichment.py       # Merge manual + automated enrichment
│   ├── 06_validate_contacts.py       # Validate emails and phone numbers
│   ├── 07_export_campaign_ready.py   # Export final lists for outreach
│   ├── 10_apollo_enrich.py           # Apollo.io API enrichment
│   ├── 11_county_clerk.py            # County clerk mortgage/lien scraping
│   ├── 12_sdf_purchase_history.py    # FDOR SDF purchase history analysis
│   ├── 13_rental_estimates.py        # HUD FMR + Zillow rent estimates
│   ├── 14_wealth_signals.py          # FEC donations, IRS 990s, board seats
│   ├── 15_network_mapping.py         # Co-investors, shared PMs, agents
│   ├── 16_life_events.py             # Divorce, liens, lis pendens, probate
│   └── 20_build_dossier.py           # Assemble full investor profile
├── data/
│   ├── raw/                           # Downloaded source files
│   ├── parsed/                        # Standardized CSVs
│   ├── filtered/                      # ICP-matched properties
│   ├── enriched/                      # Contact + entity enrichment
│   ├── financing/                     # Mortgage & lien data
│   ├── history/                       # Purchase history & SDF data
│   ├── signals/                       # Wealth, life events, network
│   ├── dossiers/                      # Complete investor profiles
│   ├── validated/                     # After contact validation
│   └── campaign_ready/               # Final export for outreach
├── config/
│   ├── counties.json                  # Target county URLs and data formats
│   ├── scoring_weights.json           # ICP scoring weights
│   └── enrichment_sources.json        # API endpoints and rate limits
└── logs/
```

## Target Counties (Phase 1)

- **Palm Beach County** — primary market
- **Broward County** — secondary market
- Leads with mailing addresses in these counties only
- Properties in Miami-Dade acceptable if <25% of portfolio

## Investor Profile — What We Capture

### Non-Negotiable (must capture accurately)

```
CONTACT
├── Investor name (decision maker)
├── Primary entity / LLC
├── Phone (cell preferred)
├── Email (validated)
└── LinkedIn profile URL

PORTFOLIO
├── Property count
├── Total portfolio value
├── Total debt (mortgage balances)
├── Total equity
└── Portfolio DSCR estimate

FINANCING
├── Number of loans
├── Lender names
├── Average interest rate
├── Loans maturing within 24 months
└── Hard money exposure

ACQUISITION BEHAVIOR
├── Purchases last 12 months
├── Purchases last 36 months
└── Average purchase price

MARKETS
├── Primary markets
└── Secondary markets

OPPORTUNITY SIGNALS
├── Refinance opportunities
├── Recent cash purchases
├── Distressed loans
└── Balloon maturities

NETWORK
├── Property managers
├── Real estate agents
└── Co-investors

OPPORTUNITY SCORE (0-100)
```

### Full Intelligence (build toward)

```
CONTACT (expanded)
├── 3+ decision makers for investment firms
├── Age / approximate age
├── Employer (if not full-time investor)
├── Social media pages
├── Company website / business page

ENTITY DETAILS
├── LLC/entity name
├── Registered agent
├── State of incorporation
├── Year formed
├── All officers / directors

PORTFOLIO (per property)
├── Address
├── Estimated value
├── Estimated debt / mortgage balance
├── Estimated equity
├── Property type (SFR, MF, condo, etc.)
├── Ownership structure

FINANCING (per property)
├── Current lender
├── Loan origination date
├── Interest rate (estimated)
├── Loan type (conventional, hard money, etc.)
├── Maturity date
├── Estimated balance remaining
├── LTV estimate
├── Fixed vs adjustable rate
├── Lender type (bank, credit union, hard money, etc.)

PURCHASE HISTORY
├── Full purchase timeline (including sold properties)
├── Average purchase price
├── Flip vs hold behavior
├── Time between purchases
├── Cash vs financed percentage
├── Off-market vs MLS indicator

RENTAL / STR
├── Estimated rent per property
├── Portfolio occupancy estimate
├── Airbnb revenue estimate
├── Property management company
├── Listing presence (Airbnb/VRBO/Zillow)

MARKET POSITIONING
├── Investment geography (counties, cities, states)
├── Distance from primary residence
├── Appreciation / ROI on properties

WEALTH SIGNALS
├── Estimated net worth
├── Estimated income
├── Other businesses / LLCs
├── Political donation records (FEC)
├── Foundation donations (IRS 990)
├── Board seats
├── Professional licenses

NETWORK
├── Property managers used
├── Real estate agents (buy-side and sell-side)
├── Agent brokerage
├── Co-investors / syndication partners
├── Shared lenders across portfolio

LIFE EVENTS
├── Divorce filings
├── Estate transitions / probate
├── Business sales
├── Liens / judgments
├── Lis pendens (pre-foreclosure)

RELATIONSHIP MAPPING
├── Co-owners across entities
├── Shared business partners
├── Shared property managers
├── Shared lenders
├── Same realtors / brokerages
├── Investment group membership
```

## Data Sources

| Source | Cost | What It Provides |
|--------|------|-----------------|
| FDOR NAL files | Free | Property ownership, values, addresses, use codes, homestead |
| FDOR SDF files | Free | Full purchase/sale history across all counties |
| FL SunBiz | Free | LLC officers, registered agents, filing dates |
| FL DBPR | Free | Vacation rental licenses, PM licenses, phone numbers |
| County Clerk (PB) | Free | Mortgages, liens, lis pendens, divorce, probate |
| County Clerk (Broward) | Free | Same as above |
| Apollo.io | $100/mo | Email, phone, LinkedIn URL, employer, social profiles |
| FL Voter File | ~$5 | Phone, DOB/age, address verification |
| FEC.gov | Free | Political donation records |
| IRS 990 (ProPublica) | Free | Foundation/nonprofit donations |
| SEC EDGAR | Free | Fund managers, board seats |
| HUD Fair Market Rents | Free | Rent estimates by zip code |
| MillionVerifier | ~$0.50/1K | Email validation |
| Twilio Lookup | $0.005/ea | Phone validation + carrier/type |
| Datazapp | $0.03/ea | Batch skip trace (phone + email) |

See `DATA_SOURCES.md` for detailed field-level mapping.

## Critical Design Principles

1. **Each script is self-contained** — reads from one `data/` subfolder, writes to the next
2. **CSV is the interchange format** — no databases, no complex setup
3. **Fail gracefully** — if a source is down, log it and skip, don't crash
4. **Progress logging** — print clear status messages
5. **Respect rate limits** — add delays between requests
6. **Cache everything** — save raw API responses so we never pay twice for the same lookup
7. **Comments everywhere** — code must be readable by a non-developer
8. **"Impossible" is not accepted** — if a company sells this data, the source exists. Find it.

## Environment Variables (.env)

```
# Apollo.io — primary enrichment ($100/mo plan)
APOLLO_API_KEY=

# Twilio — phone validation
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=

# MillionVerifier — email validation
MILLIONVERIFIER_API_KEY=

# Numverify — phone type detection (free tier: 100/month)
NUMVERIFY_API_KEY=
```
