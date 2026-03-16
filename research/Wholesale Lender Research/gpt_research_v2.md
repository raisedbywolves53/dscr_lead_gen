# Research Plan for a Non-QM and DSCR Wholesale Lender Landscape Study

## Executive summary

The attached prompt defines a multi-part research effort to map the U.S. wholesale **DSCR (Debt Service Coverage Ratio)** and broader **Non-QM** ecosystem for mortgage brokers and loan officers, with the explicit goal of supporting B2B positioning for a lead-generation product. fileciteturn0file0

This research plan is designed to produce (a) a structured lender/program dataset, (b) a state-by-state licensing and “business-purpose vs. consumer-purpose” treatment map, (c) broker-channel market intelligence (channel share, sourcing patterns, pain points, comp structures, fallout drivers), (d) competitor intelligence on “DSCR/investor lead” providers, and (e) a Florida (outside South Florida) county/metro opportunity model that connects rents, prices, insurance dynamics, STR activity, and DSCR math into a 2026 ranking.

Given the prompt’s 2025–2026 framing, the plan emphasizes **primary/official sources** (lender guidelines/sellers guides, state regulators, NMLS resources, federal regulations) and **recency (default: last 5 years)**, with explicit versioning and “as of” timestamps because program terms and licensing realities change frequently. For the legal/compliance components, the plan anchors on federal baseline definitions (e.g., Regulation Z business-purpose exemptions) and then layers state-specific requirements using regulator publications and statutes. citeturn0search4turn0search1turn0search0turn0search3

## Prompt interpretation and assumptions

### What the prompt is asking for

The prompt is scoped to five workstreams (directory, licensing, channel dynamics, competitor intelligence, and Florida market sizing/DSCR math). fileciteturn0file0 It is also implicitly a **go-to-market enablement** research task: the end product should help you “speak broker/lender language,” reflect real underwriting frictions, and support differentiated messaging.

### Explicitly specified vs. unspecified items

The table below lists key scope dimensions and labels anything not provided as **unspecified** (rather than guessing).

| Dimension | Status | Notes |
|---|---|---|
| Topic | Specified | Wholesale DSCR / Non-QM ecosystem and broker-channel intelligence. fileciteturn0file0 |
| Geography | Partially specified | U.S. states implied; Florida counties/metros explicitly called out for Part 5. Any focus on *specific additional states* is **unspecified**. fileciteturn0file0 |
| Timeframe (“as of”) | Partially specified | “As of 2025–2026” is specified, but the exact **cutoff date** is **unspecified**. Recommendation: set “as-of” to **March 16, 2026** (current date in America/New_York) unless you specify otherwise. fileciteturn0file0 |
| Depth (“every major lender”) | Unspecified | “Major” needs an operational definition (volume rank, broker adoption, #states licensed, securitization issuer presence, etc.). |
| Product scope (loan types) | Partially specified | Focus is DSCR loans; treatment of adjacent investor products (bank statement, asset depletion, DSCR HELOC, bridge-to-DSCR) is **unspecified**. |
| Property scope | Partially specified | Prompt names multiple property types (SFR through mixed-use, STR, etc.). Whether to include true commercial (10+ units) is **unspecified**. fileciteturn0file0 |
| Rate reporting | Unspecified | Whether you want “rate ranges/spreads” as public approximations vs. no rates (due to volatility and disclosure risk) is **unspecified**. Because SOFR and market rates move daily, any rate capture must be timestamped. citeturn5search6turn5search2 |
| Licensing analysis intent | Unspecified | Whether you want a **compliance-ready** resource or a **marketing-intel** “high level, not legal advice” map is **unspecified**. (This affects depth, attorney review needs, and how claims are phrased.) |
| Data-access constraints | Unspecified | Subscriptions to paywalled sources (e.g., Inside Mortgage Finance, Optimal Blue datasets, AirDNA paid cuts, Core transaction data) are **unspecified**. citeturn1search6turn7search3turn2search2 |
| Deliverable format | Unspecified | Whether you prefer a spreadsheet-first deliverable (CSV/Sheets) vs. report-first (PDF/Deck) is **unspecified**. |

## Research objectives and key questions

### Objectives

The research should reliably answer five practical questions that map to product positioning:

1. **Who matters** in wholesale DSCR (lenders, aggregators, capital sources) and **how their DSCR programs differ** in ways that brokers feel day-to-day.
2. **Where brokers can legally originate** DSCR and what licensing regimes (company vs. individual) and extra state constraints materially change operations.
3. **How brokers operate** in DSCR: partner selection, bottlenecks, comp norms, fallout drivers, and how volume flows across channels.
4. **Which “lead/data providers” compete** with your future offer and what feature gaps remain (ICP scoring, entity resolution, financing intelligence, exclusivity, AI talk-tracks).
5. **Which Florida markets (outside South Florida) pencil best in 2026** when using DSCR math under realistic assumptions (rates, insurance, vacancy, STR regulation).

### Key questions to answer (organized by workstream)

For the lender directory:

- Which lenders offer **broker/wholesale-accessible DSCR** programs, and which are retail-only or correspondent-only?
- For each lender, what are the *current* “binding constraints” that affect broker conversion: min DSCR, max LTV, min FICO, IO availability, STR/AirDNA acceptance, entity vesting, property types, and typical turn times? fileciteturn0file0

For state licensing:

- What state regimes govern **company licensing** and **individual MLO licensing** for DSCR origination, and what special requirements (bonds, registrations, exemptions) exist?
- Where is DSCR treated as “business-purpose” in practice, and where do state consumer lending laws or interpretations complicate that assumption? Federal baseline: certain business-purpose and non-natural-person credit is exempt from Regulation Z, but this does not automatically resolve state-level requirements. citeturn0search4turn0search1

For broker channel dynamics:

- What share of overall originations flows through wholesale/broker vs. retail vs. correspondent, and what can be credibly said about DSCR specifically given data limitations? citeturn1search6turn1search2turn1search7
- What are the most reported DSCR pain points (conditions, appraisals, guideline volatility, reserves, insurance/HOA, STR documentation, rent schedule issues)? fileciteturn0file0

For competitive intelligence:

- Which providers sell investor or DSCR-adjacent leads/data, what they actually sell (data vs. intent vs. scored leads), and how pricing/exclusivity works.
- Where are the gaps relative to your envisioned offer (ICP scoring, entity resolution, financing intelligence, AI talk-tracks, geographic exclusivity)? fileciteturn0file0

For Florida opportunity modeling:

- At a county/metro level, what are current prices, rents, vacancy signals, investor activity proxies, insurance trends, and STR saturation/constraints—and how do those translate into DSCR at 25% down under 2026 rate assumptions? fileciteturn0file0

## Methodology and search strategy

### Overall workflow

The most reliable way to execute this prompt is to treat it as a **data-engineering + evidence synthesis** problem:

1. **Define a data dictionary** up front for every requested field (especially DSCR calculation conventions and “property types allowed” taxonomies).
2. Build a **candidate universe** (lenders, lead providers, datasets) using high-recall discovery sources.
3. For each entity, extract facts from **primary sources** first, then use secondary sources (industry press, reviews, broker forums) as attribution and triangulation.
4. Version everything with (a) “source document date,” (b) “last checked” date, and (c) confidence level.

### Source strategy by workstream

#### Lender directory (program comparison + footprint)

Primary sources to prioritize:

- Lender **program guides / underwriting guidelines / matrices**, broker portals, and published bulletins (these are most likely to contain minimum DSCR, LTV/FICO gates, property eligibility, IO terms, STR documentation rules, reserves, and entity-vesting policies).
- **NMLS Consumer Access** for verifying licensing status and footprint where available, since it is designed to let the public view information on state-licensed companies, branches, and individuals. citeturn3search4turn3search16
- When lender “state licensing” pages exist, use them as a secondary cross-check, not the sole authority, because they can be incomplete or stale relative to regulator records.

High-recall discovery sources (used to find the “universe,” then verified with primary documents):

- Industry rankings and directories (e.g., Non-QM lender rankings) to identify large participants and new entrants. citeturn1search1
- Industry news and securitization presale/rating reports for evidence of active DSCR pools, DSCR distributions, and entity vesting prevalence (helpful for validating what is common in practice, even if not a broker-facing guide). citeturn7search6turn7search14

Data extraction method (recommended):

- Create one **master spreadsheet** where each lender-program row is keyed by:
  - Lender (legal entity + d/b/a if relevant)
  - Channel availability (wholesale, correspondent, retail)
  - Program variant (e.g., DSCR purchase, DSCR cash-out, STR DSCR)
  - “As-of” date and document version
- Use structured text extraction from PDFs where needed, but always retain the original PDF link/file reference and page numbers.

#### State licensing map (company + individual + “business-purpose” classification)

Primary sources to prioritize:

- **NMLS State Resource Center** tools:
  - Licensing checklists and requirement charts to establish baseline state-by-state license types, requirements, and fees. citeturn0search2turn3search5turn3search1
- State regulator websites and statutes for:
  - Definitions of “residential mortgage loan,” “mortgage broker,” “commercial/business-purpose,” and exemptions.
  - Bonding, call report, net worth, branch management, and “loan processor/underwriter” registration rules where applicable.

Federal baseline to frame the analysis (then state-specific layering):

- Regulation Z outlines categories of **exempt transactions**, including extensions of credit primarily for business/commercial purposes and extensions of credit to entities (non-natural persons). This is central to how DSCR is often positioned as “business-purpose.” citeturn0search4turn0search1
- ATR/QM rules are implemented in Regulation Z for covered consumer credit transactions secured by a dwelling; therefore, properly classified business-purpose credit is generally outside ATR/QM—yet state law may still impose licensing and other obligations. citeturn0search0turn0search3

Practical implementation approach:

- Build a **50-state matrix** with fields:
  - Company license required to broker DSCR? (Yes/No/Conditional/Unclear)
  - Individual MLO license required? (Yes/No/Conditional/Unclear)
  - Nonstandard requirements (bond, special registration, real estate license overlay, etc.)
  - “Business-purpose” treatment notes (statutory or regulator guidance citations)
  - Confidence grade (High/Medium/Low) + last reviewed date
- Treat “contested/unclear” categorization as a first-class output—not a failure—to avoid false certainty.

#### Broker channel dynamics (share, behavior, pain points, comp, fallout)

Primary sources and reputable market sources:

- Channel share estimates from market analytics providers and established industry research. For example, one widely cited data point is broker share of originations (overall, not DSCR-specific), which some industry sources report around ~20% in 2025, but these figures may be packaged behind paywalls and require careful citation and method review. citeturn1search6turn1search10
- For definitions and consistent channel taxonomy (retail vs wholesale vs correspondent), use industry advisory explanations as a baseline. citeturn1search2
- For Non-QM’s recent footprint in lock volume, industry reporting citing datasets like Optimal Blue’s Market Advantage can be used to frame magnitude (again, with method caveats). citeturn7search3
- Explicitly incorporate **data limitations**:
  - HMDA reporting has complex scope rules and may not cleanly capture business-purpose investor lending, so DSCR channel sizing may require triangulation across sources and proxies rather than a single dataset. citeturn1search7turn1search3

Data collection approach:

- Use a mixed-method synthesis:
  - Quant: channel share (overall), Non-QM share (overall), DSCR proxies where available.
  - Qual: broker interview synthesis (if you choose), broker forum analysis, and lender AE content for pain points and workflow friction.

#### Competitive intelligence (lead/data providers)

Primary sources to prioritize:

- Provider websites: product pages, pricing pages, terms, feature lists, and documentation (to classify “what they sell”).
- Public customer review platforms and credible third-party writeups (used cautiously; identify potential bias).
- Where competitor claims are critical (e.g., “exclusive leads”), cross-check with:
  - Terms of service language
  - Sales collateral
  - Multiple independent user reports (flag conflicts)

Output modeling:

- Build a competitor matrix with standardized columns aligned to your prompt:
  - Data type (property data / contact data / intent / scoring)
  - Exclusivity options
  - Data freshness & sourcing
  - Integrations (CRM, dialer)
  - Any financing intelligence
  - Evidence links + notes

#### Florida market model (outside South Florida)

This workstream is best approached as a reproducible **data pipeline + scenario model**:

Core datasets (primary/reputable):

- Home price levels and trends:
  - Use publicly downloadable and well-documented indices such as **Zillow Research data** (ZHVI/ZORI ecosystem) and/or **FHFA HPI** for trend context. Zillow publishes downloadable housing datasets and methodology; FHFA provides datasets and describes HPI construction. citeturn5search0turn5search15turn5search1turn5search5
- Rent levels and vacancy proxies:
  - Use **U.S. Census / ACS** tables such as median gross rent and housing characteristics (e.g., vacancy rate in DP04). citeturn2search3turn2search7
- STR supply/demand:
  - Use STR analytics providers as sources (e.g., AirDNA describes tracking performance data across major STR platforms and publishes outlook/report materials). citeturn2search2turn2search6
- Rates / benchmark framing:
  - If you present “spread over benchmark,” choose a clearly defined benchmark like **SOFR** (defined by the New York Fed; also distributed via FRED), but timestamp it and separate “benchmark” from “mortgage coupon,” since DSCR rates are typically quoted directly rather than as an index + margin to borrowers. citeturn5search6turn5search2
- Insurance trend context (critical in Florida DSCR math):
  - Use Florida regulator and quasi-public entities’ publications, such as the **Florida Office of Insurance Regulation** market updates and **Citizens** rate filing materials, with the understanding they describe important slices of the market and conditions. citeturn2search0turn2search1turn2search9

Investor activity proxies:

- Use reputable national investor activity reporting (e.g., Redfin investor reports, ATTOM summaries, and CoreLogic/Cotality-style investor reporting) to contextualize investor demand and potential saturation, and then map to Florida metros where data exists. citeturn6search0turn6search1turn6search2

Model design (recommended):

- Produce a county/metro scoring model with:
  - DSCR estimate (scenario-based: rates ±100 bps; taxes/insurance bands)
  - Rent-to-price ratio
  - vacancy proxy
  - insurance risk proxy (trend + level)
  - STR saturation and regulatory friction score
  - investor activity indicator
- Output should be scenario-driven and should clearly label assumptions as **user-specified** or **unspecified** until confirmed.

## Inclusion criteria, exclusions, and verification

### Inclusion criteria (recommended defaults unless you specify otherwise)

- Include lenders that:
  - Offer **DSCR or investor cash-flow** loans on 1–4 unit residential investment properties (and include 5–8 units only if the program is clearly documented and broker-accessible).
  - Are accessible through the **wholesale/broker** channel (or clearly have a broker/TPO program).
  - Have evidence of activity in the 2025–2026 window (guidelines, bulletins, active licensing, recent press, recent securitization participation).

### Exclusion rules (recommended defaults)

- Exclude (or label separately) lenders that are:
  - Retail-only (no broker channel) unless you explicitly want them as “competitive alternatives.”
  - Pure hard-money/short-term bridge products with no DSCR underwriting component (unless you choose to include “bridge-to-DSCR” as adjacent market).
  - Inactive or exited brands—unless the deliverable includes an “inactive/defunct” appendix.

### Verification and cross-check method

Because many requested fields change frequently (rates, DSCR floors, IO availability, turn times), verification should be systematic:

- **Two-source rule for key fields**: For any “deal-driving” field (min DSCR, max LTV, min FICO, IO rules, STR income rules, entity vesting), prefer (1) the lender’s current guide or bulletin and (2) one corroborating artifact (rate sheet, matrix, scenario desk response, or dated broker portal screenshot/PDF).
- **License footprint**:
  - Verify via NMLS Consumer Access where available, because it is explicitly intended to show licensing information for state-licensed entities. citeturn3search4turn3search16
  - Cross-check with state regulator licensee search pages when a state offers an official alternative (some state agencies explicitly direct users to NMLS Consumer Access for additional licensing detail). citeturn3search6turn3search21
- **Regulatory framing**:
  - Use federal regulation text as the definitional baseline for “business-purpose exemption” framing (Reg Z), but treat state-level conclusions as jurisdiction-specific and cite the specific statute/regulator guidance. citeturn0search4turn0search1
- **Timestamp discipline**:
  - Every extracted field should carry “document date” + “checked date,” and the final report should include an “as-of” header.

## Deliverables and estimated timelines

The table below proposes deliverables in a way that maps cleanly to product and marketing use (enablement + data asset). Timelines are estimates and depend heavily on **(a) how you define “major,” (b) how many lenders end up in scope, and (c) whether you have paywalled data access** (all currently **unspecified**).

| Deliverable | Format recommendation | What it contains | Estimated timeline |
|---|---|---|---|
| Research spec + data dictionary | Short memo + spreadsheet schema | Definitions for every field (DSCR calc conventions, property type taxonomy, channel definitions), “as-of” date and scope lock | 0.5–1 business day |
| Wholesale DSCR lender directory (core asset) | Spreadsheet (CSV + Google Sheet) | Lender-level and program-level rows with the fields in Part 1; evidence links; timestamps; confidence ratings | 4–8 business days (depending on lender count) |
| State licensing and treatment map | Spreadsheet + annotated memo | 50-state matrix: company vs individual requirements, special conditions, “business-purpose” notes + citations to regulators/statutes/NMLS resources | 5–10 business days (can run in parallel) |
| Broker channel dynamics brief | 8–15 page memo + 3–5 visuals | Channel share estimates, broker sourcing behavior, pain points, comp norms, pipeline fallout drivers; explicit data limitations | 3–6 business days |
| Competitor intelligence matrix | Spreadsheet + short narrative | Feature/pricing/exclusivity/freshness matrix; documented evidence; “gap analysis” vs your concept | 3–6 business days |
| Florida (non–South Florida) DSCR opportunity model | Spreadsheet model + charts | County/metro scorecard, DSCR scenario math, STR + insurance + vacancy notes, 2026 opportunity ranking | 4–8 business days |
| Final integrated report | Report (Markdown + PDF export) | Executive summary + the five parts + assumptions + appendices + source list | 2–4 business days after components |

## Clarifying questions to finalize scope

Answering the questions below will materially improve accuracy and reduce rework. They are ordered by impact.

1. What is the **operational definition of “major”** lenders for this project (e.g., top 20 by DSCR volume, top 30 by broker adoption, top issuers in non-agency DSCR securitizations, “licensed in ≥X states,” etc.)? (Currently **unspecified**.)
2. What is the intended **audience** for the final outputs (product team only, sales/marketing enablement, investor deck, compliance ops)? (Currently **unspecified**.)
3. Do you want this to be a **compliance-grade** licensing resource (implying legal review), or a **high-level market map** with clear “not legal advice” framing? (Currently **unspecified**.)
4. Should the lender directory include **only wholesale/broker** channels, or also **correspondent** and **retail** DSCR offerings as competitive context? (Currently **unspecified**.)
5. Are **5–8 unit** and **mixed-use** properties in scope as first-class DSCR targets, or should the focus remain on 1–4 unit residential investor DSCR? (Currently **unspecified**.)
6. For “rate range / spread,” do you want:
   - A dated **snapshot** (e.g., typical DSCR rate bands as of a specific week), or
   - No rates at all (only structural pricing drivers), or
   - A “benchmark + spread” conceptual framing (which may not match how brokers see DSCR rate sheets)? (Currently **unspecified**.)
7. Do you have or plan to get access to any of the following datasets/tools (Yes/No for each)?
   - NMLS data exports or manual lookup only
   - Optimal Blue / similar lock-volume datasets
   - Inside Mortgage Finance / other channel share datasets
   - AirDNA paid market cuts vs public materials
   - Core property transaction datasets (CoreLogic/Cotality, ATTOM paid files, First American, etc.)  
   (All currently **unspecified**.) citeturn7search3turn1search6turn2search2turn6search1turn6search2
8. For competitor analysis, do you want **only public pricing**, or is it acceptable to include “call-for-quote” pricing with documented caveats? (Currently **unspecified**.)
9. In Florida DSCR math, should the underwriting assumption be:
   - Market rent (e.g., appraiser rent schedule), or
   - Executed lease rent, or
   - STR revenue modeled via AirDNA (if accepted by certain lenders)?  
   (Priority because it changes DSCR materially; currently **unspecified**.)
10. Should the Florida market ranking optimize for **cash-flow DSCR today** (2026 acquisition math) or for **lead monetization potential** (investor churn, refi triggers, volume), or both? (Currently **unspecified**.)

## Report template, query sets, and visualization plan

### Sample final report outline/template

- Executive summary (what changed vs prior year, key winners/losers, key compliance notes)
- Methodology (as-of date, inclusion criteria, verification approach, limitations)
- Wholesale DSCR lender landscape
  - Market structure (wholesale vs retail vs correspondent)
  - Lender directory (table-driven) + “program archetypes”
  - Common guideline friction points (what breaks deals)
- State licensing and operational constraints
  - 50-state matrix (company + individual)
  - “Business-purpose” treatment notes + contested jurisdictions
  - Practical compliance workflow for brokers (decision tree)
- Broker channel intelligence
  - Channel share and trend (overall + Non-QM proxy + DSCR proxy)
  - How brokers choose DSCR lenders (signals, AEs, events, peer referral)
  - Comp norms and fallout drivers
- Competitor intelligence: DSCR/investor lead providers
  - Product/pricing/exclusivity matrix
  - Gap analysis vs your concept (ICP scoring, entity resolution, financing intelligence, talk-tracks, geo exclusivity)
- Florida opportunity model outside South Florida
  - County/metro scorecard (scenario DSCR)
  - STR + insurance + HOA headwinds
  - 2026 ranking + sensitivity analysis
- Appendices
  - Master lender comparison dataset export
  - State-by-state citations
  - Source list (primary first, then secondary)

### Suggested visualization types and where to use them

- **Wide comparison tables** (primary visualization):
  - Lender program comparison (Part 1)
  - Competitor feature/pricing matrix (Part 4)
  - Florida county/metro scorecard (Part 5)
- **Heatmaps**:
  - State licensing complexity heatmap (Part 2)
  - Florida DSCR “pencils vs doesn’t pencil” heatmap (Part 5)
- **Mermaid flowcharts** (for “how it works” comprehension):
  - Broker workflow: lead → lender selection → UW → appraisal → conditions → close (Part 3)
  - Licensing decision tree: “Is it business-purpose? entity vesting? state triggers?” (Part 2)
- **Timelines (Mermaid or simple annotated timeline)**:
  - 2022–2026 Florida insurance reform and rate/market stabilization milestones (Part 5), anchored to official publications where possible. citeturn2search0turn2search1turn2search9
- **Scatterplots**:
  - Florida markets: rent-to-price vs estimated DSCR (shows which counties are “cash-flow” vs “appreciation only”)
- **Sankey or stacked area chart** (if data is available):
  - Origination channel mix (wholesale vs retail vs correspondent) over time (Part 3). citeturn1search6turn1search10

### Sample search query sets

Below are example queries designed to prioritize **official/primary sources** and **recent (last ~5 years)** material by default. Replace bracketed placeholders.

#### Google Scholar (academic + policy)

```text
"debt service coverage ratio" mortgage underwriting investor
"DSCR loan" "non-QM" securitization performance
"business purpose" mortgage lending state law exemption
"rental income" underwriting appraisal rent schedule methodology
Florida homeowners insurance reform 2022 2023 impact housing
```

#### PubMed (expected lower yield, used selectively)

PubMed is not typically the strongest database for DSCR mortgage underwriting, but it can support adjacent questions (housing affordability stress, displacement, demographic trends, disaster/insurance impacts).

```text
housing affordability Florida insurance premiums
short-term rental regulation housing market
housing costs migration Florida county
```

#### News (general + industry press)

```text
[STATE] mortgage broker license investment property business purpose
[STATE] "mortgage loan originator" licensing requirements investment property
"DSCR loan" wholesale lender launches program 2025 OR 2026
"non-QM" "DSCR" lock volume 2025 2026
Florida Citizens rate filing 2026 premium change
Florida Office of Insurance Regulation market update 2024 2025
```

#### Industry reports / datasets (often partially paywalled)

```text
broker share of mortgage originations 2025 Inside Mortgage Finance
wholesale channel overview broker share STRATMOR 2024
Optimal Blue "Market Advantage" non-QM share 2025
non-QM issuance DSCR loans 2025 S&P presale
DSCR loans comprise % of pool Fitch presale 2025
```

#### Primary/official sites (direct-source targeting)

```text
site:ecfr.gov 1026.3 exempt transactions business purpose
site:consumerfinance.gov 1026.43 ability to repay qualified mortgage
site:mortgage.nationwidelicensingsystem.org license requirements and fees chart
site:nmlsconsumeraccess.org [COMPANY NAME]
site:fhfa.gov house price index datasets
site:data.census.gov median gross rent county
site:citizensfla.com 2026 rate kit
site:floir.gov property insurance market update
```

## Risk and limitations

1. **Program volatility risk**: DSCR guidelines, LTV/FICO gates, STR rules, and IO options can change quickly; any static directory can become stale without systematic timestamping and refresh cycles.
2. **Licensing/compliance complexity risk**: Federal framing (e.g., Reg Z business-purpose exemptions) does not automatically resolve state licensing obligations, and state interpretations can be nuanced; without careful citations and “unclear/conditional” labeling, the output risks overclaiming. citeturn0search4turn0search1turn0search0
3. **Paywall and data-access risk**: Reliable channel share, lock-volume, and DSCR-specific sizing often depends on proprietary datasets and paid research (which may be **unspecified** in availability). citeturn1search6turn7search3turn7search15
4. **HMDA/coverage limitations**: Public regulatory datasets may not cleanly represent DSCR/business-purpose lending; where they are used, the methodology must explicitly disclose scope limits and triangulation logic. citeturn1search7turn1search3
5. **Florida modeling sensitivity**: DSCR “best markets” rankings can swing materially based on assumptions about rates, insurance premiums, taxes, HOA, vacancy, and whether STR revenue is permitted—so scenario modeling and transparent assumptions are required to avoid false precision. citeturn2search0turn2search2turn5search6turn5search2