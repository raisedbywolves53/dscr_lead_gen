# DSCR Lead Generation Pipeline — Claude CLI Context

## Project Summary

This is an automated lead generation system for **DSCR (Debt Service Coverage Ratio) mortgage loans** targeting Florida real estate investors. Built for **Frank Christiano / CrossCountry Mortgage (CCM)**.

Two pipelines exist:
1. **`pipeline/`** — Original pipeline (built, Palm Beach data processed, 39K leads)
2. **`scrape/`** — Active investor intelligence pipeline (in progress, Tracerfy integration)

---

## Key Files & Where to Find Things

### Active Docs (START HERE)
- `DSCR_Lead_Gen_Strategy.md` — Comprehensive data acquisition & outreach strategy
- `E2E_EXECUTION_PLAN.md` — Step-by-step instructions to run the original pipeline
- `ICP_DEFINITIONS.md` — All 19 ICP segments with signals, sources, and classification logic
- `PIPELINE_RUNBOOK.md` — Data flow, troubleshooting, memory management, known issues
- `OUTPUT_SPEC.md` — Final Excel format, column definitions, tab structure

### Scrape Pipeline (Active Development)
- `scrape/CLAUDE.md` — Full project specification, data schema, design principles
- `scrape/PIPELINE.md` — Execution spec for all scripts (01-20)
- `scrape/DATA_SOURCES.md` — Every data field mapped to its source
- `scrape/TODO_FOR_FRANK.md` — Action items for Frank (API keys, costs, compliance)
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

- **Client**: Frank Christiano, CrossCountry Mortgage
- **Focus Market**: Palm Beach + Broward County, Florida
- **Target Scale**: All 67 FL counties, then nationwide
- **Pipeline Date**: March 2026
