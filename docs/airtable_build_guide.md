# DSCR Investor Prospecting CRM — Airtable Build Guide
## Complete Setup Instructions (Step by Step)

**Base Name:** DSCR Investor Intelligence
**Plan Required:** Airtable Team ($20/seat/month) — needed for 7,500+ records
**Estimated Setup Time:** 2–3 hours following this guide

---

## Base Architecture Overview

```
┌─────────────┐     ┌──────────────────┐     ┌──────────────┐     ┌────────────────┐
│  INVESTORS   │────▶│  OWNERSHIP       │────▶│  PROPERTIES  │────▶│  FINANCING     │
│  (People)    │     │  ENTITIES (LLCs) │     │  (Collateral)│     │  (Loans)       │
└──────┬───────┘     └──────────────────┘     └──────┬───────┘     └────────────────┘
       │                                             │
       │         ┌──────────────────┐                │
       ├────────▶│  OPPORTUNITIES   │◀───────────────┘
       │         │  (Deals)         │
       │         └──────────────────┘
       │
       │         ┌──────────────────┐
       ├────────▶│  OUTREACH LOG    │
       │         │  (Activities)    │
       │         └──────────────────┘
       │
       │         ┌──────────────────┐
       └────────▶│  COMPLIANCE      │
                 │  (DNC/Consent)   │
                 └──────────────────┘
```

**7 tables total.** Your POC called for 6 — I'm adding a Compliance table because DNC tracking is non-negotiable for mortgage outreach in Florida.

---

## STEP 1: Create the Base

1. Go to airtable.com → click **+ Create** → **Start from scratch**
2. Name the base: **DSCR Investor Intelligence**
3. Delete the default "Table 1" — we'll build from scratch

---

## TABLE 1: INVESTORS

This is your primary table. Every record is a decision-maker.

**Create the table:** Click **+** next to the tab bar → name it **Investors**

### Fields to Create (in this order):

| # | Field Name | Field Type | Configuration |
|---|-----------|------------|---------------|
| 1 | **Full Name** | Single line text | This is your primary field (first column). Rename the default "Name" field. |
| 2 | **First Name** | Single line text | For mail merge / personalization |
| 3 | **Last Name** | Single line text | For sorting and deduplication |
| 4 | **Phone (Mobile)** | Phone number | Primary phone — mobile prioritized |
| 5 | **Phone (Secondary)** | Phone number | Landline or alternate |
| 6 | **Email (Primary)** | Email | Main email for outreach |
| 7 | **Email (Secondary)** | Email | Alternate email |
| 8 | **LinkedIn URL** | URL | Profile link |
| 9 | **Mailing Address** | Single line text | Full mailing address as one field (easier for import) |
| 10 | **Mailing City** | Single line text | |
| 11 | **Mailing State** | Single line text | |
| 12 | **Mailing ZIP** | Single line text | Use text, not number (preserves leading zeros) |
| 13 | **Estimated Age Range** | Single select | Options: `Under 30` · `30-39` · `40-49` · `50-59` · `60-69` · `70+` · `Unknown` |
| 14 | **Investor Type** | Single select | Options: `Accidental Landlord` · `Lifestyle Investor` · `Growth Investor` · `Professional Investor` · `Operator` · `Capital Allocator` · `Unknown` |
| 15 | **Primary Market** | Single select | Options: `Palm Beach County` · `Broward County` · `Miami-Dade` · `Other FL` · `Out of State` |
| 16 | **Secondary Markets** | Multiple select | Same options as above (allows multiple) |
| 17 | **Years Investing** | Number | Estimated years active (integer) |
| 18 | **Lead Source** | Single select | Options: `FL DOR Records` · `Sunbiz` · `County Clerk` · `PropStream` · `Skip Trace` · `Referral` · `BiggerPockets` · `Meetup` · `LinkedIn` · `Other` |
| 19 | **Preferred Contact Method** | Single select | Options: `Phone` · `Email` · `Text` · `LinkedIn` · `Direct Mail` |
| 20 | **Last Contact Date** | Date | Include time field = No |
| 21 | **Last Conversation Notes** | Long text | Enable rich text formatting |
| 22 | **Relationship Strength** | Single select | Options: `New Lead` · `Cold` · `Warming` · `Warm` · `Hot` · `Active Client` |
| 23 | **DNC Status** | Single select | Options: `Clear` · `Federal DNC` · `State DNC` · `Internal DNC` · `Litigator` · `Not Checked` |
| 24 | **Consent Status** | Single select | Options: `No Consent` · `Verbal Consent` · `Written Consent` · `Revoked` |
| 25 | **Phone Type** | Single select | Options: `Mobile` · `Landline` · `VoIP` · `Unknown` |
| 26 | **Last DNC Scrub Date** | Date | |
| 27 | **Entities** | Link to another record | → Links to **Ownership Entities** table (create this link AFTER building Table 2) |
| 28 | **Properties** | Link to another record | → Links to **Properties** table (create AFTER Table 3) |
| 29 | **Opportunities** | Link to another record | → Links to **Opportunities** table (create AFTER Table 5) |
| 30 | **Outreach Log** | Link to another record | → Links to **Outreach Log** table (create AFTER Table 6) |

### Rollup & Formula Fields (add AFTER all tables are linked):

| # | Field Name | Field Type | Configuration |
|---|-----------|------------|---------------|
| 31 | **Property Count** | Rollup | Table: Properties → Field: Property Address → Aggregation: `COUNTA(values)` |
| 32 | **Total Portfolio Value** | Rollup | Table: Properties → Field: Estimated Property Value → Aggregation: `SUM(values)` |
| 33 | **Total Portfolio Debt** | Rollup | Table: Financing (via Properties) — *see note below* |
| 34 | **Estimated Portfolio Equity** | Formula | `{Total Portfolio Value} - {Total Portfolio Debt}` |
| 35 | **Entity Count** | Rollup | Table: Entities → Field: Entity Name → Aggregation: `COUNTA(values)` |
| 36 | **Days Since Last Contact** | Formula | `IF({Last Contact Date}, DATETIME_DIFF(NOW(), {Last Contact Date}, 'days'), 999)` |
| 37 | **Outreach Count** | Rollup | Table: Outreach Log → Field: Date → Aggregation: `COUNTA(values)` |
| 38 | **Open Opportunities** | Rollup | Table: Opportunities → Field: Opportunity Stage → Aggregation: `COUNTA(values)` |

**Note on Total Portfolio Debt:** Airtable rollups only work one link deep. Since Financing is linked to Properties (not directly to Investors), you have two options:
- **Option A (Simpler):** Add a "Total Debt" rollup on the Properties table (summing linked Financing records), then roll that up to Investors.
- **Option B (Manual):** Keep an estimated debt field on the Investor record updated via automation or manual entry.

I recommend Option A — we'll set it up when we build the Properties table.

### Lead Scoring Formula (add AFTER all rollups are working):

| # | Field Name | Field Type | Formula |
|---|-----------|------------|---------|
| 39 | **Portfolio Size Score** | Formula | See below |
| 40 | **Refi Opportunity Score** | Formula | See below |
| 41 | **Recent Purchase Score** | Formula | See below |
| 42 | **Equity Score** | Formula | See below |
| 43 | **Hard Money Score** | Formula | See below |
| 44 | **Lead Score (0-100)** | Formula | See below |
| 45 | **Lead Tier** | Formula | See below |

These formulas are detailed in the **Lead Scoring section** later in this document.

---

## TABLE 2: OWNERSHIP ENTITIES

Tracks LLCs, corporations, and trusts that hold investment properties.

**Create the table:** Click **+** → name it **Ownership Entities**

### Fields:

| # | Field Name | Field Type | Configuration |
|---|-----------|------------|---------------|
| 1 | **Entity Name** | Single line text | Primary field. Example: "Sunshine Holdings LLC" |
| 2 | **Entity Type** | Single select | Options: `LLC` · `Corporation` · `Trust` · `Limited Partnership` · `General Partnership` · `Individual` |
| 3 | **State of Incorporation** | Single select | Options: `Florida` · `Delaware` · `Wyoming` · `Nevada` · `Texas` · `New York` · `Other` |
| 4 | **Year Formed** | Number | 4-digit year (e.g., 2019) |
| 5 | **Sunbiz Document Number** | Single line text | FL Division of Corps document number |
| 6 | **Status** | Single select | Options: `Active` · `Inactive` · `Dissolved` · `Admin Dissolved` |
| 7 | **Registered Agent** | Single line text | Name of registered agent |
| 8 | **Registered Address** | Single line text | Full address as one field |
| 9 | **Principal Office Address** | Single line text | May differ from registered address |
| 10 | **Entity Email** | Email | From Sunbiz annual report (public record) |
| 11 | **Entity Phone** | Phone number | If available |
| 12 | **EIN** | Single line text | Federal Employer ID Number |
| 13 | **Investor (Owner)** | Link to another record | → Links to **Investors** table |
| 14 | **Properties** | Link to another record | → Links to **Properties** table (create AFTER Table 3) |

### Rollup Fields:

| # | Field Name | Field Type | Configuration |
|---|-----------|------------|---------------|
| 15 | **Property Count** | Rollup | Table: Properties → Field: Property Address → Aggregation: `COUNTA(values)` |
| 16 | **Total Entity Value** | Rollup | Table: Properties → Field: Estimated Property Value → Aggregation: `SUM(values)` |
| 17 | **Total Entity Debt** | Rollup | Table: Properties → Field: Total Property Debt → Aggregation: `SUM(values)` |
| 18 | **Entity Equity** | Formula | `{Total Entity Value} - {Total Entity Debt}` |
| 19 | **Primary Markets** | Rollup | Table: Properties → Field: City → Aggregation: `ARRAYUNIQUE(ARRAYFLATTEN(values))` |

---

## TABLE 3: PROPERTIES

The most important table for DSCR lending — every property is potential collateral.

**Create the table:** Click **+** → name it **Properties**

### Fields:

| # | Field Name | Field Type | Configuration |
|---|-----------|------------|---------------|
| 1 | **Property Address** | Single line text | Primary field. Full street address. |
| 2 | **City** | Single line text | |
| 3 | **State** | Single line text | Default: FL |
| 4 | **ZIP** | Single line text | Text, not number |
| 5 | **County** | Single select | Options: `Palm Beach` · `Broward` · `Miami-Dade` · `Other` |
| 6 | **Property Type** | Single select | Options: `SFR` · `Condo` · `Townhouse` · `Duplex` · `Triplex` · `Fourplex` · `Multi 5-10` · `Multi 11-50` · `Multi 50+` · `STR` · `Mixed Use` · `Commercial` · `Land` |
| 7 | **Beds** | Number | Integer |
| 8 | **Baths** | Number | Allow decimals (e.g., 2.5) |
| 9 | **Sq Ft** | Number | Integer |
| 10 | **Year Built** | Number | 4-digit year |
| 11 | **Estimated Property Value** | Currency | Dollar, precision: 0 |
| 12 | **Purchase Price** | Currency | Dollar, precision: 0 |
| 13 | **Purchase Date** | Date | |
| 14 | **Estimated Monthly Rent** | Currency | Dollar, precision: 0 |
| 15 | **Estimated Annual Rent** | Formula | `{Estimated Monthly Rent} * 12` |
| 16 | **Occupancy Status** | Single select | Options: `Tenant Occupied` · `Owner Occupied` · `Vacant` · `STR Active` · `Unknown` |
| 17 | **Homestead Exempt** | Checkbox | Checked = yes (owner-occupied, NOT an investor property) |
| 18 | **Property Manager** | Single line text | Name of PM company if known |
| 19 | **Listing Status** | Single select | Options: `Not Listed` · `Listed for Rent` · `Listed for Sale` · `Airbnb Active` · `VRBO Active` · `Unknown` |
| 20 | **Owner Entity** | Link to another record | → Links to **Ownership Entities** table |
| 21 | **Owner Investor** | Link to another record | → Links to **Investors** table (direct ownership, no LLC) |
| 22 | **Financing Records** | Link to another record | → Links to **Financing** table (create AFTER Table 4) |
| 23 | **Opportunities** | Link to another record | → Links to **Opportunities** table (create AFTER Table 5) |

### Rollup & Formula Fields:

| # | Field Name | Field Type | Configuration |
|---|-----------|------------|---------------|
| 24 | **Total Property Debt** | Rollup | Table: Financing → Field: Estimated Loan Balance → Aggregation: `SUM(values)` |
| 25 | **Estimated Equity** | Formula | `IF({Estimated Property Value}, {Estimated Property Value} - IF({Total Property Debt}, {Total Property Debt}, 0), "")` |
| 26 | **Estimated LTV** | Formula | `IF(AND({Total Property Debt} > 0, {Estimated Property Value} > 0), ROUND({Total Property Debt} / {Estimated Property Value} * 100, 1), IF(AND({Total Property Debt} = 0, {Estimated Property Value} > 0), 0, ""))` |
| 27 | **Equity Percentage** | Formula | `IF({Estimated Property Value} > 0, ROUND((1 - IF({Total Property Debt}, {Total Property Debt}, 0) / {Estimated Property Value}) * 100, 1), "")` |
| 28 | **Cash Purchase Flag** | Formula | `IF(AND({Purchase Price} > 0, {Total Property Debt} = 0), "💰 CASH PURCHASE", "")` |
| 29 | **Days Since Purchase** | Formula | `IF({Purchase Date}, DATETIME_DIFF(NOW(), {Purchase Date}, 'days'), "")` |
| 30 | **Months Owned** | Formula | `IF({Purchase Date}, DATETIME_DIFF(NOW(), {Purchase Date}, 'months'), "")` |
| 31 | **Monthly PITIA Estimate** | Rollup | Table: Financing → Field: Monthly Payment Estimate → Aggregation: `SUM(values)` |
| 32 | **Estimated DSCR** | Formula | `IF(AND({Estimated Monthly Rent} > 0, {Monthly PITIA Estimate} > 0), ROUND({Estimated Monthly Rent} / {Monthly PITIA Estimate}, 2), IF(AND({Estimated Monthly Rent} > 0, {Monthly PITIA Estimate} = 0), 99, ""))` |
| 33 | **DSCR Status** | Formula | `IF({Estimated DSCR} = "", "No Data", IF({Estimated DSCR} >= 1.25, "✅ Strong", IF({Estimated DSCR} >= 1.0, "⚠️ Marginal", IF({Estimated DSCR} = 99, "💰 No Debt", "❌ Below 1.0"))))` |

**Note on DSCR = 99:** This is a placeholder for cash-purchased properties with no debt. They show as "No Debt" which means they are prime candidates for cash-out DSCR refinancing.

---

## TABLE 4: FINANCING

Tracks existing loans tied to properties. This is the engine behind your refinance opportunity detection.

**Create the table:** Click **+** → name it **Financing**

### Fields:

| # | Field Name | Field Type | Configuration |
|---|-----------|------------|---------------|
| 1 | **Loan ID** | Single line text | Primary field. Format: `[Property Address] - [Lender]` for easy identification |
| 2 | **Property** | Link to another record | → Links to **Properties** table |
| 3 | **Current Lender** | Single line text | Name of lender / servicer |
| 4 | **Loan Type** | Single select | Options: `Conventional` · `FHA` · `VA` · `DSCR` · `Bank Portfolio` · `Hard Money` · `Private Lender` · `Seller Financing` · `Bridge` · `HELOC` · `Commercial` · `Unknown` |
| 5 | **Loan Purpose** | Single select | Options: `Purchase` · `Rate/Term Refi` · `Cash-Out Refi` · `HELOC` · `Unknown` |
| 6 | **Original Loan Amount** | Currency | Dollar, precision: 0 |
| 7 | **Estimated Loan Balance** | Currency | Dollar, precision: 0 |
| 8 | **Interest Rate** | Percent | Precision: 3 (e.g., 7.250%) |
| 9 | **Rate Type** | Single select | Options: `Fixed` · `ARM 5/1` · `ARM 7/1` · `ARM 10/1` · `Interest Only` · `Unknown` |
| 10 | **Loan Term (Months)** | Number | Integer (e.g., 360 for 30yr, 180 for 15yr) |
| 11 | **Loan Origination Date** | Date | |
| 12 | **Loan Maturity Date** | Date | |
| 13 | **Monthly Payment Estimate** | Currency | Principal + Interest. Dollar, precision: 0 |
| 14 | **Estimated Annual Taxes** | Currency | Property taxes. Dollar, precision: 0 |
| 15 | **Estimated Annual Insurance** | Currency | Hazard insurance. Dollar, precision: 0 |
| 16 | **HOA Monthly** | Currency | If applicable. Dollar, precision: 0 |
| 17 | **Prepayment Penalty** | Checkbox | Checked = has prepay penalty |
| 18 | **Prepayment Penalty End Date** | Date | When the penalty expires |
| 19 | **Balloon Payment** | Checkbox | Checked = loan has balloon |
| 20 | **Balloon Date** | Date | When balloon payment is due |
| 21 | **Mortgage Document Number** | Single line text | County clerk recording number |
| 22 | **Recording Date** | Date | Date recorded with county clerk |
| 23 | **Notes** | Long text | Observations about this loan |

### Formula & Trigger Fields:

| # | Field Name | Field Type | Formula |
|---|-----------|------------|---------|
| 24 | **Monthly PITIA** | Formula | `IF({Monthly Payment Estimate}, {Monthly Payment Estimate} + IF({Estimated Annual Taxes}, {Estimated Annual Taxes}/12, 0) + IF({Estimated Annual Insurance}, {Estimated Annual Insurance}/12, 0) + IF({HOA Monthly}, {HOA Monthly}, 0), "")` |
| 25 | **Estimated LTV** | Formula | `IF(AND({Estimated Loan Balance} > 0, LAST_MODIFIED_TIME({Property})), IF({Estimated Loan Balance} > 0, ROUND({Estimated Loan Balance} / 350000 * 100, 1), ""), "")` — *see note* |
| 26 | **Months to Maturity** | Formula | `IF({Loan Maturity Date}, DATETIME_DIFF({Loan Maturity Date}, NOW(), 'months'), "")` |
| 27 | **Days to Maturity** | Formula | `IF({Loan Maturity Date}, DATETIME_DIFF({Loan Maturity Date}, NOW(), 'days'), "")` |
| 28 | **🚨 Maturity Window Flag** | Formula | `IF(AND({Months to Maturity} != "", {Months to Maturity} > 0, {Months to Maturity} <= 24), "🚨 MATURES WITHIN 24 MO", IF(AND({Months to Maturity} != "", {Months to Maturity} <= 0), "⛔ PAST MATURITY", ""))` |
| 29 | **🚨 High Rate Flag** | Formula | `IF(AND({Interest Rate} != "", {Interest Rate} > 0.08), "🚨 RATE ABOVE 8%", IF(AND({Interest Rate} != "", {Interest Rate} > 0.07), "⚠️ RATE ABOVE 7%", ""))` |
| 30 | **🚨 Hard Money Flag** | Formula | `IF(OR({Loan Type} = "Hard Money", {Loan Type} = "Private Lender", {Loan Type} = "Bridge"), "🚨 HARD MONEY / PRIVATE", "")` |
| 31 | **🚨 Balloon Risk Flag** | Formula | `IF(AND({Balloon Payment}, {Balloon Date}), IF(DATETIME_DIFF({Balloon Date}, NOW(), 'months') <= 0, "⛔ BALLOON PAST DUE", IF(DATETIME_DIFF({Balloon Date}, NOW(), 'months') <= 24, "🚨 BALLOON WITHIN 24 MO", "")), "")` |
| 32 | **Prepay Penalty Clear** | Formula | `IF({Prepayment Penalty}, IF({Prepayment Penalty End Date}, IF(DATETIME_DIFF({Prepayment Penalty End Date}, NOW(), 'days') <= 0, "✅ Penalty Expired", "⏳ Penalty Active until " & DATETIME_FORMAT({Prepayment Penalty End Date}, 'MM/DD/YYYY')), "⏳ Penalty Active (no end date)"), "✅ No Penalty")` |
| 33 | **Refinance Opportunity Score** | Formula | See Lead Scoring section |
| 34 | **Trigger Count** | Formula | `(IF({🚨 Maturity Window Flag} != "", 1, 0)) + (IF({🚨 High Rate Flag} != "", 1, 0)) + (IF({🚨 Hard Money Flag} != "", 1, 0)) + (IF({🚨 Balloon Risk Flag} != "", 1, 0))` |

**Note on Estimated LTV (field 25):** Airtable can't look up a linked record's field value inside a formula. To get the actual property value, use a **Lookup field** instead: Create a Lookup field → Table: Properties → Field: Estimated Property Value. Then use that lookup in the LTV formula:
```
IF(AND({Estimated Loan Balance} > 0, {Property Value (Lookup)} > 0),
  ROUND({Estimated Loan Balance} / {Property Value (Lookup)} * 100, 1),
  "")
```

---

## TABLE 5: OPPORTUNITIES (DEALS)

This is your pipeline — every potential loan deal gets tracked here.

**Create the table:** Click **+** → name it **Opportunities**

### Fields:

| # | Field Name | Field Type | Configuration |
|---|-----------|------------|---------------|
| 1 | **Deal Name** | Single line text | Primary field. Format: `[Investor Last Name] - [Property Address] - [Loan Type]` |
| 2 | **Investor** | Link to another record | → Links to **Investors** table |
| 3 | **Property** | Link to another record | → Links to **Properties** table |
| 4 | **Loan Type** | Single select | Options: `DSCR Purchase` · `DSCR Refinance (Rate/Term)` · `DSCR Cash-Out Refi` · `DSCR Portfolio Loan` · `Bridge to DSCR` · `Other` |
| 5 | **Opportunity Source** | Single select | Options: `Maturity Trigger` · `High Rate Trigger` · `Hard Money Trigger` · `Cash Purchase Trigger` · `Rapid Acquisition Trigger` · `Inbound Inquiry` · `Referral` · `Manual Entry` |
| 6 | **Opportunity Stage** | Single select | Options: `Prospect Identified` · `Contacted` · `Conversation Started` · `Needs Analysis` · `Scenario Quoted` · `Application Submitted` · `In Underwriting` · `Conditional Approval` · `Clear to Close` · `Closed Won` · `Closed Lost` · `On Hold` |
| 7 | **Estimated Loan Amount** | Currency | Dollar, precision: 0 |
| 8 | **Estimated Property Value** | Currency | Dollar, precision: 0 — for the specific deal |
| 9 | **Target LTV** | Percent | Precision: 1 |
| 10 | **Target Rate** | Percent | Precision: 3 |
| 11 | **Target DSCR** | Number | Precision: 2 |
| 12 | **Probability of Close** | Percent | Your confidence level (0–100%) |
| 13 | **Expected Close Date** | Date | |
| 14 | **Weighted Value** | Formula | `IF(AND({Estimated Loan Amount}, {Probability of Close}), ROUND({Estimated Loan Amount} * {Probability of Close}, 0), "")` |
| 15 | **Estimated Commission** | Formula | `IF({Estimated Loan Amount}, ROUND({Estimated Loan Amount} * 0.02, 0), "")` — *adjust 0.02 to your actual commission %* |
| 16 | **Weighted Commission** | Formula | `IF(AND({Estimated Commission}, {Probability of Close}), ROUND({Estimated Commission} * {Probability of Close}, 0), "")` |
| 17 | **Days in Stage** | Formula | `DATETIME_DIFF(NOW(), LAST_MODIFIED_TIME(), 'days')` |
| 18 | **Days Since Created** | Formula | `DATETIME_DIFF(NOW(), CREATED_TIME(), 'days')` |
| 19 | **Lost Reason** | Single select | Options: `Rate Not Competitive` · `Went with Another Lender` · `Decided Not to Refinance` · `DSCR Too Low` · `LTV Too High` · `Documentation Issues` · `Property Issues` · `Unresponsive` · `Other` |
| 20 | **Competitor Lender** | Single line text | Who they went with if lost |
| 21 | **Notes** | Long text | Deal-specific notes and updates |
| 22 | **Date Created** | Created time | Automatic |
| 23 | **Last Modified** | Last modified time | Automatic |

---

## TABLE 6: OUTREACH LOG

Tracks every touchpoint with every investor. Critical for compliance and follow-up discipline.

**Create the table:** Click **+** → name it **Outreach Log**

### Fields:

| # | Field Name | Field Type | Configuration |
|---|-----------|------------|---------------|
| 1 | **Activity Summary** | Single line text | Primary field. Brief description (e.g., "Cold call - left VM") |
| 2 | **Investor** | Link to another record | → Links to **Investors** table |
| 3 | **Contact Method** | Single select | Options: `Phone Call` · `Voicemail` · `Email` · `Text/SMS` · `LinkedIn Message` · `LinkedIn Connection` · `Direct Mail` · `In Person` · `Video Call` |
| 4 | **Direction** | Single select | Options: `Outbound` · `Inbound` |
| 5 | **Date** | Date | Include time = Yes |
| 6 | **Call Duration (min)** | Number | For phone calls |
| 7 | **Message Sent** | Long text | What you said / sent |
| 8 | **Response Status** | Single select | Options: `No Answer` · `Left Voicemail` · `Spoke Live` · `Email Opened` · `Email Replied` · `Text Replied` · `Connected on LinkedIn` · `Bounced` · `Wrong Number` · `Do Not Call` |
| 9 | **Outcome** | Single select | Options: `Positive - Interested` · `Positive - Meeting Set` · `Neutral - More Info Needed` · `Neutral - Call Back Later` · `Negative - Not Interested` · `Negative - Do Not Contact` · `No Response` |
| 10 | **Disposition Notes** | Long text | What happened, what they said |
| 11 | **Follow Up Date** | Date | When to follow up next |
| 12 | **Follow Up Action** | Single line text | What to do on follow-up |
| 13 | **Linked Opportunity** | Link to another record | → Links to **Opportunities** table (if this outreach is deal-specific) |
| 14 | **Date Created** | Created time | Automatic |

---

## TABLE 7: COMPLIANCE

DNC tracking, consent records, and scrub history. Non-negotiable for Florida mortgage outreach.

**Create the table:** Click **+** → name it **Compliance**

### Fields:

| # | Field Name | Field Type | Configuration |
|---|-----------|------------|---------------|
| 1 | **Record ID** | Autonumber | Primary field. Auto-incrementing ID |
| 2 | **Investor** | Link to another record | → Links to **Investors** table |
| 3 | **Record Type** | Single select | Options: `DNC Scrub` · `Consent Obtained` · `Consent Revoked` · `Opt-Out Request` · `Litigator Flag` · `TCPA Complaint` · `Internal DNC Add` |
| 4 | **Date** | Date | Include time = Yes |
| 5 | **DNC List Checked** | Multiple select | Options: `Federal DNC` · `Florida State DNC` · `Internal DNC` · `Known Litigator List` |
| 6 | **Result** | Single select | Options: `Clear - All Lists` · `Hit - Federal DNC` · `Hit - State DNC` · `Hit - Internal DNC` · `Hit - Litigator` · `Hit - Multiple Lists` |
| 7 | **Phone Number Checked** | Phone number | The specific number that was scrubbed |
| 8 | **Consent Type** | Single select | Options: `Prior Express Written Consent (PEWC)` · `Verbal Consent (Recorded)` · `Verbal Consent (Not Recorded)` · `Website Opt-In` · `Business Card` · `Revoked` |
| 9 | **Consent Obtained Via** | Single select | Options: `Phone Call` · `Email` · `Text` · `Website` · `In Person` · `Direct Mail Reply` |
| 10 | **Consent Document URL** | URL | Link to stored consent documentation |
| 11 | **Expiration Date** | Date | Some consent has expiration |
| 12 | **Performed By** | Single line text | Who did the scrub / obtained consent |
| 13 | **Notes** | Long text | Additional details |
| 14 | **Next Scrub Due** | Formula | `IF(AND({Record Type} = "DNC Scrub", {Date}), DATEADD({Date}, 31, 'days'), "")` |
| 15 | **Scrub Overdue** | Formula | `IF(AND({Next Scrub Due} != "", IS_BEFORE({Next Scrub Due}, NOW())), "⛔ OVERDUE - SCRUB NOW", IF(AND({Next Scrub Due} != "", DATETIME_DIFF({Next Scrub Due}, NOW(), 'days') <= 7), "⚠️ Due within 7 days", ""))` |

---

## STEP 2: LINK THE TABLES

After creating all 7 tables, go back and create the linked record fields in this order:

1. **Investors** → Add "Entities" linked field → Ownership Entities
2. **Investors** → Add "Properties" linked field → Properties
3. **Investors** → Add "Opportunities" linked field → Opportunities
4. **Investors** → Add "Outreach Log" linked field → Outreach Log
5. **Investors** → Add "Compliance Records" linked field → Compliance
6. **Ownership Entities** → "Investor (Owner)" should already link to Investors (created above)
7. **Ownership Entities** → Add "Properties" linked field → Properties
8. **Properties** → "Owner Entity" should already link to Ownership Entities
9. **Properties** → "Owner Investor" should already link to Investors
10. **Properties** → Add "Financing Records" linked field → Financing
11. **Properties** → Add "Opportunities" linked field → Opportunities
12. **Financing** → "Property" should already link to Properties
13. **Opportunities** → "Investor" and "Property" should already link
14. **Outreach Log** → "Investor" and "Linked Opportunity" should already link

**Important:** When you create a linked record field on one table, Airtable automatically creates the reverse link on the other table. Don't create duplicates — check if the reverse field already exists before adding a new one.

---

## STEP 3: ADD ROLLUP & LOOKUP FIELDS

Now that tables are linked, add these fields in order:

### On the Properties table:
1. **Total Property Debt** — Rollup: Financing → Estimated Loan Balance → `SUM(values)`
2. **Monthly PITIA Estimate** — Rollup: Financing → Monthly Payment Estimate → `SUM(values)`
3. Now add all the formula fields from Table 3 (Estimated Equity, LTV, DSCR, etc.)

### On the Financing table:
1. **Property Value (Lookup)** — Lookup: Property → Estimated Property Value
2. Now update the Estimated LTV formula to use `{Property Value (Lookup)}` instead of a hardcoded value

### On the Ownership Entities table:
1. **Property Count** — Rollup: Properties → Property Address → `COUNTA(values)`
2. **Total Entity Value** — Rollup: Properties → Estimated Property Value → `SUM(values)`
3. **Total Entity Debt** — Rollup: Properties → Total Property Debt → `SUM(values)`
4. Now add the Entity Equity formula

### On the Investors table:
1. **Property Count** — Rollup: Properties → Property Address → `COUNTA(values)`
2. **Total Portfolio Value** — Rollup: Properties → Estimated Property Value → `SUM(values)`
3. **Total Portfolio Debt** — Rollup: Properties → Total Property Debt → `SUM(values)` *(this is Option A — chaining the rollup through Properties)*
4. **Entity Count** — Rollup: Entities → Entity Name → `COUNTA(values)`
5. **Outreach Count** — Rollup: Outreach Log → Date → `COUNTA(values)`
6. **Open Opportunities** — Count: Rollup: Opportunities → Opportunity Stage → `COUNTA(values)`
7. Now add all formula fields (Estimated Portfolio Equity, Days Since Last Contact)

---

## STEP 4: LEAD SCORING FORMULAS

Add these formula fields to the **Investors** table. These are the 5 scoring components from your POC document plus the composite score and tier.

### Before you begin:

You need these rollup/lookup fields on Investors first:
- `{Property Count}` — rollup (already created above)
- `{Total Portfolio Value}` — rollup (already created above)
- `{Total Portfolio Debt}` — rollup (already created above)
- `{Estimated Portfolio Equity}` — formula (already created above)

You also need these additional rollups on Investors:

| Field Name | Type | Configuration |
|-----------|------|---------------|
| **Hard Money Loan Count** | Rollup | *See note below* |
| **Total Trigger Count** | Rollup | *See note below* |
| **Recent Purchase Count** | Rollup | *See note below* |
| **Cash Purchase Count** | Rollup | *See note below* |

**The rollup depth problem again:** These fields require data from Financing (which links to Properties, not directly to Investors). The workaround:

**On the Properties table, add these intermediate fields:**
1. **Has Hard Money** — Lookup: Financing Records → 🚨 Hard Money Flag → then create a formula: `IF(FIND("HARD MONEY", ARRAYJOIN({Hard Money Lookup}, ",")), 1, 0)`
2. **Trigger Count** — Lookup: Financing Records → Trigger Count → then Rollup: `SUM(values)`
3. **Recent Purchase** — Formula: `IF(AND({Purchase Date}, {Months Owned} <= 24), 1, 0)`
4. **Is Cash Purchase** — Formula: `IF({Cash Purchase Flag} != "", 1, 0)`

**Then on Investors, roll up from Properties:**
1. **Hard Money Loan Count** — Rollup: Properties → Has Hard Money → `SUM(values)`
2. **Total Trigger Count** — Rollup: Properties → Trigger Count → `SUM(values)`
3. **Recent Purchase Count** — Rollup: Properties → Recent Purchase → `SUM(values)`
4. **Cash Purchase Count** — Rollup: Properties → Is Cash Purchase → `SUM(values)`

---

### Lead Scoring Component 1: Portfolio Size Score (0–30 points)

**Field Name:** Portfolio Size Score
**Type:** Formula

```
IF({Property Count} >= 20, 30,
  IF({Property Count} >= 10, 25,
    IF({Property Count} >= 5, 20,
      IF({Property Count} >= 3, 15,
        IF({Property Count} >= 2, 10,
          IF({Property Count} >= 1, 5, 0))))))
```

**Logic:** Larger portfolios = more likely to transact, more properties to refinance, and more sophisticated investor (easier conversation).

---

### Lead Scoring Component 2: Refinance Opportunity Score (0–25 points)

**Field Name:** Refi Opportunity Score
**Type:** Formula

```
IF({Total Trigger Count} >= 4, 25,
  IF({Total Trigger Count} >= 3, 20,
    IF({Total Trigger Count} >= 2, 15,
      IF({Total Trigger Count} >= 1, 10, 0))))
```

**Logic:** More trigger flags = higher urgency to refinance. A property with a maturing hard money loan at 12% is a 3-trigger event (maturity + high rate + hard money).

---

### Lead Scoring Component 3: Recent Purchase Score (0–20 points)

**Field Name:** Recent Purchase Score
**Type:** Formula

```
IF({Recent Purchase Count} >= 3, 20,
  IF({Recent Purchase Count} >= 2, 15,
    IF({Recent Purchase Count} >= 1, 10, 0)))
```

**Logic:** Active acquirers need financing. Someone who bought 3+ properties in the last 24 months is scaling fast and is a prime DSCR candidate.

---

### Lead Scoring Component 4: Equity Score (0–15 points)

**Field Name:** Equity Score
**Type:** Formula

```
IF({Estimated Portfolio Equity} = "" , 0,
  IF({Estimated Portfolio Equity} >= 2000000, 15,
    IF({Estimated Portfolio Equity} >= 1000000, 12,
      IF({Estimated Portfolio Equity} >= 500000, 9,
        IF({Estimated Portfolio Equity} >= 250000, 6,
          IF({Estimated Portfolio Equity} >= 100000, 3, 0))))))
```

**Logic:** More equity = more capacity for cash-out refinancing and more likely to qualify for DSCR loan.

---

### Lead Scoring Component 5: Hard Money Exposure Score (0–10 points)

**Field Name:** Hard Money Score
**Type:** Formula

```
IF({Hard Money Loan Count} >= 3, 10,
  IF({Hard Money Loan Count} >= 2, 8,
    IF({Hard Money Loan Count} >= 1, 5, 0)))
```

**Logic:** Hard money loans are the single strongest DSCR refinance signal. These investors are paying 10–15% rates and need to refinance into a permanent loan. Every hard money borrower should hear from you.

---

### Composite Lead Score (0–100)

**Field Name:** Lead Score (0-100)
**Type:** Formula

```
{Portfolio Size Score} + {Refi Opportunity Score} + {Recent Purchase Score} + {Equity Score} + {Hard Money Score}
```

---

### Lead Tier Assignment

**Field Name:** Lead Tier
**Type:** Formula

```
IF({Lead Score (0-100)} >= 80, "🔥 Tier 1 — Personal Outreach",
  IF({Lead Score (0-100)} >= 60, "⭐ Tier 2 — Semi-Personal",
    IF({Lead Score (0-100)} >= 40, "📋 Tier 3 — Automated Nurture",
      "⬜ Low Priority")))
```

---

### Refinance Opportunity Score (on the Financing table)

Go back to the **Financing** table and add this formula for field #33:

**Field Name:** Refinance Opportunity Score
**Type:** Formula

```
(IF({🚨 Hard Money Flag} != "", 35, 0))
+ (IF({🚨 Maturity Window Flag} != "", 25, 0))
+ (IF({🚨 High Rate Flag} != "", 20, 0))
+ (IF({🚨 Balloon Risk Flag} != "", 15, 0))
+ (IF({Prepay Penalty Clear} = "✅ No Penalty", 5, IF({Prepay Penalty Clear} = "✅ Penalty Expired", 5, 0)))
```

**Max score: 100** (if a loan is hard money, maturing, above market rate, has a balloon, and no prepay penalty).

---

## STEP 5: CREATE VIEWS

Views are saved filter/sort configurations. You'll create these on the relevant tables.

### INVESTORS TABLE — Views:

#### View 1: "🔥 Tier 1 Prospects"
- **Type:** Grid
- **Filter:** Lead Tier contains "Tier 1"
- **Sort:** Lead Score (0-100), descending
- **Hidden Fields:** Hide less critical fields (LinkedIn URL, Mailing Address, etc.)
- **Group By:** Primary Market

#### View 2: "⭐ Tier 2 Prospects"
- **Type:** Grid
- **Filter:** Lead Tier contains "Tier 2"
- **Sort:** Lead Score (0-100), descending

#### View 3: "📞 Follow-Up Due"
- **Type:** Grid
- **Filter:** Days Since Last Contact > 30 AND Relationship Strength is not "Cold" AND DNC Status = "Clear"
- **Sort:** Days Since Last Contact, descending
- **Purpose:** Shows investors you haven't contacted in 30+ days who aren't DNC blocked

#### View 4: "🚫 DNC / Do Not Contact"
- **Type:** Grid
- **Filter:** DNC Status is any of: Federal DNC, State DNC, Internal DNC, Litigator
- **Purpose:** Your compliance safety net — never dial anyone on this list

#### View 5: "🆕 New Leads (Uncontacted)"
- **Type:** Grid
- **Filter:** Last Contact Date is empty AND DNC Status = "Clear"
- **Sort:** Lead Score (0-100), descending
- **Purpose:** Your cold outreach list, sorted by highest-value targets

#### View 6: "Gallery — Investor Cards"
- **Type:** Gallery
- **Cover field:** None
- **Shown fields:** Full Name, Lead Tier, Lead Score, Property Count, Total Portfolio Value, Primary Market, Phone, Last Contact Date
- **Purpose:** Visual card view for quick browsing

---

### PROPERTIES TABLE — Views:

#### View 7: "💰 Cash Purchase Opportunities"
- **Type:** Grid
- **Filter:** Cash Purchase Flag is not empty
- **Sort:** Estimated Property Value, descending
- **Purpose:** Trigger 4 — Properties bought with cash = DSCR cash-out refi candidates

#### View 8: "🏠 All Properties by Investor"
- **Type:** Grid
- **Group By:** Owner Investor
- **Sort:** Estimated Property Value, descending
- **Purpose:** See entire portfolios at a glance

#### View 9: "⚠️ Low DSCR Properties"
- **Type:** Grid
- **Filter:** DSCR Status contains "Below 1.0" OR DSCR Status contains "Marginal"
- **Sort:** Estimated DSCR, ascending
- **Purpose:** Properties with weak DSCR — may need refinancing to improve cash flow

---

### FINANCING TABLE — Views:

#### View 10: "🚨 Maturity Window (12-24 mo)"
- **Type:** Grid
- **Filter:** 🚨 Maturity Window Flag is not empty
- **Sort:** Months to Maturity, ascending
- **Purpose:** Trigger 1 — Loans maturing soon, sorted by most urgent first

#### View 11: "🚨 High Rate Loans (>7%)"
- **Type:** Grid
- **Filter:** 🚨 High Rate Flag is not empty
- **Sort:** Interest Rate, descending
- **Purpose:** Trigger 2 — Highest rates first = most savings potential

#### View 12: "🚨 Hard Money / Bridge / Private"
- **Type:** Grid
- **Filter:** 🚨 Hard Money Flag is not empty
- **Sort:** Estimated Loan Balance, descending
- **Purpose:** Trigger 3 — These are your hottest leads. Every record here is a conversation.

#### View 13: "🚨 Balloon Risk"
- **Type:** Grid
- **Filter:** 🚨 Balloon Risk Flag is not empty
- **Sort:** Balloon Date, ascending
- **Purpose:** Loans with balloon payments coming due — forced refinance events

#### View 14: "⏳ Prepay Penalty Active"
- **Type:** Grid
- **Filter:** Prepay Penalty Clear contains "Active"
- **Sort:** Prepayment Penalty End Date, ascending
- **Purpose:** Track when penalties expire so you can time your outreach

#### View 15: "🏆 Highest Refi Score"
- **Type:** Grid
- **Filter:** Refinance Opportunity Score > 0
- **Sort:** Refinance Opportunity Score, descending
- **Purpose:** Master view of best refinance opportunities across all loans

---

### OPPORTUNITIES TABLE — Views:

#### View 16: "📊 Pipeline — Kanban"
- **Type:** Kanban
- **Stack By:** Opportunity Stage
- **Card Fields:** Deal Name, Investor, Estimated Loan Amount, Probability of Close, Expected Close Date
- **Purpose:** Visual pipeline management — drag deals between stages

#### View 17: "💲 Active Pipeline (by Value)"
- **Type:** Grid
- **Filter:** Opportunity Stage is none of: Closed Won, Closed Lost, On Hold
- **Sort:** Weighted Value, descending
- **Purpose:** See your active pipeline sorted by highest-value deals

#### View 18: "📅 Closing This Month"
- **Type:** Grid
- **Filter:** Expected Close Date is within the next 30 days AND Opportunity Stage is none of: Closed Won, Closed Lost
- **Sort:** Expected Close Date, ascending

#### View 19: "⚠️ Stale Deals (>14 days in stage)"
- **Type:** Grid
- **Filter:** Days in Stage > 14 AND Opportunity Stage is none of: Closed Won, Closed Lost, On Hold
- **Sort:** Days in Stage, descending
- **Purpose:** Deals that haven't moved — need attention or should be killed

---

### OUTREACH LOG — Views:

#### View 20: "📅 Today's Follow-Ups"
- **Type:** Grid
- **Filter:** Follow Up Date is today
- **Sort:** Follow Up Date, ascending
- **Purpose:** Your daily call/action list

#### View 21: "📅 This Week's Follow-Ups"
- **Type:** Grid
- **Filter:** Follow Up Date is within the next 7 days
- **Sort:** Follow Up Date, ascending

#### View 22: "📊 Activity by Investor"
- **Type:** Grid
- **Group By:** Investor
- **Sort:** Date, descending
- **Purpose:** See full outreach history per investor

---

### COMPLIANCE TABLE — Views:

#### View 23: "⛔ Overdue DNC Scrubs"
- **Type:** Grid
- **Filter:** Scrub Overdue is not empty
- **Sort:** Next Scrub Due, ascending
- **Purpose:** CRITICAL — never let DNC scrubs go overdue. Federal requirement: re-scrub every 31 days.

#### View 24: "📋 Consent Records"
- **Type:** Grid
- **Filter:** Record Type is any of: Consent Obtained, Consent Revoked
- **Sort:** Date, descending
- **Purpose:** Audit trail for TCPA compliance

---

## STEP 6: AUTOMATIONS

Airtable automations run on triggers and perform actions. On the Team plan you get 25,000 automation runs per month.

### Automation 1: "Auto-Create Opportunity from Hard Money Trigger"

**Trigger:** When a record matches conditions in **Financing** table
- Condition: 🚨 Hard Money Flag is not empty

**Action:** Create a record in **Opportunities** table
- Deal Name: `{Loan ID} - DSCR Refi`
- Loan Type: `DSCR Refinance (Rate/Term)`
- Opportunity Source: `Hard Money Trigger`
- Opportunity Stage: `Prospect Identified`
- Property: (link to same property)
- Notes: `Auto-created: Hard money loan detected. Investor may be a candidate for DSCR refinance.`

**Why:** Hard money is your best trigger. Auto-create the opportunity so it enters your pipeline immediately.

---

### Automation 2: "Auto-Create Opportunity from Maturity Trigger"

**Trigger:** When a record matches conditions in **Financing** table
- Condition: 🚨 Maturity Window Flag is not empty

**Action:** Create a record in **Opportunities** table
- Opportunity Source: `Maturity Trigger`
- Opportunity Stage: `Prospect Identified`
- Notes: `Auto-created: Loan maturing within 24 months. Proactive refinance outreach recommended.`

---

### Automation 3: "Auto-Create Opportunity from Cash Purchase"

**Trigger:** When a record matches conditions in **Properties** table
- Condition: Cash Purchase Flag is not empty

**Action:** Create a record in **Opportunities** table
- Loan Type: `DSCR Cash-Out Refi`
- Opportunity Source: `Cash Purchase Trigger`
- Opportunity Stage: `Prospect Identified`
- Notes: `Auto-created: Cash purchase detected. Investor may want to recoup capital via cash-out DSCR refi.`

---

### Automation 4: "Follow-Up Reminder"

**Trigger:** When a record matches conditions in **Outreach Log** table
- Condition: Follow Up Date is today

**Action:** Send an email notification (to your email)
- Subject: `📞 Follow-up due: {Investor}`
- Body: `Follow-up action: {Follow Up Action}. Last outcome: {Outcome}. Notes: {Disposition Notes}`

---

### Automation 5: "DNC Scrub Overdue Alert"

**Trigger:** When a record matches conditions in **Compliance** table
- Condition: Scrub Overdue contains "OVERDUE"

**Action:** Send an email notification
- Subject: `⛔ DNC SCRUB OVERDUE`
- Body: `Federal requirement: Re-scrub DNC lists every 31 days. Your last scrub for {Investor} is overdue. Do not make outbound calls until scrub is current.`

**Why:** Missing a DNC scrub can result in $500–$1,500 per call in fines under the TCPA. This automation is your safety net.

---

### Automation 6: "Stale Deal Alert"

**Trigger:** When a record matches conditions in **Opportunities** table
- Condition: Days in Stage > 14 AND Stage is none of: Closed Won, Closed Lost, On Hold

**Action:** Send an email notification
- Subject: `⚠️ Stale deal: {Deal Name}`
- Body: `This deal has been in "{Opportunity Stage}" for {Days in Stage} days. Take action: advance it, update it, or close it.`

---

### Automation 7: "Update Investor Last Contact Date"

**Trigger:** When a record is created in **Outreach Log**

**Action:** Update a record in **Investors** table
- Find: The linked Investor
- Update field: Last Contact Date → Set to today's date

**Why:** Keeps the Investors table current without manual updates.

---

### Automation 8: "New Lead Auto-DNC Check Reminder"

**Trigger:** When a record is created in **Investors** table

**Action:** Create a record in **Compliance** table
- Investor: (link to the new investor)
- Record Type: `DNC Scrub`
- Date: Today
- Result: `Clear - All Lists` (default — update manually after actual scrub)
- Notes: `Auto-created reminder: Scrub this number against DNC lists before any outreach.`

**Why:** Ensures every new lead gets flagged for DNC checking before first contact.

---

## STEP 7: INTERFACES (Dashboards)

Airtable Interfaces let you build visual pages that pull data from your tables. These are what you'll use for daily operations instead of staring at raw spreadsheet views.

### Interface 1: "🎯 Daily Command Center"

**Layout Type:** Dashboard

**Elements to add:**

1. **Number: Active Pipeline Value**
   - Source: Opportunities table, filtered to exclude Closed Won/Lost/On Hold
   - Field: Weighted Value → Aggregation: SUM

2. **Number: Deals in Pipeline**
   - Source: Opportunities table, same filter
   - Aggregation: Record count

3. **Number: Follow-Ups Due Today**
   - Source: Outreach Log table, filter: Follow Up Date = today
   - Aggregation: Record count

4. **Number: Tier 1 Prospects (Uncontacted)**
   - Source: Investors table, filter: Lead Tier contains "Tier 1" AND Last Contact Date is empty
   - Aggregation: Record count

5. **Chart: Pipeline by Stage**
   - Type: Bar chart
   - Source: Opportunities table
   - X-axis: Opportunity Stage
   - Y-axis: Count or SUM of Estimated Loan Amount

6. **Chart: Lead Score Distribution**
   - Type: Histogram or bar chart
   - Source: Investors table
   - X-axis: Lead Tier
   - Y-axis: Count

7. **Grid: Today's Follow-Up List**
   - Source: Outreach Log "📅 Today's Follow-Ups" view
   - Fields: Investor, Follow Up Action, Outcome (last), Contact Method

8. **Grid: Top 10 Hottest Leads**
   - Source: Investors table, sorted by Lead Score descending, limit 10
   - Fields: Full Name, Lead Score, Lead Tier, Property Count, Total Portfolio Value, Phone

---

### Interface 2: "👤 Investor Profile"

**Layout Type:** Record detail (List + Detail)

**Left Panel (List):**
- Source: Investors table
- Search enabled
- Show: Full Name, Lead Tier, Primary Market

**Right Panel (Detail) — shows selected investor:**

1. **Header Section:**
   - Full Name (large)
   - Lead Tier badge
   - Lead Score
   - Relationship Strength

2. **Contact Info Section:**
   - Phone (Mobile), Email, LinkedIn URL
   - DNC Status, Consent Status
   - Preferred Contact Method

3. **Portfolio Summary Section:**
   - Property Count, Entity Count
   - Total Portfolio Value, Total Portfolio Debt, Estimated Portfolio Equity
   - Investor Type, Primary Market

4. **Linked Properties Grid:**
   - Source: Properties linked to this investor
   - Fields: Property Address, Property Type, Estimated Value, DSCR Status, Cash Purchase Flag

5. **Linked Financing Grid:**
   - Source: via Properties → Financing (you may need to flatten this with a lookup)
   - Fields: Loan ID, Lender, Loan Type, Interest Rate, Maturity Window Flag, Hard Money Flag

6. **Linked Opportunities Grid:**
   - Source: Opportunities linked to this investor
   - Fields: Deal Name, Stage, Estimated Loan Amount, Probability, Expected Close Date

7. **Outreach History Grid:**
   - Source: Outreach Log linked to this investor
   - Fields: Date, Contact Method, Outcome, Disposition Notes, Follow Up Date

---

### Interface 3: "📊 Pipeline Manager"

**Layout Type:** Dashboard

1. **Kanban: Deal Pipeline**
   - Source: Opportunities table
   - Stack by: Opportunity Stage
   - Card: Deal Name, Investor, Estimated Loan Amount

2. **Number: Total Pipeline Value**
   - SUM of Estimated Loan Amount (active deals)

3. **Number: Weighted Pipeline Value**
   - SUM of Weighted Value (active deals)

4. **Number: Expected Commission**
   - SUM of Weighted Commission (active deals)

5. **Chart: Deals by Source (Trigger Type)**
   - Type: Pie or donut chart
   - Source: Opportunities
   - Segment by: Opportunity Source

6. **Grid: Deals Closing This Month**
   - Source: "📅 Closing This Month" view

---

### Interface 4: "🚨 Trigger Alert Center"

**Layout Type:** Dashboard

1. **Number: Hard Money Loans Found**
   - Source: Financing, filter: Hard Money Flag not empty
   - Aggregation: Count

2. **Number: Maturing Within 24 Months**
   - Source: Financing, filter: Maturity Window Flag not empty
   - Count

3. **Number: High Rate Loans (>7%)**
   - Source: Financing, filter: High Rate Flag not empty
   - Count

4. **Number: Cash Purchases**
   - Source: Properties, filter: Cash Purchase Flag not empty
   - Count

5. **Grid: All Active Triggers**
   - Source: Financing, filter: Trigger Count > 0
   - Sort: Trigger Count descending, then Refinance Opportunity Score descending
   - Fields: Loan ID, Property, Lender, Loan Type, Interest Rate, Maturity Window Flag, Hard Money Flag, High Rate Flag, Balloon Risk Flag, Refi Opportunity Score

6. **Grid: Cash Purchases Awaiting Outreach**
   - Source: Properties, filter: Cash Purchase Flag not empty
   - Fields: Property Address, Owner Investor, Purchase Price, Estimated Property Value, Purchase Date

---

## STEP 8: CSV IMPORT WORKFLOW

### Preparing Your Data

Your 7,500 leads likely come from PropStream, skip tracing, or FL DOR records. Airtable imports CSV files, but each table needs its own import.

### Import Order (critical — follow this sequence):

**Round 1: Investors**
1. Prepare a CSV with columns matching the Investors table fields (Full Name through Lead Source)
2. In Airtable, go to the Investors table → click **+** in the toolbar → **Import data** → **CSV file**
3. Map each CSV column to the correct Airtable field
4. Review the preview → Import

**Round 2: Ownership Entities**
1. Prepare a CSV with entity data
2. Import into the Ownership Entities table
3. **Linking step:** After import, you'll need to link each entity to its investor. If your CSV includes the investor's name, you can use the "Link records matching values" option — Airtable will match on the linked field's primary value (Full Name)

**Round 3: Properties**
1. Prepare a CSV with property data
2. Import into Properties table
3. Link to Owner Entity and/or Owner Investor using matching values

**Round 4: Financing**
1. Prepare a CSV with loan data (sourced from county clerk records, PropStream mortgage data)
2. Import into Financing table
3. Link to Property using matching values on Property Address

**Round 5: Verify Links**
1. Open the Investors table → spot-check 10–20 records
2. Click into linked fields to verify Properties, Entities, and Financing are properly connected
3. Check that rollup fields are calculating (Property Count, Total Portfolio Value, etc.)

### Import Tips:

- **Dates:** Format as YYYY-MM-DD or MM/DD/YYYY for reliable parsing
- **Currency:** Remove $ signs and commas before import (just numbers)
- **Percentages:** Import as decimals (0.075 for 7.5%) — Airtable will format
- **ZIP codes:** Must be text, not numbers (import as text column to preserve leading zeros)
- **Phone numbers:** Import as text to preserve formatting
- **Deduplication:** Before importing, deduplicate your CSV on a combination of (Full Name + Mailing Address) or (Phone Number) to avoid duplicates

### After Import: Trigger the Scoring

Once all data is linked:
1. Lead Scoring formulas will auto-calculate on the Investors table
2. Trigger flags will auto-populate on the Financing table
3. Check the "🏆 Highest Refi Score" view on Financing — this is your master list of refinance opportunities
4. Check the "🔥 Tier 1 Prospects" view on Investors — these are your top targets
5. Run Automation 1–3 manually the first time (or wait for them to trigger on new records)

---

## STEP 9: HUBSPOT FREE INTEGRATION

Use HubSpot Free ($0) for outreach on your top 300–500 prospects. Connect via Zapier or Make.com.

### What goes in HubSpot vs. Airtable:

| Data | Airtable | HubSpot |
|------|----------|---------|
| All 7,500 investor records | ✅ | ❌ (only top prospects) |
| Properties, Financing, Entities | ✅ | ❌ |
| Lead Scoring & Triggers | ✅ | ❌ |
| Tier 1 & 2 Contacts | ✅ | ✅ (synced from Airtable) |
| Email sequences | ❌ | ✅ |
| Call logging | ✅ (manual) | ✅ (built-in dialer) |
| Deal pipeline | ✅ (full detail) | ✅ (simplified mirror) |
| Meeting scheduling | ❌ | ✅ |

### Zapier Workflow:

**Zap 1: Sync Tier 1/2 Investors to HubSpot**
- Trigger: Airtable → When record matches conditions → Lead Tier contains "Tier 1" or "Tier 2"
- Action: HubSpot → Create/Update Contact
- Map: Full Name, First Name, Last Name, Email, Phone, Lead Tier (as HubSpot property), Lead Score (as HubSpot property)

**Zap 2: Sync Opportunities to HubSpot Deals**
- Trigger: Airtable → When record created in Opportunities
- Action: HubSpot → Create Deal
- Map: Deal Name, Estimated Loan Amount, Opportunity Stage → HubSpot Deal Stage

**Zap 3: Log HubSpot Activities Back to Airtable**
- Trigger: HubSpot → New engagement (call, email, meeting)
- Action: Airtable → Create record in Outreach Log
- Map: Contact → Investor, Engagement type → Contact Method, Timestamp → Date

### HubSpot Free Limitations to Know:
- 5 email templates
- 1 automated email per form (no multi-step sequences)
- No custom objects (everything maps to Contacts + Deals)
- Limited reporting (5 dashboards)
- For real email sequences, consider upgrading to HubSpot Starter ($20/mo) or using a separate tool like Instantly ($30/mo)

---

## MONTHLY COST SUMMARY

| Item | Cost |
|------|------|
| Airtable Team (1 seat) | $20/month |
| HubSpot Free | $0 |
| Zapier Free (100 tasks/mo) or Starter ($19.99/mo) | $0–$20/month |
| **Total** | **$20–$40/month** |

For comparison: GoHighLevel = $97/mo, PropStream + CRM = $149+/mo, Salesforce = $300+/mo.

---

## EXPECTED OUTCOMES

Once your 7,500 leads are imported and scored:

| Metric | Expected Range |
|--------|---------------|
| Tier 1 Prospects (score 80–100) | 150–300 investors |
| Tier 2 Prospects (score 60–79) | 300–500 investors |
| Hard Money Loan Flags | 50–200 loans |
| Maturity Window Triggers | 100–500 loans |
| Cash Purchase Flags | 200–800 properties |
| Active Pipeline (after 90 days outreach) | 50–100 conversations |
| Loan Opportunities (after 90 days) | 10–25 deals |

**The math:** If you close 10 DSCR loans averaging $350K at 2% commission = $70,000 in year 1, from a $240/year tool investment. That's a 291x ROI.

---

## QUICK-START CHECKLIST

Use this after reading the full guide:

- [x] Create Airtable account (Team plan, $20/mo)
- [x] Create base: "DSCR Investor Intelligence"
- [x] Build all 7 tables with fields (Tables 1–7) — via API script (airtable_build_v2.py)
- [x] Link tables (Step 2) — 9 link relationships, all created via API
- [x] Add rollups and lookups (Step 3) — all rollups on Properties, Entities, Investors
- [x] Add lead scoring formulas (Step 4) — all 7 scoring formulas on Investors
- [ ] Create all views (Step 5) — **NOT STARTED** (24 views needed)
- [ ] Set up automations (Step 6) — **NOT STARTED** (8 automations needed)
- [ ] Build Interfaces / Dashboards (Step 7) — **NOT STARTED** (4 interfaces needed)
- [ ] Quick fixes: Add "Estimated Annual Rent" formula to Properties
- [ ] Quick fixes: Add "Property Count" rollup to Ownership Entities
- [ ] Quick fixes: Rename "Trigger County" → "Trigger Count" on Properties
- [ ] Quick fixes: Delete accidental "Table 8"
- [ ] Prepare test CSV files (5-10 leads)
- [ ] Test upload and validate triggers/scoring
- [ ] Prepare full CSV files for import
- [ ] Import Round 1: Investors
- [ ] Import Round 2: Entities
- [ ] Import Round 3: Properties
- [ ] Import Round 4: Financing
- [ ] Verify all links and rollups
- [ ] Review Tier 1 prospects list
- [ ] Review Trigger Alert Center
- [ ] Create HubSpot Free account
- [ ] Set up Zapier sync (Airtable → HubSpot)
- [ ] Begin Tier 1 outreach

---

## BUILD STATUS (Updated 2026-03-06)

### Base: appJV7J1ZrNEBAWAm | Workspace: wspqb7kWqj5RidMkV

### Field Inventory (API-verified, 0 broken):

| Table | Total Fields | Formulas | Rollups | Links | Status |
|-------|-------------|----------|---------|-------|--------|
| Investors | 50 | 9 | 10 | 5 | ✅ Complete |
| Ownership Entities | 18 | 1 | 3 | 2 | ⚠️ Missing Property Count rollup |
| Properties | 36 | 10 | 3 | 4 | ⚠️ Missing Estimated Annual Rent, "Trigger County" needs rename |
| Financing | 35 | 11 | 0 | 1 | ✅ Complete |
| Compliance | 15 | 2 | 0 | 1 | ✅ Complete |
| Opportunities | 24 | 5 | 0 | 3 | ✅ Complete |
| Outreach Log | 13 | 0 | 0 | 2 | ✅ Complete |
| **TOTAL** | **191** | **38** | **16** | **18** | |

### What Was Built Via API Script:
- 7 tables, 133 base fields, 9 link relationships (airtable_build_v2.py)
- Financing trigger formulas (12 fields) — manual in Airtable UI
- Properties intermediate formulas (13 fields) — manual/AI in Airtable UI
- Investors rollups + lead scoring (19 fields) — Airtable AI prompts
- Opportunities formulas + auto fields (7 fields) — Airtable AI prompts
- Compliance formulas (2 fields) — Airtable AI prompts
- Ownership Entities rollups + formula (4 fields) — Airtable AI prompts

### Known Issues:
1. "Trigger County" on Properties is actually the Trigger Count rollup (typo in field name)
2. "Estimated Annual Rent" formula missing from Properties (spec: `{Estimated Monthly Rent} * 12`)
3. "Property Count" rollup missing from Ownership Entities
4. Accidental "Table 8" needs deletion
5. Financing trigger field names lack emoji prefixes per Build Guide spec (e.g., "Hard Money Flag" not "🚨 Hard Money Flag") — formulas reference actual names, so this is cosmetic only

### Build Files:
- `airtable/airtable_build_v1.py` — First API build attempt (superseded)
- `airtable/airtable_build_v2.py` — Production API build script (created base skeleton)
- `airtable/create_remaining_fields.py` — Attempted API field creation (blocked by Airtable API limitations on formula/rollup types)
- `airtable/Airtable_AI_Field_Prompts.md` — 10 copy-paste prompts used to create formula/rollup fields via Airtable AI
- `airtable/DSCR_Manual_Fields_Checklist.md` — Manual field creation checklist used during build

---

*Built for DSCR investor prospecting in Palm Beach & Broward County, FL. Signal over volume.*
