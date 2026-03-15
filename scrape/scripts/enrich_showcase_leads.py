"""
Enrich Showcase Leads — Full Per-Property Detail
=================================================

Pulls the COMPLETE property list + per-property detail for each of the 5
showcase FL leads used in the sales demo. Produces a CSV that
build_sales_demo.py (Tab 1 upgrade) reads to show per-property tables.

Steps:
  1. Read pilot_500_master.csv for the 5 showcase owners
  2. Read raw FL NAL data to get ALL properties per owner (not just aggregated)
  3. Pull per-property mortgage data from ATTOM or clerk cache
  4. Build enhanced talking points with specific $ figures
  5. Export to data/demo/showcase_enriched.csv

Usage:
    python scripts/enrich_showcase_leads.py
    python scripts/enrich_showcase_leads.py --skip-attom   # Use existing mortgage data only
"""

import argparse
import os
import sys
from pathlib import Path

import pandas as pd
import numpy as np

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
PROJECT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_DIR / "data"
FL_INPUT = DATA_DIR / "mvp" / "pilot_500_master.csv"
RAW_NAL_DIR = DATA_DIR / "raw"
OUTPUT_DIR = DATA_DIR / "demo"
OUTPUT_CSV = OUTPUT_DIR / "showcase_enriched.csv"
PROPS_CSV = OUTPUT_DIR / "showcase_properties.csv"

# ---------------------------------------------------------------------------
# The 5 showcase leads (must match build_sales_demo.py)
# ---------------------------------------------------------------------------
SHOWCASE_LEADS = [
    "DEMIRAY HOLDINGS INC",
    "MCDOUGALL LIVING TRUST",
    "STEBBINS LIDIA B",
    "MSNO PROPERTIES LLC",
    "JSF ENTERPRISES LLC",
]

ANON_NAMES = [
    "Apex Property Group Inc",
    "Lakeside Family Trust",
    "Lidia S. (Individual Investor)",
    "Meridian Realty Holdings LLC",
    "Coastal Equity Ventures LLC",
]

# Property use code → human-readable type
USE_CODE_MAP = {
    "000": "Vacant Residential",
    "001": "Single Family",
    "002": "Mobile Home",
    "003": "Multi-Family (2-9)",
    "004": "Condo",
    "005": "Co-op",
    "006": "Retirement Home",
    "007": "Misc Residential",
    "008": "Multi-Family (10+)",
    "009": "Residential Common",
    "010": "Vacant Commercial",
    "011": "Store/Retail",
    "012": "Mixed Use",
    "013": "Office",
    "014": "Warehouse",
    "015": "Manufacturing",
    "017": "Restaurant",
    "021": "Service Station",
    "039": "Hotel/Motel",
    "048": "Parking Lot",
    "100": "Vacant Industrial",
}


def fmt_currency(val):
    """Format as currency string."""
    try:
        v = float(val)
        if v >= 1_000_000:
            return f"${v/1_000_000:.1f}M"
        elif v >= 1_000:
            return f"${v/1_000:.0f}K"
        else:
            return f"${v:,.0f}"
    except (ValueError, TypeError):
        return ""


def load_raw_nal():
    """Load raw FL NAL data to get individual property records.

    The NAL file is ~328MB so we only load rows matching our showcase leads
    to avoid memory issues.
    """
    # Try several possible file locations
    candidates = [
        RAW_NAL_DIR / "NAL60F202501.csv",       # Palm Beach 2025 Final
        RAW_NAL_DIR / "palm_beach_nal.csv",
        RAW_NAL_DIR / "palmbeach_nal.csv",
        RAW_NAL_DIR / "pb_nal.csv",
    ]

    # Also check for any CSV in raw dir with "nal" in name
    if RAW_NAL_DIR.exists():
        for f in RAW_NAL_DIR.iterdir():
            if f.suffix == ".csv" and "nal" in f.name.lower() and f not in candidates:
                candidates.append(f)

    for path in candidates:
        if not path.exists():
            continue
        print(f"  Loading raw NAL from: {path.name} (chunked — filtering to showcase leads only)")
        # Read in chunks to handle 328MB file
        chunks = []
        lead_set = set(SHOWCASE_LEADS)
        for chunk in pd.read_csv(path, dtype=str, chunksize=50000):
            # Find owner column
            owner_col = None
            for col in ["OWN_NAME", "owner_name", "OWNER_NAME"]:
                if col in chunk.columns:
                    owner_col = col
                    break
            if owner_col is None:
                continue
            matched = chunk[chunk[owner_col].isin(lead_set)]
            if len(matched) > 0:
                chunks.append(matched)
        if chunks:
            result = pd.concat(chunks, ignore_index=True)
            print(f"    Found {len(result)} property records for showcase leads")
            return result
        else:
            print(f"    WARNING: No matching records found in {path.name}")
            return None

    return None


def get_property_type(use_code):
    """Convert use code to human-readable property type."""
    if not use_code or str(use_code).strip() in ("", "nan"):
        return "Unknown"
    code = str(use_code).strip().zfill(3)
    return USE_CODE_MAP.get(code, f"Code {code}")


def build_per_property_details(master_df, raw_df):
    """
    For each showcase lead, extract all individual properties with details.
    Returns a DataFrame with one row per property.
    """
    all_props = []

    for real_name, anon_name in zip(SHOWCASE_LEADS, ANON_NAMES):
        lead = master_df[master_df["OWN_NAME"] == real_name]
        if len(lead) == 0:
            print(f"    WARNING: {real_name} not found in master")
            continue
        lead = lead.iloc[0]

        # Get per-property records from raw NAL
        if raw_df is not None:
            # Try matching on owner name columns
            owner_col = None
            for col in ["OWN_NAME", "owner_name", "OWNER_NAME", "OWN_NAME1"]:
                if col in raw_df.columns:
                    owner_col = col
                    break

            if owner_col:
                props = raw_df[raw_df[owner_col] == real_name].copy()
            else:
                props = pd.DataFrame()
        else:
            props = pd.DataFrame()

        if len(props) == 0:
            # Fall back to pipe-delimited addresses from master
            addresses = str(lead.get("PHY_ADDR1", "")).split(" | ")
            total_val = float(lead.get("total_portfolio_value", 0) or 0)
            per_val = total_val / max(len(addresses), 1)

            for i, addr in enumerate(addresses):
                addr = addr.strip()
                if not addr:
                    continue
                all_props.append({
                    "owner_real": real_name,
                    "owner_anon": anon_name,
                    "prop_num": i + 1,
                    "address": f"{addr}, Palm Beach County, FL",
                    "est_value": per_val,
                    "property_type": "N/A",
                    "lender": str(lead.get("clean_lender", "")) or "Unknown",
                    "est_rate": str(lead.get("est_interest_rate", "")) or "",
                    "est_maturity": str(lead.get("est_maturity_date", "")) or "",
                    "est_balance": float(lead.get("est_remaining_balance", 0) or 0) / max(len(addresses), 1),
                    "est_equity": per_val - (float(lead.get("est_remaining_balance", 0) or 0) / max(len(addresses), 1)),
                    "purchase_date": str(lead.get("most_recent_purchase_date", "")) or "",
                    "purchase_price": "",
                })
        else:
            # Have individual property records
            for i, (_, prop) in enumerate(props.iterrows()):
                # Try various column name conventions
                addr = ""
                for c in ["PHY_ADDR1", "SITUS_ADDR", "property_address", "PROP_ADDR"]:
                    if c in prop and str(prop.get(c, "")).strip() not in ("", "nan"):
                        addr = str(prop[c]).strip()
                        break

                city = ""
                for c in ["PHY_CITY", "SITUS_CITY", "property_city"]:
                    if c in prop and str(prop.get(c, "")).strip() not in ("", "nan"):
                        city = str(prop[c]).strip()
                        break

                value = 0
                for c in ["JV", "JUST_VAL", "just_value", "JV_HMSTD", "TOTAL_VAL"]:
                    if c in prop:
                        try:
                            value = float(prop[c])
                            break
                        except (ValueError, TypeError):
                            pass

                use_code = ""
                for c in ["DOR_UC", "USE_CODE", "use_code"]:
                    if c in prop and str(prop.get(c, "")).strip() not in ("", "nan"):
                        use_code = str(prop[c]).strip()
                        break

                full_addr = f"{addr}, {city}, FL" if city else f"{addr}, Palm Beach County, FL"

                # Per-property mortgage estimate (divide aggregate evenly if no per-property data)
                prop_count = max(int(float(lead.get("property_count", 1) or 1)), 1)
                total_balance = float(lead.get("est_remaining_balance", 0) or 0)
                per_balance = total_balance / prop_count

                all_props.append({
                    "owner_real": real_name,
                    "owner_anon": anon_name,
                    "prop_num": i + 1,
                    "address": full_addr,
                    "est_value": value,
                    "property_type": get_property_type(use_code),
                    "lender": str(lead.get("clean_lender", "")) or "Unknown",
                    "est_rate": str(lead.get("est_interest_rate", "")) or "",
                    "est_maturity": str(lead.get("est_maturity_date", "")) or "",
                    "est_balance": per_balance,
                    "est_equity": value - per_balance if value > 0 else 0,
                    "purchase_date": "",
                    "purchase_price": "",
                })

    return pd.DataFrame(all_props)


def generate_enhanced_talking_points(lead_row, prop_count, total_value, total_equity, equity_pct):
    """
    Generate 3-5 sentence talking points with specific $ figures.
    """
    points = []
    name = str(lead_row.get("OWN_NAME", "Investor"))

    # 1. Portfolio size angle
    if prop_count >= 10:
        points.append(
            f"With {prop_count} investment properties worth {fmt_currency(total_value)} across Palm Beach County, "
            f"you're one of the most active portfolios we've identified — "
            f"let's talk about how a DSCR refinance can optimize your debt structure."
        )
    elif prop_count >= 5:
        points.append(
            f"Your {prop_count}-property portfolio valued at {fmt_currency(total_value)} puts you in a strong position — "
            f"DSCR financing can help you scale without the income documentation headaches of conventional loans."
        )
    else:
        points.append(
            f"Your {prop_count} properties valued at {fmt_currency(total_value)} show you're building actively — "
            f"DSCR loans let you qualify on property cash flow, not personal income."
        )

    # 2. Equity angle
    if equity_pct > 50:
        points.append(
            f"You're sitting on approximately {fmt_currency(total_equity)} in equity ({equity_pct:.0f}% LTV) — "
            f"a cash-out refinance at 75% LTV could unlock {fmt_currency(total_equity * 0.25)} "
            f"for your next acquisition without selling anything."
        )

    # 3. Rate/lender angle
    rate = str(lead_row.get("est_interest_rate", "")).strip()
    lender_type = str(lead_row.get("best_lender_type", "")).strip()
    if rate and rate != "nan":
        try:
            rate_num = float(rate)
            if rate_num >= 9:
                monthly_save = (total_value * (rate_num - 7.5) / 100) / 12
                points.append(
                    f"Your current rate of {rate_num}% is well above today's DSCR rates around 7-7.5% — "
                    f"refinancing could save approximately {fmt_currency(monthly_save)}/month across your portfolio."
                )
            elif rate_num >= 7.5:
                points.append(
                    f"At {rate_num}%, your current rate is competitive but there may be room to improve "
                    f"as DSCR rates have come down — worth a quick analysis."
                )
        except (ValueError, TypeError):
            pass

    if "hard money" in lender_type.lower() or "hard" in str(lead_row.get("est_loan_type", "")).lower():
        points.append(
            f"I see hard money financing on your portfolio — moving to a permanent DSCR loan "
            f"eliminates the 6-12 month maturity risk and typically cuts your rate by 3-5 points."
        )

    # 4. Maturity urgency
    if str(lead_row.get("est_maturity_urgent", "")).strip() == "True":
        months = str(lead_row.get("est_months_to_maturity", "")).strip()
        if months and months != "nan":
            points.append(
                f"With loan maturity in approximately {months} months, now is the time to line up permanent "
                f"financing — waiting until the last minute limits your negotiating power and options."
            )

    # 5. BRRRR / acquisition angle
    if str(lead_row.get("brrrr_exit_candidate", "")).strip() == "True":
        points.append(
            f"Your acquisition pattern looks like a BRRRR strategy — "
            f"a DSCR cash-out refi is the ideal exit from your rehab financing "
            f"and frees up capital for the next deal."
        )

    purchases = str(lead_row.get("purchases_last_12mo", "0")).strip()
    try:
        if int(float(purchases)) >= 2:
            points.append(
                f"With {purchases} acquisitions in the last 12 months, you're clearly active — "
                f"having a DSCR lender relationship means faster closes and better terms on each new deal."
            )
    except (ValueError, TypeError):
        pass

    # Cap at 5 points
    return " ".join(points[:5])


def main():
    parser = argparse.ArgumentParser(description="Enrich showcase leads with full property detail")
    parser.add_argument("--skip-attom", action="store_true", help="Skip ATTOM API calls, use existing data only")
    args = parser.parse_args()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    if not FL_INPUT.exists():
        print(f"  ERROR: FL master data not found: {FL_INPUT}")
        sys.exit(1)

    print("\n" + "=" * 60)
    print("SHOWCASE LEAD ENRICHMENT")
    print("=" * 60)

    # Load master data
    print("\n  Loading pilot master data...")
    master = pd.read_csv(FL_INPUT, dtype=str)
    print(f"    {len(master):,} leads loaded")

    # Load raw NAL for per-property detail
    print("\n  Loading raw NAL data for per-property records...")
    raw = load_raw_nal()
    if raw is not None:
        print(f"    {len(raw):,} raw property records loaded")
    else:
        print("    WARNING: No raw NAL file found — using pipe-delimited addresses from master")

    # Build per-property details
    print("\n  Building per-property details for 5 showcase leads...")
    props_df = build_per_property_details(master, raw)
    print(f"    {len(props_df)} total properties across {props_df['owner_real'].nunique()} leads")

    # Save per-property CSV
    props_df.to_csv(str(PROPS_CSV), index=False)
    print(f"    Saved: {PROPS_CSV.name}")

    # Build enhanced lead records with upgraded talking points
    print("\n  Generating enhanced talking points...")
    enhanced_leads = []

    for real_name, anon_name in zip(SHOWCASE_LEADS, ANON_NAMES):
        lead_match = master[master["OWN_NAME"] == real_name]
        if len(lead_match) == 0:
            continue
        lead = lead_match.iloc[0].to_dict()

        # Get property stats from our detail
        owner_props = props_df[props_df["owner_real"] == real_name]
        prop_count = len(owner_props)
        total_value = owner_props["est_value"].astype(float).sum()
        total_balance = owner_props["est_balance"].astype(float).sum()
        total_equity = total_value - total_balance
        equity_pct = (total_equity / total_value * 100) if total_value > 0 else 0

        # Generate enhanced talking points
        lead["enhanced_talking_points"] = generate_enhanced_talking_points(
            lead_match.iloc[0], prop_count, total_value, total_equity, equity_pct
        )
        lead["prop_count_verified"] = prop_count
        lead["total_value_verified"] = total_value
        lead["total_equity_verified"] = total_equity
        lead["equity_pct_verified"] = equity_pct
        lead["anon_name"] = anon_name

        # Collect all phone numbers (Tracerfy returns up to 8)
        phones = []
        for i in range(1, 9):
            p = str(lead.get(f"phone_{i}", "")).strip()
            if p and p != "nan":
                phones.append(p)
        lead["all_phones"] = " | ".join(phones) if phones else ""
        lead["phone_count"] = len(phones)

        # Collect all emails (up to 5)
        emails = []
        for i in range(1, 6):
            e = str(lead.get(f"email_{i}", "")).strip()
            if e and e != "nan":
                emails.append(e)
        lead["all_emails"] = " | ".join(emails) if emails else ""
        lead["email_count"] = len(emails)

        enhanced_leads.append(lead)
        print(f"    {anon_name}: {prop_count} properties, {fmt_currency(total_value)} value, "
              f"{equity_pct:.0f}% equity, {len(phones)} phones, {len(emails)} emails")

    # Save enhanced leads CSV
    enhanced_df = pd.DataFrame(enhanced_leads)
    enhanced_df.to_csv(str(OUTPUT_CSV), index=False)
    print(f"\n  Saved: {OUTPUT_CSV.name}")

    # Summary
    print("\n" + "=" * 60)
    print("ENRICHMENT SUMMARY")
    print("=" * 60)
    print(f"  Leads enriched:      {len(enhanced_leads)}")
    print(f"  Total properties:    {len(props_df)}")
    print(f"  Properties CSV:      {PROPS_CSV.name}")
    print(f"  Enhanced leads CSV:  {OUTPUT_CSV.name}")
    print(f"\n  Next step: Run build_sales_demo.py to generate updated Excel")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
