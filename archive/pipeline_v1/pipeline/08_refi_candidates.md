# Module 8: DSCR Refinance & Cash-Out Candidate Detection

## Purpose
Identify investment property owners who are strong candidates for DSCR refinance — specifically cash-out refinance, rate-and-term refinance, and hard-money-to-DSCR conversion. This module runs AFTER Module 1 (FDOR data) and BEFORE Module 6 (scoring) to add refinance signals to every lead.

## Why This Matters

The pipeline was originally designed to find investors who might need DSCR for new purchases. But **refinance is arguably the bigger volume opportunity:**

- **43,000-45,000 all-cash investor purchases per year in FL** — these owners have 100% equity and zero leverage
- **69% of investor purchases are all-cash** nationally
- Cash-out at 75% LTV on a $400K property = **$300K tax-free cash** to deploy
- Investors who bought in 2022-2023 financed at 7-8%+ — rate-and-term refi candidates as rates decline
- Every BRRRR investor with a hard money loan = guaranteed DSCR refi in 3-12 months

## DSCR Cash-Out Refinance Parameters

| Parameter | Typical | Aggressive (theLender/Open Mortgage) |
|---|---|---|
| Max LTV (cash-out) | 75% | 80% |
| Min equity retained | 25% | 20% |
| Seasoning required | 6 months typical | 0 days (no seasoning) |
| Min DSCR | 1.0-1.25 | 0.75 or No Ratio |
| Min FICO | 660-680 | 620 |
| Max loan amount | $2M | $3.5M |
| Proceeds use | Business purpose | Business purpose |

## Refinance Candidate Signals (Detectable from FDOR Data)

### Signal 1: High Equity — Appreciated Since Purchase
```
Estimated Equity = Current Just Value - Last Sale Price
Equity Ratio = Estimated Equity / Current Just Value

IF Equity Ratio >= 0.30 (30%+ equity):
    refi_signal = "High Equity"
    refi_score_boost = +15

IF Equity Ratio >= 0.50 (50%+ equity):
    refi_signal = "Very High Equity"
    refi_score_boost = +20
```

**Why it works:** FDOR provides both the last sale price (SDF) and current just/market value (NAL). The delta is unrealized equity that can be converted to cash via DSCR cash-out refi.

### Signal 2: Probable All-Cash Buyer
```
IF sale_price > $100K AND no_mortgage_proxy = TRUE:
    refi_signal = "Probable Cash Buyer"
    refi_score_boost = +20

Proxy indicators for all-cash (from FDOR data alone):
- Documentary stamp tax on deed but NO intangible tax recorded
  (Florida charges intangible tax only on mortgages — $0.002 per $1)
- SDF qualification code patterns associated with cash transactions
- Very high equity ratio (100% = never financed)
```

**Limitation:** FDOR data doesn't directly show mortgage status. We can only approximate. For precise identification, county Clerk records are needed (future enhancement).

**Alternative approach:** Properties where Just Value equals or closely matches the original sale price AND the purchase was 2+ years ago likely have no mortgage (or very low balance if they do).

### Signal 3: Long Hold Period (Sitting on Equity)
```
Days Since Purchase = Today - Last Sale Date

IF days_since_purchase > 730 (2+ years) AND equity_ratio > 0.25:
    refi_signal = "Long Hold / Equity Harvesting Opportunity"
    refi_score_boost = +10

IF days_since_purchase > 1825 (5+ years) AND equity_ratio > 0.40:
    refi_signal = "Prime Equity Harvest"
    refi_score_boost = +15
```

### Signal 4: Rate-and-Term Refi Candidates (2022-2023 Vintage)
```
IF last_sale_date BETWEEN 2022-01-01 AND 2023-12-31:
    refi_signal = "Rate Refi Candidate (High-Rate Vintage)"
    refi_score_boost = +10
    # These borrowers likely financed at 7-8%+
    # Current DSCR rates: 6.0-7.5% depending on profile
    # Even 50-100bps savings = significant monthly savings
```

### Signal 5: BRRRR Exit Candidates (Below-Market Purchase + Recent)
```
county_median = median sale price for county from SDF
purchase_discount = 1 - (sale_price / county_median)

IF purchase_discount > 0.30 AND days_since_purchase < 365:
    refi_signal = "BRRRR Exit Candidate"
    refi_score_boost = +15
    # Bought at 30%+ below median = likely distressed/rehab purchase
    # Held less than 1 year = likely finishing rehab, needs permanent financing
```

### Signal 6: Multi-Property Owners with Equity Across Portfolio
```
IF property_count >= 3 AND avg_equity_ratio > 0.35:
    refi_signal = "Portfolio Equity Harvest"
    refi_score_boost = +15
    # Multiple properties with significant equity =
    # multiple cash-out refi opportunities in one relationship
    # Could be blanket loan candidate (theLender's theBlanket product)
```

## Script: `scripts/08_refi_candidates.py`

```python
"""
Module 8: DSCR Refinance & Cash-Out Candidate Detection

Analyzes FDOR property data to identify investment property owners
who are strong candidates for DSCR cash-out refinance, rate-and-term
refinance, or hard-money exit.

Usage:
    python scripts/08_refi_candidates.py --input pipeline/output/01_investor_properties.csv --sdf-dir pipeline/data/fdor --output pipeline/output/08_refi_tagged.csv
"""

import argparse
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, date
import glob

OUTPUT_DIR = Path("pipeline/output")


def compute_county_medians(sdf_dir: str) -> dict:
    """
    Compute median sale prices by county from SDF data.
    Used to identify below-market (BRRRR) purchases.
    """
    medians = {}

    sdf_files = glob.glob(f"{sdf_dir}/SDF_*.csv")
    if not sdf_files:
        print("  No SDF files found. Using default median of $400,000.")
        return {}

    for sdf_file in sdf_files:
        try:
            df = pd.read_csv(sdf_file, dtype=str, low_memory=False)

            # Find county code column
            county_col = None
            for col in df.columns:
                if col.upper() in ('CO_NO', 'COUNTY', 'COUNTY_CODE'):
                    county_col = col
                    break

            # Find sale price column
            price_col = None
            for col in df.columns:
                if 'PRICE' in col.upper() or 'SALE' in col.upper() and 'AMT' in col.upper():
                    price_col = col
                    break
                elif col.upper() in ('SALE_PRC', 'SALE_PRICE', 'SALE_AMT'):
                    price_col = col
                    break

            if price_col:
                df[price_col] = pd.to_numeric(df[price_col], errors='coerce')
                # Filter to qualified arms-length sales > $50K
                valid_sales = df[df[price_col] > 50000]
                if county_col and len(valid_sales) > 0:
                    county = valid_sales[county_col].iloc[0] if len(valid_sales) > 0 else 'unknown'
                    medians[county] = valid_sales[price_col].median()
                elif len(valid_sales) > 0:
                    # Extract county from filename
                    fname = Path(sdf_file).stem
                    medians[fname] = valid_sales[price_col].median()

        except Exception as e:
            print(f"  Error processing SDF file {sdf_file}: {e}")

    return medians


def detect_refi_signals(df: pd.DataFrame, county_medians: dict) -> pd.DataFrame:
    """
    Analyze each property/owner record for refinance opportunity signals.
    Adds refi-specific columns to the dataframe.
    """

    print("Detecting refinance candidate signals...")

    # ====================================================================
    # FIND RELEVANT COLUMNS
    # ====================================================================

    # Just Value (current market value)
    jv_col = None
    for col in df.columns:
        if col.upper() in ('JV', 'JUST_VAL', 'JUST_VALUE', 'MARKET_VALUE'):
            jv_col = col
            break

    # Sale price (from SDF merge or NAL sale fields)
    price_col = None
    for col in df.columns:
        if 'PRICE' in col.upper() or 'SALE_PRC' in col.upper():
            price_col = col
            break
        elif col.upper() in ('MOST_RECENT_PRICE', 'SALE_PRICE', 'SALE_AMT'):
            price_col = col
            break

    # Sale date
    date_col = None
    for col in df.columns:
        if 'SALE' in col.upper() and 'DATE' in col.upper():
            date_col = col
            break
        elif col.upper() in ('MOST_RECENT_PURCHASE', 'SALE_DATE', 'SALE_DT'):
            date_col = col
            break

    # County
    county_col = None
    for col in df.columns:
        if col.upper() in ('CO_NO', 'COUNTY', 'COUNTY_CODE'):
            county_col = col
            break

    # Property count (if owner-level aggregation already done)
    pc_col = None
    for col in df.columns:
        if col.upper() in ('PROPERTY_COUNT',):
            pc_col = col
            break

    # ====================================================================
    # INITIALIZE NEW COLUMNS
    # ====================================================================

    df['estimated_equity'] = 0.0
    df['equity_ratio'] = 0.0
    df['days_since_purchase'] = 0
    df['max_cashout_75'] = 0.0      # Cash available at 75% LTV
    df['max_cashout_80'] = 0.0      # Cash available at 80% LTV
    df['refi_signals'] = ''
    df['refi_score_boost'] = 0
    df['refi_priority'] = ''        # "High", "Medium", "Low"
    df['probable_cash_buyer'] = False
    df['rate_refi_candidate'] = False
    df['brrrr_exit_candidate'] = False
    df['equity_harvest_candidate'] = False

    # ====================================================================
    # COMPUTE EQUITY & TIMING
    # ====================================================================

    if jv_col:
        df['_jv'] = pd.to_numeric(df[jv_col], errors='coerce').fillna(0)
    else:
        print("  WARNING: No Just Value column found. Equity calculation limited.")
        df['_jv'] = 0

    if price_col:
        df['_price'] = pd.to_numeric(df[price_col], errors='coerce').fillna(0)
    else:
        print("  WARNING: No sale price column found. Equity calculation limited.")
        df['_price'] = 0

    if date_col:
        df['_sale_date'] = pd.to_datetime(df[date_col], errors='coerce')
        df['days_since_purchase'] = (pd.Timestamp.now() - df['_sale_date']).dt.days.fillna(0).astype(int)
    else:
        print("  WARNING: No sale date column found.")
        df['_sale_date'] = pd.NaT

    # Estimated equity (simple: current value - purchase price)
    mask = (df['_jv'] > 0) & (df['_price'] > 0)
    df.loc[mask, 'estimated_equity'] = df.loc[mask, '_jv'] - df.loc[mask, '_price']
    df.loc[mask, 'equity_ratio'] = df.loc[mask, 'estimated_equity'] / df.loc[mask, '_jv']

    # Cash-out potential
    df.loc[mask, 'max_cashout_75'] = (df.loc[mask, '_jv'] * 0.75) - df.loc[mask, '_price']
    df.loc[mask, 'max_cashout_80'] = (df.loc[mask, '_jv'] * 0.80) - df.loc[mask, '_price']

    # Floor at zero (can't cash out more than equity)
    df['max_cashout_75'] = df['max_cashout_75'].clip(lower=0)
    df['max_cashout_80'] = df['max_cashout_80'].clip(lower=0)

    # ====================================================================
    # SIGNAL DETECTION
    # ====================================================================

    signals_list = []

    for idx, row in df.iterrows():
        signals = []
        boost = 0

        equity_ratio = row['equity_ratio']
        days = row['days_since_purchase']
        price = row['_price']
        jv = row['_jv']

        # Signal 1: High Equity
        if equity_ratio >= 0.50:
            signals.append("Very High Equity (50%+)")
            boost += 20
            df.at[idx, 'equity_harvest_candidate'] = True
        elif equity_ratio >= 0.30:
            signals.append("High Equity (30%+)")
            boost += 15
            df.at[idx, 'equity_harvest_candidate'] = True

        # Signal 2: Probable Cash Buyer
        # Properties with equity ratio near 100% (value ≈ purchase price with no depreciation)
        # OR purchased more than 2 years ago with equity ratio > 90%
        if equity_ratio >= 0.90 and price > 100000:
            signals.append("Probable All-Cash Buyer")
            boost += 20
            df.at[idx, 'probable_cash_buyer'] = True
        elif equity_ratio >= 0.80 and days > 365 and price > 100000:
            # High equity + held over a year = likely no mortgage or very small balance
            signals.append("Likely Minimal/No Mortgage")
            boost += 15
            df.at[idx, 'probable_cash_buyer'] = True

        # Signal 3: Long Hold
        if days > 1825 and equity_ratio > 0.40:  # 5+ years
            signals.append("Prime Equity Harvest (5yr+ hold)")
            boost += 15
        elif days > 730 and equity_ratio > 0.25:  # 2+ years
            signals.append("Equity Harvesting Opportunity (2yr+ hold)")
            boost += 10

        # Signal 4: Rate Refi Candidate (2022-2023 purchase)
        if row.get('_sale_date') is not pd.NaT and pd.notna(row.get('_sale_date')):
            sale_date = row['_sale_date']
            if isinstance(sale_date, pd.Timestamp):
                if sale_date.year in (2022, 2023) and price > 100000:
                    signals.append("Rate Refi Candidate (2022-2023 Vintage)")
                    boost += 10
                    df.at[idx, 'rate_refi_candidate'] = True

        # Signal 5: BRRRR Exit Candidate
        county = str(row.get(county_col, '')) if county_col else ''
        county_median = county_medians.get(county, 400000)  # Default $400K
        if county_median > 0 and price > 0:
            purchase_discount = 1 - (price / county_median)
            if purchase_discount > 0.30 and days < 365 and days > 0:
                signals.append("BRRRR Exit Candidate (30%+ below median, <1yr)")
                boost += 15
                df.at[idx, 'brrrr_exit_candidate'] = True
            elif purchase_discount > 0.20 and days < 365 and days > 0:
                signals.append("Possible BRRRR (20%+ below median, <1yr)")
                boost += 10
                df.at[idx, 'brrrr_exit_candidate'] = True

        # Signal 6: Portfolio Equity Harvest (multi-property owners)
        if pc_col:
            prop_count = int(float(row.get(pc_col, 0) or 0))
            if prop_count >= 3 and equity_ratio > 0.35:
                signals.append(f"Portfolio Equity Harvest ({prop_count} properties)")
                boost += 15

        # Aggregate
        df.at[idx, 'refi_signals'] = ' | '.join(signals) if signals else ''
        df.at[idx, 'refi_score_boost'] = min(boost, 40)  # Cap boost at 40

        # Priority classification
        if boost >= 25:
            df.at[idx, 'refi_priority'] = 'High'
        elif boost >= 15:
            df.at[idx, 'refi_priority'] = 'Medium'
        elif boost > 0:
            df.at[idx, 'refi_priority'] = 'Low'

    # ====================================================================
    # CLEAN UP
    # ====================================================================

    df.drop(columns=['_jv', '_price', '_sale_date'], inplace=True, errors='ignore')

    # ====================================================================
    # SUMMARY
    # ====================================================================

    total = len(df)
    has_signal = (df['refi_signals'] != '').sum()
    high_priority = (df['refi_priority'] == 'High').sum()
    med_priority = (df['refi_priority'] == 'Medium').sum()
    cash_buyers = df['probable_cash_buyer'].sum()
    rate_refi = df['rate_refi_candidate'].sum()
    brrrr = df['brrrr_exit_candidate'].sum()
    equity_harvest = df['equity_harvest_candidate'].sum()

    print(f"\n{'='*60}")
    print(f"REFINANCE CANDIDATE SUMMARY")
    print(f"{'='*60}")
    print(f"Total leads analyzed:          {total:,}")
    print(f"With refi signal:              {has_signal:,} ({has_signal/total*100:.1f}%)")
    print(f"  High priority:               {high_priority:,}")
    print(f"  Medium priority:             {med_priority:,}")
    print(f"")
    print(f"BY SIGNAL TYPE:")
    print(f"  Probable cash buyers:        {cash_buyers:,}")
    print(f"  Equity harvest candidates:   {equity_harvest:,}")
    print(f"  Rate refi (2022-2023):       {rate_refi:,}")
    print(f"  BRRRR exit candidates:       {brrrr:,}")
    print(f"")
    if has_signal > 0:
        avg_equity = df.loc[df['refi_signals'] != '', 'estimated_equity'].mean()
        avg_cashout = df.loc[df['refi_signals'] != '', 'max_cashout_75'].mean()
        total_cashout = df.loc[df['refi_signals'] != '', 'max_cashout_75'].sum()
        print(f"EQUITY OPPORTUNITY:")
        print(f"  Avg equity (refi candidates):    ${avg_equity:,.0f}")
        print(f"  Avg cash-out @ 75% LTV:          ${avg_cashout:,.0f}")
        print(f"  Total cash-out potential @ 75%:   ${total_cashout:,.0f}")

    return df


def main():
    parser = argparse.ArgumentParser(description='Detect DSCR refinance candidates')
    parser.add_argument('--input', type=str, default='pipeline/output/01_investor_properties.csv')
    parser.add_argument('--sdf-dir', type=str, default='pipeline/data/fdor',
                        help='Directory containing SDF files for county median calculation')
    parser.add_argument('--output', type=str, default='pipeline/output/08_refi_tagged.csv')

    args = parser.parse_args()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Compute county medians from SDF data
    print("Computing county median sale prices...")
    county_medians = compute_county_medians(args.sdf_dir)
    print(f"  Medians computed for {len(county_medians)} counties")

    # Load investor properties
    print("\nLoading investor properties...")
    df = pd.read_csv(args.input, dtype=str, low_memory=False)
    print(f"  Loaded {len(df):,} records")

    # Detect refinance signals
    df = detect_refi_signals(df, county_medians)

    # Save output
    df.to_csv(args.output, index=False)
    print(f"\nOutput saved: {args.output}")


if __name__ == '__main__':
    main()
```

## Integration into Pipeline

Module 8 runs **after Module 1** (FDOR download/filter) and its output feeds into Module 2 (SunBiz resolution). The updated pipeline flow:

```
Module 1 (FDOR) → Module 8 (Refi Detection) → Module 2 (SunBiz) → Module 3 (DBPR) → ...
```

The `refi_score_boost` from this module is added to the base score in Module 6 (Scoring).

## New ICP Sub-Segments Created

| Sub-Segment | Signal | Estimated Volume (FL) | Priority |
|---|---|---|---|
| **All-Cash Investor (Leverage-Up)** | 100% equity, no mortgage, owned 6mo+ | 43K-45K purchases/year | **Tier 1** |
| **Equity Harvester** | 30%+ equity, owned 2+ years | 100K+ owners | **Tier 1** |
| **Rate Refi Candidate** | Purchased 2022-2023 at 7-8%+ rates | 30K-50K owners | **Tier 2** |
| **BRRRR Exit** | Below-market purchase <12 months ago | 5K-10K/year | **Tier 1** |
| **Portfolio Equity Harvest** | 3+ properties, 35%+ avg equity | 10K-20K owners | **Tier 1** |

## Revenue Impact Estimate

If Frank's team captures just **0.5% of the all-cash investor refi opportunity:**

```
45,000 all-cash investor purchases/year in FL
× 50% could benefit from DSCR cash-out (conservative)
= 22,500 potential cash-out refi deals
× 0.5% capture rate
= 112 deals/year
× avg $300K loan amount
× ~2% total compensation
= $672,000 annual revenue from this ONE sub-segment
```

## Data Limitation & Future Enhancement

The biggest gap: **FDOR data doesn't contain mortgage information.** We're estimating equity from Just Value vs. Sale Price, which assumes the original purchase price approximates the original mortgage. In reality:

- Some investors made large down payments (equity is higher than our estimate)
- Some investors have already refinanced (equity may be lower)
- All-cash buyers have much MORE equity than our model shows

**Future enhancement:** Integrate county Clerk of Court mortgage recording data to precisely identify:
- Properties with no mortgage (confirmed free-and-clear)
- Lender names (hard money lender = confirmed BRRRR candidate)
- Mortgage amounts (precise equity calculation)
- Satisfaction of mortgage records (confirmed payoff = free-and-clear)

This requires either county-by-county Clerk portal scraping or a paid data provider (ATTOM Data Solutions).
