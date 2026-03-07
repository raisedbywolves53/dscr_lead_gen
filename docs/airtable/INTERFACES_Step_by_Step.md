# Airtable Interfaces — Step-by-Step Guide (v4)

**Base:** DSCR Lead Gen CRM
**Total interfaces:** 4
**Time estimate:** 45–60 minutes

---

## CRITICAL CONCEPT: How Dashboard Interfaces Actually Work

A dashboard is built from **Groups**. Here are the rules:

1. **Each Group = one source table.** All elements inside a group pull from that group's table. You CANNOT mix tables inside one group.
2. **Number elements (Count/Summary cards)** live inside a group. They appear as cards showing counts or totals from that group's table.
3. **Charts and grids** also live inside a group and use that group's table.
4. **To show data from multiple tables, you add MULTIPLE GROUPS** — one per table.

### What a Group Looks Like on Screen
Each group shows up as a section on the dashboard with:
- A **heading** (defaults to the source table name — you can rename it)
- A **description** area (optional)
- **Number cards** across the top (Count or Summary)
- A **chart or grid** below the cards

### The Three Levels
When you click different areas, the right panel changes:

| What you click | Right panel shows | What you can configure |
|---------------|-------------------|----------------------|
| **Empty space outside all groups** | **Page** settings | Title, Allow printing |
| **The group heading** | **Group** settings | Source table, Filter, Width, User filters |
| **A number card or chart** | **Element** settings | Title, Type (Count/Summary), Filter, Color |

---

## How to Do Things (Reference)

### How to Add a New Group
1. Scroll to the **very bottom** of the dashboard canvas
2. **Hover** right at the bottom edge — a small **blue + button** appears
3. Click the **blue +** button
4. A menu appears with element types: Bar chart, Line chart, Pie chart, Donut chart, List, Gallery, Kanban, Calendar, etc.
5. Pick an element type — this creates a new group with that element
6. Click the **group heading** to open Group settings on the right
7. Change **Source** to the table you want

### How to Change a Group's Source Table
1. Click the **group heading text** (e.g., "Opportunities")
2. Right panel shows **Page > Group**
3. Click the **Source** dropdown
4. Pick the table you want: Investors, Outreach Log, Financing, Properties, Compliance, or Opportunities

### How to Rename a Group Heading
1. Click directly on the heading text
2. Delete the old text and type your new heading

### How to Configure a Number Card
1. Click on the number card element
2. Right panel shows these settings:
   - **Title** — the label above the number
   - **Source** — inherited from the group (greyed out)
   - **Filter by** — click the ⚙️ gear to add filter conditions
   - **Type: Count** — counts records matching the filter
   - **Type: Summary** — pick a field and math (Sum, Average, Min, Max)
   - **Color** — pick a color
   - **Click to see underlying records** — toggle ON so you can click the card to see the actual records

### How to Configure a Chart
1. Click on the chart element
2. Right panel shows:
   - **Title** — chart label
   - **Type** — Bar, Line, Pie, etc.
   - **Source** — inherited from group
   - **Filter by** — click ⚙️ for filters
   - **X-axis** — click ⚙️ to pick the grouping field
   - **Y-axis (left)** — click ⚙️ to pick field and aggregation (Count, Sum, etc.)

---

## Interface 1: Daily Command Center

This dashboard uses **3 groups** (one per source table).

### Step 1: Open Your Existing Interface
1. Click **Interfaces** in the top nav bar
2. Click **Daily Command Center** in the left sidebar
3. You should see the existing "Opportunities" group with Active Pipeline Value and Deals in Pipeline

### Step 2: Fix Up the Existing Opportunities Group (Group 1 of 3)

Your existing group already has the Source set to **Opportunities**. Let's configure what's inside it.

**Rename the heading:**
1. Click the "Opportunities" heading text
2. Change it to: `Pipeline Overview`

**Number Card 1 — Already exists: "Active Pipeline Value"**
1. Click the Active Pipeline Value card
2. Confirm these settings in the right panel:

| Setting | Value |
|---------|-------|
| **Title** | `Active Pipeline Value` |
| **Filter by** | Click ⚙️ → **Opportunity Stage** → **is none of** → select `Closed Won`, `Closed Lost`, `On Hold` |
| **Type** | **Summary** |
| **Summary field** | **Weighted Value** → **Sum** |
| **Color** | `Solid green` |
| **Click to see underlying records** | **ON** ✓ |

**Number Card 2 — Already exists: "Deals in Pipeline"**
1. Click the Deals in Pipeline card
2. Confirm/set:

| Setting | Value |
|---------|-------|
| **Title** | `Deals in Pipeline` |
| **Filter by** | Click ⚙️ → **Opportunity Stage** → **is none of** → `Closed Won`, `Closed Lost`, `On Hold` |
| **Type** | **Count** |
| **Color** | `Solid blue` |
| **Click to see underlying records** | **ON** ✓ |

**Chart — Pipeline by Stage**
1. Click the chart element (the empty box below the number cards)
2. Set:

| Setting | Value |
|---------|-------|
| **Title** | `Pipeline by Stage` |
| **Type** | **Bar** |
| **X-axis** | Click ⚙️ → select **Opportunity Stage** |
| **Y-axis (left)** | Click ⚙️ → select **Count** of records |

---

### Step 3: Add a New Group for Outreach Log (Group 2 of 3)

1. Scroll to the **very bottom** of the dashboard
2. **Hover** near the bottom edge until the **blue + button** appears
3. Click the **blue +**
4. From the menu, pick **Bar chart** (we'll change it — this just creates the group)
5. A new group section appears below the first one

**Set the source table:**
1. Click the new group's **heading text** (it may say the default table name)
2. In the right panel under **Data > Source**, click the dropdown
3. Select **Outreach Log**

**Rename the heading:**
1. Click the heading text
2. Change to: `Follow-Ups`

**Configure the Number Card(s):**

If a Number card appeared automatically, click it and set:

| Setting | Value |
|---------|-------|
| **Title** | `Follow-Ups Due Today` |
| **Filter by** | Click ⚙️ → **Follow Up Date** → **is** → **today** |
| **Type** | **Count** |
| **Color** | `Solid orange` |
| **Click to see underlying records** | **ON** ✓ |

**Configure the Chart/Grid:**
1. Click the chart or grid element in this group
2. If it's a chart, you can change it to show a grid instead, or set:

| Setting | Value |
|---------|-------|
| **Title** | `Today's Follow-Ups` |

If you see a way to switch to a **List** or **Grid** view, do so and show: **Investor**, **Follow Up Action**, **Outcome**, **Contact Method**. If not, leave as chart and move on.

---

### Step 4: Add a New Group for Investors (Group 3 of 3)

1. Scroll to the **very bottom** again
2. Hover for the **blue + button** → click it
3. Pick **Bar chart** from the menu
4. A third group appears

**Set the source table:**
1. Click the new group's **heading**
2. In right panel: **Data > Source** → select **Investors**

**Rename the heading:**
1. Change to: `Leads`

**Configure Number Card:**

| Setting | Value |
|---------|-------|
| **Title** | `Tier 1 Uncontacted` |
| **Filter by** | Click ⚙️ → add TWO conditions (make sure they say AND, not OR): |
| | Condition 1: **Lead Tier** → **contains** → type `Tier 1` |
| | Condition 2: **Last Contact Date** → **is empty** |
| **Type** | **Count** |
| **Color** | `Solid red` |
| **Click to see underlying records** | **ON** ✓ |

**Configure the Chart — Lead Score Distribution:**

| Setting | Value |
|---------|-------|
| **Title** | `Lead Score Distribution` |
| **Type** | **Bar** |
| **X-axis** | Click ⚙️ → select **Lead Tier** |
| **Y-axis (left)** | Click ⚙️ → select **Count** of records |

### Step 5: Publish
Click the **Publish** button (top right, orange/red button).

---

## Interface 2: Investor Profile

This one uses a different layout — **List-Detail** (not Dashboard).

### Create It
1. Click **+ New interface** in the left sidebar
2. Pick the **List** or **Record detail** layout (split screen — list on left, detail on right)
3. Set source table to **Investors**
4. Name it: `Investor Profile`

### Left Panel (the scrollable list)
Show: **Full Name**, **Lead Tier**, **Primary Market**
Hide everything else from the list.

### Right Panel (detail of selected investor)
Arrange fields top to bottom:

**Header:** Full Name, Lead Tier, Lead Score (0-100), Relationship Strength

**Contact:** Phone (Mobile), Email (Primary), LinkedIn URL, DNC Status, Consent Status, Preferred Contact Method

**Portfolio:** Property Count, Entity Count, Total Portfolio Value, Total Portfolio Debt, Estimated Portfolio Equity, Investor Type, Primary Market

**Linked Records (expand each):**
- **Properties:** Property Address, Property Type, Estimated Property Value, DSCR Status, Cash Purchase Flag
- **Opportunities:** Deal Name, Opportunity Stage, Estimated Loan Amount, Probability of Close, Expected Close Date
- **Outreach Log:** Date, Contact Method, Outcome, Disposition Notes, Follow Up Date

### Publish when done.

---

## Interface 3: Pipeline Manager

Dashboard layout — **2 groups**.

### Create It
1. Click **+ New interface** → pick **Dashboard**
2. Name it: `Pipeline Manager`

### Group 1: Opportunities (auto-created)

**Rename heading** to: `Deal Pipeline`

**Number Card 1:**

| Setting | Value |
|---------|-------|
| **Title** | `Total Pipeline Value` |
| **Filter by** | **Opportunity Stage** → **is none of** → `Closed Won`, `Closed Lost`, `On Hold` |
| **Type** | **Summary** → field: **Estimated Loan Amount** → **Sum** |
| **Color** | `Solid green` |
| **Click to see underlying records** | **ON** ✓ |

**Number Card 2:**

| Setting | Value |
|---------|-------|
| **Title** | `Weighted Pipeline` |
| **Filter by** | Same as above |
| **Type** | **Summary** → field: **Weighted Value** → **Sum** |
| **Color** | `Solid blue` |
| **Click to see underlying records** | **ON** ✓ |

**Number Card 3** (add if the group allows a 3rd card):

| Setting | Value |
|---------|-------|
| **Title** | `Expected Commission` |
| **Filter by** | Same as above |
| **Type** | **Summary** → field: **Weighted Commission** → **Sum** |
| **Color** | `Solid green` |
| **Click to see underlying records** | **ON** ✓ |

**Chart — Pipeline by Stage:**

| Setting | Value |
|---------|-------|
| **Title** | `Deal Pipeline by Stage` |
| **Type** | **Bar** |
| **X-axis** | **Opportunity Stage** |
| **Y-axis (left)** | **Sum** of **Estimated Loan Amount** |

### Group 2: Deals by Source (also Opportunities, but different view)

If you want a second chart showing deals by source:
1. Add a new group (blue + at bottom) → pick **Pie chart** or **Donut chart**
2. Set Source to **Opportunities**
3. Rename heading to: `Deal Sources`
4. Configure chart:

| Setting | Value |
|---------|-------|
| **Title** | `Deals by Source` |
| **Type** | **Pie** or **Donut** |
| **Segment by / X-axis** | **Opportunity Source** |

### Publish when done.

---

## Interface 4: Trigger Alert Center

Dashboard layout — **2 groups** (Financing + Properties).

### Create It
1. Click **+ New interface** → pick **Dashboard**
2. Name it: `Trigger Alert Center`

### Group 1: Financing Triggers (auto-created)

**Set Source** to **Financing** (click heading → right panel → Source dropdown)
**Rename heading** to: `Financing Triggers`

**Number Card 1:**

| Setting | Value |
|---------|-------|
| **Title** | `Hard Money Loans` |
| **Filter by** | **Hard Money Flag** → **is not empty** |
| **Type** | **Count** |
| **Color** | `Solid red` |
| **Click to see underlying records** | **ON** ✓ |

**Number Card 2:**

| Setting | Value |
|---------|-------|
| **Title** | `Maturing Within 24mo` |
| **Filter by** | **Maturity Window Flag** → **is not empty** |
| **Type** | **Count** |
| **Color** | `Solid orange` |
| **Click to see underlying records** | **ON** ✓ |

**Number Card 3** (if available):

| Setting | Value |
|---------|-------|
| **Title** | `High Rate Loans (>7%)` |
| **Filter by** | **High Rate Flag** → **is not empty** |
| **Type** | **Count** |
| **Color** | `Solid orange` |
| **Click to see underlying records** | **ON** ✓ |

**Chart/Grid — Active Triggers:**

| Setting | Value |
|---------|-------|
| **Title** | `All Active Triggers` |
| **Filter by** | **Trigger Count** → **is greater than** → `0` |

If it's a grid/list, show: **Loan ID**, **Property**, **Current Lender**, **Loan Type**, **Interest Rate**, **Hard Money Flag**, **Maturity Window Flag**, **High Rate Flag**, **Refinance Opportunity Score**

### Group 2: Cash Purchases from Properties

1. Scroll to bottom → hover for **blue + button** → click it
2. Pick **List** or **Bar chart** from the menu
3. Click the new group heading → set **Source** to **Properties**
4. Rename heading to: `Cash Purchase Triggers`

**Number Card:**

| Setting | Value |
|---------|-------|
| **Title** | `Cash Purchases` |
| **Filter by** | **Cash Purchase Flag** → **is not empty** |
| **Type** | **Count** |
| **Color** | `Solid red` |
| **Click to see underlying records** | **ON** ✓ |

**Grid/List:**
If available, show: **Property Address**, **Owner Investor**, **Purchase Price**, **Estimated Property Value**, **Purchase Date**
Sort: **Purchase Date** → **Latest → Earliest**

### Publish when done.

---

## Final Checklist

- [ ] Interface 1: Daily Command Center — 3 groups (Opportunities, Outreach Log, Investors) → Published
- [ ] Interface 2: Investor Profile — List-Detail layout from Investors table → Published
- [ ] Interface 3: Pipeline Manager — 2 groups (both Opportunities) → Published
- [ ] Interface 4: Trigger Alert Center — 2 groups (Financing, Properties) → Published

---

## Color Cheat Sheet

| Color | Used for |
|-------|---------|
| 🟢 **Solid green** | Money totals: Pipeline Value, Commission |
| 🔵 **Solid blue** | Counts and weighted values: Deals in Pipeline, Weighted Pipeline |
| 🟠 **Solid orange** | Warnings: Follow-ups Due, Maturing Loans, High Rate |
| 🔴 **Solid red** | Urgent/hot: Tier 1 Uncontacted, Hard Money, Cash Purchases |

---

## Troubleshooting

**"I don't see the blue + at the bottom"**
→ Scroll all the way down past the last group. Hover your mouse along the bottom edge — the blue + appears on hover, it's not always visible.

**"The Source dropdown is greyed out on an element"**
→ The Source is set at the GROUP level, not the element level. Click the group heading to change the source table.

**"I can only see one Number card but I need more"**
→ Look for a toggle or "add summary" option in the group settings. If you can't add more Number cards to an existing group, that group may only support the ones auto-generated. You can create another group from the same table using the blue + to get more cards.

**"The new group created from blue + doesn't have Number cards"**
→ Some group types auto-generate summary Number cards, others don't. If your new group only shows a chart, the chart itself may have summary fields you can configure. Or try the "List" type from the blue + menu — it typically includes summary cards.

**"I need a grid/table view but my group only has a chart"**
→ Try deleting the group and re-creating it by picking **List** from the blue + menu instead of Bar chart.

**"Numbers all show 0"**
→ Expected! There are no records yet. Once I push test data via API, everything will populate.

---

## Sources
- [Airtable Interface Layout: Dashboard](https://support.airtable.com/docs/interface-layout-dashboard)
- [Interface Designer: Dashboards Guide](https://www.airtable.com/guides/collaborate/interface-designer-dashboards)
- [Moving Groups in Dashboard Interface](https://community.airtable.com/interface-designer-12/moving-groups-in-dashboard-interface-39664)
