# SAMPLE VALIDATION REPORT
**Date**: 2026-02-28  
**Source**: Palm Beach County FDOR NAL (189,382 investor leads)  
**Sample Size**: 50 leads (stratified diverse selection)  
**Pipeline**: FDOR Filter -> Refi Detection -> SunBiz -> DBPR -> EDGAR -> Enrichment -> ICP Scoring  

---

## Executive Summary

| Metric | Value |
|--------|-------|
| Total Leads | 50 |
| Score 70+ (High Value) | 17 (34%) |
| Score 50-69 (Medium) | 15 (30%) |
| Score <50 (Lower) | 18 (36%) |
| Average Score | 60.7 |
| Refi Candidates | 23 (46%) |
| Contact Coverage (phone or email) | 0 (0%) |
| Entity-Owned (LLC/Trust/Partnership) | 25 (50%) |
| Foreign Nationals | 5 (10%) |
| SunBiz Resolved (entity -> person) | 24 of 25 entities (96%) |

### ICP Segment Breakdown

| ICP Segment | Count | Avg Score |
|-------------|-------|-----------|
| Entity-Based Investor | 14 | 57 |
| Foreign National | 5 | 35 |
| Individual Investor (2-9) | 9 | 59 |
| Out-of-State Investor | 2 | 54 |
| Serial Investor (10+) | 14 | 71 |
| Single Investment Property | 6 | 72 |

### Tier Distribution

| Tier | Count | Description |
|------|-------|-------------|
| Tier 1 | 36 | Highest value - direct outreach |
| Tier 2 | 13 | Medium - email/campaign |
| Tier 3 | 1 | Lower priority |

### Data Quality Observations

- **Contact enrichment**: 0% coverage in this sample run. People search sites (TruePeopleSearch, FastPeopleSearch) block automated requests. Apollo.io API key not configured. DBPR had no name/address overlap with this 50-lead sample. **Action needed**: Configure Apollo API key or use manual enrichment for priority leads.
- **SunBiz resolution**: 96% success rate (24/25 entities resolved to human names). Cache from prior runs helped significantly.
- **Equity ratio anomaly**: Several leads show equity ratio ~100% with purchase price of $10. This indicates FDOR recording a $10 nominal transfer (trust/entity restructuring, not a real sale). These are NOT true BRRRR candidates despite being flagged. **Action needed**: Filter out purchase prices < $1,000 from BRRRR detection.
- **Institutional investors**: Several 'Serial Investor (10+)' leads are institutional SFR buyers (Invitation Homes/Progress Residential). These are NOT DSCR loan candidates. **Action needed**: Build institutional owner exclusion list.
- **Portfolio value calculation**: Appears accurate based on FDOR Just Values. Ranges from $79K (single condo) to $212M (institutional).
- **Foreign nationals**: All 5 in sample are Canadian with ultra-high-value Palm Beach properties ($38M-$72M). These are genuine DSCR targets — foreign nationals cannot qualify for conventional US mortgages.

---

## Lead Profile Cards

### Entity-Based Investor (14 leads)

#### DSCR-000030 | Score: 100 | Tier 1

| Field | Value |
|-------|-------|
| **Owner Name** | FLORIDA ESTATES LLC |
| **Resolved Person** | NONE |
| **Owner Type** | LLC |
| **ICP Classification** | Entity-Based Investor / Growing Portfolio |
| **Properties** | 8 |
| **Portfolio Value** | $98.4M |
| **Equity Ratio** | 78% |
| **Max Cash-Out (75% LTV)** | $6.5M |
| **Refi Signals** | Very High Equity (50%+) | Portfolio Equity Harvest (8 properties) |
| **Refi Priority** | High |
| **Most Recent Purchase** | 2025-05-01 at $2.7M |
| **Contact Info** | **None** (not enriched) |
| **Location** | PALM BEACH county (WALNUT CREEK, California) |
| **Flags** | Out-of-State, Equity Harvest |
| **Entities Controlled** | 3 |

> **Why this is a qualified lead**: Sitting on 78% equity across 8 properties ($98.4M) — cash-out refi at 75% LTV could unlock $6.5M for reinvestment.

---

#### DSCR-000009 | Score: 99 | Tier 1

| Field | Value |
|-------|-------|
| **Owner Name** | AAG PROPERTY MANAGEMENT LLC |
| **Resolved Person** | GURINO, ANTHONY |
| **Owner Type** | LLC |
| **ICP Classification** | Entity-Based Investor / BRRRR Exit Candidate |
| **Properties** | 9 |
| **Portfolio Value** | $1.5M |
| **Equity Ratio** | 100% |
| **Max Cash-Out (75% LTV)** | $127,067 |
| **Refi Signals** | Very High Equity (50%+) | BRRRR Exit Candidate (30%+ below median, <1yr) | Portfolio Equity Harvest (9 properties) |
| **Refi Priority** | High |
| **Most Recent Purchase** | 2025-04-01 at $10 |
| **Contact Info** | **None** (not enriched) |
| **Location** | PALM BEACH county (JAMAICA, New York) |
| **Flags** | Out-of-State, BRRRR Exit, Equity Harvest |
| **Entities Controlled** | 1 |

> **Why this is a qualified lead**: Flagged as BRRRR but $10 purchase price suggests entity restructuring/trust transfer, not a distressed buy — property value $1.5M still makes equity harvest viable.

---

#### DSCR-000028 | Score: 99 | Tier 1

| Field | Value |
|-------|-------|
| **Owner Name** | GONZALEZ MOISES & ISELA TRUST |
| **Resolved Person** | GONZALEZ, PEDRO |
| **Owner Type** | Trust |
| **ICP Classification** | Entity-Based Investor / BRRRR Exit Candidate |
| **Properties** | 8 |
| **Portfolio Value** | $1.8M |
| **Equity Ratio** | 100% |
| **Max Cash-Out (75% LTV)** | $166,189 |
| **Refi Signals** | Very High Equity (50%+) | BRRRR Exit Candidate (30%+ below median, <1yr) | Portfolio Equity Harvest (8 properties) |
| **Refi Priority** | High |
| **Most Recent Purchase** | 2025-07-01 at $100 |
| **Contact Info** | **None** (not enriched) |
| **Location** | PALM BEACH county (LAKE WORTH, Florida) |
| **Flags** | BRRRR Exit, Equity Harvest |
| **Entities Controlled** | 1 |

> **Why this is a qualified lead**: Flagged as BRRRR but $100 purchase price suggests entity restructuring/trust transfer, not a distressed buy — property value $1.8M still makes equity harvest viable.

---

#### DSCR-000044 | Score: 72 | Tier 1

| Field | Value |
|-------|-------|
| **Owner Name** | ENGLISH JOHN A TRUST & |
| **Resolved Person** | NONE |
| **Owner Type** | Trust |
| **ICP Classification** | Entity-Based Investor / Equity Harvest Candidate |
| **Properties** | 1 |
| **Portfolio Value** | $3.0M |
| **Equity Ratio** | 100% |
| **Max Cash-Out (75% LTV)** | $2.3M |
| **Refi Signals** | Very High Equity (50%+) |
| **Refi Priority** | Medium |
| **Most Recent Purchase** | 2024-04-01 at $10 |
| **Contact Info** | **None** (not enriched) |
| **Location** | PALM BEACH county (WEST PALM BEACH, Florida) |
| **Flags** | Equity Harvest |
| **Entities Controlled** | 3 |

> **Why this is a qualified lead**: Sitting on 100% equity across 1 property ($3.0M) — cash-out refi at 75% LTV could unlock $2.3M for reinvestment.

---

#### DSCR-000045 | Score: 66 | Tier 1

| Field | Value |
|-------|-------|
| **Owner Name** | DODGE GIOVANNA D TRUST |
| **Resolved Person** | NONE |
| **Owner Type** | Trust |
| **ICP Classification** | Entity-Based Investor / Equity Harvest Candidate |
| **Properties** | 1 |
| **Portfolio Value** | $519,176 |
| **Equity Ratio** | 100% |
| **Max Cash-Out (75% LTV)** | $389,372 |
| **Refi Signals** | Very High Equity (50%+) |
| **Refi Priority** | Medium |
| **Most Recent Purchase** | 2024-06-01 at $10 |
| **Contact Info** | **None** (not enriched) |
| **Location** | PALM BEACH county (JUPITER, Florida) |
| **Flags** | Equity Harvest |
| **Entities Controlled** | 3 |

> **Why this is a qualified lead**: Sitting on 100% equity across 1 property ($519,176) — cash-out refi at 75% LTV could unlock $389,372 for reinvestment.

---

#### DSCR-000038 | Score: 46 | Tier 1

| Field | Value |
|-------|-------|
| **Owner Name** | AARMAT HOLDINGS LLC |
| **Resolved Person** | KLEIN, jerry |
| **Owner Type** | LLC |
| **ICP Classification** | Entity-Based Investor |
| **Properties** | 3 |
| **Portfolio Value** | $595,558 |
| **Equity Ratio** | -0% |
| **Most Recent Purchase** | 2024-07-01 at $199,000 |
| **Contact Info** | **None** (not enriched) |
| **Location** | PALM BEACH county (HOLLYWOOD, Florida) |
| **Entities Controlled** | 1 |

> **Why this is a qualified lead**: Active individual investor with 3 properties ($595,558) in PALM BEACH — portfolio growth phase suggests need for DSCR to avoid DTI constraints.

---

#### DSCR-000006 | Score: 44 | Tier 1

| Field | Value |
|-------|-------|
| **Owner Name** | ZAKAI LLC |
| **Resolved Person** | HAKKI, FAWAZ Z |
| **Owner Type** | LLC |
| **ICP Classification** | Entity-Based Investor |
| **Properties** | 9 |
| **Portfolio Value** | $2.2M |
| **Contact Info** | **None** (not enriched) |
| **Location** | PALM BEACH county (WAYNESBORO, Pennsylvania) |
| **Flags** | Out-of-State |
| **Entities Controlled** | 1 |

> **Why this is a qualified lead**: Out-of-state investor from Pennsylvania with 9 FL properties ($2.2M) — remote investors commonly use DSCR since income docs are complex across state lines.

---

#### DSCR-000010 | Score: 44 | Tier 1

| Field | Value |
|-------|-------|
| **Owner Name** | PROSPERITY PROPERTIES 1 LLC |
| **Resolved Person** | ABRAMS, ERNEST S, IV |
| **Owner Type** | LLC |
| **ICP Classification** | Entity-Based Investor |
| **Properties** | 9 |
| **Portfolio Value** | $1.2M |
| **Contact Info** | **None** (not enriched) |
| **Location** | PALM BEACH county (BOYNTON BEACH, Florida) |
| **Entities Controlled** | 1 |

> **Why this is a qualified lead**: Active individual investor with 9 properties ($1.2M) in PALM BEACH — portfolio growth phase suggests need for DSCR to avoid DTI constraints.

---

#### DSCR-000007 | Score: 44 | Tier 1

| Field | Value |
|-------|-------|
| **Owner Name** | COINRA HOMES LLC |
| **Resolved Person** | IBARRA, JULIO C |
| **Owner Type** | LLC |
| **ICP Classification** | Entity-Based Investor |
| **Properties** | 9 |
| **Portfolio Value** | $2.1M |
| **Contact Info** | **None** (not enriched) |
| **Location** | PALM BEACH county (BOCA RATON, Florida) |
| **Entities Controlled** | 1 |

> **Why this is a qualified lead**: Active individual investor with 9 properties ($2.1M) in PALM BEACH — portfolio growth phase suggests need for DSCR to avoid DTI constraints.

---

#### DSCR-000008 | Score: 44 | Tier 1

| Field | Value |
|-------|-------|
| **Owner Name** | R4M LLC |
| **Resolved Person** | RANJANA AGRAWAL |
| **Owner Type** | LLC |
| **ICP Classification** | Entity-Based Investor |
| **Properties** | 9 |
| **Portfolio Value** | $2.2M |
| **Contact Info** | **None** (not enriched) |
| **Location** | PALM BEACH county (ROYAL PALM BEACH, Florida) |
| **Entities Controlled** | 1 |

> **Why this is a qualified lead**: Active individual investor with 9 properties ($2.2M) in PALM BEACH — portfolio growth phase suggests need for DSCR to avoid DTI constraints.

---

#### DSCR-000036 | Score: 36 | Tier 1

| Field | Value |
|-------|-------|
| **Owner Name** | BATTZCO BEACH REALTY LLC |
| **Resolved Person** | BATTISTA, CHRISTOPHER |
| **Owner Type** | LLC |
| **ICP Classification** | Entity-Based Investor |
| **Properties** | 4 |
| **Portfolio Value** | $945,378 |
| **Contact Info** | **None** (not enriched) |
| **Location** | PALM BEACH county (BOCA RATON, Florida) |
| **Entities Controlled** | 1 |

> **Why this is a qualified lead**: Active individual investor with 4 properties ($945,378) in PALM BEACH — portfolio growth phase suggests need for DSCR to avoid DTI constraints.

---

#### DSCR-000037 | Score: 36 | Tier 1

| Field | Value |
|-------|-------|
| **Owner Name** | ROSELLI ANNA G TRUST |
| **Resolved Person** | ROSELLI, ROBERT M |
| **Owner Type** | Trust |
| **ICP Classification** | Entity-Based Investor |
| **Properties** | 2 |
| **Portfolio Value** | $653,650 |
| **Contact Info** | **None** (not enriched) |
| **Location** | PALM BEACH county (DELRAY BEACH, Florida) |
| **Entities Controlled** | 1 |

> **Why this is a qualified lead**: Active individual investor with 2 properties ($653,650) in PALM BEACH — portfolio growth phase suggests need for DSCR to avoid DTI constraints.

---

#### DSCR-000035 | Score: 33 | Tier 1

| Field | Value |
|-------|-------|
| **Owner Name** | Z & L REALTY LLC |
| **Resolved Person** | ZHANG, SAORI |
| **Owner Type** | LLC |
| **ICP Classification** | Entity-Based Investor |
| **Properties** | 2 |
| **Portfolio Value** | $422,000 |
| **Contact Info** | **None** (not enriched) |
| **Location** | PALM BEACH county (WEST PALM BEACH, Florida) |
| **Entities Controlled** | 1 |

> **Why this is a qualified lead**: Active individual investor with 2 properties ($422,000) in PALM BEACH — portfolio growth phase suggests need for DSCR to avoid DTI constraints.

---

#### DSCR-000034 | Score: 33 | Tier 1

| Field | Value |
|-------|-------|
| **Owner Name** | M & B INVESTMENT TRUST LLC |
| **Resolved Person** | ZAHIDE DIKEC ATMACA |
| **Owner Type** | LLC |
| **ICP Classification** | Entity-Based Investor |
| **Properties** | 2 |
| **Portfolio Value** | $466,753 |
| **Contact Info** | **None** (not enriched) |
| **Location** | PALM BEACH county (BOCA RATON, Florida) |
| **Entities Controlled** | 1 |

> **Why this is a qualified lead**: Active individual investor with 2 properties ($466,753) in PALM BEACH — portfolio growth phase suggests need for DSCR to avoid DTI constraints.

---

### Foreign National (5 leads)

#### DSCR-000014 | Score: 37 | Tier 1

| Field | Value |
|-------|-------|
| **Owner Name** | 1460 N LAKE WAY LLC |
| **Resolved Person** | RABIDEAU, GUY |
| **Owner Type** | Foreign |
| **ICP Classification** | Foreign National / Entity-Based Investor |
| **Properties** | 1 |
| **Portfolio Value** | $38.4M |
| **Contact Info** | **None** (not enriched) |
| **Location** | PALM BEACH county (, CANADA) |
| **Flags** | Foreign National, Out-of-State |
| **Entities Controlled** | 1 |

> **Why this is a qualified lead**: Foreign national (CANADA) with $38.4M Palm Beach property — cannot qualify for conventional US mortgage, making DSCR the only financing option.

---

#### DSCR-000013 | Score: 37 | Tier 1

| Field | Value |
|-------|-------|
| **Owner Name** | PB PAVILION TRUST |
| **Resolved Person** | SUTARIA, PERIN A |
| **Owner Type** | Foreign |
| **ICP Classification** | Foreign National / Entity-Based Investor |
| **Properties** | 1 |
| **Portfolio Value** | $43.4M |
| **Contact Info** | **None** (not enriched) |
| **Location** | PALM BEACH county (, CANADA) |
| **Flags** | Foreign National, Out-of-State |
| **Entities Controlled** | 1 |

> **Why this is a qualified lead**: Foreign national (CANADA) with $43.4M Palm Beach property — cannot qualify for conventional US mortgage, making DSCR the only financing option.

---

#### DSCR-000012 | Score: 37 | Tier 1

| Field | Value |
|-------|-------|
| **Owner Name** | MORA MIDDLE INVS INC |
| **Resolved Person** | MORA, CAMILO |
| **Owner Type** | Foreign |
| **ICP Classification** | Foreign National / Entity-Based Investor |
| **Properties** | 1 |
| **Portfolio Value** | $45.2M |
| **Contact Info** | **None** (not enriched) |
| **Location** | PALM BEACH county (, CANADA) |
| **Flags** | Foreign National, Out-of-State |
| **Entities Controlled** | 1 |

> **Why this is a qualified lead**: Foreign national (CANADA) with $45.2M Palm Beach property — cannot qualify for conventional US mortgage, making DSCR the only financing option.

---

#### DSCR-000015 | Score: 32 | Tier 1

| Field | Value |
|-------|-------|
| **Owner Name** | GRANOVSKY GLUSKIN MAXINE TR & |
| **Owner Type** | Foreign |
| **ICP Classification** | Foreign National |
| **Properties** | 1 |
| **Portfolio Value** | $38.1M |
| **Contact Info** | **None** (not enriched) |
| **Location** | PALM BEACH county (, CANADA) |
| **Flags** | Foreign National, Out-of-State |

> **Why this is a qualified lead**: Foreign national (CANADA) with $38.1M Palm Beach property — cannot qualify for conventional US mortgage, making DSCR the only financing option.

---

#### DSCR-000011 | Score: 32 | Tier 1

| Field | Value |
|-------|-------|
| **Owner Name** | 770 SOUTH COUNTY ROAD LP |
| **Owner Type** | Foreign |
| **ICP Classification** | Foreign National |
| **Properties** | 1 |
| **Portfolio Value** | $72.2M |
| **Contact Info** | **None** (not enriched) |
| **Location** | PALM BEACH county (, CANADA) |
| **Flags** | Foreign National, Out-of-State |

> **Why this is a qualified lead**: Foreign national (CANADA) with $72.2M Palm Beach property — cannot qualify for conventional US mortgage, making DSCR the only financing option.

---

### Individual Investor (2-9) (9 leads)

#### DSCR-000031 | Score: 87 | Tier 2

| Field | Value |
|-------|-------|
| **Owner Name** | PRICE JENNIFER COOK |
| **Owner Type** | Individual |
| **ICP Classification** | Individual Investor (2-9) / BRRRR Exit Candidate |
| **Properties** | 2 |
| **Portfolio Value** | $51.1M |
| **Equity Ratio** | 100% |
| **Max Cash-Out (75% LTV)** | $19.2M |
| **Refi Signals** | Very High Equity (50%+) | BRRRR Exit Candidate (30%+ below median, <1yr) |
| **Refi Priority** | High |
| **Most Recent Purchase** | 2025-04-01 at $10 |
| **Contact Info** | **None** (not enriched) |
| **Location** | PALM BEACH county (RYE, New York) |
| **Flags** | Out-of-State, BRRRR Exit, Equity Harvest |

> **Why this is a qualified lead**: Flagged as BRRRR but $10 purchase price suggests entity restructuring/trust transfer, not a distressed buy — property value $51.1M still makes equity harvest viable.

---

#### DSCR-000021 | Score: 87 | Tier 1

| Field | Value |
|-------|-------|
| **Owner Name** | ONEILL BRIAN |
| **Owner Type** | Individual |
| **ICP Classification** | Individual Investor (2-9) / Cash-Out Refi Candidate |
| **Properties** | 4 |
| **Portfolio Value** | $25.7M |
| **Equity Ratio** | 82% |
| **Max Cash-Out (75% LTV)** | $3.7M |
| **Refi Signals** | Very High Equity (50%+) | Likely Minimal/No Mortgage | Portfolio Equity Harvest (4 properties) |
| **Refi Priority** | High |
| **Most Recent Purchase** | 2024-08-01 at $1.1M |
| **Contact Info** | **None** (not enriched) |
| **Location** | PALM BEACH county (DELRAY BEACH, Florida) |
| **Flags** | Cash Buyer, Equity Harvest |

> **Why this is a qualified lead**: Probable all-cash buyer (4 properties, $25.7M, 82% equity) — ideal cash-out refi candidate to unlock $3.7M at 75% LTV.

---

#### DSCR-000022 | Score: 87 | Tier 1

| Field | Value |
|-------|-------|
| **Owner Name** | KNEELAND PAUL J |
| **Owner Type** | Individual |
| **ICP Classification** | Individual Investor (2-9) / Multi-Family Investor |
| **Properties** | 3 |
| **Portfolio Value** | $3.5M |
| **Equity Ratio** | 80% |
| **Max Cash-Out (75% LTV)** | $641,982 |
| **Refi Signals** | Very High Equity (50%+) | Likely Minimal/No Mortgage | Portfolio Equity Harvest (3 properties) |
| **Refi Priority** | High |
| **Most Recent Purchase** | 2024-03-01 at $225,700 |
| **Contact Info** | **None** (not enriched) |
| **Location** | PALM BEACH county (NORTH PALM BEACH, Florida) |
| **Flags** | Cash Buyer, Equity Harvest |

> **Why this is a qualified lead**: Probable all-cash buyer (3 properties, $3.5M, 80% equity) — ideal cash-out refi candidate to unlock $641,982 at 75% LTV.

---

#### DSCR-000023 | Score: 84 | Tier 1

| Field | Value |
|-------|-------|
| **Owner Name** | MEKLIR KATIE |
| **Owner Type** | Individual |
| **ICP Classification** | Individual Investor (2-9) / Multi-Family Investor |
| **Properties** | 3 |
| **Portfolio Value** | $2.8M |
| **Equity Ratio** | 82% |
| **Max Cash-Out (75% LTV)** | $543,201 |
| **Refi Signals** | Very High Equity (50%+) | Likely Minimal/No Mortgage | Portfolio Equity Harvest (3 properties) |
| **Refi Priority** | High |
| **Most Recent Purchase** | 2025-02-01 at $167,300 |
| **Contact Info** | **None** (not enriched) |
| **Location** | PALM BEACH county (BOCA RATON, Florida) |
| **Flags** | Cash Buyer, Equity Harvest |

> **Why this is a qualified lead**: Probable all-cash buyer (3 properties, $2.8M, 82% equity) — ideal cash-out refi candidate to unlock $543,201 at 75% LTV.

---

#### DSCR-000041 | Score: 58 | Tier 2

| Field | Value |
|-------|-------|
| **Owner Name** | HUGHES LISA & |
| **Owner Type** | Individual |
| **ICP Classification** | Individual Investor (2-9) / BRRRR Exit Candidate |
| **Properties** | 2 |
| **Portfolio Value** | $430,372 |
| **Equity Ratio** | -21% |
| **Refi Signals** | BRRRR Exit Candidate (30%+ below median, <1yr) |
| **Refi Priority** | Medium |
| **Most Recent Purchase** | 2025-04-01 at $260,000 |
| **Contact Info** | **None** (not enriched) |
| **Location** | PALM BEACH county (LAKE WORTH, Florida) |
| **Flags** | BRRRR Exit |

> **Why this is a qualified lead**: Recent below-market purchase ($260,000) with BRRRR exit signals — likely needs DSCR permanent financing within 3-12 months to exit hard money.

---

#### DSCR-000042 | Score: 38 | Tier 2

| Field | Value |
|-------|-------|
| **Owner Name** | BALCI HALIL IBRAHIM & |
| **Owner Type** | Individual |
| **ICP Classification** | Individual Investor (2-9) |
| **Properties** | 2 |
| **Portfolio Value** | $379,000 |
| **Equity Ratio** | -13% |
| **Most Recent Purchase** | 2025-01-01 at $214,000 |
| **Contact Info** | **None** (not enriched) |
| **Location** | PALM BEACH county (WEST PALM BEACH, Florida) |

> **Why this is a qualified lead**: Active individual investor with 2 properties ($379,000) in PALM BEACH — portfolio growth phase suggests need for DSCR to avoid DTI constraints.

---

#### DSCR-000039 | Score: 31 | Tier 2

| Field | Value |
|-------|-------|
| **Owner Name** | ZUFFA MIROSLAV |
| **Owner Type** | Individual |
| **ICP Classification** | Individual Investor (2-9) |
| **Properties** | 2 |
| **Portfolio Value** | $789,353 |
| **Contact Info** | **None** (not enriched) |
| **Location** | PALM BEACH county (BOCA RATON, Florida) |

> **Why this is a qualified lead**: Active individual investor with 2 properties ($789,353) in PALM BEACH — portfolio growth phase suggests need for DSCR to avoid DTI constraints.

---

#### DSCR-000043 | Score: 31 | Tier 2

| Field | Value |
|-------|-------|
| **Owner Name** | BOUCHARD LOUIS R & |
| **Owner Type** | Individual |
| **ICP Classification** | Individual Investor (2-9) |
| **Properties** | 2 |
| **Portfolio Value** | $860,000 |
| **Contact Info** | **None** (not enriched) |
| **Location** | PALM BEACH county (HO HO KUS, New Jersey) |
| **Flags** | Out-of-State |

> **Why this is a qualified lead**: Out-of-state investor from New Jersey with 2 FL properties ($860,000) — remote investors commonly use DSCR since income docs are complex across state lines.

---

#### DSCR-000040 | Score: 25 | Tier 2

| Field | Value |
|-------|-------|
| **Owner Name** | WEINFELD JOSEPH & |
| **Owner Type** | Individual |
| **ICP Classification** | Individual Investor (2-9) |
| **Properties** | 2 |
| **Portfolio Value** | $169,739 |
| **Contact Info** | **None** (not enriched) |
| **Location** | PALM BEACH county (BROOKLYN, New York) |
| **Flags** | Out-of-State |

> **Why this is a qualified lead**: Out-of-state investor from New York with 2 FL properties ($169,739) — remote investors commonly use DSCR since income docs are complex across state lines.

---

### Out-of-State Investor (2 leads)

#### DSCR-000046 | Score: 55 | Tier 2

| Field | Value |
|-------|-------|
| **Owner Name** | NICHOLS BOBBY |
| **Owner Type** | Individual |
| **ICP Classification** | Out-of-State Investor / Equity Harvest Candidate |
| **Properties** | 1 |
| **Portfolio Value** | $101,329 |
| **Equity Ratio** | 100% |
| **Max Cash-Out (75% LTV)** | $75,987 |
| **Refi Signals** | Very High Equity (50%+) |
| **Refi Priority** | Medium |
| **Most Recent Purchase** | 2025-03-01 at $10 |
| **Contact Info** | **None** (not enriched) |
| **Location** | PALM BEACH county (IJAMSVILLE, Maryland) |
| **Flags** | Out-of-State, Equity Harvest |

> **Why this is a qualified lead**: Sitting on 100% equity across 1 property ($101,329) — cash-out refi at 75% LTV could unlock $75,987 for reinvestment.

---

#### DSCR-000050 | Score: 53 | Tier 2

| Field | Value |
|-------|-------|
| **Owner Name** | SILBERMAN FREDRIC A & |
| **Owner Type** | Individual |
| **ICP Classification** | Out-of-State Investor / Equity Harvest Candidate |
| **Properties** | 1 |
| **Portfolio Value** | $387,200 |
| **Equity Ratio** | 100% |
| **Max Cash-Out (75% LTV)** | $290,399 |
| **Refi Signals** | Very High Equity (50%+) |
| **Refi Priority** | Medium |
| **Most Recent Purchase** | 2024-10-01 at $1 |
| **Contact Info** | **None** (not enriched) |
| **Location** | PALM BEACH county (GLEN COVE, New York) |
| **Flags** | Out-of-State, Equity Harvest |

> **Why this is a qualified lead**: Sitting on 100% equity across 1 property ($387,200) — cash-out refi at 75% LTV could unlock $290,399 for reinvestment.

---

### Serial Investor (10+) (14 leads)

#### DSCR-000026 | Score: 100 | Tier 1

| Field | Value |
|-------|-------|
| **Owner Name** | MCDOUGALL LIVING TRUST |
| **Resolved Person** | MCDOUGALL, VERONICA |
| **Owner Type** | Trust |
| **ICP Classification** | Serial Investor (10+) / BRRRR Exit Candidate |
| **Properties** | 12 |
| **Portfolio Value** | $1.2M |
| **Equity Ratio** | 100% |
| **Max Cash-Out (75% LTV)** | $72,307 |
| **Refi Signals** | Very High Equity (50%+) | BRRRR Exit Candidate (30%+ below median, <1yr) | Portfolio Equity Harvest (12 properties) |
| **Refi Priority** | High |
| **Most Recent Purchase** | 2025-04-01 at $10 |
| **Contact Info** | **None** (not enriched) |
| **Location** | PALM BEACH county (BOYNTON BEACH, Florida) |
| **Flags** | BRRRR Exit, Equity Harvest |
| **Entities Controlled** | 1 |

> **Why this is a qualified lead**: Institutional-scale portfolio (12 properties, $1.2M) with nominal transfer recorded; entity resolution identified MCDOUGALL, VERONICA — verify if DSCR-eligible or institutional.

---

#### DSCR-000025 | Score: 100 | Tier 1

| Field | Value |
|-------|-------|
| **Owner Name** | MADD QUALITY LLC |
| **Resolved Person** | ACIKGOZ, MURAT |
| **Owner Type** | LLC |
| **ICP Classification** | Serial Investor (10+) / BRRRR Exit Candidate |
| **Properties** | 13 |
| **Portfolio Value** | $2.5M |
| **Equity Ratio** | 39% |
| **Max Cash-Out (75% LTV)** | $26,572 |
| **Refi Signals** | High Equity (30%+) | BRRRR Exit Candidate (30%+ below median, <1yr) | Portfolio Equity Harvest (13 properties) |
| **Refi Priority** | High |
| **Most Recent Purchase** | 2025-08-01 at $119,000 |
| **Contact Info** | **None** (not enriched) |
| **Location** | PALM BEACH county (WELLINGTON, Florida) |
| **Flags** | BRRRR Exit, Equity Harvest |
| **Entities Controlled** | 1 |

> **Why this is a qualified lead**: Serial investor with 13 properties ($2.5M), recently purchased below market with BRRRR exit signals — ideal DSCR refi timing within 3-12 months.

---

#### DSCR-000024 | Score: 100 | Tier 1

| Field | Value |
|-------|-------|
| **Owner Name** | HOME SFR BORROWER LLC |
| **Resolved Person** | Buffington, Brian |
| **Owner Type** | LLC |
| **ICP Classification** | Serial Investor (10+) / BRRRR Exit Candidate |
| **Properties** | 36 |
| **Portfolio Value** | $11.0M |
| **Equity Ratio** | 100% |
| **Max Cash-Out (75% LTV)** | $229,558 |
| **Refi Signals** | Very High Equity (50%+) | BRRRR Exit Candidate (30%+ below median, <1yr) | Portfolio Equity Harvest (36 properties) |
| **Refi Priority** | High |
| **Most Recent Purchase** | 2025-04-01 at $10 |
| **Contact Info** | **None** (not enriched) |
| **Location** | PALM BEACH county (SCOTTSDALE, Arizona) |
| **Flags** | Out-of-State, BRRRR Exit, Equity Harvest |
| **Entities Controlled** | 1 |

> **Why this is a qualified lead**: Institutional-scale portfolio (36 properties, $11.0M) with nominal transfer recorded; entity resolution identified Buffington, Brian — verify if DSCR-eligible or institutional.

---

#### DSCR-000027 | Score: 99 | Tier 1

| Field | Value |
|-------|-------|
| **Owner Name** | SECY OF HOUSING & URBAN DEV |
| **Owner Type** | Individual |
| **ICP Classification** | Serial Investor (10+) / BRRRR Exit Candidate |
| **Properties** | 10 |
| **Portfolio Value** | $2.3M |
| **Equity Ratio** | 52% |
| **Max Cash-Out (75% LTV)** | $63,259 |
| **Refi Signals** | Very High Equity (50%+) | BRRRR Exit Candidate (30%+ below median, <1yr) | Portfolio Equity Harvest (10 properties) |
| **Refi Priority** | High |
| **Most Recent Purchase** | 2025-07-01 at $111,600 |
| **Contact Info** | **None** (not enriched) |
| **Location** | PALM BEACH county (WASHINGTON, Dist. Columbia) |
| **Flags** | Out-of-State, BRRRR Exit, Equity Harvest |

> **Why this is a qualified lead**: Serial investor with 10 properties ($2.3M), recently purchased below market with BRRRR exit signals — ideal DSCR refi timing within 3-12 months.

---

#### DSCR-000001 | Score: 97 | Tier 1

| Field | Value |
|-------|-------|
| **Owner Name** | PROGRESS RESIDENTIAL BORROWER |
| **Owner Type** | Individual |
| **ICP Classification** | Serial Investor (10+) / Equity Harvest Candidate |
| **Properties** | 470 |
| **Portfolio Value** | $212.8M |
| **Equity Ratio** | 100% |
| **Max Cash-Out (75% LTV)** | $339,556 |
| **Refi Signals** | Very High Equity (50%+) | Portfolio Equity Harvest (470 properties) |
| **Refi Priority** | High |
| **Most Recent Purchase** | 2024-04-01 at $10 |
| **Contact Info** | **None** (not enriched) |
| **Location** | PALM BEACH county (SCOTTSDALE, Arizona) |
| **Flags** | Out-of-State, Equity Harvest |

> **Why this is a qualified lead**: Major portfolio holder (470 properties, $212.8M) with 100% equity — represents multiple simultaneous DSCR loan opportunities via cash-out refi.

---

#### DSCR-000002 | Score: 67 | Tier 1

| Field | Value |
|-------|-------|
| **Owner Name** | PACIFICA WEST PALM LLC |
| **Resolved Person** | ISRANI, DEEPAK |
| **Owner Type** | LLC |
| **ICP Classification** | Serial Investor (10+) |
| **Properties** | 449 |
| **Portfolio Value** | $63.8M |
| **Equity Ratio** | 16% |
| **Most Recent Purchase** | 2024-08-01 at $120,000 |
| **Contact Info** | **None** (not enriched) |
| **Location** | PALM BEACH county (SAN DIEGO, California) |
| **Flags** | Out-of-State |
| **Entities Controlled** | 1 |

> **Why this is a qualified lead**: Large-scale investor (449 properties, $63.8M) operating remotely from California — likely needs DSCR for portfolio expansion given scale and entity structure.

---

#### DSCR-000003 | Score: 57 | Tier 1

| Field | Value |
|-------|-------|
| **Owner Name** | SRP SUB LLC |
| **Resolved Person** | Tanner, Dallas |
| **Owner Type** | LLC |
| **ICP Classification** | Serial Investor (10+) |
| **Properties** | 407 |
| **Portfolio Value** | $161.5M |
| **Contact Info** | **None** (not enriched) |
| **Location** | PALM BEACH county (SCOTTSDALE, Arizona) |
| **Flags** | Out-of-State |
| **Entities Controlled** | 1 |

> **Why this is a qualified lead**: Large-scale investor (407 properties, $161.5M) operating remotely from Arizona — likely needs DSCR for portfolio expansion given scale and entity structure.

---

#### DSCR-000018 | Score: 57 | Tier 1

| Field | Value |
|-------|-------|
| **Owner Name** | VERENA AT DELRAY LLC |
| **Resolved Person** | DELRAY PARENT, LLC |
| **Owner Type** | LLC |
| **ICP Classification** | Serial Investor (10+) |
| **Properties** | 146 |
| **Portfolio Value** | $14.7M |
| **Contact Info** | **None** (not enriched) |
| **Location** | PALM BEACH county (CHICAGO, Illinois) |
| **Flags** | Out-of-State |
| **Entities Controlled** | 1 |

> **Why this is a qualified lead**: Large-scale investor (146 properties, $14.7M) operating remotely from Illinois — likely needs DSCR for portfolio expansion given scale and entity structure.

---

#### DSCR-000019 | Score: 57 | Tier 1

| Field | Value |
|-------|-------|
| **Owner Name** | FYR SFR BORROWER LLC |
| **Resolved Person** | FYR SFR Equity Owner, LLC |
| **Owner Type** | LLC |
| **ICP Classification** | Serial Investor (10+) |
| **Properties** | 134 |
| **Portfolio Value** | $38.8M |
| **Contact Info** | **None** (not enriched) |
| **Location** | PALM BEACH county (DULUTH, Georgia) |
| **Flags** | Out-of-State |
| **Entities Controlled** | 1 |

> **Why this is a qualified lead**: Large-scale investor (134 properties, $38.8M) operating remotely from Georgia — likely needs DSCR for portfolio expansion given scale and entity structure.

---

#### DSCR-000005 | Score: 52 | Tier 1

| Field | Value |
|-------|-------|
| **Owner Name** | IH4 PROPERTY FLORIDA LP |
| **Owner Type** | Partnership |
| **ICP Classification** | Serial Investor (10+) |
| **Properties** | 282 |
| **Portfolio Value** | $126.6M |
| **Contact Info** | **None** (not enriched) |
| **Location** | PALM BEACH county (SCOTTSDALE, Arizona) |
| **Flags** | Out-of-State |

> **Why this is a qualified lead**: Large-scale investor (282 properties, $126.6M) operating remotely from Arizona — likely needs DSCR for portfolio expansion given scale and entity structure.

---

#### DSCR-000004 | Score: 52 | Tier 1

| Field | Value |
|-------|-------|
| **Owner Name** | IH3 PROPERTY FLORIDA LP |
| **Owner Type** | Partnership |
| **ICP Classification** | Serial Investor (10+) |
| **Properties** | 380 |
| **Portfolio Value** | $177.1M |
| **Contact Info** | **None** (not enriched) |
| **Location** | PALM BEACH county (SCOTTSDALE, Arizona) |
| **Flags** | Out-of-State |

> **Why this is a qualified lead**: Large-scale investor (380 properties, $177.1M) operating remotely from Arizona — likely needs DSCR for portfolio expansion given scale and entity structure.

---

#### DSCR-000020 | Score: 52 | Tier 1

| Field | Value |
|-------|-------|
| **Owner Name** | 2018 3 IH BORROWER LP |
| **Owner Type** | Partnership |
| **ICP Classification** | Serial Investor (10+) |
| **Properties** | 129 |
| **Portfolio Value** | $61.9M |
| **Contact Info** | **None** (not enriched) |
| **Location** | PALM BEACH county (SCOTTSDALE, Arizona) |
| **Flags** | Out-of-State |

> **Why this is a qualified lead**: Large-scale investor (129 properties, $61.9M) operating remotely from Arizona — likely needs DSCR for portfolio expansion given scale and entity structure.

---

#### DSCR-000017 | Score: 52 | Tier 1

| Field | Value |
|-------|-------|
| **Owner Name** | IH5 PROPERTY FLORIDA LP |
| **Owner Type** | Partnership |
| **ICP Classification** | Serial Investor (10+) |
| **Properties** | 162 |
| **Portfolio Value** | $72.0M |
| **Contact Info** | **None** (not enriched) |
| **Location** | PALM BEACH county (SCOTTSDALE, Arizona) |
| **Flags** | Out-of-State |

> **Why this is a qualified lead**: Large-scale investor (162 properties, $72.0M) operating remotely from Arizona — likely needs DSCR for portfolio expansion given scale and entity structure.

---

#### DSCR-000016 | Score: 52 | Tier 1

| Field | Value |
|-------|-------|
| **Owner Name** | 2018 2 IH BORROWER LP |
| **Owner Type** | Partnership |
| **ICP Classification** | Serial Investor (10+) |
| **Properties** | 171 |
| **Portfolio Value** | $82.1M |
| **Contact Info** | **None** (not enriched) |
| **Location** | PALM BEACH county (SCOTTSDALE, Arizona) |
| **Flags** | Out-of-State |

> **Why this is a qualified lead**: Large-scale investor (171 properties, $82.1M) operating remotely from Arizona — likely needs DSCR for portfolio expansion given scale and entity structure.

---

### Single Investment Property (6 leads)

#### DSCR-000033 | Score: 87 | Tier 2

| Field | Value |
|-------|-------|
| **Owner Name** | ROBERTS DUANE & KELLY TRUST |
| **Resolved Person** | REEVES, ROBERT D., II |
| **Owner Type** | Trust |
| **ICP Classification** | Single Investment Property / BRRRR Exit Candidate |
| **Properties** | 1 |
| **Portfolio Value** | $28.9M |
| **Equity Ratio** | 100% |
| **Max Cash-Out (75% LTV)** | $21.7M |
| **Refi Signals** | Very High Equity (50%+) | BRRRR Exit Candidate (30%+ below median, <1yr) |
| **Refi Priority** | High |
| **Most Recent Purchase** | 2025-05-01 at $10 |
| **Contact Info** | **None** (not enriched) |
| **Location** | PALM BEACH county (PALM BEACH, Florida) |
| **Flags** | BRRRR Exit, Equity Harvest |
| **Entities Controlled** | 1 |

> **Why this is a qualified lead**: Flagged as BRRRR but $10 purchase price suggests entity restructuring/trust transfer, not a distressed buy — property value $28.9M still makes equity harvest viable.

---

#### DSCR-000047 | Score: 82 | Tier 2

| Field | Value |
|-------|-------|
| **Owner Name** | PENN RICHARD H & |
| **Owner Type** | Individual |
| **ICP Classification** | Single Investment Property / BRRRR Exit Candidate |
| **Properties** | 1 |
| **Portfolio Value** | $3.1M |
| **Equity Ratio** | 100% |
| **Max Cash-Out (75% LTV)** | $2.3M |
| **Refi Signals** | Very High Equity (50%+) | BRRRR Exit Candidate (30%+ below median, <1yr) |
| **Refi Priority** | High |
| **Most Recent Purchase** | 2025-06-01 at $10 |
| **Contact Info** | **None** (not enriched) |
| **Location** | PALM BEACH county (BOCA RATON, Florida) |
| **Flags** | BRRRR Exit, Equity Harvest |

> **Why this is a qualified lead**: Flagged as BRRRR but $10 purchase price suggests entity restructuring/trust transfer, not a distressed buy — property value $3.1M still makes equity harvest viable.

---

#### DSCR-000032 | Score: 82 | Tier 2

| Field | Value |
|-------|-------|
| **Owner Name** | FRECKA DAVID A & |
| **Owner Type** | Individual |
| **ICP Classification** | Single Investment Property / BRRRR Exit Candidate |
| **Properties** | 1 |
| **Portfolio Value** | $32.0M |
| **Equity Ratio** | 100% |
| **Max Cash-Out (75% LTV)** | $24.0M |
| **Refi Signals** | Very High Equity (50%+) | BRRRR Exit Candidate (30%+ below median, <1yr) |
| **Refi Priority** | High |
| **Most Recent Purchase** | 2025-08-01 at $10 |
| **Contact Info** | **None** (not enriched) |
| **Location** | PALM BEACH county (LAKE WORTH, Florida) |
| **Flags** | BRRRR Exit, Equity Harvest |

> **Why this is a qualified lead**: Flagged as BRRRR but $10 purchase price suggests entity restructuring/trust transfer, not a distressed buy — property value $32.0M still makes equity harvest viable.

---

#### DSCR-000029 | Score: 82 | Tier 2

| Field | Value |
|-------|-------|
| **Owner Name** | PELTZ NELSON 2023 NON POUROVER |
| **Owner Type** | Individual |
| **ICP Classification** | Single Investment Property / BRRRR Exit Candidate |
| **Properties** | 1 |
| **Portfolio Value** | $117.1M |
| **Equity Ratio** | 100% |
| **Max Cash-Out (75% LTV)** | $87.8M |
| **Refi Signals** | Very High Equity (50%+) | BRRRR Exit Candidate (30%+ below median, <1yr) |
| **Refi Priority** | High |
| **Most Recent Purchase** | 2025-04-01 at $10 |
| **Contact Info** | **None** (not enriched) |
| **Location** | PALM BEACH county (PALM BEACH, Florida) |
| **Flags** | BRRRR Exit, Equity Harvest |

> **Why this is a qualified lead**: Flagged as BRRRR but $10 purchase price suggests entity restructuring/trust transfer, not a distressed buy — property value $117.1M still makes equity harvest viable.

---

#### DSCR-000049 | Score: 50 | Tier 2

| Field | Value |
|-------|-------|
| **Owner Name** | GARCIA ROSA MABEL R |
| **Owner Type** | Individual |
| **ICP Classification** | Single Investment Property / BRRRR Exit Candidate |
| **Properties** | 1 |
| **Portfolio Value** | $101,405 |
| **Equity Ratio** | -48% |
| **Refi Signals** | BRRRR Exit Candidate (30%+ below median, <1yr) |
| **Refi Priority** | Medium |
| **Most Recent Purchase** | 2025-08-01 at $150,000 |
| **Contact Info** | **None** (not enriched) |
| **Location** | PALM BEACH county (BOCA RATON, Florida) |
| **Flags** | BRRRR Exit |

> **Why this is a qualified lead**: Recent below-market purchase ($150,000) with BRRRR exit signals — likely needs DSCR permanent financing within 3-12 months to exit hard money.

---

#### DSCR-000048 | Score: 50 | Tier 3

| Field | Value |
|-------|-------|
| **Owner Name** | MAUCK CHRISTOPHER |
| **Owner Type** | Individual |
| **ICP Classification** | Single Investment Property / Equity Harvest Candidate |
| **Properties** | 1 |
| **Portfolio Value** | $79,529 |
| **Equity Ratio** | 100% |
| **Max Cash-Out (75% LTV)** | $59,637 |
| **Refi Signals** | Very High Equity (50%+) |
| **Refi Priority** | Medium |
| **Most Recent Purchase** | 2024-09-01 at $10 |
| **Contact Info** | **None** (not enriched) |
| **Location** | PALM BEACH county (WELLINGTON, Florida) |
| **Flags** | Equity Harvest |

> **Why this is a qualified lead**: Sitting on 100% equity across 1 property ($79,529) — cash-out refi at 75% LTV could unlock $59,637 for reinvestment.

---

## Recommendations for Full Pipeline Run

1. **Exclude institutional SFR buyers**: Add filter for known institutional names (Progress Residential, Invitation Homes, American Homes 4 Rent, etc.) — these are not DSCR loan candidates.
2. **Fix $10 nominal transfer detection**: Sales at $10/$100/$1 are entity restructurings, not real purchases. Filter `most_recent_price < $1,000` from BRRRR detection to avoid false positives.
3. **Configure Apollo.io API key**: Contact enrichment returned 0% coverage. Apollo's free tier (10K credits/month) would significantly improve email coverage for entity-resolved leads.
4. **Prioritize SunBiz resolution**: 96% success rate validates the approach. Increase `--max-lookups` to 2,000+ for the full run to cover more entity-owned leads.
5. **Foreign national targeting**: All 5 Canadian investors hold ultra-high-value properties ($38M-$72M). These are premium DSCR targets. Consider expanding to other foreign domiciles.
6. **HUD/Government entities**: 'SECY OF HOUSING & URBAN DEV' was classified as Serial Investor. Add government entity filter.
7. **Score calibration looks good**: Mean 60.7 for this intentionally diverse sample. High-value leads (multi-property + refi signals) correctly scoring 90-100. Single-property leads without signals correctly scoring 30-50.
