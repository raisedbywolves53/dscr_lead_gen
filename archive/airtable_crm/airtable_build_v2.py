import requests
import json
import time
import sys

API_TOKEN = "YOUR_AIRTABLE_API_TOKEN"
HEADERS = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Content-Type": "application/json"
}
BASE_URL = "https://api.airtable.com/v0"

def api_call(method, url, data=None, retries=3):
    for attempt in range(retries):
        if method == "GET":
            resp = requests.get(url, headers=HEADERS)
        elif method == "POST":
            resp = requests.post(url, headers=HEADERS, json=data)
        elif method == "PATCH":
            resp = requests.patch(url, headers=HEADERS, json=data)
        if resp.status_code == 429:
            wait = int(resp.headers.get("Retry-After", 30))
            print(f"  Rate limited, waiting {wait}s...")
            time.sleep(wait)
            continue
        elif resp.status_code >= 400:
            print(f"  ERROR {resp.status_code}: {resp.text[:300]}")
            if attempt < retries - 1:
                time.sleep(2)
                continue
            return None
        time.sleep(0.3)
        return resp.json()
    return None

def create_field(base_id, table_id, field_def):
    return api_call("POST", f"{BASE_URL}/meta/bases/{base_id}/tables/{table_id}/fields", field_def)

# ============================================================
# STEP 1: Create base with minimal first table
# ============================================================
print("STEP 1: Creating base with Investors table...")

create_payload = {
    "workspaceId": "wspqb7kWqj5RidMkV",
    "name": "DSCR Investor Intelligence",
    "tables": [
        {
            "name": "Investors",
            "description": "Primary table - decision-makers / real estate investors",
            "fields": [
                {"name": "Full Name", "type": "singleLineText"},
                {"name": "First Name", "type": "singleLineText"},
                {"name": "Last Name", "type": "singleLineText"}
            ]
        }
    ]
}

result = api_call("POST", f"{BASE_URL}/meta/bases", create_payload)
if not result:
    print("❌ Failed to create base. Check token scopes.")
    print("Required: schema.bases:write, schema.bases:read")
    sys.exit(1)

base_id = result["id"]
investors_id = result["tables"][0]["id"]
print(f"  ✅ Base: {base_id}")
print(f"  ✅ Investors table: {investors_id}")

# ============================================================
# STEP 2: Add remaining fields to Investors
# ============================================================
print("\nSTEP 2: Adding fields to Investors...")

investors_fields = [
    {"name": "Phone (Mobile)", "type": "phoneNumber"},
    {"name": "Phone (Secondary)", "type": "phoneNumber"},
    {"name": "Email (Primary)", "type": "email"},
    {"name": "Email (Secondary)", "type": "email"},
    {"name": "LinkedIn URL", "type": "url"},
    {"name": "Mailing Address", "type": "singleLineText"},
    {"name": "Mailing City", "type": "singleLineText"},
    {"name": "Mailing State", "type": "singleLineText"},
    {"name": "Mailing ZIP", "type": "singleLineText"},
    {"name": "Estimated Age Range", "type": "singleSelect", "options": {"choices": [
        {"name": "Under 30"}, {"name": "30-39"}, {"name": "40-49"},
        {"name": "50-59"}, {"name": "60-69"}, {"name": "70+"}, {"name": "Unknown"}
    ]}},
    {"name": "Investor Type", "type": "singleSelect", "options": {"choices": [
        {"name": "Accidental Landlord"}, {"name": "Lifestyle Investor"},
        {"name": "Growth Investor"}, {"name": "Professional Investor"},
        {"name": "Operator"}, {"name": "Capital Allocator"}, {"name": "Unknown"}
    ]}},
    {"name": "Primary Market", "type": "singleSelect", "options": {"choices": [
        {"name": "Palm Beach County"}, {"name": "Broward County"},
        {"name": "Miami-Dade"}, {"name": "Other FL"}, {"name": "Out of State"}
    ]}},
    {"name": "Secondary Markets", "type": "multipleSelects", "options": {"choices": [
        {"name": "Palm Beach County"}, {"name": "Broward County"},
        {"name": "Miami-Dade"}, {"name": "Other FL"}, {"name": "Out of State"}
    ]}},
    {"name": "Years Investing", "type": "number", "options": {"precision": 0}},
    {"name": "Lead Source", "type": "singleSelect", "options": {"choices": [
        {"name": "FL DOR Records"}, {"name": "Sunbiz"}, {"name": "County Clerk"},
        {"name": "PropStream"}, {"name": "Skip Trace"}, {"name": "Referral"},
        {"name": "BiggerPockets"}, {"name": "Meetup"}, {"name": "LinkedIn"}, {"name": "Other"}
    ]}},
    {"name": "Preferred Contact Method", "type": "singleSelect", "options": {"choices": [
        {"name": "Phone"}, {"name": "Email"}, {"name": "Text"},
        {"name": "LinkedIn"}, {"name": "Direct Mail"}
    ]}},
    {"name": "Last Contact Date", "type": "date", "options": {"dateFormat": {"name": "local"}}},
    {"name": "Last Conversation Notes", "type": "multilineText"},
    {"name": "Relationship Strength", "type": "singleSelect", "options": {"choices": [
        {"name": "New Lead"}, {"name": "Cold"}, {"name": "Warming"},
        {"name": "Warm"}, {"name": "Hot"}, {"name": "Active Client"}
    ]}},
    {"name": "DNC Status", "type": "singleSelect", "options": {"choices": [
        {"name": "Clear"}, {"name": "Federal DNC"}, {"name": "State DNC"},
        {"name": "Internal DNC"}, {"name": "Litigator"}, {"name": "Not Checked"}
    ]}},
    {"name": "Consent Status", "type": "singleSelect", "options": {"choices": [
        {"name": "No Consent"}, {"name": "Verbal Consent"},
        {"name": "Written Consent"}, {"name": "Revoked"}
    ]}},
    {"name": "Phone Type", "type": "singleSelect", "options": {"choices": [
        {"name": "Mobile"}, {"name": "Landline"}, {"name": "VoIP"}, {"name": "Unknown"}
    ]}},
    {"name": "Last DNC Scrub Date", "type": "date", "options": {"dateFormat": {"name": "local"}}}
]

for f in investors_fields:
    r = create_field(base_id, investors_id, f)
    status = "✅" if r else "❌"
    print(f"  {status} {f['name']}")

# ============================================================
# STEP 3: Create Ownership Entities table
# ============================================================
print("\nSTEP 3: Creating Ownership Entities table...")

entities_payload = {
    "name": "Ownership Entities",
    "description": "LLCs, corporations, and trusts holding investment properties",
    "fields": [
        {"name": "Entity Name", "type": "singleLineText"},
        {"name": "Entity Type", "type": "singleSelect", "options": {"choices": [
            {"name": "LLC"}, {"name": "Corporation"}, {"name": "Trust"},
            {"name": "Limited Partnership"}, {"name": "General Partnership"}, {"name": "Individual"}
        ]}},
        {"name": "State of Incorporation", "type": "singleSelect", "options": {"choices": [
            {"name": "Florida"}, {"name": "Delaware"}, {"name": "Wyoming"},
            {"name": "Nevada"}, {"name": "Texas"}, {"name": "New York"}, {"name": "Other"}
        ]}},
        {"name": "Year Formed", "type": "number", "options": {"precision": 0}},
        {"name": "Sunbiz Document Number", "type": "singleLineText"},
        {"name": "Status", "type": "singleSelect", "options": {"choices": [
            {"name": "Active"}, {"name": "Inactive"}, {"name": "Dissolved"}, {"name": "Admin Dissolved"}
        ]}},
        {"name": "Registered Agent", "type": "singleLineText"},
        {"name": "Registered Address", "type": "singleLineText"},
        {"name": "Principal Office Address", "type": "singleLineText"},
        {"name": "Entity Email", "type": "email"},
        {"name": "Entity Phone", "type": "phoneNumber"},
        {"name": "EIN", "type": "singleLineText"}
    ]
}

result = api_call("POST", f"{BASE_URL}/meta/bases/{base_id}/tables", entities_payload)
if result:
    entities_id = result["id"]
    print(f"  ✅ Ownership Entities: {entities_id}")
else:
    print("  ❌ Failed")
    entities_id = None

# ============================================================
# STEP 4: Create Properties table
# ============================================================
print("\nSTEP 4: Creating Properties table...")

properties_payload = {
    "name": "Properties",
    "description": "Investment properties - collateral for DSCR loans",
    "fields": [
        {"name": "Property Address", "type": "singleLineText"},
        {"name": "City", "type": "singleLineText"},
        {"name": "State", "type": "singleLineText"},
        {"name": "ZIP", "type": "singleLineText"},
        {"name": "County", "type": "singleSelect", "options": {"choices": [
            {"name": "Palm Beach"}, {"name": "Broward"}, {"name": "Miami-Dade"}, {"name": "Other"}
        ]}},
        {"name": "Property Type", "type": "singleSelect", "options": {"choices": [
            {"name": "SFR"}, {"name": "Condo"}, {"name": "Townhouse"},
            {"name": "Duplex"}, {"name": "Triplex"}, {"name": "Fourplex"},
            {"name": "Multi 5-10"}, {"name": "Multi 11-50"}, {"name": "Multi 50+"},
            {"name": "STR"}, {"name": "Mixed Use"}, {"name": "Commercial"}, {"name": "Land"}
        ]}},
        {"name": "Beds", "type": "number", "options": {"precision": 0}},
        {"name": "Baths", "type": "number", "options": {"precision": 1}},
        {"name": "Sq Ft", "type": "number", "options": {"precision": 0}},
        {"name": "Year Built", "type": "number", "options": {"precision": 0}},
        {"name": "Estimated Property Value", "type": "currency", "options": {"precision": 0, "symbol": "$"}},
        {"name": "Purchase Price", "type": "currency", "options": {"precision": 0, "symbol": "$"}},
        {"name": "Purchase Date", "type": "date", "options": {"dateFormat": {"name": "local"}}},
        {"name": "Estimated Monthly Rent", "type": "currency", "options": {"precision": 0, "symbol": "$"}},
        {"name": "Occupancy Status", "type": "singleSelect", "options": {"choices": [
            {"name": "Tenant Occupied"}, {"name": "Owner Occupied"}, {"name": "Vacant"},
            {"name": "STR Active"}, {"name": "Unknown"}
        ]}},
        {"name": "Homestead Exempt", "type": "checkbox", "options": {"icon": "check", "color": "greenBright"}},
        {"name": "Property Manager", "type": "singleLineText"},
        {"name": "Listing Status", "type": "singleSelect", "options": {"choices": [
            {"name": "Not Listed"}, {"name": "Listed for Rent"}, {"name": "Listed for Sale"},
            {"name": "Airbnb Active"}, {"name": "VRBO Active"}, {"name": "Unknown"}
        ]}}
    ]
}

result = api_call("POST", f"{BASE_URL}/meta/bases/{base_id}/tables", properties_payload)
if result:
    properties_id = result["id"]
    print(f"  ✅ Properties: {properties_id}")
else:
    print("  ❌ Failed")
    properties_id = None

# ============================================================
# STEP 5: Create Financing table
# ============================================================
print("\nSTEP 5: Creating Financing table...")

financing_payload = {
    "name": "Financing",
    "description": "Existing loans tied to properties - refinance opportunity engine",
    "fields": [
        {"name": "Loan ID", "type": "singleLineText"},
        {"name": "Current Lender", "type": "singleLineText"},
        {"name": "Loan Type", "type": "singleSelect", "options": {"choices": [
            {"name": "Conventional"}, {"name": "FHA"}, {"name": "VA"}, {"name": "DSCR"},
            {"name": "Bank Portfolio"}, {"name": "Hard Money"}, {"name": "Private Lender"},
            {"name": "Seller Financing"}, {"name": "Bridge"}, {"name": "HELOC"},
            {"name": "Commercial"}, {"name": "Unknown"}
        ]}},
        {"name": "Loan Purpose", "type": "singleSelect", "options": {"choices": [
            {"name": "Purchase"}, {"name": "Rate/Term Refi"}, {"name": "Cash-Out Refi"},
            {"name": "HELOC"}, {"name": "Unknown"}
        ]}},
        {"name": "Original Loan Amount", "type": "currency", "options": {"precision": 0, "symbol": "$"}},
        {"name": "Estimated Loan Balance", "type": "currency", "options": {"precision": 0, "symbol": "$"}},
        {"name": "Interest Rate", "type": "percent", "options": {"precision": 3}},
        {"name": "Rate Type", "type": "singleSelect", "options": {"choices": [
            {"name": "Fixed"}, {"name": "ARM 5/1"}, {"name": "ARM 7/1"},
            {"name": "ARM 10/1"}, {"name": "Interest Only"}, {"name": "Unknown"}
        ]}},
        {"name": "Loan Term (Months)", "type": "number", "options": {"precision": 0}},
        {"name": "Loan Origination Date", "type": "date", "options": {"dateFormat": {"name": "local"}}},
        {"name": "Loan Maturity Date", "type": "date", "options": {"dateFormat": {"name": "local"}}},
        {"name": "Monthly Payment Estimate", "type": "currency", "options": {"precision": 0, "symbol": "$"}},
        {"name": "Estimated Annual Taxes", "type": "currency", "options": {"precision": 0, "symbol": "$"}},
        {"name": "Estimated Annual Insurance", "type": "currency", "options": {"precision": 0, "symbol": "$"}},
        {"name": "HOA Monthly", "type": "currency", "options": {"precision": 0, "symbol": "$"}},
        {"name": "Prepayment Penalty", "type": "checkbox", "options": {"icon": "check", "color": "redBright"}},
        {"name": "Prepayment Penalty End Date", "type": "date", "options": {"dateFormat": {"name": "local"}}},
        {"name": "Balloon Payment", "type": "checkbox", "options": {"icon": "check", "color": "redBright"}},
        {"name": "Balloon Date", "type": "date", "options": {"dateFormat": {"name": "local"}}},
        {"name": "Mortgage Document Number", "type": "singleLineText"},
        {"name": "Recording Date", "type": "date", "options": {"dateFormat": {"name": "local"}}},
        {"name": "Notes", "type": "multilineText"}
    ]
}

result = api_call("POST", f"{BASE_URL}/meta/bases/{base_id}/tables", financing_payload)
if result:
    financing_id = result["id"]
    print(f"  ✅ Financing: {financing_id}")
else:
    print("  ❌ Failed")
    financing_id = None

# ============================================================
# STEP 6: Create Opportunities table
# ============================================================
print("\nSTEP 6: Creating Opportunities table...")

opps_payload = {
    "name": "Opportunities",
    "description": "Pipeline - every potential loan deal",
    "fields": [
        {"name": "Deal Name", "type": "singleLineText"},
        {"name": "Loan Type", "type": "singleSelect", "options": {"choices": [
            {"name": "DSCR Purchase"}, {"name": "DSCR Refinance (Rate/Term)"},
            {"name": "DSCR Cash-Out Refi"}, {"name": "DSCR Portfolio Loan"},
            {"name": "Bridge to DSCR"}, {"name": "Other"}
        ]}},
        {"name": "Opportunity Source", "type": "singleSelect", "options": {"choices": [
            {"name": "Maturity Trigger"}, {"name": "High Rate Trigger"},
            {"name": "Hard Money Trigger"}, {"name": "Cash Purchase Trigger"},
            {"name": "Rapid Acquisition Trigger"}, {"name": "Inbound Inquiry"},
            {"name": "Referral"}, {"name": "Manual Entry"}
        ]}},
        {"name": "Opportunity Stage", "type": "singleSelect", "options": {"choices": [
            {"name": "Prospect Identified"}, {"name": "Contacted"},
            {"name": "Conversation Started"}, {"name": "Needs Analysis"},
            {"name": "Scenario Quoted"}, {"name": "Application Submitted"},
            {"name": "In Underwriting"}, {"name": "Conditional Approval"},
            {"name": "Clear to Close"}, {"name": "Closed Won"},
            {"name": "Closed Lost"}, {"name": "On Hold"}
        ]}},
        {"name": "Estimated Loan Amount", "type": "currency", "options": {"precision": 0, "symbol": "$"}},
        {"name": "Estimated Property Value", "type": "currency", "options": {"precision": 0, "symbol": "$"}},
        {"name": "Target LTV", "type": "percent", "options": {"precision": 1}},
        {"name": "Target Rate", "type": "percent", "options": {"precision": 3}},
        {"name": "Target DSCR", "type": "number", "options": {"precision": 2}},
        {"name": "Probability of Close", "type": "percent", "options": {"precision": 0}},
        {"name": "Expected Close Date", "type": "date", "options": {"dateFormat": {"name": "local"}}},
        {"name": "Lost Reason", "type": "singleSelect", "options": {"choices": [
            {"name": "Rate Not Competitive"}, {"name": "Went with Another Lender"},
            {"name": "Decided Not to Refinance"}, {"name": "DSCR Too Low"},
            {"name": "LTV Too High"}, {"name": "Documentation Issues"},
            {"name": "Property Issues"}, {"name": "Unresponsive"}, {"name": "Other"}
        ]}},
        {"name": "Competitor Lender", "type": "singleLineText"},
        {"name": "Notes", "type": "multilineText"},
        {"name": "Date Created", "type": "createdTime"},
        {"name": "Last Modified", "type": "lastModifiedTime"}
    ]
}

result = api_call("POST", f"{BASE_URL}/meta/bases/{base_id}/tables", opps_payload)
if result:
    opps_id = result["id"]
    print(f"  ✅ Opportunities: {opps_id}")
else:
    print("  ❌ Failed")
    opps_id = None

# ============================================================
# STEP 7: Create Outreach Log table
# ============================================================
print("\nSTEP 7: Creating Outreach Log table...")

outreach_payload = {
    "name": "Outreach Log",
    "description": "Every touchpoint with every investor",
    "fields": [
        {"name": "Activity Summary", "type": "singleLineText"},
        {"name": "Contact Method", "type": "singleSelect", "options": {"choices": [
            {"name": "Phone Call"}, {"name": "Voicemail"}, {"name": "Email"},
            {"name": "Text/SMS"}, {"name": "LinkedIn Message"}, {"name": "LinkedIn Connection"},
            {"name": "Direct Mail"}, {"name": "In Person"}, {"name": "Video Call"}
        ]}},
        {"name": "Direction", "type": "singleSelect", "options": {"choices": [
            {"name": "Outbound"}, {"name": "Inbound"}
        ]}},
        {"name": "Date", "type": "date", "options": {"dateFormat": {"name": "local"}}},
        {"name": "Call Duration (min)", "type": "number", "options": {"precision": 0}},
        {"name": "Message Sent", "type": "multilineText"},
        {"name": "Response Status", "type": "singleSelect", "options": {"choices": [
            {"name": "No Answer"}, {"name": "Left Voicemail"}, {"name": "Spoke Live"},
            {"name": "Email Opened"}, {"name": "Email Replied"}, {"name": "Text Replied"},
            {"name": "Connected on LinkedIn"}, {"name": "Bounced"},
            {"name": "Wrong Number"}, {"name": "Do Not Call"}
        ]}},
        {"name": "Outcome", "type": "singleSelect", "options": {"choices": [
            {"name": "Positive - Interested"}, {"name": "Positive - Meeting Set"},
            {"name": "Neutral - More Info Needed"}, {"name": "Neutral - Call Back Later"},
            {"name": "Negative - Not Interested"}, {"name": "Negative - Do Not Contact"},
            {"name": "No Response"}
        ]}},
        {"name": "Disposition Notes", "type": "multilineText"},
        {"name": "Follow Up Date", "type": "date", "options": {"dateFormat": {"name": "local"}}},
        {"name": "Follow Up Action", "type": "singleLineText"},
        {"name": "Date Created", "type": "createdTime"}
    ]
}

result = api_call("POST", f"{BASE_URL}/meta/bases/{base_id}/tables", outreach_payload)
if result:
    outreach_id = result["id"]
    print(f"  ✅ Outreach Log: {outreach_id}")
else:
    print("  ❌ Failed")
    outreach_id = None

# ============================================================
# STEP 8: Create Compliance table
# ============================================================
print("\nSTEP 8: Creating Compliance table...")

compliance_payload = {
    "name": "Compliance",
    "description": "DNC tracking, consent records, and scrub history",
    "fields": [
        {"name": "Record Label", "type": "singleLineText"},
        {"name": "Record Type", "type": "singleSelect", "options": {"choices": [
            {"name": "DNC Scrub"}, {"name": "Consent Obtained"}, {"name": "Consent Revoked"},
            {"name": "Opt-Out Request"}, {"name": "Litigator Flag"},
            {"name": "TCPA Complaint"}, {"name": "Internal DNC Add"}
        ]}},
        {"name": "Date", "type": "date", "options": {"dateFormat": {"name": "local"}}},
        {"name": "DNC List Checked", "type": "multipleSelects", "options": {"choices": [
            {"name": "Federal DNC"}, {"name": "Florida State DNC"},
            {"name": "Internal DNC"}, {"name": "Known Litigator List"}
        ]}},
        {"name": "Result", "type": "singleSelect", "options": {"choices": [
            {"name": "Clear - All Lists"}, {"name": "Hit - Federal DNC"},
            {"name": "Hit - State DNC"}, {"name": "Hit - Internal DNC"},
            {"name": "Hit - Litigator"}, {"name": "Hit - Multiple Lists"}
        ]}},
        {"name": "Phone Number Checked", "type": "phoneNumber"},
        {"name": "Consent Type", "type": "singleSelect", "options": {"choices": [
            {"name": "Prior Express Written Consent (PEWC)"},
            {"name": "Verbal Consent (Recorded)"},
            {"name": "Verbal Consent (Not Recorded)"},
            {"name": "Website Opt-In"}, {"name": "Business Card"}, {"name": "Revoked"}
        ]}},
        {"name": "Consent Obtained Via", "type": "singleSelect", "options": {"choices": [
            {"name": "Phone Call"}, {"name": "Email"}, {"name": "Text"},
            {"name": "Website"}, {"name": "In Person"}, {"name": "Direct Mail Reply"}
        ]}},
        {"name": "Consent Document URL", "type": "url"},
        {"name": "Expiration Date", "type": "date", "options": {"dateFormat": {"name": "local"}}},
        {"name": "Performed By", "type": "singleLineText"},
        {"name": "Notes", "type": "multilineText"}
    ]
}

result = api_call("POST", f"{BASE_URL}/meta/bases/{base_id}/tables", compliance_payload)
if result:
    compliance_id = result["id"]
    print(f"  ✅ Compliance: {compliance_id}")
else:
    print("  ❌ Failed")
    compliance_id = None

# ============================================================
# STEP 9: Create all linked record fields
# ============================================================
print("\nSTEP 9: Creating linked record relationships...")

table_ids = {
    "Investors": investors_id,
    "Ownership Entities": entities_id,
    "Properties": properties_id,
    "Financing": financing_id,
    "Opportunities": opps_id,
    "Outreach Log": outreach_id,
    "Compliance": compliance_id
}

# Each link is created ONCE. Airtable auto-creates the reverse link.
# Format: (source_table, field_name_on_source, target_table, reverse_field_name)
links = [
    # Entities → Investors (creates reverse "Entities" on Investors)
    ("Ownership Entities", "Investor (Owner)", "Investors"),
    # Properties → Investors (creates reverse "Properties" on Investors)
    ("Properties", "Owner Investor", "Investors"),
    # Properties → Ownership Entities (creates reverse "Properties" on Entities)
    ("Properties", "Owner Entity", "Ownership Entities"),
    # Financing → Properties (creates reverse "Financing Records" on Properties)
    ("Financing", "Property", "Properties"),
    # Opportunities → Investors (creates reverse "Opportunities" on Investors)
    ("Opportunities", "Investor", "Investors"),
    # Opportunities → Properties (creates reverse "Opportunities" on Properties)
    ("Opportunities", "Property", "Properties"),
    # Outreach Log → Investors (creates reverse "Outreach Log" on Investors)
    ("Outreach Log", "Investor", "Investors"),
    # Outreach Log → Opportunities
    ("Outreach Log", "Linked Opportunity", "Opportunities"),
    # Compliance → Investors (creates reverse "Compliance Records" on Investors)
    ("Compliance", "Investor", "Investors"),
]

for src_table, field_name, linked_table in links:
    src_id = table_ids.get(src_table)
    lnk_id = table_ids.get(linked_table)

    if not src_id or not lnk_id:
        print(f"  ⚠️ Skip {src_table}.{field_name} (missing table)")
        continue

    print(f"  {src_table}.{field_name} → {linked_table}")

    payload = {
        "name": field_name,
        "type": "multipleRecordLinks",
        "options": {"linkedTableId": lnk_id}
    }

    r = create_field(base_id, src_id, payload)
    status = "✅" if r else "❌"
    print(f"    {status}")
    time.sleep(0.5)

# ============================================================
# SUMMARY
# ============================================================
print("\n" + "=" * 60)
print("BUILD COMPLETE!")
print("=" * 60)
print(f"\n  Base URL: https://airtable.com/{base_id}")
print(f"\n  Tables created:")
for name, tid in table_ids.items():
    if tid:
        print(f"    ✅ {name} ({tid})")
    else:
        print(f"    ❌ {name} (failed)")

print(f"""
WHAT WAS BUILT AUTOMATICALLY:
  • 7 tables with all basic fields (text, number, date, select, currency, etc.)
  • All single/multi select dropdown options pre-configured
  • All linked record relationships between tables
  • Auto-timestamp fields (Created Time, Last Modified)

WHAT YOU NEED TO ADD MANUALLY (~30-45 min):
  See DSCR_Airtable_Build_Guide.md for exact formulas.
  • Formula fields (15 fields)
  • Rollup fields (12 fields)
  • Lookup fields (3 fields)
  • Views (24 saved views)
  • Automations (8)
  • Interfaces/Dashboards (4)
""")
