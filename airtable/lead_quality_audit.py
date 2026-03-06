"""Profile all 7,537 leads by ICP segment — ignore contact info, focus on investor quality."""
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

# Classify each lead by primary ICP
for r in rows:
    props = int(val(r, 'property_count'))
    portfolio_val = val(r, 'total_portfolio_value')
    is_entity = flag(r, 'is_entity')
    is_absentee = flag(r, 'is_absentee')
    out_of_state = flag(r, 'out_of_state')
    foreign = flag(r, 'foreign_owner')
    str_licensed = flag(r, 'str_licensed')
    cash_buyer = flag(r, 'probable_cash_buyer')
    refi = val(r, 'refi_score_boost') > 0
    brrrr = flag(r, 'brrrr_exit_candidate')
    equity_harvest = flag(r, 'equity_harvest_candidate')
    rate_refi = flag(r, 'rate_refi_candidate')

    # Primary ICP (highest priority first per ICP_DEFINITIONS.md)
    if props >= 10:
        r['_icp'] = 'Serial Investor (10+)'
    elif str_licensed:
        r['_icp'] = 'STR Operator'
    elif foreign:
        r['_icp'] = 'Foreign National'
    elif is_entity and props >= 2:
        r['_icp'] = 'Entity Investor (2-9)'
    elif not is_entity and props >= 2:
        r['_icp'] = 'Individual Investor (2-9)'
    elif props == 1 and is_entity:
        r['_icp'] = 'Single Prop (Entity)'
    else:
        r['_icp'] = 'Single Prop (Individual)'

    # Refi overlay
    refi_signals = []
    if cash_buyer: refi_signals.append('Cash Buyer')
    if brrrr: refi_signals.append('BRRRR Exit')
    if equity_harvest: refi_signals.append('Equity Harvest')
    if rate_refi: refi_signals.append('Rate Refi')
    r['_refi_signals'] = refi_signals
    r['_has_refi'] = len(refi_signals) > 0
    r['_props'] = props
    r['_value'] = portfolio_val
    r['_absentee'] = is_absentee
    r['_out_of_state'] = out_of_state

# ---- ICP DISTRIBUTION ----
print('='*60)
print('ICP SEGMENT DISTRIBUTION (all 7,537 leads)')
print('='*60)
icp_counts = defaultdict(int)
for r in rows:
    icp_counts[r['_icp']] += 1

icp_order = ['Serial Investor (10+)', 'STR Operator', 'Foreign National',
             'Entity Investor (2-9)', 'Individual Investor (2-9)',
             'Single Prop (Entity)', 'Single Prop (Individual)']
for icp in icp_order:
    c = icp_counts.get(icp, 0)
    bar = '#' * (c // 30)
    print(f'  {icp:<28} {c:>5}  {bar}')
print(f'  {"TOTAL":<28} {len(rows):>5}')

# ---- REFI SIGNAL OVERLAY ----
print()
print('='*60)
print('REFI SIGNAL OVERLAY')
print('='*60)
has_any_refi = sum(1 for r in rows if r['_has_refi'])
cash = sum(1 for r in rows if flag(r, 'probable_cash_buyer'))
brr = sum(1 for r in rows if flag(r, 'brrrr_exit_candidate'))
eq = sum(1 for r in rows if flag(r, 'equity_harvest_candidate'))
rate = sum(1 for r in rows if flag(r, 'rate_refi_candidate'))
print(f'  Any refi signal:    {has_any_refi}')
print(f'  Cash buyer:         {cash}')
print(f'  BRRRR exit:         {brr}')
print(f'  Equity harvest:     {eq}')
print(f'  Rate refi:          {rate}')

# ---- PORTFOLIO SIZE DISTRIBUTION ----
print()
print('='*60)
print('PORTFOLIO SIZE DISTRIBUTION')
print('='*60)
brackets = [(20, '20+'), (10, '10-19'), (5, '5-9'), (3, '3-4'), (2, '2'), (1, '1')]
for threshold, label in brackets:
    if threshold == 20:
        c = sum(1 for r in rows if r['_props'] >= 20)
    elif threshold == 10:
        c = sum(1 for r in rows if 10 <= r['_props'] < 20)
    elif threshold == 5:
        c = sum(1 for r in rows if 5 <= r['_props'] < 10)
    elif threshold == 3:
        c = sum(1 for r in rows if 3 <= r['_props'] < 5)
    elif threshold == 2:
        c = sum(1 for r in rows if r['_props'] == 2)
    else:
        c = sum(1 for r in rows if r['_props'] == 1)
    bar = '#' * (c // 30)
    print(f'  {label:<12} {c:>5}  {bar}')

# ---- VALUE DISTRIBUTION ----
print()
print('='*60)
print('PORTFOLIO VALUE DISTRIBUTION')
print('='*60)
val_brackets = [(5_000_000, '$5M+'), (3_000_000, '$3M-$5M'), (1_000_000, '$1M-$3M'),
                (500_000, '$500K-$1M'), (250_000, '$250K-$500K'), (0, 'Under $250K')]
for threshold, label in val_brackets:
    if threshold == 5_000_000:
        c = sum(1 for r in rows if r['_value'] >= 5_000_000)
    elif threshold == 3_000_000:
        c = sum(1 for r in rows if 3_000_000 <= r['_value'] < 5_000_000)
    elif threshold == 1_000_000:
        c = sum(1 for r in rows if 1_000_000 <= r['_value'] < 3_000_000)
    elif threshold == 500_000:
        c = sum(1 for r in rows if 500_000 <= r['_value'] < 1_000_000)
    elif threshold == 250_000:
        c = sum(1 for r in rows if 250_000 <= r['_value'] < 500_000)
    else:
        c = sum(1 for r in rows if r['_value'] < 250_000)
    bar = '#' * (c // 30)
    print(f'  {label:<16} {c:>5}  {bar}')

# ---- QUALITATIVE FILTERS ----
print()
print('='*60)
print('OTHER PROFILE ATTRIBUTES')
print('='*60)
print(f'  Absentee owner:     {sum(1 for r in rows if r["_absentee"])}')
print(f'  Out of state:       {sum(1 for r in rows if r["_out_of_state"])}')
print(f'  Entity-owned:       {sum(1 for r in rows if flag(r, "is_entity"))}')
print(f'  STR licensed:       {sum(1 for r in rows if flag(r, "str_licensed"))}')
print(f'  Foreign owner:      {sum(1 for r in rows if flag(r, "foreign_owner"))}')
print(f'  Has entity officers:{sum(1 for r in rows if r.get("entity_officers","").strip())}')

# ---- PILOT RECOMMENDATION ----
# "Worth fully enriching" = multi-property + absentee + has some signal
print()
print('='*60)
print('PILOT CANDIDATES — STRONGEST PROFILES')
print('='*60)

# Score each lead purely on profile quality (not contact)
for r in rows:
    score = 0
    if r['_props'] >= 10: score += 30
    elif r['_props'] >= 5: score += 20
    elif r['_props'] >= 3: score += 15
    elif r['_props'] >= 2: score += 10

    if r['_value'] >= 3_000_000: score += 15
    elif r['_value'] >= 1_000_000: score += 10
    elif r['_value'] >= 500_000: score += 5

    if r['_absentee']: score += 10
    if flag(r, 'is_entity'): score += 5
    if flag(r, 'str_licensed'): score += 10
    if flag(r, 'probable_cash_buyer'): score += 15
    if flag(r, 'brrrr_exit_candidate'): score += 15
    if flag(r, 'equity_harvest_candidate'): score += 10
    if flag(r, 'rate_refi_candidate'): score += 5
    if flag(r, 'foreign_owner'): score += 10
    r['_profile_score'] = score

# Tier by profile score
hot = [r for r in rows if r['_profile_score'] >= 50]
warm = [r for r in rows if 35 <= r['_profile_score'] < 50]
mild = [r for r in rows if 20 <= r['_profile_score'] < 35]
cold = [r for r in rows if r['_profile_score'] < 20]

print(f'  HOT  (score 50+):  {len(hot):>5} — Multi-property + signals, highest value')
print(f'  WARM (score 35-49): {len(warm):>5} — Solid investors, some signals')
print(f'  MILD (score 20-34): {len(mild):>5} — Smaller portfolios, fewer signals')
print(f'  COLD (score <20):  {len(cold):>5} — Single property, no signals')

print()
hot.sort(key=lambda r: r['_profile_score'], reverse=True)
print(f'TOP 30 HOT LEADS (by profile only):')
for i, r in enumerate(hot[:30]):
    own = r.get('OWN_NAME','').strip()
    person = r.get('resolved_person','').strip()
    officers = r.get('entity_officers','').strip()[:50]
    name = person if person else own
    signals = r['_refi_signals']
    sig_str = ', '.join(signals) if signals else '-'
    print(f'  {i+1:>2}. [{r["_profile_score"]:>2}pts] {name:<35} | {r["_icp"]:<25} | {r["_props"]} props | ${r["_value"]:,.0f} | {sig_str}')
