# DSCR Lead Generation System — Claude CLI Context

## What This Is

A portable, automated lead generation platform for **DSCR (Debt Service Coverage Ratio) mortgage loans**. Deployable in any U.S. market for any loan originator. Identifies investment property owners from public records, enriches with contact data, scores by opportunity, and exports to CRM/outreach tools.

## Active Deployments

| Market | Counties | Client | Status |
|--------|----------|--------|--------|
| Florida | Palm Beach, Broward | Frank Christiano (CCM) | Pipeline built, 7,537 leads, ON HOLD |
| North Carolina | Wake, Mecklenburg | TBD (prospecting LOs) | Research complete, not yet built |

---

## Doc Structure

### System Docs (How the platform works — generic)
| Doc | What It Covers |
|-----|---------------|
| `docs/SYSTEM_OVERVIEW.md` | Architecture, pipeline stages, tech stack, deployment model |
| `docs/ICP_PLAYBOOK.md` | All ICP segments, scoring matrix, signals, outreach angles |
| `docs/ENRICHMENT_STACK.md` | Every vendor: cost, verdict, gotchas, API config |
| `docs/PIPELINE_GUIDE.md` | Step-by-step execution, commands, rate limits, benchmarks |
| `docs/OUTPUT_SCHEMA.md` | Canonical column definitions (157 columns) |
| `docs/CRM_SETUP.md` | Airtable base design, Google Sheets MVP, setup process |
| `docs/COMPLIANCE.md` | DNC, TCPA, state-specific calling rules |

### Deployment Configs (What changes per market/client)
| Doc | What It Covers |
|-----|---------------|
| `deployments/TEMPLATE.md` | Checklist for deploying in a new market |
| `deployments/florida/CONFIG.md` | FL data sources: FDOR, SunBiz, DBPR, county codes, compliance |
| `deployments/florida/frank/CLIENT.md` | Frank's deployment: CCM, PB+Broward, Airtable base, costs |
| `deployments/north_carolina/CONFIG.md` | NC data sources: OneMap, SoS, Register of Deeds, compliance |

### Pipeline Code
| Location | What It Contains |
|----------|-----------------|
| `scrape/scripts/` | All pipeline scripts (01-20) |
| `scrape/config/` | JSON configs (scoring weights, counties, enrichment sources) |
| `scrape/data/` | Pipeline output data (gitignored) |
| `scrape/CLAUDE.md` | Pipeline-specific context |
| `scrape/PIPELINE.md` | Execution spec for scripts |

### CRM & Output
| Location | What It Contains |
|----------|-----------------|
| `airtable/` | CRM integration scripts (build, upload, validate) |
| `docs/airtable/` | Step-by-step Airtable setup guides (views, automations, interfaces) |
| `scrape/scripts/build_google_sheets.py` | Google Sheets export |

### Archive
| Location | What It Contains |
|----------|-----------------|
| `archive/README.md` | Index of all archived content |
| `archive/pipeline_v1/` | Original Palm Beach pipeline (superseded by scrape/) |
| `archive/florida_frank/` | Frank-specific docs |
| `archive/docs_v1/` | Pre-consolidation docs |
| `archive/research/` | Deep-dive research memos (Feb 2026) |

---

## Pipeline Architecture

```
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
11 Clerk Mortgage Records    (county-specific)
12 Purchase History          (state-specific)
13 Rental Estimates          (state-agnostic: HUD)
14 Wealth Signals            (state-agnostic: FEC/990)
15 Network Mapping           (state-agnostic)
16 Life Events               (county-specific)
20 Build Dossier             (state-agnostic)
```

---

## Enrichment Stack (Tested & Verified)

| Vendor | Role | Cost | Verdict |
|--------|------|------|---------|
| Tracerfy | Skip trace | $0.02/match | PRIMARY — charges per match, not upload |
| MillionVerifier | Email validation | $4.90/2K | USE — credits never expire |
| Twilio v2 | Phone type | $0.008/lookup | USE — must use v2 API |
| Apollo.io | B2B enrichment | $99/mo | CANCEL — returns nothing for RE investors |
| Datazapp | Batch skip trace | $125 minimum | AVOID — terrible for small runs |
| ATTOM | Mortgage data | $95-500/mo | OPTIONAL — 133/500 match rate |

---

## Key Technical Notes

### Dependencies
```bash
pip install pandas openpyxl requests beautifulsoup4 python-dotenv
```

### API Keys (.env)
```
TRACERFY_API_KEY=        # Primary skip trace
MILLIONVERIFIER_API_KEY= # Email validation
TWILIO_ACCOUNT_SID=      # Phone validation
TWILIO_AUTH_TOKEN=
ATTOM_API_KEY=           # Optional: mortgage data
TWOCAPTCHA_API_KEY=      # Optional: clerk portal CAPTCHA
AIRTABLE_API_TOKEN=      # CRM
FEC_API_KEY=DEMO_KEY     # Wealth signals (free)
```

### Data Quality Gotchas
- Always load property CSVs with `dtype=str` (booleans are strings)
- Entity names (LLC/Corp/Trust) → blank first/last for skip trace
- Tracerfy charges per MATCH, not per upload (much cheaper than estimated)
- MillionVerifier: if credits exhausted, API returns errors that look like "invalid"
- Twilio: must use v2 API (v1 returns no carrier data on free trial)

---

## Contact & Ownership

- **Builder:** Zack (building system to sell to LOs)
- **Current client:** Frank Christiano, CCM (FL, on hold)
- **Next target:** NC loan originators (prospecting)
- **Goal:** Portable system deployable in any U.S. market
- **Repo:** https://github.com/raisedbywolves53/dscr_lead_gen.git
