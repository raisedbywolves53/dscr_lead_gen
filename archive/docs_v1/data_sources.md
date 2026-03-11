# DATA_SOURCES.md — Field-Level Source Mapping

Every data point we capture, where it comes from, and how to get it.

## Source Reference

| ID | Source | URL | Cost | Rate Limit |
|----|--------|-----|------|-----------|
| S1 | FDOR NAL | floridarevenue.com/property/dataportal | Free | Bulk download |
| S2 | FDOR SDF | Same portal, SDF subfolder | Free | Bulk download |
| S3 | FL SunBiz | search.sunbiz.org | Free | 1 req / 3 sec |
| S4 | FL DBPR | myfloridalicense.com | Free | Bulk CSV download |
| S5 | PB County Clerk | mypalmbeachclerk.com | Free | 1 req / 2 sec |
| S6 | Broward County Clerk | browardclerk.org | Free | 1 req / 2 sec |
| S7 | Apollo.io API | apollo.io/api | $100/mo | 100 req/min |
| S8 | FL Voter File | dos.myflorida.com | ~$5 | Bulk file |
| S9 | FEC.gov | api.open.fec.gov | Free | 1,000 req/hr |
| S10 | IRS 990 / ProPublica | projects.propublica.org/nonprofits/api | Free | Reasonable |
| S11 | SEC EDGAR | efts.sec.gov | Free | 10 req/sec |
| S12 | HUD FMR | huduser.gov/portal/datasets/fmr.html | Free | Bulk download |
| S13 | MillionVerifier | api.millionverifier.com | $0.50/1K | Fast |
| S14 | Twilio Lookup | lookups.twilio.com | $0.005/ea | 100 req/sec |
| S15 | Datazapp | datazapp.com | $0.03/ea | Batch upload |
| S16 | Airbnb listings | airbnb.com | Free (scrape) | Careful rate limiting |
| S17 | Zillow | zillow.com | Free (scrape) | Careful rate limiting |

---

## Contact Information

| Field | Primary Source | Fallback Source | Notes |
|-------|---------------|-----------------|-------|
| Decision maker name | S3 (SunBiz officers) | S7 (Apollo) | For LLCs, get ALL officers not just first |
| Multiple decision makers (firms) | S3 (all officers/directors) | S7 (company search) | Target 3+ for investment firms |
| Phone (cell preferred) | S7 (Apollo) | S15 (Datazapp), S8 (voter file), S4 (DBPR) | Apollo returns mobile flag |
| Email | S7 (Apollo) | S15 (Datazapp), pattern generation + S13 validation | Apollo is highest hit rate |
| LinkedIn URL | S7 (Apollo) | Manual search | Apollo returns this directly |
| Company website | S3 (SunBiz principal address → domain lookup) | S7 (Apollo company) | Also try Google "`LLC name` site") |
| Age / DOB | S8 (voter file has DOB) | S7 (Apollo sometimes has) | Voter file is authoritative |
| Employer | S7 (Apollo) | S8 (voter file occupation field) | |
| Social media | S7 (Apollo) | Manual Google search | Apollo returns Twitter, Facebook |

---

## Entity Details

| Field | Source | Notes |
|-------|--------|-------|
| LLC / entity name | S1 (FDOR NAL owner field) | Already captured |
| Registered agent | S3 (SunBiz detail page) | Already built |
| State of incorporation | S3 (SunBiz filing info) | Already built |
| Year formed | S3 (SunBiz date filed) | Already built |
| All officers / directors | S3 (SunBiz officer section) | Need to capture ALL, not just first match |
| Entity status (active/inactive) | S3 (SunBiz) | Already built |
| Related entities (same officers) | S3 (cross-reference officer names) | Script 15 |

---

## Portfolio Data (per property)

| Field | Source | Notes |
|-------|--------|-------|
| Property count | S1 (FDOR NAL, group by owner) | Already captured |
| Property addresses | S1 (FDOR NAL PHY_ADDR1) | Already captured |
| Estimated value (each) | S1 (FDOR NAL JV field) | Already captured |
| Total portfolio value | S1 (sum of JV) | Already captured |
| Property type | S1 (FDOR NAL DOR_UC) | Already captured |
| Property type mix | S1 (aggregate DOR_UC per owner) | Derivable |
| Ownership structure | S1 (owner name per parcel) + S3 (LLC structure) | Cross-reference |

---

## Financing Intelligence (per property)

| Field | Source | How |
|-------|--------|-----|
| Lender name | S5/S6 (county clerk mortgage recordings) | Search by parcel ID or owner name |
| Loan amount (original) | S5/S6 (mortgage recording amount field) | Direct from recording |
| Origination date | S5/S6 (recording date) | Direct from recording |
| Loan type | S5/S6 (document type + lender name pattern) | Hard money lenders have recognizable names |
| Interest rate estimate | Derived from lender type + origination date + prevailing rates | Estimation model |
| Fixed vs ARM | Derived from loan type classification | ARM more common with certain lenders |
| Estimated balance | Amortization calc from original amount + date | Standard 30yr amortization unless hard money |
| LTV estimate | Estimated balance / current just value (S1) | Derivable |
| Maturity date | Origination date + standard term (30yr conventional, 1-3yr hard money) | Estimation |
| Lender type | Pattern matching on lender name | Bank, credit union, hard money, private, etc. |
| Total debt | Sum of estimated balances across portfolio | Derivable |
| Total equity | Total value - total debt | Derivable |
| Portfolio DSCR | Estimated rent / estimated debt service | Requires rent estimate (S12) |

---

## Purchase History

| Field | Source | Notes |
|-------|--------|-------|
| Full purchase timeline | S2 (FDOR SDF has all recorded sales) | Need to download SDF files |
| Sale price each transaction | S2 (SDF SALE_PRC field) | |
| Purchase date | S2 (SDF SALE_YR, SALE_MO) | |
| Sold properties (no longer owned) | S2 (SDF shows sales where owner changed) | Compare SDF seller name to current owner |
| Cash vs financed | S2 (sale) cross-referenced with S5/S6 (mortgage within 30 days of sale) | No mortgage recording near sale date = cash |
| Flip vs hold | S2 (buy date vs sell date on same parcel) | Short hold (<12mo) = likely flip |
| Time between purchases | S2 (sort by date, compute intervals) | Derivable |
| Average purchase price | S2 (mean of purchase prices) | Derivable |
| Off-market indicator | S2 (sale price = $0 or $100 = non-arms-length / off-market) | Common FDOR pattern |
| Purchases last 12/36 months | S2 (filter by date) | Derivable |

---

## Rental / STR Intelligence

| Field | Source | Notes |
|-------|--------|-------|
| Estimated rent | S12 (HUD FMR by zip + bedroom count) | Free bulk download, updated annually |
| STR license | S4 (DBPR vacation rental CSV) | Already captured |
| Airbnb listing presence | S16 (Airbnb search by address) | Scraping, requires careful approach |
| Airbnb revenue estimate | S16 (listing details: price × reviews × occupancy) | Rough estimate from listing data |
| VRBO listing presence | Similar scrape approach | |
| Property management company | S4 (DBPR PM license records, match by address) | Cross-reference |
| Zillow listing presence | S17 (Zillow search by address) | For rental listings |

---

## Wealth Signals

| Field | Source | Notes |
|-------|--------|-------|
| Political donations | S9 (FEC.gov API, search by name + state) | Free, public record |
| Foundation donations | S10 (IRS 990 filings via ProPublica) | Free API |
| Board seats | S11 (SEC EDGAR officer search) | Already partially built |
| Professional licenses | S4 (DBPR all license types) | Already have data |
| Other businesses / LLCs | S3 (SunBiz search by officer name) | Reverse lookup |
| Estimated net worth | Derived: portfolio equity + wealth signals | Estimation model |
| Estimated income | Derived: portfolio rent income + employment | Rough estimation |

---

## Network Mapping

| Field | Source | Notes |
|-------|--------|-------|
| Property managers | S4 (DBPR PM licenses) + cross-reference with property addresses | |
| Real estate agents | S5/S6 (county clerk closing docs sometimes name agents) | Partial |
| Agent brokerage | DBPR real estate license lookup | By agent name |
| Co-investors | S3 (shared officers across LLCs) + S1 (co-owners on parcel) | Cross-reference |
| Shared lenders | S5/S6 (same lender across multiple borrowers) | Powerful for referral targeting |
| Syndication partners | S3 (multiple people as officers of same LLC) + S11 (SEC fund filings) | |

---

## Life Events

| Field | Source | Notes |
|-------|--------|-------|
| Divorce filings | S5/S6 (county clerk family court records) | Searchable online |
| Liens / judgments | S5/S6 (county clerk lien recordings) | |
| Lis pendens | S5/S6 (county clerk lis pendens) | Pre-foreclosure signal |
| Probate / estate | S5/S6 (county clerk probate filings) | Estate transition = motivated seller/buyer |
| Bankruptcy | PACER (federal courts) | $0.10/page, not free but cheap |
| Business sales / dissolutions | S3 (SunBiz status changes) | |

---

## Opportunity Scoring Inputs

The opportunity score (0-100) weighs these signals:

| Signal Category | Weight | Key Indicators |
|----------------|--------|----------------|
| Financing distress | 30% | High-rate loans, balloon maturities, hard money exposure, high LTV |
| Portfolio growth | 20% | Recent purchases, increasing frequency, cash available |
| DSCR fit | 20% | Non-homesteaded, LLC owned, portfolio size, STR income |
| Refinance opportunity | 15% | Cash purchases, high equity, rate improvement possible |
| Life events / urgency | 10% | Divorce, liens, maturing loans, estate transition |
| Network accessibility | 5% | Shared PM/agent/lender, co-investor connections |
