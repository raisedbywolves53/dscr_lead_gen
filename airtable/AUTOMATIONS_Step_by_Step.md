# Airtable Automations — Step-by-Step Guide

**Base:** DSCR Lead Gen CRM
**Total automations to build:** 8
**Time estimate:** 30–45 minutes

---

## Before You Start

### Housekeeping: Delete the Test Automation
During setup, a blank automation stub was created. Delete it first:

1. Click **"Automations"** in the top-right toolbar (next to Extensions)
2. You'll see an automation called something like "Automation 1" or "When a record matches conditions"
3. Click the **three-dot menu (⋯)** next to it
4. Click **"Delete automation"**
5. Confirm the deletion

### Two Ways to Build Each Automation

**Option A — AI Prompt (faster):**
1. In the Automations panel, click **"+ Create automation"**
2. Look for the AI text box at the top that says something like "Describe what you want to automate..."
3. Paste the prompt provided below
4. Review what the AI built — check that the trigger table, conditions, and action fields all match
5. Fix anything that looks wrong using the manual instructions

**Option B — Manual (if AI doesn't get it right):**
Follow the manual steps listed under each automation.

### Important Notes
- After building each automation, click the **"Test"** button to verify it works
- **Toggle each automation ON** (the switch at the top-left of the automation) after testing
- Your email for notifications is: **admin@stillmindcreative.com**
- Field names must match EXACTLY — no emoji prefixes (the fields are named "Hard Money Flag" not "🚨 Hard Money Flag")

---

## Automation 1: Auto-Create Opportunity from Hard Money Trigger

**What it does:** When a Financing record has a Hard Money Flag, automatically create an Opportunity so it enters your deal pipeline.

### AI Prompt (copy & paste this)
```
When a record in the Financing table has the field "Hard Money Flag" that is not empty, create a new record in the Opportunities table with these values:
- Deal Name: use the Loan ID from the trigger record followed by " - DSCR Refi"
- Loan Type: "DSCR Refinance (Rate/Term)"
- Opportunity Source: "Hard Money Trigger"
- Opportunity Stage: "Prospect Identified"
- Property: link to the same Property that is linked on the Financing record
- Notes: "Auto-created: Hard money loan detected. Investor may be a candidate for DSCR refinance."
```

### Manual Steps (if AI doesn't nail it)

**Set up the trigger:**
1. Click **"+ Create automation"**
2. Name it: `Auto-Create Opportunity from Hard Money Trigger`
3. Click **"Add Trigger"**
4. Select **"When a record matches conditions"**
5. For **Table**, pick **Financing**
6. Click **"+ Add condition"**
7. Set the condition:
   - Field: **Hard Money Flag**
   - Operator: **is not empty**

**Set up the action:**
1. Click **"+ Add action"**
2. Select **"Create record"**
3. For **Table**, pick **Opportunities**
4. Fill in these fields:
   - **Deal Name** → Click the blue **+** icon to insert a dynamic value → pick **Loan ID** from the trigger → then type ` - DSCR Refi` after it
   - **Loan Type** → Select `DSCR Refinance (Rate/Term)`
   - **Opportunity Source** → Select `Hard Money Trigger`
   - **Opportunity Stage** → Select `Prospect Identified`
   - **Property** → Click the blue **+** icon → pick the **Property** linked record from the trigger
   - **Notes** → Type: `Auto-created: Hard money loan detected. Investor may be a candidate for DSCR refinance.`

**Test & activate:**
1. Click **"Test"** at the top
2. If it passes, toggle the automation **ON**

---

## Automation 2: Auto-Create Opportunity from Maturity Trigger

**What it does:** When a Financing record has a Maturity Window Flag, create an Opportunity for proactive refinance outreach.

### AI Prompt (copy & paste this)
```
When a record in the Financing table has the field "Maturity Window Flag" that is not empty, create a new record in the Opportunities table with these values:
- Deal Name: use the Loan ID from the trigger record followed by " - Maturity Refi"
- Loan Type: "DSCR Refinance (Rate/Term)"
- Opportunity Source: "Maturity Trigger"
- Opportunity Stage: "Prospect Identified"
- Property: link to the same Property that is linked on the Financing record
- Notes: "Auto-created: Loan maturing within 24 months. Proactive refinance outreach recommended."
```

### Manual Steps (if AI doesn't nail it)

**Set up the trigger:**
1. Click **"+ Create automation"**
2. Name it: `Auto-Create Opportunity from Maturity Trigger`
3. Click **"Add Trigger"**
4. Select **"When a record matches conditions"**
5. For **Table**, pick **Financing**
6. Click **"+ Add condition"**
7. Set the condition:
   - Field: **Maturity Window Flag**
   - Operator: **is not empty**

**Set up the action:**
1. Click **"+ Add action"**
2. Select **"Create record"**
3. For **Table**, pick **Opportunities**
4. Fill in these fields:
   - **Deal Name** → Insert dynamic **Loan ID** from trigger → then type ` - Maturity Refi`
   - **Loan Type** → Select `DSCR Refinance (Rate/Term)`
   - **Opportunity Source** → Select `Maturity Trigger`
   - **Opportunity Stage** → Select `Prospect Identified`
   - **Property** → Insert the **Property** linked record from the trigger
   - **Notes** → Type: `Auto-created: Loan maturing within 24 months. Proactive refinance outreach recommended.`

**Test & activate.**

---

## Automation 3: Auto-Create Opportunity from Cash Purchase

**What it does:** When a Property has a Cash Purchase Flag, create an Opportunity for cash-out refi outreach.

### AI Prompt (copy & paste this)
```
When a record in the Properties table has the field "Cash Purchase Flag" that is not empty, create a new record in the Opportunities table with these values:
- Deal Name: use the Property Address from the trigger record followed by " - Cash Out Refi"
- Loan Type: "DSCR Cash-Out Refi"
- Opportunity Source: "Cash Purchase Trigger"
- Opportunity Stage: "Prospect Identified"
- Property: link to the trigger Property record
- Notes: "Auto-created: Cash purchase detected. Investor may want to recoup capital via cash-out DSCR refi."
```

### Manual Steps (if AI doesn't nail it)

**Set up the trigger:**
1. Click **"+ Create automation"**
2. Name it: `Auto-Create Opportunity from Cash Purchase`
3. Click **"Add Trigger"**
4. Select **"When a record matches conditions"**
5. For **Table**, pick **Properties**
6. Click **"+ Add condition"**
7. Set the condition:
   - Field: **Cash Purchase Flag**
   - Operator: **is not empty**

**Set up the action:**
1. Click **"+ Add action"**
2. Select **"Create record"**
3. For **Table**, pick **Opportunities**
4. Fill in these fields:
   - **Deal Name** → Insert dynamic **Property Address** from trigger → then type ` - Cash Out Refi`
   - **Loan Type** → Select `DSCR Cash-Out Refi`
   - **Opportunity Source** → Select `Cash Purchase Trigger`
   - **Opportunity Stage** → Select `Prospect Identified`
   - **Property** → Insert the trigger record's record ID (this links back to the Property)
   - **Notes** → Type: `Auto-created: Cash purchase detected. Investor may want to recoup capital via cash-out DSCR refi.`

**Test & activate.**

---

## Automation 4: Follow-Up Reminder

**What it does:** Sends you an email when a Follow Up Date on an Outreach Log record is today. So you never forget to call someone back.

### AI Prompt (copy & paste this)
```
When a record in the Outreach Log table has the field "Follow Up Date" that is today, send an email to admin@stillmindcreative.com with:
- Subject: "Follow-up due:" followed by the Investor name from the linked Investor field
- Body: Include the Follow Up Action, the Outcome, and the Disposition Notes from the trigger record
```

### Manual Steps (if AI doesn't nail it)

**Set up the trigger:**
1. Click **"+ Create automation"**
2. Name it: `Follow-Up Reminder`
3. Click **"Add Trigger"**
4. Select **"When a record matches conditions"**
5. For **Table**, pick **Outreach Log**
6. Click **"+ Add condition"**
7. Set the condition:
   - Field: **Follow Up Date**
   - Operator: **is** → **today**

**Set up the action:**
1. Click **"+ Add action"**
2. Select **"Send email"**
3. Fill in:
   - **To** → Type: `admin@stillmindcreative.com`
   - **Subject** → Type: `Follow-up due: ` → then click the blue **+** icon → expand the **Investor** linked record → pick the **Full Name** field (or whichever name field is available)
   - **Body** → Type something like:
     ```
     Follow-up action: [insert Follow Up Action]
     Last outcome: [insert Outcome]
     Notes: [insert Disposition Notes]
     ```
     Replace each bracketed part by clicking the blue **+** icon and selecting the corresponding field from the trigger.

**Test & activate.**

---

## Automation 5: DNC Scrub Overdue Alert

**What it does:** Sends you an urgent email when a Compliance record shows "OVERDUE" — meaning you haven't re-scrubbed DNC lists within 31 days. Missing this can mean $500–$1,500 per call in TCPA fines.

### AI Prompt (copy & paste this)
```
When a record in the Compliance table has the field "Scrub Overdue" that contains the text "OVERDUE", send an email to admin@stillmindcreative.com with:
- Subject: "DNC SCRUB OVERDUE"
- Body: "Federal requirement: Re-scrub DNC lists every 31 days. Your last scrub for [Investor name] is overdue. Do not make outbound calls until scrub is current."
Use the linked Investor field to get the investor name.
```

### Manual Steps (if AI doesn't nail it)

**Set up the trigger:**
1. Click **"+ Create automation"**
2. Name it: `DNC Scrub Overdue Alert`
3. Click **"Add Trigger"**
4. Select **"When a record matches conditions"**
5. For **Table**, pick **Compliance**
6. Click **"+ Add condition"**
7. Set the condition:
   - Field: **Scrub Overdue**
   - Operator: **contains**
   - Value: `OVERDUE`

**Set up the action:**
1. Click **"+ Add action"**
2. Select **"Send email"**
3. Fill in:
   - **To** → `admin@stillmindcreative.com`
   - **Subject** → `DNC SCRUB OVERDUE`
   - **Body** → `Federal requirement: Re-scrub DNC lists every 31 days. Your last scrub for ` → insert dynamic **Investor** name → ` is overdue. Do not make outbound calls until scrub is current.`

**Test & activate.**

---

## Automation 6: Stale Deal Alert

**What it does:** Sends you an email when an Opportunity has been sitting in the same stage for more than 14 days (and isn't already closed or on hold). Keeps your pipeline moving.

### AI Prompt (copy & paste this)
```
When a record in the Opportunities table has "Days in Stage" greater than 14, AND "Opportunity Stage" is none of "Closed Won", "Closed Lost", or "On Hold", send an email to admin@stillmindcreative.com with:
- Subject: "Stale deal:" followed by the Deal Name
- Body: "This deal has been in [Opportunity Stage] for [Days in Stage] days. Take action: advance it, update it, or close it."
```

### Manual Steps (if AI doesn't nail it)

**Set up the trigger:**
1. Click **"+ Create automation"**
2. Name it: `Stale Deal Alert`
3. Click **"Add Trigger"**
4. Select **"When a record matches conditions"**
5. For **Table**, pick **Opportunities**
6. Click **"+ Add condition"** and set:
   - Field: **Days in Stage**
   - Operator: **greater than**
   - Value: `14`
7. Click **"+ Add condition"** again (this adds an AND condition):
   - Field: **Opportunity Stage**
   - Operator: **is none of**
   - Values: Select `Closed Won`, `Closed Lost`, `On Hold`

**Set up the action:**
1. Click **"+ Add action"**
2. Select **"Send email"**
3. Fill in:
   - **To** → `admin@stillmindcreative.com`
   - **Subject** → `Stale deal: ` → insert dynamic **Deal Name**
   - **Body** → `This deal has been in "` → insert **Opportunity Stage** → `" for ` → insert **Days in Stage** → ` days. Take action: advance it, update it, or close it.`

**Test & activate.**

---

## Automation 7: Update Investor Last Contact Date

**What it does:** Every time you log an outreach activity, this automatically updates the "Last Contact Date" on the linked Investor. Keeps your Investor records current without you having to remember.

### AI Prompt (copy & paste this)
```
When a new record is created in the Outreach Log table, update the linked Investor record's "Last Contact Date" field to today's date.
```

### Manual Steps (if AI doesn't nail it)

**Set up the trigger:**
1. Click **"+ Create automation"**
2. Name it: `Update Investor Last Contact Date`
3. Click **"Add Trigger"**
4. Select **"When a record is created"**
5. For **Table**, pick **Outreach Log**

**Set up the action:**
1. Click **"+ Add action"**
2. Select **"Update record"**
3. For **Table**, pick **Investors**
4. For **Record ID**: Click the blue **+** icon → select the **Investor** linked record from the trigger → pick the **Record ID** (Airtable should offer this when you expand the linked record)
5. Under **Fields**, find **Last Contact Date** → Set it to **Today** (Airtable should offer a "Today" or current date option; if not, use the dynamic value for the trigger record's created time)

**Test & activate.**

---

## Automation 8: New Lead → Auto-Create Compliance Record

**What it does:** When a new Investor is added, automatically creates a Compliance record reminding you to DNC-scrub them before any outreach. This is your legal safety net.

### AI Prompt (copy & paste this)
```
When a new record is created in the Investors table, create a new record in the Compliance table with these values:
- Investor: link to the new Investor record that triggered this automation
- Record Type: "DNC Scrub"
- Date: today's date
- Result: "Clear - All Lists"
- Notes: "Auto-created reminder: Scrub this number against DNC lists before any outreach."
```

### Manual Steps (if AI doesn't nail it)

**Set up the trigger:**
1. Click **"+ Create automation"**
2. Name it: `New Lead Auto-DNC Check Reminder`
3. Click **"Add Trigger"**
4. Select **"When a record is created"**
5. For **Table**, pick **Investors**

**Set up the action:**
1. Click **"+ Add action"**
2. Select **"Create record"**
3. For **Table**, pick **Compliance**
4. Fill in these fields:
   - **Investor** → Click the blue **+** icon → pick the **Record ID** of the trigger record (this creates the link back to the Investor)
   - **Record Type** → Select `DNC Scrub`
   - **Date** → Set to **Today**
   - **Result** → Select `Clear - All Lists`
   - **Notes** → Type: `Auto-created reminder: Scrub this number against DNC lists before any outreach.`

**Test & activate.**

---

## Checklist — After All 8 Are Built

- [ ] Automation 1: Hard Money → Opportunity (Financing table) — ON
- [ ] Automation 2: Maturity → Opportunity (Financing table) — ON
- [ ] Automation 3: Cash Purchase → Opportunity (Properties table) — ON
- [ ] Automation 4: Follow-Up Reminder email (Outreach Log) — ON
- [ ] Automation 5: DNC Scrub Overdue email (Compliance) — ON
- [ ] Automation 6: Stale Deal email (Opportunities) — ON
- [ ] Automation 7: Update Last Contact Date (Outreach Log → Investors) — ON
- [ ] Automation 8: New Lead → Compliance record (Investors → Compliance) — ON

### Quick Validation
Once all 8 are on, let me know and I'll push test data through the API. That test data is specifically designed to trigger Automations 1, 2, 3, 7, and 8 so we can confirm they fire correctly.

---

## Troubleshooting

**"The AI didn't understand my prompt"**
→ Use the manual steps instead. The AI works best for simple automations; complex conditions sometimes need manual setup.

**"I don't see the field in the dropdown"**
→ Make sure you selected the right **Table** for the trigger. Fields only show up if they belong to that table.

**"Send email action isn't available"**
→ You may need to be on a paid Airtable plan. The Team plan (which you're on) includes this.

**"The automation ran but didn't create the right values"**
→ Click into the automation's run history (the clock icon) to see what values were passed. Compare against the expected values above.

**"How do I insert a dynamic value from the trigger?"**
→ In any text field in the action, click the blue **+** icon (or it may look like a tag icon). This opens a picker showing all fields from your trigger record. Click the field you want to insert.
