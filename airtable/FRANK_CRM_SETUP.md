# Frank's CRM Setup — Step by Step

**What just happened:** We uploaded 25 leads with full data directly on each Investor record. Every number Frank needs (portfolio size, loan rate, hard money flag, opportunity score) is now on the Investor record itself — no broken rollups.

**What you need to do:** Delete 3 broken views, create 3 new views, and optionally build 1 interface. Total time: ~15 minutes.

---

## PART 1: Delete Broken Views (2 minutes)

These views use the old "Lead Tier" formula that reads from broken rollups. They show wrong data. Delete them.

### Delete View 1: "Tier 1 Prospects"

1. Open Airtable → go to the **Investors** table
2. In the view sidebar (left side), find **"Tier 1 Prospects"**
3. Right-click on the view name (or click the `...` three dots next to it)
4. Click **"Delete view"**
5. Confirm deletion

### Delete View 2: "Tier 2 Prospects"

1. Same thing — find **"Tier 2 Prospects"** in the sidebar
2. Right-click → **"Delete view"** → Confirm

### Delete View 3: "New Leads (Uncontacted)"

1. Find **"New Leads (Uncontacted)"** in the sidebar
2. Right-click → **"Delete view"** → Confirm

> **Why:** Every lead has Lead Status = "New" so this view shows everyone. Useless.

---

## PART 2: Create 3 New Views (10 minutes)

### View 1: "Hot Leads — Call Queue"

This is Frank's daily dial list. Shows Tier 1 + Tier 2 leads with the most important fields.

**Step 1 — Create the view:**
1. In the Investors table, click the **"+" button** at the bottom of the view sidebar (or next to the last view tab)
2. Choose **"Grid"**
3. Name it: `Hot Leads — Call Queue`
4. Press Enter

**Step 2 — Set the filter:**
1. Click the **"Filter"** button in the toolbar (funnel icon)
2. Click **"+ Add condition"**
3. Set the first condition:
   - Field: **Priority Tier**
   - Condition: **contains**
   - Value: `Tier 1`
4. Click **"+ Add condition"** again
5. **IMPORTANT:** At the top where it says "And", change it to **"Or"**
6. Set the second condition:
   - Field: **Priority Tier**
   - Condition: **contains**
   - Value: `Tier 2`

**Step 3 — Set the sort:**
1. Click the **"Sort"** button in the toolbar
2. Click **"+ Pick a field to sort by"**
3. Choose **Opportunity Score**
4. Set direction to **"9 → 1"** (descending — highest first)

**Step 4 — Hide fields (show only what Frank needs):**
1. Click the **"Fields"** button in the toolbar (or "Hide fields")
2. Click **"Hide all"** first (this hides everything)
3. Then turn ON (toggle/check) these fields **in this order** (drag to reorder if needed):
   - Full Name
   - Phone (Mobile)
   - Opportunity Score
   - Priority Tier
   - ICP Segment
   - Portfolio Properties
   - Portfolio Value
   - Current Lenders
   - Loan Rate
   - Hard Money
   - Months to Maturity
   - Trigger Summary
   - Estimated Monthly Savings
   - Phone (Secondary)
   - Email (Primary)

> **What Frank sees:** Opens this view, top lead has the highest score. He sees the phone number, the pitch angle (hard money, high rate, maturity), and the estimated savings. Click, dial, pitch.

---

### View 2: "Hard Money Refi"

Focused view for hard money exit campaigns — the hottest refi opportunity.

**Step 1 — Create the view:**
1. Click **"+"** to add a new Grid view
2. Name it: `Hard Money Refi`

**Step 2 — Set the filter:**
1. Click **"Filter"**
2. Add condition:
   - Field: **Hard Money**
   - Condition: **is** (checked)

**Step 3 — Set the sort:**
1. Click **"Sort"**
2. Sort by **Months to Maturity** → direction **"1 → 9"** (ascending — most urgent first)

**Step 4 — Hide fields:**
1. Click **"Fields"** → **"Hide all"**
2. Turn ON these fields:
   - Full Name
   - Phone (Mobile)
   - Opportunity Score
   - Priority Tier
   - Portfolio Properties
   - Portfolio Value
   - Current Lenders
   - Loan Rate
   - Loan Maturity
   - Months to Maturity
   - Equity Pct
   - Trigger Summary
   - Estimated Monthly Savings
   - Phone (Secondary)
   - Email (Primary)

> **What Frank sees:** Every hard money borrower sorted by urgency. The one whose loan matures next month is at the top.

---

### View 3: "Needs Contact Info"

High-value leads that need skip tracing before Frank can reach them.

**Step 1 — Create the view:**
1. Click **"+"** to add a new Grid view
2. Name it: `Needs Contact Info`

**Step 2 — Set the filter:**
1. Click **"Filter"**
2. Add condition:
   - Field: **Phone (Mobile)**
   - Condition: **is empty**
3. **Keep it as "And"** (don't change to "Or")
4. Add second condition:
   - Field: **Email (Primary)**
   - Condition: **is empty**

**Step 3 — Set the sort:**
1. Sort by **Portfolio Value** → **"9 → 1"** (descending — biggest portfolios first)

**Step 4 — Hide fields:**
1. Click **"Fields"** → **"Hide all"**
2. Turn ON these fields:
   - Full Name
   - Opportunity Score
   - Priority Tier
   - Portfolio Properties
   - Portfolio Value
   - Hard Money
   - Current Lenders
   - ICP Segment
   - Mailing Address
   - Mailing City
   - Mailing State
   - Mailing ZIP

> **What this tells you:** These are the leads worth paying for skip tracing. Ali Moledina (40 properties, $6.6M, hard money) is probably at the top — no phone, but worth $20 in Tracerfy credits to find one.

---

## PART 3: Update Existing Views (2 minutes)

### Update "All Investors" view

1. Go to the **"All Investors"** view
2. Click **"Sort"** → add sort by **Opportunity Score** descending ("9 → 1")
3. Click **"Fields"** and make sure **Opportunity Score** and **Priority Tier** are visible (they should already be since they're new fields that default to visible)

### Update "Follow-Up Due" view

1. Go to **"Follow-Up Due"** view
2. It should already be filtered on Next Action Date. If not:
   - Filter: **Next Action Date** → **is on or before** → **today**
   - Sort: **Next Action Date** ascending
3. This view will be empty until Frank starts making calls and logging follow-ups

---

## PART 4: Investor Profile Interface (Optional — 10 minutes)

This gives Frank a clean one-page view of each investor. More visual than the grid.

**Step 1 — Create the interface:**
1. Click **"Interfaces"** in the top-left menu (next to "Data", "Automations", "Forms")
2. Click **"+ New Interface"** (or "Start building")
3. Choose the **"Record detail"** template (if available) or **"Blank"**
4. Name it: `Investor Profile`

**Step 2 — Add the record list (left panel):**
1. If using blank: add a **"Record list"** element on the left side
2. Source: **Investors** table
3. Sort: **Opportunity Score** descending
4. Enable search
5. Show fields: Full Name, Priority Tier, Portfolio Properties

**Step 3 — Add the detail layout (right panel):**

Add elements in this order. For each, click **"+ Add element"** and choose the right type:

**Header section** (use a "Field" element for each):
- Full Name (large text)
- Priority Tier
- Opportunity Score
- Phone (Mobile)
- Email (Primary)
- ICP Segment

**Portfolio section** (add a "Heading" element saying "Portfolio", then fields):
- Portfolio Properties
- Portfolio Value
- Portfolio Equity
- Equity Pct
- Est Monthly Rent
- Purchases Last 12mo
- Purchases Last 36mo
- Avg Purchase Price

**Financing section** (heading "Financing & Triggers"):
- Current Lenders
- Loan Rate
- Loan Type
- Loan Maturity
- Months to Maturity
- Hard Money
- Trigger Summary
- Estimated Monthly Savings

**Linked Properties** (add a "Linked records" element):
- Source: Properties (linked from Investors)
- Show: Property Address, Property Type, Estimated Property Value, Purchase Date

**Linked Financing** (add a "Linked records" element):
- Source: Financing (through Properties)
- Show: Current Lender, Interest Rate, Loan Type, Loan Maturity Date

**Outreach History** (add a "Linked records" element):
- Source: Outreach Log (linked from Investors)
- Show: Date, Contact Method, Outcome, Disposition Notes, Follow Up Date

**Background** (heading "Entity & Background"):
- Portfolio Snapshot
- Entity Name (from linked Ownership Entities)

> **Tip:** If the interface builder feels overwhelming, skip it for now. The "Hot Leads — Call Queue" grid view gives Frank everything he needs. The interface is a nice-to-have.

---

## PART 5: Quick Sanity Check

After setting up views, verify these things:

1. **"Hot Leads — Call Queue"** should show 13 leads (5 Tier 1 + 8 Tier 2)
2. **Top lead** should be **Veronica Mcdougall** (Score 85, has phone, hard money)
3. **"Hard Money Refi"** should show 7 leads, with the one maturing soonest at top
4. **Berrin Demiray** should show: 26 properties, $4.4M value, 12% rate, Hard Money checked, Maturity 2 months
5. **"Needs Contact Info"** should show leads like Ali Moledina (40 properties, no phone)

---

## What's Next After This

1. **Frank starts dialing** from the "Hot Leads — Call Queue" view
2. **Skip trace the "Needs Contact Info" list** — run through Tracerfy when you have the API key ($0.02/lead, ~$5 for the top 250)
3. **Upload more leads** — run `python airtable/upload_full_crm.py --count 100` or `--count 500` when ready
4. **DNC scrub** — when Frank sends Blacklist Alliance credentials, we'll add DNC checking before the next upload
5. **Refresh before each dial session** — run `python airtable/refresh_call_queue.py` to update Call Priority based on any new outreach logged
