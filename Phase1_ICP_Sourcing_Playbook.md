# Phase 1: ICP Sourcing & Identification Playbook
## How to Find Them, Prove They Exist, and Get Contact Information
### Prepared for: Frank Christiano / CCM Team | March 1, 2026

---

# CORE PRINCIPLE

Nothing else matters — no messaging, no sequences, no content — unless we can answer three questions for each ICP:

1. **WHERE do they congregate?** (physical and digital locations)
2. **WHAT data signals identify them?** (observable, searchable, filterable attributes)
3. **HOW do we extract valid contact information?** (name, phone, email, business)

This playbook treats each ICP as a data problem. For every segment, we define the **signal**, the **source**, the **extraction method**, and the **expected yield**.

---

# TABLE OF CONTENTS

1. [Data Source Taxonomy](#data-source-taxonomy)
2. [ICP Sourcing Matrix — Tier 1 Segments](#tier-1-icp-sourcing)
3. [ICP Sourcing Matrix — Tier 2 Segments](#tier-2-icp-sourcing)
4. [ICP Sourcing Matrix — Tier 3 Segments](#tier-3-icp-sourcing)
5. [Public Records Strategy (Florida-Specific)](#public-records-strategy)
6. [Digital Signal Mining](#digital-signal-mining)
7. [Referral Partner Intelligence Exchange](#referral-partner-intelligence-exchange)
8. [Data Enrichment & Validation Stack](#data-enrichment--validation-stack)
9. [Contact Acquisition Costs & Expected Yields](#contact-acquisition-costs--expected-yields)
10. [Priority Execution Order](#priority-execution-order)

---

# DATA SOURCE TAXONOMY

Every lead source falls into one of five categories. Understanding the category determines the cost, quality, and speed of contact acquisition.

| Category | Description | Cost | Data Quality | Speed | Examples |
|---|---|---|---|---|---|
| **Public Record** | Government-filed data available through official or aggregated channels | Free–Low | High (verified) | Medium | County property appraiser, FL SunBiz LLC filings, SEC Form D |
| **Platform Signal** | Behavioral signals on digital platforms indicating investor intent | Free–Medium | Medium (inferred) | Fast | BiggerPockets profiles, Airbnb listings, LinkedIn activity |
| **List Purchase** | Pre-compiled contact databases from data vendors | Medium–High | Variable | Fast | PropStream, BatchLeads, REDX, ListSource |
| **Relationship Harvest** | Contacts obtained through referral partners and network relationships | Low (time cost) | High (warm) | Slow | REIA members, CPA referrals, hard money lender exits |
| **Event Capture** | In-person or virtual event attendance yielding direct contact | Medium | High (intent-qualified) | Periodic | Conference attendees, meetup sign-ups, webinar registrants |

---

# TIER 1 ICP SOURCING

## 1. Individual Real Estate Investors (1–10 Properties)

**The Signal:** Owns 2-10 residential investment properties in Florida. Properties titled to personal name or single LLC. Active in last 24 months (purchase, refinance, or cash-out).

### Source → Method → Contact Extraction

| Source | Signal | Extraction Method | Expected Data | Est. Volume (FL) |
|---|---|---|---|---|
| **County Property Appraiser** (all 67 FL counties) | Mailing address ≠ property address (non-owner-occupied) + owner has 2-10 parcels | Bulk download or scrape. Cross-reference owner name across parcels to count portfolio size. | Name, mailing address, property address, purchase date, purchase price | 500K+ records |
| **PropStream** | Filter: FL → Non-owner occupied → 2-10 properties → Purchased/refinanced last 24 months | Direct export with contact append (phone/email) | Name, phone, email, mailing address, property details, estimated equity | 50K-150K filtered leads |
| **BatchLeads** | Same filters as PropStream + skip tracing integration | Export + auto skip-trace | Name, phone (mobile preferred), email, address | Same universe |
| **BiggerPockets** | FL-based profiles, "landlord" or "buy and hold" keywords, active in last 90 days | Manual profile review or scraping with care (ToS). Cross-reference to LinkedIn for contact. | Username, self-reported portfolio, location, sometimes real name | 5K-15K active FL profiles |
| **Facebook Groups** | "Florida Real Estate Investors," "FL Landlords," "Jacksonville REI" — members posting about deals, asking questions | Engage → connect → collect. Cannot bulk extract. | Profile name → LinkedIn → email/phone via enrichment | 10K+ group members statewide |
| **REIA Membership Rosters** | Paid membership = active investor. CFRI, Tampa REIA, BPM REIA, JaxREIA, etc. | Sponsor/vendor relationship → access to membership directory or event attendee list | Name, email, sometimes phone | 500-2,000 per club |
| **ListSource (CoreLogic)** | Absentee owners, 2-10 properties, FL, recent transaction activity | Filter + purchase list | Name, address, property data | 100K+ |

### Data Validation Strategy
- **Phone:** Skip-trace through BatchSkipTracing or REISkip. Expect 60-70% hit rate on mobile numbers.
- **Email:** Enrich via Hunter.io, Apollo.io, or ZoomInfo if entity-owned. Expect 40-50% hit rate.
- **Cross-validation:** Match property records to LLC filings on FL SunBiz to get registered agent (often the investor's real name and address).

---

## 2. Professional/Serial Investors (10+ Properties)

**The Signal:** Owns 10+ residential units in FL. Multiple LLCs. Repeat buyer (3+ transactions in 24 months). Often has property management company relationship.

### Source → Method → Contact Extraction

| Source | Signal | Extraction Method | Expected Data | Est. Volume (FL) |
|---|---|---|---|---|
| **County Records + Entity Cross-Reference** | Same registered agent across multiple LLCs, each holding 1-5 properties | Aggregate county records by owner/registered agent. Link to SunBiz LLC filings. Build portfolio map. | Entity names, registered agent, registered address, total portfolio | 10K-30K entities |
| **FL SunBiz (Division of Corporations)** | Search for LLCs with "properties," "holdings," "investments," "realty," "capital" in name. Cross-ref registered agent to property records. | Free search at sunbiz.org. Manual or scripted. | LLC name, registered agent name, address, filing date | 50K+ matching entities |
| **PropStream / BatchLeads** | Filter: 10+ properties, FL, entity-owned | Direct export + skip trace on registered agent | Entity, agent name, phone, email | 5K-15K |
| **Property Management Companies** | PM companies managing 10+ unit portfolios know exactly who these investors are | Relationship approach: offer value (DSCR education, portfolio analysis) in exchange for introductions | Warm referral, name, property details | 50-200 per PM relationship |
| **Title Company Data** | Title companies see every closing. Request: "Who has closed 3+ investment property transactions in the last 12 months?" | Relationship approach with title company reps. Some will share, some won't. | Name, property, transaction history | Varies by relationship |
| **LinkedIn Sales Navigator** | Title: "Real estate investor," "portfolio owner," "landlord" + Location: Florida + Company: LLC/Holdings/Capital | Direct search, export to CRM, InMail or connection request | Name, email (if available), LinkedIn profile | 2K-5K profiles |

### Data Validation Strategy
- **Entity → Person:** FL SunBiz annual report filings list officers, directors, and registered agents. This is the bridge from LLC to human.
- **Phone:** Skip-trace the registered agent. These are serious operators — they usually have business lines.
- **Verification:** If they own 10+ properties, they likely have a Google Business presence, website, or BiggerPockets profile that confirms identity.

---

## 3. Short-Term Rental (STR) Operators

**The Signal:** Active Airbnb/VRBO listing in FL. STR permit on file with local municipality. Property managed as vacation rental.

### Source → Method → Contact Extraction

| Source | Signal | Extraction Method | Expected Data | Est. Volume (FL) |
|---|---|---|---|---|
| **AirDNA** | Active Airbnb/VRBO listing in FL markets. Revenue data, occupancy, ADR. | AirDNA Market Minder subscription ($250-500/month). Export listings with property addresses. Cross-reference to county records for owner. | Property address, revenue estimate, listing details → owner name via county records | 80K+ active listings statewide |
| **Local STR Permit Registries** | Required STR permits/business tax receipts. Osceola County, Miami-Dade, Broward, Volusia all maintain registries. | FOIA/public records request or online registry search | Owner name, permit address, contact info (sometimes email/phone) | Varies by county. Osceola alone has 10K+ |
| **FL DBPR (Dept of Business & Professional Regulation)** | Vacation rental licenses — all FL STR operators must register | DBPR license search at myfloridalicense.com. Search by license type: "Vacation Rental - Dwelling" or "Vacation Rental - Condo" | Owner/operator name, business name, address, license number | 60K+ licensed vacation rentals |
| **Airbnb/VRBO Direct** | Listing → property address → county records → owner | Manual. Identify listing, find property address from listing details/photos/map, look up owner in county records. | Owner name, address, property details | Time-intensive but high-quality |
| **Guesty/Hostaway/Lodgify user communities** | STR property management software users are by definition STR operators | Engage in communities, sponsor webinars, partner with software companies | Community member profiles | 1K-5K FL-based |
| **STR Facebook Groups** | "Florida Airbnb Hosts," "Orlando STR Investors," "Florida Vacation Rental Owners" | Community engagement → relationship building → contact collection | Profile names → enrichment | 5K-15K members |

### Data Validation Strategy
- **DBPR License → Person:** License records are public and contain owner/operator names. This is the most reliable STR data source in FL.
- **AirDNA → County Records → SunBiz:** Chain: identify property from AirDNA → look up owner in county property appraiser → if LLC, resolve to person via SunBiz.
- **Revenue Qualification:** AirDNA data lets you pre-qualify — only target operators with revenue suggesting they'd benefit from DSCR (i.e., enough income to support the ratio).

---

## 4. Foreign National Investors

**The Signal:** Non-U.S. citizen purchasing FL investment property. Often uses international wire transfers. Property may be titled to foreign entity or U.S. LLC with foreign beneficial owner.

### Source → Method → Contact Extraction

| Source | Signal | Extraction Method | Expected Data | Est. Volume (FL) |
|---|---|---|---|---|
| **FL Realtors International Division** | Agents who specialize in international buyers. They ARE the gatekeepers. | Partner with international-focused agents. Offer DSCR education + co-marketing. They bring the buyers. | Warm referral from agent with buyer's consent | Agent network = pipeline |
| **International RE Expos** | Expo Inmobiliaria (Colombia), FERIA DE BIENES RAÍCES (Mexico), Brazil RE shows. Also FIABCI, NAR Global chapters. | Attend or co-exhibit. Collect attendee contacts. | Name, country, email, investment intent | 200-1,000 per expo |
| **Latin American Chambers of Commerce** | CAMACOL (Coral Gables), Colombian American Chamber, Brazilian-American Chamber, Venezuelan Chamber, Argentine Chamber | Membership, sponsorship, event attendance. These organizations host investor-focused events. | Member directories (if sponsor), event attendee lists | 500-2,000 per chamber |
| **Immigration Attorneys** | EB-5, E-2, B-1/B-2 visa clients who are also investing in RE. They know who has capital and intent. | Referral partnership: educate attorneys on DSCR as a tool for their clients. | Warm referral | High quality, low volume |
| **County Records — Foreign Flag** | Grantee with foreign address on deed. Wire transfers from international banks (visible in some closing documents). | Search county records for grantee mailing addresses outside the U.S. or common foreign investor patterns (condo purchases, all-cash, Doral/Brickell/Weston zip codes) | Name, foreign address, property, purchase price | Estimating 5K-10K identifiable transactions/year |
| **WhatsApp/Telegram Groups** | Latin American investor WhatsApp groups focused on FL real estate. Word-of-mouth discovery. | Must be introduced by a trusted contact. Cannot cold-join most groups. | Direct messaging contacts | Varies. Can be high-value. |
| **Waltz / Milo Financial leads** | These platforms specifically serve foreign national investors. Their marketing identifies the audience. | Cannot directly access their leads, but their marketing channels (social, content) reveal WHERE foreign nationals look for information | Indirect: tells you where to fish | Market intelligence |

### Data Validation Strategy
- **Agent referral is the primary path.** Foreign national contact information is hard to acquire through data tools because these buyers often lack U.S. digital footprints.
- **ITIN as signal:** If an investor has an ITIN (Individual Taxpayer Identification Number), they're already in the U.S. tax system and likely have some form of contactable U.S. presence.
- **Consulate partnerships:** Some consulates host economic/investment events. Attending builds trust with the community.

---

## 5. Self-Employed Borrowers (Who Invest in RE)

**The Signal:** Business owner or self-employed professional who owns or is acquiring FL investment property. Tax returns show depressed income due to deductions.

### Source → Method → Contact Extraction

| Source | Signal | Extraction Method | Expected Data | Est. Volume (FL) |
|---|---|---|---|---|
| **CPA/Tax Advisor Referrals** | CPAs who serve RE investors and self-employed clients know exactly who has tax return problems that block conventional financing | Build referral relationships with 10-20 investor-focused CPAs. Educate them: "If your client's tax returns killed their mortgage app, DSCR is the answer." | Warm referral with client context | 5-20 referrals/month per active CPA relationship |
| **FL SunBiz — Active Business Filings** | Cross-reference: people who own both an active FL business AND FL investment property | Business owner from SunBiz → match to property records as investor | Name, business name, registered address | Complex but high-signal |
| **LinkedIn Sales Navigator** | Title: "Owner," "Founder," "CEO," "Self-Employed" + Location: FL + Industry cross-reference + interests in real estate | Search + connect + qualify through conversation | Name, company, email (sometimes), LinkedIn | 20K+ potential matches |
| **Chamber of Commerce / BNI / Rotary** | Local business networking organizations. Members are by definition business owners. | Join or attend as a member/speaker on "real estate investment financing for business owners" | Member directory, in-person contacts | 50-200 per chapter |
| **Small Business Development Centers (SBDCs)** | FL SBDC hosts workshops for business owners. Some attendees are also investors. | Co-host a workshop: "How Business Owners Can Build Wealth Through Real Estate" | Workshop attendee list | 20-50 per event |
| **Franchise Owner Associations** | Franchise owners = self-employed. Often high-income, tax-motivated, looking for asset diversification. | Partner with franchise consultants or attend franchise expos | Contact through association membership | Niche but high-value |

### Data Validation Strategy
- **Self-employed is a behavior, not a record.** You can't filter a database for "has depressed tax returns." This ICP is best sourced through CPA referrals and business owner networks.
- **Cross-reference:** SunBiz active business filing + property appraiser non-owner-occupied properties = confirmed self-employed investor.

---

## 6. BRRRR Strategy Investors

**The Signal:** Recent purchase of distressed/below-market property + hard money or bridge loan origination + renovation permit pulled. They WILL need DSCR refinancing in 3-12 months.

### Source → Method → Contact Extraction

| Source | Signal | Extraction Method | Expected Data | Est. Volume (FL) |
|---|---|---|---|---|
| **Hard Money Lender Referrals** | Every hard money origination = future DSCR refinance. The lender WANTS the borrower to refinance out (frees up their capital). | Formal referral partnerships with Kiavi, RCN Capital, LendingOne, ABL Funding, SEP Capital, EquityMax, Tidal Loans | Warm referral with deal details | 10-50 per lender per month |
| **Building Permit Records** | Renovation permits on recently sold properties (especially below-market sales). FL county building departments publish these. | Pull permits for residential renovation + cross-ref to recent sales below median price + owner ≠ occupant | Owner name, property, permit type, estimated cost | 5K-15K permits/year in major metros |
| **Wholesaler Networks** | New Western, Wholesale Jax, Graystone, Reivesti — their buyer lists are BRRRR investors | Partner with wholesalers. Their buyers need permanent financing. | Buyer contact through wholesaler relationship | 50-200 active buyers per wholesaler |
| **BiggerPockets BRRRR Forum** | Active BRRRR discussion participants in FL markets | Profile review → LinkedIn → contact enrichment | Username → real identity → contact | 500-2,000 active FL posters |
| **Distressed REIA (Lex Levinrad)** | This REIA specifically attracts distressed property / BRRRR investors in Broward/Palm Beach | Sponsor or attend. $15-20 door fee. | In-person contacts, attendee list if sponsor | 50-100 per meeting |
| **Contractor Referrals** | GCs doing investor rehabs know who's flipping and BRRRRing. They often work with the same investors repeatedly. | Relationship approach with 5-10 investor-focused GCs. Offer value: "I help your clients refinance so they can hire you for the next project." | Warm referral | Low volume, very high quality |

### Data Validation Strategy
- **Timeline matters:** BRRRR leads are time-sensitive. The investor needs DSCR in 3-12 months post-acquisition. Building permit dates tell you where they are in the cycle.
- **Hard money lender data is the gold standard.** They have origination date, property address, borrower name, loan amount, and estimated project timeline.

---

## 7. Corporate Entities (LLCs, S-Corps, Trusts)

**The Signal:** New LLC formation in FL with real estate investment purpose + subsequent property acquisition.

### Source → Method → Contact Extraction

| Source | Signal | Extraction Method | Expected Data | Est. Volume (FL) |
|---|---|---|---|---|
| **FL SunBiz — New LLC Filings** | New FL LLC filings with names containing: "properties," "holdings," "investments," "realty," "capital," "ventures," "rental" | Daily/weekly monitoring of new filings on sunbiz.org. Filter by name keywords. | LLC name, registered agent, address, filing date | 500-1,000+ new filings/month matching keywords |
| **FL SunBiz — Annual Reports** | Annual report filings list officers, directors, registered agents — these are the actual humans behind the LLC | Search by registered agent name to find all entities they control | Full entity portfolio per person | Cross-reference data |
| **County Records — Entity Ownership** | Properties titled to LLCs, Corps, Trusts | Filter county property appraiser records for entity-owned non-owner-occupied residential properties | Entity name, property details → SunBiz → person | 100K+ entity-owned investment properties |
| **Estate Planning / Trust Attorneys** | Attorneys forming trusts and LLCs for RE investors | Referral partnership | Warm referral | Steady pipeline |

### Data Validation Strategy
- **SunBiz is the master key.** Every FL LLC must file annual reports listing its officers. This bridges the gap from entity to person.
- **New LLC formation is a leading indicator.** Someone forming "123 Main Street Holdings LLC" in FL is about to buy an investment property. They need financing NOW.

---

# TIER 2 ICP SOURCING

## 8. High-Net-Worth Individuals (HNWIs)

| Source | Signal | Extraction Method | Expected Data |
|---|---|---|---|
| **Tiger 21 / YPO / Vistage / EO** | Membership in HNW peer groups. 6 Tiger 21 chapters in FL alone. | Cannot directly access member lists. Approach: become a trusted resource/speaker. Present on "DSCR as a wealth-building tool." | In-person relationships → referrals |
| **Palm Beach Family Office Association** | Family office events in Palm Beach | Attend events. Sponsor if possible. | Event attendee contacts |
| **Luxury Real Estate Agents** | Agents selling $1M+ properties. Their clients often also invest in income properties. | Referral partnership: "Your client just bought a $3M home. Do they also want income-producing rentals?" | Warm referral |
| **Private Bank / Wealth Advisor Referrals** | UBS, Morgan Stanley, Merrill Lynch — wealth advisors with clients looking to diversify into RE | Educational partnership. Host "alternative real estate investing" events for their client base. | Warm referral |
| **Yacht Club / Country Club Networks** | Admirals Cove, Bear's Club, BallenIsles (Palm Beach), Isleworth (Orlando) | Membership or sponsorship of events | In-person networking |
| **WealthEngine / Windfall** | Wealth-scoring databases that identify HNW individuals | Purchase data: filter by FL + net worth $1M+ + RE investment history | Name, estimated net worth, address, email |

---

## 9. Multi-Family Investors (2-4 Units)

| Source | Signal | Extraction Method | Expected Data |
|---|---|---|---|
| **County Records** | Owner of 2-4 unit property (duplex, triplex, fourplex) with mailing address ≠ property address | Filter property appraiser records for property type = multi-family + non-owner-occupied | Name, property details, address |
| **PropStream / BatchLeads** | Filter: 2-4 units, FL, absentee owner | Export + skip trace | Name, phone, email, property data |
| **LoopNet / Crexi** | Listings for small multi-family properties. Buyers who are actively searching. | Monitor listings → identify buyers through agent relationships | Indirect: buyer agent → buyer |

---

## 10. 1031 Exchange Buyers

| Source | Signal | Extraction Method | Expected Data |
|---|---|---|---|
| **1031 QI Referrals (IPX1031, Asset Preservation, Exeter)** | Active 1031 exchange = 45-day identification deadline = URGENT need for DSCR pre-approval | Formal referral partnership with QIs. They benefit when their clients can close quickly. | Warm referral with exchange timeline |
| **Recent Sales of Investment Properties** | Investor sold a FL investment property in last 30 days → potential 1031 buyer | Monitor county records for investor property sales + contact seller | Name, sold property, sale date, estimated proceeds |
| **Commercial Brokers** | Brokers handling investment property sales know which sellers are doing 1031s | Referral partnership | Warm referral with deal context |

---

## 11. Recently Retired / Career Changers

| Source | Signal | Extraction Method | Expected Data |
|---|---|---|---|
| **Financial Advisor Referrals** | Advisors managing retirement rollovers + clients interested in RE income | Educational partnership: "How retirees use DSCR loans to generate monthly income" | Warm referral |
| **55+ Community Real Estate Agents** | Agents in The Villages, Del Webb communities, etc. | Referral partnership | Warm referral |
| **AARP / Retirement Community Events** | Community events in FL retirement hubs | Attend, speak, or sponsor | In-person contacts |

---

## 12. Tax-Strategy Investors

| Source | Signal | Extraction Method | Expected Data |
|---|---|---|---|
| **Cost Segregation Firms** | Firms doing cost seg studies know who's buying investment RE for tax purposes | Referral partnership: "Your client just did a cost seg study. Do they want to buy more properties?" | Warm referral |
| **CPA Networks (Hall CPA, Investor Friendly CPA)** | CPAs advising on bonus depreciation + STR loophole | Same as self-employed CPA strategy | Warm referral |
| **High-Income Professional Networks** | Doctors, dentists, attorneys, tech executives — W-2 earners $200K+ looking for tax shelter | Targeted LinkedIn outreach + professional association events | LinkedIn → enrichment |
| **White Coat Investor / Physician RE Communities** | Physician-specific RE investing communities | Engage in communities + offer DSCR education | Community contacts |

---

## 13. Investment Funds / Small Syndicators

| Source | Signal | Extraction Method | Expected Data |
|---|---|---|---|
| **SEC EDGAR — Form D Filings** | Reg D 506(b) and 506(c) fund formation filings. Search: FL + real estate + recent filing | Free search at sec.gov/cgi-bin/browse-edgar. Filter for FL real estate offerings. | Fund name, GP name, address, offering size | 200-500 FL RE fund filings/year |
| **AAPL (American Association of Private Lenders)** | Members include fund managers who lend and invest in residential RE | Conference attendance (NPLA Miami), membership directory | Name, fund name, contact |
| **Best Ever Conference / BiggerPockets Community** | Syndicator-focused events and communities | Attend, network, collect contacts | In-person + digital |
| **LinkedIn — "Fund Manager" + "Real Estate" + FL** | Self-identified fund managers on LinkedIn | Sales Navigator search + connect | LinkedIn → enrichment |

---

# TIER 3 ICP SOURCING

## 14-19. Tertiary Segments — Summary Sourcing

| ICP | Primary Source | Signal | Contact Method |
|---|---|---|---|
| **Section 8 Landlords** | Housing Authority records (public), property management companies with Section 8 tenants | Landlord receiving HAP payments | County records → skip trace |
| **First-Time Investors** | BiggerPockets "newbie" forums, TikTok/YouTube RE investing audiences, first investment property purchase in county records | First non-owner-occupied purchase + no prior investment properties | Digital engagement + county records |
| **Commercial Crossover** | CoStar/LoopNet activity, commercial RE brokers | CRE investor adding residential | Broker referral |
| **Diaspora Investors** | Ethnic chambers of commerce, cultural organizations, diaspora Facebook groups | First-generation immigrant + FL property ownership | Community engagement |
| **Digital Nomads/Expats** | Nomad List, Remote Year alumni, expat Facebook groups, international coworking spaces | Remote worker + U.S. property interest | Digital community engagement |
| **Accidental Landlords** | Expired listings that converted to rentals (MLS → no re-list + rental listing appears), inherited property records | Owned primary → now renting it out | County records + rental listing cross-ref |

---

# PUBLIC RECORDS STRATEGY (FLORIDA-SPECIFIC)

Florida has some of the most accessible public records in the country (Sunshine Law). This is a massive advantage.

## Tier 1 Public Data Sources

### 1. County Property Appraiser (All 67 Counties)

**What's available:** Owner name, mailing address, property address, legal description, sale date, sale price, assessed value, market value, property type, homestead exemption status, tax bill.

**Key filter for investors:** Homestead exemption = NO (non-homesteaded properties are investment/second homes). Mailing address ≠ property address = absentee owner.

**Top counties by investor volume:**
| County | Portal | Key Market |
|---|---|---|
| Miami-Dade | miamidade.gov/pa | Miami, Doral, Homestead |
| Broward | bcpa.net | Fort Lauderdale, Weston, Plantation |
| Palm Beach | pbcgov.com/papa | West Palm, Boca Raton, Delray |
| Hillsborough | hcpafl.org | Tampa |
| Orange | ocpafl.org | Orlando |
| Duval | coj.net/departments/property-appraiser | Jacksonville |
| Osceola | property.osceola.org | Kissimmee (STR hub) |
| Lee | leepa.org | Cape Coral, Fort Myers |
| Pinellas | pcpao.gov | St. Petersburg, Clearwater |
| Volusia | volusia.org/property-appraiser | Daytona Beach |

**Bulk data:** Most counties offer bulk downloads or data files. Some charge a nominal fee ($25-$100). For programmatic access, PropStream and BatchLeads aggregate all 67 counties into a single searchable interface.

### 2. FL Division of Corporations (SunBiz)

**URL:** sunbiz.org

**What's available:** LLC/Corp name, registered agent, officers/directors (in annual reports), principal address, mailing address, filing date, status (active/inactive).

**Key searches:**
- New filings with RE-related keywords (daily/weekly)
- Registered agent search → find all entities controlled by one person
- Annual report filings → officer/director names

### 3. FL DBPR (Dept of Business & Professional Regulation)

**URL:** myfloridalicense.com

**What's available:** Professional licenses including vacation rental licenses, real estate agent licenses, contractor licenses.

**Key for STR sourcing:** Every vacation rental in FL must be licensed. Search license type "Vacation Rental" to get operator name, address, license status.

### 4. County Building Permits

**What's available:** Permit type, property address, permit holder, contractor, estimated cost, permit date, status.

**Key for BRRRR sourcing:** Renovation permits on recently purchased below-market properties = active rehab = future DSCR refinance need.

### 5. SEC EDGAR

**URL:** sec.gov/cgi-bin/browse-edgar

**What's available:** Form D filings for private fund offerings (Reg D 506b/c).

**Key for fund/syndicator sourcing:** Filter for FL-based issuers in real estate category. Get fund name, GP name, amount raised, filing date.

---

# DIGITAL SIGNAL MINING

## Platform-Specific Strategies

### BiggerPockets
- **Search:** FL-based members, active in last 90 days, forum participation in DSCR/BRRRR/STR topics
- **Signal strength:** Pro members (paid subscription) = more serious investors
- **Contact path:** BP profile → real name → LinkedIn → email enrichment via Apollo/Hunter
- **Volume:** Estimated 15K-25K FL-based active members

### LinkedIn Sales Navigator
- **Filters:** Location: Florida | Title keywords: "real estate investor," "landlord," "property owner," "portfolio," "rental" | Company keywords: "properties," "holdings," "investments," "capital"
- **Signal strength:** Self-identified investor with professional profile
- **Contact path:** InMail → connection → email request or Apollo enrichment
- **Volume:** 10K-20K matching FL profiles
- **Cost:** $99/month for Sales Navigator

### Airbnb/VRBO
- **Method:** Identify listings in target FL markets → extract property address from listing details → county records → owner name → skip trace
- **Signal strength:** Confirmed active STR operator with demonstrable revenue
- **Contact path:** Listing → property → county records → owner → skip trace
- **Volume:** 80K+ FL listings (AirDNA data)

### Instagram/YouTube
- **Search:** FL-based real estate investing content creators, hashtags: #floridarealstate #orlandoinvestor #miamiinvestor #dscrloan #airbnbinvestor
- **Signal strength:** Public presence = likely serious. Content reveals deal type, market, experience level.
- **Contact path:** DM → relationship → referral or direct client
- **Volume:** Low volume but high-value individuals

---

# REFERRAL PARTNER INTELLIGENCE EXCHANGE

The highest-quality leads come from referral partners who already have the trust of the target ICP. Here's how to structure the exchange:

## The Value Exchange Model

| Partner Type | What They Know | What We Offer Them | What We Get |
|---|---|---|---|
| **Hard Money Lenders** | Who has an active bridge loan, property, timeline | "I'm the exit. When I refinance your borrower into DSCR, you get your capital back to re-lend." | Borrower name, property, loan details, refinance timeline |
| **REIAs** | Who attends, who's active, who's buying | Sponsorship ($400-$1,000), educational presentations, vendor table ($100) | Membership directory, speaking platform, attendee contacts |
| **Wholesalers** | Who's on their buyer list, what they buy, how often | "I finance the deals you put under contract. More financing options = more deals closed for you." | Buyer list access, deal flow notification |
| **RE Attorneys** | Who's forming LLCs, doing 1031s, closing investment transactions | "I'm the financing arm. Refer your clients who need investment property mortgages." | Client referral with legal context |
| **CPAs** | Who owns investment RE, who has tax return income issues | "I solve the #1 problem your investor clients have: qualifying for a mortgage with tax-optimized returns." | Client referral with financial context |
| **1031 QIs** | Who's in an active exchange, deadlines, replacement property needs | "I close in 15-30 days. I help your exchangors hit their 180-day deadline." | Exchange client referral with timeline |
| **Property Managers** | Who owns what, who wants to grow, who's having cash flow issues | "I help your property owners buy more properties = more doors for you to manage." | Owner referral with portfolio details |
| **Insurance Brokers** | Who's insuring investment properties, portfolio size, property locations | "I need accurate insurance quotes to underwrite DSCR. You get my clients' insurance business." | Property owner leads |

---

# DATA ENRICHMENT & VALIDATION STACK

## Recommended Tools

| Tool | Purpose | Cost | Best For |
|---|---|---|---|
| **PropStream** | Property data, owner info, equity, transaction history | $99/month | Identifying investor-owned properties |
| **BatchLeads** | Property data + integrated skip tracing | $79-199/month | Combined property data + contact info |
| **BatchSkipTracing** | Phone + email from name/address | $0.12-0.15/record | Bulk contact acquisition |
| **REISkip** | Skip tracing for RE investors | $0.10-0.20/record | Alternative skip trace provider |
| **Apollo.io** | B2B email/phone enrichment, especially for business owners | $49-99/month | Self-employed, fund managers, professional investors |
| **Hunter.io** | Email finder from name + domain | $49-99/month | Finding emails for identified individuals |
| **LinkedIn Sales Navigator** | Professional profile search, InMail | $99/month | Professional/serial investors, HNWIs, fund managers |
| **AirDNA** | STR market data, property-level revenue | $250-500/month | STR operator identification + qualification |
| **ZoomInfo** | Enterprise contact + company database | $10K+/year | Large-scale institutional prospecting |
| **WealthEngine** | Wealth-scoring, philanthropic, asset data | Custom pricing | HNWI identification |

## Data Validation Workflow

```
Step 1: IDENTIFY (Source → Raw Lead)
   County records, PropStream, SunBiz, DBPR, AirDNA, referral partner

Step 2: ENRICH (Raw Lead → Contact)
   Skip trace (BatchSkipTracing/REISkip) → phone, email
   Apollo/Hunter → email verification
   LinkedIn → professional context
   SunBiz → entity-to-person resolution

Step 3: VALIDATE (Contact → Qualified Lead)
   Verify phone is active (ring test)
   Verify email deliverability (bounce check)
   Confirm investment activity (recent transaction in county records)
   Confirm property count / portfolio size

Step 4: SCORE (Qualified Lead → Prioritized Lead)
   Score based on: portfolio size, recent transaction activity,
   estimated equity, property type match to DSCR sweet spot,
   geographic concentration in target FL markets
```

---

# CONTACT ACQUISITION COSTS & EXPECTED YIELDS

## Per-Lead Cost Estimates

| Source | Cost Per Lead | Contact Rate | Qualified Rate | Cost Per Qualified Lead |
|---|---|---|---|---|
| **PropStream + Skip Trace** | $0.15-0.25 | 60-70% contactable | 10-15% qualified | $1.00-2.50 |
| **REIA Sponsorship** | $400-1,000/event ÷ attendees | 30-50% contactable | 20-30% qualified | $10-30 |
| **Hard Money Referral** | $0 (relationship) | 90%+ contactable | 80%+ qualified | ~$0 |
| **CPA/Attorney Referral** | $0 (relationship) | 95%+ contactable | 70-80% qualified | ~$0 |
| **LinkedIn Sales Nav** | $99/month ÷ connections | 30-40% respond to InMail | 15-25% qualified | $5-15 |
| **Conference Attendance** | $500-2,000/event ÷ contacts | 40-60% contactable | 15-25% qualified | $20-50 |
| **AirDNA + County Records** | $300-500/month ÷ leads identified | 50-60% contactable (after skip trace) | 30-40% qualified (confirmed STR) | $2-5 |
| **SunBiz LLC Monitoring** | Free ÷ leads identified | 50-60% contactable (skip trace agent) | 20-30% qualified | $0.50-1.50 |

## Expected Monthly Pipeline (At Scale — 3-6 Months In)

| Source Category | Leads/Month | Qualified/Month | Cost/Month |
|---|---|---|---|
| Public Records + Skip Trace | 500-1,000 | 75-150 | $150-250 |
| Platform Signal Mining | 200-500 | 40-100 | $200-400 |
| Referral Partners (active) | 50-200 | 35-160 | $400-1,000 (sponsorships) |
| Events/Conferences | 50-100 | 10-25 | $500-2,000 |
| **TOTAL** | **800-1,800** | **160-435** | **$1,250-3,650** |

---

# PRIORITY EXECUTION ORDER

What to do first, second, third — based on speed-to-contact, cost, and lead quality.

## Week 1-2: Foundation (Cost: ~$300)
1. Set up PropStream account ($99/month)
2. Set up BatchLeads or BatchSkipTracing account ($79-199/month)
3. Pull first list: FL non-owner-occupied, 2+ properties owned, purchased/refinanced in last 24 months, sorted by county (start with Palm Beach, Broward, Miami-Dade, Duval, Hillsborough, Orange)
4. Skip trace first 1,000 records
5. Begin SunBiz monitoring for new RE-related LLC filings

## Week 2-4: Referral Partner Activation (Cost: ~$500)
6. Contact 5 hard money lenders (Kiavi, RCN, ABL, SEP, EquityMax) to propose referral partnership
7. Identify and contact 3 REIA chapters to discuss sponsorship (start with BPM REIA in South FL, CFRI in Orlando, Tampa REIA)
8. Contact 3 investor-focused CPAs (Hall CPA, Investor Friendly CPA, Bette Hochberger)
9. Contact 2 wholesalers (New Western FL, Graystone) about buyer list access
10. Contact 2 1031 QIs (IPX1031, Exeter) about exchange client referrals

## Week 4-6: STR & Foreign National Channels (Cost: ~$500)
11. Pull FL DBPR vacation rental license data
12. Set up AirDNA account for top 3 FL STR markets (Orlando/Kissimmee, Miami Beach, Destin)
13. Contact FL Realtors International Division about international buyer agent partnerships
14. Attend 1 Latin American chamber event (CAMACOL or Colombian Chamber)
15. Begin LinkedIn Sales Navigator prospecting for professional investors

## Week 6-8: Scale & Optimize (Cost: ~$500)
16. Expand PropStream pulls to secondary counties
17. Add building permit monitoring for BRRRR leads
18. Attend first REIA meeting as sponsor/speaker
19. Begin SEC EDGAR monitoring for new FL RE fund filings
20. Evaluate lead quality by source — double down on top performers, cut underperformers

---

# VALIDATION METRICS

How we know this is working:

| Metric | Target (Month 1) | Target (Month 3) | Target (Month 6) |
|---|---|---|---|
| Raw leads generated | 500 | 1,500 | 3,000 |
| Contactable leads (valid phone or email) | 300 | 1,000 | 2,000 |
| Qualified leads (confirmed investor + DSCR fit) | 50 | 200 | 500 |
| Active referral partner relationships | 5 | 15 | 25 |
| REIA/event appearances | 1 | 3 | 6 |
| Cost per qualified lead | <$10 | <$5 | <$3 |

---

*This playbook is Phase 1 only. It answers: "Can we find them and put names to faces?" The answer is yes — through a combination of Florida public records, data vendor tools, digital signal mining, and referral partner relationships. Phase 2 will cover what to say to them once we have their contact information.*

---

**Data Sources Referenced:** FL County Property Appraisers (67 counties), FL Division of Corporations (SunBiz), FL DBPR, SEC EDGAR, PropStream, BatchLeads, AirDNA, BiggerPockets, LinkedIn Sales Navigator, Apollo.io, Hunter.io, National REIA, CAMACOL, AAPL, IMN, and referral partner ecosystem from Research Memo Part 2.
