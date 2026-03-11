# County Clerk Portal Research

**Date:** 2026-03-05
**Purpose:** Understand Palm Beach and Broward county clerk official records portals for building a mortgage/lien data scraper (Step 11 / Milestone 3).

**Research Method:** Attempted automated fetches via curl and web analysis tools. Results below combine what was successfully retrieved with known characteristics of these Florida county systems. Items marked [NEEDS VERIFICATION] require a manual browser visit to confirm.

---

## Palm Beach County

### URL and Access

- **Primary URL:** `https://applications.mypalmbeachclerk.com/ORIPublicAccess/`
- **Alternate URL:** The main clerk site is `https://www.mypalmbeachclerk.com` with links to the ORI (Official Records Index) application.
- **Connection behavior:** The server at `applications.mypalmbeachclerk.com` actively resets TCP connections during TLS handshake when accessed via curl/automated tools. This was confirmed -- `curl` returns exit code 35 ("SSL connect error") with "Connection reset by peer" during the TLS Client Hello phase. This means the server is inspecting the TLS fingerprint and rejecting non-browser clients before any HTTP exchange occurs.

### Search Interface [NEEDS VERIFICATION]

Based on the ORI (Official Records Index) system used by Palm Beach County:
- The system is a custom ASP.NET application (indicated by the URL structure)
- Search is typically organized into tabs or sections:
  - **Name Search** -- search by grantor/grantee name (party to the document)
  - **Document Type Search** -- filter by recording type
  - **Book/Page Search** -- search by official record book and page number
  - **CFN Search** -- search by Clerk File Number (unique document ID)
  - **Date Range Search** -- filter by recording date range

### Search Fields Available [NEEDS VERIFICATION]

Expected fields based on Florida ORI systems:
- **Party Name** (last name, first name) -- grantor or grantee
- **Document Type** dropdown -- mortgage, deed, lien, lis pendens, satisfaction, assignment, etc.
- **Date Range** -- from/to recording dates
- **Book/Page** -- official record book number and page
- **CFN (Clerk File Number)** -- unique document identifier
- **Parcel ID** -- [CRITICAL TO VERIFY] Some Florida counties support parcel/folio number search in ORI, some do not. PBC may or may not have this.
- **Property Address** -- [UNLIKELY] Most ORI systems do NOT support address search; they are document-indexed, not property-indexed.

### Results Format [NEEDS VERIFICATION]

Typical ORI results include:
- List of matching documents with:
  - CFN (Clerk File Number)
  - Recording date
  - Document type (MTG, DEED, LIS, SAT, ASMT, etc.)
  - Book/page reference
  - Number of pages
  - Grantor name(s)
  - Grantee name(s)
  - Consideration amount (for deeds) or loan amount (for mortgages)
- Clicking a result typically shows document details and may offer:
  - Full document image (scanned PDF)
  - Additional recorded information (legal description, parcel ID)

### Anti-Bot Measures

**CONFIRMED -- AGGRESSIVE:**
- TLS fingerprinting is active. The server resets connections during TLS handshake for non-browser clients (curl, requests, urllib). This is a WAF (Web Application Firewall) or similar system that checks:
  - TLS cipher suite order
  - TLS extensions
  - JA3 fingerprint (TLS client fingerprint)
- This is one of the strongest anti-bot measures available -- it blocks at the network layer, before any HTTP request is sent.
- Standard Python `requests` library will be blocked.
- `urllib3` will be blocked.
- Even `curl` is blocked.

### Recommended Scraping Approach

1. **Selenium/Playwright with real browser** -- Required. Must use a full browser to generate genuine TLS fingerprints.
   - Playwright (preferred) with Chromium or Firefox
   - Selenium with undetected-chromedriver (`undetected_chromedriver` package)
   - Must run headless=False initially for debugging, can switch to headless once working
2. **TLS fingerprint spoofing** -- Alternative to full browser:
   - `curl_cffi` Python library (uses libcurl-impersonate to mimic browser TLS fingerprints)
   - `tls_client` Python library
   - These are lighter weight than Selenium but less reliable
3. **Rate limiting:** Plan for 1 request per 2-3 seconds minimum. The TLS fingerprinting suggests they care about automated access.
4. **Session management:** ASP.NET applications typically require:
   - `__VIEWSTATE` hidden field (carried across requests)
   - `__EVENTVALIDATION` hidden field
   - `ASP.NET_SessionId` cookie
   - These must be extracted from the initial page load and sent with subsequent requests
5. **Search strategy:** If parcel ID search is not available, search by owner name (from FDOR data) and filter results by document type.

---

## Broward County

### URL and Access

- **Original URL:** `https://www.browardclerk.org/Web2/OfficialRecordsSearch/` -- **CONFIRMED 404.** This URL no longer works; it redirects to an error page.
- **Statewide Portal:** Broward's main site now links to `https://www.myfloridacounty.com/official_records/index.html` for "Statewide Official Records" -- this is the Florida Clerks portal operated by the Florida Court Clerks & Comptrollers association.
- **Advanced Search:** Broward has a page at `https://www.browardclerk.org/Web2/Services/AboutAdvancedSearch` which describes their advanced search capabilities (this page returned HTTP 200).
- **Case Search:** The general case search is at `https://www.browardclerk.org/Web2` but this is for court cases, not official records (deeds/mortgages).
- **IMPORTANT FINDING:** Broward may have migrated official records search entirely to the statewide `myfloridacounty.com` portal.

### Statewide Portal (myfloridacounty.com) [NEEDS VERIFICATION]

- URL: `https://www.myfloridacounty.com/official_records/index.html`
- This portal was accessible (HTTP 200 confirmed).
- It typically provides:
  - County selector dropdown (all 67 FL counties)
  - Unified search interface across participating counties
  - Name search (grantor/grantee)
  - Document type filter
  - Date range filter
  - Book/page search
- This could be a major advantage -- one scraper interface for multiple counties.

### Search Fields Available [NEEDS VERIFICATION]

On the statewide portal, expected fields:
- **County** dropdown -- select Broward (or Palm Beach, or any participating county)
- **Party Name** -- last name, first name
- **Party Type** -- grantor, grantee, or both
- **Document Type** -- dropdown or multi-select with categories like:
  - DEED, MORTGAGE (MTG), SATISFACTION OF MORTGAGE (SAT/MTG), ASSIGNMENT OF MORTGAGE (ASMT/MTG)
  - LIS PENDENS, LIEN, JUDGMENT, RELEASE, SUBORDINATION
  - Many more document type codes
- **Date Range** -- from/to recording dates
- **Instrument Number** -- county-specific document ID
- **Book/Page** -- official record book and page

On Broward's own Advanced Search (if still active for official records):
- May require a premium subscription for some features
- The "AboutAdvancedSearch" page likely describes what's available and pricing

### Results Format [NEEDS VERIFICATION]

Typical statewide portal results:
- Tabular list of matching documents
- Columns: recording date, document type, book/page, party names, consideration/amount
- Click-through to document detail with full party list and legal description
- Document image viewing (may require per-page fee or subscription)

### Anti-Bot Measures

**LIKELY MODERATE:**
- The statewide portal (`myfloridacounty.com`) responded to a standard curl request with HTTP 200, which is a positive sign -- no TLS fingerprinting was detected.
- Broward's own site (`browardclerk.org`) also responded to curl requests normally for the pages that exist.
- Expected measures:
  - Session-based access (cookies required)
  - Possible CAPTCHA after N searches [NEEDS VERIFICATION]
  - Rate limiting (requests per minute threshold)
  - Terms of service restrictions on automated access
  - Possible IP-based throttling

### Recommended Scraping Approach

1. **Start with myfloridacounty.com** -- Since it responds to curl, a Python `requests`-based scraper may work here without needing Selenium. This is much simpler to build and maintain.
2. **Session management:** Start a session, load the search page, extract any hidden form fields, then submit searches.
3. **Rate limiting:** 1 request per 2 seconds, with exponential backoff on errors.
4. **If requests-based approach fails**, fall back to Playwright/Selenium.
5. **Bonus:** If the statewide portal works for Broward, it likely works for Palm Beach too -- potentially bypassing PBC's TLS fingerprinting entirely.

---

## Comparison & Recommendation

### Which is easier to scrape?

**Broward (via myfloridacounty.com) is significantly easier.** Here is the comparison:

| Factor | Palm Beach (direct) | Broward / Statewide Portal |
|--------|--------------------|-----------------------------|
| TLS fingerprinting | YES -- blocks curl and requests | NOT detected -- curl returns 200 |
| Requires Selenium | Almost certainly | Possibly not (try requests first) |
| ASP.NET ViewState | Likely | Possibly (depends on portal tech) |
| URL still works | Yes (but connection blocked) | Original URL is 404; statewide portal works |
| Multi-county potential | PBC only | All 67 FL counties |

**Recommendation: Build against `myfloridacounty.com` first.**
- If the statewide portal covers both Palm Beach and Broward official records, we get a single scraper for both counties (and potentially all 67 FL counties for future expansion).
- The statewide portal is more likely to be scrapable with simple `requests` (no browser automation needed).
- Fall back to PBC's direct portal only if the statewide portal doesn't include PBC or lacks needed fields.

### Estimated Implementation Complexity

| Approach | Complexity | Time Estimate | Dependencies |
|----------|-----------|---------------|-------------|
| myfloridacounty.com with `requests` | Low-Medium | 2-3 days | requests, beautifulsoup4 |
| myfloridacounty.com with Selenium | Medium | 3-4 days | selenium or playwright |
| PBC direct with Selenium | High | 4-6 days | playwright + undetected-chromedriver |
| PBC direct with TLS spoofing | Medium-High | 3-5 days | curl_cffi or tls_client |

### Key Risks

1. **Parcel ID search may not be available.** If official records can only be searched by party name (not parcel/folio number), we must search by owner name from FDOR data. This creates ambiguity -- common names will return many unrelated results that must be filtered by address or legal description.

2. **Mortgage amount may not be in the index.** Some county clerk systems only show the amount in the actual document image (scanned PDF), not in the searchable index fields. If this is the case, we can still get lender name and recording date from the index, but extracting loan amounts would require OCR on document images -- dramatically increasing complexity.

3. **PBC's TLS fingerprinting may evolve.** Even if we bypass it today with Playwright, they may add additional measures (CAPTCHA, behavioral analysis). This is a cat-and-mouse risk.

4. **Statewide portal coverage.** We need to verify that both Palm Beach and Broward participate in the statewide portal and that the data is current and complete. Some counties may have limited date ranges available online.

5. **Terms of service.** Both portals likely have ToS prohibiting automated scraping. While the data is public record, automated bulk access may trigger IP bans or legal notices. Running at low volume (our 25-lead POC) mitigates this risk.

6. **Rate of data retrieval.** At 1 request per 2 seconds, and assuming ~3 requests per property (search + pagination + detail), processing 25 leads with ~5 properties each = ~375 requests = ~12 minutes. Manageable for POC. At full county scale (7,500+ leads), this could take days of continuous running.

---

## Next Steps (Recommended)

1. **Manual browser visit** to both portals to verify search fields, document types, and parcel ID search availability:
   - `https://applications.mypalmbeachclerk.com/ORIPublicAccess/`
   - `https://www.myfloridacounty.com/official_records/index.html` (select Broward, then Palm Beach)
   - Take screenshots of search forms and results pages
   - Note all form field names/IDs (inspect element)
   - Try a test search by owner name and by parcel ID if available

2. **Check myfloridacounty.com** -- Does it cover both PBC and Broward? What search fields does it offer? If it has parcel search and shows mortgage amounts in results, this is the clear winner.

3. **Test a simple Python requests script** against `myfloridacounty.com`:
   ```python
   import requests
   session = requests.Session()
   resp = session.get("https://www.myfloridacounty.com/official_records/index.html")
   print(resp.status_code)  # If 200, requests-based approach is viable
   ```

4. **Document the HTML structure** after manual inspection -- form action URLs, field names, hidden inputs, result table structure. This becomes the spec for building `11_county_clerk.py`.

---

## Alternative Data Sources (If Scraping Fails)

If county clerk portal scraping proves infeasible due to anti-bot measures:

1. **Bulk data request** -- Contact PBC and Broward clerk offices directly. Many counties sell bulk data exports of official records indexes for a modest fee ($50-$500). This would be the most reliable approach.

2. **FDOR mortgage data** -- The FDOR NAL file contains `MTG_CD` (mortgage code) fields that indicate whether a property has a mortgage. Limited but free.

3. **ATTOM Data / CoreLogic / Black Knight** -- Commercial data providers that aggregate county recorder data. Expensive ($500-$2,000/mo) but comprehensive.

4. **PropertyShark / PropertyRadar** -- Mid-tier commercial options with API access to mortgage data.

5. **County GIS portals** -- Some county property appraiser GIS systems show mortgage/lien data. Palm Beach County Property Appraiser (`pbcgov.org/papa`) may have some mortgage information.
