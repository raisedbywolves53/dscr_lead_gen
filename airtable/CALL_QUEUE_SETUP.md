# Call Queue — Manual Setup (10 minutes)

After running `python airtable/refresh_call_queue.py`, create this view in Airtable.

---

## Create "Call Queue" View on Investors Table

1. Go to **Investors** table
2. Click **+ Add a view** → **Grid**
3. Name: `📞 Call Queue`
4. **Filter** (2 conditions, AND):
   - **DNC Status** → is → `Clear`
   - AND **Call Priority** → is not empty
5. **Sort** (2 levels):
   - **Call Priority** → Ascending (A→Z)
   - **Lead Score (0-100)** → Descending (9→1)
6. **Hide all fields**, then show only these 12 columns (in this order):
   1. Full Name
   2. Call Priority
   3. Trigger Summary
   4. Estimated Monthly Savings
   5. Phone (Mobile)
   6. Last Outreach Summary
   7. Lead Score (0-100)
   8. Lead Tier
   9. Current Lenders
   10. Portfolio Snapshot
   11. Primary Market
   12. Relationship Strength

---

## How to Use

1. Run `python airtable/refresh_call_queue.py` before each dial session (~2 min for test data, ~5 min for 7,500 leads)
2. Open the **Call Queue** view — leads are sorted P0 (follow-ups) through P7 (nurture)
3. Work top-to-bottom. Each row has the trigger details, savings pitch, and last conversation right there
4. After each call, log it in Outreach Log — next refresh will update Last Outreach Summary and Call Priority

### Priority Key

| Code | Meaning | Action |
|------|---------|--------|
| P0-FollowUp | Follow-up due today/overdue | Call immediately |
| P1-HardMoney | Has hard money / bridge / private loan | Pitch DSCR refi, save them 30-50% on rate |
| P2-Balloon | Balloon payment coming | Urgent — they MUST refi or pay lump sum |
| P3-Maturity | Loan maturing within 24 months | Proactive refi before deadline |
| P4-HighRate | Rate above 7-8% | Rate reduction pitch |
| P5-CashPurchase | Bought property with cash | Cash-out refi to recoup capital |
| P6-NewLead | Never contacted | First touch |
| P7-Nurture | Contacted, no active triggers | Stay in touch |
| DQ-DNC | DNC or unchecked | Do NOT call — scrub first |

---

## Optional: Add to Investor Profile Interface

When building Interface 2 (Investor Profile) from Phase 5, add these 6 fields to the detail layout:
- Trigger Summary
- Portfolio Snapshot
- Current Lenders
- Estimated Monthly Savings
- Last Outreach Summary
- Call Priority
