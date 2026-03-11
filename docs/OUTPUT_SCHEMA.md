# Output Schema — Canonical Column Definitions

## Master Lead Record

The pilot_500_master.csv contains 157 columns. This is the canonical reference for all output files.

---

## Identification

| Column | Type | Description |
|--------|------|-------------|
| OWN_NAME | string | Property owner name (person or entity) |
| resolved_person | string | Human name behind entity (from SoS resolution) |
| is_entity | bool | Owner name contains LLC/Corp/Trust keywords |
| out_of_state | bool | Mailing state ≠ property state |
| foreign_owner | bool | Non-U.S. domicile |
| OWN_ADDR1 | string | Owner mailing address |
| OWN_CITY | string | Mailing city |
| OWN_STATE | string | Mailing state |
| OWN_ZIPCD | string | Mailing zip |
| OWN_STATE_DOM | string | 2-letter domicile state code |

## Classification & Scoring

| Column | Type | Description |
|--------|------|-------------|
| _icp | string | Primary ICP segment |
| _score | int | Lead quality score (0-100) |
| _is_brrrr | bool | BRRRR strategy candidate |
| _is_cash_buyer | bool | Probable all-cash buyer |
| _is_equity_harvest | bool | Equity harvest candidate |
| _is_rate_refi | bool | Rate refi candidate |
| _has_refi | bool | Any refi signal present |

## Portfolio

| Column | Type | Description |
|--------|------|-------------|
| property_count | int | Number of investment properties |
| total_portfolio_value | float | Sum of assessed values |
| avg_property_value | float | Average value per property |
| most_recent_price | float | Price of most recent purchase |
| avg_sale_price | float | Average purchase price |
| most_recent_purchase | date | Date of most recent purchase |
| property_types | string | Use codes (comma-separated) |
| CO_NO | string | County code(s) |

## Refinance Signals

| Column | Type | Description |
|--------|------|-------------|
| days_since_purchase | int | Days since most recent purchase |
| estimated_equity | float | Estimated equity (value - purchase price) |
| equity_ratio | float | Equity as % of value (0.0-1.0) |
| max_cashout_75 | float | Cash available at 75% LTV |
| max_cashout_80 | float | Cash available at 80% LTV |
| refi_signals | string | Pipe-separated detected signals |
| refi_score_boost | int | Points added from refi signals (0-40) |
| refi_priority | string | High / Medium / Low / blank |
| probable_cash_buyer | bool | Equity ratio 90%+ |
| rate_refi_candidate | bool | 2022-2023 vintage financing |
| brrrr_exit_candidate | bool | Below-market purchase <12 months |
| equity_harvest_candidate | bool | 30%+ equity available |
| portfolio_cashout_75 | float | Total cash-out across portfolio at 75% LTV |

## Entity Resolution

| Column | Type | Description |
|--------|------|-------------|
| registered_agent | string | SoS registered agent name |
| entity_officers | string | Officers/directors (semicolon-separated) |
| entity_status | string | Active/Inactive/Dissolved |
| entity_count | int | Number of entities controlled by same person |
| str_licensed | bool | Has active vacation rental license |
| str_license_count | int | Number of vacation rental licenses |

## Contact Information

| Column | Type | Description |
|--------|------|-------------|
| phone_1 | string | Primary phone number |
| phone_1_source | string | Where phone came from |
| phone_1_type | string | Mobile/Landline/VoIP |
| phone_2 | string | Secondary phone |
| phone_2_source | string | Source |
| phone_2_type | string | Type |
| email_1 | string | Primary email |
| email_1_source | string | Source |
| email_2 | string | Secondary email |
| email_2_source | string | Source |
| enrichment_sources | string | All sources that contributed data |
| contact_name | string | Best name for outreach (resolved_person or parsed owner) |
| str_phone | string | Phone from STR license registry |
| str_email | string | Email from STR license registry |

## Purchase History

| Column | Type | Description |
|--------|------|-------------|
| total_acquisitions | int | Total properties purchased |
| total_dispositions | int | Total properties sold |
| purchases_last_12mo | int | Purchases in last 12 months |
| purchases_last_36mo | int | Purchases in last 36 months |
| avg_purchase_price | float | Average acquisition price |
| most_recent_purchase_date | date | Date of last acquisition |
| flip_count | int | Short-hold (<12mo) transactions |
| hold_count | int | Long-hold transactions |
| avg_hold_period_months | float | Average hold period |
| cash_purchase_pct | float | % of purchases that were cash |
| purchase_frequency_months | float | Average months between purchases |

## Rental & DSCR Estimates

| Column | Type | Description |
|--------|------|-------------|
| est_monthly_rent | float | HUD FMR-based rent estimate |
| est_annual_rent | float | Annual rental income estimate |
| est_noi | float | Estimated net operating income |
| est_monthly_debt_service | float | Estimated monthly payment |
| est_dscr | float | Estimated debt service coverage ratio |
| rent_to_value_ratio | float | Annual rent / property value |

## Financing Intelligence

| Column | Type | Description |
|--------|------|-------------|
| est_loan_type | string | Estimated loan type |
| est_interest_rate | float | Estimated interest rate |
| est_remaining_balance | float | Estimated current balance |
| est_maturity_date | date | Estimated loan maturity |
| est_refi_score | int | Refinance opportunity score |
| best_lender | string | Best known lender name |
| best_lender_type | string | Bank/Credit Union/Hard Money/Private |
| attom_lender_name | string | ATTOM-sourced lender |
| attom_loan_amount | float | ATTOM-sourced loan amount |
| clerk_lender | string | County clerk-sourced lender |

## Wealth Signals

| Column | Type | Description |
|--------|------|-------------|
| fec_total_donated | float | Total political donations |
| fec_donation_count | int | Number of donations |
| fec_recipients | string | Political recipients |
| nonprofit_orgs_found | int | Nonprofit connections found |
| sunbiz_entity_count | int | Number of business entities |
| wealth_signal_score | int | Composite wealth score |

## Apollo.io Fields (Low Value — Included for Completeness)

| Column | Type | Description |
|--------|------|-------------|
| apollo_match | bool | Apollo found a match |
| apollo_email | string | Apollo email (rarely populated) |
| apollo_linkedin | string | LinkedIn URL |
| apollo_title | string | Job title |
| apollo_employer | string | Employer name |

## Output Fields

| Column | Type | Description |
|--------|------|-------------|
| talking_points | string | Generated pitch points based on financing signals |

---

## Data Types & Conventions

- **Booleans** are stored as strings ("True"/"False") in CSV
- **Dates** use "YYYY-MM-DD" format
- **Phone numbers** include country code where available
- **Monetary values** are floats (no currency symbol)
- **Pipe-separated** fields (refi_signals, enrichment_sources) use " | " delimiter
- **Semicolon-separated** fields (entity_officers) use "; " delimiter
