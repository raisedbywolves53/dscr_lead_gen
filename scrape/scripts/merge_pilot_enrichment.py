"""
Merge All Pilot 500 Enrichment Sources
=======================================

After running scripts 12 (purchase history), 13 (rental estimates),
14 (wealth signals), and 04b (SunBiz LLC resolution), this script
merges all outputs into a single enriched pilot CSV.

Input files (uses whatever exists):
  1. scrape/data/enriched/pilot_500.csv          — base pilot leads
  2. scrape/data/history/purchase_history.csv     — from script 12
  3. scrape/data/enriched/rent_estimates.csv      — from script 13
  4. scrape/data/signals/wealth_signals.csv       — from script 14
  5. scrape/data/filtered/pilot_llc_resolved.csv  — from script 04b
  6. scrape/data/enriched/apollo_results.csv      — from script 10
  7. scrape/data/financing/mortgage_estimates.csv  — from script 15

Output:
  scrape/data/enriched/pilot_500_enriched.csv

Usage:
    python scrape/scripts/merge_pilot_enrichment.py
"""

from pathlib import Path

import pandas as pd

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent

PILOT_CSV = PROJECT_DIR / "data" / "enriched" / "pilot_500.csv"
PURCHASE_HISTORY_CSV = PROJECT_DIR / "data" / "history" / "purchase_history.csv"
RENT_ESTIMATES_CSV = PROJECT_DIR / "data" / "enriched" / "rent_estimates.csv"
WEALTH_SIGNALS_CSV = PROJECT_DIR / "data" / "signals" / "wealth_signals.csv"
LLC_RESOLVED_CSV = PROJECT_DIR / "data" / "filtered" / "pilot_llc_resolved.csv"
APOLLO_CSV = PROJECT_DIR / "data" / "enriched" / "apollo_results.csv"
MORTGAGE_EST_CSV = PROJECT_DIR / "data" / "financing" / "mortgage_estimates.csv"
OUTPUT_CSV = PROJECT_DIR / "data" / "enriched" / "pilot_500_enriched.csv"

# Columns to merge from each source (avoid duplicating base columns)
PURCHASE_COLS = [
    "total_acquisitions", "total_dispositions", "purchases_last_12mo",
    "purchases_last_36mo", "avg_purchase_price", "most_recent_purchase_date",
    "most_recent_purchase_price", "flip_count", "hold_count",
    "avg_hold_period_months", "cash_purchase_pct", "off_market_count",
    "purchase_frequency_months", "total_sales_records",
]

RENT_COLS = [
    "est_monthly_rent", "est_annual_rent", "est_noi",
    "est_monthly_debt_service", "est_dscr", "rent_to_value_ratio",
]

WEALTH_COLS = [
    "fec_total_donated", "fec_donation_count", "fec_recipients",
    "fec_date_range", "nonprofit_orgs_found", "sunbiz_entity_count",
    "sunbiz_entities", "wealth_signal_score",
]

LLC_COLS = [
    "resolved_person", "registered_agent_name", "registered_agent_address",
    "officer_names", "sunbiz_filing_date", "sunbiz_status",
]

APOLLO_MERGE_COLS = [
    "apollo_match", "apollo_email", "apollo_phone", "apollo_mobile",
    "apollo_linkedin", "apollo_title", "apollo_employer",
]

MORTGAGE_EST_COLS = [
    "est_loan_origination", "est_purchase_price", "est_cash_purchase",
    "est_hard_money", "est_loan_type", "est_interest_rate",
    "est_original_loan", "est_remaining_balance", "est_maturity_date",
    "est_monthly_payment", "est_portfolio_equity", "est_equity_pct",
    "est_months_to_maturity", "est_maturity_urgent", "est_refi_score",
    "est_refi_signals",
]


def safe_merge(base: pd.DataFrame, source_path: Path, merge_cols: list,
               key_col: str, source_name: str) -> pd.DataFrame:
    """Left-join new columns from a source CSV into the base dataframe."""
    if not source_path.exists():
        print(f"  [{source_name}] Not found: {source_path.name} — skipping")
        return base

    src = pd.read_csv(source_path, dtype=str, low_memory=False)
    print(f"  [{source_name}] Loaded {len(src)} rows from {source_path.name}")

    # Only keep columns that actually exist in the source
    available = [c for c in merge_cols if c in src.columns]
    missing = [c for c in merge_cols if c not in src.columns]
    if missing:
        print(f"    Missing columns (skipped): {', '.join(missing)}")
    if not available:
        print(f"    No mergeable columns found — skipping")
        return base

    # Ensure key column exists in source
    if key_col not in src.columns:
        print(f"    Key column '{key_col}' not in source — skipping")
        return base

    # Deduplicate source on key (keep first occurrence)
    src_deduped = src.drop_duplicates(subset=[key_col], keep="first")

    # Drop columns from base that we're about to merge (avoid _x/_y suffixes)
    cols_to_drop = [c for c in available if c in base.columns]
    if cols_to_drop:
        base = base.drop(columns=cols_to_drop)

    # Left join
    merged = base.merge(
        src_deduped[[key_col] + available],
        on=key_col,
        how="left",
    )

    filled = 0
    for col in available:
        non_empty = merged[col].fillna("").astype(str).str.strip()
        non_empty = non_empty[~non_empty.isin(["", "nan", "none", "0", "0.0"])]
        filled = max(filled, len(non_empty))

    print(f"    Merged {len(available)} columns, up to {filled} rows with data")
    return merged


def main():
    if not PILOT_CSV.exists():
        print(f"Pilot CSV not found: {PILOT_CSV}")
        print("Run build_pilot_500.py first.")
        return

    print("\nMerge Pilot 500 Enrichment Sources")
    print("=" * 60)

    # Load base pilot data
    df = pd.read_csv(PILOT_CSV, dtype=str, low_memory=False)
    print(f"Base pilot leads: {len(df)} rows, {len(df.columns)} columns\n")

    # Merge purchase history (key: OWN_NAME)
    df = safe_merge(df, PURCHASE_HISTORY_CSV, PURCHASE_COLS, "OWN_NAME", "Purchase History")

    # Merge rental estimates (key: OWN_NAME — rent_estimates carries all input rows)
    df = safe_merge(df, RENT_ESTIMATES_CSV, RENT_COLS, "OWN_NAME", "Rental Estimates")

    # Merge wealth signals (key: OWN_NAME)
    df = safe_merge(df, WEALTH_SIGNALS_CSV, WEALTH_COLS, "OWN_NAME", "Wealth Signals")

    # Merge LLC resolution (key: OWN_NAME — resolved_person, officers, etc.)
    df = safe_merge(df, LLC_RESOLVED_CSV, LLC_COLS, "OWN_NAME", "LLC Resolution")

    # Merge Apollo results (key: OWN_NAME)
    df = safe_merge(df, APOLLO_CSV, APOLLO_MERGE_COLS, "OWN_NAME", "Apollo")

    # Merge mortgage estimates (key: OWN_NAME)
    df = safe_merge(df, MORTGAGE_EST_CSV, MORTGAGE_EST_COLS, "OWN_NAME", "Mortgage Estimates")

    # Save
    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT_CSV, index=False)

    # Completeness summary
    print()
    print("=" * 60)
    print("  ENRICHMENT COMPLETENESS")
    print("=" * 60)
    total = len(df)

    def count_filled(col):
        if col not in df.columns:
            return 0
        vals = df[col].fillna("").astype(str).str.strip()
        return vals[~vals.isin(["", "nan", "none", "0", "0.0", "False"])].shape[0]

    checks = [
        ("Purchase history", "total_acquisitions"),
        ("Rental estimates", "est_monthly_rent"),
        ("Wealth signals", "wealth_signal_score"),
        ("Resolved person", "resolved_person"),
        ("Phone (any)", "phone_1"),
        ("Email (any)", "email_1"),
        ("Apollo match", "apollo_match"),
        ("FEC donations", "fec_total_donated"),
        ("Nonprofit orgs", "nonprofit_orgs_found"),
        ("SunBiz entities", "sunbiz_entity_count"),
        ("Loan type est.", "est_loan_type"),
        ("Interest rate est.", "est_interest_rate"),
        ("Remaining balance", "est_remaining_balance"),
        ("Maturity date", "est_maturity_date"),
        ("Refi score", "est_refi_score"),
        ("Cash purchase", "est_cash_purchase"),
        ("Hard money flag", "est_hard_money"),
    ]

    for label, col in checks:
        n = count_filled(col)
        pct = n * 100 // total if total else 0
        bar = "#" * (pct // 2)
        print(f"  {label:<22} {n:>4}/{total}  ({pct:>2}%)  {bar}")

    print(f"\n  Total columns: {len(df.columns)}")
    print(f"  Saved: {OUTPUT_CSV}")
    print()


if __name__ == "__main__":
    main()
