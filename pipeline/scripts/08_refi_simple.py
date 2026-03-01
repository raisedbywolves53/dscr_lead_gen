"""
Step 2: Refinance Candidate Detection (Owner-Level)

Works on owner-aggregated data from Step 1.
Uses total_portfolio_value (JV sum), most_recent_price, most_recent_purchase
to detect refi signals.
"""

import argparse
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime

OUTPUT_DIR = Path("pipeline/output")


def detect_refi_signals(df: pd.DataFrame) -> pd.DataFrame:
    """Detect refinance opportunity signals on owner-level data."""

    print("Detecting refinance candidate signals...")

    # Parse numeric columns
    df['_jv'] = pd.to_numeric(df.get('total_portfolio_value', 0), errors='coerce').fillna(0)
    df['_price'] = pd.to_numeric(df.get('most_recent_price', 0), errors='coerce').fillna(0)
    df['_avg_val'] = pd.to_numeric(df.get('avg_property_value', 0), errors='coerce').fillna(0)
    df['_pc'] = pd.to_numeric(df.get('property_count', 0), errors='coerce').fillna(0).astype(int)

    # Parse dates
    df['_sale_date'] = pd.to_datetime(df.get('most_recent_purchase', ''), errors='coerce')
    df['days_since_purchase'] = (pd.Timestamp.now() - df['_sale_date']).dt.days.fillna(0).astype(int)

    # Initialize output columns
    df['estimated_equity'] = 0.0
    df['equity_ratio'] = 0.0
    df['max_cashout_75'] = 0.0
    df['max_cashout_80'] = 0.0
    df['refi_signals'] = ''
    df['refi_score_boost'] = 0
    df['refi_priority'] = ''
    df['probable_cash_buyer'] = False
    df['rate_refi_candidate'] = False
    df['brrrr_exit_candidate'] = False
    df['equity_harvest_candidate'] = False

    # For owner-level data, estimate equity per property:
    # avg_property_value (current JV/property) vs most_recent_price
    # This is a rough proxy — the most recent price is just one property
    mask = (df['_avg_val'] > 0) & (df['_price'] > 0)
    df.loc[mask, 'estimated_equity'] = df.loc[mask, '_avg_val'] - df.loc[mask, '_price']
    df.loc[mask, 'equity_ratio'] = df.loc[mask, 'estimated_equity'] / df.loc[mask, '_avg_val']

    # Cash-out potential (on avg property)
    df.loc[mask, 'max_cashout_75'] = ((df.loc[mask, '_avg_val'] * 0.75) - df.loc[mask, '_price']).clip(lower=0)
    df.loc[mask, 'max_cashout_80'] = ((df.loc[mask, '_avg_val'] * 0.80) - df.loc[mask, '_price']).clip(lower=0)

    # Scale by property count for portfolio-level cashout
    df['portfolio_cashout_75'] = df['max_cashout_75'] * df['_pc']

    # Default median for BRRRR detection
    county_median = 400000  # Palm Beach median approximation

    for idx, row in df.iterrows():
        signals = []
        boost = 0
        er = row['equity_ratio']
        days = row['days_since_purchase']
        price = row['_price']
        pc = row['_pc']

        # Signal 1: High equity
        if er >= 0.50:
            signals.append("Very High Equity (50%+)")
            boost += 20
            df.at[idx, 'equity_harvest_candidate'] = True
        elif er >= 0.30:
            signals.append("High Equity (30%+)")
            boost += 15
            df.at[idx, 'equity_harvest_candidate'] = True

        # Signal 2: Probable cash buyer (very high equity ratio)
        if er >= 0.90 and price > 100000:
            signals.append("Probable All-Cash Buyer")
            boost += 20
            df.at[idx, 'probable_cash_buyer'] = True
        elif er >= 0.80 and days > 365 and price > 100000:
            signals.append("Likely Minimal/No Mortgage")
            boost += 15
            df.at[idx, 'probable_cash_buyer'] = True

        # Signal 3: Long hold period
        if days > 1825 and er > 0.40:
            signals.append("Prime Equity Harvest (5yr+ hold)")
            boost += 15
        elif days > 730 and er > 0.25:
            signals.append("Equity Harvesting Opportunity (2yr+ hold)")
            boost += 10

        # Signal 4: Rate refi candidate (2022-2023 vintage)
        if pd.notna(row['_sale_date']):
            if row['_sale_date'].year in (2022, 2023) and price > 100000:
                signals.append("Rate Refi Candidate (2022-2023 Vintage)")
                boost += 10
                df.at[idx, 'rate_refi_candidate'] = True

        # Signal 5: BRRRR exit (below-market purchase, recent)
        if price > 0 and county_median > 0:
            discount = 1 - (price / county_median)
            if discount > 0.30 and 0 < days < 365:
                signals.append("BRRRR Exit Candidate (30%+ below median, <1yr)")
                boost += 15
                df.at[idx, 'brrrr_exit_candidate'] = True
            elif discount > 0.20 and 0 < days < 365:
                signals.append("Possible BRRRR (20%+ below median, <1yr)")
                boost += 10
                df.at[idx, 'brrrr_exit_candidate'] = True

        # Signal 6: Portfolio equity harvest (multi-property)
        if pc >= 3 and er > 0.35:
            signals.append(f"Portfolio Equity Harvest ({pc} properties)")
            boost += 15

        df.at[idx, 'refi_signals'] = ' | '.join(signals) if signals else ''
        df.at[idx, 'refi_score_boost'] = min(boost, 40)

        if boost >= 25:
            df.at[idx, 'refi_priority'] = 'High'
        elif boost >= 15:
            df.at[idx, 'refi_priority'] = 'Medium'
        elif boost > 0:
            df.at[idx, 'refi_priority'] = 'Low'

    # Drop temp columns
    df.drop(columns=['_jv', '_price', '_avg_val', '_pc', '_sale_date'], inplace=True, errors='ignore')

    # Summary
    total = len(df)
    has_signal = (df['refi_signals'] != '').sum()
    high = (df['refi_priority'] == 'High').sum()
    med = (df['refi_priority'] == 'Medium').sum()
    low = (df['refi_priority'] == 'Low').sum()

    print(f"\n{'='*60}")
    print(f"REFINANCE CANDIDATE SUMMARY")
    print(f"{'='*60}")
    print(f"Total leads analyzed:          {total:,}")
    print(f"With refi signal:              {has_signal:,} ({has_signal/total*100:.1f}%)")
    print(f"  High priority:               {high:,}")
    print(f"  Medium priority:             {med:,}")
    print(f"  Low priority:                {low:,}")
    print(f"")
    print(f"BY SIGNAL TYPE:")
    print(f"  Probable cash buyers:        {df['probable_cash_buyer'].sum():,}")
    print(f"  Equity harvest candidates:   {df['equity_harvest_candidate'].sum():,}")
    print(f"  Rate refi (2022-2023):       {df['rate_refi_candidate'].sum():,}")
    print(f"  BRRRR exit candidates:       {df['brrrr_exit_candidate'].sum():,}")

    if has_signal > 0:
        avg_eq = df.loc[df['refi_signals'] != '', 'estimated_equity'].mean()
        avg_co = df.loc[df['refi_signals'] != '', 'max_cashout_75'].mean()
        total_co = df.loc[df['refi_signals'] != '', 'portfolio_cashout_75'].sum()
        print(f"\nEQUITY OPPORTUNITY:")
        print(f"  Avg equity (refi candidates):    ${avg_eq:,.0f}")
        print(f"  Avg cash-out @ 75% LTV:          ${avg_co:,.0f}")
        print(f"  Total portfolio cash-out @ 75%:   ${total_co:,.0f}")

    return df


def main():
    parser = argparse.ArgumentParser(description='Detect DSCR refinance candidates (owner-level)')
    parser.add_argument('--input', type=str, default='pipeline/output/01_investor_properties.csv')
    parser.add_argument('--output', type=str, default='pipeline/output/02_refi_tagged.csv')
    args = parser.parse_args()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("Loading investor properties...")
    df = pd.read_csv(args.input, dtype=str, low_memory=False)
    print(f"  Loaded {len(df):,} records")

    df = detect_refi_signals(df)

    df.to_csv(args.output, index=False)
    print(f"\nOutput saved: {args.output}")


if __name__ == '__main__':
    main()
