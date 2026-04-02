# DSCR Lead Intelligence — Launch Blueprint

## Mission

Build and sell enriched DSCR investor intelligence dossiers across U.S. markets. Four buyer types (LOs, Branch Managers, RE Agents, RE Brokers), per-lead and subscription pricing. We build the data product, buyers do their own outreach.

## The Model

```
Public records → Pipeline (score, enrich, validate, ATTOM 7-endpoint) → Two product tiers
    → Semi-Enriched ($10-15/lead): contacts + portfolio summary + talking points
    → Full Dossier ($60-100/lead): complete PDF tear sheet with every property, financing, AVM, rental, permits
        → Sell to LOs, branch managers, RE agents, RE brokers
            → They do their own outreach to investors
```

---

## Progress (Last updated: 2026-03-20)

| Phase | Status | Key Output |
|-------|--------|------------|
| **South Florida Pipeline** | ✅ Complete | 654K parcels → 7,537 qualified → 500 pilot fully enriched (157 cols). Frank (CCM, Boca Raton) ON HOLD. |
| **Wake County Pipeline** | ⚠️ Scored, not enriched | 373K scored → 312K qualified. 33 samples only. Bulk pipeline (steps 04-08) not run. Entity resolution blocked. |
| **ATTOM Integration** | ⚠️ 1 of 7 endpoints | New API key active (1,000 credits). All 7 endpoints confirmed. Script needs update to call all 7. |
| **Showcase Leads** | 🔴 In progress | Need 30 fully enriched (15 FL + 15 Wake) with all 7 ATTOM endpoints. |
| **Sales Assets** | 🔴 Not started | Tear sheet template, redacted samples, pitch materials needed. |
| **LO Outbound** | 🔴 Not started | Blocked on showcase + tear sheets. |

### Resolved (March 19, 2026)

- **Wholesale lenders are NOT our buyer.** Failed pitch confirmed they have internal data teams. Our buyers are individual LOs, branch managers, RE agents, and RE brokers.
- **ATTOM is central, not optional.** Christine Woo provided new key with 1,000 credits. All 7 endpoints active. 7 calls per fully enriched lead.
- **Charlotte/Mecklenburg dropped.** Never was a real target — incorrectly assumed. Two markets: South FL + Wake County.
- **Apollo cancelled.** Returns nothing for RE investors ($99/mo wasted).
- **Pricing corrected.** Per-lead: $10-15 semi-enriched, $60-100 full dossier. Subscription: $300-2,500/mo depending on buyer type. Volume discounts capped at 35%.

---

## Target Markets

| # | Market | Counties | FIPS | Status |
|---|--------|----------|------|--------|
| 1 | **South Florida** | Palm Beach, Broward | 12099, 12011 | Pipeline built, 500 pilot enriched, Frank ON HOLD |
| 2 | **Raleigh, NC** | Wake | 37183 | 373K scored, bulk enrichment not run |

**Future (research only):** Cuyahoga OH (Cleveland), Marion IN (Indianapolis)

---

## Pricing Strategy

Four buyer types, two product tiers, per-lead and subscription options.

### Lead Quality Tiers

| Tier | ICP Score | What it means |
|------|-----------|---------------|
| **Tier 1 — Hot** | 50+ pts | Multiple strong signals: portfolio landlord, LLC-owned, out-of-state, recent acquisitions, high equity |
| **Tier 2 — Warm** | 30-49 pts | Moderate signals: absentee owner, some equity, investment property confirmed |
| **Tier 3 — Nurture** | 15-29 pts | Weak signals. Not listed for sale. Demonstrates pipeline depth. |

### Per-Lead Pricing

| Product | Tier 1 (Hot) | Tier 2 (Warm) |
|---------|-------------|---------------|
| **Semi-Enriched** (CSV + portfolio + talking points) | $15/lead | $10/lead |
| **Full Dossier** (PDF tear sheet + all data) | $100/lead | $60/lead |

Volume discounts: 5% increments from 26+ leads, capped at 35%.

### Subscription Pricing

| Buyer | Monthly | Leads Included |
|-------|---------|---------------|
| LO Starter | $500/mo | 25 leads + tear sheets |
| LO Growth | $750/mo | 50 leads + tear sheets |
| Branch Manager | $1,500/mo | 150 leads + team feed + market report |
| Agent Starter | $300/mo | 25 investor profiles (no financing fields) |
| Agent Growth | $500/mo | 50 investor profiles |
| Broker Office | $800/mo | 100 investor profiles + office distribution |

**Strategy:** Start with per-lead (lower commitment = faster first sale). Convert repeat buyers to subscription.

### Two Product Versions

- **LO version:** Full dossier with financing intel (lender, rate, maturity, DSCR)
- **Agent version:** DSCR/mortgage fields STRIPPED (RESPA compliance — agents can't steer financing)

### Unit Economics

| Metric | Value |
|--------|-------|
| COGS/lead (trial) | ~$0.02 |
| COGS/lead (post-trial with ATTOM) | ~$0.15 |
| Best margin (Tier 1 dossier) | $99.85 (99.8%) |
| Worst margin (Tier 2 semi @ 35% off) | $6.35 (97.6%) |
| Breakeven on $400/mo fixed | 27 semi-enriched leads |

---

## Monthly Operating Costs

| Item | Monthly | Category |
|------|---------|----------|
| Claude Max | $200 | Fixed — AI tooling |
| ATTOM API (post-trial) | $95 | Fixed — 7-endpoint enrichment |
| Twilio | ~$15 | Variable — phone validation |
| MillionVerifier | ~$5 | Variable — email validation |
| DNC/compliance | ~$40 | Variable — FTC scrub every 31 days |
| Sending domain + email warmup | ~$35 | Fixed — Instantly.ai or similar |
| Hosting/tools | ~$10 | Fixed — GitHub, compute |
| **Total** | **~$400/mo** |

---

## Phased Implementation

### NOW — Week 1: Build Showcase

**Goal:** 30 fully enriched showcase leads with all 7 ATTOM endpoints.

| # | Task | Credits | Status |
|---|------|---------|--------|
| 1 | Update ATTOM script to call all 7 endpoints | 0 | In progress |
| 2 | Select 15 FL leads from pilot 500 (5 per segment) | 0 | In progress |
| 3 | Select 15 Wake leads from scored data (5 per segment) | 0 | Pending |
| 4 | Run 7-endpoint ATTOM enrichment on 15 FL leads | 105 | Pending |
| 5 | Skip trace 15 Wake leads (Tracerfy) | 0 | Pending |
| 6 | Run 7-endpoint ATTOM enrichment on 15 Wake leads | 105 | Pending |
| 7 | Validate contacts (Twilio + MillionVerifier) on all 30 | 0 | Pending |
| 8 | Build tear sheet template (PDF, one page per lead) | 0 | Pending |
| 9 | Generate 30 tear sheets with real data | 0 | Pending |

**ATTOM credits used: 210. Remaining: 790.**

### NEXT — Weeks 2-3: Sales Collateral + First Conversations

| # | Task |
|---|------|
| 1 | Build redacted sample package (5 tear sheets with contact info blurred) |
| 2 | Create buyer-specific pitch decks (LO, Branch Mgr, Agent, Broker — 1 page each) |
| 3 | Finalize compliance one-pager for distribution |
| 4 | Frank works 15 FL showcase leads (track: outreach, response rate, pipeline) |
| 5 | Zack works 15 Wake leads locally (same tracking) |
| 6 | LinkedIn outreach: 15 DSCR LOs in South FL |
| 7 | LinkedIn outreach: 10 DSCR LOs in Raleigh |
| 8 | LinkedIn outreach: 10 investor-specialist RE agents (both markets) |

### LATER — Weeks 4-8: First Revenue

| # | Task |
|---|------|
| 1 | Close first LO customer(s) — per-lead pricing |
| 2 | Fulfill orders using ATTOM reserve credits (790 ÷ 7 = ~112 leads) |
| 3 | Collect feedback on tear sheet format + data quality |
| 4 | Run Wake County bulk pipeline (Steps 04-08) if demand justifies |
| 5 | Decide on NC entity resolution (paid NC SoS subscription vs name parsing) |
| 6 | Evaluate ATTOM paid subscription ($95/mo) — subscribe if showcase converts |

### FUTURE — Months 3-6: Scale

| # | Task |
|---|------|
| 1 | Convert per-lead buyers to subscription pricing |
| 2 | Pitch branch managers using LO customer conversion data |
| 3 | Pitch RE brokers using agent customer data |
| 4 | Activate Cuyahoga OH and/or Marion IN |
| 5 | Revenue target: $5K-10K/month recurring (10-20 customers) |

---

## ATTOM Credit Strategy

| Item | Credits |
|------|---------|
| Total available | 1,000 |
| Showcase (30 leads × 7 endpoints) | 210 |
| Reserved for paying customers | 790 |
| Max fully enriched from reserve | ~112 leads |

**Do NOT burn credits carelessly.** Minimum viable enrichment → showcase → sell → revenue justifies more credits.

---

## Git Protocol

### Branch Strategy
```
master (production — stable)
├── phase1/infrastructure
├── phase2/pipeline
│   ├── phase2/florida
│   └── phase2/wake-county
├── phase3/sales-assets
├── phase4/outbound
└── phase5/automation
```

### Commit Standards
- Descriptive messages: "Add Wake County property parser for NC OneMap format"
- Reference phase: "Phase 2: Adapt ICP scoring for NC data fields"
- No commits with secrets (.env, API keys, client data)
- .gitignore: all CSV data files, .env, cache directories

---

## Moat Protection

- No source attribution — dossiers show WHAT we know, never HOW
- Entity resolution (LLC → person) takes 6+ sources to replicate
- ICP scoring logic is proprietary
- ATTOM 7-endpoint enrichment assembled into a single dossier — no one sells this bundle
- Semi-exclusive model: limited buyers per market

---

## Open Questions

1. **NC SoS entity resolution** — Paid subscription ($200-500/yr) vs name parsing workaround. Not blocking for MVP.
2. **ATTOM post-trial** — $95/mo starter if showcase converts to sales. Monitor.
3. **CRM delivery** — CSV + tear sheets for now. Airtable/GoHighLevel if customers request it.

## Risks

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Frank doesn't activate FL leads | Lose FL proof of concept | HIGH | Zack tests locally in Wake |
| LOs don't work leads properly | Low conversion, blame data | HIGH | Include outreach playbook + track which leads convert |
| Compliance objection kills deals | Lost sales | MEDIUM | Lead with compliance one-pager |
| NC entity resolution too hard | Lower Wake data quality | HIGH | Name parsing + portfolio detection as proxy |
| ATTOM trial expires before proving value | Lose mortgage enrichment | MEDIUM | Only burn 210/1,000 on showcase; pipeline works without ATTOM |

---

## Success Metrics

| Metric | Target | Gate |
|--------|--------|------|
| Showcase leads fully enriched | 30 | Before any outreach |
| Tear sheet template working | Yes | Before any outreach |
| Redacted sample package | 5 tear sheets | Before LO outreach |
| LO conversations started | 5+ | After outreach begins |
| First lead sale | 1 | After conversations |
| Monthly revenue | $1,000+ | After first few sales |

---

*All numbers sourced from actual pipeline data. See `DSCR_Business_Plan_DRAFT.md` for the canonical business plan and `HANDOFF_20260319.md` for the March 19 session decisions.*
