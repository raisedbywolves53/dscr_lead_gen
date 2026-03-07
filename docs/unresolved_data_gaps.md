# DSCR Lead Gen — Unresolved Data Gaps & GitHub Search Guide

## Current Pipeline Coverage (Pilot 500)

| Data Point | Coverage | Source | Status |
|---|---|---|---|
| Owner name | 500/500 (100%) | FDOR NAL | DONE |
| Resolved person (behind LLC) | 242/500 (48%) | SunBiz curl_cffi | DONE |
| Purchase history + avg price | 345/500 (69%) | FDOR SDF + PAO API | DONE |
| Rental estimates | 500/500 (100%) | HUD FMR | DONE |
| Loan type estimate | 500/500 (100%) | Script 15 heuristics | DONE |
| Interest rate estimate | 349/500 (69%) | Script 15 | DONE |
| Refi score | 500/500 (100%) | Scoring logic | DONE |
| Wealth signals | 26/500 (5%) | FEC + ProPublica 990 | DONE |
| Phone | 211/500 (42%) | Tracerfy | DONE |
| Email | 154/500 (30%) | Tracerfy | DONE |
| ICP segment + score | 500/500 (100%) | Scoring logic | DONE |
| **Lender names** | **0/500 (0%)** | County clerk portals | **BLOCKED** |
| **RE agent data** | **0/500 (0%)** | MLS / listing sites | **BLOCKED** |
| **Lis pendens** | **0/500 (0%)** | County clerk portals | **BLOCKED** |
| **Liens / judgments** | **0/500 (0%)** | County clerk portals | **BLOCKED** |
| **Property manager** | **0/500 (0%)** | Rental listings | **NO SOURCE** |
| **Airbnb/STR revenue** | **0/500 (0%)** | AirDNA ($500+/mo) | **NO SOURCE** |
| **Divorce / probate** | **0/500 (0%)** | Court records | **BLOCKED** |

---

## Gap #1: Lender Names (Current Mortgage Holder)

### What We Need
Who holds the mortgage on each property — Wells Fargo, Kiavi, Lima One, Chase, etc.

### Why It Matters
This is the core of the DSCR refi pitch. Knowing their current lender tells you:
- If they're on a bad rate (hard money at 12%+ → refi to DSCR at 7-8%)
- If they have a balloon note maturing soon (forced refi)
- If they're with a hard money lender (short term, high cost → needs permanent financing)
- If the loan has been assigned/sold (borrower may not even know their current servicer)

**This is the single most valuable missing data point.**

### What's Blocking Us
- **Palm Beach County Clerk** (`erec.mypalmbeachclerk.com`): Google reCAPTCHA required on every search. The portal uses a "Landmark Web" system. We can reach the search page via curl_cffi but the server requires a valid reCAPTCHA token before returning results (`ShowCaptcha` endpoint returns `True`).
- **Broward County Clerk** (`officialrecords.broward.org`): Cloudflare challenge page. Even curl_cffi with browser impersonation gets a 403. Uses "AcclaimWeb" system.
- **PBC Property Appraiser** (`pbcpao.gov`): Accessible, but only has last sale price/date — no mortgage/lender data. The Property Appraiser tracks ownership and values; the Clerk tracks mortgages and liens.

### What We Tried
- curl_cffi with Chrome impersonation (bypasses Cloudflare on SunBiz but NOT on Broward Clerk)
- Direct AJAX POST to PBC Clerk's `/Search/NameSearch` endpoint (returns 500 without valid reCAPTCHA)
- PBC PAO Property Summary page (has sale history but zero mortgage data)
- Selenium headless + undetected-chromedriver (both blocked)

### GitHub Search Queries
```
florida clerk official records scraper
landmark web scraper erec
acclaim web scraper broward official records
county recorder mortgage scraper python
reCAPTCHA bypass selenium python clerk
ATTOM property API python
corelogic API python mortgage
public records mortgage scraper florida
florida official records API
palm beach clerk scraper
broward county records scraper python
mortgage recording data scraper
deed of trust scraper county
```

### What a Working Solution Looks Like
Any repo that can:
1. Submit a name search to PBC or Broward clerk portals
2. Handle the reCAPTCHA or Cloudflare challenge
3. Parse the results table (doc type, parties, date, amount)
4. Extract lender names from MTG (Mortgage) document types

OR any repo that wraps a paid API that has this data:
- ATTOM Data Solutions (property + mortgage data API)
- CoreLogic / Black Knight (enterprise mortgage data)
- Reonomy API (commercial property intelligence)
- DataTree / First American (title + mortgage data)

### Workaround (Manual, ~30 min for top 25)
We built `scrape/scripts/11b_clerk_lookup_helper.py` that generates a lookup sheet with clerk portal URLs. Open each in a browser, search manually, record lender name in the template CSV, then merge back with `--merge`.

---

## Gap #2: Lis Pendens / Pre-Foreclosure

### What We Need
Active lis pendens filings — a legal notice filed when a foreclosure action begins.

### Why It Matters
A lis pendens means the investor is in active financial distress on that property. They NEED financing help NOW. These are the hottest leads in the pipeline — they have urgency and motivation.

### What's Blocking Us
Same clerk portals as Gap #1. Lis pendens (doc type "LP", code 20 in PBC) are recorded with the Clerk of Court.

### GitHub Search Queries
```
lis pendens scraper florida
pre-foreclosure data scraper python
florida foreclosure public records scraper
county clerk lis pendens python
foreclosure filing scraper selenium
pre-foreclosure lead generation python
distressed property data scraper
notice of default scraper
```

### What a Working Solution Looks Like
Same as Gap #1 — if you crack the clerk portal, you get lis pendens, liens, judgments, and lender data all at once.

Alternative data sources:
- PropertyRadar (has pre-foreclosure data)
- ForeclosureRadar
- RealtyTrac/ATTOM foreclosure data
- HUD foreclosure listings

---

## Gap #3: Liens & Judgments

### What We Need
Tax liens, mechanic's liens, HOA liens, and court judgments filed against the investor or their properties.

### Why It Matters
Liens signal financial pressure. An investor with a tax lien or judgment may need to refinance to pay it off. Also useful for risk assessment.

### What's Blocking Us
Same clerk portals (doc types LN, LN_TX, JUD in PBC system).

### GitHub Search Queries
```
tax lien scraper florida
judgment lien public records scraper python
county clerk lien search python
florida tax lien data
mechanics lien scraper
HOA lien public records
court judgment scraper florida
```

---

## Gap #4: Real Estate Agent (Buy-Side)

### What We Need
Which real estate agent helped the investor purchase their properties.

### Why It Matters
Referral partnerships — if Agent X helped 5 of your leads buy investment properties, that agent specializes in investors. Build a relationship, and the agent sends you their next 50 investor clients for financing.

### What's Blocking Us
Agent data lives in the MLS (Multiple Listing Service), which is locked behind paid access restricted to licensed agents. Public listing sites (Zillow, Redfin, Realtor.com) sometimes show the listing/selling agent but aggressively block scraping.

### GitHub Search Queries
```
redfin scraper python property agent
zillow scraper python listing agent
realtor.com scraper python
MLS API python real estate
rets API python real estate listings
spark API real estate
bright MLS scraper python
florida MLS data scraper
real estate agent lookup python
listing agent scraper property
homebot API python
```

### What a Working Solution Looks Like
Any repo that can:
1. Take a property address
2. Look up the listing on Redfin/Zillow/Realtor.com
3. Extract the buyer's agent name and brokerage

OR any wrapper for MLS/RETS API access (would need agent credentials).

### Alternative Approaches
- **DBPR cross-reference**: Florida DBPR has licensed real estate agent data. If we can match agents to areas/transactions, we might infer relationships.
- **Redfin sold listings**: Redfin shows agent names on sold property pages. A headless browser scraper might work.
- **Manual for top 10**: Search each property address on Redfin, note the buyer's agent.

---

## Gap #5: Property Manager

### What We Need
Which property management company manages each investor's rental properties.

### Why It Matters
Property managers are the ultimate referral source. One PM manages 50-200+ investor-owned rentals. If you get the PM relationship, you get access to their entire client book.

### What's Blocking Us
No single public database of PM assignments. This data is scattered across rental listings, DBPR licenses, and property management company websites.

### GitHub Search Queries
```
rental listing scraper property manager python
zillow rental scraper python
apartments.com scraper python
DBPR license lookup florida python
property management company scraper
rent.com scraper python
trulia rental scraper
rental property manager lookup
florida property management license lookup
```

### What a Working Solution Looks Like
Any repo that can:
1. Search rental listing sites by address
2. Extract the property management company name from the listing
3. Cross-reference DBPR PM licenses with property addresses

---

## Gap #6: Airbnb / STR Revenue

### What We Need
Estimated rental revenue for short-term rental (STR) properties — Airbnb, VRBO, etc.

### Why It Matters
For STR investor leads (one of our ICP segments), knowing their actual or estimated rental revenue is critical for the DSCR calculation. If we can show "your property generates $4,500/mo on Airbnb and qualifies for a DSCR refi at 7.5%", that's a compelling pitch.

### What's Blocking Us
- AirDNA (the industry standard) costs $500+/month
- Airbnb has no public API for revenue data
- VRBO/HomeAway similarly locked down

### GitHub Search Queries
```
airbnb scraper python revenue
airdna alternative python free
vrbo scraper python listings
short term rental revenue scraper
airbnb listing data python selenium
airbnb calendar scraper occupancy
airbnb pricing scraper python
str revenue estimator python
mashvisor API python
pricelabs API python scraper
```

### What a Working Solution Looks Like
Any repo that can:
1. Search Airbnb/VRBO by location or property address
2. Extract listing details (nightly rate, occupancy calendar, reviews)
3. Estimate monthly/annual revenue from calendar data

---

## Gap #7: Better Contact Data (Phone / Email)

### What We Need
Higher hit rate on cell phone numbers and personal email addresses. Currently at 42% phone and 30% email from Tracerfy.

### Why It Matters
Can't call leads without phone numbers. The 58% without phones are unreachable by phone.

### What's Blocking Us
- Apollo.io returns near-zero contact data for private RE investors (2% email rate even with resolved person names)
- Tracerfy is our best source but still misses 58% of phones
- Datazapp has a $125 minimum per transaction

### GitHub Search Queries
```
skip trace API python
people search scraper python
whitepages scraper python
truepeoplesearch scraper python
fastpeoplesearch scraper python
OSINT phone email python lookup
voter file florida phone lookup
beenverified API python
spokeo scraper python
thatsthem scraper python
numverify phone lookup python
people finder scraper python
reverse address lookup phone python
```

### What a Working Solution Looks Like
Any repo that can:
1. Take a person's name + address (or just name + city/state)
2. Look up phone numbers and email addresses
3. Return results programmatically (API or scraping)

Best free sources to look for scrapers of:
- ThatsThem.com (free people search, shows phones)
- FastPeopleSearch.com (free, shows phones + emails)
- TruePeopleSearch.com (free, shows phones)
- Nuwber.com (free basic results)
- Florida voter file (has phone numbers, costs ~$5 from state)

---

## Gap #8: Divorce / Probate / Life Events

### What We Need
Recent divorce filings, probate cases, estate transitions, business dissolutions tied to our leads.

### Why It Matters
- **Divorce** = forced property liquidation or division. One spouse may need to refi to buy out the other.
- **Probate** = inherited property. Heirs often need financing to keep or liquidate.
- **Business dissolution** = assets being unwound, possible fire sale.

### What's Blocking Us
Same county clerk portals (court records division). Divorce is doc type "DM" (code 5) and Probate is "PRO" (code 8) in PBC Landmark Web.

### GitHub Search Queries
```
florida court records scraper python
divorce filing public records scraper
probate records scraper python
clerk of court scraper florida
florida court case search scraper
family court records scraper
estate filing scraper python
oscceola clerk scraper
miami dade clerk scraper
```

---

## How to Search GitHub Effectively

### Basic Search
Go to [github.com/search](https://github.com/search) and type your query. By default it searches repository names, descriptions, and README files.

### Filter by Language
Add `language:python` to only find Python repos:
```
florida clerk scraper language:python
```

### Filter by Recently Updated
Avoid abandoned repos. Only show repos updated in the last year:
```
florida property scraper language:python pushed:>2025-01-01
```

### Filter by Stars (Quality Signal)
Repos with more stars are generally more reliable:
```
real estate scraper python stars:>5
web scraping selenium recaptcha stars:>10
```

### Filter by Topic
Some repos are tagged with topics. Search within topics:
```
topic:web-scraping topic:real-estate
topic:public-records
topic:property-data
```

Or browse topic pages directly:
- https://github.com/topics/web-scraping
- https://github.com/topics/real-estate
- https://github.com/topics/public-records
- https://github.com/topics/property-data
- https://github.com/topics/scraper

### Search Code (Not Just Repos)
Click "Code" tab in search results to find specific code patterns:
```
"mypalmbeachclerk" language:python
"officialrecords.broward" language:python
"pbcpao.gov" language:python
"erec.mypalmbeachclerk" language:python
```

This finds any repo that references these URLs in their code — even if the repo name doesn't mention "clerk" or "florida".

### Search for API Wrappers
```
"ATTOM" API python wrapper
"corelogic" API python
"reonomy" API python
"datatree" API python
"first american" API python property
```

### Search for reCAPTCHA Solutions
Since the PBC clerk portal is blocked by reCAPTCHA:
```
recaptcha solver python selenium
recaptcha bypass python
2captcha python selenium
anticaptcha python
capsolver python recaptcha
```

Note: These are paid CAPTCHA-solving services ($1-3 per 1,000 solves). They use human workers or AI to solve CAPTCHAs. For 500 leads at ~3 searches each, that's ~1,500 solves = ~$3-5 total. Repos to look for:
```
2captcha python selenium integration
anticaptcha python example
capsolver python recaptcha v2
python recaptcha selenium automated
```

### Useful Broader Searches
```
florida public records python
county records scraper python
property data pipeline python
real estate lead generation python
skip tracing python
real estate investor data python
FDOR florida python
sunbiz scraper python
```

### Check "Awesome" Lists
Curated lists of tools and resources:
```
awesome real estate data
awesome web scraping
awesome OSINT
awesome python scraping
```

---

## Priority Order (What to Search First)

| Priority | Gap | Impact | Search Focus |
|---|---|---|---|
| **1** | Lender names | Entire DSCR pitch depends on this | Clerk portal scrapers, ATTOM API, reCAPTCHA solvers |
| **2** | Lis pendens | Hottest leads, most urgency | Same clerk portal — solving #1 solves #2 |
| **3** | Better contact data | Can't sell if can't reach them | People search scrapers, skip trace APIs |
| **4** | RE agents | Referral channel | Redfin/Zillow scrapers |
| **5** | STR revenue | Nice-to-have for STR segment | Airbnb scrapers |
| **6** | Property manager | Referral channel | Rental listing scrapers |
| **7** | Liens/judgments | Risk signals | Same clerk portal |
| **8** | Divorce/probate | Life event triggers | Court records scrapers |

**Key insight:** The county clerk portal is the single biggest unlock. If you find a repo that cracks PBC or Broward clerk access, it solves gaps #1, #2, #7, and #8 simultaneously. Focus your search there first.

**Second key insight:** A reCAPTCHA solving service (2Captcha, AntiCaptcha, CapSolver) might be the simplest path. For ~$3-5 we could automate all 500 clerk lookups by integrating a solver into the existing script 11. Look for repos that demonstrate this integration.

---

## File Locations

| File | Description |
|---|---|
| `scrape/scripts/11_county_clerk.py` | Existing clerk scraper (blocked by CAPTCHA) |
| `scrape/scripts/11b_clerk_lookup_helper.py` | Manual lookup helper (generates URLs + template) |
| `scrape/data/financing/clerk_lookup_sheet.csv` | Top 25 leads with clerk portal URLs |
| `scrape/data/financing/clerk_recording_template.csv` | Template for recording lender data manually |
| `scrape/data/enriched/pilot_500_enriched.csv` | Current enriched data (500 leads, 121 columns) |
