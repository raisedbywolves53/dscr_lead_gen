"""Check data completeness of merged enriched leads."""
import csv

with open('scrape/data/enriched/merged_enriched.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    rows = list(reader)

print(f'Total records: {len(rows)}')
print()

has_person = sum(1 for r in rows if r.get('resolved_person','').strip())
has_phone1 = sum(1 for r in rows if r.get('phone_1','').strip())
has_phone2 = sum(1 for r in rows if r.get('phone_2','').strip())
has_email1 = sum(1 for r in rows if r.get('email_1','').strip())
has_email2 = sum(1 for r in rows if r.get('email_2','').strip())
has_any_phone = sum(1 for r in rows if r.get('phone_1','').strip() or r.get('phone','').strip() or r.get('str_phone','').strip())
has_any_email = sum(1 for r in rows if r.get('email_1','').strip() or r.get('email','').strip() or r.get('str_email','').strip())

print('CONTACT DATA:')
print(f'  resolved_person:    {has_person}')
print(f'  phone_1 (merged):   {has_phone1}')
print(f'  phone_2 (merged):   {has_phone2}')
print(f'  ANY phone:          {has_any_phone}')
print(f'  email_1 (merged):   {has_email1}')
print(f'  email_2 (merged):   {has_email2}')
print(f'  ANY email:          {has_any_email}')
print()

# Dialable = person + any phone
dialable = [r for r in rows if r.get('resolved_person','').strip() and (r.get('phone_1','').strip() or r.get('phone','').strip() or r.get('str_phone','').strip())]
# Full = person + phone + email
full = [r for r in dialable if r.get('email_1','').strip() or r.get('email','').strip() or r.get('str_email','').strip()]

print(f'DIALABLE (person + phone):       {len(dialable)}')
print(f'FULL (person + phone + email):   {len(full)}')
print()

# Enrichment source breakdown
sources = {}
for r in rows:
    src = r.get('enrichment_sources','').strip() or r.get('enrichment_source','').strip() or 'none'
    sources[src] = sources.get(src, 0) + 1
print('ENRICHMENT SOURCES:')
for src, count in sorted(sources.items(), key=lambda x: -x[1])[:15]:
    print(f'  {src}: {count}')
print()

# Sort full records by property count + value
full.sort(key=lambda r: (int(r.get('property_count','0') or 0), float(r.get('total_portfolio_value','0') or 0)), reverse=True)

print(f'TOP 15 FULL RECORDS (person + phone + email):')
for i, r in enumerate(full[:15]):
    val = float(r.get('total_portfolio_value', 0) or 0)
    ph = r.get('phone_1','').strip() or r.get('phone','').strip() or r.get('str_phone','').strip()
    em = r.get('email_1','').strip() or r.get('email','').strip() or r.get('str_email','').strip()
    person = r.get('resolved_person','').strip()
    props = r.get('property_count','0')
    print(f'  #{i+1}: {person} | {props} props | ${val:,.0f} | {ph} | {em}')

# Full detail for #1
if full:
    print()
    print('='*60)
    print(f'EXAMPLE COMPLETE RECORD - {full[0].get("resolved_person","")}:')
    print('='*60)
    for col, val in full[0].items():
        label = col
        display = val if val and str(val).strip() else '(empty)'
        print(f'  {label}: {display}')
