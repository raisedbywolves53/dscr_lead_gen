# DSCR Lead Intelligence — Claude CLI Context

## What This Is

A data product company that produces enriched investor intelligence dossiers from public property records. We identify investment property owners, enrich through a 20-step automated pipeline (7+ data sources), score by DSCR opportunity, and package for four buyer types. Built to be portable across any U.S. market.

**We are NOT a lead gen agency.** We build the data product — scored, enriched, contact-validated investor dossiers. The buyer does their own outreach.

## Business Model

**What we sell:** Investor intelligence (semi-enriched CSV or full PDF tear sheet per lead)
**Who buys it:** LOs, Branch Managers, RE Agents, RE Brokers (NOT wholesale lenders — they have internal data teams)
**Pricing:** $10-15/lead semi-enriched, $60-100/lead full dossier, or $300-2,500/mo subscription depending on buyer type

### Four Buyer ICPs (Our Customers)

| Buyer | What They Get | Price Range |
|-------|--------------|-------------|
| **Loan Officer** | Full dossier with financing intel, tear sheets, outreach playbook | $15/lead, $100/dossier, $500-750/mo |
| **Branch Manager** | Monthly CRM feed, territory segmentation, market report | $1,500-2,500/mo |
| **RE Agent** | Investor profiles with DSCR/mortgage fields STRIPPED (RESPA) | $300-500/mo or $10-12/lead |
| **RE Broker** | Same as agent, office-wide distribution | $800-1,500/mo |

## Active Markets

| Market | Counties | Status |
|--------|----------|--------|
| South Florida | Palm Beach, Broward | Pipeline built: 7,537 qualified, 500 pilot fully enriched (157 cols). Frank (LO at CCM, Boca Raton) is test buyer — ON HOLD awaiting his setup. |
| North Carolina | Wake | 373K scored, 312K qualified, 33 samples enriched. Bulk pipeline (steps 04-08) not run at scale. Entity resolution blocked (NC SoS no free bulk data). |

**Future markets (research only):** Cuyahoga OH (Cleveland), Marion IN (Indianapolis)

---

## Canonical Documents

| Doc | Role |
|-----|------|
| `docs/business/DSCR_Business_Plan_DRAFT.md` | **THE business plan** — grounded in actual pipeline data, correct pricing, correct markets |
| `docs/business/DSCR_PnL_Model.xlsx` | P&L spreadsheet — both pricing models, editable blue inputs |
| `archive/outdated_docs/HANDOFF_20260319.md` | Session handoff from March 19 pivot (reference only, partially outdated) |

## Doc Structure

### System Docs (How the platform works)
| Doc | What It Covers |
|-----|---------------|
| `docs/SYSTEM_OVERVIEW.md` | Architecture, pipeline stages, tech stack, deployment model |
| `docs/ICP_PLAYBOOK.md` | Borrower ICP segments (11 types), scoring matrix 0-100, signals, outreach angles |
| `docs/ENRICHMENT_STACK.md` | Every vendor: cost, verdict, gotchas, API config |
| `docs/PIPELINE_GUIDE.md` | Step-by-step execution, commands, rate limits, benchmarks |
| `docs/OUTPUT_SCHEMA.md` | Canonical column definitions (157 columns) |
| `docs/COMPLIANCE.md` | DNC, TCPA, state-specific calling rules |
| `docs/LEGAL_COMPLIANCE_ANALYSIS.md` | Full FCRA/RESPA/TCPA legal analysis |
| `docs/ATTOM_API_Integration_Spec.docx` | All 7 ATTOM endpoints — fields, URLs, parameters |

### Deployment Configs (What changes per market)
| Doc | What It Covers |
|-----|---------------|
| `deployments/TEMPLATE.md` | Checklist for deploying in a new market |
| `deployments/florida/CONFIG.md` | FL data sources: FDOR, SunBiz, DBPR, county codes, compliance |
| `deployments/florida/CLIENT.md` | FL deployment: CCM, PB+Broward |
| `deployments/north_carolina/CONFIG.md` | NC data sources: OneMap, SoS, Register of Deeds, compliance |

### Pipeline Code
| Location | What It Contains |
|----------|-----------------|
| `scrape/scripts/` | All pipeline scripts (01-20 + showcase/demo builders) |
| `scrape/config/` | JSON configs (scoring weights, counties) |
| `scrape/data/` | Pipeline output data (gitignored) |

### Archive
| Location | What It Contains |
|----------|-----------------|
| `archive/` | Old pipeline_v1, FL client docs, pre-consolidation docs, research memos |
| `archive/airtable_crm/` | Airtable CRM scripts (archived — may revisit later) |

---

## Pipeline Architecture

```
FOUNDATION (Steps 01-08)
01 Download Property Data    (state-specific)
02 Parse & Standardize       (state-specific)
03 Score & Filter by ICP     (config-driven)
04 Entity Resolution         (state-specific: SoS registry)
05 Contact Enrichment        (state-agnostic)
08 Skip Trace (Tracerfy)     (state-agnostic)
05b Merge Sources            (state-agnostic)
06 Validate (phone/email)    (state-agnostic)
07 Export Campaign-Ready     (state-agnostic)
─────────────────────────────────────────────
INTELLIGENCE (Steps 10-20)
11 Clerk Mortgage Records    (county-specific)
12 Purchase History          (state-specific)
13 Rental Estimates          (state-agnostic: HUD)
14 Wealth Signals            (state-agnostic: FEC/990)
15 Network Mapping           (state-agnostic)
16 ATTOM Enrichment          (state-agnostic: 7 endpoints)
20 Build Dossier             (state-agnostic)
─────────────────────────────────────────────
TARGETING (Steps 21-22)
21 Market Monitor            (state-agnostic)
22 PPP Targeting             (state-agnostic: HMDA + lender classification)
```

### Step 22: Prepayment Penalty Targeting (NEW — April 2026)
Identifies DSCR borrowers approaching prepayment penalty expiration.
- **Two models:** HMDA definitive (free federal data, 2.4M loans) + inference (54-lender classification)
- **Config:** `scrape/config/dscr_lenders.json` — curated DSCR lender database
- **Script:** `scrape/scripts/22_prepayment_penalty_targeting.py`
- **Deliverable:** `scrape/scripts/build_ppp_deliverable.py` — branded Excel workbook
- **Data:** `scrape/data/hmda/` (HMDA downloads, ~900MB, gitignored) + `scrape/data/ppp_targeting/`

---

## Enrichment Stack (Tested & Verified)

| Vendor | Role | Cost | Status |
|--------|------|------|--------|
| **ATTOM** | Property + mortgage + AVM + rental + sales + tax + permits | 7 endpoints/lead | **CENTRAL** — core product differentiator. 1,000 trial credits (new key from Christine Woo). 210 allocated for 30 showcase leads, 790 reserved. |
| Tracerfy | Skip trace | $0.02/match | **PRIMARY** — charges per match, not upload. 45% match rate. |
| MillionVerifier | Email validation | $4.90/2K | **USE** — credits never expire |
| Twilio v2 | Phone type | $0.008/lookup | **USE** — must use v2 API |
| Datazapp | Batch skip trace | $125 minimum | **AVOID** — terrible for small runs |
| Apollo.io | B2B enrichment | $99/mo | **CANCELLED** — returns nothing for RE investors. Do not use. |

### ATTOM 7-Endpoint Strategy

Each fully enriched lead requires 7 API calls (1 credit each):

| Endpoint | What It Returns |
|----------|----------------|
| `/property/detailmortgageowner` | Lender, loan amount, rate, maturity, owner resolution |
| `/property/expandedprofile` | Beds, baths, sqft, year built, lot, zoning, REO/quit claim flags |
| `/attomavm/detail` | AVM estimate, confidence, high/low range, appreciation |
| `/valuation/rentalavm` | Property-specific monthly rent estimate + range |
| `/saleshistory/detail` | 10-year transaction history, cash vs mortgage flag |
| `/assessment/detail` | Tax assessment, land vs improvement split, annual tax |
| `/property/buildingpermits` | Renovation permits, job values, contractor names |

**Budget:** 1,000 credits / 7 = ~142 fully enriched leads max. Showcase: 30 leads (210 credits). Reserve: 790 for paying customers.

---

## Unit Economics

| Metric | Value |
|--------|-------|
| COGS/lead (trial) | ~$0.02 |
| COGS/lead (post-trial with ATTOM) | ~$0.15 |
| Monthly fixed costs | ~$400 |
| Margin on $15 semi-enriched | 99% |
| Margin on $100 full dossier | 99.8% |
| Breakeven | 27 semi-enriched leads/month |

---

## Key Technical Notes

### Dependencies
```bash
pip install pandas openpyxl requests beautifulsoup4 python-dotenv
```

### API Keys (.env in scrape/)
```
ATTOM_API_KEY=           # CENTRAL: 7-endpoint property enrichment
TRACERFY_API_KEY=        # Primary skip trace
MILLIONVERIFIER_API_KEY= # Email validation
TWILIO_ACCOUNT_SID=      # Phone validation
TWILIO_AUTH_TOKEN=
FEC_API_KEY=DEMO_KEY     # Wealth signals (free)
AIRTABLE_PAT=            # CRM (archived, optional)
```

### Data Quality Gotchas
- Always load property CSVs with `dtype=str` (booleans are strings)
- Entity names (LLC/Corp/Trust) → blank first/last for skip trace
- Tracerfy charges per MATCH, not per upload (much cheaper than estimated)
- MillionVerifier: if credits exhausted, API returns errors that look like "invalid"
- Twilio: must use v2 API (v1 returns no carrier data on free trial)
- ATTOM: use APN + FIPS as primary lookup, address as fallback

---

## People

- **Zack** — Builder, based in Raleigh NC. Non-developer (vibe coder). Uses Claude Desktop + CLI in VS Code.
- **Frank Christiano** — LO partner at CrossCountry Mortgage (CCM), based in Boca Raton FL. FL pipeline built for him but ON HOLD (hasn't set up Airtable).
- **Christine Woo** — ATTOM API contact. Provided new API key with 1,000 credits. Confirmed all 7 endpoints active.

## Ownership

- **Business:** Still Mind Creative
- **Goal:** Portable data product deployable in any U.S. market, sold to LOs/agents/brokers
- **Repo:** https://github.com/raisedbywolves53/dscr_lead_gen.git
