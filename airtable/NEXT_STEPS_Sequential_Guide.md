# Airtable CRM — Next Steps (Sequential Guide)

Do these in order. Each section is either an **Airtable AI prompt** (paste into Airtable AI) or a **Manual step** (you do it yourself in the UI).

---

## PHASE 1: QUICK FIXES (5 minutes)

### Step 1 — MANUAL: Delete Table 8
1. Open your Airtable base
2. Find the tab labeled "Table 8" at the top
3. Click the dropdown arrow (▼) next to the tab name
4. Click "Delete table"
5. Confirm deletion

### Step 2 — MANUAL: Rename "Trigger County" → "Trigger Count"
1. Go to the **Properties** table
2. Find the column header labeled "Trigger County"
3. Click the column header → "Edit field"
4. Change the name to **Trigger Count**
5. Click Save

### Step 3 — AI PROMPT: Add "Estimated Annual Rent" to Properties
```
On the "Properties" table, please create a formula field named "Estimated Annual Rent" with this formula:

{Estimated Monthly Rent} * 12
```

### Step 4 — AI PROMPT: Add "Property Count" to Ownership Entities
```
On the "Ownership Entities" table, please create a rollup field named "Property Count":
- Use the "Properties" link field on this table
- Field to aggregate: Property Address
- Aggregation function: COUNTA(values)
```

**After Steps 1-4: All tables are 100% field-complete.**

---

## PHASE 2: KEY VIEWS (15-20 minutes)

Views are saved filter/sort configurations. They turn raw data into actionable lists.

### Step 5 — AI PROMPT: Investors Views (6 views)
```
On the "Investors" table, please create these 6 views:

1. Grid view named "🔥 Tier 1 Prospects"
   - Filter: Lead Tier contains "Tier 1"
   - Sort: Lead Score (0-100), descending
   - Group by: Primary Market

2. Grid view named "⭐ Tier 2 Prospects"
   - Filter: Lead Tier contains "Tier 2"
   - Sort: Lead Score (0-100), descending

3. Grid view named "📞 Follow-Up Due"
   - Filter: Days Since Last Contact is greater than 30, AND Relationship Strength is not "Cold", AND DNC Status equals "Clear"
   - Sort: Days Since Last Contact, descending

4. Grid view named "🚫 DNC / Do Not Contact"
   - Filter: DNC Status is any of: Federal DNC, State DNC, Internal DNC, Litigator

5. Grid view named "🆕 New Leads (Uncontacted)"
   - Filter: Last Contact Date is empty, AND DNC Status equals "Clear"
   - Sort: Lead Score (0-100), descending

6. Gallery view named "Gallery — Investor Cards"
   - Show fields: Full Name, Lead Tier, Lead Score (0-100), Property Count, Total Portfolio Value, Primary Market, Phone (Mobile), Last Contact Date
```

### Step 6 — AI PROMPT: Properties Views (3 views)
```
On the "Properties" table, please create these 3 views:

1. Grid view named "💰 Cash Purchase Opportunities"
   - Filter: Cash Purchase Flag is not empty
   - Sort: Estimated Property Value, descending

2. Grid view named "🏠 All Properties by Investor"
   - Group by: Owner Investor
   - Sort: Estimated Property Value, descending

3. Grid view named "⚠️ Low DSCR Properties"
   - Filter: DSCR Status contains "Below 1.0" OR DSCR Status contains "Marginal"
   - Sort: Estimated DSCR, ascending
```

### Step 7 — AI PROMPT: Financing Views (6 views)
```
On the "Financing" table, please create these 6 views:

1. Grid view named "🚨 Maturity Window (12-24 mo)"
   - Filter: Maturity Window Flag is not empty
   - Sort: Months to Maturity, ascending

2. Grid view named "🚨 High Rate Loans (>7%)"
   - Filter: High Rate Flag is not empty
   - Sort: Interest Rate, descending

3. Grid view named "🚨 Hard Money / Bridge / Private"
   - Filter: Hard Money Flag is not empty
   - Sort: Estimated Loan Balance, descending

4. Grid view named "🚨 Balloon Risk"
   - Filter: Balloon Risk Flag is not empty
   - Sort: Balloon Date, ascending

5. Grid view named "⏳ Prepay Penalty Active"
   - Filter: Prepay Penalty Clear contains "Active"
   - Sort: Prepayment Penalty End Date, ascending

6. Grid view named "🏆 Highest Refi Score"
   - Filter: Refinance Opportunity Score is greater than 0
   - Sort: Refinance Opportunity Score, descending
```

### Step 8 — AI PROMPT: Opportunities Views (4 views)
```
On the "Opportunities" table, please create these 4 views:

1. Kanban view named "📊 Pipeline — Kanban"
   - Stack by: Opportunity Stage
   - Card fields: Deal Name, Investor, Estimated Loan Amount, Probability of Close, Expected Close Date

2. Grid view named "💲 Active Pipeline (by Value)"
   - Filter: Opportunity Stage is none of: Closed Won, Closed Lost, On Hold
   - Sort: Weighted Value, descending

3. Grid view named "📅 Closing This Month"
   - Filter: Expected Close Date is within the next 30 days, AND Opportunity Stage is none of: Closed Won, Closed Lost
   - Sort: Expected Close Date, ascending

4. Grid view named "⚠️ Stale Deals (>14 days in stage)"
   - Filter: Days in Stage is greater than 14, AND Opportunity Stage is none of: Closed Won, Closed Lost, On Hold
   - Sort: Days in Stage, descending
```

### Step 9 — AI PROMPT: Outreach Log Views (3 views)
```
On the "Outreach Log" table, please create these 3 views:

1. Grid view named "📅 Today's Follow-Ups"
   - Filter: Follow Up Date is today
   - Sort: Follow Up Date, ascending

2. Grid view named "📅 This Week's Follow-Ups"
   - Filter: Follow Up Date is within the next 7 days
   - Sort: Follow Up Date, ascending

3. Grid view named "📊 Activity by Investor"
   - Group by: Investor
   - Sort: Date, descending
```

### Step 10 — AI PROMPT: Compliance Views (2 views)
```
On the "Compliance" table, please create these 2 views:

1. Grid view named "⛔ Overdue DNC Scrubs"
   - Filter: Scrub Overdue is not empty
   - Sort: Next Scrub Due, ascending

2. Grid view named "📋 Consent Records"
   - Filter: Record Type is any of: Consent Obtained, Consent Revoked
   - Sort: Date, descending
```

**After Steps 5-10: All 24 views created.**

---

## PHASE 3: AUTOMATIONS (15-20 minutes)

Automations must be created manually — Airtable AI can't create them. Follow each step exactly.

### Step 11 — MANUAL: Auto-Create Opportunity from Hard Money Trigger
1. Click "Automations" in the top toolbar
2. Click "+ Create automation"
3. Name it: **Auto-Create Opportunity from Hard Money Trigger**
4. **Trigger:** "When record matches conditions"
   - Table: Financing
   - Condition: Hard Money Flag — is not empty
5. **Action:** "Create record"
   - Table: Opportunities
   - Fields to set:
     - Deal Name: (use the formula icon) → `{Loan ID} - DSCR Refi`
     - Loan Type: `DSCR Refinance (Rate/Term)`
     - Opportunity Source: `Hard Money Trigger`
     - Opportunity Stage: `Prospect Identified`
     - Notes: `Auto-created: Hard money loan detected. Investor may be a candidate for DSCR refinance.`
6. Click "Test" → verify it works → Turn ON

### Step 12 — MANUAL: Auto-Create Opportunity from Maturity Trigger
1. Click "+ Create automation"
2. Name: **Auto-Create Opportunity from Maturity Trigger**
3. **Trigger:** "When record matches conditions"
   - Table: Financing
   - Condition: Maturity Window Flag — is not empty
4. **Action:** "Create record"
   - Table: Opportunities
   - Fields:
     - Opportunity Source: `Maturity Trigger`
     - Opportunity Stage: `Prospect Identified`
     - Notes: `Auto-created: Loan maturing within 24 months. Proactive refinance outreach recommended.`
5. Test → Turn ON

### Step 13 — MANUAL: Auto-Create Opportunity from Cash Purchase
1. Click "+ Create automation"
2. Name: **Auto-Create Opportunity from Cash Purchase**
3. **Trigger:** "When record matches conditions"
   - Table: Properties
   - Condition: Cash Purchase Flag — is not empty
4. **Action:** "Create record"
   - Table: Opportunities
   - Fields:
     - Loan Type: `DSCR Cash-Out Refi`
     - Opportunity Source: `Cash Purchase Trigger`
     - Opportunity Stage: `Prospect Identified`
     - Notes: `Auto-created: Cash purchase detected. Investor may want to recoup capital via cash-out DSCR refi.`
5. Test → Turn ON

### Step 14 — MANUAL: Follow-Up Reminder
1. Click "+ Create automation"
2. Name: **Follow-Up Reminder**
3. **Trigger:** "When record matches conditions"
   - Table: Outreach Log
   - Condition: Follow Up Date — is today
4. **Action:** "Send an email"
   - To: your email address
   - Subject: `📞 Follow-up due: {Investor}`
   - Body: `Follow-up action: {Follow Up Action}. Last outcome: {Outcome}. Notes: {Disposition Notes}`
5. Test → Turn ON

### Step 15 — MANUAL: DNC Scrub Overdue Alert
1. Click "+ Create automation"
2. Name: **DNC Scrub Overdue Alert**
3. **Trigger:** "When record matches conditions"
   - Table: Compliance
   - Condition: Scrub Overdue — contains "OVERDUE"
4. **Action:** "Send an email"
   - To: your email address
   - Subject: `⛔ DNC SCRUB OVERDUE`
   - Body: `Federal requirement: Re-scrub DNC lists every 31 days. Your last scrub for {Investor} is overdue. Do not make outbound calls until scrub is current.`
5. Test → Turn ON

### Step 16 — MANUAL: Stale Deal Alert
1. Click "+ Create automation"
2. Name: **Stale Deal Alert**
3. **Trigger:** "When record matches conditions"
   - Table: Opportunities
   - Condition: Days in Stage — is greater than 14
   - AND: Opportunity Stage — is none of: Closed Won, Closed Lost, On Hold
4. **Action:** "Send an email"
   - To: your email address
   - Subject: `⚠️ Stale deal: {Deal Name}`
   - Body: `This deal has been in "{Opportunity Stage}" for {Days in Stage} days. Take action: advance it, update it, or close it.`
5. Test → Turn ON

### Step 17 — MANUAL: Update Investor Last Contact Date
1. Click "+ Create automation"
2. Name: **Update Investor Last Contact Date**
3. **Trigger:** "When a record is created"
   - Table: Outreach Log
4. **Action:** "Update record"
   - Table: Investors
   - Record: The Investor linked in the trigger record
   - Field to update: Last Contact Date → today's date
5. Test → Turn ON

### Step 18 — MANUAL: New Lead Auto-DNC Check Reminder
1. Click "+ Create automation"
2. Name: **New Lead Auto-DNC Check Reminder**
3. **Trigger:** "When a record is created"
   - Table: Investors
4. **Action:** "Create record"
   - Table: Compliance
   - Fields:
     - Investor: link to the new investor record
     - Record Type: `DNC Scrub`
     - Date: today
     - Result: `Clear - All Lists`
     - Notes: `Auto-created reminder: Scrub this number against DNC lists before any outreach.`
5. Test → Turn ON

**After Steps 11-18: All 8 automations created.**

---

## PHASE 4: TEST UPLOAD (10 minutes)

Test CSV files are pre-built in the `airtable/test_data/` folder. Upload in this exact order:

### Step 19 — Upload Test Investors
1. Go to the **Investors** table
2. Click the dropdown (▼) next to the table name → **Import data** → **CSV file**
3. Upload `test_investors.csv`
4. Map each column to the correct field
5. Import

### Step 20 — Upload Test Entities
1. Go to the **Ownership Entities** table
2. Import `test_entities.csv`
3. When mapping, link the "Investor (Owner)" column to match on Full Name

### Step 21 — Upload Test Properties
1. Go to the **Properties** table
2. Import `test_properties.csv`
3. Link "Owner Investor" to match on Full Name
4. Link "Owner Entity" to match on Entity Name

### Step 22 — Upload Test Financing
1. Go to the **Financing** table
2. Import `test_financing.csv`
3. Link "Property" to match on Property Address

### Step 23 — VALIDATE
After upload, check these things:
- [ ] Financing table: Do trigger flags show up? (Hard Money Flag, High Rate Flag, etc.)
- [ ] Properties table: Do rollups calculate? (Total Property Debt, Estimated DSCR, etc.)
- [ ] Investors table: Do lead scores calculate? (Lead Score 0-100, Lead Tier)
- [ ] Views: Do filtered views show correct records? ("🔥 Tier 1", "🚨 Hard Money")
- [ ] Automations: Did any auto-create Opportunities? (check Opportunities table)

---

## PHASE 5: INTERFACES (Later — after test upload validates)

Build these 4 dashboards in the Airtable Interface Designer. Not critical for test upload, but essential before daily use.

1. **🎯 Daily Command Center** — Pipeline value, follow-ups due, top leads
2. **👤 Investor Profile** — Single-investor detail view with portfolio, financing, outreach history
3. **📊 Pipeline Manager** — Kanban + deal metrics
4. **🚨 Trigger Alert Center** — All active trigger flags in one place

Detailed specs are in the Build Guide (DSCR_Airtable_Build_Guide.md, Step 7).

---

## PHASE 6: FULL IMPORT + HUBSPOT (Later)

Once test upload validates:
1. Prepare full CSV files (7,500 leads)
2. Import in order: Investors → Entities → Properties → Financing
3. Set up HubSpot Free + Zapier sync for Tier 1/2 prospects
4. Begin outreach

---

*Total estimated time for Phases 1-4: ~45-60 minutes*
