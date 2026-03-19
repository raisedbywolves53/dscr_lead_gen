# DSCR Lead Intelligence — Business Plan & GTM Roadmap

**Still Mind Creative | March 2026 | DRAFT FOR REVIEW**

---

## 1. What We're Selling

We produce investor intelligence dossiers from public property records and commercial enrichment sources. Each dossier contains up to 157 data points per lead, covering property details, financing intelligence, ownership resolution, contact information, DSCR scoring, and suggested outreach angles.

The data costs us roughly **$0.02–0.13 per lead to produce** (depending on enrichment depth). The market sells far less enriched leads for **$15–100+ each**. Our moat is the assembly — no single vendor produces this output. It requires stitching together 7+ data sources, scoring against a proprietary ICP matrix, and packaging for specific buyer types.

### What Makes Ours Different

| Feature | Generic Lead Vendor | PropStream DIY | Our Product |
|---------|-------------------|----------------|-------------|
| Property data | Basic | Full | Full |
| Financing intelligence (lender, rate, maturity) | No | Partial | Full (ATTOM 7-endpoint) |
| AVM + rental estimates | No | Partial | Full (property-specific) |
| Entity resolution (LLC → person) | No | No | Yes (SunBiz/SoS) |
| Skip-traced + validated contact | Sometimes | No (separate sub) | Yes (Tracerfy + MillionVerifier + Twilio) |
| DSCR-specific scoring | No | No | Yes (11-segment ICP matrix, 0–100) |
| Outreach angle per lead | No | No | Yes |
| DNC/TCPA scrubbed | Sometimes | No | Yes |
| Building permits (BRRRR signals) | No | No | Yes (ATTOM) |
| Sales history (acquisition velocity) | No | Partial | Full (10-year + cash/mortgage flag) |
| Compliance one-pager included | No | No | Yes |

---

## 2. Pipeline Status — What We Actually Have Today

### Florida (Palm Beach + Broward)

| Item | Status | Detail |
|------|--------|--------|
| Raw property data (FDOR NAL) | ✅ Complete | 654,538 Broward parcels + PB |
| Parsed + scored | ✅ Complete | 7,537 qualified investment properties |
| Entity resolution (SunBiz) | ✅ Complete | LLC/Corp → officers/registered agents |
| Skip trace (Tracerfy) | ✅ Complete | 2,880 matches (45% rate), $57.60 spent |
| Email validation (MillionVerifier) | ⚠️ Partial | Credits exhausted after $4.90/2K |
| Phone validation (Twilio v2) | ✅ Complete | 303/500 have carrier type in pilot |
| ATTOM enrichment | ⚠️ Partial — 1 of 7 endpoints | Only detailmortgageowner pulled. Missing: AVM, rental AVM, sales history, tax assessment, expanded profile, building permits |
| Pilot master (500 leads) | ✅ Complete | 157 columns, all enrichment merged |
| Full population (7,537) | ⚠️ Basic enrichment only | 57 columns — no ATTOM, limited contact |
| Google Sheets MVP | ✅ Deployed | 500 pilot leads |
| Client (Frank/CCM) | 🔴 On hold | Awaiting his Airtable setup; data ready |

**FL Pilot 500 — ICP Breakdown:**

| Segment | Count | % |
|---------|-------|---|
| Individual Investor (2-4 properties) | 150 | 30% |
| Entity Investor (2-4 properties) | 99 | 20% |
| Entity Investor (5-9 properties) | 80 | 16% |
| Serial Investor (10+ properties) | 60 | 12% |
| Individual Investor (5-9 properties) | 60 | 12% |
| STR Operator | 40 | 8% |
| Single Property | 10 | 2% |
| Foreign National | 1 | <1% |

**FL Pilot 500 — Scoring:**

- Tier 1 (score 50+): **163 leads** (33%)
- Tier 2 (score 30-49): **331 leads** (66%)
- Tier 3 (15-29): 5 leads

**FL Pilot 500 — Contact Coverage:**

- Phone 1: 338/500 (68%)
- Phone 2: 164/500 (33%)
- Email 1: 257/500 (51%)
- Email 2: 128/500 (26%)

### Wake County, NC (Raleigh)

| Item | Status | Detail |
|------|--------|--------|
| Raw property data (NC OneMap + Wake detailed) | ✅ Complete | 373,373 properties parsed |
| Scored + filtered | ✅ Complete | All 373K scored, ~312K qualified |
| Entity resolution (NC SoS) | 🔴 Not done | NC SoS has no free bulk data; requires paid subscription or workaround |
| Skip trace (Tracerfy) | ⚠️ 33 samples only | 17/33 matched (53%), $0.34 spent |
| ATTOM enrichment | ⚠️ 33 samples only | 26/33 matched via free tier (property basics only, no mortgage data) |
| Bulk enrichment (Steps 04-08) | 🔴 Not run at scale | Blocked on entity resolution decision + ATTOM paid tier |

**Wake County — ICP Breakdown (first 50K scored):**

| Segment | Count | % |
|---------|-------|---|
| Cash Buyer / BRRRR | 32,114 | 64% |
| Portfolio Landlord (5+) | 17,439 | 35% |
| STR Investor | 214 | <1% |
| Self-Employed / LLC Investor | 155 | <1% |
| Out-of-State Investor | 45 | <1% |
| Foreign National | 20 | <1% |
| Growing Portfolio (2-4) | 13 | <1% |

**Note:** Wake County is dominated by Cash Buyer/BRRRR and Portfolio Landlord segments. STR is much smaller than FL because NC has no state STR registry to identify them — we rely on proxy signals only.

---

## 3. ATTOM Credit Strategy

### The Math

- **1,000 credits available** (new key: b9fac048...)
- **7 endpoints per fully enriched property** (detailmortgageowner, expandedprofile, attomavm/detail, rentalavm, saleshistory, assessment, buildingpermits)
- **1,000 ÷ 7 = ~142 fully enriched leads maximum**
- **Showcase allocation: 30 leads × 7 calls = 210 credits**
- **Reserve: 790 credits** for first paying customers' inventory

### Showcase Allocation (210 Credits)

We need enough fully enriched leads to demonstrate the product to each buyer type across the borrower segments that exist in each market.

**South Florida — 15 leads (105 credits):**

| Segment | Count | Why |
|---------|-------|-----|
| Entity/Serial Investor (LLC, 5+ props) | 5 | Core DSCR prospect — LO's primary target |
| Individual Investor (2-4 props, BRRRR/cash buyer) | 5 | Refi candidate — demonstrates financing intelligence value |
| STR Operator | 5 | Niche segment — shows depth for STR-focused LOs |

**Wake County — 15 leads (105 credits):**

| Segment | Count | Why |
|---------|-------|-----|
| Cash Buyer / BRRRR | 5 | Dominant segment (64%) — must showcase this |
| Portfolio Landlord (5+) | 5 | Second largest — serious investors with scale |
| LLC / Self-Employed Investor | 5 | Entity-based owners — demonstrates entity resolution value |

### Selection Criteria (Which 30 Specifically?)

Pick the leads most likely to make an impressive showcase:

1. **Must have skip-traced contact info** (phone or email) — a lead without contact is useless as a demo
2. **Prefer multi-property owners** — more interesting dossier with portfolio data
3. **Prefer recent acquisitions** (last 24 months) — shows active investor, not a passive holder
4. **Prefer entities (LLC/Trust)** — demonstrates entity resolution capability
5. **Spread across property types** — mix of SFR, multi-family, condo to show breadth

### What Each ATTOM Call Returns (Per the Integration Spec)

After all 7 endpoints, each lead gains:

- **Financing:** Lender name/city/state, loan amount, origination date, interest rate, rate type (fixed/ARM), maturity date, loan term, deed type, title company
- **Valuation:** AVM estimate + confidence score + high/low range, value per sqft, monthly appreciation trend, value by condition (poor/good/excellent)
- **Rental:** Property-specific monthly rent estimate + min/max range (replaces zip-level HUD data)
- **Tax:** Assessed total, land vs improvement split, annual tax amount, tax per sqft
- **Sales History:** 10-year transaction history, sale amounts, cash vs mortgage flag, buyer/seller names, price per bed/sqft, interfamily transfer flag
- **Property:** Full building details (beds/baths/sqft/stories), construction type, zoning, census tract, pool, parking, lot dimensions
- **Permits:** Renovation permits, job values, contractor names, permit dates/status — BRRRR gold
- **Flags:** Quit claim, REO/foreclosure, resale vs new construction

---

## 4. Products by ICP (What Each Buyer Gets)

### Product A: LO Intelligence Package

**Buyer:** Individual loan officer originating DSCR loans at a brokerage or bank.

**What they need:** A reason to call, and enough context to have an intelligent first conversation with an affluent investor. They can't use a raw spreadsheet — they need a story about each prospect.

**What they get:**

1. **CRM CSV** — all relevant fields, import-ready (HubSpot, GoHighLevel, Follow Up Boss, Salesforce mapping)
2. **PDF tear sheet per lead** — one page showing:
   - Investor name + entity (if LLC)
   - Portfolio summary: property count, total value, property types
   - Current financing: lender name, loan amount, estimated rate, maturity date, equity position
   - AVM + rental estimate → calculated DSCR ratio
   - Recent transaction history: acquisitions last 24 months, cash vs financed
   - Building permits (renovation activity = BRRRR signal)
   - Contact info: phone (type validated) + email (deliverability validated)
   - **Suggested outreach angle** — 2-3 sentences personalized to their situation
3. **"How to Work These Leads" guide** — call script, email template, follow-up cadence
4. **Compliance one-pager** — they can show their compliance department

**What's NOT included:** Raw property data dump, anything requiring them to do additional research. The tear sheet IS the product — everything they need on one page.

### Product B: Branch Manager Team Feed

**Buyer:** Branch manager or sales director at a mortgage brokerage with 5-30 LOs.

**What they need:** A lead source they can "turn on" for their team. Competitive advantage for recruiting/retaining LOs. Not individual dossiers — they need a pipeline that feeds their existing distribution workflow.

**What they get:**

1. **Monthly CRM feed** — 100-500 leads, segmented by territory/zip code, scored and tiered
2. **Monthly market intelligence report** — new investor activity in their metro: "47 new investment property acquisitions in PB County this month, 12 cash buyers, 8 entity-based"
3. **Tear sheet packet** — same as LO product, but for the top 20% of leads only (their LOs can drill into the rest in the CRM)
4. **Outreach playbook** — team-distributable version

**Key pitch:** "Your LOs are buying garbage leads from Zillow at $300-500/month each. I can give your entire branch exclusive investor intelligence for less than what two LOs spend on Zillow."

### Product C: Agent Investor Pipeline

**Buyer:** Real estate agent who works with (or wants to work with) investment property buyers.

**What they need:** Active portfolio builders who will buy or sell again soon. They don't care about DSCR eligibility — they care about acquisition velocity and repeat transaction potential.

**What they get:**

1. **CRM CSV** — investor-focused fields only. **DSCR/mortgage fields stripped out** (avoids RESPA concerns about agents steering financing)
2. **Investor profile cards** — simplified tear sheet showing:
   - Investor name + entity
   - Portfolio: property count, types owned, geographic focus
   - Acquisition velocity: purchases last 12/24 months, average purchase price
   - Estimated portfolio value + recent appreciation
   - Contact info + suggested approach
3. **"Working Investor Clients" playbook** — how to approach portfolio builders, what to say, how to position as their go-to acquisition agent

**What's REMOVED vs LO product:** All financing fields (lender, rate, loan amount, DSCR score, refi signals). Agents don't need this, and removing it avoids any RESPA gray area about agents directing financing.

### Product D: Broker Office Feed

**Buyer:** Real estate broker or team lead distributing leads to their agents.

**What they get:** Same as Agent product but sold as office-wide access. Broker distributes leads to agents by territory/specialty.

**Key pitch:** "Join our brokerage and you get access to an exclusive investor lead pipeline that no other office has."

---

## 5. Pricing Models

### Model A: Per-Lead Pricing (From Project Docs)

| Product | Tier 1 (Hot, 50+) | Tier 2 (Warm, 30-49) |
|---------|-------------------|----------------------|
| Semi-Enriched (CSV + basic profile) | $15/lead | $10/lead |
| Full Dossier (PDF tear sheet + all data) | $100/lead | $60/lead |

**Volume discounts:** 5% increments, capped at 35%

| Volume | Discount |
|--------|----------|
| 11-25 leads | List price |
| 26-50 | 5% off |
| 51-100 | 10% off |
| 101-150 | 15% off |
| 151-200 | 20% off |
| 201-250 | 25% off |
| 251-300 | 30% off |
| 301-350 | 35% off |

**Pros:** Simple, low commitment for buyer, easy to test. No recurring obligation — LO buys 25 leads, tests them, buys more if they work.
**Cons:** Unpredictable revenue for us, requires reselling every month, no lock-in.

### Model B: Subscription Pricing

| Product | Monthly | Leads Included |
|---------|---------|---------------|
| LO Starter | $500/mo | 25 leads + tear sheets |
| LO Growth | $750/mo | 50 leads + tear sheets |
| Branch Manager | $1,500/mo | 150 leads + team feed + market report |
| Agent Starter | $300/mo | 25 investor profiles |
| Agent Growth | $500/mo | 50 investor profiles |
| Broker Office | $800/mo | 100 investor profiles + office distribution |

**Pros:** Predictable recurring revenue, customer lock-in, easier to scale.
**Cons:** Higher commitment for buyer (harder first sale), more pressure to deliver consistently every month.

### Recommended Approach

**Start with per-lead pricing** to get first customers. Lower commitment = faster first sale. Once you have 3-5 customers who reorder monthly, **offer to convert them to subscription** at a discount (effectively the same thing, but with a commitment).

The P&L spreadsheet models both — you can play with the assumptions.

---

## 6. Cost Structure

### Per-Lead COGS (Variable)

| Item | Cost | Source |
|------|------|--------|
| Property data | $0.00 | Free (FDOR, NC OneMap) |
| Skip trace (Tracerfy) | $0.009 effective | $0.02/match × 45% match rate |
| Email validation | $0.0025 | MillionVerifier $4.90/2K |
| Phone validation | $0.008 | Twilio v2 |
| DNC scrub | $0.00 | Free (first 5 area codes) |
| ATTOM (trial) | $0.00 | Using 1,000 free credits |
| **Total COGS/lead** | **~$0.02** | During trial period |

Post-trial, ATTOM adds $0.017-0.10/lead depending on tier. At the $95/mo starter (5K calls/month): $0.019/call × 7 endpoints = $0.133/lead. Total COGS rises to ~$0.15/lead.

### Monthly Fixed Costs

| Item | Cost | Notes |
|------|------|-------|
| Claude Max | $200 | AI development tool |
| ATTOM API (post-trial) | $95 | Starter tier, 5K calls/mo |
| Twilio | ~$15 | Variable |
| MillionVerifier | ~$5 | Top-ups as needed |
| DNC/compliance | ~$40 | FTC re-scrub every 31 days |
| Sending domain + email warmup | ~$35 | Instantly.ai or equivalent |
| Hosting/tools | ~$10 | GitHub, compute |
| **Total** | **~$400/mo** | |

### Margin Analysis

At **$15/lead (semi-enriched)**: $15 - $0.15 COGS = **$14.85 margin (99%)**
At **$100/lead (full dossier)**: $100 - $0.15 COGS = **$99.85 margin (99.8%)**
At **$500/mo subscription**: $500 - ($0.15 × 25 leads) = **$496.25 margin (99.3%)**

Breakeven on fixed costs: $400/mo ÷ $14.85/lead = **27 semi-enriched leads/month**

---

## 7. Target Markets

### Why These Two Markets First

| Factor | South Florida (PB + Broward) | Wake County (Raleigh) |
|--------|------------------------------|----------------------|
| DSCR market rank | #1 nationally (18-22% of volume) | #5 nationally (4-6% of volume) |
| Pipeline status | 7,537 leads built, 500 fully enriched | 373K scored, 33 samples enriched |
| Your presence | Frank (LO partner) in Boca Raton | You in Raleigh — can sell face-to-face |
| Entity resolution | ✅ Done (SunBiz free bulk data) | 🔴 Not done (NC SoS requires paid sub) |
| STR identification | ✅ Done (DBPR bulk CSV, 70-80% match) | 🔴 No state registry — proxy signals only |
| Compliance | FL has strictest state rules ($1,500 license, $50K bond) | NC has no state telemarketing license |
| Key risk | Frank may not activate | Entity resolution gap reduces LLC enrichment quality |

### Future Markets (From Your Research)

| Rank | Market | County | Rationale | Status |
|------|--------|--------|-----------|--------|
| 3 | Cleveland, OH | Cuyahoga | #1 nationally for DSCR; median $140K, 11.3% yield | Research phase |
| 4 | Indianapolis, IN | Marion | Largest YoY occupancy gain; 47% renter; underpenetrated | Research phase |

---

## 8. Phased Roadmap

### NOW — Week 1: Build Showcase (This Week)

**Goal:** 30 fully enriched showcase leads (15 FL, 15 Wake) with all 7 ATTOM endpoints.

| # | Task | Credits | Cost | Dependencies |
|---|------|---------|------|-------------|
| 1 | Select 15 FL leads from pilot 500 (5 per segment, must have skip-traced contact) | 0 | $0 | Already have data |
| 2 | Run all 7 ATTOM endpoints on 15 FL leads | 105 | $0 | New API key (done) |
| 3 | Select 15 Wake leads from scored data (5 per segment) | 0 | $0 | Already scored |
| 4 | Run Tracerfy skip trace on 15 Wake leads | 0 | ~$0.30 | Need to select leads first |
| 5 | Run all 7 ATTOM endpoints on 15 Wake leads | 105 | $0 | Need APN + FIPS for Wake |
| 6 | Validate phones (Twilio) + emails (MillionVerifier) on all 30 | 0 | ~$0.50 | After skip trace |
| 7 | Build tear sheet template (PDF, one page per lead) | 0 | $0 | After all enrichment |
| 8 | Generate 30 tear sheets with real data | 0 | $0 | After template built |

**Output:** 30 fully enriched dossiers — the actual product you'll show buyers.

**ATTOM credits used: 210. Remaining: 790.**

### NEXT — Weeks 2-3: Sales Collateral + First Conversations

**Goal:** Pitch materials built, 10+ conversations started.

| # | Task | Notes |
|---|------|-------|
| 1 | Build redacted sample package | 5 tear sheets with contact info blurred — this is what you show in a pitch |
| 2 | Create buyer-specific pitch decks (1 page each) | LO pitch, Branch Mgr pitch, Agent pitch, Broker pitch |
| 3 | Finalize compliance one-pager | Already drafted — polish for distribution |
| 4 | Frank works 15 FL showcase leads | Track: outreach method, response rate, conversations, pipeline |
| 5 | YOU work 15 Wake leads locally | Same tracking — you are the backup proof of concept |
| 6 | LinkedIn outreach: 15 DSCR loan officers in South FL | "I source exclusive investor leads with full financing intelligence for DSCR lenders in Palm Beach. Want to see a sample?" |
| 7 | LinkedIn outreach: 10 DSCR loan officers in Raleigh area | Same message, Wake County |
| 8 | LinkedIn outreach: 10 investor-specialist RE agents (both markets) | Different message: "I identify active portfolio builders in [county] before they hit the MLS. Want to see who's acquiring in your market?" |

### LATER — Weeks 4-8: First Revenue

**Goal:** 3-5 paying customers.

| # | Task | Notes |
|---|------|-------|
| 1 | Close first LO customer(s) — per-lead pricing | Start with semi-enriched at $15/lead, upsell to dossier |
| 2 | Fulfill first orders using ATTOM reserve credits | 790 credits ÷ 7 = ~112 fully enriched leads available |
| 3 | Collect feedback on tear sheet format + data quality | What was useful? What was missing? What converted to a conversation? |
| 4 | Run Wake County bulk pipeline (Steps 04-08) | Skip trace + validate at scale if demand justifies |
| 5 | Decide on NC entity resolution approach | Paid NC SoS subscription ($200-500/yr) vs name parsing workaround |
| 6 | Evaluate ATTOM paid subscription ($95/mo) | If showcase converts to sales, subscribe; if not, pipeline still works without it |

### FUTURE — Months 3-6: Scale

| # | Task | Notes |
|---|------|-------|
| 1 | Introduce subscription pricing for repeat customers | Convert per-lead buyers to monthly subscriptions |
| 2 | Pitch branch managers using LO customer conversion data | "Your LO John closed a $450K DSCR deal from our leads" |
| 3 | Pitch RE brokers using agent customer data | Same playbook |
| 4 | Activate Cuyahoga OH and/or Marion IN | Pipeline designed to be portable — swap state configs |
| 5 | Revenue target: $5K-10K/month recurring | 10-20 customers across all 4 ICP types |

---

## 9. Risks

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Frank doesn't activate FL leads | Lose FL proof of concept | HIGH | You test locally in Wake — that's why 2 markets |
| LOs don't work leads properly | Low conversion, blame data, churn | HIGH | Include outreach playbook + track which leads convert |
| Compliance objection kills deals | Lost sales | MEDIUM | Lead with compliance one-pager; HPPA ban makes us the safe alternative |
| NC entity resolution too hard | Lower data quality for Wake leads | HIGH | Use name parsing + portfolio detection as proxy for MVP |
| ATTOM trial expires before proving value | Lose mortgage enrichment | MEDIUM | Only burn 210 of 1,000 on showcase; pipeline works without ATTOM (fewer fields) |
| 7 API calls per lead makes ATTOM expensive at scale | COGS rises from $0.02 to $0.15/lead | LOW | Still 99% margin at $15/lead; can optimize to fewer endpoints for Tier 2 leads |

---

## 10. Immediate Next Steps

**This session or today:**

1. ✅ ATTOM API key updated (done — b9fac048...)
2. Select 15 FL leads from pilot 500 for full 7-endpoint enrichment
3. Select 15 Wake leads from scored data for full enrichment
4. Update ATTOM script to call all 7 endpoints (currently only calls detailmortgageowner)
5. Design tear sheet template

**This week:**

6. Run 210 ATTOM calls (30 leads × 7 endpoints)
7. Build 30 PDF tear sheets with real data
8. Create redacted sample package for pitches
9. Frank starts working FL leads
10. You start working Wake leads

---

*All numbers in this document are sourced from actual pipeline data files, the ICP Playbook, Enrichment Stack docs, market research memos (archive/research/04_market_sizing_macro.md), and the ATTOM API Integration Spec (March 2026). P&L projections are in the companion spreadsheet DSCR_PnL_Model.xlsx with editable blue-input assumptions.*
