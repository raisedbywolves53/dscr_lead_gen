# DSCR Lead Gen — Investor Intelligence Pipeline

## Project Overview

Portable investor intelligence platform that produces enriched DSCR investor dossiers from public property records. Sold to LOs, branch managers, RE agents, and RE brokers. Deployable in any U.S. market.

See root `CLAUDE.md` for full business context, buyer ICPs, and pricing.
See `docs/SYSTEM_OVERVIEW.md` for architecture. See `deployments/` for market-specific configs.

## Tech Stack

- **Language:** Python 3.10+
- **Key Libraries:** requests, beautifulsoup4, pandas, openpyxl, python-dotenv
- **ATTOM API:** 7 endpoints per lead — core enrichment differentiator
- **Skip Trace:** Tracerfy ($0.02/match) — see `docs/ENRICHMENT_STACK.md`
- **Validation:** MillionVerifier (email), Twilio v2 (phone)
- **Data Storage:** CSV files in `data/` subdirectories

## Target Markets

| Market | Counties | FIPS | Status |
|--------|----------|------|--------|
| South Florida | Palm Beach | 12099 | Pipeline built, 500 pilot fully enriched |
| South Florida | Broward | 12011 | Pipeline built, included in 7,537 qualified |
| North Carolina | Wake | 37183 | 373K scored, 33 samples enriched, bulk pipeline not run |

**Future (research only):** Cuyahoga OH, Marion IN

## Architecture

```
scrape/
├── CLAUDE.md                          # This file
├── scripts/
│   ├── 01_download_nal.py             # Download FDOR NAL + SDF files (FL)
│   ├── 01_download_wake.py            # Download Wake County property data (NC)
│   ├── 02_parse_nal.py                # Parse FL property data
│   ├── 02_parse_wake.py               # Parse NC property data
│   ├── 03_filter_icp.py              # Score and filter by ICP criteria
│   ├── 04_sunbiz_llc_resolver.py     # Resolve LLCs → people via SunBiz (FL only)
│   ├── 05_enrich_contacts.py         # Multi-source contact enrichment
│   ├── 05b_merge_enrichment.py       # Merge all enrichment sources
│   ├── 06_validate_contacts.py       # Validate emails and phone numbers
│   ├── 07_export_campaign_ready.py   # Export final lists for outreach
│   ├── 08_tracerfy_skip_trace.py     # Tracerfy skip trace API
│   ├── 11_clerk_lender_lookup.py     # County clerk mortgage scraping
│   ├── 12_sdf_purchase_history.py    # Purchase history analysis
│   ├── 13_rental_estimates.py        # HUD FMR rent estimates
│   ├── 14_wealth_signals.py          # FEC donations, IRS 990s
│   ├── 15_mortgage_estimates.py      # Mortgage balance/rate estimation
│   ├── 16_attom_mortgage.py          # ATTOM API — detailmortgageowner (Step 16)
│   ├── 20_build_dossier.py           # Assemble full investor profile
│   ├── attom_showcase_mortgage.py    # ATTOM 7-endpoint enrichment for showcase leads
│   ├── enrich_showcase_leads.py      # Per-property detail for showcase leads
│   ├── build_sales_demo.py           # Sales demo Excel workbook
│   ├── build_dossier_pdf.py          # PDF tear sheet generator
│   ├── build_workbook.py             # Excel workbook builder
│   ├── build_compliance_sheet.py     # Compliance documentation
│   ├── sunbiz_showcase_lookup.py     # SunBiz lookup for showcase leads
│   ├── 22_prepayment_penalty_targeting.py  # PPP expiration targeting (HMDA + inference)
│   └── build_ppp_deliverable.py      # PPP deliverable Excel (branded, client-facing)
├── data/
│   ├── raw/                           # Downloaded source files
│   ├── parsed/                        # Standardized CSVs
│   ├── filtered/                      # ICP-scored properties
│   ├── enriched/                      # Contact + entity enrichment
│   ├── financing/                     # Mortgage & lien data + ATTOM cache
│   ├── history/                       # Purchase history & SDF data
│   ├── signals/                       # Wealth, life events, network
│   ├── mvp/                           # Pilot 500 master (FL)
│   ├── demo/                          # Showcase lead enrichment output
│   ├── validated/                     # After contact validation
│   ├── campaign_ready/               # Final export for outreach
│   ├── hmda/                          # HMDA LAR downloads (~900MB, gitignored)
│   ├── ppp_targeting/                 # PPP scoring output
│   └── deliverables/                  # Client-facing Excel workbooks
└── config/
    ├── counties.json                  # Target county URLs and data formats
    ├── scoring_weights.json           # FL ICP scoring weights
    ├── nc_scoring_weights.json        # NC ICP scoring weights
    └── dscr_lenders.json              # 54 known DSCR/non-QM lenders (3 tiers)
```

## Data Sources

| Source | Cost | What It Provides | Markets |
|--------|------|-----------------|---------|
| FDOR NAL/SDF files | Free | Property ownership, values, sales history | FL |
| NC OneMap + Wake Tax | Free | Property ownership, values, sales | NC |
| FL SunBiz | Free | LLC officers, registered agents | FL |
| FL DBPR | Free | Vacation rental licenses, PM licenses | FL |
| County Clerk (PB/Broward) | Free | Mortgages, liens, lis pendens | FL |
| **ATTOM API** | **7 calls/lead** | **Mortgage, AVM, rental, sales, tax, permits, property details** | **All** |
| Tracerfy | $0.02/match | Up to 8 phones + 5 emails per lead | All |
| MillionVerifier | $4.90/2K | Email validation | All |
| Twilio v2 | $0.008/lookup | Phone type (mobile/landline/VoIP) | All |
| FEC.gov | Free | Political donation records | All |
| HUD Fair Market Rents | Free | Rent estimates by zip code | All |

**Do NOT use:** Apollo.io (cancelled — returns nothing for RE investors), Datazapp ($125 minimum — terrible for small runs)

## Environment Variables (.env)

```
# ATTOM — 7-endpoint property enrichment (CENTRAL)
ATTOM_API_KEY=

# Tracerfy — primary skip trace
TRACERFY_API_KEY=

# Twilio — phone validation (must use v2 API)
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=

# MillionVerifier — email validation
MILLIONVERIFIER_API_KEY=

# FEC.gov — wealth signals (free)
FEC_API_KEY=DEMO_KEY

# Airtable — CRM (archived, optional)
AIRTABLE_PAT=
AIRTABLE_BASE_ID=
```

## Critical Design Principles

1. **Each script is self-contained** — reads from one `data/` subfolder, writes to the next
2. **CSV is the interchange format** — no databases, no complex setup
3. **Fail gracefully** — if a source is down, log it and skip, don't crash
4. **Cache everything** — save raw API responses so we never pay twice for the same lookup
5. **Respect rate limits** — built-in delays between requests
6. **Comments everywhere** — code must be readable by a non-developer
7. **Always load CSVs with `dtype=str`** — booleans are stored as strings
8. **ATTOM: APN + FIPS as primary lookup** — address as fallback only
