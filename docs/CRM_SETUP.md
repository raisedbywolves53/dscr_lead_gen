# CRM Setup — Airtable + Google Sheets

## Overview

Two output targets:
1. **Airtable** — Full CRM with 7 tables, 191 fields, automations, and views
2. **Google Sheets** — Lightweight MVP with call sheet, battlecards, and performance tracking

---

## Airtable CRM

### Base Architecture

```
INVESTORS (50 fields)
  ├── OWNERSHIP ENTITIES (18 fields)
  │     └── PROPERTIES (36 fields)
  │           └── FINANCING (35 fields)
  ├── OPPORTUNITIES (24 fields)
  ├── OUTREACH LOG (13 fields)
  └── COMPLIANCE (15 fields)
```

7 tables, 191 fields total, 9 link relationships, rollup chains from Financing → Properties → Investors.

### Table Summary

| Table | Fields | Role |
|-------|--------|------|
| Investors | 50 | Contact info, 10 rollups, 9 formulas, lead scoring 0-100 |
| Ownership Entities | 18 | Entity details, 3 rollups, 1 formula |
| Properties | 36 | Property details, 3 rollups, 10 formulas, 1 lookup |
| Financing | 35 | Loan details, 11 formula trigger flags |
| Compliance | 15 | DNC/consent tracking, 2 formulas |
| Opportunities | 24 | Deal pipeline, 5 formulas + auto timestamps |
| Outreach Log | 13 | Activity tracking |

### Key Formulas

**Lead Score (Investors table):** Composite of property count, portfolio value, entity sophistication, STR license, contact availability, refi signals.

**Trigger Flags (Financing table):** Hard Money Flag, High Rate Flag, Balloon Maturity Flag, Cash Purchase Flag, High LTV Flag, etc. These drive the "Hot Leads" view.

### Important Technical Notes

- Airtable API **CANNOT** create formula, rollup, createdTime, or lastModifiedTime fields
- Airtable AI assistant **CANNOT** create views or automations
- These must be created manually in the Airtable UI
- Rollup aggregations show as "NONE" in API metadata — this is normal, they work

### Setup Process

1. Run `airtable/airtable_build_v2.py` to create base skeleton (tables + text/number fields)
2. Manually create formula and rollup fields in Airtable UI (see `docs/airtable/` guides)
3. Manually create views (24 views — see `docs/airtable/VIEWS_Step_by_Step.md`)
4. Manually create automations (8 — see `docs/airtable/AUTOMATIONS_Step_by_Step.md`)
5. Upload test data from `airtable/test_data/`
6. Run `airtable/upload_pilot_leads.py` for full data import

### Detailed Airtable Guides

- `docs/airtable/VIEWS_Step_by_Step.md` — 24 views setup
- `docs/airtable/AUTOMATIONS_Step_by_Step.md` — 8 automations setup
- `docs/airtable/INTERFACES_Step_by_Step.md` — 4 dashboards
- `docs/airtable/CALL_QUEUE_SETUP.md` — Dialer integration

---

## Google Sheets MVP

### Sheet Structure

| Tab | Rows | Purpose |
|-----|------|---------|
| Call Sheet | Callable leads (with phone) | Priority-sorted, phone + talking points |
| Battlecards | All leads (500) | Full dossier with financing angles |
| Performance | All leads | Pipeline tracking with status dropdowns |
| Dashboard | KPIs | ICP breakdown, charts |

### Setup

1. Create Google OAuth credentials (one-time)
2. Run `scrape/scripts/build_google_sheets.py`
3. Share sheet with loan originator

### OAuth Setup

1. Go to Google Cloud Console → APIs & Services → Credentials
2. Create OAuth 2.0 Client ID (Desktop application)
3. Download JSON → save as `credentials/google_oauth.json`
4. Enable Google Sheets API and Google Drive API
5. First run will open browser for auth → token saved at `scrape/google_token.json`

---

## Airtable Scripts

| Script | Purpose | Status |
|--------|---------|--------|
| `airtable/airtable_build_v2.py` | Create base skeleton (tables + fields) | Working |
| `airtable/build_pilot_500.py` | Prep data for upload | Working |
| `airtable/upload_pilot_leads.py` | Upload leads to Airtable | Working |
| `airtable/upload_full_crm.py` | Upload full dataset | Incomplete |
| `airtable/check_completeness.py` | Validate base structure | Working |
| `airtable/lead_quality_audit.py` | Data quality checks | Working |
| `airtable/refresh_call_queue.py` | Update call queue view | Incomplete |

### Validation via API

```python
import os, requests
API_TOKEN = os.getenv('AIRTABLE_API_TOKEN')
BASE_ID = 'your_base_id_here'
headers = {'Authorization': f'Bearer {API_TOKEN}'}
resp = requests.get(f'https://api.airtable.com/v0/meta/bases/{BASE_ID}/tables', headers=headers)
data = resp.json()
for table in data['tables']:
    broken = sum(1 for f in table['fields']
                 if f['type'] in ('formula','rollup')
                 and f.get('options',{}).get('result') is None)
    print(f"{table['name']}: {len(table['fields'])} fields"
          + (f" ({broken} BROKEN)" if broken else ""))
```
