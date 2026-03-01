# End-to-End Execution Plan — DSCR Lead Pipeline

## Purpose

This document provides exact, copy-paste commands to run the full pipeline from raw FDOR data to a scored, segmented, contact-enriched Excel workbook. Designed so Claude CLI can execute without additional context.

---

## Prerequisites

```bash
cd /sessions/keen-wonderful-tesla/mnt/dscr_lead_gen
pip install pandas openpyxl requests beautifulsoup4
```

Verify data files exist:
```bash
ls -lh pipeline/data/fdor/NAL_60_PALM_BEACH.csv    # ~343MB expected
ls -lh pipeline/data/dbpr/dbpr_vacation_rentals.csv  # ~126MB expected
```

If FDOR data is missing, Step 1's original script (`01_fdor_download_filter.py`) will attempt to download from `https://floridarevenue.com/property/Documents/` — but this is 343MB per county and may timeout. Download manually if needed.

---

## Pipeline Steps

### Step 1: FDOR Property Filter (Palm Beach County)

**Script**: `pipeline/scripts/01_chunked_filter.py`
**Input**: `pipeline/data/fdor/NAL_60_PALM_BEACH.csv` (343MB, 654K parcels)
**Output**: `pipeline/output/01_investor_properties.csv`

**What it does**:
- Reads NAL file in 50K-row chunks (avoids OOM on 343MB file)
- Filters for residential use codes (SFR, mobile, 2-9 units, condo, 10+ units)
- Removes homesteaded properties (primary residences)
- Flags: entity ownership, absentee owner, out-of-state, foreign owner
- Aggregates by owner: property count, portfolio value, most recent sale date/price
- Carries forward SALE_PRC1, SALE_YR1, SALE_MO1 for refi detection

**Command**:
```bash
python pipeline/scripts/01_chunked_filter.py
```

**Expected output**: ~189K unique owner leads, ~50K entity-owned, ~8K foreign owners, ~12K multi-property (2+)

**Runtime**: 2-3 minutes

**Verify**:
```bash
wc -l pipeline/output/01_investor_properties.csv
head -1 pipeline/output/01_investor_properties.csv  # should include most_recent_purchase column
```

**IMPORTANT**: If `most_recent_purchase` column is named `sale_date_max`, rename it:
```python
python -c "
import pandas as pd
df = pd.read_csv('pipeline/output/01_investor_properties.csv', dtype=str, low_memory=False)
if 'sale_date_max' in df.columns and 'most_recent_purchase' not in df.columns:
    df.rename(columns={'sale_date_max': 'most_recent_purchase'}, inplace=True)
    df.to_csv('pipeline/output/01_investor_properties.csv', index=False)
    print('Column renamed successfully')
"
```

---

### Step 2: Refinance Candidate Detection

**Script**: `pipeline/scripts/08_refi_simple.py`
**Input**: `pipeline/output/01_investor_properties.csv`
**Output**: `pipeline/output/02_refi_tagged.csv`

**What it does**:
- Analyzes each owner for 6 refinance signals:
  1. **High Equity (30%+)**: current value vs. purchase price appreciation
  2. **Probable All-Cash Buyer**: equity ratio 90%+ and price > $100K
  3. **Long Hold Period**: 2yr+ hold with 25%+ equity (equity harvesting)
  4. **Rate Refi Candidate**: purchased 2022-2023 at peak rates (7-8%+)
  5. **BRRRR Exit**: purchased 30%+ below county median within 12 months
  6. **Portfolio Equity Harvest**: 3+ properties with 35%+ average equity
- Adds refi_score_boost (0-40 points) for downstream scoring
- Classifies refi priority: High / Medium / Low

**Command**:
```bash
python pipeline/scripts/08_refi_simple.py \
  --input pipeline/output/01_investor_properties.csv \
  --output pipeline/output/02_refi_tagged.csv
```

**Expected output**: ~14K leads with refi signals (7-8%), ~4K high priority, $5B+ total cash-out potential

**Runtime**: 3-5 minutes

---

### Step 3: SunBiz Entity Resolution

**Script**: `pipeline/scripts/02_sunbiz_resolve.py`
**Input**: `pipeline/output/02_refi_tagged.csv`
**Output**: `pipeline/output/03_resolved_entities.csv`
**Cache**: `pipeline/data/sunbiz/resolution_cache.json` (persists across runs)

**What it does**:
- Identifies entity-owned properties (LLC, Corp, Trust in owner name)
- Searches sunbiz.org for each entity to find registered agent, officers, directors
- Resolves entity to human owner name (prefers Manager/President/CEO)
- Caches results — subsequent runs skip already-resolved entities
- Rate limited: 2-second delay between requests

**Command**:
```bash
python pipeline/scripts/02_sunbiz_resolve.py \
  --input pipeline/output/02_refi_tagged.csv \
  --output pipeline/output/03_resolved_entities.csv \
  --max-lookups 500
```

**Expected output**: 70-80% resolution rate on looked-up entities. Adds resolved_person, registered_agent, entity_officers columns.

**Runtime**: ~17 minutes at 500 lookups (2s delay each). Uses cache for previously resolved entities.

**Notes**:
- SunBiz may block after many requests — session cookies help
- Cache is cumulative; safe to re-run with higher `--max-lookups` later
- Prioritizes entities that own the most properties (biggest investors first)

---

### Step 4: DBPR STR Operator Tagging

**Script**: `pipeline/scripts/03_dbpr_str.py`
**Input**: `pipeline/output/03_resolved_entities.csv`
**Output**: `pipeline/output/04_str_tagged.csv`
**Data**: `pipeline/data/dbpr/dbpr_vacation_rentals.csv`

**What it does**:
- Loads FL DBPR vacation rental license database (60K+ licenses)
- Cross-references licensee names and addresses against property owner leads
- Fuzzy address matching (normalizes ST/STREET, DR/DRIVE, etc.)
- Extracts phone and email from DBPR records when available
- Tags STR-licensed leads and counts licenses per owner

**Command**:
```bash
python pipeline/scripts/03_dbpr_str.py \
  --input pipeline/output/03_resolved_entities.csv \
  --output pipeline/output/04_str_tagged.csv
```

**Expected output**: 2-5% of leads tagged as STR licensed (Palm Beach has moderate STR activity). Adds str_licensed, str_license_count, str_phone, str_email columns.

**Runtime**: 2-5 minutes

---

### Step 5: SEC EDGAR Fund Manager Identification

**Script**: `pipeline/scripts/04_sec_edgar.py`
**Input**: N/A (queries SEC EDGAR API directly)
**Output**: `pipeline/output/05_fund_managers.csv`

**What it does**:
- Queries SEC EDGAR full-text search for FL real estate fund filings (Form D)
- Search terms: "real estate", "rental property", "investment property", etc.
- Filters for FL-based issuers
- Extracts: fund name, GP name, offering amount, phone, related persons
- Rate limited: 7 requests/second (SEC limit is 10/sec)

**Command**:
```bash
python pipeline/scripts/04_sec_edgar.py \
  --output pipeline/output/05_fund_managers.csv \
  --state FL \
  --max-results 200
```

**Expected output**: 50-200 FL real estate fund filings with GP names and contact info

**Runtime**: 2-5 minutes

**Notes**:
- EDGAR can be slow; --max-results controls how many filings to fetch
- Fund managers are added as separate leads AND cross-matched to property owners in Step 7
- Can be skipped with `--skip-edgar` if not needed for test runs

---

### Step 6: Free Contact Enrichment

**Script**: `pipeline/scripts/05_enrich_contacts.py`
**Input**: `pipeline/output/04_str_tagged.csv`
**Output**: `pipeline/output/06_enriched.csv`
**Cache**: `pipeline/data/enrichment/enrichment_cache.json`

**What it does**:
- Attempts to find phone and email for leads using free sources:
  1. DBPR data (already extracted in Step 4)
  2. TruePeopleSearch.com (web scraping)
  3. FastPeopleSearch.com (web scraping)
  4. Apollo.io free tier API (if API key set)
  5. Hunter.io free tier (if API key set)
- Cleans owner names: removes entity suffixes, handles "LAST, FIRST" format
- Rate limited: 3-second delay between people search lookups
- Results cached to avoid repeat lookups

**Command**:
```bash
python pipeline/scripts/05_enrich_contacts.py \
  --input pipeline/output/04_str_tagged.csv \
  --output pipeline/output/06_enriched.csv \
  --max-lookups 500
```

**Expected output**: 40-60% of looked-up leads get phone or email. Adds phone, email, enrichment_source columns.

**Runtime**: ~25 minutes at 500 lookups (3s delay each)

**Notes**:
- People search sites may block or require CAPTCHA — enrichment is best-effort
- Apollo.io requires `APOLLO_API_KEY` env variable for API enrichment
- Cache is cumulative; safe to increase `--max-lookups` on re-runs
- Individual (non-entity) owners have higher enrichment success rate

---

### Step 7: ICP Scoring & Excel Output

**Script**: `pipeline/scripts/06_score_and_output.py`
**Input**: `pipeline/output/06_enriched.csv` + `pipeline/output/05_fund_managers.csv`
**Output**: `pipeline/output/leads_YYYY-MM-DD.xlsx`

**What it does**:
1. **Merges** SEC EDGAR fund data with property owner leads
2. **Classifies** each lead into primary ICP segment + secondary tag + tier (1-3)
3. **Scores** each lead 0-100 based on:
   - Property count (0-25)
   - Purchase recency (0-20)
   - Portfolio value (0-15)
   - Entity sophistication (0-10)
   - STR indicator (0-10)
   - Geographic fit (0-10)
   - Contact availability (0-10)
   - Refi score boost (0-40, from Step 2)
4. **Generates** multi-tab Excel workbook:
   - `All Leads` tab — master list sorted by score
   - Per-ICP segment tabs — filtered views
   - `Summary` tab — statistics dashboard

**Command**:
```bash
python pipeline/scripts/06_score_and_output.py \
  --input pipeline/output/06_enriched.csv \
  --edgar-input pipeline/output/05_fund_managers.csv \
  --output pipeline/output/leads_$(date +%Y-%m-%d).xlsx
```

**Expected output**: 189K+ lead Excel with 10+ tabs, scores 0-100, ICP classifications

**Runtime**: 5-10 minutes

---

## Quick Test Run (Fastest Path)

Skip SunBiz, EDGAR, and enrichment for a fast test of data flow:

```bash
cd /sessions/keen-wonderful-tesla/mnt/dscr_lead_gen

# Step 1: FDOR filter
python pipeline/scripts/01_chunked_filter.py

# Fix column name if needed
python -c "
import pandas as pd
df = pd.read_csv('pipeline/output/01_investor_properties.csv', dtype=str, low_memory=False)
if 'sale_date_max' in df.columns:
    df.rename(columns={'sale_date_max': 'most_recent_purchase'}, inplace=True)
    df.to_csv('pipeline/output/01_investor_properties.csv', index=False)
"

# Step 2: Refi detection
python pipeline/scripts/08_refi_simple.py

# Steps 3-6: Copy through (no SunBiz/DBPR/EDGAR/enrichment)
cp pipeline/output/02_refi_tagged.csv pipeline/output/06_enriched.csv

# Step 7: Score + Excel (with empty EDGAR file)
touch pipeline/output/05_fund_managers.csv
python pipeline/scripts/06_score_and_output.py \
  --input pipeline/output/06_enriched.csv \
  --output pipeline/output/leads_$(date +%Y-%m-%d).xlsx
```

**Runtime**: ~10 minutes total

---

## Full Run (All Steps)

```bash
cd /sessions/keen-wonderful-tesla/mnt/dscr_lead_gen

# Step 1
python pipeline/scripts/01_chunked_filter.py

# Column fix
python -c "
import pandas as pd
df = pd.read_csv('pipeline/output/01_investor_properties.csv', dtype=str, low_memory=False)
if 'sale_date_max' in df.columns:
    df.rename(columns={'sale_date_max': 'most_recent_purchase'}, inplace=True)
    df.to_csv('pipeline/output/01_investor_properties.csv', index=False)
"

# Step 2
python pipeline/scripts/08_refi_simple.py

# Step 3 (17 min)
python pipeline/scripts/02_sunbiz_resolve.py \
  --input pipeline/output/02_refi_tagged.csv \
  --output pipeline/output/03_resolved_entities.csv \
  --max-lookups 500

# Step 4
python pipeline/scripts/03_dbpr_str.py \
  --input pipeline/output/03_resolved_entities.csv \
  --output pipeline/output/04_str_tagged.csv

# Step 5
python pipeline/scripts/04_sec_edgar.py \
  --output pipeline/output/05_fund_managers.csv \
  --state FL --max-results 200

# Step 6 (25 min)
python pipeline/scripts/05_enrich_contacts.py \
  --input pipeline/output/04_str_tagged.csv \
  --output pipeline/output/06_enriched.csv \
  --max-lookups 500

# Step 7
python pipeline/scripts/06_score_and_output.py \
  --input pipeline/output/06_enriched.csv \
  --edgar-input pipeline/output/05_fund_managers.csv \
  --output pipeline/output/leads_$(date +%Y-%m-%d).xlsx
```

**Total runtime**: ~60 minutes

---

## Multi-County Expansion

To run for South Florida (3 counties):

1. Download additional NAL files to `pipeline/data/fdor/`:
   - `NAL_16_BROWARD.csv` (county code 16)
   - `NAL_23_MIAMI_DADE.csv` (county code 23)

2. Modify `01_chunked_filter.py` to process all files:
   ```python
   NAL_FILES = [
       Path("pipeline/data/fdor/NAL_60_PALM_BEACH.csv"),
       Path("pipeline/data/fdor/NAL_16_BROWARD.csv"),
       Path("pipeline/data/fdor/NAL_23_MIAMI_DADE.csv"),
   ]
   ```

3. Or use the original `01_fdor_download_filter.py` with county flag:
   ```bash
   python pipeline/scripts/01_fdor_download_filter.py --counties "PALM BEACH,BROWARD,MIAMI-DADE"
   ```
   (Warning: may OOM on multiple large counties — use chunked version)

---

## Validation Checklist

After full run, verify:

- [ ] `01_investor_properties.csv` has columns: OWN_NAME, property_count, total_portfolio_value, most_recent_purchase, most_recent_price, is_entity, out_of_state, foreign_owner
- [ ] `02_refi_tagged.csv` has columns: refi_signals, refi_priority, refi_score_boost, probable_cash_buyer, brrrr_exit_candidate, equity_harvest_candidate
- [ ] `03_resolved_entities.csv` has columns: resolved_person, registered_agent, entity_officers
- [ ] `04_str_tagged.csv` has columns: str_licensed, str_license_count
- [ ] `06_enriched.csv` has columns: phone, email, enrichment_source
- [ ] Final Excel has tabs: All Leads, per-ICP segments, Summary
- [ ] Score distribution: mean ~30-40, top leads 70+
- [ ] ICP segments present: Serial Investor, STR Operator, Entity-Based, Individual Investor, Out-of-State, Foreign National
- [ ] Refi candidates: probable_cash_buyer, brrrr_exit_candidate, equity_harvest_candidate tagged in icp_secondary
