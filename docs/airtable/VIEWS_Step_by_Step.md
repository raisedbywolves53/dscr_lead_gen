# Airtable Views — Click-by-Click Instructions

**Base:** DSCR Investor Intelligence
**What you're building:** 24 filtered/sorted views across 6 tables

---

## HOW THE AIRTABLE UI WORKS (read this first)

Your toolbar looks like this across the top right:

```
Hide fields | Filter | Group | Sort | Color | Share and sync
```

**These three buttons are what you'll use for every view:**

### FILTER (the funnel icon)
1. Click **Filter** in the toolbar
2. You'll see an AI text box at top ("Describe what you want to see") — **ignore this**
3. Click the blue **+ Add condition** link below
4. A row appears: **Where** [ Field ▼ ] [ Operator ▼ ] [ Value ]
5. Click the **Field dropdown** to pick which column to filter by
6. Click the **Operator dropdown** to pick how to match it
7. Type or select the **value**
8. To add more conditions: click **+ Add condition** again — a second row appears with **and** between them

**The operators change depending on the field type:**

| Field type | Operators you'll see |
|---|---|
| Text fields (Single Line) | contains, does not contain, is, is not, is empty, is not empty |
| Single Select (dropdown) | is, is not, is any of, is none of, is empty, is not empty |
| Number / Formula fields | =, ≠, <, >, ≤, ≥, is empty, is not empty |
| Date fields | is, is before, is after, is within, is empty, is not empty |
| Checkbox | is checked, is not checked |

### SORT (the up/down arrows icon)
1. Click **Sort** in the toolbar
2. A search box appears with all your fields listed below it
3. **Type the field name** in the search box to find it fast (e.g., type "Lead Score")
4. **Click the field name** — it gets added as a sort
5. You'll now see: [ Field Name ▼ ] [ direction ▼ ]
6. The **direction dropdown** label depends on the field type:
   - For numbers: **1 → 9** (lowest first) or **9 → 1** (highest first)
   - For text/formulas: **A → Z** (lowest first) or **Z → A** (highest first)
   - For dates: **Earliest → Latest** or **Latest → Earliest**
7. **Click the direction dropdown** and pick the one you want
8. **Simple rule:** "ascending" or "lowest/soonest first" = 1→9 or A→Z or Earliest→Latest. "Descending" or "highest/most recent first" = the reverse.
8. Leave "Automatically sort records" toggled ON (green)

### GROUP (the stacked layers icon)
1. Click **Group** in the toolbar
2. You'll see a short list of suggested fields + "See all fields" at the bottom
3. If your field is in the list, click it. If not, click **See all fields** and find it
4. Once selected, you can pick ascending or descending order for the groups

### CREATING A NEW VIEW
1. Look at the **left sidebar** — you'll see your existing views listed there
2. At the very top of the sidebar, click **+ Create new...**
3. A menu pops up with view types: **Grid**, **Calendar**, **Gallery**, **Kanban**, **Timeline**, **List**, **Gantt**, **Form**
4. Click **Grid** (unless instructions say otherwise)
5. Type the view name and press **Enter**
6. You're now in your new empty view — add filters, sorts, and groups

---

## IMPORTANT TIPS

- **Filters save automatically** — as soon as you set a filter, it's applied to that view
- **Sorts save automatically** — same thing
- **Each view is independent** — filters on one view don't affect other views
- **You can't break anything** — if a view looks wrong, just delete it (right-click the view name in the sidebar → Delete) and start over
- **"is not empty" means the field has any value at all** — this is how we check for trigger flags (if the formula puts text in the field, "is not empty" catches it)

---

## TABLE 1: INVESTORS — 6 views

### View 1: 🔥 Tier 1 Prospects

**Create the view:**
1. Click the **Investors** tab at the top
2. In the left sidebar, click **+ Create new...**
3. Click **Grid**
4. Type: `🔥 Tier 1 Prospects` → press Enter

**Add filter:**
1. Click **Filter** in the toolbar
2. Click **+ Add condition**
3. Click the first dropdown (says "Full Name") → scroll down or type `Lead Tier` → click **Lead Tier**
4. The operator should show **is** (since Lead Tier is a Single Select)
5. Click the operator dropdown → select **is...**
6. In the value area, click and select **Tier 1** from the dropdown that appears

**Add sort:**
1. Click **Sort** in the toolbar
2. Type `Lead Score` in the search box
3. Click **Lead Score (0-100)** when it appears
4. Click the direction dropdown (shows **1 → 9**) → change to **9 → 1** (highest scores first)

**Add group:**
1. Click **Group** in the toolbar
2. Click **Primary Market** (should be in the short list) — if not, click "See all fields" and find it

**Done!** Move to the next view.

---

### View 2: ⭐ Tier 2 Prospects

**Create the view:**
1. Left sidebar → **+ Create new...** → **Grid**
2. Name: `⭐ Tier 2 Prospects`

**Add filter:**
1. Click **Filter** → **+ Add condition**
2. Change field to **Lead Tier** → operator **is...** → value **Tier 2**

**Add sort:**
1. Click **Sort** → type `Lead Score` → click **Lead Score (0-100)** → direction **9 → 1**

---

### View 3: 📞 Follow-Up Due

**Create the view:**
1. Left sidebar → **+ Create new...** → **Grid**
2. Name: `📞 Follow-Up Due`

**Add filter (3 conditions):**
1. Click **Filter** → **+ Add condition**
2. First condition: field **Days Since Last Contact** → operator **>** → value `30`
3. Click **+ Add condition** (a second row appears with "and" between them)
4. Second condition: field **Relationship Strength** → operator **is not...** → value `Cold`
5. Click **+ Add condition** again
6. Third condition: field **DNC Status** → operator **is...** → value `Clear`

**Add sort:**
1. Click **Sort** → search `Days Since Last` → click **Days Since Last Contact** → direction **9 → 1**

---

### View 4: 🚫 DNC / Do Not Contact

**Create the view:**
1. Left sidebar → **+ Create new...** → **Grid**
2. Name: `🚫 DNC / Do Not Contact`

**Add filter:**
1. Click **Filter** → **+ Add condition**
2. Field: **DNC Status** → operator: **is any of...** → click to check: `Federal DNC`, `State DNC`, `Internal DNC`, `Litigator`

> **Note:** "is any of" lets you select multiple values from the dropdown. Check each one you want.

---

### View 5: 🆕 New Leads (Uncontacted)

**Create the view:**
1. Left sidebar → **+ Create new...** → **Grid**
2. Name: `🆕 New Leads (Uncontacted)`

**Add filter (2 conditions):**
1. Click **Filter** → **+ Add condition**
2. First condition: field **Last Contact Date** → operator **is empty**
   (no value needed — "is empty" means the field is blank)
3. Click **+ Add condition**
4. Second condition: field **DNC Status** → operator **is...** → value `Clear`

**Add sort:**
1. Click **Sort** → search `Lead Score` → click **Lead Score (0-100)** → direction **9 → 1**

---

### View 6: Gallery — Investor Cards

**Create the view (Gallery, not Grid!):**
1. Left sidebar → **+ Create new...** → **Gallery** (NOT Grid)
2. Name: `Gallery — Investor Cards`

**Configure visible fields:**
1. In Gallery view, the toolbar shows a **Fields** button (NOT "Hide fields") — click **Fields**
2. Click **Hide all** at the bottom to hide everything
3. Now turn ON (click the toggle to green) only these fields:
   - Full Name
   - Lead Tier
   - Lead Score (0-100)
   - Property Count
   - Total Portfolio Value
   - Primary Market
   - Phone (Mobile)
   - Last Contact Date
4. All other fields stay hidden

---

## TABLE 2: PROPERTIES — 3 views

> **First:** Click the **Properties** tab at the top of the screen

### View 7: 💰 Cash Purchase Opportunities

**Create the view:**
1. Left sidebar → **+ Create new...** → **Grid**
2. Name: `💰 Cash Purchase Opportunities`

**Add filter:**
1. Click **Filter** → **+ Add condition**
2. Field: **Cash Purchase Flag** → operator: **is not empty**

> **Why "is not empty"?** This is a formula field. When the formula detects a cash purchase, it puts text in the field (like "Cash Purchase"). When it doesn't, the field is blank. "is not empty" catches all records where the formula fired.

**Add sort:**
1. Click **Sort** → search `Estimated Property Value` → click it → direction **9 → 1**

---

### View 8: 🏠 All Properties by Investor

**Create the view:**
1. Left sidebar → **+ Create new...** → **Grid**
2. Name: `🏠 All Properties by Investor`

**Add group:**
1. Click **Group** → click "See all fields" if needed → find and click **Owner Investor**

**Add sort:**
1. Click **Sort** → search `Estimated Property Value` → click it → direction **9 → 1**

> **No filter needed** — this view shows all properties, just organized by who owns them.

---

### View 9: ⚠️ Low DSCR Properties

**Create the view:**
1. Left sidebar → **+ Create new...** → **Grid**
2. Name: `⚠️ Low DSCR Properties`

**Add filter (2 conditions with OR):**
1. Click **Filter** → **+ Add condition**
2. First condition: field **DSCR Status** → operator **contains...** → value `Below 1.0`
3. Click **+ Add condition**
4. **IMPORTANT:** By default, conditions are joined with "and". You need to change it to "or":
   - Look at the word **and** between the two conditions
   - Click on the word **and** — it should toggle to **or** (or show a dropdown letting you pick)
5. Second condition: field **DSCR Status** → operator **contains...** → value `Marginal`

**Add sort:**
1. Click **Sort** → search `Estimated DSCR` → click it → direction **A → Z** (lowest DSCR first)

---

## TABLE 3: FINANCING — 6 views

> **First:** Click the **Financing** tab at the top

### View 10: 🚨 Maturity Window (12-24 mo)

**Create the view:**
1. Left sidebar → **+ Create new...** → **Grid**
2. Name: `🚨 Maturity Window (12-24 mo)`

**Add filter:**
1. Click **Filter** → **+ Add condition**
2. Field: **Maturity Window Flag** → operator: **is not empty**

**Add sort:**
1. Click **Sort** → search `Months to Maturity` → click it → direction **A → Z** (soonest maturity first)

---

### View 11: 🚨 High Rate Loans (>7%)

**Create the view:**
1. Left sidebar → **+ Create new...** → **Grid**
2. Name: `🚨 High Rate Loans (>7%)`

**Add filter:**
1. Click **Filter** → **+ Add condition**
2. Field: **High Rate Flag** → operator: **is not empty**

**Add sort:**
1. Click **Sort** → search `Interest Rate` → click it → direction **9 → 1** (highest rates first)

---

### View 12: 🚨 Hard Money / Bridge / Private

**Create the view:**
1. Left sidebar → **+ Create new...** → **Grid**
2. Name: `🚨 Hard Money / Bridge / Private`

**Add filter:**
1. Click **Filter** → **+ Add condition**
2. Field: **Hard Money Flag** → operator: **is not empty**

**Add sort:**
1. Click **Sort** → search `Estimated Loan Balance` → click it → direction **9 → 1**

---

### View 13: 🚨 Balloon Risk

**Create the view:**
1. Left sidebar → **+ Create new...** → **Grid**
2. Name: `🚨 Balloon Risk`

**Add filter:**
1. Click **Filter** → **+ Add condition**
2. Field: **Balloon Risk Flag** → operator: **is not empty**

**Add sort:**
1. Click **Sort** → search `Balloon Date` → click it → direction **Earliest → Latest** (soonest balloon first)

---

### View 14: ⏳ Prepay Penalty Active

**Create the view:**
1. Left sidebar → **+ Create new...** → **Grid**
2. Name: `⏳ Prepay Penalty Active`

**Add filter:**
1. Click **Filter** → **+ Add condition**
2. Field: **Prepay Penalty Clear** → operator: **contains...** → value `Active`

**Add sort:**
1. Click **Sort** → search `Prepayment Penalty End Date` → click it → direction **Earliest → Latest**

---

### View 15: 🏆 Highest Refi Score

**Create the view:**
1. Left sidebar → **+ Create new...** → **Grid**
2. Name: `🏆 Highest Refi Score`

**Add filter:**
1. Click **Filter** → **+ Add condition**
2. Field: **Refinance Opportunity Score** → operator: **>** → value `0`

**Add sort:**
1. Click **Sort** → search `Refinance Opportunity Score` → click it → direction **9 → 1**

---

## TABLE 4: OPPORTUNITIES — 4 views

> **First:** Click the **Opportunities** tab at the top

### View 16: 📊 Pipeline — Kanban

**Create the view (Kanban, not Grid!):**
1. Left sidebar → **+ Create new...** → **Kanban**
2. Name: `📊 Pipeline — Kanban`
3. It will ask you to pick a field to "stack by" — select **Opportunity Stage**
4. You should see columns for each stage (Prospect Identified, Initial Outreach, etc.)

**Configure card fields:**
1. Click the **Fields** button (or "Customize cards") that appears in the toolbar
2. **Deal Name is the primary field** — it shows on every card automatically and can't be toggled off. That's normal.
3. Show these additional fields: Investor, Estimated Loan Amount, Probability of Close, Expected Close Date
4. Hide everything else

---

### View 17: 💲 Active Pipeline (by Value)

**Create the view:**
1. Left sidebar → **+ Create new...** → **Grid**
2. Name: `💲 Active Pipeline (by Value)`

**Add filter:**
1. Click **Filter** → **+ Add condition**
2. Field: **Opportunity Stage** → operator: **is none of...** → check: `Closed Won`, `Closed Lost`, `On Hold`

> **"is none of"** means "show me everything EXCEPT these values" — so you'll see all active deals

**Add sort:**
1. Click **Sort** → search `Weighted Value` → click it → direction **9 → 1**

---

### View 18: 📅 Closing This Month

**Create the view:**
1. Left sidebar → **+ Create new...** → **Grid**
2. Name: `📅 Closing This Month`

**Add filter (2 conditions):**
1. Click **Filter** → **+ Add condition**
2. First condition: field **Expected Close Date** → operator **is within...** → value: select **the next 30 days** or **the next number of days** and type `30`
3. Click **+ Add condition**
4. Second condition: field **Opportunity Stage** → operator **is none of...** → check: `Closed Won`, `Closed Lost`

**Add sort:**
1. Click **Sort** → search `Expected Close Date` → click it → direction **Earliest → Latest** (soonest first)

---

### View 19: ⚠️ Stale Deals (>14 days in stage)

**Create the view:**
1. Left sidebar → **+ Create new...** → **Grid**
2. Name: `⚠️ Stale Deals (>14 days in stage)`

**Add filter (2 conditions):**
1. Click **Filter** → **+ Add condition**
2. First condition: field **Days in Stage** → operator **>** → value `14`
3. Click **+ Add condition**
4. Second condition: field **Opportunity Stage** → operator **is none of...** → check: `Closed Won`, `Closed Lost`, `On Hold`

**Add sort:**
1. Click **Sort** → search `Days in Stage` → click it → direction **Z → A** (most stale first)

---

## TABLE 5: OUTREACH LOG — 3 views

> **First:** Click the **Outreach Log** tab at the top

### View 20: 📅 Today's Follow-Ups

**Create the view:**
1. Left sidebar → **+ Create new...** → **Grid**
2. Name: `📅 Today's Follow-Ups`

**Add filter:**
1. Click **Filter** → **+ Add condition**
2. Field: **Follow Up Date** → operator: **is...** → value: select **today** (or type `today` — Airtable recognizes date keywords)

**Add sort:**
1. Click **Sort** → search `Follow Up Date` → click it → direction **Earliest → Latest**

---

### View 21: 📅 This Week's Follow-Ups

**Create the view:**
1. Left sidebar → **+ Create new...** → **Grid**
2. Name: `📅 This Week's Follow-Ups`

**Add filter:**
1. Click **Filter** → **+ Add condition**
2. Field: **Follow Up Date** → operator: **is within...** → value: select **the next 7 days** (or type `7` if it asks for a number of days)

**Add sort:**
1. Click **Sort** → search `Follow Up Date` → click it → direction **Earliest → Latest**

---

### View 22: 📊 Activity by Investor

**Create the view:**
1. Left sidebar → **+ Create new...** → **Grid**
2. Name: `📊 Activity by Investor`

**Add group:**
1. Click **Group** → find and click **Investor**

**Add sort:**
1. Click **Sort** → search `Date` → click **Date** → direction **Latest → Earliest** (most recent first)

> **No filter needed** — this view shows all activities grouped by investor.

---

## TABLE 6: COMPLIANCE — 2 views

> **First:** Click the **Compliance** tab at the top

### View 23: ⛔ Overdue DNC Scrubs

**Create the view:**
1. Left sidebar → **+ Create new...** → **Grid**
2. Name: `⛔ Overdue DNC Scrubs`

**Add filter:**
1. Click **Filter** → **+ Add condition**
2. Field: **Scrub Overdue** → operator: **is not empty**

**Add sort:**
1. Click **Sort** → search `Next Scrub Due` → click it → direction **A → Z** (most overdue first)

---

### View 24: 📋 Consent Records

**Create the view:**
1. Left sidebar → **+ Create new...** → **Grid**
2. Name: `📋 Consent Records`

**Add filter:**
1. Click **Filter** → **+ Add condition**
2. Field: **Record Type** → operator: **is any of...** → check: `Consent Obtained`, `Consent Revoked`

**Add sort:**
1. Click **Sort** → search `Date` → click **Date** → direction **Latest → Earliest** (newest first)

---

## QUICK CHECKLIST

When you finish, you should have these views in your left sidebar:

**Investors (6):**
- [ ] 🔥 Tier 1 Prospects
- [ ] ⭐ Tier 2 Prospects
- [ ] 📞 Follow-Up Due
- [ ] 🚫 DNC / Do Not Contact
- [ ] 🆕 New Leads (Uncontacted)
- [ ] Gallery — Investor Cards

**Properties (3):**
- [ ] 💰 Cash Purchase Opportunities
- [ ] 🏠 All Properties by Investor
- [ ] ⚠️ Low DSCR Properties

**Financing (6):**
- [ ] 🚨 Maturity Window (12-24 mo)
- [ ] 🚨 High Rate Loans (>7%)
- [ ] 🚨 Hard Money / Bridge / Private
- [ ] 🚨 Balloon Risk
- [ ] ⏳ Prepay Penalty Active
- [ ] 🏆 Highest Refi Score

**Opportunities (4):**
- [ ] 📊 Pipeline — Kanban
- [ ] 💲 Active Pipeline (by Value)
- [ ] 📅 Closing This Month
- [ ] ⚠️ Stale Deals (>14 days in stage)

**Outreach Log (3):**
- [ ] 📅 Today's Follow-Ups
- [ ] 📅 This Week's Follow-Ups
- [ ] 📊 Activity by Investor

**Compliance (2):**
- [ ] ⛔ Overdue DNC Scrubs
- [ ] 📋 Consent Records

---

## TROUBLESHOOTING

**"I don't see the field I need in the filter/sort dropdown"**
→ Type the field name in the search box. The list is long (50 fields on Investors) — you need to search.

**"The operator I need isn't showing up"**
→ Different field types show different operators. If you're looking for "is any of" but only see "contains", it means the field is a text/formula field, not a single select. Use "contains" instead.

**"I accidentally added a filter/sort I don't want"**
→ In the filter panel, click the **trash can icon** (🗑) on the right side of the condition row. For sort, click the **X** next to the sort rule.

**"I want to start a view over from scratch"**
→ Right-click the view name in the left sidebar → Delete view. Then create a new one.

**"Filters aren't showing any records"**
→ That's expected right now! The table has 0 records. The filters will work once you upload test data in Phase 4.

**"I see 'and' between conditions but I need 'or'"**
→ Click on the word **and** between the two condition rows. It should toggle to **or**, or show a dropdown to switch.
