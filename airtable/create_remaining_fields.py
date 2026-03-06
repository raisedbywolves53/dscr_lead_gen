import requests, json, time, sys

API_TOKEN = 'YOUR_AIRTABLE_API_TOKEN'
BASE_ID = 'appJV7J1ZrNEBAWAm'
HEADERS = {
    'Authorization': f'Bearer {API_TOKEN}',
    'Content-Type': 'application/json'
}

# Table IDs
INVESTORS = 'tbla2NnrEDSFA3UFP'
ENTITIES = 'tblSwOPMuzEWRBVcF'
PROPERTIES = 'tblVXwCSkubWp30UO'
FINANCING = 'tblh4OgGSpyf6hSfX'
COMPLIANCE = 'tblfCU8wWB0tHDtDn'
OPPORTUNITIES = 'tblOWWcS1s6mfpqcH'
OUTREACH = 'tbl0uK5dE9orqCeq9'

# =====================================================
# Key Field IDs (from schema fetch)
# =====================================================

# -- On Properties table --
PROP_Address = 'fldhJ83sgAbt01ESo'           # Property Address (singleLineText)
PROP_EstValue = 'fldLAoiiMRgJKUR63'          # Estimated Property Value (currency)
PROP_TotalDebt = 'fldDGZt5eiPTkonYj'         # Total Property Debt (rollup)
PROP_HasHardMoney = 'fldoVxUZ7BAdqnDcV'      # Has Hard Money (formula, returns 1/0)
PROP_TriggerCount = 'fldaxqBlOWWmaDdgD'      # Trigger County [sic — actually Trigger Count rollup]
PROP_RecentPurchase = 'fldxjlwa5Iui3d9mT'    # Recent Purchase (formula, 1/0)
PROP_IsCashPurchase = 'fld94yFNHUCyAWf1a'    # Is Cash Purchase (formula, 1/0)
PROP_City = 'fldAzvfFLwhm6YeI2'             # City (singleLineText)

# -- Link fields on Ownership Entities --
ENT_PropertiesLink = 'fld7UXWOgzpu7iKDx'     # Properties (multipleRecordLinks → Properties)
ENT_InvestorLink = 'fldS3Yr6me2DIevyH'       # Investor (Owner) (multipleRecordLinks → Investors)

# -- Link fields on Investors --
INV_PropertiesLink = 'fldKtu9K0ZTxqKRZX'     # Properties (multipleRecordLinks → Properties)
INV_EntitiesLink = 'fldsH4OoUaFIbVaWR'       # Ownership Entities (multipleRecordLinks → Entities)
INV_OutreachLink = 'fldbP1OUNaJXIXCjj'       # Outreach Log (multipleRecordLinks → Outreach)
INV_OpportunitiesLink = 'fldjhoinxZKee7XJP'   # Opportunities (multipleRecordLinks → Opportunities)
INV_ComplianceLink = 'fldsUILiTK5rTp58I'      # Compliance (multipleRecordLinks → Compliance)

# -- On Entities table (existing fields) --
ENT_EntityName = 'fldpp8FDAorwAREFL'          # Entity Name (singleLineText)

# -- On Outreach table --
OUT_Date = 'fld9pNbQEuqEL2QiQ'              # Date (date)

# -- On Opportunities table --
OPP_Stage = 'fldBc09uGvSbM3Xfr'             # Opportunity Stage (singleSelect)

# =====================================================

results = {"success": [], "failed": []}

def create_field(table_id, table_name, payload):
    """Create a field via Airtable API with rate limiting"""
    url = f'https://api.airtable.com/v0/meta/bases/{BASE_ID}/tables/{table_id}/fields'
    field_name = payload.get('name', 'Unknown')

    resp = requests.post(url, headers=HEADERS, json=payload)

    if resp.status_code == 200:
        field_id = resp.json().get('id', '?')
        print(f"  ✅ {table_name} → {field_name} (ID: {field_id})")
        results["success"].append(f"{table_name} → {field_name}")
        time.sleep(0.25)  # rate limit
        return field_id
    elif resp.status_code == 422 and 'DUPLICATE_FIELD_NAME' in resp.text:
        print(f"  ⏭️  {table_name} → {field_name} — already exists, skipping")
        results["success"].append(f"{table_name} → {field_name} (already existed)")
        time.sleep(0.25)
        return "EXISTS"
    elif resp.status_code == 429:
        print(f"  ⏳ Rate limited, waiting 30s...")
        time.sleep(30)
        return create_field(table_id, table_name, payload)  # retry
    else:
        print(f"  ❌ {table_name} → {field_name} — Error {resp.status_code}: {resp.text[:200]}")
        results["failed"].append(f"{table_name} → {field_name}: {resp.text[:150]}")
        time.sleep(0.25)
        return None


# =====================================================
# PHASE 1: OWNERSHIP ENTITIES (3 remaining fields)
# =====================================================
print("\n" + "="*60)
print("PHASE 1: OWNERSHIP ENTITIES")
print("="*60)

# 1. Total Entity Value — Rollup: Properties → Estimated Property Value → SUM
create_field(ENTITIES, "Entities", {
    "name": "Total Entity Value",
    "type": "rollup",
    "options": {
        "recordLinkFieldId": ENT_PropertiesLink,
        "fieldIdInLinkedTable": PROP_EstValue,
        "formulaTextParsed": "SUM(values)"
    }
})

# 2. Total Entity Debt — Rollup: Properties → Total Property Debt → SUM
create_field(ENTITIES, "Entities", {
    "name": "Total Entity Debt",
    "type": "rollup",
    "options": {
        "recordLinkFieldId": ENT_PropertiesLink,
        "fieldIdInLinkedTable": PROP_TotalDebt,
        "formulaTextParsed": "SUM(values)"
    }
})

# 3. Entity Equity — Formula
create_field(ENTITIES, "Entities", {
    "name": "Entity Equity",
    "type": "formula",
    "options": {
        "formulaTextParsed": '{Total Entity Value} - {Total Entity Debt}'
    }
})

# 4. Primary Markets — Rollup: Properties → City → ARRAYUNIQUE
create_field(ENTITIES, "Entities", {
    "name": "Primary Markets",
    "type": "rollup",
    "options": {
        "recordLinkFieldId": ENT_PropertiesLink,
        "fieldIdInLinkedTable": PROP_City,
        "formulaTextParsed": "ARRAYUNIQUE(ARRAYFLATTEN(values))"
    }
})


# =====================================================
# PHASE 2: OPPORTUNITIES (7 remaining fields)
# =====================================================
print("\n" + "="*60)
print("PHASE 2: OPPORTUNITIES")
print("="*60)

# 1. Weighted Value — Formula
create_field(OPPORTUNITIES, "Opportunities", {
    "name": "Weighted Value",
    "type": "formula",
    "options": {
        "formulaTextParsed": 'IF(AND({Estimated Loan Amount}, {Probability of Close}), ROUND({Estimated Loan Amount} * {Probability of Close}, 0), "")'
    }
})

# 2. Estimated Commission — Formula (2% of loan amount)
create_field(OPPORTUNITIES, "Opportunities", {
    "name": "Estimated Commission",
    "type": "formula",
    "options": {
        "formulaTextParsed": 'IF({Estimated Loan Amount}, ROUND({Estimated Loan Amount} * 0.02, 0), "")'
    }
})

# 3. Weighted Commission — Formula
create_field(OPPORTUNITIES, "Opportunities", {
    "name": "Weighted Commission",
    "type": "formula",
    "options": {
        "formulaTextParsed": 'IF(AND({Estimated Commission}, {Probability of Close}), ROUND({Estimated Commission} * {Probability of Close}, 0), "")'
    }
})

# 4. Days in Stage — Formula
create_field(OPPORTUNITIES, "Opportunities", {
    "name": "Days in Stage",
    "type": "formula",
    "options": {
        "formulaTextParsed": "DATETIME_DIFF(NOW(), LAST_MODIFIED_TIME(), 'days')"
    }
})

# 5. Days Since Created — Formula
create_field(OPPORTUNITIES, "Opportunities", {
    "name": "Days Since Created",
    "type": "formula",
    "options": {
        "formulaTextParsed": "DATETIME_DIFF(NOW(), CREATED_TIME(), 'days')"
    }
})

# 6. Date Created — Created time
create_field(OPPORTUNITIES, "Opportunities", {
    "name": "Date Created",
    "type": "createdTime",
    "options": {
        "result": {
            "type": "dateTime",
            "options": {
                "dateFormat": {"name": "local"},
                "timeFormat": {"name": "12hour"},
                "timeZone": "America/New_York"
            }
        }
    }
})

# 7. Last Modified — Last modified time
create_field(OPPORTUNITIES, "Opportunities", {
    "name": "Last Modified",
    "type": "lastModifiedTime",
    "options": {
        "result": {
            "type": "dateTime",
            "options": {
                "dateFormat": {"name": "local"},
                "timeFormat": {"name": "12hour"},
                "timeZone": "America/New_York"
            }
        }
    }
})


# =====================================================
# PHASE 3: COMPLIANCE (2 remaining fields)
# =====================================================
print("\n" + "="*60)
print("PHASE 3: COMPLIANCE")
print("="*60)

# 1. Next Scrub Due — Formula
create_field(COMPLIANCE, "Compliance", {
    "name": "Next Scrub Due",
    "type": "formula",
    "options": {
        "formulaTextParsed": 'IF(AND({Record Type} = "DNC Scrub", {Date}), DATEADD({Date}, 31, \'days\'), "")'
    }
})

# 2. Scrub Overdue — Formula
create_field(COMPLIANCE, "Compliance", {
    "name": "Scrub Overdue",
    "type": "formula",
    "options": {
        "formulaTextParsed": "IF(AND({Next Scrub Due} != \"\", IS_BEFORE({Next Scrub Due}, NOW())), \"⛔ OVERDUE - SCRUB NOW\", IF(AND({Next Scrub Due} != \"\", DATETIME_DIFF({Next Scrub Due}, NOW(), 'days') <= 7), \"⚠️ Due within 7 days\", \"\"))"
    }
})


# =====================================================
# PHASE 4: INVESTORS — Rollups first (10 fields)
# =====================================================
print("\n" + "="*60)
print("PHASE 4: INVESTORS — Rollups")
print("="*60)

# 1. Property Count — Rollup: Properties → Property Address → COUNTA
create_field(INVESTORS, "Investors", {
    "name": "Property Count",
    "type": "rollup",
    "options": {
        "recordLinkFieldId": INV_PropertiesLink,
        "fieldIdInLinkedTable": PROP_Address,
        "formulaTextParsed": "COUNTA(values)"
    }
})

# 2. Total Portfolio Value — Rollup: Properties → Estimated Property Value → SUM
create_field(INVESTORS, "Investors", {
    "name": "Total Portfolio Value",
    "type": "rollup",
    "options": {
        "recordLinkFieldId": INV_PropertiesLink,
        "fieldIdInLinkedTable": PROP_EstValue,
        "formulaTextParsed": "SUM(values)"
    }
})

# 3. Total Portfolio Debt — Rollup: Properties → Total Property Debt → SUM (chained rollup)
create_field(INVESTORS, "Investors", {
    "name": "Total Portfolio Debt",
    "type": "rollup",
    "options": {
        "recordLinkFieldId": INV_PropertiesLink,
        "fieldIdInLinkedTable": PROP_TotalDebt,
        "formulaTextParsed": "SUM(values)"
    }
})

# 4. Entity Count — Rollup: Entities → Entity Name → COUNTA
create_field(INVESTORS, "Investors", {
    "name": "Entity Count",
    "type": "rollup",
    "options": {
        "recordLinkFieldId": INV_EntitiesLink,
        "fieldIdInLinkedTable": ENT_EntityName,
        "formulaTextParsed": "COUNTA(values)"
    }
})

# 5. Outreach Count — Rollup: Outreach Log → Date → COUNTA
create_field(INVESTORS, "Investors", {
    "name": "Outreach Count",
    "type": "rollup",
    "options": {
        "recordLinkFieldId": INV_OutreachLink,
        "fieldIdInLinkedTable": OUT_Date,
        "formulaTextParsed": "COUNTA(values)"
    }
})

# 6. Open Opportunities — Rollup: Opportunities → Opportunity Stage → COUNTA
create_field(INVESTORS, "Investors", {
    "name": "Open Opportunities",
    "type": "rollup",
    "options": {
        "recordLinkFieldId": INV_OpportunitiesLink,
        "fieldIdInLinkedTable": OPP_Stage,
        "formulaTextParsed": "COUNTA(values)"
    }
})

# 7. Hard Money Loan Count — Rollup: Properties → Has Hard Money → SUM
create_field(INVESTORS, "Investors", {
    "name": "Hard Money Loan Count",
    "type": "rollup",
    "options": {
        "recordLinkFieldId": INV_PropertiesLink,
        "fieldIdInLinkedTable": PROP_HasHardMoney,
        "formulaTextParsed": "SUM(values)"
    }
})

# 8. Total Trigger Count — Rollup: Properties → Trigger Count → SUM
create_field(INVESTORS, "Investors", {
    "name": "Total Trigger Count",
    "type": "rollup",
    "options": {
        "recordLinkFieldId": INV_PropertiesLink,
        "fieldIdInLinkedTable": PROP_TriggerCount,
        "formulaTextParsed": "SUM(values)"
    }
})

# 9. Recent Purchase Count — Rollup: Properties → Recent Purchase → SUM
create_field(INVESTORS, "Investors", {
    "name": "Recent Purchase Count",
    "type": "rollup",
    "options": {
        "recordLinkFieldId": INV_PropertiesLink,
        "fieldIdInLinkedTable": PROP_RecentPurchase,
        "formulaTextParsed": "SUM(values)"
    }
})

# 10. Cash Purchase Count — Rollup: Properties → Is Cash Purchase → SUM
create_field(INVESTORS, "Investors", {
    "name": "Cash Purchase Count",
    "type": "rollup",
    "options": {
        "recordLinkFieldId": INV_PropertiesLink,
        "fieldIdInLinkedTable": PROP_IsCashPurchase,
        "formulaTextParsed": "SUM(values)"
    }
})


# =====================================================
# PHASE 5: INVESTORS — Formulas (2 fields)
# =====================================================
print("\n" + "="*60)
print("PHASE 5: INVESTORS — Core Formulas")
print("="*60)

# 1. Estimated Portfolio Equity — Formula
create_field(INVESTORS, "Investors", {
    "name": "Estimated Portfolio Equity",
    "type": "formula",
    "options": {
        "formulaTextParsed": "{Total Portfolio Value} - {Total Portfolio Debt}"
    }
})

# 2. Days Since Last Contact — Formula
create_field(INVESTORS, "Investors", {
    "name": "Days Since Last Contact",
    "type": "formula",
    "options": {
        "formulaTextParsed": "IF({Last Contact Date}, DATETIME_DIFF(NOW(), {Last Contact Date}, 'days'), 999)"
    }
})


# =====================================================
# PHASE 6: INVESTORS — Lead Scoring (7 fields)
# =====================================================
print("\n" + "="*60)
print("PHASE 6: INVESTORS — Lead Scoring")
print("="*60)

# 1. Portfolio Size Score (0–30)
create_field(INVESTORS, "Investors", {
    "name": "Portfolio Size Score",
    "type": "formula",
    "options": {
        "formulaTextParsed": "IF({Property Count} >= 20, 30, IF({Property Count} >= 10, 25, IF({Property Count} >= 5, 20, IF({Property Count} >= 3, 15, IF({Property Count} >= 2, 10, IF({Property Count} >= 1, 5, 0))))))"
    }
})

# 2. Refi Opportunity Score (0–25)
create_field(INVESTORS, "Investors", {
    "name": "Refi Opportunity Score",
    "type": "formula",
    "options": {
        "formulaTextParsed": "IF({Total Trigger Count} >= 4, 25, IF({Total Trigger Count} >= 3, 20, IF({Total Trigger Count} >= 2, 15, IF({Total Trigger Count} >= 1, 10, 0))))"
    }
})

# 3. Recent Purchase Score (0–20)
create_field(INVESTORS, "Investors", {
    "name": "Recent Purchase Score",
    "type": "formula",
    "options": {
        "formulaTextParsed": "IF({Recent Purchase Count} >= 3, 20, IF({Recent Purchase Count} >= 2, 15, IF({Recent Purchase Count} >= 1, 10, 0)))"
    }
})

# 4. Equity Score (0–15)
create_field(INVESTORS, "Investors", {
    "name": "Equity Score",
    "type": "formula",
    "options": {
        "formulaTextParsed": 'IF({Estimated Portfolio Equity} = "" , 0, IF({Estimated Portfolio Equity} >= 2000000, 15, IF({Estimated Portfolio Equity} >= 1000000, 12, IF({Estimated Portfolio Equity} >= 500000, 9, IF({Estimated Portfolio Equity} >= 250000, 6, IF({Estimated Portfolio Equity} >= 100000, 3, 0))))))'
    }
})

# 5. Hard Money Score (0–10)
create_field(INVESTORS, "Investors", {
    "name": "Hard Money Score",
    "type": "formula",
    "options": {
        "formulaTextParsed": "IF({Hard Money Loan Count} >= 3, 10, IF({Hard Money Loan Count} >= 2, 8, IF({Hard Money Loan Count} >= 1, 5, 0)))"
    }
})

# 6. Lead Score (0-100)
create_field(INVESTORS, "Investors", {
    "name": "Lead Score (0-100)",
    "type": "formula",
    "options": {
        "formulaTextParsed": "{Portfolio Size Score} + {Refi Opportunity Score} + {Recent Purchase Score} + {Equity Score} + {Hard Money Score}"
    }
})

# 7. Lead Tier
create_field(INVESTORS, "Investors", {
    "name": "Lead Tier",
    "type": "formula",
    "options": {
        "formulaTextParsed": 'IF({Lead Score (0-100)} >= 80, "🔥 Tier 1 — Personal Outreach", IF({Lead Score (0-100)} >= 60, "⭐ Tier 2 — Semi-Personal", IF({Lead Score (0-100)} >= 40, "📋 Tier 3 — Automated Nurture", "⬜ Low Priority")))'
    }
})


# =====================================================
# SUMMARY
# =====================================================
print("\n" + "="*60)
print("SUMMARY")
print("="*60)
print(f"\n✅ Successful: {len(results['success'])}")
for s in results['success']:
    print(f"   {s}")
print(f"\n❌ Failed: {len(results['failed'])}")
for f in results['failed']:
    print(f"   {f}")
print(f"\nTotal: {len(results['success'])} succeeded, {len(results['failed'])} failed out of 33 fields")
