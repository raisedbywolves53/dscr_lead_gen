# DSCR Lead Generation Pipeline

## Overview

This pipeline sources, identifies, and enriches Florida real estate investor leads from free public data sources. It outputs a scored, tagged Excel spreadsheet of prospects matching DSCR loan ICP criteria.

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                   DATA SOURCES                       │
│                                                      │
│  1. FDOR NAL/SDF ─── FL property records (all 67)   │
│  2. SunBiz FTP ───── LLC/Corp filings               │
│  3. DBPR CSV ─────── Vacation rental licenses        │
│  4. SEC EDGAR API ── RE fund Form D filings          │
└──────────────┬──────────────────────────┬────────────┘
               │                          │
               ▼                          ▼
┌──────────────────────┐  ┌──────────────────────────┐
│  FILTER & CLASSIFY   │  │  ENTITY RESOLUTION       │
│                      │  │                          │
│  Non-owner-occupied  │  │  LLC name → SunBiz →     │
│  Homestead = NO      │  │  Registered Agent →      │
│  Entity ownership    │  │  Human name + address    │
│  Property type       │  │                          │
│  Recent transactions │  │                          │
└──────────┬───────────┘  └──────────┬───────────────┘
           │                         │
           ▼                         ▼
┌─────────────────────────────────────────────────────┐
│                   ENRICHMENT                         │
│                                                      │
│  Name + Address → Skip trace → Phone + Email        │
│  Business name → Apollo/Hunter → Email              │
│  Google search → Website, social profiles            │
└──────────────────────────┬──────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────┐
│                 ICP SCORING & OUTPUT                  │
│                                                      │
│  Tag ICP segment (investor type)                    │
│  Score by: portfolio size, recency, property type,  │
│            equity estimate, geographic fit           │
│  Output: leads_YYYY-MM-DD.xlsx                      │
└─────────────────────────────────────────────────────┘
```

## Modules

| Module | File | Purpose |
|---|---|---|
| 1 | `01_fdor_property_data.md` | Download & filter FL property records |
| 2 | `02_sunbiz_entity_resolution.md` | Resolve LLC owners to humans |
| 3 | `03_dbpr_str_operators.md` | Identify vacation rental operators |
| 4 | `04_sec_edgar_funds.md` | Find FL real estate fund managers |
| 5 | `05_enrichment.md` | Add phone/email to leads |
| 6 | `06_scoring_output.md` | Score, tag, and export to Excel |
| 7 | `07_orchestrator.md` | Master runner — executes full pipeline |

## Output Schema

See `output_schema.md` for the full column specification of the output Excel file.

## Requirements

- Python 3.8+
- Libraries: `pandas`, `openpyxl`, `requests`, `beautifulsoup4`, `zipfile`, `csv`, `json`
- Internet access (for downloading public data files)
- No paid API keys required for base pipeline
- Optional: Apollo.io free tier API key for email enrichment

## Test Run

Start with a single county (Palm Beach — Frank's home market) to validate the pipeline end-to-end before scaling to all 67 counties.

```bash
python pipeline/scripts/run_pipeline.py --counties "PALM BEACH" --output leads_test.xlsx
```
