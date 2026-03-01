"""
DSCR Lead Generation Pipeline — Master Orchestrator

Runs the full pipeline end-to-end:
1. Download & filter FDOR property data
2. Detect refinance & cash-out candidates (equity analysis)
3. Resolve entity owners via SunBiz
4. Tag STR operators via DBPR
5. Identify fund managers via SEC EDGAR
6. Enrich contacts (phone/email)
7. Score, classify, and output to Excel

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

    # Step 2: Refinance & Cash-Out Candidate Detection
    run_step(2, "Refinance & Cash-Out Candidate Detection",
             f"{scripts_dir}/08_refi_candidates.py",
             ['--input', 'pipeline/output/01_investor_properties.csv',
              '--sdf-dir', 'pipeline/data/fdor',
              '--output', 'pipeline/output/02_refi_tagged.csv'])

    # Step 3: SunBiz Entity Resolution
    run_step(3, "SunBiz Entity Resolution",
             f"{scripts_dir}/02_sunbiz_resolve.py",
             ['--input', 'pipeline/output/02_refi_tagged.csv',
              '--output', 'pipeline/output/03_resolved_entities.csv',
              '--max-lookups', str(args.max_sunbiz)])

    # Step 4: DBPR STR Operator Tagging
    run_step(4, "DBPR STR Operator Identification",
             f"{scripts_dir}/03_dbpr_str.py",
             ['--input', 'pipeline/output/03_resolved_entities.csv',
              '--output', 'pipeline/output/04_str_tagged.csv'])

    # Step 5: SEC EDGAR (optional)
    if not args.skip_edgar:
        run_step(5, "SEC EDGAR — FL Real Estate Fund Identification",
                 f"{scripts_dir}/04_sec_edgar.py",
                 ['--output', 'pipeline/output/05_fund_managers.csv',
                  '--fetch-details'])
    else:
        print("\nStep 5: SEC EDGAR — SKIPPED")

    # Step 6: Contact Enrichment (optional)
    if not args.skip_enrichment:
        enrich_args = ['--input', 'pipeline/output/04_str_tagged.csv',
                       '--output', 'pipeline/output/06_enriched.csv',
                       '--max-lookups', str(args.max_enrichment)]
        if args.apollo_key:
            enrich_args += ['--apollo-key', args.apollo_key]

        run_step(6, "Contact Enrichment",
                 f"{scripts_dir}/05_enrich_contacts.py",
                 enrich_args)
    else:
        print("\nStep 6: Contact Enrichment — SKIPPED")
        # Copy input directly to enrichment output
        import shutil
        shutil.copy('pipeline/output/04_str_tagged.csv',
                     'pipeline/output/06_enriched.csv')

    # Step 7: Scoring & Excel Output
    run_step(7, "ICP Scoring & Excel Output",
             f"{scripts_dir}/06_score_and_output.py",
             ['--input', 'pipeline/output/06_enriched.csv',
              '--edgar-input', 'pipeline/output/05_fund_managers.csv',
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
