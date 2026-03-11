# DSCR Lead Generation System — Overview

## What This Is

An automated lead generation platform for **DSCR (Debt Service Coverage Ratio) mortgage loans** targeting real estate investors. Built to be deployed in any U.S. market for any loan originator.

DSCR loans qualify borrowers based on the property's rental income rather than personal income — making them ideal for investors, self-employed borrowers, LLC owners, and anyone who struggles with traditional income documentation.

## What It Produces

For a given market (state + counties), the system produces:
1. **Scored lead lists** — every investment property owner ranked 0-100 by DSCR opportunity
2. **Investor dossiers** — portfolio, financing, purchase behavior, wealth signals, network
3. **Campaign-ready exports** — formatted for email, SMS, dialer, and direct mail platforms
4. **CRM integration** — Airtable base with 7 tables, 191 fields, full lead scoring
5. **Google Sheets MVP** — call sheet, battlecards, and performance tracking

## How It Compares

| Feature | This System | PropStream ($99/mo) | BatchData ($299/mo) | Reonomy ($249/mo) |
|---------|------------|--------------------|--------------------|-------------------|
| Property ownership | Yes | Yes | Yes | Yes |
| LLC resolution to person | Yes (SunBiz/SoS) | No | No | Partial |
| Financing intelligence | Yes (clerk records) | No | Partial | No |
| Purchase behavior analysis | Yes (SDF data) | Limited | No | No |
| Wealth signals (FEC, 990) | Yes | No | No | No |
| Network mapping | Yes | No | No | No |
| ICP scoring | Custom 0-100 | Basic | No | No |
| Skip trace | Tracerfy ($0.02/match) | $0.10-0.12/lead | $0.02-0.10/lead | N/A |
| Cost (per market) | ~$60-120 one-time | $99/mo ongoing | $299/mo ongoing | $249/mo ongoing |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    PHASE 1: FOUNDATION                       │
├─────────────────────────────────────────────────────────────┤
│ 01 Download    → 02 Parse    → 03 Score/Filter → 04 Resolve│
│ Property Data     Standardize    ICP Scoring       LLCs     │
└─────────────────────────────┬───────────────────────────────┘
                              │
┌─────────────────────────────▼───────────────────────────────┐
│                    PHASE 2: ENRICHMENT                       │
├─────────────────────────────────────────────────────────────┤
│ 05 Contact     → 05b Merge  → 06 Validate   → 07 Export   │
│ Enrichment        Sources      Phone/Email      Campaign    │
│ 08 Skip Trace (Tracerfy)                                    │
└─────────────────────────────┬───────────────────────────────┘
                              │
┌─────────────────────────────▼───────────────────────────────┐
│                    PHASE 3: INTELLIGENCE                     │
├─────────────────────────────────────────────────────────────┤
│ 11 Clerk Records  12 Purchase History  13 Rent Estimates    │
│ 14 Wealth Signals 15 Network Mapping   16 Life Events       │
│ 20 Build Dossier                                            │
└─────────────────────────────────────────────────────────────┘
```

### Pipeline Principles
1. **Each script is self-contained** — reads CSV in, writes CSV out
2. **CSV is the interchange format** — no databases required
3. **Fail gracefully** — if a source is down, skip it, don't crash
4. **Cache everything** — never pay twice for the same API lookup
5. **Respect rate limits** — built-in delays between requests

---

## Tech Stack

| Component | Tool | Cost |
|-----------|------|------|
| Language | Python 3.10+ | Free |
| Libraries | pandas, openpyxl, requests, beautifulsoup4, python-dotenv | Free |
| Skip trace | Tracerfy API ($0.02/match) | Per-use |
| Email validation | MillionVerifier ($4.90/2K credits) | Per-use |
| Phone validation | Twilio Lookup v2 ($0.008/lookup) | Per-use |
| CRM | Airtable (Team plan, $20/seat/mo) | Monthly |
| Output | Google Sheets (free) | Free |
| Hosting | Local machine / any Python environment | Free |

---

## Data Flow Per Deployment

```
State Property Records (free)
  → Parse & standardize
  → Score by ICP criteria (0-100)
  → Resolve entities (LLC → person via Secretary of State)
  → Skip trace (Tracerfy: $0.02/match)
  → Validate contacts (phone type, email validity, DNC)
  → Export campaign-ready lists
  → Upload to CRM (Airtable) + Google Sheets
```

**Cost per market (typical):**
- Property data: $0 (public records)
- Skip trace: $0.02/match × ~45% match rate
- Validation: ~$15-20
- Total for ~7,500 leads: **$60-120**

---

## State-Specific Components

Each state deployment requires locating equivalents for:

| Component | What It Provides | Florida Example |
|-----------|-----------------|----------------|
| **Property tax records** | Ownership, values, addresses, use codes | FDOR NAL files |
| **Business entity registry** | LLC officers, registered agents | SunBiz (Division of Corporations) |
| **STR/vacation rental registry** | Licensed short-term rental operators | DBPR vacation rental licenses |
| **County clerk/recorder** | Mortgages, liens, lis pendens, deeds | County Clerk of Court |
| **Homestead/owner-occupied flag** | Distinguish investors from residents | Homestead exemption (FDOR) |
| **Sales/deed records** | Purchase history, transaction prices | FDOR SDF files |

See `deployments/{state}/CONFIG.md` for state-specific data sources.

---

## File Structure

```
CLAUDE.md                       # Claude CLI context
docs/
├── SYSTEM_OVERVIEW.md          # This file — architecture, tech stack
├── ICP_PLAYBOOK.md             # All ICP segments, scoring, outreach angles
├── ENRICHMENT_STACK.md         # Every vendor: cost, verdict, gotchas
├── PIPELINE_GUIDE.md           # Step-by-step execution bible
├── OUTPUT_SCHEMA.md            # Canonical column definitions
├── CRM_SETUP.md                # Airtable base design
├── COMPLIANCE.md               # DNC, TCPA, state calling rules
└── airtable/                   # Detailed Airtable step-by-step guides

deployments/
├── TEMPLATE.md                 # Checklist for deploying in a new market
├── florida/                    # FL-specific config + client deployments
└── north_carolina/             # NC-specific config

scrape/                         # Active pipeline code
├── scripts/                    # Pipeline scripts (01-20)
├── config/                     # JSON configs (scoring, counties, enrichment)
├── data/                       # Pipeline output data (gitignored)
└── CLAUDE.md                   # Pipeline-specific context

airtable/                       # CRM integration scripts
archive/                        # Preserved old docs, pipeline_v1, research
```

---

## Deployment Model

To deploy in a new market:

1. **Research** state-specific data sources (property records, entity registry, STR licenses)
2. **Configure** `deployments/{state}/CONFIG.md` with sources, URLs, county codes
3. **Adapt** pipeline scripts for new data format (Steps 01-04 are state-specific)
4. **Run** enrichment + validation (Steps 05-08 are state-agnostic)
5. **Deploy** CRM + Sheets output for the loan originator

Steps 05-08 (enrichment, skip trace, validation, export) work unchanged across all states. Steps 01-04 (download, parse, score, entity resolve) need state-specific adapters. Steps 10-20 (intelligence) are mostly state-agnostic with some county clerk variations.
