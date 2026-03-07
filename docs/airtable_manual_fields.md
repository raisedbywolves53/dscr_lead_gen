# DSCR Investor Intelligence -- Manual Fields Checklist

## What Was Already Built (via API)

The automated setup script successfully created:

- **7 tables**: Investors, Ownership Entities, Properties, Financing, Opportunities, Outreach Log, Compliance
- **133 fields** across all tables (singleLineText, phoneNumber, email, url, multilineText, singleSelect, multipleSelects, number, currency, percent, date, checkbox, autoNumber)
- **All multipleRecordLinks** (linked record fields between tables, both directions)

## What Remains (Must Be Created Manually in Airtable)

The Airtable REST API **cannot** create the following field types. Each one must be added by hand in the Airtable UI.

**Summary:**

| Type | Count |
|------|-------|
| Rollup fields | 16 |
| Formula fields | 33 |
| Lookup fields | 1 |
| Created Time fields | 2 |
| Last Modified Time fields | 1 |
| **TOTAL manual fields** | **53** |

---

## CREATION ORDER

Fields must be created in dependency order. A formula that references a rollup cannot exist until that rollup is built. Follow the phases below sequentially.

---

## PHASE 1: Properties Table -- Rollups and Base Formulas

These must come first because Investors and Ownership Entities roll up data *from* Properties.

### Table: Properties

- [ ] **Total Property Debt**
  - Type: `Rollup`
  - Linked Table: Financing (via "Financing Records" link)
  - Rolled-Up Field: `Estimated Loan Balance`
  - Aggregation: `SUM(values)`

- [ ] **Monthly PITIA Estimate**
  - Type: `Rollup`
  - Linked Table: Financing (via "Financing Records" link)
  - Rolled-Up Field: `Monthly Payment Estimate`
  - Aggregation: `SUM(values)`

- [ ] **Estimated Annual Rent**
  - Type: `Formula`
  - Formula: `{Estimated Monthly Rent} * 12`

- [ ] **Estimated Equity**
  - Type: `Formula`
  - Formula: `IF({Estimated Property Value}, {Estimated Property Value} - IF({Total Property Debt}, {Total Property Debt}, 0), "")`

- [ ] **Estimated LTV**
  - Type: `Formula`
  - Formula: `IF(AND({Total Property Debt} > 0, {Estimated Property Value} > 0), ROUND({Total Property Debt} / {Estimated Property Value} * 100, 1), IF(AND({Total Property Debt} = 0, {Estimated Property Value} > 0), 0, ""))`

- [ ] **Equity Percentage**
  - Type: `Formula`
  - Formula: `IF({Estimated Property Value} > 0, ROUND((1 - IF({Total Property Debt}, {Total Property Debt}, 0) / {Estimated Property Value}) * 100, 1), "")`

- [ ] **Cash Purchase Flag**
  - Type: `Formula`
  - Formula: `IF(AND({Purchase Price} > 0, {Total Property Debt} = 0), "CASH PURCHASE", "")`

- [ ] **Days Since Purchase**
  - Type: `Formula`
  - Formula: `IF({Purchase Date}, DATETIME_DIFF(NOW(), {Purchase Date}, 'days'), "")`

- [ ] **Months Owned**
  - Type: `Formula`
  - Formula: `IF({Purchase Date}, DATETIME_DIFF(NOW(), {Purchase Date}, 'months'), "")`

- [ ] **Estimated DSCR**
  - Type: `Formula`
  - Formula: `IF(AND({Estimated Monthly Rent} > 0, {Monthly PITIA Estimate} > 0), ROUND({Estimated Monthly Rent} / {Monthly PITIA Estimate}, 2), IF(AND({Estimated Monthly Rent} > 0, {Monthly PITIA Estimate} = 0), 99, ""))`

- [ ] **DSCR Status**
  - Type: `Formula`
  - Formula: `IF({Estimated DSCR} = "", "No Data", IF({Estimated DSCR} >= 1.25, "Strong", IF({Estimated DSCR} >= 1.0, "Marginal", IF({Estimated DSCR} = 99, "No Debt", "Below 1.0"))))`

---

## PHASE 2: Financing Table -- Lookup, Formulas, and Trigger Flags

These depend on the Financing table's own fields plus the Lookup from Properties.

### Table: Financing

- [ ] **Property Value (Lookup)**
  - Type: `Lookup`
  - Linked Table: Properties (via "Property" link)
  - Looked-Up Field: `Estimated Property Value`

- [ ] **Monthly PITIA**
  - Type: `Formula`
  - Formula: `IF({Monthly Payment Estimate}, {Monthly Payment Estimate} + IF({Estimated Annual Taxes}, {Estimated Annual Taxes}/12, 0) + IF({Estimated Annual Insurance}, {Estimated Annual Insurance}/12, 0) + IF({HOA Monthly}, {HOA Monthly}, 0), "")`

- [ ] **Estimated LTV**
  - Type: `Formula`
  - Formula: `IF(AND({Estimated Loan Balance} > 0, {Property Value (Lookup)} > 0), ROUND({Estimated Loan Balance} / {Property Value (Lookup)} * 100, 1), "")`
  - Note: Uses the Lookup field created above -- NOT the hardcoded placeholder

- [ ] **Months to Maturity**
  - Type: `Formula`
  - Formula: `IF({Loan Maturity Date}, DATETIME_DIFF({Loan Maturity Date}, NOW(), 'months'), "")`

- [ ] **Days to Maturity**
  - Type: `Formula`
  - Formula: `IF({Loan Maturity Date}, DATETIME_DIFF({Loan Maturity Date}, NOW(), 'days'), "")`

- [ ] **Maturity Window Flag**
  - Type: `Formula`
  - Formula: `IF(AND({Months to Maturity} != "", {Months to Maturity} > 0, {Months to Maturity} <= 24), "MATURES WITHIN 24 MO", IF(AND({Months to Maturity} != "", {Months to Maturity} <= 0), "PAST MATURITY", ""))`

- [ ] **High Rate Flag**
  - Type: `Formula`
  - Formula: `IF(AND({Interest Rate} != "", {Interest Rate} > 0.08), "RATE ABOVE 8%", IF(AND({Interest Rate} != "", {Interest Rate} > 0.07), "RATE ABOVE 7%", ""))`

- [ ] **Hard Money Flag**
  - Type: `Formula`
  - Formula: `IF(OR({Loan Type} = "Hard Money", {Loan Type} = "Private Lender", {Loan Type} = "Bridge"), "HARD MONEY / PRIVATE", "")`

- [ ] **Balloon Risk Flag**
  - Type: `Formula`
  - Formula: `IF(AND({Balloon Payment}, {Balloon Date}), IF(DATETIME_DIFF({Balloon Date}, NOW(), 'months') <= 0, "BALLOON PAST DUE", IF(DATETIME_DIFF({Balloon Date}, NOW(), 'months') <= 24, "BALLOON WITHIN 24 MO", "")), "")`

- [ ] **Prepay Penalty Clear**
  - Type: `Formula`
  - Formula: `IF({Prepayment Penalty}, IF({Prepayment Penalty End Date}, IF(DATETIME_DIFF({Prepayment Penalty End Date}, NOW(), 'days') <= 0, "Penalty Expired", "Penalty Active until " & DATETIME_FORMAT({Prepayment Penalty End Date}, 'MM/DD/YYYY')), "Penalty Active (no end date)"), "No Penalty")`

- [ ] **Trigger Count**
  - Type: `Formula`
  - Formula: `(IF({Maturity Window Flag} != "", 1, 0)) + (IF({High Rate Flag} != "", 1, 0)) + (IF({Hard Money Flag} != "", 1, 0)) + (IF({Balloon Risk Flag} != "", 1, 0))`
  - Note: Use whatever exact field names you gave the flag fields above

- [ ] **Refinance Opportunity Score**
  - Type: `Formula`
  - Formula: `(IF({Hard Money Flag} != "", 35, 0)) + (IF({Maturity Window Flag} != "", 25, 0)) + (IF({High Rate Flag} != "", 20, 0)) + (IF({Balloon Risk Flag} != "", 15, 0)) + (IF({Prepay Penalty Clear} = "No Penalty", 5, IF({Prepay Penalty Clear} = "Penalty Expired", 5, 0)))`

---

## PHASE 3: Properties Table -- Intermediate Fields for Lead Scoring

These fields on Properties aggregate Financing data so that Investors can roll them up (Airtable rollups only go one link deep).

### Table: Properties (continued)

- [ ] **Has Hard Money** (intermediate field)
  - Step A: Create a `Lookup` field on Properties -- but since we need a formula combining lookup results, instead create this as a `Formula` type
  - Type: `Formula`
  - Formula: `IF(FIND("HARD MONEY", ARRAYJOIN({Hard Money Flag Lookup}, ",")), 1, 0)`
  - **PREREQUISITE**: First create a **Lookup** field called "Hard Money Lookup" on Properties, looking up `Hard Money Flag` from Financing via the "Financing Records" link. Then use that lookup in this formula.
  - **Alternate simpler approach**: Create as a `Rollup` on Properties -> Financing Records -> Hard Money Flag -> `COUNTA(values)` and then wrap: `IF({Hard Money Rollup} > 0, 1, 0)` in a formula.

- [ ] **Trigger Count** (intermediate field -- on Properties)
  - Type: `Rollup`
  - Linked Table: Financing (via "Financing Records" link)
  - Rolled-Up Field: `Trigger Count` (the formula field on Financing)
  - Aggregation: `SUM(values)`

- [ ] **Recent Purchase** (intermediate field)
  - Type: `Formula`
  - Formula: `IF(AND({Purchase Date}, {Months Owned} <= 24), 1, 0)`
  - Depends on: `Months Owned` formula (created in Phase 1)

- [ ] **Is Cash Purchase** (intermediate field)
  - Type: `Formula`
  - Formula: `IF({Cash Purchase Flag} != "", 1, 0)`
  - Depends on: `Cash Purchase Flag` formula (created in Phase 1)

---

## PHASE 4: Ownership Entities Table -- Rollups and Formulas

### Table: Ownership Entities

- [ ] **Property Count**
  - Type: `Rollup`
  - Linked Table: Properties (via "Properties" link)
  - Rolled-Up Field: `Property Address`
  - Aggregation: `COUNTA(values)`

- [ ] **Total Entity Value**
  - Type: `Rollup`
  - Linked Table: Properties (via "Properties" link)
  - Rolled-Up Field: `Estimated Property Value`
  - Aggregation: `SUM(values)`

- [ ] **Total Entity Debt**
  - Type: `Rollup`
  - Linked Table: Properties (via "Properties" link)
  - Rolled-Up Field: `Total Property Debt`
  - Aggregation: `SUM(values)`
  - Depends on: `Total Property Debt` rollup on Properties (created in Phase 1)

- [ ] **Entity Equity**
  - Type: `Formula`
  - Formula: `{Total Entity Value} - {Total Entity Debt}`
  - Depends on: both rollups above

- [ ] **Primary Markets**
  - Type: `Rollup`
  - Linked Table: Properties (via "Properties" link)
  - Rolled-Up Field: `City`
  - Aggregation: `ARRAYUNIQUE(ARRAYFLATTEN(values))`

---

## PHASE 5: Investors Table -- Rollups

These rollups on Investors pull from Properties, Entities, Outreach Log, and Opportunities.

### Table: Investors

- [ ] **Property Count**
  - Type: `Rollup`
  - Linked Table: Properties (via "Properties" link)
  - Rolled-Up Field: `Property Address`
  - Aggregation: `COUNTA(values)`

- [ ] **Total Portfolio Value**
  - Type: `Rollup`
  - Linked Table: Properties (via "Properties" link)
  - Rolled-Up Field: `Estimated Property Value`
  - Aggregation: `SUM(values)`

- [ ] **Total Portfolio Debt**
  - Type: `Rollup`
  - Linked Table: Properties (via "Properties" link)
  - Rolled-Up Field: `Total Property Debt`
  - Aggregation: `SUM(values)`
  - Note: This is "Option A" -- chaining through the Properties table rollup

- [ ] **Entity Count**
  - Type: `Rollup`
  - Linked Table: Ownership Entities (via "Entities" link)
  - Rolled-Up Field: `Entity Name`
  - Aggregation: `COUNTA(values)`

- [ ] **Outreach Count**
  - Type: `Rollup`
  - Linked Table: Outreach Log (via "Outreach Log" link)
  - Rolled-Up Field: `Date`
  - Aggregation: `COUNTA(values)`

- [ ] **Open Opportunities**
  - Type: `Rollup`
  - Linked Table: Opportunities (via "Opportunities" link)
  - Rolled-Up Field: `Opportunity Stage`
  - Aggregation: `COUNTA(values)`

- [ ] **Hard Money Loan Count**
  - Type: `Rollup`
  - Linked Table: Properties (via "Properties" link)
  - Rolled-Up Field: `Has Hard Money` (intermediate field from Phase 3)
  - Aggregation: `SUM(values)`

- [ ] **Total Trigger Count**
  - Type: `Rollup`
  - Linked Table: Properties (via "Properties" link)
  - Rolled-Up Field: `Trigger Count` (the rollup on Properties from Phase 3)
  - Aggregation: `SUM(values)`

- [ ] **Recent Purchase Count**
  - Type: `Rollup`
  - Linked Table: Properties (via "Properties" link)
  - Rolled-Up Field: `Recent Purchase` (intermediate field from Phase 3)
  - Aggregation: `SUM(values)`

- [ ] **Cash Purchase Count**
  - Type: `Rollup`
  - Linked Table: Properties (via "Properties" link)
  - Rolled-Up Field: `Is Cash Purchase` (intermediate field from Phase 3)
  - Aggregation: `SUM(values)`

---

## PHASE 6: Investors Table -- Formulas (Basic + Lead Scoring)

All of these depend on the rollups created in Phase 5.

### Table: Investors (continued)

- [ ] **Estimated Portfolio Equity**
  - Type: `Formula`
  - Formula: `{Total Portfolio Value} - {Total Portfolio Debt}`

- [ ] **Days Since Last Contact**
  - Type: `Formula`
  - Formula: `IF({Last Contact Date}, DATETIME_DIFF(NOW(), {Last Contact Date}, 'days'), 999)`

- [ ] **Portfolio Size Score**
  - Type: `Formula`
  - Formula:
    ```
    IF({Property Count} >= 20, 30,
      IF({Property Count} >= 10, 25,
        IF({Property Count} >= 5, 20,
          IF({Property Count} >= 3, 15,
            IF({Property Count} >= 2, 10,
              IF({Property Count} >= 1, 5, 0))))))
    ```

- [ ] **Refi Opportunity Score**
  - Type: `Formula`
  - Formula:
    ```
    IF({Total Trigger Count} >= 4, 25,
      IF({Total Trigger Count} >= 3, 20,
        IF({Total Trigger Count} >= 2, 15,
          IF({Total Trigger Count} >= 1, 10, 0))))
    ```

- [ ] **Recent Purchase Score**
  - Type: `Formula`
  - Formula:
    ```
    IF({Recent Purchase Count} >= 3, 20,
      IF({Recent Purchase Count} >= 2, 15,
        IF({Recent Purchase Count} >= 1, 10, 0)))
    ```

- [ ] **Equity Score**
  - Type: `Formula`
  - Formula:
    ```
    IF({Estimated Portfolio Equity} = "", 0,
      IF({Estimated Portfolio Equity} >= 2000000, 15,
        IF({Estimated Portfolio Equity} >= 1000000, 12,
          IF({Estimated Portfolio Equity} >= 500000, 9,
            IF({Estimated Portfolio Equity} >= 250000, 6,
              IF({Estimated Portfolio Equity} >= 100000, 3, 0))))))
    ```

- [ ] **Hard Money Score**
  - Type: `Formula`
  - Formula:
    ```
    IF({Hard Money Loan Count} >= 3, 10,
      IF({Hard Money Loan Count} >= 2, 8,
        IF({Hard Money Loan Count} >= 1, 5, 0)))
    ```

- [ ] **Lead Score (0-100)**
  - Type: `Formula`
  - Formula: `{Portfolio Size Score} + {Refi Opportunity Score} + {Recent Purchase Score} + {Equity Score} + {Hard Money Score}`
  - Depends on: all 5 scoring component formulas above

- [ ] **Lead Tier**
  - Type: `Formula`
  - Formula:
    ```
    IF({Lead Score (0-100)} >= 80, "Tier 1 -- Personal Outreach",
      IF({Lead Score (0-100)} >= 60, "Tier 2 -- Semi-Personal",
        IF({Lead Score (0-100)} >= 40, "Tier 3 -- Automated Nurture",
          "Low Priority")))
    ```
  - Depends on: `Lead Score (0-100)` formula above

---

## PHASE 7: Opportunities Table -- Formulas and Auto-Timestamp Fields

### Table: Opportunities

- [ ] **Weighted Value**
  - Type: `Formula`
  - Formula: `IF(AND({Estimated Loan Amount}, {Probability of Close}), ROUND({Estimated Loan Amount} * {Probability of Close}, 0), "")`

- [ ] **Estimated Commission**
  - Type: `Formula`
  - Formula: `IF({Estimated Loan Amount}, ROUND({Estimated Loan Amount} * 0.02, 0), "")`
  - Note: Adjust 0.02 to your actual commission percentage

- [ ] **Weighted Commission**
  - Type: `Formula`
  - Formula: `IF(AND({Estimated Commission}, {Probability of Close}), ROUND({Estimated Commission} * {Probability of Close}, 0), "")`
  - Depends on: `Estimated Commission` formula above

- [ ] **Days in Stage**
  - Type: `Formula`
  - Formula: `DATETIME_DIFF(NOW(), LAST_MODIFIED_TIME(), 'days')`

- [ ] **Days Since Created**
  - Type: `Formula`
  - Formula: `DATETIME_DIFF(NOW(), CREATED_TIME(), 'days')`

- [ ] **Date Created**
  - Type: `Created time`
  - Configuration: Automatic timestamp when record is created

- [ ] **Last Modified**
  - Type: `Last modified time`
  - Configuration: Automatic timestamp when record is modified

---

## PHASE 8: Outreach Log -- Created Time Field

### Table: Outreach Log

- [ ] **Date Created**
  - Type: `Created time`
  - Configuration: Automatic timestamp when record is created

---

## PHASE 9: Compliance Table -- Formulas

### Table: Compliance

- [ ] **Next Scrub Due**
  - Type: `Formula`
  - Formula: `IF(AND({Record Type} = "DNC Scrub", {Date}), DATEADD({Date}, 31, 'days'), "")`

- [ ] **Scrub Overdue**
  - Type: `Formula`
  - Formula: `IF(AND({Next Scrub Due} != "", IS_BEFORE({Next Scrub Due}, NOW())), "OVERDUE - SCRUB NOW", IF(AND({Next Scrub Due} != "", DATETIME_DIFF({Next Scrub Due}, NOW(), 'days') <= 7), "Due within 7 days", ""))`
  - Depends on: `Next Scrub Due` formula above

---

## COMPLETE FIELD COUNT BY TABLE

| Table | Rollup | Formula | Lookup | Created Time | Last Modified Time | Subtotal |
|-------|--------|---------|--------|--------------|-------------------|----------|
| Investors | 10 | 9 | 0 | 0 | 0 | **19** |
| Ownership Entities | 4 | 1 | 0 | 0 | 0 | **5** |
| Properties | 3 | 9 | 0 | 0 | 0 | **12** |
| Financing | 0 | 11 | 1 | 0 | 0 | **12** |
| Opportunities | 0 | 5 | 0 | 1 | 1 | **7** |
| Outreach Log | 0 | 0 | 0 | 1 | 0 | **1** |
| Compliance | 0 | 2 | 0 | 0 | 0 | **2** |
| **TOTAL** | **17** | **37** | **1** | **2** | **1** | **58** |

Note: The count above includes the "Hard Money Lookup" helper lookup on Properties (needed for the Has Hard Money formula), bringing the lookup count to 2 and the total closer to 58. The exact count depends on implementation approach for the Has Hard Money intermediate field.

---

## TIPS FOR EFFICIENT MANUAL CREATION

1. **Work in the order above** -- Phase 1 before Phase 2, etc. Skipping ahead will cause "field not found" errors in formulas.
2. **Copy-paste formulas** -- Click into a formula field config, paste the formula from this doc, then verify field name references match exactly (including capitalization and special characters).
3. **Test with sample data** -- After each phase, enter 1-2 test records to verify rollups and formulas calculate correctly before moving on.
4. **Field name matching** -- Formula references like `{Total Property Debt}` must match the field name EXACTLY. If you named it slightly differently during API creation, update the formula to match.
5. **Rollup field selection** -- When creating a rollup, Airtable shows a dropdown of linked tables, then fields on that table, then aggregation functions. Follow the three values listed for each rollup above.
6. **The "Has Hard Money" workaround** -- This is the trickiest field. You need a Lookup on Properties to pull Hard Money Flag values from Financing, then a Formula to convert that array into a 0/1 flag. Consider the simpler Rollup approach noted in Phase 3.

---

*This checklist covers all fields that the Airtable API cannot create. Once all 53+ fields are added, proceed to Step 5 (Views), Step 6 (Automations), and Step 7 (Interfaces) from the main Build Guide.*
