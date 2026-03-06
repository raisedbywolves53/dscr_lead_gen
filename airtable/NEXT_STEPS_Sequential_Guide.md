# Airtable CRM — Next Steps (Sequential Guide)

Everything remaining is done manually in the Airtable UI. Follow each step in order.

**Airtable Base URL:** https://airtable.com/appJV7J1ZrNEBAWAm

---

## PHASE 1: QUICK FIXES (5 minutes)

### Step 1 — Delete Table 8
1. Open your Airtable base
2. Find the tab labeled **Table 8** at the top
3. Click the dropdown arrow (▼) next to the tab name
4. Click **Delete table**
5. Confirm deletion

### Step 2 — Rename "Trigger County" → "Trigger Count"
1. Go to the **Properties** table
2. Scroll right to find the column header labeled **Trigger County**
3. Click the column header → click **Edit field**
4. Change the name to **Trigger Count**
5. Click **Save**

### Step 3 — Add "Estimated Annual Rent" formula to Properties
1. Stay on the **Properties** table
2. Scroll to the rightmost column → click the **+** to add a new field
3. Name: **Estimated Annual Rent**
4. Type: **Formula**
5. Paste this formula:
```
{Estimated Monthly Rent} * 12
```
6. Click **Save**

### Step 4 — Add "Property Count" rollup to Ownership Entities
1. Go to the **Ownership Entities** table
2. Scroll right → click **+** to add a new field
3. Name: **Property Count**
4. Type: **Rollup**
5. Linked record field: select **Properties**
6. Field to aggregate: select **Property Address**
7. Aggregation function: type or select **COUNTA(values)**
8. Click **Save**

**✅ After Steps 1-4: All tables are 100% field-complete.**

---

## PHASE 2: VIEWS (20-30 minutes)

For each view: click the **+** icon next to the existing views on the left sidebar (or top toolbar), choose the view type, name it, then configure filters/sorts.

---

### INVESTORS TABLE — 6 views

#### View 1: 🔥 Tier 1 Prospects
1. Go to **Investors** table
2. Click **+ Add a view** → choose **Grid**
3. Name: `🔥 Tier 1 Prospects`
4. Click **Filter** → Add filter:
   - Field: **Lead Tier** → Operator: **contains** → Value: `Tier 1`
5. Click **Sort** → Add sort:
   - Field: **Lead Score (0-100)** → **Descending** (Z→A / 9→1)
6. Click **Group** → Group by:
   - Field: **Primary Market**

#### View 2: ⭐ Tier 2 Prospects
1. Click **+ Add a view** → **Grid**
2. Name: `⭐ Tier 2 Prospects`
3. Filter: **Lead Tier** → contains → `Tier 2`
4. Sort: **Lead Score (0-100)** → Descending

#### View 3: 📞 Follow-Up Due
1. Click **+ Add a view** → **Grid**
2. Name: `📞 Follow-Up Due`
3. Filter (add 3 conditions, set to "AND"):
   - **Days Since Last Contact** → is greater than → `30`
   - AND **Relationship Strength** → is not → `Cold`
   - AND **DNC Status** → is → `Clear`
4. Sort: **Days Since Last Contact** → Descending

#### View 4: 🚫 DNC / Do Not Contact
1. Click **+ Add a view** → **Grid**
2. Name: `🚫 DNC / Do Not Contact`
3. Filter: **DNC Status** → is any of → select: `Federal DNC`, `State DNC`, `Internal DNC`, `Litigator`

#### View 5: 🆕 New Leads (Uncontacted)
1. Click **+ Add a view** → **Grid**
2. Name: `🆕 New Leads (Uncontacted)`
3. Filter (2 conditions, AND):
   - **Last Contact Date** → is empty
   - AND **DNC Status** → is → `Clear`
4. Sort: **Lead Score (0-100)** → Descending

#### View 6: Gallery — Investor Cards
1. Click **+ Add a view** → **Gallery**
2. Name: `Gallery — Investor Cards`
3. Click **Fields** to configure visible fields. Show only:
   - Full Name, Lead Tier, Lead Score (0-100), Property Count, Total Portfolio Value, Primary Market, Phone (Mobile), Last Contact Date
4. Hide all other fields

---

### PROPERTIES TABLE — 3 views

#### View 7: 💰 Cash Purchase Opportunities
1. Go to **Properties** table
2. Click **+ Add a view** → **Grid**
3. Name: `💰 Cash Purchase Opportunities`
4. Filter: **Cash Purchase Flag** → is not empty
5. Sort: **Estimated Property Value** → Descending

#### View 8: 🏠 All Properties by Investor
1. Click **+ Add a view** → **Grid**
2. Name: `🏠 All Properties by Investor`
3. Group by: **Owner Investor**
4. Sort: **Estimated Property Value** → Descending

#### View 9: ⚠️ Low DSCR Properties
1. Click **+ Add a view** → **Grid**
2. Name: `⚠️ Low DSCR Properties`
3. Filter (2 conditions, set to **OR**):
   - **DSCR Status** → contains → `Below 1.0`
   - OR **DSCR Status** → contains → `Marginal`
4. Sort: **Estimated DSCR** → Ascending

---

### FINANCING TABLE — 6 views

#### View 10: 🚨 Maturity Window (12-24 mo)
1. Go to **Financing** table
2. Click **+ Add a view** → **Grid**
3. Name: `🚨 Maturity Window (12-24 mo)`
4. Filter: **Maturity Window Flag** → is not empty
5. Sort: **Months to Maturity** → Ascending

#### View 11: 🚨 High Rate Loans (>7%)
1. Click **+ Add a view** → **Grid**
2. Name: `🚨 High Rate Loans (>7%)`
3. Filter: **High Rate Flag** → is not empty
4. Sort: **Interest Rate** → Descending

#### View 12: 🚨 Hard Money / Bridge / Private
1. Click **+ Add a view** → **Grid**
2. Name: `🚨 Hard Money / Bridge / Private`
3. Filter: **Hard Money Flag** → is not empty
4. Sort: **Estimated Loan Balance** → Descending

#### View 13: 🚨 Balloon Risk
1. Click **+ Add a view** → **Grid**
2. Name: `🚨 Balloon Risk`
3. Filter: **Balloon Risk Flag** → is not empty
4. Sort: **Balloon Date** → Ascending

#### View 14: ⏳ Prepay Penalty Active
1. Click **+ Add a view** → **Grid**
2. Name: `⏳ Prepay Penalty Active`
3. Filter: **Prepay Penalty Clear** → contains → `Active`
4. Sort: **Prepayment Penalty End Date** → Ascending

#### View 15: 🏆 Highest Refi Score
1. Click **+ Add a view** → **Grid**
2. Name: `🏆 Highest Refi Score`
3. Filter: **Refinance Opportunity Score** → is greater than → `0`
4. Sort: **Refinance Opportunity Score** → Descending

---

### OPPORTUNITIES TABLE — 4 views

#### View 16: 📊 Pipeline — Kanban
1. Go to **Opportunities** table
2. Click **+ Add a view** → **Kanban**
3. Name: `📊 Pipeline — Kanban`
4. Stack by: **Opportunity Stage**
5. Configure card fields to show: Deal Name, Investor, Estimated Loan Amount, Probability of Close, Expected Close Date

#### View 17: 💲 Active Pipeline (by Value)
1. Click **+ Add a view** → **Grid**
2. Name: `💲 Active Pipeline (by Value)`
3. Filter: **Opportunity Stage** → is none of → select: `Closed Won`, `Closed Lost`, `On Hold`
4. Sort: **Weighted Value** → Descending

#### View 18: 📅 Closing This Month
1. Click **+ Add a view** → **Grid**
2. Name: `📅 Closing This Month`
3. Filter (2 conditions, AND):
   - **Expected Close Date** → is within → `the next 30 days`
   - AND **Opportunity Stage** → is none of → `Closed Won`, `Closed Lost`
4. Sort: **Expected Close Date** → Ascending

#### View 19: ⚠️ Stale Deals (>14 days in stage)
1. Click **+ Add a view** → **Grid**
2. Name: `⚠️ Stale Deals (>14 days in stage)`
3. Filter (2 conditions, AND):
   - **Days in Stage** → is greater than → `14`
   - AND **Opportunity Stage** → is none of → `Closed Won`, `Closed Lost`, `On Hold`
4. Sort: **Days in Stage** → Descending

---

### OUTREACH LOG TABLE — 3 views

#### View 20: 📅 Today's Follow-Ups
1. Go to **Outreach Log** table
2. Click **+ Add a view** → **Grid**
3. Name: `📅 Today's Follow-Ups`
4. Filter: **Follow Up Date** → is → `today`
5. Sort: **Follow Up Date** → Ascending

#### View 21: 📅 This Week's Follow-Ups
1. Click **+ Add a view** → **Grid**
2. Name: `📅 This Week's Follow-Ups`
3. Filter: **Follow Up Date** → is within → `the next 7 days`
4. Sort: **Follow Up Date** → Ascending

#### View 22: 📊 Activity by Investor
1. Click **+ Add a view** → **Grid**
2. Name: `📊 Activity by Investor`
3. Group by: **Investor**
4. Sort: **Date** → Descending

---

### COMPLIANCE TABLE — 2 views

#### View 23: ⛔ Overdue DNC Scrubs
1. Go to **Compliance** table
2. Click **+ Add a view** → **Grid**
3. Name: `⛔ Overdue DNC Scrubs`
4. Filter: **Scrub Overdue** → is not empty
5. Sort: **Next Scrub Due** → Ascending

#### View 24: 📋 Consent Records
1. Click **+ Add a view** → **Grid**
2. Name: `📋 Consent Records`
3. Filter: **Record Type** → is any of → select: `Consent Obtained`, `Consent Revoked`
4. Sort: **Date** → Descending

**✅ After Views 1-24: All views created.**

---

## PHASE 3: AUTOMATIONS (15-20 minutes)

All automations are manual. Click **Automations** in the top toolbar to start.

---

### Automation 1: Auto-Create Opportunity from Hard Money Trigger
1. Click **+ Create automation**
2. Name: `Auto-Create Opportunity from Hard Money Trigger`
3. **Trigger:** click "When record matches conditions"
   - Table: **Financing**
   - Condition: **Hard Money Flag** → is not empty
4. **Action:** click **+ Add action** → "Create record"
   - Table: **Opportunities**
   - Set these fields:
     - **Deal Name:** click the blue + insert icon → pick `Loan ID` from trigger, then type ` - DSCR Refi` after it
     - **Loan Type:** `DSCR Refinance (Rate/Term)`
     - **Opportunity Source:** `Hard Money Trigger`
     - **Opportunity Stage:** `Prospect Identified`
     - **Notes:** `Auto-created: Hard money loan detected. Investor may be a candidate for DSCR refinance.`
5. Click **Test** to verify → then toggle the automation **ON**

### Automation 2: Auto-Create Opportunity from Maturity Trigger
1. Click **+ Create automation**
2. Name: `Auto-Create Opportunity from Maturity Trigger`
3. **Trigger:** "When record matches conditions"
   - Table: **Financing**
   - Condition: **Maturity Window Flag** → is not empty
4. **Action:** "Create record"
   - Table: **Opportunities**
   - Set fields:
     - **Opportunity Source:** `Maturity Trigger`
     - **Opportunity Stage:** `Prospect Identified`
     - **Notes:** `Auto-created: Loan maturing within 24 months. Proactive refinance outreach recommended.`
5. Test → Turn **ON**

### Automation 3: Auto-Create Opportunity from Cash Purchase
1. Click **+ Create automation**
2. Name: `Auto-Create Opportunity from Cash Purchase`
3. **Trigger:** "When record matches conditions"
   - Table: **Properties**
   - Condition: **Cash Purchase Flag** → is not empty
4. **Action:** "Create record"
   - Table: **Opportunities**
   - Set fields:
     - **Loan Type:** `DSCR Cash-Out Refi`
     - **Opportunity Source:** `Cash Purchase Trigger`
     - **Opportunity Stage:** `Prospect Identified`
     - **Notes:** `Auto-created: Cash purchase detected. Investor may want to recoup capital via cash-out DSCR refi.`
5. Test → Turn **ON**

### Automation 4: Follow-Up Reminder
1. Click **+ Create automation**
2. Name: `Follow-Up Reminder`
3. **Trigger:** "When record matches conditions"
   - Table: **Outreach Log**
   - Condition: **Follow Up Date** → is → today
4. **Action:** "Send an email"
   - To: **your email address**
   - Subject: `📞 Follow-up due:` then insert **Investor** field from trigger
   - Body: `Follow-up action:` insert **Follow Up Action** `. Last outcome:` insert **Outcome** `. Notes:` insert **Disposition Notes**
5. Test → Turn **ON**

### Automation 5: DNC Scrub Overdue Alert
1. Click **+ Create automation**
2. Name: `DNC Scrub Overdue Alert`
3. **Trigger:** "When record matches conditions"
   - Table: **Compliance**
   - Condition: **Scrub Overdue** → contains → `OVERDUE`
4. **Action:** "Send an email"
   - To: **your email address**
   - Subject: `⛔ DNC SCRUB OVERDUE`
   - Body: `Federal requirement: Re-scrub DNC lists every 31 days. Your last scrub for` insert **Investor** `is overdue. Do not make outbound calls until scrub is current.`
5. Test → Turn **ON**

### Automation 6: Stale Deal Alert
1. Click **+ Create automation**
2. Name: `Stale Deal Alert`
3. **Trigger:** "When record matches conditions"
   - Table: **Opportunities**
   - Conditions (AND):
     - **Days in Stage** → is greater than → `14`
     - AND **Opportunity Stage** → is none of → `Closed Won`, `Closed Lost`, `On Hold`
4. **Action:** "Send an email"
   - To: **your email address**
   - Subject: `⚠️ Stale deal:` insert **Deal Name**
   - Body: `This deal has been in "` insert **Opportunity Stage** `" for` insert **Days in Stage** `days. Take action: advance it, update it, or close it.`
5. Test → Turn **ON**

### Automation 7: Update Investor Last Contact Date
1. Click **+ Create automation**
2. Name: `Update Investor Last Contact Date`
3. **Trigger:** "When a record is created"
   - Table: **Outreach Log**
4. **Action:** "Update record"
   - Table: **Investors**
   - Record ID: click the insert icon → find the **Investor** linked record from the trigger → select its **Record ID**
   - Fields to update:
     - **Last Contact Date** → set to → **Created time** from the trigger (or use "Now")
5. Test → Turn **ON**

### Automation 8: New Lead Auto-DNC Check Reminder
1. Click **+ Create automation**
2. Name: `New Lead Auto-DNC Check Reminder`
3. **Trigger:** "When a record is created"
   - Table: **Investors**
4. **Action:** "Create record"
   - Table: **Compliance**
   - Set fields:
     - **Investor:** click insert icon → select the **Record ID** of the trigger record (this links back to the new investor)
     - **Record Type:** `DNC Scrub`
     - **Date:** use "Now" or today's date
     - **Result:** `Clear - All Lists`
     - **Notes:** `Auto-created reminder: Scrub this number against DNC lists before any outreach.`
5. Test → Turn **ON**

**✅ After Automations 1-8: All automations created.**

---

## PHASE 4: TEST UPLOAD (10 minutes)

Test CSV files are in the repo at `airtable/test_data/`. Upload in this exact order:

### Step 1 — Upload Test Investors
1. Go to the **Investors** table
2. Click the dropdown (▼) next to the table name → **Import data** → **CSV file**
3. Upload `test_investors.csv`
4. Map each CSV column to the matching Airtable field
5. Click **Import**

### Step 2 — Upload Test Entities
1. Go to the **Ownership Entities** table
2. Click dropdown → **Import data** → **CSV file**
3. Upload `test_entities.csv`
4. Map columns. For **Investor (Owner)**: match the CSV value to existing Investor records by **Full Name**
5. Import

### Step 3 — Upload Test Properties
1. Go to the **Properties** table
2. Import `test_properties.csv`
3. Map columns. For linked fields:
   - **Owner Investor** → match on **Full Name**
   - **Owner Entity** → match on **Entity Name**
4. Import

### Step 4 — Upload Test Financing
1. Go to the **Financing** table
2. Import `test_financing.csv`
3. Map columns. For **Property** → match on **Property Address**
4. Import

### Step 5 — Validate Everything
After all uploads, check:

- [ ] **Financing table:** Scroll to trigger columns. LOAN-003, LOAN-006, LOAN-007 should show Hard Money Flag. LOAN-003/005/006/007/009/010 should show High Rate Flag.
- [ ] **Properties table:** Total Property Debt, Estimated Equity, Estimated DSCR should calculate.
- [ ] **Investors table:** Lead Score (0-100) and Lead Tier should populate. David Goldstein and Jennifer Wu should score highest.
- [ ] **Views:** Click the trigger views (🚨 Hard Money, 🚨 High Rate) — they should show filtered records.
- [ ] **Opportunities table:** If automations are ON, check for auto-created opportunity records from hard money triggers.
- [ ] **Ownership Entities:** Property Count and Total Entity Value should show numbers.

---

## PHASE 5: INTERFACES (After test validates)

Build 4 dashboards in Airtable Interface Designer. Full specs in `DSCR_Airtable_Build_Guide.md`, Step 7.

1. **🎯 Daily Command Center** — Pipeline value, follow-ups due, top leads
2. **👤 Investor Profile** — Single-investor detail view with portfolio + financing + outreach
3. **📊 Pipeline Manager** — Kanban + deal metrics
4. **🚨 Trigger Alert Center** — All active trigger flags in one place

---

## PHASE 6: FULL IMPORT + HUBSPOT (After everything validates)

1. Prepare full CSV files (7,500 leads)
2. Import in order: Investors → Entities → Properties → Financing
3. Set up HubSpot Free + Zapier sync for Tier 1/2 prospects
4. Begin outreach

---

*Total estimated time for Phases 1-4: ~60-90 minutes on desktop*
