# Airtable AI Prompts — Remaining 32 Fields

Copy and paste each prompt below into Airtable's AI assistant. Do them in order since later fields depend on earlier ones. Wait for each batch to finish before moving to the next.

---

## PROMPT 1: Ownership Entities Table (4 fields)

```
On the "Ownership Entities" table, please create these 4 fields:

1. A Rollup field named "Total Entity Value"
   - Linked table: Properties (use the "Properties" link field on this table)
   - Field to aggregate: Estimated Property Value
   - Aggregation function: SUM(values)

2. A Rollup field named "Total Entity Debt"
   - Linked table: Properties (use the "Properties" link field on this table)
   - Field to aggregate: Total Property Debt
   - Aggregation function: SUM(values)

3. A Formula field named "Entity Equity"
   - Formula: {Total Entity Value} - {Total Entity Debt}

4. A Rollup field named "Primary Markets"
   - Linked table: Properties (use the "Properties" link field on this table)
   - Field to aggregate: City
   - Aggregation function: ARRAYUNIQUE(ARRAYFLATTEN(values))
```

---

## PROMPT 2: Opportunities Table — Formulas (5 fields)

```
On the "Opportunities" table, please create these 5 formula fields:

1. Formula field named "Weighted Value"
   Formula: IF(AND({Estimated Loan Amount}, {Probability of Close}), ROUND({Estimated Loan Amount} * {Probability of Close}, 0), "")

2. Formula field named "Estimated Commission"
   Formula: IF({Estimated Loan Amount}, ROUND({Estimated Loan Amount} * 0.02, 0), "")

3. Formula field named "Weighted Commission"
   Formula: IF(AND({Estimated Commission}, {Probability of Close}), ROUND({Estimated Commission} * {Probability of Close}, 0), "")

4. Formula field named "Days in Stage"
   Formula: DATETIME_DIFF(NOW(), LAST_MODIFIED_TIME(), 'days')

5. Formula field named "Days Since Created"
   Formula: DATETIME_DIFF(NOW(), CREATED_TIME(), 'days')
```

---

## PROMPT 3: Opportunities Table — Auto Fields (2 fields)

```
On the "Opportunities" table, please create these 2 fields:

1. A "Created time" field named "Date Created"
   - Format: Local date and time
   - Time zone: Eastern Time

2. A "Last modified time" field named "Last Modified"
   - Format: Local date and time
   - Time zone: Eastern Time
```

---

## PROMPT 4: Compliance Table (2 fields)

```
On the "Compliance" table, please create these 2 formula fields:

1. Formula field named "Next Scrub Due"
   Formula: IF(AND({Record Type} = "DNC Scrub", {Date}), DATEADD({Date}, 31, 'days'), "")

2. Formula field named "Scrub Overdue"
   Formula: IF(AND({Next Scrub Due} != "", IS_BEFORE({Next Scrub Due}, NOW())), "⛔ OVERDUE - SCRUB NOW", IF(AND({Next Scrub Due} != "", DATETIME_DIFF({Next Scrub Due}, NOW(), 'days') <= 7), "⚠️ Due within 7 days", ""))
```

---

## PROMPT 5: Investors Table — Core Rollups (6 fields)

```
On the "Investors" table, please create these 6 rollup fields:

1. Rollup field named "Property Count"
   - Use the "Properties" link field on this table
   - Field to aggregate: Property Address
   - Aggregation: COUNTA(values)

2. Rollup field named "Total Portfolio Value"
   - Use the "Properties" link field on this table
   - Field to aggregate: Estimated Property Value
   - Aggregation: SUM(values)

3. Rollup field named "Total Portfolio Debt"
   - Use the "Properties" link field on this table
   - Field to aggregate: Total Property Debt
   - Aggregation: SUM(values)

4. Rollup field named "Entity Count"
   - Use the "Ownership Entities" link field on this table
   - Field to aggregate: Entity Name
   - Aggregation: COUNTA(values)

5. Rollup field named "Outreach Count"
   - Use the "Outreach Log" link field on this table
   - Field to aggregate: Date
   - Aggregation: COUNTA(values)

6. Rollup field named "Open Opportunities"
   - Use the "Opportunities" link field on this table
   - Field to aggregate: Opportunity Stage
   - Aggregation: COUNTA(values)
```

---

## PROMPT 6: Investors Table — Lead Scoring Rollups (4 fields)

```
On the "Investors" table, please create these 4 rollup fields. These roll up intermediate calculation fields from the Properties table:

1. Rollup field named "Hard Money Loan Count"
   - Use the "Properties" link field on this table
   - Field to aggregate: Has Hard Money
   - Aggregation: SUM(values)

2. Rollup field named "Total Trigger Count"
   - Use the "Properties" link field on this table
   - Field to aggregate: Trigger County (this is the trigger count rollup on Properties)
   - Aggregation: SUM(values)

3. Rollup field named "Recent Purchase Count"
   - Use the "Properties" link field on this table
   - Field to aggregate: Recent Purchase
   - Aggregation: SUM(values)

4. Rollup field named "Cash Purchase Count"
   - Use the "Properties" link field on this table
   - Field to aggregate: Is Cash Purchase
   - Aggregation: SUM(values)
```

---

## PROMPT 7: Investors Table — Core Formulas (2 fields)

```
On the "Investors" table, please create these 2 formula fields:

1. Formula field named "Estimated Portfolio Equity"
   Formula: {Total Portfolio Value} - {Total Portfolio Debt}

2. Formula field named "Days Since Last Contact"
   Formula: IF({Last Contact Date}, DATETIME_DIFF(NOW(), {Last Contact Date}, 'days'), 999)
```

---

## PROMPT 8: Investors Table — Lead Scoring Formulas Part 1 (3 fields)

```
On the "Investors" table, please create these 3 formula fields for lead scoring:

1. Formula field named "Portfolio Size Score"
   Formula: IF({Property Count} >= 20, 30, IF({Property Count} >= 10, 25, IF({Property Count} >= 5, 20, IF({Property Count} >= 3, 15, IF({Property Count} >= 2, 10, IF({Property Count} >= 1, 5, 0))))))

2. Formula field named "Refi Opportunity Score"
   Formula: IF({Total Trigger Count} >= 4, 25, IF({Total Trigger Count} >= 3, 20, IF({Total Trigger Count} >= 2, 15, IF({Total Trigger Count} >= 1, 10, 0))))

3. Formula field named "Recent Purchase Score"
   Formula: IF({Recent Purchase Count} >= 3, 20, IF({Recent Purchase Count} >= 2, 15, IF({Recent Purchase Count} >= 1, 10, 0)))
```

---

## PROMPT 9: Investors Table — Lead Scoring Formulas Part 2 (2 fields)

```
On the "Investors" table, please create these 2 formula fields for lead scoring:

1. Formula field named "Equity Score"
   Formula: IF({Estimated Portfolio Equity} = "" , 0, IF({Estimated Portfolio Equity} >= 2000000, 15, IF({Estimated Portfolio Equity} >= 1000000, 12, IF({Estimated Portfolio Equity} >= 500000, 9, IF({Estimated Portfolio Equity} >= 250000, 6, IF({Estimated Portfolio Equity} >= 100000, 3, 0))))))

2. Formula field named "Hard Money Score"
   Formula: IF({Hard Money Loan Count} >= 3, 10, IF({Hard Money Loan Count} >= 2, 8, IF({Hard Money Loan Count} >= 1, 5, 0)))
```

---

## PROMPT 10: Investors Table — Composite Score + Tier (2 fields)

```
On the "Investors" table, please create these 2 final formula fields:

1. Formula field named "Lead Score (0-100)"
   Formula: {Portfolio Size Score} + {Refi Opportunity Score} + {Recent Purchase Score} + {Equity Score} + {Hard Money Score}

2. Formula field named "Lead Tier"
   Formula: IF({Lead Score (0-100)} >= 80, "🔥 Tier 1 — Personal Outreach", IF({Lead Score (0-100)} >= 60, "⭐ Tier 2 — Semi-Personal", IF({Lead Score (0-100)} >= 40, "📋 Tier 3 — Automated Nurture", "⬜ Low Priority")))
```

---

## COMPLETION CHECKLIST

After running all 10 prompts, verify these totals:

- [ ] Ownership Entities: 4 new fields (Total Entity Value, Total Entity Debt, Entity Equity, Primary Markets)
- [ ] Opportunities: 7 new fields (Weighted Value, Estimated Commission, Weighted Commission, Days in Stage, Days Since Created, Date Created, Last Modified)
- [ ] Compliance: 2 new fields (Next Scrub Due, Scrub Overdue)
- [ ] Investors: 19 new fields (6 core rollups + 4 scoring rollups + 2 core formulas + 7 lead scoring formulas)

**Total: 32 new fields across 4 tables**

NOTE on "Trigger County" field: The Properties table has a field called "Trigger County" which is actually the Trigger Count rollup (it was named slightly wrong during creation). When Prompt 6 references it, use whatever name appears in the Properties table for that rollup field.
