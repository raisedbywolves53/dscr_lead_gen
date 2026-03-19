# Legal & Compliance Analysis: DSCR Lead Generation Business Model

**Date:** March 19, 2026
**Scope:** Data aggregation, skip tracing, lead list sales to mortgage loan officers
**Disclaimer:** This is a research summary, not legal advice. Consult a licensed attorney before making business decisions based on this analysis.

---

## Table of Contents

1. [Business Model Summary](#1-business-model-summary)
2. [Data Collection Legality](#2-data-collection-legality)
3. [FCRA Analysis — The Critical Question](#3-fcra-analysis--the-critical-question)
4. [Outreach Compliance for Loan Officers](#4-outreach-compliance-for-loan-officers)
5. [RESPA / Mortgage-Specific Rules](#5-respa--mortgage-specific-rules)
6. [How Existing Companies Handle This](#6-how-existing-companies-handle-this)
7. [CFPB Data Broker Rulemaking (2024-2026)](#7-cfpb-data-broker-rulemaking-2024-2026)
8. [State-Specific Rules: Florida & North Carolina](#8-state-specific-rules-florida--north-carolina)
9. [What Makes This Clearly Compliant vs Clearly Illegal](#9-what-makes-this-clearly-compliant-vs-clearly-illegal)
10. [Liability Split: Data Aggregator vs Loan Officer](#10-liability-split-data-aggregator-vs-loan-officer)
11. [Recommended Safeguards](#11-recommended-safeguards)
12. [Sources & Citations](#12-sources--citations)

---

## 1. Business Model Summary

The business operates in three stages:

1. **Aggregate public records** — county property records (assessor/tax rolls), state corporate filings (SOS/SunBiz), FEC donation records, HUD rent data
2. **Enrich with skip trace data** — use services like Tracerfy/BatchData to append phone numbers and emails to property owner records
3. **Sell enriched lead lists** — to licensed mortgage loan officers who cold-call/email the investors to offer DSCR (Debt Service Coverage Ratio) loans

This places the business at the intersection of four regulatory frameworks: **FCRA** (data), **TCPA/TSR** (calling), **CAN-SPAM** (email), and **RESPA** (mortgage marketing).

---

## 2. Data Collection Legality

### 2a. Public Property Records (County Assessor, Tax Rolls)

**Legal status: CLEARLY LEGAL to access and aggregate.**

County property records — assessor data, tax rolls, deed records, mortgage filings — are public records by law in all 50 states. They exist specifically to provide public notice of property ownership and encumbrances.

- **Freedom of Information / Public Records Acts** in every state guarantee public access
- There is no copyright in government-created factual databases (see *Feist Publications v. Rural Telephone Service*, 499 U.S. 340 (1991) — facts are not copyrightable)
- Companies like CoreLogic (now Cotality), ATTOM Data, and DataTree have built multi-billion-dollar businesses aggregating these exact records
- County websites typically provide bulk download or API access; some charge fees for bulk access, but the data itself is public

**Caveat:** Some counties restrict *automated scraping* of their websites via terms of service. Using bulk data downloads, FOIA requests, or licensed data feeds (like ATTOM) avoids this issue entirely.

### 2b. State Corporate Filings (SunBiz, SOS Registries)

**Legal status: CLEARLY LEGAL to access and use commercially.**

- State Secretary of State filings (LLC articles, corporate registrations, registered agent info) are public records maintained for public notice purposes
- Florida's SunBiz, North Carolina's SOS — all provide free public search and bulk data access
- This data is routinely used by title companies, due diligence firms, skip tracers, and data aggregators
- No state restricts commercial use of SOS filing data

### 2c. FEC Donation Records

**Legal status: CLEARLY LEGAL.**

- Federal Election Commission data is public by federal law (52 USC 30111)
- The FEC provides a public API (api.open.fec.gov) specifically for programmatic access
- Donor names, addresses, employers, and donation amounts are all public
- Widely used by political campaigns, journalists, researchers, and commercial data companies

### 2d. HUD/Census Rent Data

**Legal status: CLEARLY LEGAL.**

- HUD Fair Market Rents are aggregate statistical data, not individual consumer records
- Published specifically for public use
- No restrictions on commercial use

### 2e. Skip Tracing (Tracerfy, BatchData, PropStream)

**Legal status: LEGAL, with important FCRA constraints (see Section 3).**

Skip tracing — finding contact information for known individuals — is a legal and well-established industry. The data typically comes from:

- Public records (voter registrations, property records, court records)
- Commercial data sources (utility connections, magazine subscriptions, warranty cards)
- Data cooperatives (data sharing between companies)
- Social media and web scraping

**How existing skip trace companies operate legally:**
- They explicitly disclaim being Consumer Reporting Agencies under FCRA
- They contractually prohibit customers from using the data for FCRA-regulated purposes (credit, insurance, employment, tenant screening)
- They position their data as contact information for marketing/outreach purposes only
- They require users to agree to acceptable use policies

**Key legal principle:** Skip tracing data is NOT a "consumer report" under FCRA *as long as it is not used for a purpose regulated by FCRA* (credit decisions, employment, insurance, tenant screening). Using it for marketing outreach is a permissible non-FCRA use.

---

## 3. FCRA Analysis — The Critical Question

This is the single most important legal question for the business model. The answer is nuanced.

### 3a. What Is a "Consumer Report"?

Under **15 USC 1681a(d)**, a consumer report is:

> "Any written, oral, or other communication of any information by a consumer reporting agency bearing on a consumer's credit worthiness, credit standing, credit capacity, character, general reputation, personal characteristics, or mode of living which is used or expected to be used or collected in whole or in part for the purpose of serving as a factor in establishing the consumer's eligibility for (A) credit or insurance to be used primarily for personal, family, or household purposes; (B) employment purposes; or (C) any other purpose authorized under section 1681b."

### 3b. What Is a "Consumer Reporting Agency"?

Under **15 USC 1681a(f)**, a CRA is:

> "Any person which, for monetary fees, dues, or on a cooperative nonprofit basis, regularly engages in whole or in part in the practice of assembling or evaluating consumer credit information or other information on consumers for the purpose of furnishing consumer reports to third parties."

### 3c. Analysis: Does This Business Model Trigger FCRA?

**The answer depends on HOW the data is used, not WHAT the data contains.**

**Arguments that FCRA does NOT apply:**

1. **Purpose test:** The data is being sold for marketing outreach (cold calling/emailing investors), NOT for making credit decisions, employment decisions, insurance underwriting, or tenant screening. The LOs who buy the leads use them to *market* to investors, not to *evaluate* them for credit.

2. **Not "consumer credit information":** Property ownership records, corporate filings, and contact info are not inherently "consumer credit information." They don't bear on creditworthiness per se.

3. **Industry precedent:** PropStream, BatchData, ATTOM, Reonomy, and CoreLogic all sell similar data without operating as CRAs. They accomplish this through:
   - Explicit FCRA disclaimers ("this is not a consumer report")
   - Contractual restrictions on FCRA-purpose uses
   - Not including traditional credit data (scores, payment history, accounts)

4. **Marketing exclusion:** The FCRA was designed to regulate credit reporting, not marketing data. Using property records + contact info to identify and reach potential customers is fundamentally a marketing activity.

**Arguments that FCRA COULD apply (risk factors):**

1. **The "expected to be used" language:** FCRA covers data "used or *expected to be used*" for credit decisions. If an LO uses the lead list not just to market but to pre-screen or pre-qualify borrowers based on the property/financial data, that could trigger FCRA.

2. **Wealth signals and financial data:** If the lead list includes mortgage balances, estimated equity, DSCR calculations, or other financial characteristics, these come closer to "bearing on a consumer's credit worthiness." The more financial scoring and analysis you layer on, the closer you get to FCRA territory.

3. **The Spokeo precedent:** The FTC fined Spokeo $800,000 in 2012 for operating as a CRA without complying with FCRA. Spokeo aggregated public records (social media, public records, commercial data) into people profiles. The FTC's position: if you assemble data about consumers and market it in a way that *suggests* it can be used for FCRA purposes, you may be a CRA regardless of your disclaimers.

4. **CFPB's expanding view:** The CFPB proposed a rule in December 2024 that would treat certain data brokers as CRAs. While targeted primarily at data brokers selling sensitive location data and communications metadata, the rule signals an expansive regulatory posture. (Note: the status of this rule under the current administration is uncertain — see Section 7.)

### 3d. FCRA Bottom Line

**The business model as currently structured — selling property-record-based marketing lists with appended contact info — is very likely NOT an FCRA-regulated activity**, provided:

1. The data is sold explicitly for marketing/outreach purposes
2. The terms of sale prohibit FCRA-regulated uses
3. The data does not include traditional credit information (scores, payment history, account balances)
4. The marketing does not suggest the data can be used for credit/employment/insurance decisions

**However**, the more financial analysis layered into the product (equity estimates, DSCR calculations, wealth scoring), the more the product resembles something "bearing on creditworthiness," and the more important it becomes to have strong FCRA disclaimers and use restrictions.

---

## 4. Outreach Compliance for Loan Officers

This section covers the rules that apply to the **loan officers who buy the leads and make calls/send emails**. As the data provider, you have indirect but real exposure here.

### 4a. TCPA (Telephone Consumer Protection Act) — 47 USC 227

The TCPA is the primary federal law governing cold calling. Key provisions:

| Rule | Requirement |
|------|-------------|
| **Autodialer/prerecorded to cell phones** | Prohibited without prior express consent |
| **Manual calls to cell phones** | Legal (no ATDS restriction), but DNC rules still apply |
| **Calls to residential landlines** | Prerecorded calls prohibited without consent |
| **Do Not Call** | Must scrub against national DNC registry |
| **Entity-specific DNC** | Must maintain internal DNC list; honor opt-out requests |
| **Calling hours** | 8 AM - 9 PM in recipient's time zone (FCC rule) |
| **Penalties** | $500/violation; $1,500/violation if willful |

**Critical distinction for DSCR leads:** Many of the property owners on the lead lists are individuals (not businesses). Even though they own investment properties (a commercial activity), their personal cell phone numbers are protected by TCPA. The B2B exemption in the FTC's Telemarketing Sales Rule does NOT override TCPA cell phone protections.

### 4b. FTC Telemarketing Sales Rule (16 CFR 310)

The TSR applies to "telemarketing" — a plan, program, or campaign to sell goods or services through interstate phone calls. Key provisions:

- **DNC Registry:** Telemarketers must access and scrub against the national DNC registry; scrub every 31 days
- **Entity-specific DNC:** Must maintain internal DNC list
- **Calling hours:** Before 8 AM or after 9 PM local time prohibited
- **Caller ID:** Must transmit accurate caller ID
- **Abandoned calls:** Cannot abandon more than 3% of calls per campaign per 30-day period

**B2B Exemption:** The TSR's DNC provisions do NOT apply to calls to businesses. However, "business" means calling a business phone number for business purposes — calling an investor's personal cell is NOT a B2B call even if the purpose is business.

**Seller vs. Telemarketer distinction:** Under the TSR, both the "seller" (the LO/lender) and the "telemarketer" (if they hire one) can be liable. As the data provider (not the caller), you are generally NOT the "telemarketer" or "seller" under the TSR. But see Section 10 on liability.

### 4c. CAN-SPAM Act (15 USC 7701-7713)

CAN-SPAM governs commercial email. Key requirements:

| Requirement | Detail |
|-------------|--------|
| **Accurate headers** | From name, email address, and routing info must be accurate |
| **Non-deceptive subject lines** | Cannot mislead about content |
| **Identify as ad** | Must clearly identify message as advertisement |
| **Physical address** | Must include valid physical postal address |
| **Opt-out mechanism** | Must include clear way to unsubscribe |
| **Honor opt-outs** | Within 10 business days |
| **No opt-out list transfer** | Cannot sell/transfer email addresses of people who opted out |

**B2B emails:** CAN-SPAM applies to ALL commercial email, including B2B. There is no B2B exemption. However, enforcement focus is overwhelmingly on consumer-facing spam.

**Penalties:** Up to $51,744 per violation (FTC-enforced).

**Important for your business:** CAN-SPAM does NOT require prior consent for cold email (unlike many countries' laws). You CAN send unsolicited commercial email as long as you comply with the requirements above. This makes cold email to investors a relatively lower-risk channel compared to phone calls.

### 4d. NMLS/State Licensing for Loan Officers

The LOs buying your leads must be:
- Licensed through NMLS (Nationwide Multistate Licensing System)
- Licensed in the state where the borrower/property is located
- Compliant with their state's specific advertising and solicitation rules
- Operating under their employer's compliance framework

**Your exposure:** If you sell leads to unlicensed individuals or entities, you could face scrutiny for facilitating unlicensed mortgage solicitation. Verifying NMLS status of lead buyers is a reasonable safeguard.

---

## 5. RESPA / Mortgage-Specific Rules

### 5a. RESPA Section 8 — Kickbacks and Referral Fees (12 USC 2607)

RESPA Section 8(a) prohibits:

> "Any fee, kickback, or thing of value pursuant to any agreement or understanding, oral or otherwise, that business incident to or a part of a real estate settlement service involving a federally related mortgage loan shall be referred to any person."

Section 8(c)(2) carves out an exception for:

> "Payment to any person of a bona fide salary or compensation or other payment for goods or facilities actually furnished or for services actually performed."

### 5b. Does Selling Lead Lists to LOs Violate RESPA Section 8?

**Short answer: Almost certainly NO, if structured correctly.**

**Why it should be safe:**

1. **You are not a settlement service provider.** RESPA Section 8 applies to referral fees *between settlement service providers* (lenders, title companies, real estate agents, appraisers, etc.). A data/lead company that is not itself involved in the settlement process is generally not covered.

2. **Leads are not referrals.** A "referral" under RESPA means directing a specific consumer to a specific settlement service provider. Selling a list of potential prospects is not a referral — it is selling marketing data. The LO still has to contact, qualify, and convert the lead.

3. **Payment for goods actually furnished.** Under Section 8(c)(2), payment for actual services or goods (like a compiled lead list) is explicitly permitted. The key is that the payment must be for the list itself, not contingent on closed loans.

4. **Industry practice.** Companies like Zillow, LendingTree, Bankrate, and dozens of lead generation companies sell mortgage leads to LOs. This is a well-established, multi-billion-dollar industry.

**What WOULD create RESPA risk:**

- **Per-closed-loan pricing:** If you charge LOs per closed loan rather than per lead or per list, that looks like a referral fee
- **Exclusive referral arrangements:** If an LO pays you a fee and in return you exclusively direct leads only to them, that looks more like a kickback
- **Quid pro quo:** If the LO gives you something of value (referrals, business, below-market services) in exchange for leads, that could trigger Section 8

### 5c. CFPB Bulletin 2015-05: Marketing Services Agreements

The CFPB issued Compliance Bulletin 2015-05 specifically warning about Marketing Services Agreements (MSAs) that are used to disguise referral fees. Key findings:

- "Many MSAs are designed to evade RESPA's prohibition on the payment and acceptance of kickbacks and referral fees"
- The CFPB found instances where companies paid for "marketing services" but the payments were really based on how many referrals were received
- Over $75 million in penalties assessed for RESPA violations
- Penalties have included bans on entering MSAs or working in the mortgage industry for up to 5 years

**Relevance to your model:** Your business is NOT an MSA. You are selling a product (data/leads) to LOs, not entering into a mutual marketing arrangement between settlement service providers. This is fundamentally different from the MSA structures the CFPB targeted. However, you should:
- Price leads per record or per list, not per closed loan
- Not require LOs to refer any business back to you
- Not structure any revenue-sharing based on loan outcomes

### 5d. Trigger Leads vs. Your Model

"Trigger leads" are a specific practice where credit bureaus sell lists of consumers who just pulled their credit for a mortgage. These are generated from credit inquiry data and sold to competing lenders.

**The Homebuyers Privacy Protection Act (effective ~March 2026) bans trigger leads** — but your model is completely different:
- Trigger leads = credit bureau inquiry data (FCRA-regulated)
- Your model = public property records + skip trace (not FCRA-regulated)

Your system does NOT use credit bureau data and is NOT affected by the trigger lead ban.

---

## 6. How Existing Companies Handle This

### 6a. PropStream

- Provides property data, owner info, skip tracing, and lead lists to real estate investors
- **Positions as:** Real estate data platform, NOT a CRA
- **FCRA disclaimer:** Standard disclaimer that data is not a consumer report and cannot be used for FCRA purposes
- **Compliance approach:** Places compliance burden on the user through terms of service

### 6b. BatchData (formerly BatchSkipTracing)

- Provides skip trace and property data API
- **Positions as:** Data provider for real estate investors
- **FCRA disclaimer:** Explicitly states they are not a CRA; prohibits FCRA uses in TOS
- **Data use restrictions:** Contractually prohibits use for credit, employment, insurance, or tenant screening decisions

### 6c. CoreLogic (now Cotality) / ATTOM Data

- Largest property data aggregators in the US
- **Positions as:** Data licensing companies providing property and analytics data
- **FCRA approach:** Maintain separate product lines — property data products are explicitly non-FCRA; credit/tenant screening products are FCRA-compliant through separate divisions
- **Licensing model:** Enterprise data licensing agreements with explicit use restrictions

### 6d. Reonomy

- Commercial real estate data platform
- **Positions as:** B2B commercial data provider (not consumer data)
- **Key distinction:** Focuses on commercial property and entity data, further distancing from FCRA

### 6e. Skip Trace Companies (Tracerfy, SkipGenie, REISkip)

Common compliance approach across the skip trace industry:
1. **FCRA disclaimer on every product page and in TOS** — "This product is not a consumer report"
2. **Prohibited uses clearly listed** — cannot use for credit, employment, insurance, tenant screening
3. **User certification** — require users to certify their intended use before accessing data
4. **No compliance guidance on outreach** — generally place all TCPA/DNC compliance burden on the customer

### 6f. Key Takeaway from Industry

Every major player in this space operates by maintaining a clear wall between "marketing data" (not FCRA) and "consumer reports" (FCRA). The wall is maintained through:
- Explicit contractual terms
- FCRA disclaimers
- Prohibited use policies
- User certifications
- NOT including credit scores, payment history, or account data

---

## 7. CFPB Data Broker Rulemaking (2024-2026)

### What Happened

In December 2024, the CFPB proposed a rule that would have expanded FCRA to cover certain data brokers by treating the sale of consumer data as furnishing "consumer reports." The proposal targeted:
- Data brokers selling sensitive location data
- Data brokers selling consumer communications metadata
- Certain header data and consumer contact information sold for targeted marketing

### Current Status (as of March 2026)

**This rule is almost certainly dead or indefinitely delayed.** The CFPB under the current administration (post-January 2025) has dramatically scaled back rulemaking and enforcement. The data broker rule was a late-stage Biden-era CFPB proposal that:
- Never received a final rule
- Was not finalized before the administration change
- Has not been advanced by the current CFPB leadership
- Is likely to be withdrawn or allowed to expire

### What This Means for You

- The current regulatory posture is more permissive for data brokers than 2024
- However, the underlying legal framework (FCRA, TCPA) hasn't changed
- State-level data privacy laws (especially California's CCPA/CPRA) are increasingly relevant but do not specifically regulate this business model's core activities
- A future administration could revive this rulemaking

---

## 8. State-Specific Rules: Florida & North Carolina

### 8a. Florida

**Florida Telemarketing Act (FS 501.601-501.626):**

| Requirement | Detail |
|-------------|--------|
| **Telemarketing license** | Required — $1,500/year from FDACS |
| **Salesperson license** | $50/year per individual making calls |
| **Surety bond** | $50,000 face value |
| **Calling hours** | 8 AM - 8 PM local (stricter than federal 9 PM) |
| **Call frequency** | Max 3 calls per 24 hours on same subject |
| **Caller ID** | Must display accurate number; spoofing = 2nd degree misdemeanor |
| **State DNC** | Florida maintains its own DNC list (separate from federal) |

**FL Exemptions (FS 501.604):**
- **Supervised financial institutions** (banks, credit unions, S&Ls) are EXEMPT when operating within scope of supervised activity
- **Licensed insurance agents** are EXEMPT within scope of license
- **Licensed real estate professionals** (Chapter 475) are EXEMPT
- **Securities brokers/dealers** are EXEMPT within license scope
- **Mortgage loan officers** — NOT explicitly listed as exempt. LOs working for a bank may inherit the bank's exemption; independent LOs and mortgage brokers likely do NOT qualify

**Critical implication for FL:** If your LO customers are independent mortgage brokers (not bank employees), they likely need a Florida telemarketing license to cold-call FL residents, OR they need to hire a licensed telemarketer. This is a compliance issue for your customers, but one you should flag.

### 8b. North Carolina

**NC Telephone Solicitations Act (GS Chapter 75, Article 4):**

| Requirement | Detail |
|-------------|--------|
| **Registration** | NC relies on federal DNC registry (no separate state registration) |
| **Calling hours** | 8 AM - 9 PM local |
| **DNC compliance** | Must scrub against federal DNC registry |
| **Internal DNC** | Must remove callers within 30 business days of request |
| **Penalties** | $500 (1st), $1,000 (2nd), $5,000 (3rd+) within 2 years |

**NC Exemptions:**
- Prior express permission
- Established business relationship
- Tax-exempt nonprofits
- Small businesses (fewer than 10 employees)
- **NO specific financial services exemption** (unlike Florida)
- **NO B2B exemption** — applies to residential telephone subscribers

**NC vs FL:** North Carolina is significantly less burdensome than Florida. No state telemarketing license required, no bond, no separate state DNC registry, and penalties are lower. However, there is no financial services carve-out.

---

## 9. What Makes This Clearly Compliant vs Clearly Illegal

### CLEARLY COMPLIANT (Green Zone)

1. **Aggregating public property records and selling them** — this is what CoreLogic, ATTOM, and every title company in America does
2. **Using skip trace data for marketing outreach** — standard practice across real estate, debt collection, and direct marketing industries
3. **Selling lead lists to LOs at a flat per-record or subscription price** — this is a product sale, not a referral fee
4. **Including property data** (address, owner name, entity type, assessed value, deed dates) — all public record, no FCRA issue
5. **Cold emailing investors with CAN-SPAM compliance** — legal, lower risk than phone calls
6. **Manual cold calling to landlines with DNC scrubbing** — legal with proper compliance

### GRAY ZONE (Proceed with Caution)

1. **Including detailed financial estimates** (equity calculations, mortgage balance estimates, DSCR estimates) — the more financial analysis, the closer to FCRA territory. Mitigate with strong disclaimers.
2. **Cold calling cell phones** — legal if done manually (no autodialer), but must still scrub DNC and honor opt-outs. TCPA litigation risk is significant even for compliant callers.
3. **Wealth scoring / net worth estimates** — could be construed as "bearing on creditworthiness." Label clearly as estimates for marketing purposes only.
4. **Selling to unlicensed individuals** — if buyers use the data for unlicensed mortgage solicitation, you could face indirect liability. Verify NMLS.

### CLEARLY ILLEGAL (Red Lines)

1. **Selling data as a "credit report" or for credit decisions** — instant FCRA violation, $1,000/consumer statutory damages
2. **Including actual credit scores, credit account data, or payment history** — this IS a consumer report
3. **Pricing leads per closed loan** — RESPA Section 8 violation (referral fee)
4. **Using an autodialer to call cell phones without consent** — TCPA violation, $500-$1,500/call
5. **Ignoring DNC registries** — $51,744/violation (FTC), $500-$1,500/call (TCPA private right of action)
6. **Cold calling FL residents without a telemarketing license** — state criminal penalties
7. **Selling trigger leads from credit bureau data** — violates HPPA (effective 2026) and FCRA prescreening rules
8. **Making deceptive claims about the data** — FTC Section 5 unfair/deceptive practices

---

## 10. Liability Split: Data Aggregator vs Loan Officer

### Your Liability (as the data provider/aggregator)

| Risk Area | Your Exposure | Mitigation |
|-----------|--------------|------------|
| **FCRA** | LOW if properly structured — you are selling marketing data, not consumer reports | FCRA disclaimers, prohibited use policy, user certification |
| **TCPA** | VERY LOW — you don't make calls | Terms of service requiring customer TCPA compliance |
| **CAN-SPAM** | VERY LOW — you don't send emails | Terms requiring customer CAN-SPAM compliance |
| **RESPA** | LOW — you are not a settlement service provider | Flat pricing, no per-loan fees, no reciprocal referral arrangements |
| **State telemarketing** | NONE — you are not telemarketing | N/A |
| **FTC Section 5** | MODERATE — if data is inaccurate and causes harm | Data quality practices, accuracy disclaimers |
| **State data privacy** | LOW-MODERATE — varies by state | Privacy policy, data handling practices |

### LO's Liability (as the caller/emailer)

| Risk Area | Their Exposure | Your Role |
|-----------|---------------|-----------|
| **TCPA** | HIGH — they are the ones making calls | Provide DNC-scrubbed data, flag cell vs landline |
| **TSR** | HIGH — they are the telemarketer/seller | Include compliance guidance with lead delivery |
| **CAN-SPAM** | MODERATE — they send the emails | Provide opt-out guidance |
| **RESPA** | MODERATE — they are the settlement service provider | Structure pricing to avoid referral fee appearance |
| **State telemarketing** | HIGH — varies by state | Flag state-specific requirements |
| **NMLS/licensing** | HIGH — must be licensed in relevant state | Verify NMLS before selling leads |

### Key Principle

**The data provider bears primary liability for data-related compliance (FCRA, accuracy). The caller/emailer bears primary liability for outreach compliance (TCPA, CAN-SPAM, state telemarketing).** However, the FTC has pursued "assisting and facilitating" theories against data providers whose data was used for illegal purposes, particularly where the provider knew or should have known about the illegal use.

---

## 11. Recommended Safeguards

### Must-Have (Non-Negotiable)

1. **FCRA Disclaimer** — On your website, in your terms of service, and on every data delivery:
   > "This data is not a consumer report as defined by the Fair Credit Reporting Act (15 USC 1681 et seq.). This data may not be used for any purpose regulated by FCRA, including but not limited to: credit decisions, employment screening, insurance underwriting, or tenant screening."

2. **Acceptable Use Policy** — Require every customer to certify they will NOT use data for FCRA-regulated purposes

3. **DNC Scrubbing** — Scrub all phone numbers against federal DNC before delivery; flag or remove DNC-registered numbers

4. **Phone Type Classification** — Classify phones as mobile/landline/VoIP so LOs know TCPA rules for each number

5. **NMLS Verification** — Verify buyers are licensed LOs before selling mortgage-targeted leads

6. **Flat Pricing** — Price per record, per list, or per subscription. NEVER per closed loan.

7. **Terms of Service** — Include:
   - FCRA prohibited use certification
   - Customer's responsibility for TCPA/CAN-SPAM/state compliance
   - No guarantee of data accuracy
   - Indemnification clause

### Should-Have (Best Practice)

8. **Compliance Guide** — Provide customers a brief compliance guide covering DNC, TCPA calling rules, CAN-SPAM requirements, and state-specific notes for FL/NC

9. **State DNC Scrubbing** — For FL leads, also scrub against Florida's state DNC list

10. **TCPA Litigator Flagging** — Flag known TCPA serial litigants in the data (services like Litigator Scrub exist for this)

11. **Data Freshness Disclosure** — Disclose the date of the underlying data; stale data leads to wrong-number complaints

12. **Opt-Out Mechanism** — Allow property owners who contact you to opt out of future lead lists (not legally required for public records, but good practice and reduces complaints)

13. **Record Retention** — Keep records of what data was sold to whom, when, and what certifications were obtained. Retain for 6+ years.

### Nice-to-Have (Competitive Advantage)

14. **Insurance** — Errors & omissions (E&O) insurance and cyber liability insurance
15. **Legal Review** — Have an attorney review your TOS, FCRA disclaimer, and AUP annually
16. **SOC 2 / Security Practices** — If handling data at scale, basic security hygiene documentation

---

## 12. Sources & Citations

### Statutes

| Law | Citation | Relevance |
|-----|----------|-----------|
| Fair Credit Reporting Act | 15 USC 1681-1681x | Consumer report definitions, CRA requirements |
| FCRA — Consumer Report definition | 15 USC 1681a(d) | What IS a consumer report |
| FCRA — CRA definition | 15 USC 1681a(f) | What IS a consumer reporting agency |
| FCRA — Permissible Purposes | 15 USC 1681b | When consumer reports can be furnished |
| TCPA | 47 USC 227 | Autodialer restrictions, DNC, cell phone rules |
| CAN-SPAM Act | 15 USC 7701-7713 | Commercial email requirements |
| CAN-SPAM — Requirements | 15 USC 7704 | Specific compliance obligations |
| RESPA — Kickbacks | 12 USC 2607 | Prohibited referral fees |
| RESPA — Settlement services | 12 USC 2602(3) | Definition of covered services |
| FTC Telemarketing Sales Rule | 16 CFR 310 | DNC, calling rules, seller/telemarketer |
| Gramm-Leach-Bliley Act | 15 USC 6801 | Financial privacy obligations |
| FEC Disclosure | 52 USC 30111 | Public access to donation records |
| FL Telemarketing Act | FL Stat. 501.601-501.626 | FL-specific telemarketing rules |
| FL Exemptions | FL Stat. 501.604 | Who is exempt from FL telemarketing act |
| FL Call Restrictions | FL Stat. 501.616 | Calling hours, frequency, caller ID |
| NC Telephone Solicitations Act | NC GS Chapter 75, Article 4 | NC-specific telemarketing rules |

### Regulatory Guidance

| Source | Document | Key Finding |
|--------|----------|-------------|
| CFPB | Compliance Bulletin 2015-05 (Oct 2015) | MSAs are high-risk for RESPA violations; >$75M in penalties assessed |
| CFPB | Proposed Data Broker Rule (Dec 2024) | Would have expanded FCRA to data brokers; likely dead under current administration |
| FTC | Spokeo Enforcement (2012) | $800K fine for operating as unregistered CRA while aggregating public records |
| FTC | Data Brokers Report (May 2014) | Categorized data brokers; recommended transparency legislation |
| CFPB | Homebuyers Privacy Protection Act | Bans trigger leads from credit bureaus; does NOT affect public records |

### Industry Practice

| Company | How They Position Data | FCRA Approach |
|---------|----------------------|---------------|
| PropStream | Real estate data platform | Not a CRA; FCRA-use prohibited in TOS |
| BatchData | Data provider for RE investors | Not a CRA; explicit prohibited use policy |
| CoreLogic/Cotality | Data licensing company | Separate FCRA and non-FCRA product lines |
| ATTOM Data | Property data licensing | Enterprise agreements with use restrictions |
| Tracerfy | Skip trace provider | Not a CRA; requires user certification |

### Key Case Law

| Case | Citation | Relevance |
|------|----------|-----------|
| *Feist v. Rural Telephone* | 499 U.S. 340 (1991) | Facts (like property records) are not copyrightable |
| *Spokeo v. Robins* | 578 U.S. 330 (2016) | FCRA standing requires concrete injury; narrowed but did not eliminate private rights of action |
| *Facebook v. Duguid* | 592 U.S. 395 (2021) | Narrowed ATDS definition under TCPA; equipment must use random/sequential number generator |

---

## Summary Assessment

**This business model is legally viable and operates in the same space as established, well-funded companies.** The core activity — aggregating public records, enriching with contact data, and selling to marketing users — is legal and widely practiced.

The primary risks are:
1. **FCRA creep** — as you add more financial analysis to the product, maintain strong disclaimers
2. **Customer non-compliance** — your customers (LOs) bear the outreach compliance risk, but you should provide guidance and require certifications
3. **RESPA structuring** — keep pricing flat, never per-closed-loan
4. **Regulatory change** — a future CFPB could revive the data broker rulemaking; monitor this

The business model is **not novel or legally untested**. PropStream, BatchData, ATTOM, CoreLogic, and dozens of smaller companies operate this exact model. The key is proper legal infrastructure: FCRA disclaimers, acceptable use policies, and customer certifications.
