
Zack Lewis <zack@zackthewriter.com>
8:09 PM (0 minutes ago)
to me

Here's a comprehensive breakdown of every repo and codebase I found relevant to your gaps, organized by priority:

---

## 🔴 Priority 1 & 2: County Clerk Portals (Lender Names, Lis Pendens, Liens, Divorce/Probate)

This is the biggest unlock. I found **three directly relevant repos**, including one that has *already solved your exact problem* for PBC.

---

### ⭐⭐⭐ BEST FIND — PBC Clerk + 2Captcha: `hamza-140/scrapy-projects`

This is the closest thing to a working solution for your specific blocker. It targets **`erec.mypalmbeachclerk.com` directly**, uses **2Captcha to solve the reCAPTCHA**, POSTs to the exact `/Search/DocumentTypeSearch` endpoint you've been hitting, and passes the session cookies into a Scrapy pipeline to call `/Search/GetSearchResults`.

```python name=tankterminals_scraper/spiders/clerk.py url=https://github.com/hamza-140/scrapy-projects/blob/108b5d63b51787842eb3c9cbc8b94b259e992447/tankterminals_scraper/tankterminals_scraper/spiders/clerk.py#L1-L70
import scrapy
import requests
from twocaptcha import TwoCaptcha

class ClerkSpider(scrapy.Spider):
    name = "clerk"
    def start_requests(self):
        # STEP 1: Solve captcha via 2Captcha
        solver = TwoCaptcha("YOUR_API_KEY")
        result = solver.recaptcha(
            sitekey="6Lc9yBsUAAAAAL-kDRIczjkDHgSbDLAWtl2zewcx",  # PBC sitekey
            url="https://erec.mypalmbeachclerk.com/search/index?..."
        )
        captcha_token = result["code"]

        # STEP 2: POST to DocumentTypeSearch with token
        s = requests.Session()
        form_data = {
            'doctype': '20',  # doc type 20 = Lis Pendens in PBC
            'beginDate': '08/11/2025',
            'endDate': '08/12/2025',
            'g-recaptcha-response': captcha_token,
        }
        s.post("https://erec.mypalmbeachclerk.com/Search/DocumentTypeSearch", ...)
       
        # STEP 3: Forward cookies into Scrapy, call GetSearchResults
        yield scrapy.FormRequest(url='https://erec.mypalmbeachclerk.com/Search/GetSearchResults', ...)
```

🔑 **Key details:**
- The PBC reCAPTCHA sitekey `6Lc9yBsUAAAAAL-kDRIczjkDHgSbDLAWtl2zewcx` is hardcoded — confirms it's targeting your exact portal
- `doctype: '20'` = Lis Pendens. Change to the MTG doc type code to pull **mortgages/lender names**
- Repo: [hamza-140/scrapy-projects](https://github.com/hamza-140/scrapy-projects)
- The `test.py` file in the same repo also shows a Selenium approach for PBC
- **2Captcha cost**: ~$1–3 per 1,000 solves → 500 leads × ~3 searches = ~$1.50 total

---

### ⭐⭐ Broward AcclaimWeb Scraper: `Angelsantiago-lopez23/DHS-Project-ACDC`

This repo directly targets `officialrecords.broward.org/AcclaimWeb` with Selenium, doing a full **name search**, paginating results, and exporting to Excel. It extracts doc type, parties, record date, book/page, instrument #, and consideration — exactly the fields you need for lender extraction.

```python name=tester/Broward_County/broward_county_part2.py url=https://github.com/Angelsantiago-lopez23/DHS-Project-ACDC/blob/4b9828bbab167f166f54e61121e69f0a50cb5bf8/tester/Broward_County/broward_county_part2.py#L94-L167
# Reads names from input.xlsx, searches each name on Broward AcclaimWeb,
# paginates all results, and exports: Party, DocType, Book/Page, Consideration, etc.
def main():
    for target_name in names:
        driver = driver_initialization()
        website_target(driver, 'https://officialrecords.broward.org/AcclaimWeb/search/Disclaimer?...')
        conditions_then_searchboxperson(driver, target_name)
        all_data = multiple_pages(driver)
        data_to_excel(all_data, f"{target_name}_output.xlsx")
```

- Repo: [Angelsantiago-lopez23/DHS-Project-ACDC](https://github.com/Angelsantiago-lopez23/DHS-Project-ACDC)
- ⚠️ Uses standard Selenium — may be Cloudflare-blocked. Look for the `driver_initialization()` function to see if they handle the CF challenge. You may need to swap in `undetected-chromedriver` or add Playwright with stealth.

---

### ⭐⭐ Broward Playwright Scraper: `gSimani/ConcordBroker`

This repo has two highly relevant files:

1. **`apps/workers/official_records/scraper.py`** — A full async Playwright scraper for Broward AcclaimWeb that searches by doc type (WARRANTY DEED, MORTGAGE, ASSIGNMENT OF MORTGAGE, etc.), date range, and extracts `mortgage_amount` as a dataclass field
2. **`download_all_florida_data.py`** — Shows the three Broward search endpoint URLs and also downloads SunBiz SFTP data (liens, fictitious names) — highly relevant

```python name=apps/workers/official_records/scraper.py url=https://github.com/gSimani/ConcordBroker/blob/50e6c3ea9f1792638ba481d0956dbeabc0d4cafe/apps/workers/official_records/scraper.py#L1-L116
@dataclass
class PropertyTransfer:
    mortgage_amount: Optional[float]  # ← what you need
    grantor: str   # seller
    grantee: str   # buyer
    doc_type: str  # MORTGAGE, WARRANTY DEED, etc.

class OfficialRecordsScraper:
    BASE_URL = "https://officialrecords.broward.org/AcclaimWeb"
    SEARCH_URL = f"{BASE_URL}/search/SearchTypeDocType"
    # Uses Playwright with headless=True, --disable-blink-features=AutomationControlled
```

- Repo: [gSimani/ConcordBroker](https://github.com/gSimani/ConcordBroker)

---

### ⭐⭐ Lis Pendens + Broward/Miami-Dade Scraper: `dlogozz0/tax-deed-ai`

Has an `async httpx` scraper for **both Broward and Miami-Dade lis pendens** with a clean `_scrape_broward_lis_pendens()` function. Good reference for the Broward AcclaimWeb API endpoints and the exact parameter names (`DocTypeName`, `StartDate`, `EndDate`).

```python name=backend/app/integrations/clerk_scraping.py url=https://github.com/dlogozz0/tax-deed-ai/blob/e296e56149a67e411d9c60d543e98973dba81083/backend/app/integrations/clerk_scraping.py#L50-L142
# Broward lis pendens via AcclaimWeb
search_url = "https://officialrecords.browardclerk.org/AcclaimWeb/search/SearchTypeDocType"
params = {
    "DocTypeName": "LIS PENDENS",
    "StartDate": start_date.strftime("%m/%d/%Y"),
    "EndDate": end_date.strftime("%m/%d/%Y"),
}
```

- Repo: [dlogozz0/tax-deed-ai](https://github.com/dlogozz0/tax-deed-ai)

---

### ⭐⭐ PBC Showcase/Court Case Scraper: `davidkarpay/ShowMyCase`

Targets `jiswebprod.mypalmbeachclerk.com/ShowCaseWebSSO` — the PBC **court case** system (divorce, probate, civil). Has both Playwright and Selenium versions. Requires login credentials (it's behind a login wall, not just CAPTCHA), but shows the full workflow for case lookup. Directly relevant to your Gap #8 (divorce/probate).

- Repo: [davidkarpay/ShowMyCase](https://github.com/davidkarpay/ShowMyCase)

---

### ⭐ Florida Foreclosure Source Map: `breverdbidder/zonewise-agents`

A production-ready `source_map.py` that maps every Florida county to its foreclosure portal, tax deed portal, and PA GIS API. Includes the PBC GIS endpoint for parcel lookups. Good for wiring up county-level routing in your pipeline.

- Repo: [breverdbidder/zonewise-agents](https://github.com/breverdbidder/zonewise-agents)

---

## 🟡 Priority 1 Alternative: ATTOM Data API (Paid, No Scraping)

If you want to bypass the clerk portal problem entirely via a paid API:

| Resource | Link | Notes |
|---|---|---|
| Official ATTOM sample code | [AttomDataSolutions/Sample_Code](https://github.com/AttomDataSolutions/Sample_Code) | Python + other languages, property detail endpoint |
| Unofficial Python client | [johncoleman83/attom_python_client](https://github.com/johncoleman83/attom_python_client) | Template client, easy to extend for mortgage endpoints |
| ATTOM API Docs | [api.developer.attomdata.com/docs](https://api.developer.attomdata.com/docs) | Has `/property/mortgage` — returns lender name, amount, date, lien position |
| Buyers Agent MCP | [DuneRaccoon/buyers-agent-mcp](https://github.com/DuneRaccoon/buyers-agent-mcp) | Shows ATTOM + HouseCanary + FirstStreet in a real RE pipeline |

ATTOM has a **free trial tier** and the mortgage endpoint returns lender name, loan amount, loan type, and recording date — exactly Gap #1.

---

## 🟡 Priority 3: Better Contact Data (Phone/Email)

### ThatsThem Scraper: `RetroPackets/Fugitive` + `Sechorda/secOS`

Two repos with working ThatsThem scrapers:

- **[RetroPackets/Fugitive](https://github.com/RetroPackets/Fugitive)** (`src/Xurma-Dox/src/xurma-dox-email.py`): Uses `cloudscraper` with session cookies to hit `thatsthem.com/email/{email}` and extract phones, names, addresses
- **[Sechorda/secOS](https://github.com/Sechorda/secOS)** (`OSINT/osint.py`): Has a `PhoneSearch` class that hits `thatsthem.com/phone/{phone_number}` with **proxy rotation** to avoid rate limits — exactly what you'd need at 500-lead scale

```python name=OSINT/osint.py url=https://github.com/Sechorda/secOS/blob/d45e8ed6917831ff8d31278087e11cbe2fac0522/OSINT/osint.py#L35-L108
class PhoneSearch:
    def search_by_phone(self, phone_number: str) -> Dict[str, Any]:
        url = f"https://thatsthem.com/phone/{phone_number}"
        for proxy in self.proxies:  # rotates proxies from proxyscrape API
            response = self.scraper.get(url, proxies={"http": proxy}, timeout=10)
            if "Limit Reached" in response.text:
                continue  # try next proxy
            return self._extract_phone_records(response.text)
```

### TruePeopleSearch Scraper: `a-a-ronc/Automated-Homeowner-Offer`

This repo is extremely close to your exact use case — it's literally a homeowner lead gen pipeline that enriches county parcel data with contacts via **TruePeopleSearch**, achieving a **40–60% email hit rate**. It even warns about the same rate limit / ToS issues you'll face and recommends batches of 50/hour.

- Repo: [a-a-ronc/Automated-Homeowner-Offer](https://github.com/a-a-ronc/Automated-Homeowner-Offer)

---

## 🟠 Priority 4: RE Agent Data (Redfin/Zillow)

The best lead here is [`ipJoseph/myDREAMS`](https://github.com/ipJoseph/myDREAMS) — it has a property dashboard with full MLS field coverage including `buyer_agent_name`, `buyer_office_name`, `listing_agent_name`, `listing_agent_id` etc., stored from an MLS/Spark API integration. It's not a scraper per se but shows the data model and MLS API wiring.

For actual Redfin/Zillow scraping, the code search results were noisy — your best bet is to search GitHub directly with:
```
redfin sold listing scraper buyer agent language:python pushed:>2025-01-01
```

---

## 🟠 Priority 5: STR / Airbnb Revenue

### `jcherranz/lombok-intel` + `pyairbnb`

This is a production STR market intelligence pipeline that uses the **`pyairbnb` library** (Airbnb GraphQL v3 API wrapper) to collect listings, ADR, occupancy rates, and RevPAR by zone. The PRD explicitly calls out DSCR calculations, which is your exact use case.

- Repo: [jcherranz/lombok-intel](https://github.com/jcherranz/lombok-intel)
- Key library: **`pyairbnb`** on PyPI — pulls calendar data from Airbnb's unofficial GraphQL API without paying AirDNA $500/mo
- Also see: [Zdziszkee/PricePOL](https://github.com/Zdziszkee/PricePOL) which explicitly plans Airbnb calendar scraping for occupancy/revenue estimation

---

## Summary Action Plan

| Priority | Gap | Repo to Use | Effort |
|---|---|---|---|
| **1** | Lender names (PBC) | `hamza-140/scrapy-projects` + 2Captcha | ~2 hrs to adapt + $1.50 in CAPTCHA credits |
| **1** | Lender names (Broward) | `gSimani/ConcordBroker` Playwright scraper | ~2 hrs, may need undetected-chromium |
| **2** | Lis pendens (PBC) | Same `hamza-140` repo — change `doctype` to `LP` code | Already solved if #1 works |
| **2** | Lis pendens (Broward) | `dlogozz0/tax-deed-ai` httpx scraper | 1 hr to adapt |
| **3** | Better contact data | `a-a-ronc/Automated-Homeowner-Offer` (TPS) + `Sechorda/secOS` (ThatsThem) | 1–2 hrs |
| **4** | RE agents | ATTOM API `/property/detail` has agent data | Paid API, free trial available |
| **5** | STR revenue | `jcherranz/lombok-intel` + `pyairbnb` | 1–2 hrs to stand up |
| **8** | Divorce/probate | `davidkarpay/ShowMyCase` (PBC court scraper) | Requires PBC login credentials |

**The single most important insight:** The `hamza-140/scrapy-projects` repo has literally already solved your Gap #1 blocker — it handles the PBC reCAPTCHA using 2Captcha and posts to the exact same endpoints your script 11 has been failing on. Integrate that CAPTCHA-solving pattern into your existing `11_county_clerk.py` and you unblock lender names, lis pendens, liens, and judgments simultaneously for under $5.

> **Note:** Search results here may be incomplete — GitHub code search returns up to 10 results per query. You can explore further at these links: [PBC clerk search](https://github.com/search?q=mypalmbeachclerk+language%3Apython&type=code), [Broward AcclaimWeb search](https://github.com/search?q=officialrecords.broward.org+language%3Apython&type=code), [TruePeopleSearch scrapers](https://github.com/search?q=truepeoplesearch+scraper+python&type=code).