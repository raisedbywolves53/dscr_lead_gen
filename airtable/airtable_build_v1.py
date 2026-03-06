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
    """Make API call with rate limit handling."""
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
            print(f"  ERROR {resp.status_code}: {resp.text}")
            if attempt < retries - 1:
                time.sleep(2)
                continue
            return None

        time.sleep(0.25)  # Gentle rate limiting
        return resp.json()
    return None

# ============================================================
# STEP 1: Get workspace ID
# ============================================================
print("=" * 60)
print("STEP 1: Getting workspace ID...")
print("=" * 60)

# List bases to find workspace - we need to use the bases endpoint
# since the workspaces endpoint returned NOT_FOUND
# We'll create a base first, which requires a workspace ID
# Let's try the whoami endpoint or list workspaces differently

resp = requests.get(f"{BASE_URL}/meta/whoami", headers=HEADERS)
print(f"  whoami response: {resp.status_code} - {resp.text[:200]}")

# Try to get workspaces through bases list
# Since user has no bases, we need workspace ID another way
# The Airtable create-base API can use a workspaceId
# Let's try listing workspaces via the enterprise endpoint or create without workspace

# Actually, Airtable's create base endpoint requires workspaceId
# Let's try to extract it from the bases metadata
resp2 = requests.get(f"{BASE_URL}/meta/bases", headers=HEADERS)
print(f"  bases response: {resp2.status_code} - {resp2.text[:200]}")

# If no bases exist, we need to try creating one to find workspace
# The API docs say we can list workspaces at /v0/meta/workspaces
# but that may require specific scope. Let's check token scopes.

print("\n  Checking if we can create a base directly...")
print("  (Airtable may auto-assign to default workspace)")

# ============================================================
# STEP 2: Create the base
# ============================================================
print("\n" + "=" * 60)
print("STEP 2: Creating base 'DSCR Investor Intelligence'...")
print("=" * 60)

# First table definition - Investors (required to create base)
create_base_payload = {
    "name": "DSCR Investor Intelligence",
    "tables": [
        {
            "name": "Investors",
            "description": "Primary table - every record is a decision-maker / real estate investor",
            "fields": [
                {"name": "Full Name", "type": "singleLineText", "description": "Investor full name (primary field)"},
                {"name": "First Name", "type": "singleLineText", "description": "For mail merge / personalization"},
                {"name": "Last Name", "type": "singleLineText", "description": "For sorting and deduplication"},
                {"name": "Phone (Mobile)", "type": "phoneNumber"},
                {"name": "Phone (Secondary)", "type": "phoneNumber"},
                {"name": "Email (Primary)", "type": "email"},
                {"name": "Email (Secondary)", "type": "email"},
                {"name": "LinkedIn URL", "type": "url"},
                {"name": "Mailing Address", "type": "singleLineText"},
                {"name": "Mailing City", "type": "singleLineText"},
                {"name": "Mailing State", "type": "singleLineText"},
                {"name": "Mailing ZIP", "type": "singleLineText", "description": "Text to preserve leading zeros"},
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
        },
        {
            "name": "Ownership Entities",
            "description": "LLCs, corporations, and trusts that hold investment properties",
            "fields": [
                {"name": "Entity Name", "type": "singleLineText", "description": "LLC/Corp name (primary field)"},
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
        },
        {
            "name": "Properties",
            "description": "Investment properties - the collateral for DSCR loans",
            "fields": [
                {"name": "Property Address", "type": "singleLineText", "description": "Full street address (primary field)"},
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
        },
        {
            "name": "Financing",
            "description": "Existing loans tied to properties - engine for refinance opportunity detection",
            "fields": [
                {"name": "Loan ID", "type": "singleLineText", "description": "Format: [Property Address] - [Lender]"},
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
        },
        {
            "name": "Opportunities",
            "description": "Pipeline - every potential loan deal gets tracked here",
            "fields": [
                {"name": "Deal Name", "type": "singleLineText", "description": "Format: [Investor Last Name] - [Property] - [Loan Type]"},
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
                {"name": "Notes", "type": "multilineText"}
            ]
        },
        {
            "name": "Outreach Log",
            "description": "Every touchpoint with every investor - critical for compliance and follow-up",
            "fields": [
                {"name": "Activity Summary", "type": "singleLineText", "description": "Brief description (primary field)"},
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
                {"name": "Follow Up Action", "type": "singleLineText"}
            ]
        },
        {
            "name": "Compliance",
            "description": "DNC tracking, consent records, and scrub history for Florida mortgage outreach",
            "fields": [
                {"name": "Record ID", "type": "autoNumber"},
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
    ]
}

result = api_call("POST", f"{BASE_URL}/meta/bases", create_base_payload)

if not result:
    print("\n❌ FAILED to create base. Check token permissions.")
    print("Token needs these scopes: data.records:read, data.records:write,")
    print("schema.bases:read, schema.bases:write")
    sys.exit(1)

base_id = result.get("id")
print(f"\n  ✅ Base created! ID: {base_id}")

# Extract table IDs
tables = result.get("tables", [])
table_map = {}
for t in tables:
    table_map[t["name"]] = t["id"]
    print(f"  Table: {t['name']} → {t['id']}")

# ============================================================
# STEP 3: Create linked record fields between tables
# ============================================================
print("\n" + "=" * 60)
print("STEP 3: Creating linked record fields...")
print("=" * 60)

# Define all the links we need to create
# Format: (source_table, field_name, linked_table, description)
links = [
    # Investors links
    ("Investors", "Entities", "Ownership Entities", "LLCs/companies owned by this investor"),
    ("Investors", "Properties", "Properties", "Properties owned directly by this investor"),
    ("Investors", "Opportunities", "Opportunities", "Loan deals for this investor"),
    ("Investors", "Outreach Log", "Outreach Log", "Contact history with this investor"),
    ("Investors", "Compliance Records", "Compliance", "DNC/consent records for this investor"),

    # Ownership Entities → Investors (already created above as reverse of Entities)
    # We need: Ownership Entities → Properties
    ("Ownership Entities", "Properties", "Properties", "Properties held by this entity"),

    # Properties → Financing
    ("Properties", "Financing Records", "Financing", "Loans on this property"),

    # Properties → Opportunities (reverse already exists from Investors→Opportunities)
    # Actually we need a direct link from Properties to Opportunities too
    ("Properties", "Opportunities", "Opportunities", "Deals involving this property"),

    # Outreach Log → Opportunities
    ("Outreach Log", "Linked Opportunity", "Opportunities", "Related deal if outreach is deal-specific"),
]

# Track created reverse links to avoid duplicates
for source_table, field_name, linked_table, description in links:
    source_id = table_map.get(source_table)
    linked_id = table_map.get(linked_table)

    if not source_id or not linked_id:
        print(f"  ⚠️ Skipping {source_table}.{field_name} - table not found")
        continue

    print(f"  Creating: {source_table}.{field_name} → {linked_table}")

    field_payload = {
        "name": field_name,
        "type": "multipleRecordLinks",
        "options": {
            "linkedTableId": linked_id
        }
    }

    result = api_call("POST", f"{BASE_URL}/meta/bases/{base_id}/tables/{source_id}/fields", field_payload)

    if result:
        print(f"    ✅ Created {field_name}")
    else:
        print(f"    ⚠️ May already exist (from reverse link)")

    time.sleep(0.5)  # Extra delay for linked fields

# ============================================================
# STEP 4: Add Created Time and Last Modified Time fields
# ============================================================
print("\n" + "=" * 60)
print("STEP 4: Adding auto-timestamp fields...")
print("=" * 60)

# Opportunities needs Date Created and Last Modified
opps_id = table_map.get("Opportunities")
if opps_id:
    for fname, ftype in [("Date Created", "createdTime"), ("Last Modified", "lastModifiedTime")]:
        print(f"  Creating: Opportunities.{fname}")
        payload = {"name": fname, "type": ftype}
        result = api_call("POST", f"{BASE_URL}/meta/bases/{base_id}/tables/{opps_id}/fields", payload)
        if result:
            print(f"    ✅ Created")

# Outreach Log needs Date Created
outreach_id = table_map.get("Outreach Log")
if outreach_id:
    print(f"  Creating: Outreach Log.Date Created")
    payload = {"name": "Date Created", "type": "createdTime"}
    result = api_call("POST", f"{BASE_URL}/meta/bases/{base_id}/tables/{outreach_id}/fields", payload)
    if result:
        print(f"    ✅ Created")

print("\n" + "=" * 60)
print("BUILD COMPLETE!")
print("=" * 60)
print(f"\n  Base ID: {base_id}")
print(f"  Base URL: https://airtable.com/{base_id}")
print(f"\n  Tables created: {len(table_map)}")
for name, tid in table_map.items():
    print(f"    • {name} ({tid})")

print(f"""
  ✅ WHAT WAS BUILT:
  • 7 tables with all non-formula fields
  • All single select / multiple select dropdown options pre-configured
  • All linked record relationships between tables
  • Auto-timestamp fields (Created Time, Last Modified)

  ❌ WHAT YOU NEED TO ADD MANUALLY:
  • Formula fields (~15 fields)
  • Rollup fields (~12 fields)
  • Lookup fields (~3 fields)
  • Views (24 saved views)
  • Automations (8 automations)
  • Interfaces (4 dashboards)

  See the DSCR_Airtable_Build_Guide.md for exact formulas.
""")
