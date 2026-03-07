"""
Step 11b: County Clerk Lender Lookup Helper
=============================================

Generates a CSV of top leads with pre-built clerk portal URLs for manual
mortgage/lender lookup. Both PBC and Broward clerk portals require CAPTCHA,
so this creates a structured workflow for manual browser lookups.

What this produces:
  1. A "lookup sheet" CSV with lead info + clerk portal URLs
  2. A "recording template" CSV to paste lender data into
  3. A --merge mode that reads back the filled template and adds to pipeline

Usage:
    python scripts/11b_clerk_lookup_helper.py --top 25
    python scripts/11b_clerk_lookup_helper.py --merge results.csv
    python scripts/11b_clerk_lookup_helper.py --top 50 --input data/enriched/pilot_500_enriched.csv

Manual workflow:
  1. Run this script to generate the lookup sheet
  2. Open each URL in your browser, accept disclaimer, search
  3. Record lender names in the template CSV
  4. Run with --merge to integrate results back into the pipeline
"""

import argparse
import os
import sys
import urllib.parse
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import pandas as pd

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent
ENRICHED_DIR = PROJECT_DIR / "data" / "enriched"
FINANCING_DIR = PROJECT_DIR / "data" / "financing"

DEFAULT_INPUT = ENRICHED_DIR / "pilot_500_enriched.csv"

# Clerk portal base URLs
PBC_CLERK_URL = "https://erec.mypalmbeachclerk.com/"
BROWARD_CLERK_URL = "https://officialrecords.broward.org/AcclaimWeb/"

# Hard money lender keywords (for classification)
HARD_MONEY_KEYWORDS = [
    "HARD MONEY", "BRIDGE", "FIX AND FLIP", "REHAB",
    "KIAVI", "LIMA ONE", "CIVIC", "ANCHOR LOANS", "GENESIS",
    "RCLENDING", "GROUNDFLOOR", "FUND THAT FLIP",
    "LENDING HOME", "VISIO", "NEW SILVER", "EASY STREET",
    "PATCH OF LAND", "COREVEST", "RENOVO", "TEMPLE VIEW",
    "AMERICAN HERITAGE", "VELOCITY", "TOORAK",
]


def classify_lender(lender_name: str) -> str:
    """Classify a lender as bank, credit_union, hard_money, private, or unknown."""
    if not lender_name or str(lender_name).strip().lower() in ("", "nan", "none"):
        return ""
    upper = lender_name.upper()
    for kw in HARD_MONEY_KEYWORDS:
        if kw in upper:
            return "hard_money"
    for kw in ["CREDIT UNION", "FCU", "FEDERAL CREDIT"]:
        if kw in upper:
            return "credit_union"
    for kw in ["PRIVATE", "INDIVIDUAL", "TRUST", "FAMILY"]:
        if kw in upper:
            return "private"
    for kw in ["BANK", "NATIONAL ASSOCIATION", "N.A.", "MORTGAGE CORP",
               "WELLS FARGO", "CHASE", "JPMORGAN", "CITIBANK",
               "REGIONS", "TRUIST", "PNC", "US BANK", "TD BANK",
               "LENDING", "FINANCIAL", "SAVINGS"]:
        if kw in upper:
            return "bank"
    return "unknown"


def generate_lookup_sheet(df: pd.DataFrame, top_n: int, output_dir: Path):
    """Generate CSV with leads + clerk portal URLs for manual lookup."""

    # Score and sort
    if "_score" in df.columns:
        df["_score_num"] = pd.to_numeric(df["_score"], errors="coerce")
        df = df.nlargest(top_n, "_score_num")
    else:
        df = df.head(top_n)

    rows = []
    for _, row in df.iterrows():
        # Get best name
        person = str(row.get("resolved_person", "") or "").strip()
        owner = str(row.get("OWN_NAME", "") or "").strip()
        name = person if person and person.lower() != "nan" else owner

        # Determine county
        co_no = str(row.get("CO_NO", "")).strip()
        if co_no == "60":
            county = "Palm Beach"
            clerk_url = PBC_CLERK_URL
        elif co_no == "16":
            county = "Broward"
            clerk_url = BROWARD_CLERK_URL
        else:
            county = co_no
            clerk_url = PBC_CLERK_URL  # default

        # Build search name (Last, First for individuals)
        search_name = owner  # Use LLC/entity name as-is

        score = row.get("_score", "")
        icp = row.get("_icp", "")
        est_loan = row.get("est_loan_type", "")
        prop_count = row.get("property_count", "")
        portfolio_val = row.get("JV", "")
        phone = str(row.get("phone_1", "") or "").strip()
        email = str(row.get("email_1", "") or "").strip()
        if phone.lower() == "nan":
            phone = ""
        if email.lower() == "nan":
            email = ""

        rows.append({
            "rank": len(rows) + 1,
            "OWN_NAME": owner,
            "resolved_person": person if person.lower() != "nan" else "",
            "search_name": search_name,
            "county": county,
            "clerk_url": clerk_url,
            "score": score,
            "icp_segment": icp,
            "est_loan_type": est_loan,
            "property_count": prop_count,
            "portfolio_value": portfolio_val,
            "phone": phone,
            "email": email,
            # Fields for manual entry
            "lender_1": "",
            "lender_1_type": "",
            "mortgage_amount_1": "",
            "mortgage_date_1": "",
            "lender_2": "",
            "lender_2_type": "",
            "mortgage_amount_2": "",
            "mortgage_date_2": "",
            "has_hard_money": "",
            "has_lis_pendens": "",
            "notes": "",
        })

    out_df = pd.DataFrame(rows)

    # Save lookup sheet
    lookup_path = output_dir / "clerk_lookup_sheet.csv"
    out_df.to_csv(lookup_path, index=False)

    # Also save a simpler recording template
    template_cols = [
        "rank", "OWN_NAME", "resolved_person", "search_name", "county",
        "lender_1", "lender_1_type", "mortgage_amount_1", "mortgage_date_1",
        "lender_2", "lender_2_type", "mortgage_amount_2", "mortgage_date_2",
        "has_hard_money", "has_lis_pendens", "notes"
    ]
    template_df = out_df[template_cols]
    template_path = output_dir / "clerk_recording_template.csv"
    template_df.to_csv(template_path, index=False)

    return lookup_path, template_path, out_df


def merge_results(input_csv: Path, results_csv: Path, output_csv: Path):
    """Merge manually recorded lender data back into enriched CSV."""
    df = pd.read_csv(input_csv, dtype=str, low_memory=False)
    results = pd.read_csv(results_csv, dtype=str, low_memory=False)

    # Clean up results
    lender_cols = [
        "lender_1", "lender_1_type", "mortgage_amount_1", "mortgage_date_1",
        "lender_2", "lender_2_type", "mortgage_amount_2", "mortgage_date_2",
        "has_hard_money", "has_lis_pendens",
    ]

    # Auto-classify lenders if type not filled in
    for _, row in results.iterrows():
        for i in [1, 2]:
            lender = str(row.get(f"lender_{i}", "") or "").strip()
            ltype = str(row.get(f"lender_{i}_type", "") or "").strip()
            if lender and lender.lower() != "nan" and (not ltype or ltype.lower() == "nan"):
                results.at[_, f"lender_{i}_type"] = classify_lender(lender)

    # Merge on OWN_NAME
    merge_cols = ["OWN_NAME"] + lender_cols
    available = [c for c in merge_cols if c in results.columns]
    results_clean = results[available].copy()

    # Remove empty rows
    results_clean = results_clean.dropna(subset=["lender_1"], how="all")

    # Only keep rows where lender_1 has actual data
    mask = results_clean["lender_1"].apply(
        lambda x: bool(str(x).strip()) and str(x).strip().lower() not in ("nan", "none", "")
    )
    results_clean = results_clean[mask]

    if len(results_clean) == 0:
        print("  No lender data found in results file.")
        return

    # Merge
    for col in lender_cols:
        if col not in df.columns:
            df[col] = ""

    for _, result_row in results_clean.iterrows():
        own_name = str(result_row.get("OWN_NAME", "")).strip()
        match_mask = df["OWN_NAME"].str.strip() == own_name
        if match_mask.sum() > 0:
            for col in lender_cols:
                val = str(result_row.get(col, "") or "").strip()
                if val and val.lower() not in ("nan", "none"):
                    df.loc[match_mask, col] = val

    df.to_csv(output_csv, index=False)
    with_lender = df["lender_1"].apply(
        lambda x: bool(str(x).strip()) and str(x).strip().lower() not in ("nan", "none", "")
    ).sum()
    print(f"  Merged lender data: {with_lender}/{len(df)} leads have lender info")
    print(f"  Output: {output_csv}")


def main():
    parser = argparse.ArgumentParser(description="Clerk lender lookup helper (Step 11b)")
    parser.add_argument("--input", type=str, default=str(DEFAULT_INPUT))
    parser.add_argument("--top", type=int, default=25,
                        help="Number of top leads to generate lookup URLs for")
    parser.add_argument("--merge", type=str, default="",
                        help="Path to filled recording template CSV to merge back")
    parser.add_argument("--output", type=str, default="",
                        help="Output path for merged CSV (default: overwrites input)")
    args = parser.parse_args()

    FINANCING_DIR.mkdir(parents=True, exist_ok=True)

    if args.merge:
        # Merge mode
        results_path = Path(args.merge)
        if not results_path.exists():
            print(f"\n  ERROR: Results file not found: {args.merge}")
            return
        input_path = Path(args.input)
        output_path = Path(args.output) if args.output else input_path
        print(f"\n  Merging lender data from: {results_path}")
        merge_results(input_path, results_path, output_path)
        return

    # Generate lookup sheet
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"\n  ERROR: Input not found: {args.input}")
        return

    print(f"\n  Loading leads: {input_path}")
    df = pd.read_csv(input_path, dtype=str, low_memory=False)
    print(f"  Total leads: {len(df)}")

    lookup_path, template_path, top_df = generate_lookup_sheet(df, args.top, FINANCING_DIR)

    print()
    print("=" * 60)
    print("  CLERK LENDER LOOKUP HELPER")
    print("=" * 60)
    print(f"  Top {args.top} leads selected for lookup")
    print(f"  Lookup sheet: {lookup_path}")
    print(f"  Recording template: {template_path}")
    print()
    print("  HOW TO USE:")
    print("  1. Open the lookup sheet CSV")
    print("  2. For each lead, open the clerk_url in your browser")
    print(f"     - PBC: {PBC_CLERK_URL}")
    print(f"     - Broward: {BROWARD_CLERK_URL}")
    print("  3. Accept the disclaimer, search by the 'search_name'")
    print("  4. Filter to MTG (Mortgage) document types")
    print("  5. Record the lender name, amount, and date in the template")
    print("  6. Note if any hard money or lis pendens found")
    print("  7. Run: python scripts/11b_clerk_lookup_helper.py --merge <template.csv>")
    print()
    print("  SEARCH TIPS:")
    print("  - For LLC names, search the entity name as-is")
    print("  - For person names, search LAST NAME first")
    print("  - Check MTG (Mortgage) and ASG (Assignment) doc types")
    print("  - Most recent MTG = current lender")
    print("  - ASG after MTG = loan was sold to new lender")
    print("  - SAT = Satisfaction (mortgage paid off)")
    print()
    print("  TOP LEADS:")
    for _, row in top_df.iterrows():
        name = row.get("resolved_person", "") or row.get("OWN_NAME", "")
        if not name or str(name).lower() == "nan":
            name = row.get("OWN_NAME", "")
        score = row.get("score", "")
        est = row.get("est_loan_type", "")
        print(f"    #{row['rank']:>2} | {str(name)[:35]:<35} | score={score} | est_type={est}")
    print()


if __name__ == "__main__":
    main()
