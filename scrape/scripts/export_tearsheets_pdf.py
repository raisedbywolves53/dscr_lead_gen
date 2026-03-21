"""
Export Tearsheets to PDF
=========================

Converts HTML tearsheets to print-ready PDF files using Playwright
(headless Chromium). This is the final delivery step — produces the
actual files that get sent to clients.

Output: One PDF per tearsheet, same directory as the HTML source.

Requires: pip install playwright && playwright install chromium

Usage:
    python scripts/export_tearsheets_pdf.py
    python scripts/export_tearsheets_pdf.py --files tearsheet_moyer*.html
    python scripts/export_tearsheets_pdf.py --output-dir /path/to/delivery/
"""

import argparse
import sys
from pathlib import Path

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("ERROR: playwright not installed. Run: pip install playwright && playwright install chromium")
    sys.exit(1)

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent
DEFAULT_DIR = PROJECT_DIR.parent / "sales" / "demo_tearsheets"


def html_to_pdf(html_path: Path, pdf_path: Path, browser):
    """Convert a single HTML file to PDF using Playwright."""
    page = browser.new_page()
    page.goto(f"file://{html_path.resolve()}", wait_until="networkidle")

    # Wait for fonts to load
    page.wait_for_timeout(1000)

    page.pdf(
        path=str(pdf_path),
        format="Letter",
        margin={"top": "0.4in", "bottom": "0.4in", "left": "0.4in", "right": "0.4in"},
        print_background=True,
    )
    page.close()


def main():
    parser = argparse.ArgumentParser(description="Export HTML tearsheets to PDF")
    parser.add_argument("--dir", type=str, default="",
                        help=f"Directory containing HTML tearsheets (default: {DEFAULT_DIR})")
    parser.add_argument("--files", type=str, default="",
                        help="Glob pattern for specific files (e.g., 'tearsheet_moyer*.html')")
    parser.add_argument("--output-dir", type=str, default="",
                        help="Output directory for PDFs (default: same as HTML)")
    parser.add_argument("--include-market", action="store_true",
                        help="Also export market_universe*.html files")
    args = parser.parse_args()

    source_dir = Path(args.dir) if args.dir else DEFAULT_DIR
    output_dir = Path(args.output_dir) if args.output_dir else source_dir

    if not source_dir.exists():
        print(f"  ERROR: Directory not found: {source_dir}")
        sys.exit(1)

    output_dir.mkdir(parents=True, exist_ok=True)

    # Find HTML files
    if args.files:
        html_files = sorted(source_dir.glob(args.files))
    else:
        html_files = sorted(source_dir.glob("tearsheet_*.html"))
        if args.include_market:
            html_files += sorted(source_dir.glob("market_universe_*.html"))

    if not html_files:
        print(f"  No HTML files found in {source_dir}")
        sys.exit(1)

    print(f"\n{'='*60}")
    print(f"  EXPORT TEARSHEETS TO PDF")
    print(f"  Source: {source_dir}")
    print(f"  Output: {output_dir}")
    print(f"  Files:  {len(html_files)}")
    print(f"{'='*60}")

    with sync_playwright() as p:
        browser = p.chromium.launch()

        for html_path in html_files:
            pdf_name = html_path.stem + ".pdf"
            pdf_path = output_dir / pdf_name

            html_to_pdf(html_path, pdf_path, browser)

            size_kb = pdf_path.stat().st_size / 1024
            print(f"  {pdf_name} ({size_kb:.0f} KB)")

        browser.close()

    print(f"\n  {len(html_files)} PDFs exported to {output_dir}")
    print()


if __name__ == "__main__":
    main()
