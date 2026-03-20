"""
ATTOM 7-Endpoint Showcase Enrichment
=====================================

Calls all 7 ATTOM endpoints for each property belonging to showcase leads.
This is the core enrichment that makes our dossiers unique — no competitor
bundles mortgage, AVM, rental, sales history, assessment, and permits
into a single per-property tear sheet.

7 Endpoints (1 credit each = 7 credits per fully enriched property):
  1. /property/detailmortgageowner   — Lender, loan, rate, maturity, owner
  2. /property/expandedprofile       — Beds, baths, sqft, year, zoning, pool
  3. /attomavm/detail                — AVM estimate, confidence, appreciation
  4. /valuation/rentalavm            — Monthly rent estimate + range
  5. /saleshistory/detail            — 10-year transaction history
  6. /assessment/detail              — Tax assessment, land vs improvement
  7. /property/buildingpermits       — Renovation permits, contractor names

Credit Budget: 210 credits total (30 leads × ~7 properties avg × 7 endpoints).
  Actual usage depends on property count per lead.

Lookup Strategy:
  - FL leads: Address-based lookup (PHY_ADDR1 from pilot_500_master.csv)
    Raw NAL data with parcel IDs is not on this machine.
  - Wake leads: APN + FIPS lookup (parcel_id + county_fips from wake_qualified.csv)

Caching: Per-endpoint JSON cache files — never pay twice for the same lookup.
  Cache key = "{endpoint}|{address}" or "{endpoint}|{fips}:{apn}"

Usage:
    python scripts/attom_7endpoint_showcase.py --market fl
    python scripts/attom_7endpoint_showcase.py --market wake
    python scripts/attom_7endpoint_showcase.py --market fl --dry-run
    python scripts/attom_7endpoint_showcase.py --market fl --leads "OWNER NAME 1,OWNER NAME 2"

After running, use build_dossier_pdf.py to generate tear sheets.
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path

import pandas as pd
import requests

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent
DATA_DIR = PROJECT_DIR / "data"
DEMO_DIR = DATA_DIR / "demo"
CACHE_DIR = DEMO_DIR / "attom_7ep_cache"

# Load .env from scrape/ first, then root
if load_dotenv:
    load_dotenv(PROJECT_DIR / ".env")
    root_env = PROJECT_DIR.parent / ".env"
    if root_env.exists():
        load_dotenv(root_env)

ATTOM_API_KEY = os.getenv("ATTOM_API_KEY", "")

# ---------------------------------------------------------------------------
# ATTOM API Configuration
# ---------------------------------------------------------------------------
ATTOM_BASE = "https://api.gateway.attomdata.com/propertyapi/v1.0.0"
REQUEST_DELAY = 0.5  # seconds between requests (conservative)

# All 7 endpoints with short names for caching and output columns
ENDPOINTS = [
    {
        "name": "mortgage",
        "path": "/property/detailmortgageowner",
        "description": "Mortgage + lender + owner data",
    },
    {
        "name": "profile",
        "path": "/property/expandedprofile",
        "description": "Property characteristics, zoning, census",
    },
    {
        "name": "avm",
        "path": "/attomavm/detail",
        "description": "Automated valuation model (AVM)",
    },
    {
        "name": "rental",
        "path": "/valuation/rentalavm",
        "description": "Rental AVM (monthly rent estimate)",
    },
    {
        "name": "sales",
        "path": "/saleshistory/detail",
        "description": "Sales/transaction history",
    },
    {
        "name": "assessment",
        "path": "/assessment/detail",
        "description": "Tax assessment values",
    },
    {
        "name": "permits",
        "path": "/property/buildingpermits",
        "description": "Building permits and renovation activity",
    },
]

# FIPS codes for target counties
FIPS_CODES = {
    # Florida
    "60": "12099",   # Palm Beach
    "16": "12011",   # Broward
    # North Carolina
    "183": "37183",  # Wake County
}

# ---------------------------------------------------------------------------
# Hard money lender classification (from 16_attom_mortgage.py)
# ---------------------------------------------------------------------------
HARD_MONEY_KEYWORDS = [
    "KIAVI", "LIMA ONE", "CIVIC", "ANCHOR LOANS", "GENESIS",
    "RCLENDING", "GROUNDFLOOR", "FUND THAT FLIP",
    "LENDING HOME", "VISIO", "NEW SILVER", "EASY STREET",
    "COREVEST", "RENOVO", "TEMPLE VIEW", "VELOCITY", "TOORAK",
    "HARD MONEY", "BRIDGE", "FIX AND FLIP", "REHAB",
]


def classify_lender(name: str) -> str:
    """Classify lender into type buckets for dossier."""
    if not name:
        return ""
    upper = name.upper()
    for kw in HARD_MONEY_KEYWORDS:
        if kw in upper:
            return "hard_money"
    for kw in ["CREDIT UNION", "FCU", "FEDERAL CREDIT"]:
        if kw in upper:
            return "credit_union"
    for kw in ["PRIVATE", "INDIVIDUAL"]:
        if kw in upper:
            return "private"
    for kw in ["BANK", "NATIONAL ASSOCIATION", "N.A.", "MORTGAGE",
               "WELLS FARGO", "CHASE", "JPMORGAN", "CITIBANK",
               "REGIONS", "TRUIST", "PNC", "US BANK", "TD BANK",
               "LENDING", "FINANCIAL", "SAVINGS"]:
        if kw in upper:
            return "bank"
    return "other"


# ---------------------------------------------------------------------------
# APN formatting (for APN+FIPS lookups)
# ---------------------------------------------------------------------------
def format_apn_pbc(raw_pcn: str) -> str:
    """Format PBC raw PCN (17 digits) to ATTOM APN format: XX-XX-XX-XX-XX-XXX-XXXX"""
    pcn = raw_pcn.strip().strip('"')
    if len(pcn) >= 17:
        return f"{pcn[0:2]}-{pcn[2:4]}-{pcn[4:6]}-{pcn[6:8]}-{pcn[8:10]}-{pcn[10:13]}-{pcn[13:17]}"
    elif len(pcn) >= 15:
        return f"{pcn[0:2]}-{pcn[2:4]}-{pcn[4:6]}-{pcn[6:8]}-{pcn[8:10]}-{pcn[10:13]}-{pcn[13:]}"
    return pcn


def format_apn_broward(raw_folio: str) -> str:
    """Format Broward folio number for ATTOM. Broward uses 13-digit folios."""
    return raw_folio.strip().strip('"')


# ---------------------------------------------------------------------------
# Cache management — per-endpoint JSON files
# ---------------------------------------------------------------------------
def get_cache_path(endpoint_name: str) -> Path:
    """Return cache file path for a given endpoint."""
    return CACHE_DIR / f"cache_{endpoint_name}.json"


def load_cache(endpoint_name: str) -> dict:
    """Load cached results for an endpoint."""
    path = get_cache_path(endpoint_name)
    if path.exists():
        with open(path, "r") as f:
            return json.load(f)
    return {}


def save_cache(endpoint_name: str, cache: dict):
    """Save cache for an endpoint."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    with open(get_cache_path(endpoint_name), "w") as f:
        json.dump(cache, f, indent=2, default=str)


# ---------------------------------------------------------------------------
# ATTOM API call — generic for any endpoint
# ---------------------------------------------------------------------------
def call_attom(endpoint_path: str, params: dict, session: requests.Session) -> dict:
    """
    Call a single ATTOM endpoint. Returns raw JSON response or error dict.

    params should contain either:
      - apn + fips (preferred), OR
      - address1 + address2 (fallback)
    """
    url = f"{ATTOM_BASE}{endpoint_path}"
    headers = {
        "apikey": ATTOM_API_KEY,
        "Accept": "application/json",
    }

    try:
        resp = session.get(url, params=params, headers=headers, timeout=30)
    except requests.RequestException as e:
        return {"_error": str(e)}

    if resp.status_code == 200:
        return resp.json()
    elif resp.status_code == 429:
        return {"_rate_limited": True, "_error": "Rate limited — stop and wait"}
    elif resp.status_code == 404:
        return {"_error": "not_found"}
    else:
        return {"_error": f"HTTP {resp.status_code}: {resp.text[:200]}"}


# ---------------------------------------------------------------------------
# Field extraction per endpoint — pull the fields we need for dossiers
# ---------------------------------------------------------------------------
def extract_mortgage(data: dict) -> dict:
    """Extract fields from /property/detailmortgageowner response."""
    props = data.get("property", [])
    if not props:
        return {}
    prop = props[0]
    mortgage = prop.get("mortgage", {})
    owner = prop.get("owner", {})
    address = prop.get("address", {})
    summary = prop.get("summary", {})

    lender = mortgage.get("lender", {})
    title = mortgage.get("title", {})
    owner1 = owner.get("owner1", {})
    owner2 = owner.get("owner2", {})

    result = {
        "attom_lender_name": lender.get("lastname", ""),
        "attom_lender_city": lender.get("city", ""),
        "attom_lender_state": lender.get("state", ""),
        "attom_title_company": title.get("companyname", ""),
        "attom_loan_amount": mortgage.get("amount", ""),
        "attom_loan_date": mortgage.get("date", ""),
        "attom_loan_type": mortgage.get("loantypecode", ""),
        "attom_interest_rate": mortgage.get("interestrate", ""),
        "attom_rate_type": mortgage.get("interestratetype", ""),
        "attom_deed_type": mortgage.get("deedtype", ""),
        "attom_due_date": mortgage.get("duedate", ""),
        "attom_loan_term": mortgage.get("term", ""),
        # Owner resolution
        "attom_owner1_name": owner1.get("fullname", ""),
        "attom_owner1_last": owner1.get("lastname", ""),
        "attom_owner1_first": owner1.get("firstnameandmi", ""),
        "attom_owner2_name": owner2.get("fullname", ""),
        "attom_corporate": owner.get("corporateindicator", ""),
        "attom_absentee": owner.get("absenteeownerstatus", ""),
        "attom_mail_address": owner.get("mailingaddressoneline", ""),
        # Property identifiers
        "attom_property_address": address.get("oneLine", ""),
        "attom_property_type": summary.get("proptype", ""),
        "attom_year_built": summary.get("yearbuilt", ""),
    }
    # Classify lender type
    result["attom_lender_type"] = classify_lender(result["attom_lender_name"])
    return result


def extract_profile(data: dict) -> dict:
    """Extract fields from /property/expandedprofile response."""
    props = data.get("property", [])
    if not props:
        return {}
    prop = props[0]
    bldg = prop.get("building", {})
    geo = prop.get("geography", {})
    zoning = prop.get("zoning", {})
    summary = prop.get("summary", {})
    ident = prop.get("identifier", {})

    return {
        "attom_sqft": bldg.get("size", {}).get("livingsize", ""),
        "attom_beds": bldg.get("rooms", {}).get("beds", ""),
        "attom_baths_full": bldg.get("rooms", {}).get("bathsfull", ""),
        "attom_baths_half": bldg.get("rooms", {}).get("bathshalf", ""),
        "attom_baths_total": bldg.get("rooms", {}).get("bathstotal", ""),
        "attom_stories": bldg.get("summary", {}).get("levels", ""),
        "attom_year_built_profile": bldg.get("summary", {}).get("yearbuilt", ""),
        "attom_condition": bldg.get("summary", {}).get("quality", ""),
        "attom_construction": bldg.get("construction", {}).get("constructiontype", ""),
        "attom_roof": bldg.get("construction", {}).get("roofcover", ""),
        "attom_exterior": bldg.get("construction", {}).get("walltype", ""),
        "attom_parking": bldg.get("parking", {}).get("garagetype", ""),
        "attom_pool": bldg.get("summary", {}).get("view", ""),
        "attom_lat": geo.get("latitude", ""),
        "attom_lon": geo.get("longitude", ""),
        "attom_census_tract": geo.get("censustractandblock", ""),
        "attom_zoning": zoning.get("zoning", ""),
        "attom_lot_size_acres": summary.get("lotsizeacres", ""),
        "attom_lot_size_sqft": summary.get("lotsizesquarefeet", ""),
        "attom_subdivision": summary.get("legal1", ""),
        "attom_apn": ident.get("apn", ""),
    }


def extract_avm(data: dict) -> dict:
    """Extract fields from /attomavm/detail response."""
    props = data.get("property", [])
    if not props:
        return {}
    prop = props[0]
    avm = prop.get("avm", {})

    return {
        "attom_avm_value": avm.get("amount", {}).get("value", ""),
        "attom_avm_high": avm.get("amount", {}).get("high", ""),
        "attom_avm_low": avm.get("amount", {}).get("low", ""),
        "attom_avm_confidence": avm.get("amount", {}).get("scr", ""),
        "attom_avm_value_sqft": avm.get("amount", {}).get("valuePerSizeUnit", ""),
        "attom_avm_change_pct": avm.get("changePercent", ""),
        "attom_avm_date": avm.get("eventDate", ""),
    }


def extract_rental(data: dict) -> dict:
    """Extract fields from /valuation/rentalavm response."""
    props = data.get("property", [])
    if not props:
        return {}
    prop = props[0]
    # ATTOM returns "rentalAvm" with flat fields, NOT nested under "avm"
    rental = prop.get("rentalAvm", {})
    # Fallback to old path in case API format varies
    if not rental:
        rental = prop.get("avm", {})
        return {
            "attom_rent_estimate": rental.get("amount", {}).get("value", ""),
            "attom_rent_high": rental.get("amount", {}).get("high", ""),
            "attom_rent_low": rental.get("amount", {}).get("low", ""),
            "attom_rent_confidence": rental.get("amount", {}).get("scr", ""),
            "attom_rent_date": rental.get("eventDate", ""),
        }

    return {
        "attom_rent_estimate": rental.get("estimatedRentalValue", ""),
        "attom_rent_high": rental.get("estimatedMaxRentalValue", ""),
        "attom_rent_low": rental.get("estimatedMinRentalValue", ""),
        "attom_rent_confidence": "",
        "attom_rent_date": rental.get("valuationDate", ""),
    }


def extract_sales(data: dict) -> dict:
    """Extract fields from /saleshistory/detail response."""
    props = data.get("property", [])
    if not props:
        return {}
    prop = props[0]
    # ATTOM returns lowercase 'salehistory', not camelCase
    sales = prop.get("salehistory", []) or prop.get("saleHistory", [])

    if not sales:
        return {"attom_sale_count": "0"}

    result = {"attom_sale_count": str(len(sales))}

    # Most recent sale
    most_recent = sales[0] if sales else {}
    amt = most_recent.get("amount", {})
    calc = most_recent.get("calculation", {})
    # Fields use lowercase keys (saleamt, saletranstype, etc.)
    result["attom_last_sale_date"] = most_recent.get("saleTransDate", "") or amt.get("saleTransDate", "")
    result["attom_last_sale_price"] = str(amt.get("saleamt", "") or amt.get("saleAmt", ""))
    result["attom_last_sale_type"] = amt.get("saletranstype", "") or amt.get("saleTransType", "")
    result["attom_last_deed_type"] = amt.get("saledoctype", "") or amt.get("saleDocType", "")
    result["attom_last_price_per_bed"] = str(calc.get("priceperbed", "") or calc.get("pricePerBed", ""))
    result["attom_last_price_sqft"] = str(calc.get("pricepersizeunit", "") or calc.get("pricePerSizeUnit", ""))

    # Build full sales history as JSON string for the dossier
    history = []
    for sale in sales[:10]:  # Cap at 10 transactions
        s_amt = sale.get("amount", {})
        s_calc = sale.get("calculation", {})
        history.append({
            "date": sale.get("saleTransDate", ""),
            "price": s_amt.get("saleamt", "") or s_amt.get("saleAmt", ""),
            "type": s_amt.get("saletranstype", "") or s_amt.get("saleTransType", ""),
            "doc": s_amt.get("saledoctype", "") or s_amt.get("saleDocType", ""),
            "price_sqft": s_calc.get("pricepersizeunit", "") or s_calc.get("pricePerSizeUnit", ""),
        })
    result["attom_sales_history_json"] = json.dumps(history)

    return result


def extract_assessment(data: dict) -> dict:
    """Extract fields from /assessment/detail response."""
    props = data.get("property", [])
    if not props:
        return {}
    prop = props[0]
    assess = prop.get("assessment", {})
    tax = assess.get("tax", {})
    assessed = assess.get("assessed", {})
    market = assess.get("market", {})

    return {
        "attom_assessed_total": assessed.get("assdttlvalue", assessed.get("assdTtlValue", "")),
        "attom_assessed_improvement": assessed.get("assdimprvalue", assessed.get("assdImprValue", "")),
        "attom_assessed_land": assessed.get("assdlandvalue", assessed.get("assdLandValue", "")),
        "attom_market_total": market.get("mktttlvalue", market.get("mktTtlValue", "")),
        "attom_market_improvement": market.get("mktimprvalue", market.get("mktImprValue", "")),
        "attom_market_land": market.get("mktlandvalue", market.get("mktLandValue", "")),
        "attom_annual_tax": tax.get("taxamt", tax.get("taxAmt", "")),
        "attom_tax_year": tax.get("taxyear", tax.get("taxYear", "")),
    }


def extract_permits(data: dict) -> dict:
    """Extract fields from /property/buildingpermits response."""
    props = data.get("property", [])
    if not props:
        return {"attom_permit_count": "0"}
    prop = props[0]
    permits = prop.get("buildingPermits", [])

    if not permits:
        return {"attom_permit_count": "0"}

    result = {"attom_permit_count": str(len(permits))}

    # Most recent permit
    recent = permits[0] if permits else {}
    permit_type = recent.get("type", "")
    result["attom_last_permit_type"] = permit_type.get("category", "") if isinstance(permit_type, dict) else str(permit_type)
    result["attom_last_permit_desc"] = recent.get("description", "")
    result["attom_last_permit_date"] = recent.get("effectiveDate", "")
    permit_status = recent.get("status", "")
    result["attom_last_permit_status"] = permit_status.get("description", "") if isinstance(permit_status, dict) else str(permit_status)
    result["attom_last_permit_value"] = recent.get("jobValue", "")
    permit_biz = recent.get("business", "")
    result["attom_last_permit_contractor"] = permit_biz.get("name", "") if isinstance(permit_biz, dict) else str(permit_biz)

    # Total permit value
    total_value = 0
    for p in permits:
        try:
            val = float(p.get("jobValue", 0) or 0)
            total_value += val
        except (ValueError, TypeError):
            pass
    result["attom_total_permit_value"] = str(total_value) if total_value > 0 else ""

    # Full permit history as JSON for dossier
    permit_list = []
    for p in permits[:10]:
        p_type = p.get("type", "")
        p_status = p.get("status", "")
        p_biz = p.get("business", "")
        permit_list.append({
            "type": p_type.get("category", "") if isinstance(p_type, dict) else str(p_type),
            "desc": p.get("description", ""),
            "date": p.get("effectiveDate", ""),
            "status": p_status.get("description", "") if isinstance(p_status, dict) else str(p_status),
            "value": p.get("jobValue", ""),
            "contractor": p_biz.get("name", "") if isinstance(p_biz, dict) else str(p_biz),
        })
    result["attom_permits_json"] = json.dumps(permit_list)

    return result


# Map endpoint names to their extraction functions
EXTRACTORS = {
    "mortgage": extract_mortgage,
    "profile": extract_profile,
    "avm": extract_avm,
    "rental": extract_rental,
    "sales": extract_sales,
    "assessment": extract_assessment,
    "permits": extract_permits,
}


# ---------------------------------------------------------------------------
# Build property lookup list from lead data
# ---------------------------------------------------------------------------
def build_fl_lookups(lead_names: list, master_df: pd.DataFrame) -> list:
    """
    Build property lookup list for FL showcase leads.
    Uses pipe-delimited PHY_ADDR1 addresses from pilot_500_master.csv.
    Returns list of dicts with address-based lookup params.

    Note: The FL pilot data has property street addresses but no property
    zip codes. We pass the county + state to ATTOM as address2, which is
    more reliable than using the owner's mailing zip (which may be in a
    different city or state than the property).
    """
    # Map CO_NO to county name for address2
    COUNTY_NAMES = {
        "60": "Palm Beach County, FL",
        "16": "Broward County, FL",
    }

    lookups = []
    for name in lead_names:
        match = master_df[master_df["OWN_NAME"] == name]
        if len(match) == 0:
            print(f"  WARNING: '{name}' not found in FL master data")
            continue
        row = match.iloc[0]

        # Skip condo-only leads (property_types == "004") — ATTOM returns no data
        prop_types = str(row.get("property_types", "")).strip()
        if prop_types == "004":
            print(f"  SKIP (condo-only): '{name}'")
            continue

        co_no = str(row.get("CO_NO", "60")).strip()

        # Parse pipe-delimited addresses
        addresses_raw = str(row.get("PHY_ADDR1", "")).strip()
        if not addresses_raw or addresses_raw == "nan":
            print(f"  WARNING: No addresses for '{name}'")
            continue

        addresses = [a.strip() for a in addresses_raw.split("|") if a.strip()]

        # Use county+state for address2 — more reliable than mailing zip
        county_addr2 = COUNTY_NAMES.get(co_no, "FL")

        for addr in addresses:
            # For FL, we use address-based lookup since raw NAL (with parcel IDs)
            # is not on this machine. Pass county+state as address2.
            lookups.append({
                "owner_name": name,
                "co_no": co_no,
                "address": f"{addr}, {county_addr2}",
                "lookup_type": "address",
                "params": {
                    "address1": addr,
                    "address2": county_addr2,
                },
                "cache_key": f"fl|{co_no}|{addr.upper().replace(' ', '')}",
            })

    return lookups


def build_wake_lookups(lead_names: list, wake_df: pd.DataFrame) -> list:
    """
    Build property lookup list for Wake County showcase leads.
    Uses parcel_id + FIPS for APN-based lookup (preferred method).
    Returns list of dicts with APN+FIPS lookup params.
    """
    lookups = []
    for name in lead_names:
        # Wake data is property-level, so one owner may have multiple rows
        matches = wake_df[wake_df["owner_name_1"] == name]
        if len(matches) == 0:
            print(f"  WARNING: '{name}' not found in Wake data")
            continue

        for _, row in matches.iterrows():
            parcel_id = str(row.get("parcel_id", "")).strip()
            if not parcel_id or parcel_id == "nan":
                continue

            prop_street = str(row.get("prop_street", "")).strip()
            prop_city = str(row.get("prop_city", "")).strip()
            prop_zip = str(row.get("prop_zip", "")).strip()

            # APN + FIPS lookup (preferred)
            lookups.append({
                "owner_name": name,
                "co_no": "183",
                "address": f"{prop_street}, {prop_city}, NC",
                "lookup_type": "apn",
                "params": {
                    "apn": parcel_id,
                    "fips": "37183",
                },
                "cache_key": f"wake|{parcel_id}",
                # Fallback address params if APN fails
                "fallback_params": {
                    "address1": prop_street,
                    "address2": prop_zip if prop_zip and prop_zip != "nan" else "",
                },
            })

    return lookups


# ---------------------------------------------------------------------------
# Main enrichment loop
# ---------------------------------------------------------------------------
def enrich_properties(lookups: list, dry_run: bool = False) -> pd.DataFrame:
    """
    Run all 7 ATTOM endpoints for each property lookup.
    Returns a DataFrame with one row per property, all endpoint fields merged.
    """
    session = requests.Session()
    total_credits = 0
    total_cached = 0
    total_errors = 0
    rate_limited = False

    all_rows = []

    for li, lookup in enumerate(lookups):
        if rate_limited:
            break

        row_data = {
            "owner_name": lookup["owner_name"],
            "co_no": lookup["co_no"],
            "address": lookup["address"],
            "lookup_type": lookup["lookup_type"],
        }

        print(f"\n  [{li+1}/{len(lookups)}] {lookup['owner_name'][:35]} — {lookup['address'][:45]}")

        for ep in ENDPOINTS:
            ep_name = ep["name"]
            ep_path = ep["path"]
            cache = load_cache(ep_name)
            cache_key = lookup["cache_key"]

            # Check cache first
            if cache_key in cache:
                cached_data = cache[cache_key]
                if "_error" not in cached_data:
                    # Use cached data
                    extractor = EXTRACTORS[ep_name]
                    # The cache stores raw API response, extract fields
                    fields = extractor(cached_data)
                    row_data.update(fields)
                    total_cached += 1
                    continue
                elif cached_data.get("_error") == "not_found":
                    # Already confirmed no data — skip
                    total_cached += 1
                    continue
                elif "SuccessWithoutResult" in str(cached_data.get("_error", "")):
                    # ATTOM returned success but no data — skip, don't re-call
                    total_cached += 1
                    continue

            if dry_run:
                print(f"    WOULD CALL: {ep_name} ({ep['description']})")
                continue

            # Make API call
            params = lookup["params"].copy()
            result = call_attom(ep_path, params, session)

            # Check for rate limiting
            if result.get("_rate_limited"):
                print(f"\n  *** RATE LIMITED at credit {total_credits} ***")
                print(f"  Saving all caches and stopping.")
                rate_limited = True
                break

            # Handle errors — try fallback for APN lookups
            if "_error" in result and lookup["lookup_type"] == "apn" and "fallback_params" in lookup:
                error_type = result["_error"]
                if error_type not in ("not_found",):
                    # Try address fallback
                    print(f"    {ep_name}: APN failed ({error_type}), trying address fallback...")
                    fallback = lookup["fallback_params"].copy()
                    result = call_attom(ep_path, fallback, session)
                    total_credits += 1
                    time.sleep(REQUEST_DELAY)
                    if "_error" in result:
                        print(f"    {ep_name}: fallback also failed ({result['_error']})")

            total_credits += 1

            # Cache the raw response
            cache[cache_key] = result
            save_cache(ep_name, cache)

            # Extract fields if successful
            if "_error" not in result:
                extractor = EXTRACTORS[ep_name]
                fields = extractor(result)
                row_data.update(fields)
                lender = fields.get("attom_lender_name", "")
                if ep_name == "mortgage" and lender:
                    ltype = classify_lender(lender)
                    print(f"    {ep_name}: {lender} ({ltype})")
                elif ep_name == "avm":
                    avm_val = fields.get("attom_avm_value", "")
                    print(f"    {ep_name}: AVM ${avm_val}")
                elif ep_name == "rental":
                    rent = fields.get("attom_rent_estimate", "")
                    print(f"    {ep_name}: Rent ${rent}/mo")
                elif ep_name == "permits":
                    pcount = fields.get("attom_permit_count", "0")
                    print(f"    {ep_name}: {pcount} permits")
                else:
                    print(f"    {ep_name}: OK")
            else:
                error_msg = result.get("_error", "unknown")
                if error_msg != "not_found":
                    print(f"    {ep_name}: ERROR — {error_msg}")
                    total_errors += 1
                else:
                    print(f"    {ep_name}: no data (property not found)")

            time.sleep(REQUEST_DELAY)

        all_rows.append(row_data)

    # Summary
    print(f"\n  {'='*60}")
    print(f"  ENRICHMENT SUMMARY")
    print(f"  {'='*60}")
    print(f"  Properties processed: {len(all_rows)}")
    print(f"  API credits used:     {total_credits}")
    print(f"  Cache hits:           {total_cached}")
    print(f"  Errors:               {total_errors}")
    if rate_limited:
        print(f"  *** STOPPED DUE TO RATE LIMITING ***")
    print(f"  {'='*60}")

    return pd.DataFrame(all_rows)


# ---------------------------------------------------------------------------
# Derived Signal Computation — LO-focused intelligence columns
# ---------------------------------------------------------------------------
from datetime import datetime, date

def compute_derived_signals(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add LO-focused derived columns to the enriched property DataFrame.
    These signals turn raw ATTOM fields into actionable intelligence
    that an LO can use to prioritize calls and open conversations.
    """
    def _float(val, default=0.0):
        try:
            v = float(str(val).replace(",", "").replace("$", "").strip() or 0)
            return default if pd.isna(v) else v
        except (ValueError, TypeError):
            return default

    today = date.today()
    rows = []

    for _, row in df.iterrows():
        r = row.to_dict()

        avm = _float(r.get("attom_avm_value"))
        loan = _float(r.get("attom_loan_amount"))
        last_sale_price = _float(r.get("attom_last_sale_price"))
        rent_monthly = _float(r.get("attom_rent_estimate"))
        interest_rate = _float(r.get("attom_interest_rate"))
        annual_tax = _float(r.get("attom_annual_tax"))
        lender = str(r.get("attom_lender_name", "") or "").strip()
        due_date_str = str(r.get("attom_due_date", "") or "").strip()
        last_sale_date_str = str(r.get("attom_last_sale_date", "") or "").strip()
        lender_type = str(r.get("attom_lender_type", "") or "").strip()

        # --- Equity ---
        is_cash = (avm > 0 and loan == 0 and not lender)
        equity = avm - loan if avm > 0 else 0
        equity_pct = (equity / avm * 100) if avm > 0 else 0

        r["derived_equity"] = equity if equity > 0 else ""
        r["derived_equity_pct"] = round(equity_pct, 1) if equity_pct > 0 else ""
        r["derived_cash_buyer"] = is_cash

        # --- Appreciation ---
        if avm > 0 and last_sale_price > 0:
            appreciation = (avm - last_sale_price) / last_sale_price * 100
            r["derived_appreciation"] = round(appreciation, 1)
        else:
            r["derived_appreciation"] = ""

        # --- Hold years ---
        hold_years = ""
        if last_sale_date_str and last_sale_date_str not in ("", "nan", "None"):
            for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%Y-%m-%dT%H:%M:%S"):
                try:
                    sale_dt = datetime.strptime(last_sale_date_str[:10], fmt).date()
                    hold_years = round((today - sale_dt).days / 365.25, 1)
                    break
                except ValueError:
                    continue
        r["derived_hold_years"] = hold_years

        # --- Rental / DSCR ---
        annual_rent = rent_monthly * 12 if rent_monthly > 0 else 0
        r["derived_annual_rent"] = annual_rent if annual_rent > 0 else ""

        # Estimate annual debt service (P&I on 30yr at stated rate)
        annual_debt_service = 0
        if loan > 0 and interest_rate > 0:
            monthly_rate = interest_rate / 100 / 12
            n_payments = 360  # 30-year
            if monthly_rate > 0:
                monthly_pmt = loan * (monthly_rate * (1 + monthly_rate)**n_payments) / ((1 + monthly_rate)**n_payments - 1)
                annual_debt_service = monthly_pmt * 12

        dscr = 0
        if annual_rent > 0 and annual_debt_service > 0:
            dscr = annual_rent / annual_debt_service
        elif annual_rent > 0 and is_cash:
            dscr = 99.0  # Cash buyer — infinite DSCR (display as "N/A — Cash")
        r["derived_dscr"] = round(dscr, 2) if dscr > 0 and dscr < 99 else ("CASH" if is_cash and annual_rent > 0 else "")

        # --- Cash-out at 75% LTV ---
        cashout_75 = (avm * 0.75) - loan if avm > 0 else 0
        r["derived_cashout_75"] = round(cashout_75) if cashout_75 > 0 else ""

        # --- Months to maturity ---
        months_to_maturity = ""
        if due_date_str and due_date_str not in ("", "nan", "None"):
            for fmt in ("%Y-%m-%d", "%m/%d/%Y"):
                try:
                    due_dt = datetime.strptime(due_date_str[:10], fmt).date()
                    months_to_maturity = round((due_dt - today).days / 30.44)
                    break
                except ValueError:
                    continue
        r["derived_months_to_maturity"] = months_to_maturity

        # --- Refi Priority ---
        priority = "LOW"
        reasons = []
        if is_cash and equity > 200_000:
            priority = "HIGH"
            reasons.append("Cash buyer, high equity")
        if lender_type == "hard_money":
            priority = "HIGH"
            reasons.append("Hard money — needs refi")
        if isinstance(months_to_maturity, (int, float)) and 0 < months_to_maturity <= 12:
            priority = "HIGH"
            reasons.append("Maturity <12mo")
        if interest_rate > 8:
            if priority != "HIGH":
                priority = "HIGH"
            reasons.append(f"High rate ({interest_rate}%)")
        if equity_pct > 50 and not is_cash and equity > 100_000:
            if priority == "LOW":
                priority = "MEDIUM"
            reasons.append("Significant equity")

        r["derived_refi_priority"] = priority
        r["derived_refi_reasons"] = "; ".join(reasons) if reasons else ""

        # --- Call Opener ---
        opener = ""
        if is_cash and avm > 0:
            equity_fmt = f"${equity:,.0f}" if equity >= 1000 else f"${equity:.0f}"
            opener = f"You purchased this property with cash — you're sitting on {equity_fmt} in equity. Have you considered a cash-out refi to redeploy that capital?"
        elif lender_type == "hard_money" and lender:
            opener = f"I see you're financed through {lender} — I can help you exit into a long-term DSCR loan at a much better rate."
        elif interest_rate > 7.5:
            opener = f"Your current rate is {interest_rate}% — I can likely save you hundreds per month with a DSCR refi."
        elif isinstance(months_to_maturity, (int, float)) and 0 < months_to_maturity <= 18:
            opener = f"Your loan matures in about {months_to_maturity} months — let's get ahead of that with a DSCR refi."
        elif equity > 200_000:
            equity_fmt = f"${equity:,.0f}" if equity >= 1000 else f"${equity:.0f}"
            opener = f"You have about {equity_fmt} in equity — a cash-out refi could free up capital for your next investment."
        elif avm > 0:
            opener = f"I work with investors in your area and can offer competitive DSCR financing for your portfolio."
        r["derived_call_opener"] = opener

        rows.append(r)

    result = pd.DataFrame(rows)
    print(f"\n  Derived signals computed: {len(result)} properties")

    # Summary stats
    cash_count = sum(1 for _, r in result.iterrows() if r.get("derived_cash_buyer") == True)
    high_pri = sum(1 for _, r in result.iterrows() if r.get("derived_refi_priority") == "HIGH")
    has_rent = sum(1 for _, r in result.iterrows() if r.get("derived_annual_rent") not in ("", 0))
    has_tax = sum(1 for _, r in result.iterrows() if r.get("attom_annual_tax") not in ("", None, 0))
    print(f"    Cash buyers: {cash_count}")
    print(f"    HIGH priority: {high_pri}")
    print(f"    With rent estimate: {has_rent}")
    print(f"    With tax data: {has_tax}")

    return result


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="ATTOM 7-endpoint showcase enrichment"
    )
    parser.add_argument(
        "--market", required=True, choices=["fl", "wake"],
        help="Market to enrich: fl (South Florida) or wake (Wake County NC)"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Preview API calls without making them"
    )
    parser.add_argument(
        "--leads", type=str, default="",
        help="Comma-separated list of owner names to enrich (overrides defaults)"
    )
    parser.add_argument(
        "--max-props", type=int, default=0,
        help="Max properties per lead (0 = all)"
    )
    args = parser.parse_args()

    # Check API key
    if not ATTOM_API_KEY and not args.dry_run:
        print("\n  ERROR: ATTOM_API_KEY not set in .env")
        print("  Add ATTOM_API_KEY=your_key to scrape/.env")
        sys.exit(1)

    DEMO_DIR.mkdir(parents=True, exist_ok=True)
    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    # Parse lead names
    if args.leads:
        lead_names = [n.strip() for n in args.leads.split(",") if n.strip()]
    else:
        lead_names = None  # Will use all leads from the data

    print(f"\n{'='*60}")
    print(f"  ATTOM 7-ENDPOINT SHOWCASE ENRICHMENT")
    print(f"  Market: {args.market.upper()}")
    print(f"{'='*60}")

    # Build lookup list based on market
    if args.market == "fl":
        # Load FL pilot 500 master
        fl_input = DATA_DIR / "mvp" / "pilot_500_master.csv"
        if not fl_input.exists():
            print(f"\n  ERROR: FL master data not found: {fl_input}")
            sys.exit(1)

        master = pd.read_csv(fl_input, dtype=str)
        print(f"\n  Loaded FL master: {len(master)} leads")

        if lead_names is None:
            print("  ERROR: Must specify --leads for FL market")
            print("  Example: --leads 'DEMIRAY HOLDINGS INC,MSNO PROPERTIES LLC'")
            sys.exit(1)

        lookups = build_fl_lookups(lead_names, master)

    elif args.market == "wake":
        # Load Wake qualified data (property-level)
        wake_input = DATA_DIR / "filtered" / "wake_qualified.csv"
        if not wake_input.exists():
            print(f"\n  ERROR: Wake data not found: {wake_input}")
            sys.exit(1)

        wake_df = pd.read_csv(wake_input, dtype=str)
        print(f"\n  Loaded Wake data: {len(wake_df)} properties")

        if lead_names is None:
            print("  ERROR: Must specify --leads for Wake market")
            print("  Example: --leads 'OWNER NAME 1,OWNER NAME 2'")
            sys.exit(1)

        lookups = build_wake_lookups(lead_names, wake_df)

    if not lookups:
        print("\n  No properties to look up. Check lead names.")
        sys.exit(1)

    # Cap properties per lead if requested
    if args.max_props > 0:
        capped = []
        owner_counts = {}
        for lk in lookups:
            name = lk["owner_name"]
            owner_counts[name] = owner_counts.get(name, 0) + 1
            if owner_counts[name] <= args.max_props:
                capped.append(lk)
        lookups = capped

    print(f"\n  Leads: {len(set(lk['owner_name'] for lk in lookups))}")
    print(f"  Properties to enrich: {len(lookups)}")
    print(f"  Credits needed (max): {len(lookups) * 7}")

    if args.dry_run:
        print(f"\n  DRY RUN — previewing calls:")

    # Run enrichment
    result_df = enrich_properties(lookups, dry_run=args.dry_run)

    if not args.dry_run and len(result_df) > 0:
        # Compute derived LO-focused signals
        result_df = compute_derived_signals(result_df)

        # Save output
        output_file = DEMO_DIR / f"showcase_7ep_{args.market}.csv"
        result_df.to_csv(output_file, index=False)
        print(f"\n  Output saved: {output_file}")
        print(f"  Columns: {len(result_df.columns)}")

        # Show per-lead summary
        print(f"\n  Per-lead property counts:")
        for name in result_df["owner_name"].unique():
            count = len(result_df[result_df["owner_name"] == name])
            has_lender = result_df[
                (result_df["owner_name"] == name) &
                (result_df.get("attom_lender_name", pd.Series(dtype=str)).fillna("") != "")
            ].shape[0] if "attom_lender_name" in result_df.columns else 0
            has_avm = result_df[
                (result_df["owner_name"] == name) &
                (result_df.get("attom_avm_value", pd.Series(dtype=str)).fillna("") != "")
            ].shape[0] if "attom_avm_value" in result_df.columns else 0
            print(f"    {name[:40]}: {count} props, {has_lender} w/lender, {has_avm} w/AVM")

    print(f"\n  Next step: Run build_dossier_pdf.py to generate tear sheets")
    print()


if __name__ == "__main__":
    main()
