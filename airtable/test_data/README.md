# Test Data — Expected Results

Upload in order: Investors → Entities → Properties → Financing

## 7 Test Investors
| Investor | Properties | Key Trait |
|----------|-----------|-----------|
| Carlos Rivera | 2 (SFR + Duplex) | Mid-portfolio, conventional loans, stable |
| Jennifer Wu | 2 (SFR + Condo) | Has a HARD MONEY loan — top trigger |
| Marcus Thompson | 1 (SFR) | Recent cash purchase (no entity), hard money |
| David Goldstein | 2 (Condo + Fourplex) | Largest portfolio value, 2 entities, high rate + hard money |
| Natasha Petrov | 2 (SFR + SFR) | Recent cash purchase + private money loan |
| Robert Chen | 0 | New lead, no properties yet — tests empty scoring |
| Angela Martinez | 1 (Condo) | Small portfolio, conventional, low triggers |

## 6 Test Entities
| Entity | Owner | Properties |
|--------|-------|-----------|
| Rivera Investments LLC | Carlos Rivera | 2 |
| Suncoast Capital Partners LLC | Jennifer Wu | 2 |
| WPB Holdings Trust | David Goldstein | 1 |
| Palm Beach Capital Group LLC | David Goldstein | 1 |
| Broward Holdings Inc | Angela Martinez | 1 |
| Petrov Property Group LLC | Natasha Petrov | 2 |

## 10 Test Properties
Mix of SFR, Duplex, Condo, Fourplex across Palm Beach and Broward counties.
- 2 vacant properties (recent purchases, testing cash purchase trigger)
- 8 tenant-occupied with rental income (testing DSCR calculations)

## 10 Test Financing Records — Expected Triggers

| Loan ID | Lender | Type | Rate | Maturity | Expected Triggers |
|---------|--------|------|------|----------|-------------------|
| LOAN-001 | Wells Fargo | Conventional | 4.5% | 2049 | None — clean conventional |
| LOAN-002 | Chase | Conventional | 5.25% | 2050 | None — clean conventional |
| LOAN-003 | Lima One Capital | **Hard Money** | **11.5%** | **2026-11** | 🚨 Hard Money + 🚨 High Rate + 🚨 Maturity + 🚨 Balloon = **4 triggers** |
| LOAN-004 | BofA | Conventional | 3.75% | 2051 | None — clean, low rate |
| LOAN-005 | Velocity | DSCR | **7.8%** | 2052 | 🚨 High Rate (>7%) = **1 trigger** |
| LOAN-006 | NY Private Lending | **Hard Money** | **12%** | **2027-01** | 🚨 Hard Money + 🚨 High Rate + 🚨 Maturity + 🚨 Balloon = **4 triggers** |
| LOAN-007 | Kiavi | **Hard Money** | **10.5%** | **2026-09** | 🚨 Hard Money + 🚨 High Rate + 🚨 Maturity = **3 triggers** |
| LOAN-008 | PNC | Conventional | 4.25% | 2049 | None — clean conventional |
| LOAN-009 | Visio | DSCR | 7.2% | 2052 | 🚨 High Rate (>7%) = **1 trigger** |
| LOAN-010 | Private Lender | **Private Money** | **9.5%** | **2027-11** | 🚨 High Rate + 🚨 Maturity + 🚨 Balloon = **3 triggers** (note: not flagged as hard money since loan type is "Private Money" not a hard money keyword) |

## Expected Lead Scores (approximate)

| Investor | Property Count | Hard Money | Triggers | Recent Purchase | Equity | Expected Tier |
|----------|---------------|------------|----------|-----------------|--------|---------------|
| David Goldstein | 2 (10 pts) | 1 (5 pts) | 5+ (25 pts) | 0 | High (9-12 pts) | 🔥 Tier 1 or ⭐ Tier 2 |
| Jennifer Wu | 2 (10 pts) | 1 (5 pts) | 4 (25 pts) | 0 | Medium (6-9 pts) | ⭐ Tier 2 |
| Natasha Petrov | 2 (10 pts) | 0 | 3-4 (20-25 pts) | 1 (10 pts) | Medium (6-9 pts) | ⭐ Tier 2 |
| Marcus Thompson | 1 (5 pts) | 1 (5 pts) | 3 (20 pts) | 0 | Low (0-3 pts) | 📋 Tier 3 |
| Carlos Rivera | 2 (10 pts) | 0 | 0 | 0 | Medium (6-9 pts) | ⬜ Low Priority |
| Angela Martinez | 1 (5 pts) | 0 | 0 | 0 | Low (3-6 pts) | ⬜ Low Priority |
| Robert Chen | 0 | 0 | 0 | 0 | 0 | ⬜ Low Priority |

## What To Validate After Upload

1. **Financing triggers:** LOAN-003, LOAN-006, LOAN-007 should show Hard Money Flag. LOAN-003/005/006/007/009/010 should show High Rate Flag.
2. **Properties rollups:** Total Property Debt, Estimated Equity, DSCR calculations should populate.
3. **Cash purchases:** Marcus Thompson's property (78 NE 4th Ave, purchased 2025-08-30 for $495K with no rent) and Natasha Petrov's second property should flag.
4. **Investors rollups:** Property Count, Total Portfolio Value, Hard Money Loan Count should chain up.
5. **Lead scoring:** David Goldstein and Jennifer Wu should score highest. Robert Chen should score 0.
6. **Automations:** If turned on, LOAN-003, LOAN-006, LOAN-007 should auto-create Opportunities.

## Important Notes on CSV Formatting
- Interest rates are decimals (0.045 = 4.5%) — Airtable percent fields expect this
- Currency values have no $ sign or commas — just numbers
- Dates are YYYY-MM-DD format
- Booleans are TRUE/FALSE for checkbox fields
- "Property" column in financing CSV should match the Property Address value exactly for linking
