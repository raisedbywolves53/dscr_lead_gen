# Florida Deployment Configuration

## Property Records

### FDOR NAL Files (Primary Source)
- **Source:** Florida Department of Revenue
- **URL:** https://floridarevenue.com/property/Pages/DataPortal_RequestAssessmentRollGISData.aspx
- **Access:** Email PTOTechnology@floridarevenue.com to request
- **Format:** CSV (fixed-width origin), one ZIP per county
- **Cost:** Free
- **Frequency:** Annual (January)
- **Size:** ~343MB per major county (654K parcels for Palm Beach)

### FDOR SDF Files (Sales History)
- **Source:** Same portal as NAL
- **Format:** CSV with purchase/sale history
- **Cost:** Free

### Key FDOR Columns
| Our Field | FDOR Column | Notes |
|-----------|-------------|-------|
| Owner name | OWN_NAME | Format: "LAST FIRST MIDDLE" |
| Mailing address | OWN_ADDR1 | |
| Mailing state | OWN_STATE_DOM | 2-letter code (NOT OWN_STATE) |
| Property address | PHY_ADDR1 | |
| Assessed value | JV | Just Value |
| Homestead | AV_HMSTD | Non-zero = homesteaded |
| Use code | DOR_UC | See use codes below |
| Sale price | SALE_PRC1 | Most recent sale only |
| Sale year | SALE_YR1 | Most recent sale only |
| County | CO_NO | 2-digit code |

### County Codes (Target Markets)
| Code | County | FIPS |
|------|--------|------|
| 60 | Palm Beach | 099 |
| 16 (or 06) | Broward | 011 |
| 23 | Miami-Dade | 086 |
| 58 | Orange (Orlando) | 095 |
| 39 | Hillsborough (Tampa) | 057 |
| 26 | Duval (Jacksonville) | 031 |
| 62 | Pinellas (St. Pete) | 103 |

### Property Use Codes (FDOR DOR_UC)
| Code | Description | Include? |
|------|-------------|---------|
| 01 | Single Family Residential | Yes |
| 02 | Mobile Home | Yes |
| 03 | Multi-Family (2-9 units) | Yes |
| 04 | Condominium | Yes |
| 05 | Cooperatives | Yes |
| 08 | Multi-Family (10+ units) | Yes |
| 10-39 | Vacant Land | No |
| 48 | Warehouse | No |

### Homestead Detection
- `AV_HMSTD > 0` = homesteaded (primary residence) → exclude
- `AV_HMSTD = 0` or blank = non-homesteaded (investment property) → include

---

## Entity Registry

### SunBiz (FL Division of Corporations)
- **URL:** https://search.sunbiz.org
- **Search:** POST to `/Inquiry/CorporationSearch/ByName`
- **Bulk data:** FTP at dos.fl.gov/sunbiz/other-services/data-downloads/
  - Username: `Public`, Password: `PubAccess1845!`
  - Quarterly full dumps (3.5M+ entities), daily incrementals
- **Cost:** Free
- **Rate limit:** 1 request per 3 seconds (Cloudflare protected)
- **Returns:** Entity name, officers (up to 6), registered agent, filing date, status, FEIN

### Known Issues
- Cloudflare blocks aggressive scraping → use session cookies + delays
- Bulk FTP only has up to 6 officers per entity
- Selenium also blocked (headless detection)

---

## STR / Vacation Rental Licensing

### DBPR (FL Dept. of Business & Professional Regulation)
- **URL:** https://www.myfloridalicense.com
- **Bulk download:** https://www2.myfloridalicense.com/instant-public-records/
- **Format:** Weekly CSV of all active/inactive licensees
- **Cost:** Free
- **License type:** "Vacation Rental" (search DBPR)
- **Returns:** Licensee name, address, phone, email, license status
- **Match rate:** ~70-80% via fuzzy address matching to property records

---

## County Clerk / Register of Deeds

### Palm Beach County Clerk
- **URL:** https://erec.mypalmbeachclerk.com
- **System:** Landmark Web
- **Access:** Google reCAPTCHA required on every search
- **Workaround:** 2Captcha integration ($3-5 per 1,500 solves)
- **FTP subscription:** $600/year or $50/month for bulk index data
- **Records from:** January 1968 to present

### Broward County Clerk
- **URL:** https://officialrecords.broward.org/AcclaimWeb
- **System:** AcclaimWeb
- **Access:** Cloudflare challenge page (blocks curl_cffi)
- **FTP bulk data:** FREE (10 rolling days of index + images)
- **Records from:** 1978 forward

### What Clerk Records Provide
- Mortgage recordings (lender, amount, date)
- Deed recordings (buyer, seller, consideration)
- Liens, lis pendens, satisfactions, assignments
- Divorce filings, probate, judgments

---

## STR-Eligible Zip Codes (Tourist Markets)

### Orlando Metro
32801, 32803, 32804, 32806, 32807, 32808, 32809, 32812, 32819, 32821, 32822, 32824, 32827, 32828, 32829, 32830, 32836, 32837, 34711, 34714, 34747, 34786, 34787

### Miami / Fort Lauderdale
33101, 33109, 33132, 33133, 33137, 33139, 33140, 33141, 33154, 33160, 33180, 33304, 33305, 33308, 33316, 33334, 33019, 33020

### Florida Keys
33036, 33037, 33040, 33042, 33043, 33050, 33051, 33070

### Gulf Coast (Sarasota / Naples / Fort Myers / Destin)
34102, 34103, 34108, 34109, 34110, 34112, 34119, 34201, 34228, 34229, 34230, 34231, 34236, 34237, 34238, 34239, 34242, 33901, 33908, 33919, 33928, 33931, 33957, 32541, 32550, 32459

### Jacksonville / St. Augustine
32082, 32084, 32233, 32250, 32266

### Tampa / St. Pete / Clearwater
33701-33716, 33762-33776, 33785, 33786

---

## Florida Compliance

### Telemarketing License
- **FDACS (FL Dept. of Agriculture):** $1,500/year
- **Salesperson license:** $50/year per person
- **Surety bond:** $50,000 face value (~$500-1,500 premium)
- **Background check:** ~$50-75 per person (fingerprint)

### Florida-Specific Calling Rules
| Rule | Florida | Federal |
|------|---------|---------|
| Calling hours | **8 AM – 8 PM local** | 8 AM – 9 PM |
| Call frequency | **Max 3 per 24 hours** | No limit |
| Caller ID | Must display accurate # (criminal penalty) | Spoofing prohibited |
| B2B calls | **Florida rules apply** | More lenient |
| State DNC | Separate list (FDACS, quarterly) | Federal only |
| STOP reply (texts) | 15-day safe harbor after STOP | Immediate |

### DNC Area Codes (FL)
Primary: 561 (Palm Beach), 954 (Broward), 305 (Miami), 786 (Miami)
All FL: 239, 321, 352, 386, 407, 561, 689, 727, 754, 772, 786, 813, 850, 863, 904, 941, 954

---

## Data Quirks & Gotchas

- FDOR names are "LAST FIRST" — parse as `parts[0]` = last, `parts[1]` = first
- Use `OWN_STATE_DOM` for 2-letter state codes (not `OWN_STATE`)
- Entity names (LLC/Corp/Trust) → blank first/last for skip trace
- Strip trailing "&" from joint ownership names
- FDOR `SALE_YR1`/`SALE_PRC1` reflects most recent sale only (not full history)
- Equity ratio is estimated (JV vs sale price) — no mortgage balance from FDOR
- Miami-Dade county code: "23" (not "13" — that's DeSoto)
- Always load FDOR CSVs with `dtype=str` — booleans are stored as strings
- NAL files are ~343MB — MUST use chunked processing (50K rows) to avoid OOM
