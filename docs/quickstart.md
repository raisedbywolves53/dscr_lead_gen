# QUICKSTART.md — How to Use These Files with Claude CLI

## Setup

1. Copy this entire `dscr_lead_gen/` folder into your local Projects directory
   - PC: `C:\Projects\dscr_lead_gen\`
   - Mac: `~/Projects/dscr_lead_gen/`

2. Open the folder in VS Code

3. Open a terminal in VS Code (Ctrl+` or Cmd+`)

---

## Prompts to Run in Claude CLI (copy/paste these)

### PROMPT 1: Scaffold the Project

Open Claude CLI in the `dscr_lead_gen` folder and paste:

```
Read CLAUDE.md, PIPELINE.md, and ICP_CRITERIA.md in this project folder. Then:

1. Create requirements.txt with all needed Python dependencies
2. Create .env.example with placeholder API keys
3. Create config/counties.json with the Florida county data sources listed in PIPELINE.md
4. Create config/scoring_weights.json based on the scoring matrix in ICP_CRITERIA.md
5. Create the folder structure (data/raw, data/parsed, data/filtered, data/enriched, data/validated, data/campaign_ready, scripts/, logs/)

Do NOT build the Python scripts yet. Just set up the project structure and config files.
```

### PROMPT 2: Build the NAL Parser (Step 1-2)

```
Read CLAUDE.md and PIPELINE.md. Build scripts/01_download_nal.py and scripts/02_parse_nal.py.

For 01_download_nal.py:
- Accept --county argument (e.g., "seminole", "sarasota", "all")
- For counties with free bulk downloads (from config/counties.json), download the files automatically
- For counties requiring email request (FL DOR NAL), print instructions on how to request the data
- Save raw files to data/raw/

For 02_parse_nal.py:
- Accept --county argument
- Read raw files from data/raw/
- Standardize into clean CSV format per the PIPELINE.md column spec
- Detect LLC/Corp owners, absentee owners, portfolio landlords
- Save to data/parsed/

Include clear print statements showing progress. Add comments explaining each section. I am not a developer — make the code readable.
```

### PROMPT 3: Build the ICP Filter (Step 3)

```
Read CLAUDE.md, PIPELINE.md, and ICP_CRITERIA.md. Build scripts/03_filter_icp.py.

- Accept --county argument
- Read from data/parsed/
- Apply the full scoring matrix from ICP_CRITERIA.md
- Score each record 0-100
- Assign tier (Tier 1: 50+, Tier 2: 30-49, Tier 3: 15-29, Discard: <15)
- List which ICP signals matched for each record
- Print summary stats: total records, records per tier, top ICP segments
- Save to data/filtered/

Use config/scoring_weights.json so I can adjust weights without editing code.
```

### PROMPT 4: Build the Sunbiz LLC Resolver (Step 4)

```
Read CLAUDE.md and PIPELINE.md. Build scripts/04_sunbiz_llc_resolver.py.

- Accept --county argument
- Read LLC-flagged records from data/filtered/
- For each LLC, search sunbiz.org to find registered agent, officers, and filing info
- Rate limit: 1 request per 3 seconds with exponential backoff if blocked
- Save progress after every 50 records (so we can resume if interrupted)
- Save results to data/filtered/{county}_llc_resolved.csv

Important: Sunbiz may use JavaScript rendering. If basic requests fail, try using their search API endpoint directly. Check the network tab pattern: the search URL is https://search.sunbiz.org/Inquiry/CorporationSearch/SearchByName
```

### PROMPT 5: Build the Contact Enrichment Pipeline (Step 5)

```
Read CLAUDE.md and PIPELINE.md. Build scripts/05_enrich_contacts.py.

This script should try FREE sources first, then cheap paid sources as fallback:

Source A (FREE): If we have a Florida voter registration file in data/raw/voter_file.csv, match owner names against it to get phone numbers.

Source B (FREE): For unmatched records, generate likely email patterns from the owner's name (if we resolved an LLC to a human via Sunbiz). Pattern: firstname@domain, first.last@domain, flast@domain.

Source C (CHEAP FALLBACK): For still-unmatched records, export a CSV formatted for upload to Datazapp.com (3 cents per match). Print instructions for how to upload and download results.

Save enriched records to data/enriched/

Print stats: how many matched from each source, how many still unmatched.
```

### PROMPT 6: Build Validation + Export (Steps 6-7)

```
Read CLAUDE.md and PIPELINE.md. Build scripts/06_validate_contacts.py and scripts/07_export_campaign_ready.py.

For 06_validate_contacts.py:
- Validate emails using MillionVerifier API (needs API key in .env)
- Validate phones using Twilio Lookup API (needs credentials in .env)
- Check phones against DNC list if available
- If no API keys configured, skip validation and just pass data through with a warning
- Save to data/validated/

For 07_export_campaign_ready.py:
- Read from data/validated/
- Export separate files for: email campaigns (Instantly format), SMS/dialer, direct mail, Apollo import
- Split by ICP tier (Tier 1 and Tier 2 get separate files)
- Save to data/campaign_ready/
- Print final summary: total leads by tier, by channel, with contact coverage stats
```

---

## Running the Full Pipeline

After all scripts are built, run the pipeline for a county:

```bash
cd C:\Projects\dscr_lead_gen  # or ~/Projects/dscr_lead_gen on Mac

python scripts/01_download_nal.py --county seminole
python scripts/02_parse_nal.py --county seminole
python scripts/03_filter_icp.py --county seminole
python scripts/04_sunbiz_llc_resolver.py --county seminole
python scripts/05_enrich_contacts.py --county seminole
python scripts/06_validate_contacts.py --county seminole
python scripts/07_export_campaign_ready.py --county seminole
```

Or run all at once:
```bash
python scripts/01_download_nal.py --county seminole && \
python scripts/02_parse_nal.py --county seminole && \
python scripts/03_filter_icp.py --county seminole && \
python scripts/04_sunbiz_llc_resolver.py --county seminole && \
python scripts/05_enrich_contacts.py --county seminole && \
python scripts/06_validate_contacts.py --county seminole && \
python scripts/07_export_campaign_ready.py --county seminole
```

---

## Tips

- **Start with Seminole County** — it has free daily-updated Excel downloads, making it the easiest to test with
- **You need the NAL file first** — email PTOTechnology@floridarevenue.com ASAP requesting statewide NAL files. This is the single most important data source.
- **Datazapp is your best friend for skip tracing** — at 3¢/record with no subscription, it's the cheapest way to fill gaps the free sources miss
- **Don't skip the DNC check** — calling numbers on the Do Not Call list can result in $43,000+ fines per violation
- **Run Sunbiz lookups overnight** — the rate limiting means it's slow. Start it before bed.
