"""Select 500 diverse pilot leads weighted across ICP segments.
Filter: mailing or property in Palm Beach (CO_NO=60) or Broward (CO_NO=6)."""
import csv
from collections import defaultdict

with open('scrape/data/enriched/merged_enriched.csv', 'r', encoding='utf-8') as f:
    rows = list(csv.DictReader(f))

def val(r, field):
    try: return float(r.get(field, 0) or 0)
    except: return 0

def flag(r, field):
    v = r.get(field, '').strip().lower()
    return v in ('true', '1', 'yes')

# ---- STEP 1: Filter to PB/Broward ----
# CO_NO = county of PROPERTY. Check mailing address too.
pb_zips = set()  # We'll use county code since we have it
broward_zips = set()

def is_pb_or_broward(r):
    co = r.get('CO_NO', '').strip()
    if co in ('60', '06', '6'):  # 60=Palm Beach, 6=Broward (some data uses '06')
        return True
    # Check mailing city for known PB/Broward cities
    city = r.get('OWN_CITY', '').strip().upper()
    pb_cities = {'WEST PALM BEACH', 'PALM BEACH', 'BOCA RATON', 'DELRAY BEACH',
                 'BOYNTON BEACH', 'LAKE WORTH', 'JUPITER', 'PALM BEACH GARDENS',
                 'ROYAL PALM BEACH', 'WELLINGTON', 'RIVIERA BEACH', 'GREENACRES',
                 'BELLE GLADE', 'LANTANA', 'NORTH PALM BEACH', 'PAHOKEE',
                 'PALM SPRINGS', 'LOXAHATCHEE', 'TEQUESTA', 'JUNO BEACH',
                 'MANGONIA PARK', 'GLEN RIDGE', 'HAVERHILL', 'CLOUD LAKE',
                 'HYPOLUXO', 'MANALAPAN', 'OCEAN RIDGE', 'SOUTH PALM BEACH',
                 'HIGHLAND BEACH', 'GULF STREAM'}
    broward_cities = {'FORT LAUDERDALE', 'FT LAUDERDALE', 'HOLLYWOOD', 'POMPANO BEACH',
                      'CORAL SPRINGS', 'PLANTATION', 'DAVIE', 'SUNRISE', 'DEERFIELD BEACH',
                      'LAUDERHILL', 'WESTON', 'MIRAMAR', 'PEMBROKE PINES', 'COCONUT CREEK',
                      'TAMARAC', 'MARGATE', 'DANIA', 'DANIA BEACH', 'HALLANDALE',
                      'HALLANDALE BEACH', 'LIGHTHOUSE POINT', 'LAUDERDALE LAKES',
                      'NORTH LAUDERDALE', 'OAKLAND PARK', 'WILTON MANORS',
                      'COOPER CITY', 'PARKLAND', 'SOUTHWEST RANCHES', 'LAZY LAKE',
                      'SEA RANCH LAKES', 'HILLSBORO BEACH', 'LAUDERDALE BY THE SEA'}
    if city in pb_cities or city in broward_cities:
        return True
    # Check mailing state = FL and ZIP starts with 33 (South FL)
    state = r.get('OWN_STATE', '').strip().upper()
    zipcode = r.get('OWN_ZIPCD', '').strip()[:5]
    if state in ('FL', 'FLORIDA') and zipcode.startswith('33'):
        return True  # South FL — close enough for pilot
    return False

eligible = [r for r in rows if is_pb_or_broward(r)]
print(f'Total records: {len(rows)}')
print(f'PB/Broward eligible: {len(eligible)}')
print()

# ---- STEP 2: Classify each lead ----
for r in eligible:
    props = int(val(r, 'property_count'))
    is_entity = flag(r, 'is_entity')
    str_licensed = flag(r, 'str_licensed')
    foreign = flag(r, 'foreign_owner')
    cash_buyer = flag(r, 'probable_cash_buyer')
    brrrr = flag(r, 'brrrr_exit_candidate')
    equity_harvest = flag(r, 'equity_harvest_candidate')
    rate_refi = flag(r, 'rate_refi_candidate')
    out_of_state = flag(r, 'out_of_state')

    # Primary ICP
    if props >= 10:
        r['_icp'] = 'Serial Investor (10+)'
    elif str_licensed and props >= 2:
        r['_icp'] = 'STR Operator'
    elif foreign:
        r['_icp'] = 'Foreign National'
    elif is_entity and props >= 5:
        r['_icp'] = 'Entity Investor (5-9)'
    elif is_entity and props >= 2:
        r['_icp'] = 'Entity Investor (2-4)'
    elif not is_entity and props >= 5:
        r['_icp'] = 'Individual Investor (5-9)'
    elif not is_entity and props >= 2:
        r['_icp'] = 'Individual Investor (2-4)'
    elif str_licensed:
        r['_icp'] = 'STR Operator'
    else:
        r['_icp'] = 'Single Property'

    # Refi overlay — can belong to multiple
    r['_is_brrrr'] = brrrr
    r['_is_cash_buyer'] = cash_buyer
    r['_is_equity_harvest'] = equity_harvest
    r['_is_rate_refi'] = rate_refi
    r['_has_refi'] = brrrr or cash_buyer or equity_harvest or rate_refi
    r['_props'] = props
    r['_value'] = val(r, 'total_portfolio_value')

    # Profile score (for ranking within segment)
    score = 0
    if props >= 20: score += 30
    elif props >= 10: score += 25
    elif props >= 5: score += 20
    elif props >= 3: score += 15
    elif props >= 2: score += 10
    if r['_value'] >= 3_000_000: score += 15
    elif r['_value'] >= 1_000_000: score += 10
    elif r['_value'] >= 500_000: score += 5
    if flag(r, 'is_absentee'): score += 5
    if is_entity: score += 5
    if str_licensed: score += 10
    if cash_buyer: score += 15
    if brrrr: score += 15
    if equity_harvest: score += 10
    if rate_refi: score += 5
    if out_of_state: score += 5
    r['_score'] = score

# ---- STEP 3: Show available pool by segment ----
segments = defaultdict(list)
for r in eligible:
    segments[r['_icp']].append(r)

# Also tag refi-overlay segments
refi_brrrr = [r for r in eligible if r['_is_brrrr']]
refi_equity = [r for r in eligible if r['_is_equity_harvest']]
refi_cash = [r for r in eligible if r['_is_cash_buyer']]

print('ELIGIBLE POOL BY SEGMENT:')
print(f'  Serial Investor (10+):     {len(segments.get("Serial Investor (10+)", []))}')
print(f'  STR Operator:              {len(segments.get("STR Operator", []))}')
print(f'  Foreign National:          {len(segments.get("Foreign National", []))}')
print(f'  Entity Investor (5-9):     {len(segments.get("Entity Investor (5-9)", []))}')
print(f'  Entity Investor (2-4):     {len(segments.get("Entity Investor (2-4)", []))}')
print(f'  Individual Investor (5-9): {len(segments.get("Individual Investor (5-9)", []))}')
print(f'  Individual Investor (2-4): {len(segments.get("Individual Investor (2-4)", []))}')
print(f'  Single Property:           {len(segments.get("Single Property", []))}')
print()
print('REFI OVERLAY (cross-cutting):')
print(f'  BRRRR exit candidates:     {len(refi_brrrr)}')
print(f'  Equity harvest:            {len(refi_equity)}')
print(f'  Cash buyers:               {len(refi_cash)}')
print()

# ---- STEP 4: Build the 500 ----
# Target allocation: diverse but weighted toward refi + high-value
# Refi signals get ~40% (200), remaining segments fill ~60% (300)

allocation = {
    # High-value segments
    'Serial Investor (10+)': 60,      # All 10+ property owners — whales
    'STR Operator': 40,               # Vacation rental operators
    'Entity Investor (5-9)': 80,      # Sophisticated, entity-structured
    'Individual Investor (5-9)': 60,  # Growing portfolios
    # Mid-tier segments
    'Entity Investor (2-4)': 80,      # Bread and butter
    'Individual Investor (2-4)': 150, # Largest pool, good mix
    # Niche
    'Foreign National': 1,            # Tiny pool
    'Single Property': 10,            # Control group — should score low
}

# Adjust if a segment doesn't have enough
selected = []
used_ids = set()
remaining_budget = 500

print('PILOT 500 ALLOCATION:')
print(f'  {"Segment":<30} {"Target":>6} {"Available":>9} {"Selected":>8}')
print(f'  {"-"*30} {"-"*6} {"-"*9} {"-"*8}')

for seg_name in ['Serial Investor (10+)', 'STR Operator', 'Entity Investor (5-9)',
                 'Individual Investor (5-9)', 'Entity Investor (2-4)',
                 'Individual Investor (2-4)', 'Foreign National', 'Single Property']:
    pool = segments.get(seg_name, [])
    target = allocation.get(seg_name, 0)

    # Sort by score descending, then by refi signal (refi first)
    pool.sort(key=lambda r: (r['_has_refi'], r['_score'], r['_value']), reverse=True)

    # Deduplicate by OWN_NAME (same entity can appear multiple times)
    seg_selected = []
    seen_names = set()
    for r in pool:
        name = r.get('OWN_NAME', '').strip().upper()
        if name in seen_names:
            continue
        seen_names.add(name)
        seg_selected.append(r)
        if len(seg_selected) >= target:
            break

    actual = len(seg_selected)
    selected.extend(seg_selected)
    remaining_budget -= actual

    refi_in_seg = sum(1 for r in seg_selected if r['_has_refi'])
    print(f'  {seg_name:<30} {target:>6} {len(pool):>9} {actual:>8}  ({refi_in_seg} with refi signal)')

# If we're short of 500, fill from highest-scoring remaining
if remaining_budget > 0:
    used_names = {r.get('OWN_NAME','').strip().upper() for r in selected}
    remaining = [r for r in eligible if r.get('OWN_NAME','').strip().upper() not in used_names]
    remaining.sort(key=lambda r: (r['_has_refi'], r['_score'], r['_value']), reverse=True)
    for r in remaining:
        if remaining_budget <= 0:
            break
        name = r.get('OWN_NAME','').strip().upper()
        if name not in used_names:
            selected.append(r)
            used_names.add(name)
            remaining_budget -= 1

print(f'\n  TOTAL SELECTED: {len(selected)}')

# ---- STEP 5: Summary stats of the 500 ----
print()
print('='*60)
print('PILOT 500 — PROFILE SUMMARY')
print('='*60)

total_refi = sum(1 for r in selected if r['_has_refi'])
total_brrrr = sum(1 for r in selected if r['_is_brrrr'])
total_equity = sum(1 for r in selected if r['_is_equity_harvest'])
total_cash = sum(1 for r in selected if r['_is_cash_buyer'])
total_str = sum(1 for r in selected if flag(r, 'str_licensed'))
total_entity = sum(1 for r in selected if flag(r, 'is_entity'))
avg_props = sum(r['_props'] for r in selected) / len(selected)
avg_value = sum(r['_value'] for r in selected) / len(selected)
total_value = sum(r['_value'] for r in selected)

print(f'  Total leads:          {len(selected)}')
print(f'  Avg properties:       {avg_props:.1f}')
print(f'  Avg portfolio value:  ${avg_value:,.0f}')
print(f'  Total portfolio value:${total_value:,.0f}')
print(f'  With refi signal:     {total_refi} ({total_refi*100//len(selected)}%)')
print(f'    BRRRR exit:         {total_brrrr}')
print(f'    Equity harvest:     {total_equity}')
print(f'    Cash buyer:         {total_cash}')
print(f'  STR operators:        {total_str}')
print(f'  Entity-owned:         {total_entity}')
print()

# Score distribution
s50 = sum(1 for r in selected if r['_score'] >= 50)
s35 = sum(1 for r in selected if 35 <= r['_score'] < 50)
s20 = sum(1 for r in selected if 20 <= r['_score'] < 35)
s0 = sum(1 for r in selected if r['_score'] < 20)
print(f'  Score 50+ (hot):      {s50}')
print(f'  Score 35-49 (warm):   {s35}')
print(f'  Score 20-34 (mild):   {s20}')
print(f'  Score <20 (cold):     {s0}')

# ICP mix
print()
print('  ICP MIX:')
icp_mix = defaultdict(int)
for r in selected:
    icp_mix[r['_icp']] += 1
for icp, count in sorted(icp_mix.items(), key=lambda x: -x[1]):
    pct = count * 100 // len(selected)
    print(f'    {icp:<30} {count:>4} ({pct}%)')

# Has contact info?
has_phone = sum(1 for r in selected if r.get('phone_1','').strip() or r.get('phone','').strip() or r.get('str_phone','').strip())
has_email = sum(1 for r in selected if r.get('email_1','').strip() or r.get('email','').strip() or r.get('str_email','').strip())
print()
print(f'  Already have phone:   {has_phone} ({has_phone*100//len(selected)}%)')
print(f'  Already have email:   {has_email} ({has_email*100//len(selected)}%)')
print(f'  Need enrichment:      {len(selected) - has_phone} (no phone yet)')
