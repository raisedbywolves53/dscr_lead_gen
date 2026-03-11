# ICP_CRITERIA.md — DSCR Loan Lead Scoring & ICP Definitions

## Context

This scoring system identifies Florida property owners most likely to need or benefit from a DSCR (Debt Service Coverage Ratio) mortgage loan. DSCR loans qualify borrowers based on the property's rental income rather than personal income — making them ideal for investors, self-employed borrowers, LLC owners, and anyone who struggles with traditional income documentation.

The MLO client works with Change Wholesale as the lender. Key product features:
- No income documentation required
- LLC closing required in Florida
- Min FICO 680 (some programs 660)
- DSCR ratios accepted down to 0.75
- Zero seasoning on cash-out refinance
- AirDNA/STR income accepted
- Section 8 income accepted
- Foreign national programs available
- 40-year and interest-only options
- Gift funds up to 100% accepted

---

## Master Scoring Matrix

Each property/owner combination receives a score from 0-100. Points are additive.

### Property Signals (max 45 points)

| Signal | Points | How to Detect | Why It Matters |
|--------|--------|---------------|----------------|
| No homestead exemption | +20 | homestead_flag = N or blank | Confirms investment property, not primary residence |
| Property value $150K-$500K | +10 | just_value in range | Sweet spot for DSCR — high enough to pencil, low enough for most investors |
| Property value $500K-$1M | +8 | just_value in range | Larger deals, but fewer investors qualify |
| Multi-family (2-4 units) | +10 | use_code in [02, 03, 04] or description contains "DUPLEX", "TRIPLEX", "QUAD" | Higher rental income, better DSCR ratios |
| STR-eligible zip code | +5 | Property in tourist zip codes (Orlando, Miami Beach, Keys, Gulf Coast, etc.) | Short-term rental strategy viable — DSCR lender accepts AirDNA income |

### Owner Signals (max 40 points)

| Signal | Points | How to Detect | Why It Matters |
|--------|--------|---------------|----------------|
| Absentee owner (out-of-state) | +15 | mail_state ≠ "FL" | Strong indicator of investor — likely manages remotely |
| Absentee owner (in-state, different zip) | +10 | mail_state = "FL" but mail_zip ≠ prop_zip | Local investor, likely owns as rental |
| LLC/Corp owned | +10 | Entity keywords in owner_name | Sophisticated investor, already structured for DSCR |
| Portfolio landlord (5+ properties) | +20 | portfolio_count >= 5 | High-value target — likely needs DSCR for scaling |
| Portfolio landlord (2-4 properties) | +10 | portfolio_count 2-4 | Growing investor, approaching conventional limits |

### Transaction Signals (max 30 points)

| Signal | Points | How to Detect | Why It Matters |
|--------|--------|---------------|----------------|
| Cash purchase (no mortgage) | +15 | No mortgage in county records OR sale_price > 0 with no DOT recorded | May want to extract equity via DSCR cash-out refi |
| Recent purchase (0-12 months) | +10 | sale_date within last 12 months | Active buyer — may want to buy more using DSCR |
| Recent purchase (12-24 months) | +5 | sale_date within 12-24 months | Moderately active, may be ready for next deal |
| Property owned 5+ years with no refi | +5 | sale_date > 5 years ago, no recent mortgage | Likely has significant equity to tap |

---

## ICP Tier Definitions

### Tier 1: Hot Leads (Score 50+)
**Action:** Immediate outreach — phone call + email + direct mail
**Expected volume:** ~10-15% of total records
**Profile:** These are active investors with clear DSCR need signals

### Tier 2: Warm Leads (Score 30-49)
**Action:** Email + direct mail sequence, phone if resources allow
**Expected volume:** ~25-35% of total records
**Profile:** Likely investors but fewer confirming signals

### Tier 3: Nurture (Score 15-29)
**Action:** Add to long-term email nurture only
**Expected volume:** ~20-30% of total records

### Below 15: Discard
**Action:** Do not outreach
**Reason:** Insufficient investor signals — likely owner-occupants or non-targets

---

## ICP Segment Definitions

### ICP #1: Portfolio Landlords (Scaling Investors)
**Who:** Owns 5+ rental properties in Florida
**Why DSCR:** Hit conventional 10-property limit, DTI maxed out
**Key signals:** portfolio_count >= 5, no homestead, LLC ownership
**Outreach angle:** "You own [X] properties in [County]. DSCR lets you keep scaling without income docs or DTI limits."

### ICP #2: Self-Employed Business Owners
**Who:** LLC/Corp owners buying investment property
**Why DSCR:** Tax write-offs reduce reportable income, can't qualify conventionally
**Key signals:** LLC ownership, cross-reference with Sunbiz active business filings
**Outreach angle:** "Your tax returns don't show your true income. DSCR qualifies on the property's rent — not your 1040."

### ICP #3: Short-Term Rental Investors
**Who:** Airbnb/VRBO operators in Florida tourist markets
**Why DSCR:** Conventional lenders exclude STR income
**Key signals:** Property in STR-eligible zip, absentee owner, recent purchase in tourist area
**Outreach angle:** "Your Airbnb income qualifies — we use AirDNA data, not bank rent estimates."

### ICP #4: Out-of-State Investors
**Who:** Non-Florida residents owning FL investment property
**Why DSCR:** Remote investing is common, DSCR simplifies qualification from anywhere
**Key signals:** mail_state ≠ "FL", no homestead, LLC ownership common
**Outreach angle:** "Investing in Florida from [their state]? DSCR makes it simple — no tax returns needed."

### ICP #5: Cash Buyers Seeking Leverage (BRRRR / Equity Extraction)
**Who:** Bought property with cash, now want to pull equity out
**Why DSCR:** Zero seasoning cash-out refi — extract equity immediately
**Key signals:** Cash purchase, no mortgage on record, property value > $150K
**Outreach angle:** "You own [Property] free and clear. Extract up to 80% equity with zero seasoning — close in 3 weeks."

### ICP #6: Section 8 Landlords
**Who:** Owners renting to Section 8 voucher holders
**Why DSCR:** Government-backed rent is reliable income for DSCR qualification
**Key signals:** Properties in Section 8-heavy zip codes, below-market rents, stable occupancy
**Outreach angle:** "Section 8 landlord? Your government-backed rent qualifies for DSCR — no income docs needed."

### ICP #7: Foreign National Investors
**Who:** Non-US citizens investing in Florida real estate
**Why DSCR:** Cannot qualify for conventional US mortgages
**Key signals:** Foreign mailing address, LLC with foreign agent, purchase in international investor corridors (Miami, Orlando)
**Outreach angle:** "Foreign national? DSCR is your path to Florida real estate financing — no US tax returns or credit history needed."

### ICP #8: First-Time Real Estate Investors
**Who:** Buying first investment property
**Why DSCR:** Simple qualification, doesn't impact primary residence DTI
**Key signals:** Single non-homesteaded property, recent purchase, individual (not LLC) owner
**Outreach angle:** "First investment property? DSCR keeps your personal DTI clean for your next primary home purchase."

---

## Florida STR-Eligible Zip Codes (Tourist Markets)

### Orlando Metro
32801, 32803, 32804, 32806, 32807, 32808, 32809, 32812, 32819, 32821, 32822, 32824, 32827, 32828, 32829, 32830, 32836, 32837, 34711, 34714, 34747, 34786, 34787

### Miami / Miami Beach / Fort Lauderdale
33101, 33109, 33132, 33133, 33137, 33139, 33140, 33141, 33154, 33160, 33180, 33304, 33305, 33308, 33316, 33334, 33019, 33020

### Florida Keys
33036, 33037, 33040, 33042, 33043, 33050, 33051, 33070

### Gulf Coast (Sarasota / Naples / Fort Myers / Destin)
34102, 34103, 34108, 34109, 34110, 34112, 34119, 34201, 34228, 34229, 34230, 34231, 34236, 34237, 34238, 34239, 34242, 33901, 33908, 33919, 33928, 33931, 33957, 32541, 32550, 32459

### Jacksonville Beach / St. Augustine
32082, 32084, 32233, 32250, 32266

### Tampa / St. Pete / Clearwater
33701, 33702, 33703, 33704, 33705, 33706, 33707, 33708, 33709, 33710, 33711, 33712, 33713, 33714, 33715, 33716, 33762, 33763, 33764, 33765, 33767, 33770, 33771, 33772, 33773, 33774, 33776, 33785, 33786

---

## Florida Property Use Codes (Key Codes for Filtering)

| Code | Description | Relevance |
|------|-------------|-----------|
| 01 | Single Family Residential | Primary target if non-homesteaded |
| 02 | Mobile Home | Lower value, still DSCR eligible |
| 03 | Multi-Family (2-9 units) | High priority — better DSCR ratios |
| 04 | Condominium | Good for STR investors |
| 05 | Cooperatives | Less common, still eligible |
| 08 | Multi-Family (10+ units) | Commercial crossover — high value |
| 10-39 | Vacant Land | Not DSCR eligible (no rental income) |
| 48 | Warehouse/Distribution | Not DSCR residential eligible |

**Filter IN:** Use codes 01, 02, 03, 04, 05, 08
**Filter OUT:** Everything else (vacant land, commercial, agricultural, institutional)
