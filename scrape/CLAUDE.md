# DSCR Lead Gen — Property Owner Contact Pipeline

## Project Overview

This project builds a low-cost lead generation pipeline for a mortgage loan originator (MLO) specializing in DSCR (Debt Service Coverage Ratio) loans in Florida. The pipeline scrapes, parses, enriches, and exports property owner contact data from free/cheap public sources — replacing $700+/mo platforms like BatchData, PropStream, and PopStream.

## Tech Stack

- **Language:** Python 3.10+
- **Key Libraries:** requests, beautifulsoup4, pandas, openpyxl, selenium (if needed for JS-rendered county sites)
- **Data Storage:** CSV files in `data/` subdirectories
- **IDE:** VS Code with Claude CLI (user is non-technical — code must be clean, well-commented, and runnable with simple terminal commands)

## Architecture

```
dscr_lead_gen/
├── CLAUDE.md                          # This file — project spec
├── PIPELINE.md                        # Detailed pipeline execution spec
├── ICP_CRITERIA.md                    # ICP definitions and scoring logic
├── requirements.txt
├── .env.example
├── scripts/
│   ├── 01_download_nal.py             # Download FL Dept of Revenue NAL files
│   ├── 02_parse_nal.py                # Parse fixed-width NAL into clean CSV
│   ├── 03_filter_icp.py              # Filter properties matching ICP criteria
│   ├── 04_sunbiz_llc_resolver.py     # Resolve LLC owners via FL Sunbiz
│   ├── 05_enrich_contacts.py         # Enrich with phone/email (voter file + APIs)
│   ├── 06_validate_contacts.py       # Validate emails and phone numbers
│   └── 07_export_campaign_ready.py   # Export final lists for outreach
├── data/
│   ├── raw/                           # Downloaded NAL files, voter files
│   ├── parsed/                        # Clean CSVs from NAL parsing
│   ├── filtered/                      # ICP-matched properties
│   ├── enriched/                      # With contact info appended
│   ├── validated/                     # After email/phone validation
│   └── campaign_ready/               # Final export for outreach tools
├── config/
│   ├── counties.json                  # Target county URLs and data formats
│   └── scoring_weights.json           # ICP scoring weights
└── logs/
```

## Execution Model

Each script is numbered and runs sequentially. The user runs them one at a time:

```bash
python scripts/01_download_nal.py --county broward
python scripts/02_parse_nal.py --county broward
python scripts/03_filter_icp.py --county broward
# ... etc
```

Or run the full pipeline:

```bash
python scripts/01_download_nal.py --county broward && python scripts/02_parse_nal.py --county broward && python scripts/03_filter_icp.py --county broward
```

## Critical Design Principles

1. **Each script is self-contained** — reads from one `data/` subfolder, writes to the next
2. **CSV is the interchange format** — no databases, no complex setup
3. **Fail gracefully** — if a county site is down, log it and skip, don't crash
4. **Progress logging** — print clear status messages so the user knows what's happening
5. **Respect rate limits** — add delays between requests, honor robots.txt
6. **Comments everywhere** — the user is a non-technical marketer who needs to understand what each section does

## Environment Variables (.env)

```
# Optional — only needed for enrichment/validation steps
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
NUMVERIFY_API_KEY=
MILLIONVERIFIER_API_KEY=
```

## County Data Sources (Florida)

Priority counties for DSCR leads (high investor activity):
1. Miami-Dade (bulk download: $50/file from bbs.miamidade.gov)
2. Broward (bcpa.net — free search, may need scraping)
3. Palm Beach (pbcgov.org — GIS data downloads available)
4. Orange (ocpafl.org — data downloads available)
5. Hillsborough (hcpafl.org — GIS search portal)
6. Duval/Jacksonville (coj.net — property appraiser downloads)
7. Pinellas (pcpao.gov — data extracts available)
8. Lee (leepa.org — data downloads)
9. Sarasota (sc-pa.com — free CSV downloads)
10. Seminole (scpafl.org — free Excel/Access downloads updated daily)

The FL Department of Revenue also publishes statewide NAL (Name-Address-Legal) files that cover ALL 67 counties. This is the primary data source. Request via: PTOTechnology@floridarevenue.com

## ICP Targets (see ICP_CRITERIA.md for full definitions)

1. Portfolio Landlords (5+ properties, same owner/LLC)
2. Self-Employed Investors (LLC owners buying investment properties)
3. Short-Term Rental Investors (Airbnb/VRBO markets)
4. Out-of-State Investors (mailing address ≠ property address)
5. Fix-and-Flip / BRRRR Investors (recent cash purchases)
6. Cash Buyers Seeking Leverage (no mortgage on record)
7. Foreign National Investors
8. Section 8 Landlords
