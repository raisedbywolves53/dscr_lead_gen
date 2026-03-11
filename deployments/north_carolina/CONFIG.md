# North Carolina Deployment Configuration

## Status: RESEARCH COMPLETE — NOT YET DEPLOYED

---

## Property Records

### NC OneMap Statewide Parcels (Primary Source — FL FDOR Equivalent)
- **URL:** https://www.nconemap.gov/
- **Hub:** https://experience.arcgis.com/experience/268c396eb28b445b9a188e2097429c5d
- **Data dictionary:** https://assets.nconemap.gov/pages/hub/ncom-parcels-dd.htm
- **Format:** CSV, GeoJSON, Shapefile, File Geodatabase
- **Cost:** Free
- **Coverage:** Statewide (all 100 counties), standardized parcel data
- **API:** GeoServices, WMS, WFS endpoints
- **Fields:** Owner name, mailing address, property address, acreage, assessed value
- **Investment property detection:** Mailing address ≠ property address (primary signal)

### Wake County (Raleigh) — Detailed Data
- **URL:** https://taxhelp.wake.gov/hc/en-us/articles/42592272930452-Real-Estate-Property-Data-Files
- **Format:** XLSX and fixed-width text (with record layout docs)
- **Cost:** Free
- **Refresh:** Daily
- **Fields:** Ownership, sale information, property details for all parcels
- **GIS:** https://data-wake.opendata.arcgis.com/
- **Property lookup:** https://maps.raleighnc.gov/iMAPS/

### Mecklenburg County (Charlotte) — Detailed Data
- **URL:** https://gis.mecknc.gov/data-center
- **POLARIS 3G:** https://polaris3g.mecklenburgcountync.gov (80+ mapping overlays)
- **Open Data:** https://data.charlottenc.gov/datasets/charlotte::parcel-look-up/about
- **Format:** Various GIS formats
- **Cost:** Free (standard downloads)

---

## Entity Registry

### NC Secretary of State Business Search
- **URL:** https://www.sosnc.gov/online_services/search/by_title/_Business_Registration
- **Search by:** Business name, SOS ID, registered agent, company officials
- **Cost:** Free (individual searches)
- **Returns:** Entity name, type, registration date, status, registered agent, officers/directors, principal office
- **Bulk download:** NOT available publicly
- **Bulk subscription:** Available via https://www.sosnc.gov/online_services/data_subscriptions
  - Contact: subscriptions@sosnc.gov for pricing
  - Two types: Business Registration and UCC/Notary
- **Scraping:** EXPLICITLY PROHIBITED per TOS
- **Comparison to FL SunBiz:** Same data fields, but no free bulk access and no scraping allowed

### Adaptation Required
Unlike Florida where we scrape SunBiz freely, NC requires either:
1. **Paid data subscription** from NC SoS (recommended for production)
2. **Manual lookups** with significant delays (risky TOS-wise)
3. **Alternative:** Skip entity resolution initially, rely on owner name parsing

---

## STR / Vacation Rental Licensing

### No State-Level Registry
NC has **no equivalent to Florida's DBPR** vacation rental database. This is the biggest gap.

### State Requirements
- Operators renting 15+ days/year must register with NC Department of Revenue
- Must collect 6.75% state sales tax + local occupancy taxes
- No centralized searchable database

### Raleigh (Wake County)
- **URL:** https://raleighnc.gov/permits/services/short-term-rentals
- Requires zoning permit ($194 initial, $86 annual renewal)
- Permitted in specific zoning districts: R-1, R-2, R-4, R-6, R-10, RX, OX, NX, CX, DX
- May have permit database (unclear if publicly searchable)

### Charlotte (Mecklenburg County)
- **URL:** https://rentalregistration.charlottenc.gov/
- Very permissive — removed STR-specific regulations in April 2022
- Voluntary rental registry (free) via Charlotte-Mecklenburg Police
- Business license required from City of Charlotte

### Workaround
- Use proxy signals: mailing address mismatch + LLC ownership in tourist zips
- FOIA individual city permit records if needed
- Consider AirDNA ($500+/mo) for STR identification at scale

---

## County Register of Deeds (FL Clerk Equivalent)

### Wake County Register of Deeds
- **URL:** https://www.wake.gov/departments-government/register-deeds/search-real-estate-records
- **Search portal:** https://rodcrpi.wakegov.com/booksweb/genextsearch.aspx
- **Records:** Deeds, deeds of trust (mortgages), powers of attorney, maps/plats
- **Search by:** Grantor/grantee name, document type, recording date
- **Cost:** Free to search, per-page fees for certified copies
- **Alert service:** https://docalert.wakegov.com/
- **Contact:** 919-856-5460

### Mecklenburg County Register of Deeds
- **URL:** https://deeds.mecknc.gov/services/real-estate-records
- **Search portals:**
  - Primary: https://deeds.mecknc.gov
  - Alternative: https://meckrod.manatron.com/
  - Historical (1763-1990): https://www.meckrodhistorical.com/
- **Records from:** March 1990 to present (online)
- **Cost:** Free to search online
- **Contact:** 704-336-2443, ROD@MecklenburgCountyNC.gov

### Scraping Assessment
Both counties use form-based search interfaces. Scraping feasibility depends on anti-bot measures — needs testing. Similar challenge to FL clerk portals.

---

## Homestead / Owner-Occupied Detection

### NC Does NOT Have a Universal Homestead Exemption
- NC "Homestead Exclusion" (G.S. 105-277.1) only applies to:
  - Age 65+ OR totally disabled
  - Income under $38,800
  - Owner-occupant
- **This is NOT a reliable investment property indicator** (unlike FL)

### How to Identify Investment Properties Instead
1. **Mailing address ≠ property address** — PRIMARY signal (absentee owner)
2. **LLC/Corp/Trust ownership** — entity keywords in owner name
3. **Multiple properties under same owner** — portfolio detection
4. **Out-of-state owner** — mailing state ≠ NC
5. **No homestead exclusion** — WEAK signal only (most NC residents also won't have it)

---

## STR-Eligible Zip Codes (NC Tourist Markets)

### Outer Banks
27948 (Nags Head), 27959 (Kill Devil Hills), 27949 (Kitty Hawk), 27954 (Duck), 27927 (Corolla)

### Asheville Area
28801, 28803, 28804, 28805, 28806 (Asheville), 28711 (Black Mountain), 28731 (Flat Rock)

### Charlotte (Urban STR)
28202, 28203, 28204, 28205, 28206 (Uptown/South End/NoDa/Plaza Midwood)

### Raleigh (Urban STR)
27601, 27603, 27604, 27607, 27608 (Downtown, Glenwood South, Five Points)

### Wilmington / Carolina Beach
28401, 28403 (Wilmington), 28428 (Carolina Beach), 28449 (Kure Beach), 28480 (Wrightsville Beach)

### Pinehurst / Southern Pines
28374 (Pinehurst), 28387 (Southern Pines)

---

## NC-Specific Compliance

### Telemarketing
- NC has a state DNC list (NC Attorney General maintains)
- Calling hours: check NC state law (may differ from federal)
- NC does NOT require a state telemarketing license like FL does
- Still subject to federal TCPA, FTC DNC, CAN-SPAM

### Area Codes
Wake County: 919, 984
Mecklenburg County: 704, 980
Additional NC: 252, 336, 743, 828, 910

---

## Key Differences from Florida

| Factor | Florida | North Carolina | Impact |
|--------|---------|---------------|--------|
| Property data | FDOR NAL (statewide, standardized) | NC OneMap (statewide) + county files | Similar — NC OneMap is solid |
| Owner-occupied signal | Homestead exemption (binary, reliable) | No universal equivalent | Harder — rely on mailing address mismatch |
| Entity resolution | SunBiz (free, scrapeable) | NC SoS (no scraping, paid subscription) | Harder — need paid data or alternatives |
| STR registry | DBPR (statewide, 60K+ licenses) | No state registry | Much harder — city-level only |
| Clerk records | County-level portals | County-level portals | Similar difficulty |
| Compliance | Very strict ($1,500 license) | Less strict (no state license) | Easier in NC |
| Data culture | Very open (FL Sunshine Law) | Moderately open | Slightly harder |

---

## Recommended Approach for NC MVP

1. **Start with NC OneMap** statewide parcel data (free, equivalent to FDOR NAL)
2. **Supplement with Wake + Mecklenburg** county downloads for sale prices and details
3. **Skip entity resolution initially** — use owner name parsing + mailing address signals
4. **Skip STR tagging** — no centralized source (use proxy signals from scoring)
5. **Run Tracerfy skip trace** as normal (nationwide, no state-specific changes)
6. **Test clerk portals** for Wake + Mecklenburg mortgage records
7. **Once validated:** Investigate NC SoS paid data subscription for entity resolution
