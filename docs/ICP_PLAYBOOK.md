# ICP Playbook — Ideal Customer Profiles for DSCR Lending

## How This Works

Every investment property owner gets scored 0-100. The score determines their tier and outreach priority. ICP segments describe *why* someone needs a DSCR loan. Refi overlays describe *when* they need one. A single lead can have both a primary ICP and multiple refi signals.

---

## Master Scoring Matrix

### Property Signals (max 45 points)

| Signal | Points | Detection | Why It Matters |
|--------|--------|-----------|----------------|
| No homestead exemption | +20 | homestead_flag = N/blank | Confirms investment property |
| Value $150K-$500K | +10 | just_value in range | DSCR sweet spot |
| Value $500K-$1M | +8 | just_value in range | Larger deals, fewer qualify |
| Multi-family (2-4 units) | +10 | use_code in [02,03,04] | Higher rent, better DSCR |
| STR-eligible zip | +5 | Property in tourist zips | STR income viable |

### Owner Signals (max 40 points)

| Signal | Points | Detection | Why It Matters |
|--------|--------|-----------|----------------|
| Out-of-state absentee | +15 | mail_state ≠ property_state | Strong investor indicator |
| In-state absentee | +10 | same state, different zip | Local investor |
| LLC/Corp owned | +10 | Entity keywords in name | Sophisticated investor |
| Portfolio 5+ properties | +20 | property_count >= 5 | High-value, scaling |
| Portfolio 2-4 properties | +10 | property_count 2-4 | Growing investor |

### Transaction Signals (max 30 points)

| Signal | Points | Detection | Why It Matters |
|--------|--------|-----------|----------------|
| Cash purchase (no mortgage) | +15 | No mortgage in clerk records | Cash-out refi candidate |
| Recent purchase (0-12 mo) | +10 | sale_date within 12 months | Active buyer |
| Recent purchase (12-24 mo) | +5 | sale_date within 12-24 months | Moderately active |
| Owned 5+ years, no refi | +5 | sale_date > 5 years ago | Equity to tap |

### Refi Score Boost (0-40 additional points, from refi overlay detection)

---

## Tier Definitions

| Tier | Score | Action | Expected Volume |
|------|-------|--------|----------------|
| **Tier 1: Hot** | 50+ | Immediate: phone + email + direct mail | 10-15% of leads |
| **Tier 2: Warm** | 30-49 | Email + mail sequence, phone if resources allow | 25-35% |
| **Tier 3: Nurture** | 15-29 | Long-term email nurture only | 20-30% |
| **Discard** | <15 | Do not outreach | Remainder |

---

## Purchase-Side ICP Segments

### Tier 1 (Highest Value)

**ICP 1: Individual Investors (2-9 Properties)**
- **Signal:** 2-9 non-homesteaded residential properties, personal name
- **Detection:** `property_count >= 2 AND < 10 AND is_entity = FALSE`
- **Why DSCR:** Tax returns understate income. DSCR qualifies on rent.
- **Outreach:** "You own [X] properties in [County]. DSCR lets you keep growing without income docs."
- **Volume:** Largest segment (~10K-12K per major metro county)

**ICP 2: Serial Investors (10+ Properties)**
- **Signal:** 10+ residential units, often multiple LLCs, repeat buyer
- **Detection:** `property_count >= 10`
- **Why DSCR:** Maxed conventional limit (10 properties). Multiple simultaneous DSCR loans.
- **Outreach:** "You've outgrown conventional. DSCR has no property limit."
- **Volume:** ~300-500 per major county. Highest per-relationship value.

**ICP 3: STR Operators**
- **Signal:** Active vacation rental license or listing in tourist market
- **Detection:** `str_licensed = TRUE` or property in STR-eligible zip
- **Why DSCR:** Conventional lenders exclude STR income. DSCR accepts AirDNA data.
- **Outreach:** "Your Airbnb income qualifies — we use AirDNA data, not bank rent estimates."

**ICP 4: Foreign National Investors**
- **Signal:** Non-U.S. mailing address, no U.S. state domicile
- **Detection:** `foreign_owner = TRUE`
- **Why DSCR:** Cannot qualify for conventional U.S. mortgages. DSCR is often their ONLY option.
- **Outreach:** "Foreign national? DSCR is your path to U.S. real estate financing."
- **Volume:** 5-10% of investor properties in international markets (Miami, Orlando)

**ICP 5: BRRRR Strategy Investors**
- **Signal:** Recent purchase well below median + hard money/bridge loan
- **Detection:** `purchase_discount > 0.30 AND days_since_purchase < 365`
- **Why DSCR:** Every BRRRR investor with hard money = future DSCR refi in 3-12 months.
- **Outreach:** "Ready to refinance out of that hard money loan? Zero seasoning cash-out."

**ICP 6: Entity-Based Investors (Multi-Entity)**
- **Signal:** Property titled to LLC/Corp/Trust, active entity filing, 2+ entities
- **Detection:** `is_entity = TRUE AND (entity_count >= 2 OR property_count >= 2)`
- **Why DSCR:** DSCR loans can close in entity name (conventional usually cannot).

### Tier 2

**ICP 7: High-Net-Worth Individuals**
- **Signal:** Portfolio value >$3M, premium zip codes
- **Detection:** Captured indirectly through scoring (high portfolio value)

**ICP 8: Multi-Family Investors**
- **Signal:** Owns duplex/triplex/fourplex, non-owner-occupied
- **Detection:** `use_code in ('03','08') AND property_count = 1`

**ICP 9: 1031 Exchange Buyers**
- **Signal:** Recent sale + new purchase within 180 days
- **Detection:** Derived from purchase history analysis

**ICP 10: Self-Employed RE Investors**
- **Signal:** Business owner + investment property
- **Detection:** SunBiz/SoS active business filing + property ownership (indirect)
- **Why DSCR:** Tax write-offs reduce reportable income — can't qualify conventionally.

**ICP 11: Fund Managers / Syndicators**
- **Signal:** SEC Form D filing for real estate offering
- **Detection:** `sec_fund_filing = TRUE`
- **Volume:** 200-500 per state per year

### Tier 3 (Niche)

| ICP | Signal | Source |
|-----|--------|--------|
| Section 8 Landlords | HAP payments from housing authority | Housing Authority records |
| First-Time Investors | Single non-homesteaded property, recent purchase | Property records |
| Accidental Landlords | Previously homesteaded, now non-homesteaded | Property records delta |
| Out-of-State Investors | Mailing state ≠ property state | Property records |

---

## Refinance Overlay Segments

These are **additive** — a lead can be both a purchase ICP AND a refi candidate. The refi signal boosts their score by 10-40 points.

**Cash Buyers (Leverage-Up)** — Score boost: +20
- Detection: `equity_ratio >= 0.90 AND price > $100,000`
- Opportunity: Cash-out at 75% LTV. Zero seasoning.

**Equity Harvesters** — Score boost: +15 to +20
- Detection: `equity_ratio >= 0.30` (30%+) or `>= 0.50` (50%+)
- Opportunity: Extract equity for next deal.

**Rate Refi Candidates** — Score boost: +10
- Detection: Purchased/financed 2022-2023 (peak rates 7-8%+)
- Opportunity: Current rates lower. Savings on monthly payment.

**BRRRR Exit Candidates** — Score boost: +15
- Detection: Purchased 30%+ below median within 12 months
- Opportunity: Hard money → permanent DSCR financing.

**Portfolio Equity Harvesters** — Score boost: +15
- Detection: `property_count >= 3 AND equity_ratio > 0.35`
- Opportunity: Multiple cash-out refis in one relationship. Blanket loan candidates.

---

## ICP Classification Priority

When a lead matches multiple ICPs, highest-priority wins:

```
1. Serial Investor (10+)
2. Fund Manager / Syndicator
3. STR Operator
4. Foreign National
5. Entity-Based Investor
6. Individual Investor (2-9)
7. Multi-Family Investor
8. Out-of-State Investor
9. Single Investment Property
```

The refi overlay is always applied as a secondary tag regardless of primary ICP.

---

## DSCR Product Features (For Outreach Context)

Key product features that map to ICP needs:
- No income documentation required
- LLC/entity closing allowed
- Min FICO 680 (some programs 660)
- DSCR ratios accepted down to 0.75
- Zero seasoning on cash-out refinance
- AirDNA/STR income accepted
- Section 8 income accepted
- Foreign national programs (ITIN, passport-based)
- 40-year and interest-only options
- Gift funds up to 100% accepted

---

## STR-Eligible Zip Codes

STR zips are market-specific and stored in `config/scoring_weights.json` under `str_eligible_zips`. Each deployment should define tourist zip codes for its market.

## Property Use Codes

Use codes are state-specific. Common residential codes to include:

| Code | Description | DSCR Eligible |
|------|-------------|--------------|
| Single Family Residential | Primary target if non-homesteaded | Yes |
| Mobile Home | Lower value, still eligible | Yes |
| Multi-Family (2-9 units) | High priority — better DSCR ratios | Yes |
| Condominium | Good for STR investors | Yes |
| Multi-Family (10+ units) | Commercial crossover — high value | Yes |
| Vacant Land | No rental income | No |
| Commercial | Not DSCR residential eligible | No |

State-specific use code mappings are in `deployments/{state}/CONFIG.md`.
