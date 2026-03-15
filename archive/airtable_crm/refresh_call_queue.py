#!/usr/bin/env python3
"""
refresh_call_queue.py — Enrich Investors table with call-ready summary fields.

Reads Investors, Properties, Financing, and Outreach Log tables from Airtable,
computes 6 summary fields per investor, and writes them back. Run before each
dial session so the "Call Queue" view has everything at a glance.

Usage:
    python airtable/refresh_call_queue.py              # Full refresh
    python airtable/refresh_call_queue.py --dry-run    # Preview without writing
    python airtable/refresh_call_queue.py --target-rate 0.065  # Custom benchmark rate
"""

import os, sys, time, argparse
from datetime import datetime, date
from collections import defaultdict

import requests
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

load_dotenv()

API_TOKEN = os.getenv('AIRTABLE_API_TOKEN')
BASE_ID = 'appJV7J1ZrNEBAWAm'
HEADERS = {
    'Authorization': f'Bearer {API_TOKEN}',
    'Content-Type': 'application/json',
}

# Table IDs (from create_remaining_fields.py)
INVESTORS = 'tbla2NnrEDSFA3UFP'
PROPERTIES = 'tblVXwCSkubWp30UO'
FINANCING = 'tblh4OgGSpyf6hSfX'
OUTREACH = 'tbl0uK5dE9orqCeq9'

# Fields to create on the Investors table (if missing)
CALL_QUEUE_FIELDS = [
    {"name": "Trigger Summary", "type": "multilineText"},
    {"name": "Portfolio Snapshot", "type": "multilineText"},
    {"name": "Current Lenders", "type": "singleLineText"},
    {
        "name": "Estimated Monthly Savings",
        "type": "currency",
        "options": {"precision": 0, "symbol": "$"},
    },
    {"name": "Last Outreach Summary", "type": "singleLineText"},
    {"name": "Call Priority", "type": "singleLineText"},
]

DEFAULT_TARGET_RATE = 0.07   # 7.0% DSCR benchmark
DEFAULT_TERM_MONTHS = 360    # 30-year amortization for DSCR refi


# ---------------------------------------------------------------------------
# API helpers
# ---------------------------------------------------------------------------

def api_call(method, url, **kwargs):
    """Make an Airtable API call with retry on rate limits."""
    for attempt in range(5):
        resp = requests.request(method, url, headers=HEADERS, **kwargs)
        if resp.status_code == 429:
            wait = int(resp.headers.get('Retry-After', 30))
            print(f"  Rate limited, waiting {wait}s...")
            time.sleep(wait)
            continue
        if resp.status_code >= 400:
            print(f"  API error {resp.status_code}: {resp.text[:300]}")
            return None
        time.sleep(0.22)  # stay under 5 req/s
        return resp.json()
    print("  Max retries exceeded")
    return None


def fetch_all_records(table_id, table_name):
    """Paginated fetch of all records from a table."""
    records = []
    offset = None
    page = 0
    while True:
        page += 1
        url = f'https://api.airtable.com/v0/{BASE_ID}/{table_id}'
        params = {}
        if offset:
            params['offset'] = offset
        data = api_call('GET', url, params=params)
        if data is None:
            print(f"  ERROR: Failed to fetch {table_name} page {page}")
            break
        records.extend(data.get('records', []))
        offset = data.get('offset')
        if not offset:
            break
    print(f"  {table_name}: {len(records)} records")
    return records


def patch_records(table_id, batch):
    """Update up to 10 records in a single PATCH call."""
    url = f'https://api.airtable.com/v0/{BASE_ID}/{table_id}'
    return api_call('PATCH', url, json={"records": batch})


# ---------------------------------------------------------------------------
# Schema management — ensure the 6 fields exist on Investors
# ---------------------------------------------------------------------------

def ensure_fields_exist():
    """Check Investors schema and create any missing call-queue fields."""
    url = f'https://api.airtable.com/v0/meta/bases/{BASE_ID}/tables'
    data = api_call('GET', url)
    if data is None:
        print("ERROR: Cannot read base schema")
        sys.exit(1)

    inv_table = next((t for t in data['tables'] if t['id'] == INVESTORS), None)
    if inv_table is None:
        print("ERROR: Investors table not found")
        sys.exit(1)

    existing = {f['name'] for f in inv_table['fields']}
    created = 0
    for field_def in CALL_QUEUE_FIELDS:
        if field_def['name'] in existing:
            continue
        print(f"  Creating field: {field_def['name']}")
        create_url = (
            f'https://api.airtable.com/v0/meta/bases/{BASE_ID}'
            f'/tables/{INVESTORS}/fields'
        )
        result = api_call('POST', create_url, json=field_def)
        if result:
            print(f"    OK ({result.get('id', '?')})")
            created += 1
        else:
            print(f"    FAILED: {field_def['name']}")
    if created:
        print(f"  Created {created} new field(s)")
    else:
        print(f"  All 6 call-queue fields already exist")


# ---------------------------------------------------------------------------
# Computation helpers
# ---------------------------------------------------------------------------

def monthly_payment(principal, annual_rate, term_months):
    """Standard amortization: monthly P&I payment."""
    if principal <= 0 or annual_rate <= 0 or term_months <= 0:
        return 0
    r = annual_rate / 12
    n = term_months
    return principal * (r * (1 + r) ** n) / ((1 + r) ** n - 1)


def get_field(record, *names, default=None):
    """Get a field value, trying multiple possible names (handles emoji variants)."""
    fields = record.get('fields', {})
    for name in names:
        if name in fields:
            val = fields[name]
            if val is not None and val != '':
                return val
    return default


def get_linked_ids(record, field_name):
    """Extract linked record IDs from a link field."""
    val = record.get('fields', {}).get(field_name, [])
    if isinstance(val, list):
        return val
    return []


def format_currency(amount):
    """Format a number as $X,XXX or $X.XM."""
    if amount is None:
        return '$0'
    if abs(amount) >= 1_000_000:
        return f'${amount / 1_000_000:.1f}M'
    return f'${amount:,.0f}'


def parse_date(date_str):
    """Parse a YYYY-MM-DD date string, returning None on failure."""
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str[:10], '%Y-%m-%d')
    except (ValueError, TypeError):
        return None


# ---------------------------------------------------------------------------
# Trigger-flag helpers (handle both emoji and plain field names)
# ---------------------------------------------------------------------------

TRIGGER_FLAG_NAMES = {
    'hard_money': ('Hard Money Flag', 'Hard Money Flag'),
    'high_rate':  ('High Rate Flag', 'High Rate Flag'),
    'maturity':   ('Maturity Window Flag', 'Maturity Window Flag'),
    'balloon':    ('Balloon Risk Flag', 'Balloon Risk Flag'),
}

# Build lookup list: for each trigger, try emoji-prefixed name first
TRIGGER_LOOKUPS = {
    'hard_money': ['\U0001f6a8 Hard Money Flag', 'Hard Money Flag'],
    'high_rate':  ['\U0001f6a8 High Rate Flag', 'High Rate Flag'],
    'maturity':   ['\U0001f6a8 Maturity Window Flag', 'Maturity Window Flag'],
    'balloon':    ['\U0001f6a8 Balloon Risk Flag', 'Balloon Risk Flag'],
}


def has_trigger(fin_rec, trigger_key):
    """Check if a financing record has a specific trigger flag set."""
    names = TRIGGER_LOOKUPS[trigger_key]
    return get_field(fin_rec, *names) is not None


def has_any_trigger(fin_rec):
    """Check if a financing record has any trigger flag."""
    return any(has_trigger(fin_rec, k) for k in TRIGGER_LOOKUPS)


# ---------------------------------------------------------------------------
# Core computation — 6 fields per investor
# ---------------------------------------------------------------------------

def compute_investor_fields(inv_rec, inv_id, props_by_investor,
                            fin_by_property, outreach_by_investor,
                            target_rate):
    """Compute the 6 call-queue fields for one investor."""
    fields = inv_rec.get('fields', {})
    result = {}

    # Gather all properties and their financing
    prop_entries = props_by_investor.get(inv_id, [])
    all_financing = []
    for prop_id, prop_rec in prop_entries:
        for fin_id, fin_rec in fin_by_property.get(prop_id, []):
            all_financing.append(fin_rec)

    # Gather outreach
    outreach_list = outreach_by_investor.get(inv_id, [])

    # ---------------------------------------------------------------
    # 1. Trigger Summary
    # ---------------------------------------------------------------
    trigger_lines = []
    for fin in all_financing:
        ff = fin.get('fields', {})
        loan_id = ff.get('Loan ID', '?')
        lender = ff.get('Current Lender', 'Unknown')
        rate = ff.get('Interest Rate')
        rate_str = f'{rate * 100:.1f}%' if rate else '?%'

        triggers = []

        if has_trigger(fin, 'hard_money'):
            triggers.append('Hard Money')
        if has_trigger(fin, 'high_rate'):
            triggers.append(f'High Rate {rate_str}')
        if has_trigger(fin, 'maturity'):
            md = parse_date(ff.get('Loan Maturity Date', ''))
            triggers.append(f'Matures {md.strftime("%b %Y")}' if md else 'Maturity')
        if has_trigger(fin, 'balloon'):
            bd = parse_date(ff.get('Balloon Date', ''))
            triggers.append(f'Balloon {bd.strftime("%b %Y")}' if bd else 'Balloon')

        if triggers:
            trigger_lines.append(
                f'{loan_id} ({lender}): {", ".join(triggers)}'
            )

    # Cash purchase properties (no financing = bought with cash)
    cash_props = [
        p for pid, p in prop_entries
        if not fin_by_property.get(pid)
    ]
    if cash_props:
        cash_value = sum(
            (p.get('fields', {}).get('Estimated Property Value') or 0)
            for p in cash_props
        )
        cash_str = format_currency(cash_value) if cash_value else ''
        trigger_lines.append(
            f'{len(cash_props)} cash purchase(s) {cash_str} — no leverage, refi opportunity'
        )

    result['Trigger Summary'] = '\n'.join(trigger_lines) if trigger_lines else ''

    # ---------------------------------------------------------------
    # 2. Portfolio Snapshot
    # ---------------------------------------------------------------
    n_props = len(prop_entries)
    total_value = sum(
        (p.get('fields', {}).get('Estimated Property Value') or 0)
        for _, p in prop_entries
    )
    total_debt = sum(
        (f.get('fields', {}).get('Estimated Loan Balance') or 0)
        for f in all_financing
    )
    total_equity = total_value - total_debt

    lenders = sorted({
        f.get('fields', {}).get('Current Lender', '')
        for f in all_financing
        if f.get('fields', {}).get('Current Lender')
    })

    trigger_count = sum(
        sum(1 for k in TRIGGER_LOOKUPS if has_trigger(fin, k))
        for fin in all_financing
    )

    snap_parts = [
        f'{n_props} properties, {format_currency(total_value)} value, '
        f'{format_currency(total_debt)} debt, {format_currency(total_equity)} equity'
    ]
    if lenders:
        snap_parts.append(f'Lenders: {", ".join(lenders)}')
    if trigger_count:
        snap_parts.append(f'{trigger_count} active trigger(s)')

    result['Portfolio Snapshot'] = '\n'.join(snap_parts)

    # ---------------------------------------------------------------
    # 3. Current Lenders
    # ---------------------------------------------------------------
    result['Current Lenders'] = ', '.join(lenders) if lenders else ''

    # ---------------------------------------------------------------
    # 4. Estimated Monthly Savings
    # ---------------------------------------------------------------
    total_savings = 0.0
    for fin in all_financing:
        if not has_any_trigger(fin):
            continue
        ff = fin.get('fields', {})
        balance = ff.get('Estimated Loan Balance') or 0
        if balance <= 0:
            continue

        # Current payment: use the actual Monthly Payment Estimate if available,
        # otherwise compute from amortization at current rate/term
        current_pmt = ff.get('Monthly Payment Estimate') or 0
        if current_pmt <= 0:
            current_rate = ff.get('Interest Rate') or 0
            current_term = ff.get('Loan Term (Months)') or 360
            if current_rate > 0:
                current_pmt = monthly_payment(balance, current_rate, current_term)

        # DSCR refi payment: amortize remaining balance at target rate / 30yr
        dscr_pmt = monthly_payment(balance, target_rate, DEFAULT_TERM_MONTHS)

        savings = current_pmt - dscr_pmt
        if savings > 0:
            total_savings += savings

    result['Estimated Monthly Savings'] = (
        round(total_savings) if total_savings > 0 else None
    )

    # ---------------------------------------------------------------
    # 5. Last Outreach Summary
    # ---------------------------------------------------------------
    if outreach_list:
        outreach_list.sort(
            key=lambda r: r.get('fields', {}).get('Date', ''),
            reverse=True,
        )
        last = outreach_list[0].get('fields', {})
        parts = []

        d = parse_date(last.get('Date', ''))
        if d:
            parts.append(d.strftime('%b %d'))

        resp = last.get('Response Status', '')
        if resp:
            parts.append(resp)

        outcome = last.get('Outcome', '')
        if outcome:
            parts.append(outcome)

        notes = last.get('Disposition Notes', '')
        if notes:
            if len(notes) > 60:
                notes = notes[:57] + '...'
            parts.append(notes)

        follow_up = last.get('Follow Up Action', '')
        if follow_up:
            parts.append(follow_up)

        result['Last Outreach Summary'] = ' - '.join(parts) if parts else ''
    else:
        result['Last Outreach Summary'] = ''

    # ---------------------------------------------------------------
    # 6. Call Priority
    # ---------------------------------------------------------------
    dnc = fields.get('DNC Status', '')
    if dnc and dnc not in ('Clear', 'Not Checked', ''):
        result['Call Priority'] = 'DQ-DNC'
    else:
        # P0: follow-up due today or overdue
        today_str = date.today().isoformat()
        has_followup_due = any(
            (o.get('fields', {}).get('Follow Up Date', '') or '')[:10] <= today_str
            and (o.get('fields', {}).get('Follow Up Date', '') or '') != ''
            for o in outreach_list
        )

        # Trigger checks: linked Financing records OR direct Investor fields
        hm = (any(has_trigger(f, 'hard_money') for f in all_financing)
              or fields.get('Hard Money') is True)
        bl = any(has_trigger(f, 'balloon') for f in all_financing)
        mt_linked = any(has_trigger(f, 'maturity') for f in all_financing)
        mt_direct = (fields.get('Months to Maturity') or 999) <= 24
        mt = mt_linked or mt_direct
        hr_linked = any(has_trigger(f, 'high_rate') for f in all_financing)
        hr_direct = (fields.get('Loan Rate') or 0) >= 0.07
        hr = hr_linked or hr_direct

        # Cash purchase: property with no financing
        has_cash = any(
            not fin_by_property.get(pid) for pid, _ in prop_entries
        )

        never_contacted = (
            not outreach_list and not fields.get('Last Contact Date')
        )

        # DNC = "Not Checked" → treat as new lead (Frank needs to see them)
        if has_followup_due:
            result['Call Priority'] = 'P0-FollowUp'
        elif hm:
            result['Call Priority'] = 'P1-HardMoney'
        elif bl:
            result['Call Priority'] = 'P2-Balloon'
        elif mt:
            result['Call Priority'] = 'P3-Maturity'
        elif hr:
            result['Call Priority'] = 'P4-HighRate'
        elif has_cash:
            result['Call Priority'] = 'P5-CashPurchase'
        elif never_contacted:
            result['Call Priority'] = 'P6-NewLead'
        else:
            result['Call Priority'] = 'P7-Nurture'

    return result


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description='Refresh call queue fields on Investors table',
    )
    parser.add_argument(
        '--dry-run', action='store_true',
        help='Preview computed values without writing to Airtable',
    )
    parser.add_argument(
        '--target-rate', type=float, default=DEFAULT_TARGET_RATE,
        help=f'DSCR benchmark rate for savings calc (default: {DEFAULT_TARGET_RATE})',
    )
    args = parser.parse_args()

    if not API_TOKEN:
        print("ERROR: AIRTABLE_API_TOKEN not set. Add it to .env")
        sys.exit(1)

    print(f'\n{"=" * 60}')
    print(f'Call Queue Refresh  {datetime.now().strftime("%Y-%m-%d %H:%M")}')
    print(f'Target rate: {args.target_rate * 100:.1f}%  |  Dry run: {args.dry_run}')
    print(f'{"=" * 60}')

    # Phase 0: Ensure fields exist
    if not args.dry_run:
        print('\nPhase 0: Checking schema...')
        ensure_fields_exist()

    # Phase 1: Read all tables
    print('\nPhase 1: Reading tables...')
    investors = fetch_all_records(INVESTORS, 'Investors')
    properties = fetch_all_records(PROPERTIES, 'Properties')
    financing = fetch_all_records(FINANCING, 'Financing')
    outreach = fetch_all_records(OUTREACH, 'Outreach Log')

    if not investors:
        print('ERROR: No investors found. Upload test data first.')
        sys.exit(1)

    # Phase 2: Build relationship graph
    # Link direction: child -> parent (more reliable than reading parent link fields)
    print('\nPhase 2: Building relationship graph...')

    # Properties -> Investor (via "Owner Investor" link field on Properties)
    props_by_investor = defaultdict(list)
    for prop in properties:
        linked_inv_ids = get_linked_ids(prop, 'Owner Investor')
        for inv_id in linked_inv_ids:
            props_by_investor[inv_id].append((prop['id'], prop))

    # Financing -> Property (via "Property" link field on Financing)
    fin_by_property = defaultdict(list)
    for fin in financing:
        linked_prop_ids = get_linked_ids(fin, 'Property')
        for prop_id in linked_prop_ids:
            fin_by_property[prop_id].append((fin['id'], fin))

    # Outreach -> Investor (via "Investor" link field on Outreach)
    outreach_by_investor = defaultdict(list)
    for out in outreach:
        linked_inv_ids = get_linked_ids(out, 'Investor')
        for inv_id in linked_inv_ids:
            outreach_by_investor[inv_id].append(out)

    print(
        f'  {len(props_by_investor)} investors with properties, '
        f'{len(fin_by_property)} properties with financing, '
        f'{len(outreach_by_investor)} investors with outreach'
    )

    # Phase 3: Compute
    print('\nPhase 3: Computing call-queue fields...')
    updates = []
    priority_counts = defaultdict(int)

    for inv in investors:
        inv_id = inv['id']
        computed = compute_investor_fields(
            inv, inv_id, props_by_investor, fin_by_property,
            outreach_by_investor, args.target_rate,
        )
        priority_counts[computed.get('Call Priority', '')] += 1

        # Build update payload — write None to clear empty currency fields
        update_fields = {}
        for key, val in computed.items():
            if key == 'Estimated Monthly Savings' and val is None:
                update_fields[key] = None
            elif val is not None:
                update_fields[key] = val

        updates.append((inv_id, update_fields))

    # Preview in dry-run mode
    if args.dry_run:
        print(f'\n{"=" * 60}')
        print('DRY RUN — Preview (first 10 investors):')
        print(f'{"=" * 60}')
        for inv_id, upd_fields in updates[:10]:
            inv_rec = next(r for r in investors if r['id'] == inv_id)
            name = inv_rec.get('fields', {}).get('Full Name', inv_id)
            print(f'\n--- {name} ---')
            for k, v in upd_fields.items():
                if isinstance(v, str) and '\n' in v:
                    print(f'  {k}:')
                    for line in v.split('\n'):
                        print(f'    {line}')
                else:
                    display = (
                        format_currency(v)
                        if k == 'Estimated Monthly Savings' and v is not None
                        else v
                    )
                    print(f'  {k}: {display}')

    # Phase 4: Write back to Airtable
    if not args.dry_run:
        print(f'\nPhase 4: Writing {len(updates)} records...')
        batches = []
        batch = []
        for inv_id, upd_fields in updates:
            batch.append({"id": inv_id, "fields": upd_fields})
            if len(batch) == 10:
                batches.append(batch)
                batch = []
        if batch:
            batches.append(batch)

        success = 0
        failed = 0
        for i, b in enumerate(batches):
            result = patch_records(INVESTORS, b)
            if result:
                success += len(b)
            else:
                failed += len(b)
            if (i + 1) % 50 == 0:
                print(
                    f'  Progress: {success + failed}/{len(updates)} '
                    f'({success} ok, {failed} failed)'
                )

        print(f'  Done: {success} updated, {failed} failed')
    else:
        print('\n  (Dry run — no records written)')

    # Phase 5: Report
    print(f'\n{"=" * 60}')
    print('Priority Distribution:')
    print(f'{"=" * 60}')
    for priority in sorted(priority_counts.keys()):
        count = priority_counts[priority]
        bar = '#' * min(count, 50)
        print(f'  {priority:<16} {count:>5}  {bar}')
    print(f'  {"TOTAL":<16} {sum(priority_counts.values()):>5}')
    print()


if __name__ == '__main__':
    main()
