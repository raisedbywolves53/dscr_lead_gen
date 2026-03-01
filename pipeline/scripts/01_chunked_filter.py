"""
Step 1: FDOR NAL Chunked Filter — Memory-Efficient Version

Reads the Palm Beach NAL file in chunks, filters for investor properties,
and aggregates by owner. Avoids OOM by never loading full 343MB CSV at once.
"""

import pandas as pd
from pathlib import Path
from datetime import date

# Config
NAL_FILE = Path("pipeline/data/fdor/NAL_60_PALM_BEACH.csv")
OUTPUT_FILE = Path("pipeline/output/01_investor_properties.csv")
CHUNK_SIZE = 50000  # rows per chunk

RESIDENTIAL_USE_CODES = {1, 2, 3, 4, 8}

ENTITY_KEYWORDS = [
    " LLC", " L.L.C", " INC", " CORP", " TRUST", " LP ", " LTD",
    " HOLDINGS", " PROPERTIES", " INVESTMENTS", " CAPITAL", " VENTURES",
    " PARTNERS", " PARTNERSHIP", " FUND", " GROUP",
    " ENTERPRISES", " REALTY", " REAL ESTATE", " MANAGEMENT"
]

# Only load columns we need — huge memory savings
USE_COLS = [
    'CO_NO', 'PARCEL_ID', 'DOR_UC', 'JV', 'AV_HMSTD',
    'OWN_NAME', 'OWN_ADDR1', 'OWN_ADDR2', 'OWN_CITY', 'OWN_STATE', 'OWN_ZIPCD',
    'OWN_STATE_DOM',
    'PHY_ADDR1', 'PHY_ADDR2', 'PHY_CITY', 'PHY_ZIPCD',
    'SALE_PRC1', 'SALE_YR1', 'SALE_MO1',  # Most recent sale data for refi detection
]

def is_entity_owned(owner_name: str) -> bool:
    if not owner_name:
        return False
    upper = owner_name.upper()
    return any(kw in upper for kw in ENTITY_KEYWORDS)


def process_chunk(chunk: pd.DataFrame) -> pd.DataFrame:
    """Filter a chunk for investment properties."""

    # Step 1: Residential use codes only
    chunk['DOR_UC_INT'] = pd.to_numeric(chunk['DOR_UC'].astype(str).str.strip(), errors='coerce').fillna(-1).astype(int)
    residential = chunk[chunk['DOR_UC_INT'].isin(RESIDENTIAL_USE_CODES)].copy()
    if residential.empty:
        return pd.DataFrame()

    # Step 2: Non-homesteaded (AV_HMSTD == 0)
    residential['AV_HMSTD'] = pd.to_numeric(residential['AV_HMSTD'], errors='coerce').fillna(0)
    non_homestead = residential[residential['AV_HMSTD'] == 0].copy()
    if non_homestead.empty:
        return pd.DataFrame()

    # Step 3: Flag entity ownership
    non_homestead['is_entity'] = non_homestead['OWN_NAME'].apply(
        lambda x: is_entity_owned(str(x)) if pd.notna(x) else False
    )

    # Step 4: Flag absentee owners
    non_homestead['is_absentee'] = (
        non_homestead['OWN_ADDR1'].astype(str).str.upper().str.strip() !=
        non_homestead['PHY_ADDR1'].astype(str).str.upper().str.strip()
    )

    # Step 5: Out-of-state and foreign owners
    us_state_codes = {
        'AL','AK','AZ','AR','CA','CO','CT','DE','FL','GA','HI','ID','IL','IN',
        'IA','KS','KY','LA','ME','MD','MA','MI','MN','MS','MO','MT','NE','NV',
        'NH','NJ','NM','NY','NC','ND','OH','OK','OR','PA','RI','SC','SD','TN',
        'TX','UT','VT','VA','WA','WV','WI','WY','DC','PR','VI','GU','AS','MP'
    }
    state_vals = non_homestead['OWN_STATE_DOM'].astype(str).str.strip().str.upper()
    non_homestead['out_of_state'] = (state_vals != 'FL') & (state_vals != '') & (state_vals != 'NAN')
    non_homestead['foreign_owner'] = ~state_vals.isin(us_state_codes) & (state_vals != '') & (state_vals != 'NAN')

    return non_homestead


def main():
    Path("pipeline/output").mkdir(parents=True, exist_ok=True)

    print(f"Processing NAL file in chunks of {CHUNK_SIZE:,}...")
    print(f"Source: {NAL_FILE}")

    all_investors = []
    total_parcels = 0
    total_residential = 0
    total_non_homestead = 0

    for i, chunk in enumerate(pd.read_csv(NAL_FILE, dtype=str, low_memory=False,
                                           usecols=USE_COLS, chunksize=CHUNK_SIZE)):
        total_parcels += len(chunk)
        filtered = process_chunk(chunk)

        if not filtered.empty:
            total_non_homestead += len(filtered)
            all_investors.append(filtered)

        if (i + 1) % 5 == 0:
            print(f"  Processed {total_parcels:,} parcels, {total_non_homestead:,} investor properties so far...")

    if not all_investors:
        print("No investor properties found!")
        return

    # Combine chunks
    print(f"\nCombining {len(all_investors)} chunks...")
    combined = pd.concat(all_investors, ignore_index=True)
    print(f"Total investor properties (pre-aggregation): {len(combined):,}")

    # Aggregate by owner
    print("Aggregating by owner...")
    combined['JV'] = pd.to_numeric(combined['JV'], errors='coerce').fillna(0)
    combined['SALE_PRC1'] = pd.to_numeric(combined['SALE_PRC1'], errors='coerce').fillna(0)
    combined['SALE_YR1'] = pd.to_numeric(combined['SALE_YR1'], errors='coerce').fillna(0)
    combined['SALE_MO1'] = pd.to_numeric(combined['SALE_MO1'], errors='coerce').fillna(1)

    # Build a sale date string for most recent sale per property
    combined['_sale_date'] = combined.apply(
        lambda r: f"{int(r['SALE_YR1'])}-{int(r['SALE_MO1']):02d}-01"
        if r['SALE_YR1'] > 1900 else '', axis=1
    )

    grouped = combined.groupby(
        ['OWN_NAME', 'OWN_ADDR1', 'OWN_CITY', 'OWN_STATE', 'OWN_ZIPCD'],
        dropna=False
    ).agg({
        'PARCEL_ID': 'count',
        'JV': ['sum', 'mean'],                  # total and avg portfolio value
        'SALE_PRC1': ['max', 'mean'],            # most recent and avg sale price
        '_sale_date': 'max',                     # most recent purchase date
        'PHY_ADDR1': lambda x: ' | '.join(x.dropna().unique()[:5]),
        'DOR_UC': lambda x: ','.join(sorted(x.dropna().unique())),
        'CO_NO': lambda x: ','.join(sorted(x.dropna().unique())),
        'is_entity': 'max',
        'is_absentee': 'max',
        'out_of_state': 'max',
        'foreign_owner': 'max',
        'OWN_STATE_DOM': 'first',
    }).reset_index()

    # Flatten multi-level columns
    grouped.columns = [
        '_'.join(col).strip('_') if isinstance(col, tuple) else col
        for col in grouped.columns
    ]

    grouped = grouped.rename(columns={
        'PARCEL_ID_count': 'property_count',
        'JV_sum': 'total_portfolio_value',
        'JV_mean': 'avg_property_value',
        'SALE_PRC1_max': 'most_recent_price',
        'SALE_PRC1_mean': 'avg_sale_price',
        '_sale_date_max': 'most_recent_purchase',
        'DOR_UC_<lambda>': 'property_types',
        'CO_NO_<lambda>': 'CO_NO',
        'PHY_ADDR1_<lambda>': 'PHY_ADDR1',
        'is_entity_max': 'is_entity',
        'is_absentee_max': 'is_absentee',
        'out_of_state_max': 'out_of_state',
        'foreign_owner_max': 'foreign_owner',
        'OWN_STATE_DOM_first': 'OWN_STATE_DOM',
    })

    # Sort by property count descending
    grouped = grouped.sort_values('property_count', ascending=False)

    # Save
    grouped.to_csv(OUTPUT_FILE, index=False)

    # Summary
    print(f"\n{'='*60}")
    print(f"STEP 1 COMPLETE — FDOR INVESTOR PROPERTIES")
    print(f"{'='*60}")
    print(f"Total parcels scanned:     {total_parcels:,}")
    print(f"Investor properties:       {total_non_homestead:,}")
    print(f"Unique owner leads:        {len(grouped):,}")
    print(f"Entity-owned:              {grouped['is_entity'].sum():,}")
    print(f"Out-of-state:              {grouped['out_of_state'].sum():,}")
    print(f"Foreign owners:            {grouped['foreign_owner'].sum():,}")
    print(f"Multi-property (2+):       {(grouped['property_count'] >= 2).sum():,}")
    print(f"Serial (10+):              {(grouped['property_count'] >= 10).sum():,}")
    print(f"Output: {OUTPUT_FILE}")


if __name__ == '__main__':
    main()
