# DSCR Lead Generation Pipeline — Claude CLI Context

## Project Summary

This is an automated lead generation system for **DSCR (Debt Service Coverage Ratio) mortgage loans** targeting Florida real estate investors. Built for **Zack / CrossCountry Mortgage (CCM)**.

Two pipelines exist:
1. **`pipeline/`** — Original pipeline (built, Palm Beach data processed, 39K leads)
2. **`scrape/`** — Active investor intelligence pipeline (in progress, Tracerfy integration)

**Plus the Airtable CRM** — the operational hub where all leads, properties, financing, and opportunities are managed.

---

## Airtable CRM (Active Build)

### Base Details
- **Base ID:** appJV7J1ZrNEBAWAm
- **Workspace ID:** wspqb7kWqj5RidMkV
- **API Token:** stored in `.env` file (key: `AIRTABLE_API_TOKEN`)
- **Base URL:** https://airtable.com/appJV7J1ZrNEBAWAm

### Build Status (as of 2026-03-06)

**COMPLETED:**
- All 7 tables (191 fields total, 0 broken formulas/rollups)
  - Investors (50 fields) — contact info, 10 rollups, 9 formulas, full lead scoring 0-100
  - Ownership Entities (18 fields) — entity details, 3 rollups, 1 formula
  - Properties (36 fields) — property details, 3 rollups, 10 formulas, 1 lookup
  - Financing (35 fields) — loan details, 11 formulas (all trigger flags)
  - Compliance (15 fields) — DNC/consent tracking, 2 formulas
  - Opportunities (24 fields) — deal pipeline, 5 formulas + auto timestamps
  - Outreach Log (13 fields) — activity tracking
- All 9 link relationships between tables
- Rollup chains: Financing → Properties → Investors
- Test CSV data in `airtable/test_data/`

**NOT YET DONE (Zack is working through these manually on desktop):**
Follow `airtable/NEXT_STEPS_Sequential_Guide.md`:
1. Phase 1: Quick Fixes (delete Table 8, rename Trigger County, add 2 missing fields)
2. Phase 2: 24 Views (all manual in Airtable UI)
3. Phase 3: 8 Automations (all manual)
4. Phase 4: Test Upload (CSVs ready in `airtable/test_data/`)
5. Phase 5: 4 Interfaces/Dashboards
6. Phase 6: Full 7,500 lead import + HubSpot sync

### Key Airtable Files
- `DSCR_Airtable_Build_Guide.md` — Master spec (1,162 lines): all fields, formulas, views, automations, interfaces
- `airtable/NEXT_STEPS_Sequential_Guide.md` — Step-by-step manual instructions for remaining work
- `airtable/Airtable_AI_Field_Prompts.md` — AI prompts used to create 32 formula/rollup fields
- `airtable/airtable_build_v2.py` — API script that created the base skeleton (tokens redacted)
- `airtable/create_remaining_fields.py` — Attempted API field creation (blocked by API limitations)
- `airtable/test_data/` — Test CSVs + README with expected trigger results

### Important Technical Notes
- Airtable API CANNOT create formula, rollup, createdTime, or lastModifiedTime fields
- Airtable AI assistant CANNOT create views or automations
- Financing trigger fields lack emoji prefixes (e.g., "Hard Money Flag" not "🚨 Hard Money Flag")
- "Trigger County" on Properties is actually Trigger Count rollup (typo, needs rename)
- Rollup aggregations show as "NONE" in API metadata — this is normal, they work

### How To Validate via API
```python
import os, requests
API_TOKEN = os.getenv('AIRTABLE_API_TOKEN')  # stored in .env file
BASE_ID = 'appJV7J1ZrNEBAWAm'
headers = {'Authorization': f'Bearer {API_TOKEN}'}
resp = requests.get(f'https://api.airtable.com/v0/meta/bases/{BASE_ID}/tables', headers=headers)
data = resp.json()
for table in data['tables']:
    broken = sum(1 for f in table['fields'] if f['type'] in ('formula','rollup') and f.get('options',{}).get('result') is None)
    print(f"{table['name']}: {len(table['fields'])} fields" + (f" ({broken} BROKEN)" if broken else ""))
```

---

## Key Files & Where to Find Things

### Active Docs (START HERE)
- `DSCR_Lead_Gen_Strategy.md` — Comprehensive data acquisition & outreach strategy
- `DSCR_Airtable_Build_Guide.md` — Complete Airtable CRM spec
- `E2E_EXECUTION_PLAN.md` — Step-by-step instructions to run the original pipeline
- `ICP_DEFINITIONS.md` — All 19 ICP segments with signals, sources, and classification logic
- `PIPELINE_RUNBOOK.md` — Data flow, troubleshooting, memory management, known issues
- `OUTPUT_SPEC.md` — Final Excel format, column definitions, tab structure

### Scrape Pipeline (Active Development)
- `scrape/CLAUDE.md` — Full project specification, data schema, design principles
- `scrape/PIPELINE.md` — Execution spec for all scripts (01-20)
- `scrape/DATA_SOURCES.md` — Every data field mapped to its source
- `scrape/TODO_FOR_FRANK.md` — Action items for Zack (API keys, costs, compliance)
- `scrape/VERIFIED_PRICING.md` — Fact-checked vendor pricing (Tracerfy, Datazapp, Apollo, etc.)
- `scrape/ICP_CRITERIA.md` — Scoring weights for scrape pipeline
- `scrape/BUILD_PLAN.md` — Development roadmap and milestones
- `scrape/QUICKSTART.md` — Setup instructions
- `scrape/research/county_clerk_research.md` — PB/Broward clerk portal findings

### Archived Research (Background Context)
- `archive/DSCR_Research_Memo.md` — Core DSCR market intelligence, lender comparison
- `archive/DSCR_Research_Memo_Part2.md` — Competitive landscape, referral ecosystem
- `archive/Phase1_ICP_Sourcing_Playbook.md` — Tactical ICP sourcing guide
- `archive/SAMPLE_VALIDATION_REPORT.md` — 50-lead validation results
- `archive/research/01-05_*.md` — Deep-dive research (product mechanics, ICPs, competition, market sizing, vendors)

### Original Pipeline Code
- `pipeline/scripts/run_pipeline.py` — Master orchestrator (runs all steps)
- `pipeline/scripts/01_chunked_filter.py` — Step 1: FDOR property filter (memory-efficient)
- `pipeline/scripts/08_refi_simple.py` — Step 2: Refinance candidate detection
- `pipeline/scripts/02_sunbiz_resolve.py` — Step 3: LLC-to-human resolution via SunBiz
- `pipeline/scripts/03_dbpr_str.py` — Step 4: Vacation rental license tagging
- `pipeline/scripts/04_sec_edgar.py` — Step 5: SEC fund manager identification
- `pipeline/scripts/05_enrich_contacts.py` — Step 6: Phone/email enrichment
- `pipeline/scripts/06_score_and_output.py` — Step 7: ICP scoring + Excel generation

### Scrape Pipeline Code
- `scrape/scripts/01_download_nal.py` — Download FDOR NAL files
- `scrape/scripts/02_parse_nal.py` — Parse & standardize property data
- `scrape/scripts/03_filter_icp.py` — Score and filter by ICP criteria
- `scrape/scripts/04_sunbiz_llc_resolver.py` — Resolve LLCs to people via SunBiz
- `scrape/scripts/05_enrich_contacts.py` — Multi-source contact enrichment + county filter
- `scrape/scripts/05b_merge_enrichment.py` — Merge all enrichment sources
- `scrape/scripts/06_validate_contacts.py` — Email/phone/DNC validation
- `scrape/scripts/07_export_campaign_ready.py` — Export for outreach platforms
- `scrape/scripts/08_tracerfy_skip_trace.py` — Tracerfy API skip trace + DNC scrub
- `scrape/scripts/10_apollo_enrich.py` — Apollo.io API enrichment
- `scrape/scripts/11-16, 20` — Phase 2 intelligence scripts (specced, not all built)

### Pipeline Module Docs
- `pipeline/01_fdor_property_data.md` through `pipeline/08_refi_candidates.md`
- `pipeline/README.md` — Architecture overview
- `pipeline/output_schema.md` — Output column schema

### Data Locations
- `pipeline/data/fdor/` — Florida DOR NAL property files (343MB+ per county)
- `pipeline/data/dbpr/` — DBPR vacation rental license CSV (126MB)
- `pipeline/output/06_enriched.csv` — 39,353 leads (source for scrape pipeline)
- `scrape/data/enriched/` — Contact enrichment results
- `scrape/data/enriched/tracerfy_results.csv` — Tracerfy skip trace output
- `scrape/data/enriched/merged_enriched.csv` — All sources merged

---

## Current Execution Flow (Scrape Pipeline)

```
Step 1: Select + filter PB/Broward leads    → scrape/data/enriched/top_leads_enriched.csv
Step 2: Tracerfy skip trace ($0.02/lead)     → scrape/data/enriched/tracerfy_results.csv
Step 3: Merge all enrichment sources         → scrape/data/enriched/merged_enriched.csv
Step 4: Validate emails + phones + DNC       → scrape/data/validated/merged_validated.csv
Step 5: Export campaign-ready lists          → scrape/data/campaign_ready/
```

```bash
python scrape/scripts/05_enrich_contacts.py --counties "palm beach,broward"
python scrape/scripts/08_tracerfy_skip_trace.py
python scrape/scripts/05b_merge_enrichment.py
python scrape/scripts/06_validate_contacts.py --county merged
python scrape/scripts/07_export_campaign_ready.py --county merged
```

---

## Skip Trace & Enrichment Stack

| Provider | Cost | Role | Status |
|----------|------|------|--------|
| Tracerfy | $0.02/lead, no minimums | Primary skip trace | NEED API KEY |
| Tracerfy DNC | $0.02/phone | Federal+State+DMA+TCPA litigator scrub | Optional |
| Datazapp | $125 minimum/transaction | Second-pass on Tracerfy misses | $75 balance, unused |
| Apollo.io | $99/mo | B2B enrichment | Returns nothing for LLC investors — cancel? |
| FTC DNC | Free (4 area codes) | Federal DNC compliance | NEED TO REGISTER |
| MillionVerifier | $4.90 one-time | Email validation | NEED API KEY |
| Twilio | Free $15 trial | Phone type detection | NEED API KEY |

**Total cost for full PB/Broward run (7,537 leads): $156-$226**

---

## Critical Technical Notes

### Memory Management
- Palm Beach NAL file is 343MB / 654K rows — **MUST use chunked processing**
- Use `01_chunked_filter.py` (NOT `01_fdor_download_filter.py`) to avoid OOM kills

### Rate Limiting
- SunBiz: 3-second delay between requests
- Tracerfy: max 10 POST requests per 5 minutes
- SEC EDGAR: 7 requests/second

### Data Quality Known Issues
- FDOR `SALE_YR1`/`SALE_PRC1` reflects most recent sale only
- Equity ratio is estimated (JV vs. sale price); no mortgage balance from FDOR
- SunBiz web scraping may hit Cloudflare blocks — uses session cookies + retry
- DBPR matching is fuzzy (address normalization) — ~70-80% match rate
- Apollo.io returns 0 contact data for private RE investors through LLCs
- Datazapp has $125 minimum per transaction (not per-match as advertised)

### Dependencies
```bash
pip install pandas openpyxl requests beautifulsoup4 python-dotenv
```

---

## Contact & Ownership

- **User**: Zack, Mortgage Loan Originator (DSCR specialist)
- **Focus Market**: Palm Beach + Broward County, Florida
- **Target Scale**: All 67 FL counties, then nationwide
- **Pipeline Date**: March 2026
- **GitHub**: https://github.com/raisedbywolves53/dscr_lead_gen.git
