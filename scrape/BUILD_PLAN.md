# BUILD_PLAN.md — Development Blueprint

## Goal

Build a full investor intelligence platform that produces comprehensive
dossiers on Florida real estate investors, starting with a 25-record
proof of concept in Palm Beach and Broward counties.

## Where We Are Now

### Built and Working
- [x] FDOR NAL download + parse (scripts 01-02)
- [x] ICP scoring + filtering (script 03)
- [x] SunBiz LLC resolution (script 04)
- [x] Basic contact enrichment with research tracker (script 05/05b)
- [x] Contact validation framework (script 06)
- [x] Campaign export framework (script 07)
- [x] 39,353 leads loaded from existing pipeline
- [x] Top 25 PB/Broward leads identified
- [x] Apollo API key configured

### Not Built Yet
- [ ] Apollo.io API enrichment (script 10)
- [ ] County clerk mortgage scraping (script 11)
- [ ] FDOR SDF purchase history (script 12)
- [ ] Rental estimates (script 13)
- [ ] Wealth signals (script 14)
- [ ] Network mapping (script 15)
- [ ] Life events (script 16)
- [ ] Dossier assembly (script 20)
- [ ] Opportunity score rewrite (uses financing data)

---

## The Plan

### Milestone 1: Contact Intelligence (get the person)
**Goal:** For 25 leads, resolve LLC → person and get validated phone + email + LinkedIn.
**Success:** 80%+ person resolution, 70%+ valid phone, 50%+ email, 40%+ LinkedIn.

| Step | Script | What | Depends On | Status |
|------|--------|------|------------|--------|
| 1.1 | 05 | Select top 25 PB/Broward leads | Existing pipeline data | Done |
| 1.2 | 05 | SunBiz resolve all 25 LLCs (with --counties flag) | 1.1 | Ready to run |
| 1.3 | 10 | Apollo enrichment for resolved names | 1.2, API key | To build |
| 1.4 | 05b | Merge Apollo + SunBiz + DBPR data | 1.3 | Built, needs update for Apollo |
| 1.5 | 06 | Validate phones (Twilio) + emails (MillionVerifier) | 1.4, API keys | Built |
| 1.6 | — | **CHECKPOINT: Review results, measure hit rates** | 1.5 | — |

**Decision gate after 1.6:**
- If hit rates meet targets → proceed to Milestone 2
- If Apollo hit rates are low → try Datazapp as fallback, adjust approach
- If SunBiz resolution is low → investigate why, adjust search logic

---

### Milestone 2: Portfolio Intelligence (understand what they own)
**Goal:** For each lead, build complete property-level portfolio with values, types, and ownership structure.
**Success:** 100% of properties mapped with value, type, and ownership for each lead.

| Step | Script | What | Depends On | Status |
|------|--------|------|------------|--------|
| 2.1 | — | Verify FDOR NAL data has per-property detail for all 25 leads | Existing data | Check |
| 2.2 | — | Build per-property view (not aggregated by owner) | 2.1 | To build |
| 2.3 | — | Property type mix breakdown per portfolio | 2.2 | Derivable |
| 2.4 | — | Ownership structure (which LLC owns which property) | 2.2 + SunBiz | Cross-reference |
| 2.5 | — | **CHECKPOINT: Portfolio accuracy review** | 2.4 | — |

**Note:** Most of this data is already in the FDOR NAL — we just aggregated it
in step 02. We need the per-property detail, not just the rollup.

---

### Milestone 3: Financing Intelligence (understand their debt)
**Goal:** For each property, identify mortgages, lenders, and calculate debt/equity.
**Success:** Mortgage data found for 60%+ of properties, lender classification working.

| Step | Script | What | Depends On | Status |
|------|--------|------|------------|--------|
| 3.1 | 11 | Research PB County Clerk search portal (understand the interface) | — | To do |
| 3.2 | 11 | Research Broward Clerk search portal | — | To do |
| 3.3 | 11 | Build scraper for PB clerk: search by parcel → extract mortgages | 3.1 | To build |
| 3.4 | 11 | Build scraper for Broward clerk | 3.2 | To build |
| 3.5 | 11 | Parse mortgage data: lender, amount, date, doc type | 3.3/3.4 | To build |
| 3.6 | 11 | Classify lenders (bank, credit union, hard money, private) | 3.5, config | To build |
| 3.7 | 11 | Calculate: est balance, LTV, maturity date, est rate | 3.5 | To build |
| 3.8 | 11 | Identify: hard money exposure, balloon maturities, high-rate loans | 3.7 | Derivable |
| 3.9 | — | **CHECKPOINT: Financing data accuracy review** | 3.8 | — |

**This is the hardest technical milestone.** County clerk portals vary widely
in how they work. Steps 3.1 and 3.2 are pure research — we need to understand
the search interface, HTML structure, and any anti-bot measures before writing code.

**Decision gate after 3.9:**
- If clerk scraping works → this is our biggest competitive advantage
- If clerk portals block scraping → investigate bulk data requests or alternative sources

---

### Milestone 4: Purchase History (understand their behavior)
**Goal:** Full acquisition timeline showing buy/sell patterns, flip vs hold, cash vs financed.
**Success:** Purchase history for 90%+ of leads.

| Step | Script | What | Depends On | Status |
|------|--------|------|------------|--------|
| 4.1 | 12 | Download FDOR SDF files for PB + Broward | — | To build |
| 4.2 | 12 | Parse SDF: extract all sales per parcel | 4.1 | To build |
| 4.3 | 12 | Match sales to leads (by owner name or parcel ID) | 4.2 | To build |
| 4.4 | 12 | Classify: flip vs hold, cash vs financed (cross-ref M3) | 4.3 + M3 | Derivable |
| 4.5 | 12 | Calculate: frequency, avg price, last 12/36 mo activity | 4.3 | Derivable |
| 4.6 | — | **CHECKPOINT: Purchase history accuracy review** | 4.5 | — |

---

### Milestone 5: Rental & Market Intelligence
**Goal:** Estimate rental income, identify STR presence, map market positioning.
**Success:** Rent estimate for 90%+ of properties, STR detection for tourist markets.

| Step | Script | What | Depends On | Status |
|------|--------|------|------------|--------|
| 5.1 | 13 | Download HUD Fair Market Rent tables | — | To build |
| 5.2 | 13 | Match properties to FMR by zip + bedroom count | 5.1 + M2 | To build |
| 5.3 | 13 | Calculate: portfolio gross rent, est NOI, portfolio DSCR | 5.2 + M3 | Derivable |
| 5.4 | 13 | STR listing detection (Airbnb/VRBO by address) | M2 | To build (careful) |
| 5.5 | — | Market positioning: geography breakdown per investor | M2 | Derivable |
| 5.6 | — | **CHECKPOINT: Rental estimate accuracy review** | 5.3 | — |

---

### Milestone 6: Wealth & Life Event Signals
**Goal:** Add wealth indicators and urgency signals.
**Success:** At least one wealth signal for 30%+ of leads, life events detected where they exist.

| Step | Script | What | Depends On | Status |
|------|--------|------|------------|--------|
| 6.1 | 14 | FEC.gov: political donation lookup | M1 (need person name) | To build |
| 6.2 | 14 | ProPublica: IRS 990 nonprofit search | M1 | To build |
| 6.3 | 14 | SunBiz reverse: all LLCs per person | M1 | To build |
| 6.4 | 16 | County clerk: liens, lis pendens, probate | M3 (reuse clerk scraper) | To build |
| 6.5 | — | **CHECKPOINT: Signal accuracy review** | 6.4 | — |

---

### Milestone 7: Network Mapping
**Goal:** Identify shared connections across leads (co-investors, PMs, agents, lenders).
**Success:** At least 20% of leads connected to another lead or shared service provider.

| Step | Script | What | Depends On | Status |
|------|--------|------|------------|--------|
| 7.1 | 15 | Cross-reference SunBiz officers across all leads | M1 | To build |
| 7.2 | 15 | Cross-reference lenders across leads | M3 | To build |
| 7.3 | 15 | DBPR PM license → property address matching | M2 | To build |
| 7.4 | 15 | Build relationship graph | 7.1-7.3 | To build |
| 7.5 | — | **CHECKPOINT: Network map review** | 7.4 | — |

---

### Milestone 8: Dossier Assembly & Opportunity Scoring
**Goal:** Assemble everything into final investor profiles with scoring.
**Success:** Complete dossier for each lead, opportunity score that correctly ranks leads.

| Step | Script | What | Depends On | Status |
|------|--------|------|------------|--------|
| 8.1 | 20 | Merge all data sources into single investor profile | M1-M7 | To build |
| 8.2 | 20 | Rewrite opportunity score using financing intelligence | M3 | To build |
| 8.3 | 20 | Generate multi-tab Excel dossier | 8.1 | To build |
| 8.4 | 20 | Generate per-investor one-pager (for sales calls) | 8.1 | To build |
| 8.5 | — | **FINAL CHECKPOINT: Full dossier review with Frank** | 8.4 | — |

---

### Milestone 9: Scale to Full County
**Goal:** Run the complete pipeline on all 7,537 PB/Broward leads.
**Success:** Dossiers generated at scale, campaign-ready exports working.

| Step | What | Depends On |
|------|------|------------|
| 9.1 | Run M1-M8 on full PB/Broward dataset | All milestones validated on 25 |
| 9.2 | Monitor API costs and rate limits at scale | 9.1 |
| 9.3 | Generate campaign-ready exports | 9.2 |
| 9.4 | Hand off to Frank for outreach testing | 9.3 |

---

## Dependency Graph

```
M1 Contact ──────┬──→ M6 Wealth/Events
                  │
M2 Portfolio ─────┼──→ M5 Rental/Market ──→ M8 Dossier + Score
                  │
M3 Financing ─────┼──→ M7 Network
                  │
M4 History ───────┘
```

M1 (Contact) is the prerequisite for everything — you need person names first.
M2 (Portfolio) and M3 (Financing) can run in parallel after M1.
M4 (History) can run in parallel with M2/M3.
M5-M7 depend on earlier milestones.
M8 assembles everything.

---

## Current Priority

**→ We are starting Milestone 1, Step 1.2**

Next actions:
1. Run script 05 without --skip-sunbiz to resolve all 25 LLCs
2. Build and run script 10 (Apollo enrichment)
3. Merge results and validate
4. Checkpoint: measure hit rates against targets

---

## Risk Register

| Risk | Impact | Mitigation |
|------|--------|-----------|
| County clerk portals block scraping | Lose financing intelligence (M3) | Try bulk data request, different scraping approach, or paid data source |
| Apollo hit rates low for LLC officers | Low email/LinkedIn coverage | Datazapp fallback, manual research for top leads |
| SunBiz blocks us at scale (7K+ lookups) | Can't resolve all LLCs | Batch over multiple days, use SunBiz bulk FTP data |
| FDOR SDF doesn't have enough history | Weak purchase history | Supplement with county clerk deed recordings |
| Airbnb/VRBO block listing scrapes | No STR revenue estimates | Use DBPR license data + HUD FMR as proxy |
