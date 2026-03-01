# DSCR Lead Generation Pipeline — Claude CLI Context

## Project Summary

This is an automated lead generation system for **DSCR (Debt Service Coverage Ratio) mortgage loans** targeting Florida real estate investors. Built for **Frank Christiano / CrossCountry Mortgage (CCM)**.

The pipeline ingests free public data sources, identifies investment property owners, classifies them into ICP segments (including purchase AND refinance candidates), enriches contacts, scores leads, and outputs a multi-tab Excel workbook.

---

## Key Files & Where to Find Things

### Execution Docs (START HERE)
- `E2E_EXECUTION_PLAN.md` — Step-by-step instructions to run the full pipeline end to end
- `ICP_DEFINITIONS.md` — All 19 ICP segments with signals, sources, and classification logic
- `PIPELINE_RUNBOOK.md` — Data flow, troubleshooting, memory management, known issues
- `OUTPUT_SPEC.md` — Final Excel format, column definitions, tab structure

### Research (Background Context)
- `DSCR_Research_Memo.md` — Core DSCR market intelligence, lender comparison, ICP universe
- `DSCR_Research_Memo_Part2.md` — Competitive landscape, referral ecosystem, LatAm buyers
- `Phase1_ICP_Sourcing_Playbook.md` — Tactical sourcing for each ICP: signal, source, method, cost
- `research/01-04_*.md` — Deep-dive research on product mechanics, ICPs, competition, market sizing

### Pipeline Code
- `pipeline/scripts/run_pipeline.py` — Master orchestrator (runs all steps)
- `pipeline/scripts/01_chunked_filter.py` — Step 1: FDOR property filter (memory-efficient)
- `pipeline/scripts/08_refi_simple.py` — Step 2: Refinance candidate detection
- `pipeline/scripts/02_sunbiz_resolve.py` — Step 3: LLC-to-human resolution via SunBiz
- `pipeline/scripts/03_dbpr_str.py` — Step 4: Vacation rental license tagging
- `pipeline/scripts/04_sec_edgar.py` — Step 5: SEC fund manager identification
- `pipeline/scripts/05_enrich_contacts.py` — Step 6: Phone/email enrichment
- `pipeline/scripts/06_score_and_output.py` — Step 7: ICP scoring + Excel generation

### Pipeline Module Docs
- `pipeline/01_fdor_property_data.md` through `pipeline/08_refi_candidates.md`
- `pipeline/README.md` — Architecture overview
- `pipeline/output_schema.md` — Output column schema

### Data Locations
- `pipeline/data/fdor/` — Florida DOR NAL property files (343MB+ per county)
- `pipeline/data/dbpr/` — DBPR vacation rental license CSV (126MB)
- `pipeline/data/sunbiz/` — SunBiz resolution cache (JSON)
- `pipeline/data/enrichment/` — Contact enrichment cache (JSON)
- `pipeline/output/` — Intermediate CSVs and final Excel

---

## Pipeline Execution Order

```
Step 1: FDOR Filter      → pipeline/output/01_investor_properties.csv
Step 2: Refi Detection    → pipeline/output/02_refi_tagged.csv
Step 3: SunBiz Resolve    → pipeline/output/03_resolved_entities.csv
Step 4: DBPR STR Tag      → pipeline/output/04_str_tagged.csv
Step 5: SEC EDGAR         → pipeline/output/05_fund_managers.csv
Step 6: Contact Enrich    → pipeline/output/06_enriched.csv
Step 7: Score + Excel     → pipeline/output/leads_YYYY-MM-DD.xlsx
```

See `E2E_EXECUTION_PLAN.md` for full execution commands.

---

## ICP Segments (Summary)

The pipeline identifies leads across **two major opportunity types**:

### Purchase Candidates (need DSCR for new acquisitions)
1. Individual Investors (1-10 properties) — Tier 1
2. Serial Investors (10+) — Tier 1
3. STR Operators — Tier 1
4. Foreign Nationals — Tier 1
5. Self-Employed Borrowers — Tier 1
6. BRRRR Strategy Investors — Tier 1
7. Corporate Entities (LLC/Trust) — Tier 1
8. HNWIs — Tier 2
9. Multi-Family (2-4 units) — Tier 2
10. 1031 Exchange Buyers — Tier 2
11. Recently Retired — Tier 2
12. Tax-Strategy Investors — Tier 2
13. Fund Managers / Syndicators — Tier 2

### Refinance Candidates (need DSCR to refi existing properties)
14. All-Cash Buyers (leverage-up via cash-out refi) — Tier 1
15. Equity Harvesters (30%+ equity, 2yr+ hold) — Tier 1
16. Rate Refi Candidates (2022-2023 vintage at 7-8%+) — Tier 2
17. BRRRR Exit (hard money to DSCR conversion) — Tier 1
18. Portfolio Equity Harvest (3+ properties, 35%+ avg equity) — Tier 1

### Niche Segments
19. Section 8 Landlords, First-Time Investors, Commercial Crossover, Diaspora, Digital Nomads, Accidental Landlords — Tier 3

See `ICP_DEFINITIONS.md` for complete signal definitions and classification logic.

---

## Critical Technical Notes

### Memory Management
- Palm Beach NAL file is 343MB / 654K rows — **MUST use chunked processing**
- Use `01_chunked_filter.py` (NOT `01_fdor_download_filter.py`) to avoid OOM kills
- Load only needed columns via `usecols` parameter
- Process in 50K-row chunks

### Rate Limiting
- SunBiz: 2-second delay between requests, max 500 lookups per run
- SEC EDGAR: 7 requests/second (limit is 10/sec)
- People search enrichment: 3-second delay
- All lookups use persistent caching (JSON files in `pipeline/data/`)

### Data Quality Known Issues
- FDOR `SALE_YR1`/`SALE_PRC1` reflects most recent sale only — no historical sale data
- Rate refi detection (2022-2023 vintage) limited by NAL only showing latest sale year
- Equity ratio is estimated (JV vs. sale price); no mortgage balance data from FDOR
- SunBiz web scraping may hit Cloudflare blocks — uses session cookies + retry
- DBPR matching is fuzzy (address normalization) — ~70-80% match rate expected

### Dependencies
```bash
pip install pandas openpyxl requests beautifulsoup4
```

---

## What "Free Method" Means

This pipeline uses only **free or freemium** data sources:
- **FDOR**: Free public records (FL Dept of Revenue)
- **SunBiz**: Free web search (FL Division of Corporations)
- **DBPR**: Free public records (FL Dept of Business & Professional Regulation)
- **SEC EDGAR**: Free public API (Securities and Exchange Commission)
- **People Search Sites**: Free ad-supported (TruePeopleSearch, FastPeopleSearch)
- **Apollo.io**: 10K free credits/month

No paid data vendors (PropStream, BatchLeads, AirDNA, etc.) are used in this pipeline. Those are referenced in the research docs as future enhancements.

---

## Contact & Ownership

- **Client**: Frank Christiano, CrossCountry Mortgage
- **Focus Market**: Florida, starting with Palm Beach County
- **Target Scale**: All 67 FL counties
- **Pipeline Date**: March 2026
