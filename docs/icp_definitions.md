# ICP Definitions — All Segments Including Refinance

## How This Document Works

Each ICP segment has:
- **Signal**: What observable data identifies this person
- **Source**: Where the signal comes from in our pipeline
- **Classification Logic**: Exact rules used in `06_score_and_output.py`
- **Tier**: Priority level (1 = highest value, 3 = niche)
- **Refi Overlay**: Whether this ICP also has refinance opportunity signals

---

## PURCHASE CANDIDATES — Tier 1

### ICP 1: Individual Real Estate Investors (1-10 Properties)

**Signal**: Owns 2-10 non-homesteaded residential investment properties in FL. Properties titled to personal name. Active (purchase/refi) in last 24 months.

**Source**: FDOR NAL data — property_count 2-9, homestead exemption = 0, mailing address != property address

**Classification Logic**:
```
IF property_count >= 2 AND property_count < 10 AND is_entity = FALSE:
    icp_primary = "Individual Investor (2-9)"
    tier = 1 if property_count >= 5 else 2
```

**Estimated Volume (Palm Beach)**: ~10K-12K leads
**DSCR Fit**: Core audience. Tax returns often understate income, making DSCR the ideal product.

---

### ICP 2: Professional / Serial Investors (10+ Properties)

**Signal**: Owns 10+ residential units in FL. Multiple LLCs. Repeat buyer (3+ transactions in 24 months).

**Source**: FDOR NAL — property_count >= 10

**Classification Logic**:
```
IF property_count >= 10:
    icp_primary = "Serial Investor (10+)"
    tier = 1
```

**Estimated Volume (Palm Beach)**: ~383 leads
**DSCR Fit**: Highest value. Multiple simultaneous DSCR loans per relationship. Blanket loan candidates.

---

### ICP 3: Short-Term Rental (STR) Operators

**Signal**: Active Airbnb/VRBO listing in FL. STR permit on file with DBPR. Property managed as vacation rental.

**Source**: DBPR vacation rental license database cross-referenced to FDOR property records

**Classification Logic**:
```
IF str_licensed = TRUE OR str_license_count > 0:
    icp_primary = "STR Operator"
    tier = 1
```

**Estimated Volume (FL-wide)**: 60K+ licensed vacation rentals. Palm Beach: moderate (not primary STR market like Orlando/Kissimmee)
**DSCR Fit**: Excellent. STR income often exceeds long-term rental income, producing strong DSCR ratios. theLender and Change Wholesale specifically support STR DSCR.

---

### ICP 4: Foreign National Investors

**Signal**: Non-U.S. citizen purchasing FL investment property. Mailing address outside U.S. No U.S. state code in owner domicile.

**Source**: FDOR NAL — OWN_STATE_DOM not in U.S. state code list

**Classification Logic**:
```
IF foreign_owner = TRUE:
    icp_primary = "Foreign National"
    tier = 1
```

**Estimated Volume (Palm Beach)**: ~8,892 leads
**DSCR Fit**: Critical. Foreign nationals CANNOT qualify for conventional U.S. mortgages. DSCR is often their ONLY financing option. theLender specifically offers Foreign National DSCR (ITIN, passport-based qualification). 47% of international FL buyers pay all-cash = massive cash-out refi opportunity.

---

### ICP 5: Self-Employed Borrowers (Who Invest in RE)

**Signal**: Business owner or self-employed professional who owns FL investment property. Tax returns show depressed income due to deductions.

**Source**: Cannot be directly identified from FDOR data. Identified indirectly via:
- SunBiz active business filing + property ownership
- CPA referral partnerships (Phase 2)
- LinkedIn targeting (Phase 2)

**Classification Logic**: Not directly classified in current pipeline. Future enhancement.

**DSCR Fit**: Broad audience. The #1 reason self-employed borrowers use DSCR: their tax-optimized returns don't show enough income for conventional qualification.

---

### ICP 6: BRRRR Strategy Investors

**Signal**: Recent purchase of distressed/below-market property + hard money or bridge loan + renovation. Will need DSCR refinancing in 3-12 months.

**Source**: FDOR NAL — sale price significantly below county median + recent purchase date

**Classification Logic** (via refi detection):
```
IF purchase_discount > 0.30 AND days_since_purchase < 365:
    brrrr_exit_candidate = TRUE
    icp_secondary = "BRRRR Exit Candidate"
    refi_score_boost += 15
```

**Estimated Volume (Palm Beach)**: ~5K leads flagged as BRRRR exit candidates
**DSCR Fit**: Guaranteed pipeline. Every BRRRR investor with a hard money loan = future DSCR refi. Time-sensitive (3-12 month window).

---

### ICP 7: Corporate Entities (LLCs, S-Corps, Trusts)

**Signal**: Property titled to LLC, Corporation, or Trust. Active entity filing with FL Division of Corporations.

**Source**: FDOR NAL — entity keyword detection in OWN_NAME field. Resolved to human via SunBiz.

**Classification Logic**:
```
IF is_entity = TRUE AND entity_count >= 2:
    icp_primary = "Entity-Based Investor"
    tier = 1
ELIF is_entity = TRUE AND property_count >= 2:
    icp_primary = "Entity-Based Investor"
    tier = 1
```

**Estimated Volume (Palm Beach)**: ~49K entity-owned properties
**DSCR Fit**: Standard. Serious investors use entities. DSCR loans can close in entity name (most conventional cannot). SunBiz resolution provides the human contact.

---

## PURCHASE CANDIDATES — Tier 2

### ICP 8: High-Net-Worth Individuals (HNWIs)

**Signal**: Net worth $1M+, member of wealth peer groups (Tiger 21, YPO, Vistage), luxury property ownership.

**Source**: Not directly identifiable from FDOR data. Proxied by:
- Very high portfolio value (total_portfolio_value > $3M)
- Multiple high-value properties in premium zip codes

**Classification Logic**: Captured indirectly through scoring. Portfolio value > $3M gets max score.

---

### ICP 9: Multi-Family Investors (2-4 Units)

**Signal**: Owner of duplex, triplex, or fourplex. Non-owner-occupied.

**Source**: FDOR NAL — DOR_UC = 03 (2-9 units) or 08 (10+ units)

**Classification Logic**:
```
IF DOR_UC in ('03','08') AND property_count = 1:
    icp_primary = "Multi-Family Investor"
    tier = 2
```

---

### ICP 10: 1031 Exchange Buyers

**Signal**: Active 1031 exchange = 45-day identification deadline = urgent DSCR pre-approval need.

**Source**: Not directly in FDOR data. Identified through:
- Recent sale of investment property + new purchase within 180 days
- 1031 QI referral partnerships (Phase 2)

---

### ICP 11: Recently Retired / Career Changers

**Source**: Not directly identifiable from FDOR. Proxied by age of owner (if available) and 55+ community locations.

---

### ICP 12: Tax-Strategy Investors

**Source**: CPA referral partnerships. Cost segregation firm partnerships. Not in current pipeline.

---

### ICP 13: Fund Managers / Syndicators

**Signal**: SEC Form D filing for FL real estate offering (Reg D 506b/c).

**Source**: SEC EDGAR full-text search API

**Classification Logic**:
```
IF sec_fund_filing = TRUE:
    icp_primary = "Fund Manager / Syndicator"
    tier = 2
```

**Estimated Volume**: 200-500 FL RE fund filings per year

---

## REFINANCE CANDIDATES

These are **overlay segments** — a lead can be BOTH a purchase candidate ICP AND a refi candidate. The refi signal is captured in `icp_secondary` and `refi_signals` columns.

### Refi ICP 14: All-Cash Buyers (Leverage-Up)

**Signal**: 100% equity, no mortgage, owned 6+ months. These buyers paid all-cash and now have a property sitting with zero leverage.

**Source**: FDOR NAL — equity_ratio >= 0.90 (JV ≈ sale price with no mortgage paydown)

**Detection Logic** (in `08_refi_simple.py`):
```
IF equity_ratio >= 0.90 AND most_recent_price > $100,000:
    probable_cash_buyer = TRUE
    refi_signal = "Probable All-Cash Buyer"
    refi_score_boost = +20
```

**Opportunity**: Cash-out at 75% LTV on $400K property = $300K tax-free capital to redeploy
**Volume**: 43K-45K all-cash investor purchases per year in FL (69% of investor purchases nationally are all-cash)
**Tier**: 1

---

### Refi ICP 15: Equity Harvesters

**Signal**: 30%+ equity built up through appreciation. Owned 2+ years. Sitting on extractable wealth.

**Source**: FDOR NAL — JV (current value) vs. SALE_PRC1 (purchase price) delta

**Detection Logic**:
```
IF equity_ratio >= 0.50:
    equity_harvest_candidate = TRUE
    refi_signal = "Very High Equity (50%+)"
    refi_score_boost = +20

IF equity_ratio >= 0.30:
    equity_harvest_candidate = TRUE
    refi_signal = "High Equity (30%+)"
    refi_score_boost = +15
```

**Volume**: 100K+ owners statewide with 30%+ equity
**Tier**: 1

---

### Refi ICP 16: Rate Refi Candidates (2022-2023 Vintage)

**Signal**: Purchased and financed in 2022-2023 when DSCR rates were 7-8%+. Current rates 6.0-7.5% = savings opportunity.

**Source**: FDOR NAL — SALE_YR1 in (2022, 2023)

**Detection Logic**:
```
IF sale_date.year in (2022, 2023) AND most_recent_price > $100,000:
    rate_refi_candidate = TRUE
    refi_signal = "Rate Refi Candidate (2022-2023 Vintage)"
    refi_score_boost = +10
```

**Known Limitation**: FDOR NAL only stores the most recent sale. Owner-level aggregation takes the max (most recent) date, so if a 2022 buyer also bought in 2024, only 2024 shows. This signal works best at property level.
**Volume**: 30K-50K FL owners estimated
**Tier**: 2

---

### Refi ICP 17: BRRRR Exit Candidates

**Signal**: Purchased well below county median (<12 months ago). Likely distressed/rehab purchase with hard money financing. Will need permanent DSCR financing in 3-12 months.

**Source**: FDOR NAL — sale price 20-30%+ below county median AND purchased within 12 months

**Detection Logic**:
```
county_median = $400,000  # Palm Beach approximation

IF (1 - price/county_median) > 0.30 AND days_since_purchase < 365:
    brrrr_exit_candidate = TRUE
    refi_signal = "BRRRR Exit Candidate (30%+ below median, <1yr)"
    refi_score_boost = +15

IF (1 - price/county_median) > 0.20 AND days_since_purchase < 365:
    brrrr_exit_candidate = TRUE
    refi_signal = "Possible BRRRR (20%+ below median, <1yr)"
    refi_score_boost = +10
```

**Volume**: 5K-10K per year statewide
**Tier**: 1

---

### Refi ICP 18: Portfolio Equity Harvesters

**Signal**: Owns 3+ properties with average equity ratio above 35%. Multiple cash-out refi opportunities in a single relationship.

**Source**: FDOR NAL — property_count >= 3 AND avg equity_ratio > 0.35

**Detection Logic**:
```
IF property_count >= 3 AND equity_ratio > 0.35:
    refi_signal = "Portfolio Equity Harvest ({property_count} properties)"
    refi_score_boost = +15
```

**Volume**: 10K-20K owners statewide
**Tier**: 1
**Special Value**: Blanket loan candidates (theLender's "theBlanket" product). One relationship = multiple loan originations.

---

## NICHE SEGMENTS — Tier 3

### ICP 19: Section 8 Landlords
- **Signal**: Landlord receiving HAP payments from housing authority
- **Source**: Housing Authority records (not in current pipeline)

### ICP 20: First-Time Investors
- **Signal**: First non-owner-occupied purchase, no prior investment properties
- **Source**: FDOR property_count = 1 + recent purchase

### ICP 21: Commercial Crossover
- **Signal**: CRE investor adding residential
- **Source**: CoStar/LoopNet activity (not in current pipeline)

### ICP 22: Diaspora Investors
- **Signal**: First-generation immigrant with FL property ownership
- **Source**: Ethnic chambers, cultural organizations (relationship-based)

### ICP 23: Digital Nomads / Expats
- **Signal**: Remote worker with U.S. property interest
- **Source**: Digital community engagement (not in current pipeline)

### ICP 24: Accidental Landlords
- **Signal**: Converted primary to rental (had homestead, now renting out)
- **Source**: FDOR — previously homesteaded property now non-homesteaded

---

## ICP Classification Priority Order

When a lead matches multiple ICPs, the highest-priority classification wins:

```
1. Serial Investor (10+)       — property_count >= 10
2. Fund Manager / Syndicator   — SEC Form D filing
3. STR Operator                — DBPR licensed
4. Foreign National            — non-US domicile
5. Entity-Based Investor       — LLC/Corp/Trust + multi-property
6. Individual Investor (2-9)   — property_count 2-9
7. Multi-Family Investor       — DOR_UC 03/08
8. Out-of-State Investor       — mailing state != FL
9. Single Investment Property  — default
```

The **refi overlay** is always applied as `icp_secondary` regardless of primary classification. A "Serial Investor (10+)" can also be tagged "Portfolio Equity Harvest Candidate".

---

## Scoring Interaction with Refi Signals

The `refi_score_boost` (0-40 points) from Step 2 is ADDED to the base score (0-100) in Step 7. This means:

- A single-property owner with no contact info (base score ~15) but strong refi signal (+20) gets score 35
- A 10+ property entity-based investor (base score ~60) with equity harvest signal (+15) gets score 75
- Cap at 100

This ensures refi candidates get elevated even if their purchase-side profile is weaker.
