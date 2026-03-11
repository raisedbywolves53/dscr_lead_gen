# Deployment Template — New Market Checklist

Use this checklist when deploying the DSCR lead gen system in a new state/market.

---

## 1. Market Definition

- [ ] **State:** ___
- [ ] **Target counties:** ___
- [ ] **Loan originator:** ___ (name, company, NMLS#)
- [ ] **Wholesaler/lender:** ___ (Change Wholesale, etc.)
- [ ] **Target lead volume:** ___

---

## 2. Data Source Research

### Property Records (REQUIRED)
- [ ] Identify state property tax/assessment data source
- [ ] Confirm bulk download availability (format, cost, frequency)
- [ ] Map column names to standard schema (owner, address, value, use code, sale info)
- [ ] Identify homestead/owner-occupied indicator field
- [ ] Identify property use codes (residential, multi-family, condo, etc.)
- [ ] Document county codes for target counties

### Entity Registry (REQUIRED)
- [ ] Identify Secretary of State business search portal
- [ ] Test search functionality (by entity name)
- [ ] Confirm officer/agent data is available
- [ ] Check for bulk download or API access
- [ ] Document rate limits and anti-bot measures

### County Clerk / Register of Deeds (HIGHLY RECOMMENDED)
- [ ] Identify online search portal for each target county
- [ ] Test search by owner name and/or parcel ID
- [ ] Confirm mortgage recording data is available (lender, amount, date)
- [ ] Check for anti-bot measures (CAPTCHA, Cloudflare, rate limits)
- [ ] Investigate bulk data access (FTP, subscription, FOIA request)

### STR / Vacation Rental Registry (NICE TO HAVE)
- [ ] Check if state has licensing requirement for short-term rentals
- [ ] Check if individual cities/counties have STR registries
- [ ] Identify data format and access method

---

## 3. Configuration Files

Create `deployments/{state}/CONFIG.md` with:
- [ ] All data source URLs and access methods
- [ ] County code mapping
- [ ] Property use code mapping (residential types)
- [ ] Homestead/owner-occupied detection logic
- [ ] STR-eligible zip codes (tourist areas)
- [ ] State-specific compliance rules (calling hours, DNC, licensing)

Create `deployments/{state}/config/` with:
- [ ] `counties.json` — target counties with URLs and formats
- [ ] `scoring_weights.json` — ICP scoring (can start from FL template)
- [ ] `enrichment_sources.json` — state-specific data sources

---

## 4. Script Adaptation

### State-Specific Scripts (need modification)
- [ ] **Step 01:** Adapt download script for new data source
- [ ] **Step 02:** Adapt parser for new column names and format
- [ ] **Step 03:** Update scoring config (STR zips, use codes, state check)
- [ ] **Step 04:** Adapt entity resolver for state's SoS registry

### State-Agnostic Scripts (work as-is)
- Step 05/05b: Contact enrichment + merge
- Step 06: Validation (phone/email/DNC)
- Step 07: Campaign export
- Step 08: Tracerfy skip trace
- Step 13: Rental estimates (HUD is nationwide)
- Step 14: Wealth signals (FEC/990/SEC are federal)
- Step 20: Dossier assembly

### May Need Adaptation
- Step 11: County clerk scraping (different portal per county)
- Step 12: Purchase history (different SDF format per state)
- Step 16: Life events (different clerk portal)

---

## 5. Compliance Setup

- [ ] Research state telemarketing license requirements
- [ ] Research state DNC list (separate from federal)
- [ ] Document state-specific calling hours
- [ ] Document state-specific call frequency limits
- [ ] Register for FTC DNC with relevant area codes
- [ ] Set up Tracerfy DNC scrub if comprehensive coverage needed

---

## 6. API Setup

- [ ] Tracerfy API key (same key works nationwide)
- [ ] MillionVerifier API key (same)
- [ ] Twilio API keys (same)
- [ ] Google OAuth credentials (same)
- [ ] Airtable API token (new base per client? or shared?)

---

## 7. Test Run

- [ ] Download property data for one target county
- [ ] Parse and filter — confirm reasonable lead count
- [ ] Run entity resolution on 25 test leads
- [ ] Run Tracerfy on 25 test leads
- [ ] Validate phone/email on results
- [ ] Review output quality before scaling

---

## 8. Client Deployment

- [ ] Create `deployments/{state}/{client}/CLIENT.md`
- [ ] Set up Airtable base (or clone existing)
- [ ] Create Google Sheet from template
- [ ] Run full pipeline for target counties
- [ ] Upload to CRM
- [ ] Hand off to loan originator

---

## Estimated Timeline

| Phase | Duration | Notes |
|-------|----------|-------|
| Data source research | 1-2 days | Web research + testing |
| Script adaptation | 1-3 days | Depends on data format complexity |
| Test run (25 leads) | 1 day | Verify everything works |
| Full run | 1 day | Scale to all target counties |
| CRM + Sheets setup | 1 day | Clone and populate |
| **Total** | **5-8 days** | For a new state |

Subsequent deployments in the same state (new client, different counties) take 1-2 days.
