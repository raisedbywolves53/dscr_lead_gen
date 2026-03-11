# Output Schema — Lead Spreadsheet

## File Format
- **Primary:** `.xlsx` (Excel workbook with multiple tabs)
- **Backup:** `.csv` (flat file, single tab)
- **Filename pattern:** `leads_YYYY-MM-DD.xlsx`

## Tab 1: All Leads (Master List)

Every lead in a single flat table, sorted by score descending.

| Column | Type | Source | Description |
|---|---|---|---|
| `lead_id` | String | Generated | Unique ID (county_parcel or entity_id) |
| `score` | Integer (0-100) | Scoring engine | Composite lead quality score |
| `icp_primary` | String | Classification | Primary ICP tag (e.g., "STR Operator", "Serial Investor 10+") |
| `icp_secondary` | String | Classification | Secondary ICP tag if applicable |
| `tier` | Integer (1-3) | Classification | ICP priority tier |
| `owner_name` | String | FDOR NAL / SunBiz | Individual or entity name |
| `owner_type` | String | Derived | "Individual", "LLC", "Corp", "Trust", "Foreign" |
| `resolved_person` | String | SunBiz | If entity-owned: registered agent or officer name |
| `mailing_address` | String | FDOR NAL | Owner's mailing address |
| `mailing_city` | String | FDOR NAL | Mailing city |
| `mailing_state` | String | FDOR NAL | Mailing state |
| `mailing_zip` | String | FDOR NAL | Mailing ZIP |
| `phone` | String | Enrichment | Phone number (if found) |
| `email` | String | Enrichment | Email address (if found) |
| `enrichment_source` | String | Enrichment | Where phone/email came from |
| `property_count` | Integer | Derived | Total FL investment properties owned |
| `total_portfolio_value` | Float | Derived | Sum of just values across all properties |
| `total_estimated_equity` | Float | Derived | Portfolio value minus estimated mortgages |
| `most_recent_purchase` | Date | FDOR SDF | Date of most recent property purchase |
| `most_recent_price` | Float | FDOR SDF | Price of most recent purchase |
| `county` | String | FDOR NAL | Primary county of investment |
| `property_types` | String | Derived | Comma-separated property types owned |
| `str_licensed` | Boolean | DBPR | Has active FL vacation rental license |
| `str_license_count` | Integer | DBPR | Number of active STR licenses |
| `has_homestead_elsewhere` | Boolean | FDOR NAL | Owns a homesteaded property (primary residence) in FL |
| `out_of_state_owner` | Boolean | Derived | Mailing address outside FL |
| `foreign_owner` | Boolean | Derived | Mailing address outside US |
| `entity_count` | Integer | SunBiz | Number of FL entities linked to this person |
| `entity_names` | String | SunBiz | Comma-separated entity names |
| `sec_fund_filing` | Boolean | SEC EDGAR | Has Form D real estate fund filing |
| `fund_name` | String | SEC EDGAR | Fund name if applicable |
| `fund_offering_amount` | Float | SEC EDGAR | Form D offering amount |
| `data_sources` | String | Pipeline | Which sources contributed to this lead |
| `last_updated` | Date | Pipeline | When this record was last refreshed |

## Tab 2: By ICP Segment

Same data as Tab 1, but filtered into separate sections by `icp_primary`:

- Individual Investors (1-10 Properties)
- Serial Investors (10+)
- STR Operators
- Foreign Nationals
- Entity-Based Investors (LLC/Trust)
- Fund Managers / Syndicators
- Self-Employed (flagged via entity + business indicators)
- BRRRR Candidates (flagged via recent below-market purchase)
- Multi-Family Owners (2-4 unit property type)

## Tab 3: Summary Statistics

| Metric | Value |
|---|---|
| Total leads | Count |
| By ICP segment | Count per segment |
| By county | Count per county |
| By tier | Count per tier |
| Average score | Mean score |
| Contact rate | % with phone or email |
| Entity ownership rate | % owned by LLC/Corp/Trust |
| Out-of-state rate | % with non-FL mailing address |
| Foreign owner rate | % with non-US mailing address |
| STR licensed rate | % with active vacation rental license |

## Tab 4: Data Quality

| Field | Coverage | Notes |
|---|---|---|
| Owner name | 100% | From FDOR NAL |
| Mailing address | 100% | From FDOR NAL |
| Phone | Target 40-60% | From enrichment |
| Email | Target 30-50% | From enrichment |
| Property count | 100% | Derived from FDOR |
| Portfolio value | 100% | From FDOR assessed values |
| STR license match | 100% of STR operators | From DBPR cross-reference |
| Entity resolution | Target 80%+ of LLC-owned | From SunBiz cross-reference |

## ICP Classification Rules

```
IF property_count >= 10:
    icp_primary = "Serial Investor (10+)"
    tier = 1

ELIF str_licensed = TRUE:
    icp_primary = "STR Operator"
    tier = 1

ELIF foreign_owner = TRUE:
    icp_primary = "Foreign National"
    tier = 1

ELIF owner_type IN ("LLC", "Corp", "Trust") AND property_count >= 2:
    icp_primary = "Entity-Based Investor"
    tier = 1

ELIF sec_fund_filing = TRUE:
    icp_primary = "Fund Manager / Syndicator"
    tier = 2

ELIF property_count BETWEEN 2 AND 9:
    icp_primary = "Individual Investor (1-10)"
    tier = 1

ELIF most_recent_price < (county_median * 0.7) AND most_recent_purchase > (today - 180 days):
    icp_primary = "BRRRR Candidate"
    tier = 1

ELIF property_type CONTAINS "multi-family" OR "duplex" OR "triplex" OR "fourplex":
    icp_primary = "Multi-Family Investor"
    tier = 2

ELSE:
    icp_primary = "Single Investment Property"
    tier = 3
```

## Scoring Formula

```
score = (
    property_count_score     (0-25 pts: 1 prop=5, 2-4=10, 5-9=15, 10-19=20, 20+=25)
  + recency_score            (0-20 pts: <6mo=20, 6-12mo=15, 1-2yr=10, 2-3yr=5, 3yr+=0)
  + portfolio_value_score    (0-15 pts: <200K=3, 200K-500K=6, 500K-1M=9, 1M-3M=12, 3M+=15)
  + entity_sophistication    (0-10 pts: individual=0, single LLC=5, multiple entities=10)
  + str_indicator            (0-10 pts: no STR=0, STR licensed=10)
  + geographic_fit           (0-10 pts: Palm Beach/Broward/Dade=10, other major metro=7, secondary=5, rural=3)
  + contact_availability     (0-10 pts: phone+email=10, phone only=7, email only=5, address only=2)
)
```

Max score: 100
