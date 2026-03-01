# Pipeline Runbook — Troubleshooting, Data Flow & Known Issues

## Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                     EXTERNAL DATA SOURCES                       │
├─────────────────────────────────────────────────────────────────┤
│ FDOR NAL (FL DOR)    │ DBPR Licenses │ SunBiz  │ SEC EDGAR    │
│ 343MB/county         │ 126MB total   │ Web     │ API          │
│ 654K parcels (PB)    │ 60K+ licenses │ Scrape  │ Form D       │
└────────┬─────────────┴──────┬────────┴────┬────┴──────┬───────┘
         │                    │             │           │
         ▼                    │             │           │
┌─────────────────────┐       │             │           │
│ STEP 1: FDOR Filter │       │             │           │
│ 01_chunked_filter.py│       │             │           │
│ 654K → 189K owners  │       │             │           │
└────────┬────────────┘       │             │           │
         ▼                    │             │           │
┌─────────────────────┐       │             │           │
│ STEP 2: Refi Detect │       │             │           │
│ 08_refi_simple.py   │       │             │           │
│ 189K → 14K flagged  │       │             │           │
└────────┬────────────┘       │             │           │
         ▼                    │             │           │
┌─────────────────────┐       │             │           │
│ STEP 3: SunBiz      │◄─────┼─────────────┘           │
│ 02_sunbiz_resolve.py│       │                         │
│ 500 entity lookups  │       │                         │
└────────┬────────────┘       │                         │
         ▼                    │                         │
┌─────────────────────┐       │                         │
│ STEP 4: DBPR STR    │◄──────┘                         │
│ 03_dbpr_str.py      │                                 │
│ License matching     │                                 │
└────────┬────────────┘                                 │
         │                                              │
         │              ┌─────────────────────┐         │
         │              │ STEP 5: SEC EDGAR   │◄────────┘
         │              │ 04_sec_edgar.py      │
         │              │ Fund manager search  │
         │              └────────┬────────────┘
         ▼                       │
┌─────────────────────┐          │
│ STEP 6: Enrichment  │          │
│ 05_enrich_contacts  │          │
│ 500 phone/email     │          │
└────────┬────────────┘          │
         ▼                       ▼
┌─────────────────────────────────────┐
│ STEP 7: Score + Excel Output       │
│ 06_score_and_output.py             │
│ Merge EDGAR + Classify + Score     │
│ → leads_YYYY-MM-DD.xlsx           │
└─────────────────────────────────────┘
```

---

## File Dependencies

Each step reads from the previous step's output:

| Step | Script | Reads | Writes |
|------|--------|-------|--------|
| 1 | 01_chunked_filter.py | pipeline/data/fdor/NAL_60_PALM_BEACH.csv | pipeline/output/01_investor_properties.csv |
| 2 | 08_refi_simple.py | 01_investor_properties.csv | 02_refi_tagged.csv |
| 3 | 02_sunbiz_resolve.py | 02_refi_tagged.csv | 03_resolved_entities.csv |
| 4 | 03_dbpr_str.py | 03_resolved_entities.csv | 04_str_tagged.csv |
| 5 | 04_sec_edgar.py | (SEC API) | 05_fund_managers.csv |
| 6 | 05_enrich_contacts.py | 04_str_tagged.csv | 06_enriched.csv |
| 7 | 06_score_and_output.py | 06_enriched.csv + 05_fund_managers.csv | leads_YYYY-MM-DD.xlsx |

**If you skip a step**, copy the previous step's output to the expected input filename:
```bash
# Example: skip SunBiz (Step 3) and DBPR (Step 4)
cp pipeline/output/02_refi_tagged.csv pipeline/output/04_str_tagged.csv
```

---

## Cache Files

Caches persist across runs to avoid redundant API calls:

| Cache | Location | Purpose | Safe to Delete? |
|-------|----------|---------|-----------------|
| SunBiz | pipeline/data/sunbiz/resolution_cache.json | Entity → person resolution results | Yes (will re-scrape) |
| Enrichment | pipeline/data/enrichment/enrichment_cache.json | Phone/email lookup results | Yes (will re-search) |

Caches are cumulative — increasing `--max-lookups` on a re-run only processes NEW uncached entries.

---

## Memory Management

### The Problem
Palm Beach NAL file is 343MB / 654K rows. Loading it all at once with pandas causes OOM kills in memory-constrained environments.

### The Solution
`01_chunked_filter.py` processes in 50K-row chunks with `usecols` to load only needed columns:

```python
USE_COLS = [
    'CO_NO', 'PARCEL_ID', 'DOR_UC', 'JV', 'AV_HMSTD',
    'OWN_NAME', 'OWN_ADDR1', 'OWN_ADDR2', 'OWN_CITY', 'OWN_STATE', 'OWN_ZIPCD',
    'OWN_STATE_DOM',
    'PHY_ADDR1', 'PHY_ADDR2', 'PHY_CITY', 'PHY_ZIPCD',
    'SALE_PRC1', 'SALE_YR1', 'SALE_MO1',
]
```

This reduces memory from ~1.5GB to ~200MB per chunk.

### DO NOT USE
`01_fdor_download_filter.py` — the original full-load version. It will OOM on large county files.

---

## Known Issues & Limitations

### 1. Sale Date Aggregation Bias
**Issue**: Owner-level aggregation uses `max()` on sale dates, so only the most recent sale date per owner is preserved. If an owner bought in 2022 and again in 2024, only 2024 appears.
**Impact**: Rate refi detection (2022-2023 vintage) undercounts. BRRRR detection may miss older rehab purchases.
**Workaround**: Run refi detection at property level before aggregation (future enhancement).

### 2. Column Name Mismatch After Aggregation
**Issue**: Pandas MultiIndex flattening can produce `sale_date_max` instead of `most_recent_purchase`.
**Fix**: Run the column rename step after Step 1 (see E2E_EXECUTION_PLAN.md).

### 3. No Mortgage Data
**Issue**: FDOR NAL does not include mortgage information. Equity ratio is estimated from JV (Just Value) vs. SALE_PRC1 (last sale price).
**Impact**: Cannot confirm free-and-clear status, actual mortgage balance, or lender identity.
**Future Fix**: Integrate county Clerk of Court mortgage recording data or ATTOM Data Solutions.

### 4. SunBiz Cloudflare Blocking
**Issue**: SunBiz.org uses Cloudflare protection. Aggressive scraping triggers blocks.
**Mitigation**: Session cookies, 2-second delays, max 500 lookups per run.
**Signs of blocking**: Empty results, HTTP 403 errors, CAPTCHA pages.
**Recovery**: Wait 30-60 minutes, or use a different IP/VPN.

### 5. People Search Rate Limits
**Issue**: TruePeopleSearch and FastPeopleSearch may block or require CAPTCHA after too many requests.
**Mitigation**: 3-second delays, max 500 lookups per run, caching.
**Fallback**: Apollo.io API (requires free API key — 10K credits/month).

### 6. DBPR Address Matching
**Issue**: DBPR licensee addresses don't always exactly match FDOR property addresses (different formatting, abbreviations).
**Mitigation**: Address normalization (ST→STREET, DR→DRIVE, etc.) and fuzzy matching.
**Expected Match Rate**: ~70-80% of actual STR operators correctly tagged.

### 7. FDOR Data Freshness
**Issue**: NAL files are published annually (January). Data may be 1-12 months stale.
**Impact**: Recent sales, new LLC formations, and ownership transfers may not appear.
**Workaround**: Supplement with county property appraiser web searches for real-time data.

### 8. Large Entity Owner Aggregation
**Issue**: Some entity names (e.g., "INVITATION HOMES") own hundreds of properties, creating very high property_count values. These are institutional owners, not the target ICP.
**Impact**: Inflates serial investor counts. May dominate "top leads" by score.
**Future Fix**: Add institutional owner filter (property_count > 50 = institutional, exclude or flag differently).

---

## Error Recovery

### Step Failed Mid-Run
All steps write output atomically at the end. If a step crashes:
1. The previous step's output is still valid
2. Re-run the failed step from its input file
3. Cache files preserve partial progress (SunBiz, enrichment)

### Need to Re-Run a Single Step
Change the `--input` and `--output` flags to point to the correct files:
```bash
# Example: Re-run only DBPR tagging
python pipeline/scripts/03_dbpr_str.py \
  --input pipeline/output/03_resolved_entities.csv \
  --output pipeline/output/04_str_tagged.csv
```

### Pipeline Freezes / Times Out
Common causes:
- **SunBiz step**: Web scraping is slow (2s per lookup × 500 = 17 min). Normal.
- **Enrichment step**: People search can be slow (3s per lookup × 500 = 25 min). Normal.
- **FDOR download**: Downloading 343MB NAL ZIP can timeout. Use pre-downloaded files.

If a session freezes:
1. Check if output file was written (partial or complete)
2. If partial, the caches saved progress — re-run with same parameters
3. If no output, re-run from the last successful step's output

---

## Performance Benchmarks

| Step | Records | Runtime | Memory |
|------|---------|---------|--------|
| 1: FDOR Filter | 654K parcels → 189K owners | 2-3 min | ~300MB peak |
| 2: Refi Detection | 189K owners | 3-5 min | ~400MB |
| 3: SunBiz (500) | 500 lookups | ~17 min | ~400MB + network |
| 4: DBPR STR | 189K × 60K cross-ref | 2-5 min | ~500MB |
| 5: SEC EDGAR | API queries | 2-5 min | minimal |
| 6: Enrichment (500) | 500 lookups | ~25 min | ~400MB + network |
| 7: Score + Excel | 189K leads | 5-10 min | ~500MB |
| **Total** | | **~60 min** | **~500MB peak** |

---

## Adding New Counties

1. Download NAL file from FDOR:
   ```
   https://floridarevenue.com/property/Documents/NAL_{CO_NO}_{COUNTY_NAME}.zip
   ```

2. Place in `pipeline/data/fdor/`

3. Update `01_chunked_filter.py`:
   ```python
   NAL_FILE = Path("pipeline/data/fdor/NAL_XX_COUNTY_NAME.csv")
   ```
   Or modify to loop over multiple NAL files.

4. County codes (CO_NO) reference:
   - 16: BROWARD
   - 23: MIAMI-DADE
   - 26: DUVAL (Jacksonville)
   - 39: HILLSBOROUGH (Tampa)
   - 58: ORANGE (Orlando)
   - 59: OSCEOLA (Kissimmee — STR hub)
   - 60: PALM BEACH
   - 62: PINELLAS (St. Pete)

5. Re-run full pipeline from Step 1.

---

## Environment Variables (Optional)

```bash
# Apollo.io API key (for email enrichment)
export APOLLO_API_KEY="your_key_here"

# Hunter.io API key (for email finder)
export HUNTER_API_KEY="your_key_here"
```

Neither is required — the pipeline works with free people search sites as the primary enrichment method.
