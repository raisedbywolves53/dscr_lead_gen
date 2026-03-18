# DSCR Lead Intelligence — Launch Blueprint

## Mission

Build and sell enriched DSCR investor leads across 3 U.S. markets. Two product tiers (semi-enriched and full dossier), flat per-lead pricing, volume discounts. We build the leads, LOs buy them, they do their own outreach. Going for volume.

## The Model

```
Public records → Pipeline (score, enrich, validate) → Two product tiers
    → Semi-Enriched ($10/lead): contacts + portfolio summary + talking points
    → Full Dossier ($75/lead): complete PDF with every property, financing, wealth signals
        → Sell to LOs/branch managers via outbound prospecting
            → They do their own outreach to investors
```

---

## Target Markets

| # | Market | County | Why |
|---|--------|--------|-----|
| 1 | **Raleigh, NC** | Wake | Local — face-to-face selling, already researched |
| 2 | **Cleveland, OH** | Cuyahoga | #1 nationally for DSCR loans, median $140K, 11.3% yield, low competition (score: 4.45) |
| 3 | **Indianapolis, IN** | Marion | Largest YoY occupancy gain nationally, 47% renter pop, underpenetrated (score: 4.35) |

---

## What We're Building (End State)

### Per Market — Product
1. **Enriched investor database** — scored, contact-verified, DNC-scrubbed
2. **Semi-enriched lead export** — structured data ready to sell (Tier 1 product)
3. **Full dossier PDFs** — code-generated, professionally designed (Tier 2 product)

### Per Market — Sales Assets
4. **3 redacted sample dossiers** (1 per ICP segment) — proves depth to LO prospects
5. **Market TAM one-pager** — total properties, Tier 1 leads, market stats
6. **25 LO battlecards** — decision-maker profiles with personalized outreach angles

### Platform Infrastructure
7. **Dossier generation script** — code-generated PDFs from enriched data
8. **LO outbound sequences** — email + LinkedIn, personalized per battlecard

---

## Pricing Strategy

Two product tiers, flat per-lead pricing, volume discounts. Semi-exclusive (each lead sold to a limited number of buyers per market). Going for volume.

### Tier 1: Semi-Enriched Lead — $10/lead

What the LO gets:
- Validated contact info (phone verified mobile/landline, email verified)
- Number of investment properties owned
- Estimated portfolio value
- Estimated debt-to-equity ratio
- AI-generated talking points (purchase history analysis, trends, refi angles)

**This is what most competitors charge $15-55 for — except theirs are consumer form-fills, not scored investor profiles.**

| Volume | Per lead | Total | Discount |
|--------|----------|-------|----------|
| 1-24 | $10.00 | — | List price |
| 25 | $9.00 | $225 | 10% off |
| 50 | $8.00 | $400 | 20% off |
| 100 | $7.00 | $700 | 30% off |
| 250+ | $6.00 | $1,500+ | 40% off |

### Tier 2: Fully Enriched Dossier — $75/lead

Everything in Tier 1, plus a complete investor dossier — professionally designed PDF + structured data:
- Every property in portfolio with details (type, beds, baths, sqft, value, address)
- Financing per property (lender, loan amount, origination date, rate type, estimated balance)
- Entity ownership details (LLC/Corp/Trust → officers, registered agent, filing dates)
- Equity analysis per property and portfolio-wide
- Refi opportunity scoring with specific signals
- Wealth signals (FEC donations, IRS 990 filings, board seats)
- Acquisition timeline and investment behavior patterns
- Detailed AI-generated talking points and recommended approach

**No one sells this. The closest alternative is PropStream ($199/mo) where the LO does all the work themselves — and still can't get this level of analysis.**

| Volume | Per lead | Total | Discount |
|--------|----------|-------|----------|
| 1-4 | $75.00 | — | List price |
| 5 | $65.00 | $325 | 13% off |
| 10 | $55.00 | $550 | 27% off |
| 25 | $45.00 | $1,125 | 40% off |
| 50+ | $35.00 | $1,750+ | 53% off |

### Unit Economics

| Metric | Semi-Enriched | Fully Enriched |
|--------|---------------|----------------|
| Our COGS/lead | ~$1.00 | ~$2.00 |
| List price | $10.00 | $75.00 |
| Margin (list) | 90% | 97% |
| Deepest bulk price | $6.00 | $35.00 |
| Margin (deepest bulk) | 83% | 94% |

### Revenue Scenarios

| Scenario | Monthly revenue | COGS | Net |
|----------|----------------|------|-----|
| 3 LOs buy 25 semi-enriched each | $675 | ~$75 + $350 fixed | +$250 |
| 5 LOs buy 50 semi-enriched each | $2,000 | ~$250 + $350 fixed | +$1,400 |
| 2 LOs buy 10 full dossiers each | $1,100 | ~$40 + $350 fixed | +$710 |
| 5 LOs buy 25 semi + 2 buy 10 full | $3,325 | ~$290 + $350 | +$2,685 |
| Volume play: 10 LOs × 100 semi | $7,000 | ~$1,000 + $350 | +$5,650 |

### Moat Protection

- No source attribution anywhere — dossiers show WHAT we know, never HOW
- Entity resolution (LLC → person) takes 6+ sources to replicate
- ICP scoring logic is proprietary
- Semi-exclusive model: limited buyers per market prevents lead fatigue
- Full dossier depth is the differentiator — no one can buy this anywhere else

---

## Monthly Operating Costs

| Item | Monthly | Category |
|------|---------|----------|
| Claude Max | $200 | Fixed — AI tooling |
| ATTOM API | $95 | Fixed — mortgage/property data |
| Twilio | ~$15 | Variable — phone validation |
| MillionVerifier | ~$5 | Variable — email validation (credits don't expire) |
| DNC (FTC + Tracerfy) | ~$35-50 | Variable — compliance |
| Sending domains (1-2 lookalikes) | ~$2 | Fixed — ~$24/yr |
| Email warmup tool | $30-50 | Fixed — Instantly or similar |
| **Total** | **~$385-420/mo** |

Rounds to **~$350/mo fixed** once you remove one-time setup costs.

---

## Phased Implementation

### Phase 1: Infrastructure & Email Warming
**Branch:** `phase1/infrastructure`
**Effort:** ~2-3 hours of setup, then 2-3 weeks of passive warming
**Goal:** Sending infrastructure warming while we build product

#### Email Domain Strategy
- **Primary (warm conversations):** zack@stillmindcreative.com — for replies, follow-ups, and conversations that started on LinkedIn
- **Cold outreach (volume protection):** 1-2 lookalike domains (stillmindcreative.co, etc.) to protect primary domain reputation

#### Tasks
- [ ] **1.1** Buy 1-2 lookalike sending domains (~$24/yr total)
- [ ] **1.2** Set up mailboxes with Google Workspace or Zoho
- [ ] **1.3** Configure SPF, DKIM, DMARC
- [ ] **1.4** Start email warmup (Instantly.ai or similar) — runs passively
- [ ] **1.5** Confirm ATTOM API access and tier ($95/mo plan)
- [ ] **1.6** Verify Tracerfy API key is active, credits loaded
- [ ] **1.7** Verify MillionVerifier credits available
- [ ] **1.8** Set up FTC DNC registry account (free, first 5 area codes)

**Deliverable:** Domains warming, APIs verified.

---

### Phase 2: Data Pipeline — All 3 Markets
**Branch:** `phase2/multi-market-pipeline`
**Effort:** ~8-12 hours for Wake (adapting existing pipeline), ~4-6 hours each for OH/IN (once Wake is working)
**Goal:** Enriched investor databases for all 3 markets

#### 2A: Wake County, NC (Adapt Existing Pipeline)
- [ ] **2A.1** Download Wake County property data (tax records + OneMap parcels)
- [ ] **2A.2** Adapt `02_parse_nal.py` for NC data format (columns differ from FL FDOR)
- [ ] **2A.3** Run `03_filter_icp.py` — score and filter to Tier 1
- [ ] **2A.4** Entity resolution via owner name parsing (skip NC SoS initially)
- [ ] **2A.5** Run Tracerfy skip trace
- [ ] **2A.6** Run ATTOM mortgage enrichment
- [ ] **2A.7** Validate contacts (MillionVerifier + Twilio)
- [ ] **2A.8** DNC scrub (FTC + Tracerfy comprehensive)

#### 2B: Cuyahoga County, OH (New Market)
- [ ] **2B.1** Research OH property data sources (County Fiscal Officer, OH GIS)
- [ ] **2B.2** Create `deployments/ohio/CONFIG.md` (data sources, compliance, area codes)
- [ ] **2B.3** Download + parse property data
- [ ] **2B.4** Run pipeline (score → skip trace → ATTOM → validate → DNC)

#### 2C: Marion County, IN (New Market)
- [ ] **2C.1** Research IN property data sources (County Assessor, Indiana GIS)
- [ ] **2C.2** Create `deployments/indiana/CONFIG.md`
- [ ] **2C.3** Download + parse property data
- [ ] **2C.4** Run pipeline (score → skip trace → ATTOM → validate → DNC)

**Deliverable:** Enriched, DNC-scrubbed investor databases for all 3 markets.

**Git protocol:**
- Feature branches per market: `phase2/wake-county`, `phase2/cuyahoga-county`, `phase2/marion-county`
- PR to `phase2/multi-market-pipeline`, then merge to `master` when all 3 complete
- Each script adaptation gets its own commit with clear message

---

### Phase 3: Sales Assets & Product Build
**Branch:** `phase3/sales-assets`
**Effort:** ~10-15 hours (dossier template is the heaviest lift)
**Goal:** Sellable product + materials to sell it with

#### 3A: Dossier Generation Script (The Product)
- [ ] **3A.1** Build dossier generation script — code-generated PDF (Python)
  - Use WeasyPrint (HTML/CSS → PDF) or ReportLab for programmatic generation
  - Professional, clean layout — think consulting report, not spreadsheet dump
  - Find 2-3 visual reference PDFs to guide design
  - **Full version** (Tier 2 product): all data, all contacts, all property addresses
  - **Redacted version** (sales sample): shows depth but no identifying info
  - Same script generates both — redaction is a flag, not a separate template
- [ ] **3A.2** Build semi-enriched export (Tier 1 product):
  - Structured CSV/Google Sheet with: contact info, property count, portfolio value, D/E ratio, AI talking points
  - Clean, well-labeled columns, ready for LO to import into their CRM

#### 3B: Sample Dossiers (3 per market = 9 total)
- [ ] **3B.1** Select 3 real leads per market representing each ICP:
  - **Portfolio Landlord** (5+ properties, LLC-owned, out-of-state)
  - **Growing Investor** (2-4 properties, individual, recent acquisitions)
  - **Entity/High Net Worth** (trust/corp, multi-county, wealth signals)
- [ ] **3B.2** Fully enrich each lead — every property, all financing, wealth signals
- [ ] **3B.3** Generate 9 redacted sample dossier PDFs (3 markets × 3 ICPs)

#### 3C: Market TAM One-Pagers (1 per market = 3 total)
- [ ] **3C.1** For each market, compile:
  - Total investment properties in county
  - Total identified as investor-owned (mailing ≠ property address)
  - Tier 1 leads identified (ICP score threshold)
  - Top zip codes by investor density
  - Average portfolio size, value, equity
  - DSCR market stats (median home price, rental yield, vacancy rate)
  - Top lenders in market (from ATTOM data)
- [ ] **3C.2** Design one-pager template (code-generated PDF, branded)
- [ ] **3C.3** Generate 3 market one-pagers

#### 3D: LO Battlecards (25 per market = 75 total)
- [ ] **3D.1** Use Apollo (remaining credits) to build hit lists:
  - Search: DSCR loan officers, branch managers, mortgage brokers in each metro
  - Cohort B (DSCR Specialist LOs) performed best in experiment — weight toward these
  - Pull: name, title, company, email, phone, LinkedIn URL, company size
- [ ] **3D.2** Enrich beyond Apollo:
  - NMLS Consumer Access — license history, production volume, active states
  - LinkedIn profile review — recent posts, activity, DSCR mentions
  - Company website — team page, specialties, lender relationships
  - REIA membership — speaking at or attending local investor meetups?
- [ ] **3D.3** Build battlecard template per LO:
  - Name, title, company, NMLS#, years licensed
  - Contact: email, phone, LinkedIn
  - Production signals: states licensed, company size, DSCR focus indicators
  - Personalization hooks: recent LinkedIn posts, REIA involvement, lender relationships
  - Outreach angle: why OUR leads matter for THIS person
  - Objection pre-handles based on their profile
- [ ] **3D.4** Generate 75 battlecards (stored as structured data)

**Deliverable:** Working dossier generator, 9 sample PDFs, 3 market one-pagers, 75 LO battlecards.

---

### Phase 4: LO Outbound Prospecting (Manual First)
**Branch:** `phase4/outbound`
**Effort:** ~2-3 hours to write sequences, then ~30 min/day for manual sends
**Goal:** Start selling leads to LOs

- [ ] **4.1** LO sequence design (per prospect):
  - **Day 0:** LinkedIn connection request (personalized from battlecard)
  - **Day 1:** If accepted → LinkedIn DM #1 (value-first, reference their market)
  - **Day 3:** Cold email #1 (attach market one-pager PDF)
  - **Day 5:** LinkedIn DM #2 (share a specific insight about their market)
  - **Day 7:** Cold email #2 (attach redacted sample dossier PDF)
  - **Day 10:** LinkedIn DM #3 (direct ask — "want to see 5 real leads in your market?")
  - **Day 14:** Cold email #3 (case study / social proof once available)
- [ ] **4.2** Write messaging templates using battlecard fields
  - Tone: peer-to-peer. "I built a system that identifies investors ready for DSCR lending — you're someone who'd actually use this."
  - Key differentiator: "Scored, enriched investor profiles with validated contacts and financing intel. Not a recycled list."
- [ ] **4.3** Start with Wake County (local advantage) — first 10-15 LOs manually
- [ ] **4.4** Iterate based on responses, then expand to Cleveland + Indianapolis
- [ ] **4.5** Track everything in outreach tracker spreadsheet

**Deliverable:** Active LO pipeline, first lead sales.

---

### Phase 5: Automation (N8N)
**Branch:** `phase5/n8n-automation`
**Effort:** ~6-10 hours to build workflows (after manual outreach validates messaging)
**Goal:** Automate the repeatable parts of LO outbound

#### Why N8N Fits
LO outbound has conditional steps that benefit from orchestration:
1. Pull battlecard data → 2. Generate personalized message (Claude API) → 3. Send via email → 4. Wait X days → 5. Check for reply → 6. If no reply → different follow-up angle → 7. If reply → notify Zack → 8. Track status

#### Implementation
- [ ] **5.1** Install N8N (self-hosted or cloud)
- [ ] **5.2** Build LO outbound workflow:
  - Trigger: new LO added to battlecard sheet
  - Claude API generates personalized email from battlecard
  - Human review checkpoint → send via warmed domain → schedule follow-ups
- [ ] **5.3** Build LinkedIn daily digest:
  - N8N can't automate LinkedIn (TOS violation risk)
  - Instead: daily summary of "send these messages today" with pre-written copy
- [ ] **5.4** Build response handling:
  - Monitor reply inbox
  - On reply: notify Zack, pull battlecard context, suggest response
- [ ] **5.5** Build pipeline tracking:
  - Auto-update outreach tracker when emails sent/replies received

**Deliverable:** Semi-automated LO outbound engine. Zack reviews/approves, N8N handles timing and personalization.

---

### Phase 6: Market-Specific Collateral
**Branch:** `phase6/collateral`
**Effort:** Ongoing — informed by Phase 4 conversations
**Goal:** Content that demonstrates expertise and builds trust with LOs

This phase is intentionally open — content strategy TBD after outreach reveals what resonates. Potential assets:

- [ ] **6.1** Market reports: "Q1 2026 DSCR Investor Activity in [Market]"
  - Top zip codes for investor acquisitions
  - Average DSCR ratios by submarket
  - Lender market share shifts
- [ ] **6.2** Insight pieces for LOs:
  - "5 Signals That a Landlord Is Ready to Refi"
  - "Why [Market] Investors Are Shifting from Hard Money to DSCR"
- [ ] **6.3** Case studies (once sales close):
  - "LO closed $450K DSCR deal in 18 days using our intel"
  - Anonymized but specific

**Format:** Code-generated PDFs. Professional, clean, 1-2 pages max.

---

## Git Protocol

### Branch Strategy
```
master (production — stable)
├── phase1/infrastructure
├── phase2/multi-market-pipeline
│   ├── phase2/wake-county
│   ├── phase2/cuyahoga-county
│   └── phase2/marion-county
├── phase3/sales-assets
├── phase4/outbound
├── phase5/n8n-automation
└── phase6/collateral
```

### Workflow
1. Create feature branch from `master` for each phase
2. Sub-branches for parallel work (e.g., 3 markets in Phase 2)
3. PR to phase branch when sub-work complete
4. PR phase branch to `master` when phase deliverables verified
5. Tag releases: `v0.1-infrastructure`, `v0.2-pipeline`, `v0.3-sales-assets`, etc.

### Commit Standards
- Descriptive messages: "Add Wake County property parser for NC OneMap format"
- Reference phase: "Phase 2A: Adapt ICP scoring for NC data fields"
- No commits with secrets (.env, API keys, client data)
- .gitignore: all CSV data files, .env, cache directories, client-specific outputs

---

## Critical Path & Dependencies

```
Phase 1 (Infrastructure)  ←── START FIRST (email warming is the only hard blocker)
    ↓ runs passively
Phase 2 (Pipeline)         ←── can start same day as Phase 1
    ↓ produces enriched data
Phase 3 (Sales Assets)     ←── needs Phase 2 data to build product + samples
    ↓ produces sellable product + sales materials
Phase 4 (LO Outbound)     ←── needs Phase 3 assets + Phase 1 warm domains
    ↓ validates messaging, generates revenue
Phase 5 (N8N Automation)   ←── needs Phase 4 learnings (what messages work)
Phase 6 (Collateral)       ←── ongoing, informed by Phase 4 conversations
```

**Hard blocker:** Email domain warming (~2-3 weeks passive) — start immediately.

**LinkedIn outreach to LOs can start as soon as battlecards are ready**, independent of email warming. That's the fastest path to first sale.

**Total estimated effort to first LO outreach:** ~25-30 hours of active work (Phases 1-4)

---

## Open Questions

1. **CRM** — CSV/Google Sheets tracker for now. Revisit when 10+ active conversations.
2. **NC SoS paid subscription** — worth investigating for entity resolution quality. Contact subscriptions@sosnc.gov. Not blocking.
3. **ATTOM tier** — $95/mo to start. Monitor API usage as 3 markets ramp.

## Resolved Decisions

- **Business model:** Build leads, sell leads. Two tiers, flat pricing, volume discounts. LOs do their own outreach to investors.
- **Sending domains:** Still Mind Creative lookalikes for cold volume protection. Primary conversations from zack@stillmindcreative.com.
- **No investor-facing brand.** We don't contact investors. We sell data to LOs.
- **Collateral format:** Code-generated PDFs via Python (WeasyPrint or ReportLab). No Canva.
- **Timelines:** No calendar dates. Phases gated by dependencies. Effort estimates in hours.
- **Pricing:** $10/lead semi-enriched, $75/lead full dossier, bulk discounts up to 40-53% off.

---

## Success Metrics

| Metric | Target | Gate |
|--------|--------|------|
| Markets with enriched data | 3 | Before any outreach |
| Dossier generator working | Yes | Before any outreach |
| Sample dossiers created | 9 | Before any LO outreach |
| LO battlecards created | 75 | Before any LO outreach |
| LO outreach sent | 25+ | After assets complete |
| LO conversations started | 5+ | After outreach begins |
| First lead sale | 1 | After conversations |
| Monthly revenue | $1,000+ | After first few sales |

---

## File Structure

```
sales/
├── LAUNCH_BLUEPRINT.md          ← THIS FILE
├── battlecards/
│   ├── wake_county/             # 25 LO battlecards
│   ├── cuyahoga_county/         # 25 LO battlecards
│   └── marion_county/           # 25 LO battlecards
├── dossiers/
│   ├── samples/
│   │   ├── wake_county/         # 3 redacted sample dossiers (PDF)
│   │   ├── cuyahoga_county/
│   │   └── marion_county/
│   └── templates/               # Dossier generation templates (HTML/CSS)
├── market_reports/
│   ├── wake_county_tam.pdf
│   ├── cuyahoga_county_tam.pdf
│   └── marion_county_tam.pdf
├── collateral/                  # Existing — one-pager, sample dossier
├── outreach/                    # Existing — LO sequences, tracker
├── prospects/                   # Existing — LO lists, experiment data
└── pricing_research/            # Competitive pricing landscape

deployments/
├── north_carolina/CONFIG.md     # Existing
├── ohio/CONFIG.md               # NEW
└── indiana/CONFIG.md            # NEW
```
