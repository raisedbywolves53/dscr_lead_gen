"""
Build Presentation PDF
=======================

Combines all demo materials into a single PDF for easy email delivery.
Uses Playwright to merge individual PDFs in presentation order.

Output: sales/demo_tearsheets/Northside_Realty_Intelligence_Brief.pdf
"""

import sys
from pathlib import Path

try:
    from pypdf import PdfWriter
except ImportError:
    try:
        from PyPDF2 import PdfMerger as PdfWriter
    except ImportError:
        print("ERROR: Install pypdf: pip install pypdf")
        sys.exit(1)

TEARSHEET_DIR = Path(__file__).resolve().parent.parent.parent / "sales" / "demo_tearsheets"

# Presentation order
PAGES = [
    "market_universe_wake.pdf",
    "tearsheet_wang_jing.pdf",
    "tearsheet_yeramsetty_srinivasa_rao_gunti_krishna_kumari.pdf",
    "tearsheet_moyer_jonathan_eck_kelly.pdf",
    "sample_weekly_digest.pdf",
]

OUTPUT = TEARSHEET_DIR / "Northside_Realty_Intelligence_Brief.pdf"


def main():
    print(f"\n{'='*60}")
    print(f"  BUILD PRESENTATION PDF")
    print(f"{'='*60}")

    writer = PdfWriter()

    for filename in PAGES:
        path = TEARSHEET_DIR / filename
        if not path.exists():
            print(f"  SKIP (not found): {filename}")
            continue
        writer.append(str(path))
        print(f"  Added: {filename}")

    writer.write(str(OUTPUT))
    writer.close()

    size_kb = OUTPUT.stat().st_size / 1024
    print(f"\n  Output: {OUTPUT.name} ({size_kb:.0f} KB)")
    print(f"  Pages: {len(PAGES)}")
    print()


if __name__ == "__main__":
    main()
