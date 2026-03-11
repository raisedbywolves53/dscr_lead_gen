# Module 7: Pipeline Orchestrator

## Purpose
Single-command execution of the full lead generation pipeline. Downloads data, filters, resolves entities, tags STR operators, enriches contacts, scores leads, and outputs the final Excel spreadsheet.

## Script: `scripts/run_pipeline.py`

```python
"""
DSCR Lead Generation Pipeline — Master Orchestrator

Runs the full pipeline end-to-end:
1. Download & filter FDOR property data
2. Resolve entity owners via SunBiz
3. Tag STR operators via DBPR
4. Identify fund managers via SEC EDGAR
5. Enrich contacts (phone/email)
6. Score, classify, and output to Excel

Usage:
    # Test run — single county, minimal enrichment
    python pipeline/scripts/run_pipeline.py --counties "PALM BEACH" --max-enrichment 100

    # Full South FL run
    python pipeline/scripts/run_pipeline.py --counties "PALM BEACH,BROWARD,MIAMI-DADE" --max-enrichment 500

    # All 67 counties (takes hours)
    python pipeline/scripts/run_pipeline.py --all-counties --max-enrichment 2000

    # With Apollo.io enrichment
    python pipeline/scripts/run_pipeline.py --counties "PALM BEACH" --apollo-key YOUR_KEY
"""

import os
import sys
import argparse
import subprocess
from pathlib import Path
from datetime import date

# Add scripts directory to path
SCRIPTS_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPTS_DIR))

# Import pipeline modules
# These will be available once the individual scripts are extracted
# from the .md documentation files into standalone .py files


def ensure_directories():
    """Create required directories."""
    dirs = [
        'pipeline/data/fdor',
        'pipeline/data/sunbiz',
        'pipeline/data/dbpr',
        'pipeline/data/edgar',
        'pipeline/data/enrichment',
        'pipeline/output',
    ]
    for d in dirs:
        Path(d).mkdir(parents=True, exist_ok=True)


def install_dependencies():
    """Ensure required Python packages are installed."""
    required = ['pandas', 'openpyxl', 'requests', 'beautifulsoup4']
    for pkg in required:
        try:
            __import__(pkg.replace('-', '_').split('[')[0])
        except ImportError:
            print(f"Installing {pkg}...")
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', pkg, '-q'])


def run_step(step_num: int, description: str, script: str, args: list):
    """Run a pipeline step and report results."""
    print(f"\n{'='*70}")
    print(f"STEP {step_num}: {description}")
    print(f"{'='*70}\n")

    cmd = [sys.executable, script] + args
    result = subprocess.run(cmd, capture_output=False)

    if result.returncode != 0:
        print(f"\nWARNING: Step {step_num} exited with code {result.returncode}")
        print("Continuing to next step...")

    return result.returncode == 0


def main():
    parser = argparse.ArgumentParser(description='DSCR Lead Gen Pipeline — Full Run')
    parser.add_argument('--counties', type=str, default='PALM BEACH',
                        help='Comma-separated county names')
    parser.add_argument('--all-counties', action='store_true',
                        help='Process all 67 FL counties')
    parser.add_argument('--max-sunbiz', type=int, default=500,
                        help='Max SunBiz entity lookups')
    parser.add_argument('--max-enrichment', type=int, default=500,
                        help='Max contact enrichment lookups')
    parser.add_argument('--apollo-key', type=str, default='',
                        help='Apollo.io API key for business email enrichment')
    parser.add_argument('--skip-edgar', action='store_true',
                        help='Skip SEC EDGAR step')
    parser.add_argument('--skip-enrichment', action='store_true',
                        help='Skip contact enrichment step')
    parser.add_argument('--output', type=str,
                        default=f'pipeline/output/leads_{date.today().isoformat()}.xlsx',
                        help='Output Excel file path')

    args = parser.parse_args()

    print(f"""
╔══════════════════════════════════════════════════════════════╗
║        DSCR LEAD GENERATION PIPELINE                        ║
║        Target: Florida Investment Property Owners            ║
║        Date: {date.today().isoformat()}                                     ║
╠══════════════════════════════════════════════════════════════╣
║  Counties: {args.counties if not args.all_counties else 'ALL 67 FL COUNTIES':<47} ║
║  Max SunBiz lookups: {args.max_sunbiz:<37} ║
║  Max enrichment lookups: {args.max_enrichment:<33} ║
║  Apollo.io: {'Enabled' if args.apollo_key else 'Disabled':<46} ║
║  Output: {args.output:<50} ║
╚══════════════════════════════════════════════════════════════╝
    """)

    ensure_directories()
    install_dependencies()

    scripts_dir = str(SCRIPTS_DIR)

    # Step 1: FDOR Property Data
    county_args = ['--all-counties'] if args.all_counties else ['--counties', args.counties]
    run_step(1, "FDOR Property Data — Download & Filter",
             f"{scripts_dir}/01_fdor_download_filter.py",
             county_args + ['--output', 'pipeline/output/01_investor_properties.csv'])

    # Step 2: SunBiz Entity Resolution
    run_step(2, "SunBiz Entity Resolution",
             f"{scripts_dir}/02_sunbiz_resolve.py",
             ['--input', 'pipeline/output/01_investor_properties.csv',
              '--output', 'pipeline/output/02_resolved_entities.csv',
              '--max-lookups', str(args.max_sunbiz)])

    # Step 3: DBPR STR Operator Tagging
    run_step(3, "DBPR STR Operator Identification",
             f"{scripts_dir}/03_dbpr_str.py",
             ['--input', 'pipeline/output/02_resolved_entities.csv',
              '--output', 'pipeline/output/03_str_tagged.csv'])

    # Step 4: SEC EDGAR (optional)
    if not args.skip_edgar:
        run_step(4, "SEC EDGAR — FL Real Estate Fund Identification",
                 f"{scripts_dir}/04_sec_edgar.py",
                 ['--output', 'pipeline/output/04_fund_managers.csv',
                  '--fetch-details'])
    else:
        print("\nStep 4: SEC EDGAR — SKIPPED")

    # Step 5: Contact Enrichment (optional)
    if not args.skip_enrichment:
        enrich_args = ['--input', 'pipeline/output/03_str_tagged.csv',
                       '--output', 'pipeline/output/05_enriched.csv',
                       '--max-lookups', str(args.max_enrichment)]
        if args.apollo_key:
            enrich_args += ['--apollo-key', args.apollo_key]

        run_step(5, "Contact Enrichment",
                 f"{scripts_dir}/05_enrich_contacts.py",
                 enrich_args)
    else:
        print("\nStep 5: Contact Enrichment — SKIPPED")
        # Copy input directly to enrichment output
        import shutil
        shutil.copy('pipeline/output/03_str_tagged.csv',
                     'pipeline/output/05_enriched.csv')

    # Step 6: Scoring & Excel Output
    run_step(6, "ICP Scoring & Excel Output",
             f"{scripts_dir}/06_score_and_output.py",
             ['--input', 'pipeline/output/05_enriched.csv',
              '--edgar-input', 'pipeline/output/04_fund_managers.csv',
              '--output', args.output])

    print(f"""
╔══════════════════════════════════════════════════════════════╗
║                    PIPELINE COMPLETE                         ║
║                                                              ║
║  Output: {args.output:<50}║
║                                                              ║
║  Next steps:                                                 ║
║  1. Open the Excel file and review lead quality              ║
║  2. Check Summary tab for coverage stats                     ║
║  3. Focus on Tier 1 leads with score 70+                     ║
║  4. Increase --max-enrichment for more contacts              ║
╚══════════════════════════════════════════════════════════════╝
    """)


if __name__ == '__main__':
    main()
```

## Quick Start

### Minimal Test (5 minutes)
```bash
python pipeline/scripts/run_pipeline.py \
    --counties "PALM BEACH" \
    --max-sunbiz 50 \
    --max-enrichment 50 \
    --skip-edgar
```

### Standard Run — South FL (30-60 minutes)
```bash
python pipeline/scripts/run_pipeline.py \
    --counties "PALM BEACH,BROWARD,MIAMI-DADE" \
    --max-sunbiz 500 \
    --max-enrichment 500
```

### Full State Run (2-4 hours)
```bash
python pipeline/scripts/run_pipeline.py \
    --all-counties \
    --max-sunbiz 2000 \
    --max-enrichment 2000
```

## Pipeline Output Files

After a complete run, the `pipeline/output/` directory contains:

```
pipeline/output/
├── 01_investor_properties.csv    # Filtered FDOR property data
├── 02_resolved_entities.csv      # Entity owners resolved to humans
├── 03_str_tagged.csv             # STR operators tagged via DBPR
├── 04_fund_managers.csv          # SEC EDGAR fund manager leads
├── 05_enriched.csv               # Contact-enriched leads
└── leads_2026-03-01.xlsx         # FINAL OUTPUT — multi-tab Excel
```

Each intermediate CSV is preserved so you can inspect and debug each pipeline stage independently.
