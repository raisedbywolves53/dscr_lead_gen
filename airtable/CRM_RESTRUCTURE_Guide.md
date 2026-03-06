# CRM Restructure Guide — 7 Manual Changes

Everything else was already done via API. These 7 things require you because Airtable's API does not allow editing formulas, automations, or views.

---

## CHANGE 1 of 7: Hard Money Score Formula

**WHERE TO GO:**
1. Open your Airtable base "DSCR Investor Intelligence"
2. Click the **Investors** tab at the top of the screen
3. Scroll RIGHT through the columns until you see a column called **Hard Money Score**
4. Click directly on the column header text **Hard Money Score** — a dropdown menu appears
5. Click **Edit field** in that dropdown
6. You will see a formula editor box with the current formula inside it

**WHAT TO DO:**
7. Click inside the formula editor box
8. Select ALL the existing formula text (Ctrl+A on PC, Cmd+A on Mac)
9. Delete it
10. Paste this exact formula:

```
IF({Hard Money Loan Count} >= 3, 30, IF({Hard Money Loan Count} >= 2, 25, IF({Hard Money Loan Count} >= 1, 15, 0)))
```

11. Click the blue **Save** button

**WHAT THIS DOES:** Changes Hard Money scoring from a 0–10 scale to a 0–30 scale. Hard money investors are your hottest leads — they're paying 10-15% and need to refinance.

---

## CHANGE 2 of 7: Recent Purchase Score Formula

**WHERE TO GO:**
1. Stay on the **Investors** tab
2. Scroll RIGHT to find the column called **Recent Purchase Score**
3. Click the column header text **Recent Purchase Score**
4. Click **Edit field**

**WHAT TO DO:**
5. Click inside the formula editor box
6. Select ALL (Ctrl+A / Cmd+A)
7. Delete it
8. Paste this exact formula:

```
IF({Recent Purchase Count} >= 3, 15, IF({Recent Purchase Count} >= 2, 10, IF({Recent Purchase Count} >= 1, 5, 0)))
```

9. Click **Save**

**WHAT THIS DOES:** Changes from 0–20 scale to 0–15 scale. Active buyers matter but less urgently than hard money borrowers.

---

## CHANGE 3 of 7: Portfolio Size Score Formula

**WHERE TO GO:**
1. Stay on the **Investors** tab
2. Scroll RIGHT to find the column called **Portfolio Size Score**
3. Click the column header text **Portfolio Size Score**
4. Click **Edit field**

**WHAT TO DO:**
5. Click inside the formula editor box
6. Select ALL (Ctrl+A / Cmd+A)
7. Delete it
8. Paste this exact formula:

```
IF({Property Count} >= 20, 15, IF({Property Count} >= 10, 13, IF({Property Count} >= 5, 10, IF({Property Count} >= 3, 7, IF({Property Count} >= 2, 4, IF({Property Count} >= 1, 2, 0))))))
```

9. Click **Save**

**WHAT THIS DOES:** Changes from 0–30 scale to 0–15 scale. Big portfolio is nice but doesn't mean they need you today.

---

## CHANGE 4 of 7: Edit "Create Opportunity for Hard Money Loans"

**WHERE TO GO:**
1. Click **Automations** in the top-right toolbar (between "Interfaces" and "Forms")
2. In the left sidebar, click on **"Create Opportunity for Hard Money Loans"** (first in the list)
3. You should now see the automation editor with the trigger and action visible

**AI PROMPT — paste this into the Airtable AI chat box at the bottom of the screen:**
```
Modify the existing automation called "Create Opportunity for Hard Money Loans". Do not change the trigger — keep it exactly as it is. It currently triggers when a record in the Financing table matches certain conditions. Change ONLY the action. Remove the current action that creates a record in the Opportunities table. Replace it with a new action that updates a record in the Investors table. To find the correct Investor record to update, follow the linked record chain starting from the triggering Financing record: first follow the "Property" linked record field to get to the Properties table, then from that Property record follow the "Owner Investor" linked record field to get to the Investors table. Use that Investor record's Airtable record ID as the record to update. On that Investor record, update two fields: set the checkbox field called "Has Trigger" to true (checked), and set the single select field called "ICP Segment" to the option "Hard Money Refi". Also rename this automation to "Flag Investor — Hard Money Trigger".
```

**If AI fails, do it manually:**
1. Leave the Trigger alone — do not touch it
2. Click the Action box → trash icon or "..." → Delete this action
3. Click **+ Add action** → select **"Update record"**
4. Table: select **Investors**
5. Record ID: click blue **+** → find **Property** → expand → find **Owner Investor** → expand → click **Airtable record ID**
6. Click **+ Choose field** → select **Has Trigger** → set to checked (true)
7. Click **+ Choose field** → select **ICP Segment** → select **Hard Money Refi**
8. Rename the automation: click the name at the top → replace with **Flag Investor — Hard Money Trigger**
9. Click **Test** → toggle **ON**

---

## CHANGE 5 of 7: Edit "Create Opportunity for Maturing Loan"

**WHERE TO GO:**
1. Stay in the **Automations** panel
2. Click on **"Create Opportunity for Maturing Loan"** (second in the list)

**AI PROMPT — paste into AI chat:**
```
Modify the existing automation called "Create Opportunity for Maturing Loan". Do not change the trigger — keep it exactly as it is. It currently triggers when a record in the Financing table matches certain conditions. Change ONLY the action. Remove the current action that creates a record in the Opportunities table. Replace it with a new action that updates a record in the Investors table. To find the correct Investor record to update, follow the linked record chain starting from the triggering Financing record: first follow the "Property" linked record field to get to the Properties table, then from that Property record follow the "Owner Investor" linked record field to get to the Investors table. Use that Investor record's Airtable record ID as the record to update. On that Investor record, update two fields: set the checkbox field called "Has Trigger" to true (checked), and set the single select field called "ICP Segment" to the option "Maturity Refi". Also rename this automation to "Flag Investor — Maturity Trigger".
```

**If AI fails, do it manually:**
1. Leave the Trigger alone
2. Delete the existing Action
3. **+ Add action** → **"Update record"**
4. Table: **Investors**
5. Record ID: click **+** → **Property** → expand → **Owner Investor** → expand → **Airtable record ID**
6. **+ Choose field** → **Has Trigger** → checked (true)
7. **+ Choose field** → **ICP Segment** → **Maturity Refi**
8. Rename to **Flag Investor — Maturity Trigger**
9. **Test** → toggle **ON**

---

## CHANGE 6 of 7: Edit "Create Opportunity for Cash Purchase Properties"

**WHERE TO GO:**
1. Stay in the **Automations** panel
2. Click on **"Create Opportunity for Cash Purchase Properties"** (third in the list)

**AI PROMPT — paste into AI chat:**
```
Modify the existing automation called "Create Opportunity for Cash Purchase Properties". Do not change the trigger — keep it exactly as it is. It currently triggers when a record in the Properties table matches certain conditions. Change ONLY the action. Remove the current action that creates a record in the Opportunities table. Replace it with a new action that updates a record in the Investors table. To find the correct Investor record to update, follow the "Owner Investor" linked record field on the triggering Properties record — this links directly to the Investors table (no need to go through another table). Use that Investor record's Airtable record ID as the record to update. On that Investor record, update two fields: set the checkbox field called "Has Trigger" to true (checked), and set the single select field called "ICP Segment" to the option "Cash Purchase Refi". Also rename this automation to "Flag Investor — Cash Purchase Trigger".
```

**If AI fails, do it manually:**
1. Leave the Trigger alone
2. Delete the existing Action
3. **+ Add action** → **"Update record"**
4. Table: **Investors**
5. Record ID: click **+** → **Owner Investor** → expand → **Airtable record ID** (this one goes direct — Properties links straight to Investors)
6. **+ Choose field** → **Has Trigger** → checked (true)
7. **+ Choose field** → **ICP Segment** → **Cash Purchase Refi**
8. Rename to **Flag Investor — Cash Purchase Trigger**
9. **Test** → toggle **ON**

---

## CHANGE 7 of 7: Hide Optional Fields in Outreach Log

**WHERE TO GO:**
1. Click **Data** in the top-left toolbar to go back to the table grid views
2. Click the **Outreach Log** tab at the top of the screen (it's the last tab on the right)
3. On the left sidebar, make sure you're on the default view — it should say **Grid view** or just be the first view listed

**WHAT TO DO:**
4. In the toolbar above the grid, click **Hide fields** (look for it between "Filter" and "Group" — it may show as an eye icon)
5. A panel opens showing all fields with toggle switches next to each one
6. Find and turn **OFF** each of these 5 fields (click the toggle so it turns gray/off):
   - **Direction**
   - **Call Duration (min)**
   - **Message Sent**
   - **Response Status**
   - **Outcome**
7. Click anywhere outside the panel to close it

**RESULT:** Your default Outreach Log view now shows only: Activity Summary, Investor, Date, Contact Method, Quick Result, Disposition Notes, Follow Up Date, Follow Up Action, Linked Opportunity.

---

## ALSO: Toggle ON All Remaining Automations

**WHERE TO GO:**
1. Click **Automations** in the top-right toolbar

**WHAT TO DO:**
2. Go through each automation in the left sidebar one at a time
3. Click on each one and look at the toggle switch at the top — if it says **OFF**, flip it to **ON**
4. All 8 automations should be **ON** when you're done:
   - Flag Investor — Hard Money Trigger → **ON**
   - Flag Investor — Maturity Trigger → **ON**
   - Flag Investor — Cash Purchase Trigger → **ON**
   - Follow-up Reminder Email → **ON**
   - DNC Scrub Overdue Notification → **ON**
   - Notify Admin of Stale Deals → **ON**
   - Update Investor Last Contact Date on New Outreach Log Entry → **ON**
   - New Investor Compliance Record Creation → **ON**

---

## Checklist

- [ ] Change 1: Hard Money Score formula pasted and saved
- [ ] Change 2: Recent Purchase Score formula pasted and saved
- [ ] Change 3: Portfolio Size Score formula pasted and saved
- [ ] Change 4: "Create Opportunity for Hard Money Loans" renamed + action changed to flag Investor
- [ ] Change 5: "Create Opportunity for Maturing Loan" renamed + action changed to flag Investor
- [ ] Change 6: "Create Opportunity for Cash Purchase Properties" renamed + action changed to flag Investor
- [ ] Change 7: Outreach Log — 6 optional fields hidden
- [ ] All 8 automations toggled ON

**When you're done, tell me and I'll push test data directly into the tables via the Airtable connector to validate everything fires correctly.**
