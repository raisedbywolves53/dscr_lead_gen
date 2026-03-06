# Airtable Interfaces (Dashboards) — Step-by-Step Guide

**Base:** DSCR Lead Gen CRM
**Total interfaces to build:** 4
**Time estimate:** 30–45 minutes

---

## How to Build Each Interface

Airtable's interface builder has an AI assistant. Here's the workflow:

1. Click **"Interfaces"** in the top-left sidebar (below your table list)
2. Click **"+ New interface"**
3. You'll see layout options — pick the one specified for each interface
4. Once inside the interface editor, you can use AI to help add and configure elements
5. Look for an AI input box or assistant — paste the prompt provided below
6. Review what the AI builds, then adjust anything that's off using the manual notes

### If the AI Can't Build the Whole Thing
Airtable's interface AI may only handle one element at a time. If so, add elements one by one — paste the prompt for each element separately, or use the manual fallback notes to configure it by hand.

### Important Notes
- All number/chart elements need a **source table** and usually a **filter**
- Formula fields (Lead Score, Trigger Count, etc.) sort as **A→Z / Z→A**, not 1→9
- Everything will show 0 or empty until we push test data — that's normal

---

## Interface 1: Daily Command Center

**Layout type:** Dashboard (blank canvas)

### Create the Interface
1. Click **"+ New interface"**
2. Pick **Dashboard** (or "Blank" if that's what it's called)
3. Name it: `Daily Command Center`

### AI Prompts — Paste Each One Separately

**Element 1 — Active Pipeline Value:**
```
Add a number element. Source: Opportunities table. Filter: Opportunity Stage is none of "Closed Won", "Closed Lost", "On Hold". Field: Weighted Value. Aggregation: Sum. Label: "Active Pipeline Value"
```

**Element 2 — Deals in Pipeline:**
```
Add a number element. Source: Opportunities table. Filter: Opportunity Stage is none of "Closed Won", "Closed Lost", "On Hold". Aggregation: Record count. Label: "Deals in Pipeline"
```

**Element 3 — Follow-Ups Due Today:**
```
Add a number element. Source: Outreach Log table. Filter: Follow Up Date is today. Aggregation: Record count. Label: "Follow-Ups Due Today"
```

**Element 4 — Tier 1 Prospects (Uncontacted):**
```
Add a number element. Source: Investors table. Filter: Lead Tier contains "Tier 1" AND Last Contact Date is empty. Aggregation: Record count. Label: "Tier 1 Prospects (Uncontacted)"
```

**Element 5 — Pipeline by Stage chart:**
```
Add a bar chart. Source: Opportunities table. X-axis: Opportunity Stage. Y-axis: Count of records. Label: "Pipeline by Stage"
```

**Element 6 — Lead Score Distribution chart:**
```
Add a bar chart. Source: Investors table. X-axis: Lead Tier. Y-axis: Count of records. Label: "Lead Score Distribution"
```

**Element 7 — Today's Follow-Up List grid:**
```
Add a grid element. Source: Outreach Log table. Filter: Follow Up Date is today. Show these fields only: Investor, Follow Up Action, Outcome, Contact Method. Label: "Today's Follow-Up List"
```

**Element 8 — Top 10 Hottest Leads grid:**
```
Add a grid element. Source: Investors table. Sort by Lead Score (0-100) descending (Z to A). Limit to 10 records. Show these fields only: Full Name, Lead Score (0-100), Lead Tier, Property Count, Total Portfolio Value, Phone (Mobile). Label: "Top 10 Hottest Leads"
```

### Manual Fallback Notes
If the AI doesn't understand an element, add it manually:
- Click **"+ Add element"** → pick the element type (Number, Chart, or Grid)
- Set the **Source** table, add **Filters** using the funnel icon, pick the **Field** and **Aggregation**
- For grids: use the field visibility toggle to show/hide columns

---

## Interface 2: Investor Profile

**Layout type:** List-Detail (split screen — record list on left, full detail on right)

### Create the Interface
1. Click **"+ New interface"**
2. Pick **List-Detail** (might be called "Record Detail" or "Record List")
3. Source table: **Investors**
4. Name it: `Investor Profile`

### AI Prompt for the Whole Interface
```
Create a list-detail interface from the Investors table. The left panel should show a searchable list with Full Name, Lead Tier, and Primary Market. The right detail panel should show the selected investor's full record organized into sections:

Section 1 - Header: Full Name (large), Lead Tier, Lead Score (0-100), Relationship Strength
Section 2 - Contact Info: Phone (Mobile), Email (Primary), LinkedIn URL, DNC Status, Consent Status, Preferred Contact Method
Section 3 - Portfolio Summary: Property Count, Entity Count, Total Portfolio Value, Total Portfolio Debt, Estimated Portfolio Equity, Investor Type, Primary Market
Section 4 - Linked Properties grid showing: Property Address, Property Type, Estimated Property Value, DSCR Status, Cash Purchase Flag
Section 5 - Linked Opportunities grid showing: Deal Name, Opportunity Stage, Estimated Loan Amount, Probability of Close, Expected Close Date
Section 6 - Outreach History grid showing: Date, Contact Method, Outcome, Disposition Notes, Follow Up Date
```

### Manual Fallback Notes
If the AI can't do it all at once:
1. Set the **left panel** list fields to: Full Name, Lead Tier, Primary Market
2. On the **right panel**, drag fields into groups/sections:
   - Header fields at the top
   - Contact fields together
   - Portfolio rollup fields together
3. For linked record grids (Properties, Opportunities, Outreach Log): add a **linked records** element for each and configure which fields to show

---

## Interface 3: Pipeline Manager

**Layout type:** Dashboard

### Create the Interface
1. Click **"+ New interface"**
2. Pick **Dashboard**
3. Name it: `Pipeline Manager`

### AI Prompts — Paste Each One Separately

**Element 1 — Deal Pipeline visual:**
```
Add a bar chart. Source: Opportunities table. X-axis: Opportunity Stage. Y-axis: Sum of Estimated Loan Amount. Label: "Deal Pipeline by Stage"
```

*Note: If Airtable offers a Kanban element in interfaces, use that instead with Opportunity Stage as the stack field and Deal Name, Investor, Estimated Loan Amount as card fields.*

**Element 2 — Total Pipeline Value:**
```
Add a number element. Source: Opportunities table. Filter: Opportunity Stage is none of "Closed Won", "Closed Lost", "On Hold". Field: Estimated Loan Amount. Aggregation: Sum. Label: "Total Pipeline Value"
```

**Element 3 — Weighted Pipeline Value:**
```
Add a number element. Source: Opportunities table. Filter: Opportunity Stage is none of "Closed Won", "Closed Lost", "On Hold". Field: Weighted Value. Aggregation: Sum. Label: "Weighted Pipeline Value"
```

**Element 4 — Expected Commission:**
```
Add a number element. Source: Opportunities table. Filter: Opportunity Stage is none of "Closed Won", "Closed Lost", "On Hold". Field: Weighted Commission. Aggregation: Sum. Label: "Expected Commission"
```

**Element 5 — Deals by Source chart:**
```
Add a pie chart or donut chart. Source: Opportunities table. Segment by: Opportunity Source. Label: "Deals by Source"
```

**Element 6 — Deals Closing This Month grid:**
```
Add a grid element. Source: Opportunities table. Filter: Expected Close Date is within this month. Sort: Expected Close Date earliest to latest. Show these fields only: Deal Name, Investor, Estimated Loan Amount, Opportunity Stage, Probability of Close, Expected Close Date. Label: "Deals Closing This Month"
```

---

## Interface 4: Trigger Alert Center

**Layout type:** Dashboard

### Create the Interface
1. Click **"+ New interface"**
2. Pick **Dashboard**
3. Name it: `Trigger Alert Center`

### AI Prompts — Paste Each One Separately

**Element 1 — Hard Money Loans Found:**
```
Add a number element. Source: Financing table. Filter: Hard Money Flag is not empty. Aggregation: Record count. Label: "Hard Money Loans Found"
```

**Element 2 — Maturing Within 24 Months:**
```
Add a number element. Source: Financing table. Filter: Maturity Window Flag is not empty. Aggregation: Record count. Label: "Maturing Within 24 Months"
```

**Element 3 — High Rate Loans:**
```
Add a number element. Source: Financing table. Filter: High Rate Flag is not empty. Aggregation: Record count. Label: "High Rate Loans (>7%)"
```

**Element 4 — Cash Purchases:**
```
Add a number element. Source: Properties table. Filter: Cash Purchase Flag is not empty. Aggregation: Record count. Label: "Cash Purchases"
```

**Element 5 — All Active Triggers grid:**
```
Add a grid element. Source: Financing table. Filter: Trigger Count is greater than 0. Sort: Trigger Count Z to A, then Refinance Opportunity Score Z to A. Show these fields only: Loan ID, Property, Current Lender, Loan Type, Interest Rate, Maturity Window Flag, Hard Money Flag, High Rate Flag, Balloon Risk Flag, Refinance Opportunity Score. Label: "All Active Triggers"
```

**Element 6 — Cash Purchases Awaiting Outreach grid:**
```
Add a grid element. Source: Properties table. Filter: Cash Purchase Flag is not empty. Sort: Purchase Date latest to earliest. Show these fields only: Property Address, Owner Investor, Purchase Price, Estimated Property Value, Purchase Date. Label: "Cash Purchases Awaiting Outreach"
```

---

## Checklist — After All 4 Are Built

- [ ] Interface 1: Daily Command Center (8 elements)
- [ ] Interface 2: Investor Profile (list-detail layout)
- [ ] Interface 3: Pipeline Manager (6 elements)
- [ ] Interface 4: Trigger Alert Center (6 elements)

Everything will show 0 / empty right now — that's expected. Once I push test data via API, all dashboards will light up and we can validate everything is calculating correctly.

---

## Troubleshooting

**"The AI doesn't understand my prompt"**
→ Try shorter prompts, one element at a time. Or add the element manually: click **"+ Add element"**, pick the type, configure source/filter/fields.

**"I don't see Dashboard as a layout option"**
→ It might be labeled "Blank" or show as a template with an empty canvas preview.

**"I don't see List-Detail"**
→ Look for "Record Detail", "Record List", or a template showing a split-screen preview.

**"Number shows 0"**
→ Normal — no records yet. Will populate after test data upload.

**"Sort shows A→Z instead of 1→9"**
→ Formula fields sort as A→Z. Use **Z→A** to get highest values first.
