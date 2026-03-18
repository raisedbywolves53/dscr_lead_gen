# DSCR Lead Intelligence — Launch Blueprint

## Mission

Build an investor-to-lender matching platform across 3 U.S. markets. We identify investment property owners, enrich them with deep portfolio intelligence, initiate conversations on behalf of our LO clients, and deliver warm introductions — not cold data. We own the investor relationship from first touch through post-close.

## The Model

```
We find the investor → We reach out → Investor responds
    → We qualify + warm intro to LO client
        → LO works the deal
            → We follow up with investor (concierge QC)
                → Deal closes → verified via public records
                    → Rev share triggered
```

**Why this beats selling dossiers:**
- We own the funnel — LO can't cut us out
- Warm intro > cold list (10x more valuable to the LO)
- We see every conversation, know which leads convert
- Rev share is enforceable — we introduced the parties and verify via public records
- The investor is OUR client — if the LO drops the ball, we re-route to another LO

---

## Two Brands, Two Audiences

### 1. Still Mind Creative (LO-Facing — existing)
- **Domain:** stillmindcreative.com (+ 1-2 lookalikes for cold email volume protection)
- **Purpose:** Sell the service to loan officers. "We generate warm investor introductions in your market."
- **Outreach from:** zack@stillmindcreative.com (warm), lookalike domain (cold sequences)

### 2. Investor-Facing Brand (NEW — needs to be created)
- **Domain:** TBD — something that positions as advisory/marketplace, not a lead gen company
  - Examples: dscrcapitaladvisors.com, investorlendingadvisors.com, [something]capital.com
  - Should feel trustworthy to a real estate investor receiving a cold email
- **Purpose:** Reach out to investors. "We help investment property owners find optimal DSCR lending terms for their portfolio."
- **Landing page:** Simple one-page site explaining the value prop. Gives legitimacy when investor Googles the domain.
- **Outreach from:** zack@[investor-brand].com or team@[investor-brand].com
- **This is the brand investors interact with.** The LO's name comes in at the warm introduction stage, not before.

### Why Two Brands
- Investors seeing "Still Mind Creative" (a creative agency) reaching out about lending would be confusing
- The investor-facing brand needs to feel like an advisory/marketplace — someone who helps them find the best deal
- Keeps the B2B sales operation (selling to LOs) separate from the B2C operation (talking to investors)
- If an LO Googles us, they see our sales brand. If an investor Googles us, they see the advisory brand. Clean separation.

---

## Target Markets

| # | Market | County | Why |
|---|--------|--------|-----|
| 1 | **Raleigh, NC** | Wake | Local — face-to-face selling, already researched |
| 2 | **Cleveland, OH** | Cuyahoga | #1 nationally for DSCR loans, median $140K, 11.3% yield, low competition (score: 4.45) |
| 3 | **Indianapolis, IN** | Marion | Largest YoY occupancy gain nationally, 47% renter pop, underpenetrated (score: 4.35) |

---

## What We're Building (End State)

### Per Market — LO Sales Assets
1. **3 fully enriched sample dossiers** (1 per ICP segment) — redacted, proves depth
2. **Market TAM one-pager** — total properties, Tier 1 leads, market stats
3. **25 LO battlecards** — decision-maker profiles with personalized outreach angles
4. **LO outbound sequences** — email + LinkedIn, personalized per battlecard

### Per Market — Investor Pipeline
5. **Enriched investor database** — scored, contact-verified, DNC-scrubbed
6. **Investor outreach sequences** — personalized by ICP segment and portfolio signals
7. **Concierge follow-up templates** — post-introduction QC touchpoints

### Platform Infrastructure
8. **Investor-facing brand + landing page** — legitimacy for cold outreach
9. **Dossier generation script** — code-generated PDFs from enriched data
10. **Pipeline tracker** — tracks every investor from first touch through deal close

---

## Pricing Strategy

### Pilot: Prove Concept ($500 / 5 Warm Introductions)

| Element | Detail |
|---------|--------|
| Deliverable | 5 qualified warm introductions (investor expressed interest in DSCR lending options) |
| What the LO gets | Investor name, full dossier (portfolio, financing, scoring), and a warm handoff ("I'd like to connect you with [LO]") |
| Cost per intro | $100 |
| Our COGS | ~$5-10 total (~$1-2/lead enrichment + email sending costs) |
| Margin | 95%+ |

**Why $500/5 intros works:**
- One closed deal on a $400K DSCR loan = $4K-10K commission = 8-20x ROI
- These aren't cold names — the investor already replied "yes, I'm interested"
- Small enough they can't reverse-engineer our process
- Large enough to prove value and likely close at least 1 deal

### Scale Pricing (Post-Pilot)

| Tier | Warm intros/mo | Monthly | Per intro | Notes |
|------|---------------|---------|-----------|-------|
| Growth | 10 | $1,500/mo | $150 | 1-2 counties |
| Pro | 25 | $3,000/mo | $120 | Full metro area |
| Enterprise | 50+ | $5,000+/mo | $100+ | Multi-county, priority routing |

### Revenue Share (Endgame)

Once trust is established:
- Base subscription + **$500-1,000 per verified funded deal**
- Verified via county clerk mortgage recordings (public record, they can't hide it)
- We introduced the parties → we have the email thread → public record confirms the closing
- "We noticed a new mortgage recorded on a property we connected you with — congrats! Performance bonus applies."

### Moat Protection

- No source attribution anywhere — dossiers show WHAT we know, never HOW
- Entity resolution (LLC → person) takes 6+ sources to replicate
- ICP scoring logic is proprietary
- **The real moat: we own the investor relationship.** The LO can't cut us out because they didn't find the investor — we did, and we stay in the loop through concierge follow-up.

---

## The Concierge QC Loop

This is the piece that locks the model together. It's investor experience management AND deal verification in one.

### Why It Matters
1. **Maintains visibility after handoff** — we stay in the conversation
2. **Verifies deal progress** without relying on LO self-reporting
3. **Builds direct relationship with investor** — they're OUR client, not the LO's
4. **Creates upsell opportunities** — "Glad the refi went well. We're seeing strong acquisition opportunities in your market — want us to keep you posted?"
5. **Generates feedback data** — which LOs close? Which ones ghost? This determines who we keep routing to.

### The Flow

```
Warm Introduction Made (Day 0)
    ↓
Concierge Check-In #1 (Day 7-10)
    "Hi [Investor], we connected you with [LO] regarding your portfolio
     last week. Wanted to make sure the conversation was valuable and
     that [LO] was a good fit for what you're looking for. If you'd like
     to explore other options, we're here."
    ↓
    → Positive response → note in pipeline, monitor for closing
    → Negative/no response from LO → offer to re-route to different LO
    → No response from investor → one more touch at Day 14, then pause
    ↓
Concierge Check-In #2 (Day 21-30)
    "Just checking in — how are things progressing with [LO]?
     We want to make sure you're getting the attention your
     portfolio deserves."
    ↓
    → Deal in progress → note estimated close date
    → Deal fell through → "Would you like us to connect you with
       another specialist in your market?"
    → Deal closed → congratulations + stay in relationship
    ↓
Public Record Verification (Day 30-60)
    Automated check: new mortgage recorded on properties we flagged?
    → Lender matches LO's company = verified close → rev share triggered
    → No recording → deal may still be in process, check again next month
    ↓
Ongoing Relationship (Quarterly)
    "Hi [Investor], we've identified some new opportunities in your
     market — [specific insight about their portfolio]. Would you like
     an updated analysis?"
    → Keeps investor in our ecosystem for future LO clients
    → Generates repeat introductions from same investor pool
```

### Tone Guidelines
- **Concierge, not surveillance.** We're the investor's advocate, not the LO's spy.
- **Specific, not generic.** Reference their portfolio, their market, the specific conversation.
- **Helpful, not pushy.** The follow-up should feel like a service, not a sales tactic.
- **Always offer alternatives.** If the LO isn't performing, we route to someone who will. This is our leverage.

### LO Accountability (Internal)
Track per LO:
- Response time to warm intro (did they actually reach out?)
- Investor feedback (positive/negative/no contact)
- Deals closed vs. intros received (conversion rate)
- LOs with low conversion get fewer intros. LOs who perform get priority routing.

---

## Monthly Operating Costs

| Item | Monthly | Category |
|------|---------|----------|
| Claude Max | $200 | Fixed — AI tooling |
| ATTOM API | $95 | Fixed — mortgage/property data |
| Twilio | ~$15 | Variable — phone validation |
| MillionVerifier | ~$5 | Variable — email validation (credits don't expire) |
| DNC (FTC + Tracerfy) | ~$35-50 | Variable — compliance |
| LO-facing sending domains (1-2 lookalikes) | ~$2 | Fixed — ~$24/yr |
| Investor-facing domain + hosting | ~$5 | Fixed — domain + simple landing page |
| Email warmup tool | $30-50 | Fixed — Instantly or similar |
| **Total** | **~$390-425/mo** |

### Cost Per Fully Enriched Lead (3 Markets Blended)

| Volume | Variable/lead | Fixed/lead | Total/lead |
|--------|---------------|------------|------------|
| 15 (pilot) | ~$1.50 | $27.00 | ~$28.50 |
| 75 (5 pilots) | ~$1.50 | $5.40 | ~$6.90 |
| 150 (subscriptions) | ~$1.50 | $2.70 | ~$4.20 |
| 300+ | ~$1.50 | $1.35 | ~$2.85 |

Not every enriched lead becomes a warm intro — assume 10-20% response rate from investor outreach. So cost per warm intro is roughly 5-10x the cost per enriched lead:

| Warm intros/mo | Cost per warm intro | Revenue per intro (pilot) | Margin |
|----------------|--------------------|-----------------------------|--------|
| 5 | ~$28-57 | $100 | 65-80% |
| 25 | ~$14-28 | $120 | 77-88% |
| 50 | ~$10-20 | $100 | 80-90% |

### Breakeven

| Scenario | Revenue | Total cost | Net |
|----------|---------|------------|-----|
| 1 pilot/month | $500 | ~$425 fixed + ~$50 variable = $475 | +$25 |
| 2 pilots/month | $1,000 | ~$425 + ~$100 = $525 | +$475 |
| 1 pilot + 1 Growth sub | $2,000 | ~$425 + ~$200 = $625 | +$1,375 |
| 3 Growth subs | $4,500 | ~$425 + ~$400 = $825 | +$3,675 |

---

## Phased Implementation

### Phase 1: Infrastructure & Email Warming
**Branch:** `phase1/infrastructure`
**Effort:** ~3-5 hours of setup, then 2-3 weeks of passive warming
**Goal:** Both brands live and warming in background

#### LO-Facing (Still Mind Creative)
- [ ] **1.1** Buy 1-2 lookalike sending domains (stillmindcreative.co, etc.) — ~$24/yr
- [ ] **1.2** Set up mailboxes with Google Workspace or Zoho
- [ ] **1.3** Configure SPF, DKIM, DMARC
- [ ] **1.4** Start email warmup (Instantly.ai or similar) — runs passively

#### Investor-Facing (New Brand)
- [ ] **1.5** Choose brand name and buy domain
  - Check availability for top candidates
  - Needs to feel advisory/trustworthy, not "lead gen"
- [ ] **1.6** Set up mailboxes (zack@[brand].com, team@[brand].com)
- [ ] **1.7** Configure SPF, DKIM, DMARC
- [ ] **1.8** Start email warmup for investor-facing domain
- [ ] **1.9** Build simple landing page (one-page, code-generated or static HTML)
  - Value prop: "We help investment property owners find optimal DSCR lending terms"
  - Brief explanation of service
  - Professional, clean, minimal — just enough for legitimacy when someone Googles the domain

#### API & Compliance
- [ ] **1.10** Confirm ATTOM API access and tier ($95/mo plan)
- [ ] **1.11** Verify Tracerfy API key is active, credits loaded
- [ ] **1.12** Verify MillionVerifier credits available
- [ ] **1.13** Set up FTC DNC registry account (free, first 5 area codes)

**Deliverable:** Both brands live, domains warming, APIs verified.

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

### Phase 3: Sales Assets
**Branch:** `phase3/sales-assets`
**Effort:** ~10-15 hours (dossier template is the heaviest lift)
**Goal:** Everything needed to sell to LOs AND reach out to investors

#### 3A: Sample Dossiers (3 per market = 9 total)
- [ ] **3A.1** Select 3 real leads per market representing each ICP:
  - **Portfolio Landlord** (5+ properties, LLC-owned, out-of-state)
  - **Growing Investor** (2-4 properties, individual, recent acquisitions)
  - **Entity/High Net Worth** (trust/corp, multi-county, wealth signals)
- [ ] **3A.2** Fully enrich each lead — every property, all financing, wealth signals
- [ ] **3A.3** Build dossier generation script — code-generated PDF (Python)
  - Use WeasyPrint (HTML/CSS → PDF) or ReportLab for programmatic generation
  - Professional, clean layout — think consulting report, not spreadsheet dump
  - Find 2-3 visual reference PDFs (investor reports, property analysis sheets) to guide design
  - **Full version** (paid): all data, all contacts, all property addresses
  - **Redacted version** (sample): shows depth but no identifying info
  - Same script generates both — redaction is a flag, not a separate template
- [ ] **3A.4** Generate 9 redacted sample dossier PDFs (3 markets × 3 ICPs)

#### 3B: Market TAM One-Pagers (1 per market = 3 total)
- [ ] **3B.1** For each market, compile:
  - Total investment properties in county
  - Total identified as investor-owned (mailing ≠ property address)
  - Tier 1 leads identified (ICP score threshold)
  - Top zip codes by investor density
  - Average portfolio size, value, equity
  - DSCR market stats (median home price, rental yield, vacancy rate)
  - Top lenders in market (from ATTOM data)
- [ ] **3B.2** Design one-pager template (code-generated PDF, branded)
- [ ] **3B.3** Generate 3 market one-pagers

#### 3C: LO Battlecards (25 per market = 75 total)
- [ ] **3C.1** Use Apollo (remaining credits) to build hit lists:
  - Search: DSCR loan officers, branch managers, mortgage brokers in each metro
  - Cohort B (DSCR Specialist LOs) performed best in experiment — weight toward these
  - Pull: name, title, company, email, phone, LinkedIn URL, company size
- [ ] **3C.2** Enrich beyond Apollo:
  - NMLS Consumer Access — license history, production volume, active states
  - LinkedIn profile review — recent posts, activity, DSCR mentions
  - Company website — team page, specialties, lender relationships
  - REIA membership — speaking at or attending local investor meetups?
- [ ] **3C.3** Build battlecard template per LO:
  - Name, title, company, NMLS#, years licensed
  - Contact: email, phone, LinkedIn
  - Production signals: states licensed, company size, DSCR focus indicators
  - Personalization hooks: recent LinkedIn posts, REIA involvement, lender relationships
  - Outreach angle: why OUR platform matters for THIS person
  - Objection pre-handles based on their profile
- [ ] **3C.4** Generate 75 battlecards (stored as structured data)

#### 3D: Investor Outreach Templates
- [ ] **3D.1** Build outreach sequences per ICP segment:
  - **Portfolio Landlord:** angle on portfolio-level DSCR optimization, cash-out potential
  - **Growing Investor:** angle on scaling strategy, next acquisition financing
  - **Entity/HNW:** angle on sophisticated lending options, rate optimization
- [ ] **3D.2** Build concierge QC follow-up templates (see QC Loop section above)
- [ ] **3D.3** Build re-routing templates (for when an LO underperforms)

**Deliverable:** 9 sample dossier PDFs, 3 market one-pagers, 75 LO battlecards, investor outreach + QC templates.

---

### Phase 4: Outbound — Two Tracks (Manual First)
**Branch:** `phase4/outbound`
**Effort:** ~3-5 hours to write sequences, then ~45 min/day for manual sends across both tracks
**Goal:** Land first LO client AND start investor conversations

#### Track A: LO Prospecting (via Still Mind Creative)
- [ ] **4A.1** LO sequence design (per prospect):
  - **Day 0:** LinkedIn connection request (personalized from battlecard)
  - **Day 1:** If accepted → LinkedIn DM #1 (value-first, reference their market)
  - **Day 3:** Cold email #1 (attach market one-pager PDF)
  - **Day 5:** LinkedIn DM #2 (share a specific insight about their market)
  - **Day 7:** Cold email #2 (attach sample dossier PDF, redacted)
  - **Day 10:** LinkedIn DM #3 (direct ask — "want to see qualified investors in your market?")
  - **Day 14:** Cold email #3 (case study / social proof once available)
- [ ] **4A.2** Write messaging templates using battlecard fields
  - Tone: peer-to-peer. "I built a platform that identifies investors ready for DSCR lending — you're someone who'd actually use this."
  - Key differentiator: "We don't sell you a list. We send you investors who already raised their hand."
- [ ] **4A.3** Send manually to first 10-15 Wake County LOs
- [ ] **4A.4** Iterate based on responses

#### Track B: Investor Outreach (via Investor-Facing Brand)
- [ ] **4B.1** Begin ONLY after at least 1 LO is signed (even as pilot)
  - We need someone to route warm intros TO before we start generating them
  - Exception: can start 5-10 test sends earlier to validate messaging/response rates
- [ ] **4B.2** Investor sequence design (per ICP):
  - **Email 1:** Value-first. Reference their specific portfolio signals (without being creepy). "We've been analyzing investment property portfolios in [market] and noticed some interesting refinancing opportunities..."
  - **Email 2 (Day 5):** Specific insight. "Properties acquired in 2021-2022 with rates above 7% are strong candidates for DSCR refi at current rates..."
  - **Email 3 (Day 10):** Direct offer. "Would it be helpful if we connected you with a DSCR lending specialist who focuses on [their market]? No cost, no obligation."
- [ ] **4B.3** Send manually, track response rates per ICP segment and market
- [ ] **4B.4** For respondents: qualify, then warm intro to LO client

#### Track C: Concierge QC (Begins After First Warm Intro)
- [ ] **4C.1** Day 7-10 after each intro: concierge check-in with investor
- [ ] **4C.2** Track all feedback in pipeline tracker
- [ ] **4C.3** Flag non-responsive LOs — follow up with LO first, re-route if needed

**Deliverable:** Active LO pipeline, first investor conversations, QC loop running.

---

### Phase 5: Automation (N8N)
**Branch:** `phase5/n8n-automation`
**Effort:** ~8-12 hours to build workflows (after manual outreach validates messaging)
**Goal:** Automate the repeatable parts of both outbound tracks + QC loop

#### Why N8N Fits
Three distinct workflows with conditional logic, API integrations, and timing:
1. **LO outbound:** battlecard → personalize → send → follow up → track
2. **Investor outreach:** enriched lead → personalize by ICP → send → qualify responses → warm intro
3. **Concierge QC:** intro made → schedule check-in → send → process feedback → alert if action needed

#### Implementation
- [ ] **5.1** Install N8N (self-hosted or cloud)
- [ ] **5.2** Build LO outbound workflow:
  - Trigger: new LO added to battlecard sheet
  - Claude API generates personalized email from battlecard
  - Human review checkpoint → send → schedule follow-ups
- [ ] **5.3** Build investor outreach workflow:
  - Trigger: new enriched lead batch ready
  - Claude API generates personalized email from dossier data + ICP segment
  - Human review checkpoint → send from investor-facing domain → track responses
  - On reply: notify Zack, qualify, prepare warm intro
- [ ] **5.4** Build concierge QC workflow:
  - Trigger: warm intro made (logged in tracker)
  - Auto-schedule Day 7 and Day 21 check-ins
  - Generate personalized follow-up referencing the specific LO and conversation
  - Human review → send → log feedback
  - Alert if negative feedback → suggest re-route
- [ ] **5.5** Build LinkedIn daily digest:
  - N8N can't automate LinkedIn (TOS violation risk)
  - Instead: daily summary of "send these messages today" with pre-written copy
- [ ] **5.6** Build public record monitoring:
  - Monthly check: new mortgages recorded on properties we flagged?
  - Cross-reference lender with LO's company
  - Auto-notify when deal verified

**Deliverable:** Semi-automated three-track engine. Zack reviews/approves, N8N handles timing, personalization, and tracking.

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
- [ ] **6.3** Case studies (once pilots close):
  - "LO closed $450K DSCR deal from a warm intro in 18 days"
  - Anonymized but specific

**Format:** Code-generated PDFs. Professional, clean, 1-2 pages max.

---

### Phase 7: Pricing Finalization
**Effort:** Informed by first 3-5 pilot conversations
**Goal:** Lock pricing based on real market feedback

- [ ] **7.1** Test pilot pricing ($500/5 warm intros) in first LO conversations
  - Track: objections, counter-offers, willingness to pay
  - Note: do they want more intros? Different data? Ongoing?
- [ ] **7.2** Refine based on feedback:
  - If "too expensive" → warm intros aren't converting, fix investor outreach quality
  - If "too cheap" → raise price or add premium tier
  - If "I want ongoing" → subscription model validated
  - If "what about performance?" → rev share conversation opens naturally
- [ ] **7.3** Finalize pricing tiers and update all collateral
- [ ] **7.4** Build pilot → subscription → rev share upgrade path

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
├── phase6/collateral
└── phase7/pricing
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
    ↓ runs passively            Both LO + investor domains warming simultaneously
Phase 2 (Pipeline)         ←── can start same day as Phase 1
    ↓ produces enriched data
Phase 3 (Sales Assets)     ←── needs Phase 2 data to build real dossiers + outreach templates
    ↓ produces dossiers, battlecards, investor sequences
Phase 4 Track A (LO Sales) ←── needs Phase 3 assets + Phase 1 warm LO domain
Phase 4 Track B (Investor) ←── needs Phase 3 + Phase 1 warm investor domain + at least 1 LO signed
Phase 4 Track C (QC Loop)  ←── needs first warm intro made
    ↓ validates messaging
Phase 5 (N8N Automation)   ←── needs Phase 4 learnings (what messages work)
Phase 6 (Collateral)       ←── ongoing, informed by Phase 4 conversations
Phase 7 (Pricing)          ←── informed by Phase 4 pilot feedback
```

**Hard blockers:**
- Email domain warming (~2-3 weeks passive) — start immediately
- Investor outreach requires at least 1 LO client to route intros to

**LinkedIn outreach to LOs can start as soon as battlecards are ready**, independent of email warming. That's the fastest path to first LO client.

**Total estimated effort to first LO outreach:** ~25-35 hours of active work (Phases 1-4A)
**Total estimated effort to first investor outreach:** +5-8 hours on top (Phase 4B), but gated by having an LO to route to

---

## Open Questions

1. **Investor-facing brand name** — needs to be chosen and domain purchased. Should feel advisory/trustworthy.
2. **CRM** — CSV/Google Sheets tracker for now. Revisit when 10+ active conversations across both tracks.
3. **NC SoS paid subscription** — worth investigating for entity resolution quality. Contact subscriptions@sosnc.gov. Not blocking.
4. **ATTOM tier** — $95/mo to start. Monitor API usage as 3 markets ramp.
5. **Landing page complexity** — single static HTML page is fine to start. Can evolve later.

## Resolved Decisions

- **LO outreach domain:** Still Mind Creative lookalikes for cold volume protection. Primary conversations from zack@stillmindcreative.com.
- **Investor outreach:** Separate brand/domain. We own the investor relationship. LO gets warm intros, not raw data.
- **Concierge QC:** Post-introduction follow-up with investors. Builds trust, verifies deals, enables re-routing.
- **Collateral format:** Code-generated PDFs via Python (WeasyPrint or ReportLab). No Canva.
- **Timelines:** No calendar dates. Phases gated by dependencies. Effort estimates in hours.

---

## Success Metrics

| Metric | Target | Gate |
|--------|--------|------|
| Markets with enriched data | 3 | Before any outreach |
| Sample dossiers created | 9 | Before any LO outreach |
| LO battlecards created | 75 | Before any LO outreach |
| LO outreach sent | 25+ | After assets complete |
| LO conversations started | 5+ | After LO outreach begins |
| First LO pilot signed | 1 | Before investor outreach at scale |
| Investor outreach sent | 50+ | After LO signed |
| Warm intros delivered | 5+ | After investor responses |
| Concierge QC sent | 5+ | After warm intros made |
| First verified deal close | 1 | After pipeline matures |

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
├── investor_outreach/
│   ├── sequences/               # Email templates per ICP segment
│   └── qc_templates/            # Concierge follow-up templates
├── collateral/                  # Existing — one-pager, sample dossier
├── outreach/                    # Existing — LO sequences, tracker
└── prospects/                   # Existing — LO lists, experiment data

deployments/
├── north_carolina/CONFIG.md     # Existing
├── ohio/CONFIG.md               # NEW
└── indiana/CONFIG.md            # NEW

investor-brand/
├── index.html                   # Landing page
├── styles.css
└── assets/                      # Logo, images
```
