"""
Step 17: Derive Investment Profile
===================================

Takes ATTOM-enriched property data and derives investor-level intelligence:
  - Investment thesis (what kind of investor are they?)
  - Geographic focus (where do they concentrate?)
  - Price range preference (what's their sweet spot?)
  - Acquisition cadence (how often do they buy?)
  - Hold strategy (buy-and-hold vs flip?)
  - Property type preference (SFH, multi-family, etc.)
  - Next move prediction (what are they likely to do next?)

This is pure data derivation — no API calls, no LLM. Runs on any
ATTOM-enriched CSV (showcase_7ep_*.csv) and outputs investor-level
profiles that feed into Step 18 (Outreach Playbook Generator).

Input:  scrape/data/demo/showcase_7ep_{market}.csv  (property-level)
Output: scrape/data/demo/investment_profiles_{market}.csv (investor-level)

Usage:
    python scripts/17_derive_investment_profile.py --market wake
    python scripts/17_derive_investment_profile.py --market fl
    python scripts/17_derive_investment_profile.py --input path/to/enriched.csv
"""

import argparse
import json
import sys
from datetime import datetime, date
from pathlib import Path
from collections import Counter

import pandas as pd

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent
DATA_DIR = PROJECT_DIR / "data"
DEMO_DIR = DATA_DIR / "demo"

TODAY = date.today()


def _float(val, default=0.0):
    """Safely convert to float."""
    try:
        v = float(str(val).replace(",", "").replace("$", "").strip() or 0)
        return default if pd.isna(v) else v
    except (ValueError, TypeError):
        return default


def _parse_date(date_str):
    """Parse date string into date object, return None on failure."""
    if not date_str or str(date_str).strip() in ("", "nan", "None", "NaT"):
        return None
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%Y-%m-%dT%H:%M:%S", "%Y-%m"):
        try:
            return datetime.strptime(str(date_str).strip()[:10], fmt).date()
        except ValueError:
            continue
    return None


def derive_profile(owner_name: str, properties: pd.DataFrame) -> dict:
    """
    Derive an investor-level profile from their property portfolio.

    Args:
        owner_name: The investor/entity name
        properties: DataFrame of all properties owned by this investor
                   (from ATTOM-enriched data)

    Returns:
        dict with derived investment profile fields
    """
    n_props = len(properties)

    profile = {
        "investor_name": owner_name,
        "property_count": n_props,
    }

    # -----------------------------------------------------------------------
    # Geographic Focus
    # -----------------------------------------------------------------------
    cities = []
    zips = []
    streets = []
    for _, row in properties.iterrows():
        addr = str(row.get("address", ""))
        # Parse city from address (format: "STREET, CITY, ST ZIP")
        parts = addr.split(",")
        if len(parts) >= 2:
            city = parts[1].strip().split(",")[0].strip()
            if city:
                cities.append(city.upper())
        # Track street names for clustering
        street_parts = parts[0].strip().split(" ") if parts else []
        if len(street_parts) >= 2:
            street_name = " ".join(street_parts[1:])  # Drop house number
            streets.append(street_name.upper())

    city_counts = Counter(cities)
    street_counts = Counter(streets)

    profile["geo_cities"] = json.dumps(dict(city_counts))
    profile["geo_primary_city"] = city_counts.most_common(1)[0][0] if city_counts else ""
    profile["geo_city_count"] = len(city_counts)
    profile["geo_concentrated"] = len(city_counts) <= 2 and n_props >= 3

    # Detect street clustering (adjacent/same-street buys)
    repeated_streets = {s: c for s, c in street_counts.items() if c >= 2}
    profile["geo_street_clustering"] = bool(repeated_streets)
    profile["geo_clustered_streets"] = json.dumps(dict(repeated_streets)) if repeated_streets else ""

    # -----------------------------------------------------------------------
    # Price Range Preference
    # -----------------------------------------------------------------------
    avms = [_float(row.get("attom_avm_value")) for _, row in properties.iterrows()]
    avms = [v for v in avms if v > 0]

    if avms:
        avg_avm = sum(avms) / len(avms)
        min_avm = min(avms)
        max_avm = max(avms)
        total_portfolio_value = sum(avms)

        profile["price_avg"] = round(avg_avm)
        profile["price_min"] = round(min_avm)
        profile["price_max"] = round(max_avm)
        profile["price_range"] = f"${min_avm/1000:.0f}K - ${max_avm/1000:.0f}K"
        profile["portfolio_total_value"] = round(total_portfolio_value)

        # Classify price preference
        if avg_avm < 200_000:
            profile["price_preference"] = "entry_level"
        elif avg_avm < 350_000:
            profile["price_preference"] = "core_investment"
        elif avg_avm < 500_000:
            profile["price_preference"] = "mid_market"
        elif avg_avm < 1_000_000:
            profile["price_preference"] = "premium"
        else:
            profile["price_preference"] = "luxury"
    else:
        profile["price_avg"] = ""
        profile["price_min"] = ""
        profile["price_max"] = ""
        profile["price_range"] = ""
        profile["portfolio_total_value"] = ""
        profile["price_preference"] = ""

    # -----------------------------------------------------------------------
    # Acquisition Cadence & Timeline
    # -----------------------------------------------------------------------
    sale_dates = []
    sale_prices = []
    for _, row in properties.iterrows():
        # Try ATTOM sale history first, then fall back to base data
        sale_history_json = str(row.get("attom_sales_history_json", ""))
        if sale_history_json and sale_history_json not in ("", "nan", "None"):
            try:
                history = json.loads(sale_history_json)
                for sale in history:
                    dt = _parse_date(sale.get("date", ""))
                    price = _float(sale.get("price", 0))
                    if dt:
                        sale_dates.append(dt)
                        if price > 0:
                            sale_prices.append(price)
            except (json.JSONDecodeError, TypeError):
                pass

        # Also check last sale date as fallback
        last_dt = _parse_date(row.get("attom_last_sale_date", ""))
        if last_dt and last_dt not in sale_dates:
            sale_dates.append(last_dt)
            last_price = _float(row.get("attom_last_sale_price"))
            if last_price > 0:
                sale_prices.append(last_price)

    sale_dates.sort()
    unique_dates = sorted(set(sale_dates))

    if unique_dates:
        first_purchase = unique_dates[0]
        last_purchase = unique_dates[-1]
        years_active = max((last_purchase - first_purchase).days / 365.25, 0.1)

        profile["first_purchase_date"] = str(first_purchase)
        profile["last_purchase_date"] = str(last_purchase)
        profile["years_active"] = round(years_active, 1)
        profile["total_transactions"] = len(unique_dates)
        profile["transactions_per_year"] = round(len(unique_dates) / years_active, 1) if years_active >= 0.5 else len(unique_dates)

        # Days since last purchase
        days_since = (TODAY - last_purchase).days
        profile["days_since_last_purchase"] = days_since
        profile["months_since_last_purchase"] = round(days_since / 30.44)

        # Acquisition cadence
        if len(unique_dates) >= 2:
            gaps = [(unique_dates[i+1] - unique_dates[i]).days
                    for i in range(len(unique_dates) - 1)]
            avg_gap_days = sum(gaps) / len(gaps)
            profile["avg_days_between_purchases"] = round(avg_gap_days)
            profile["avg_months_between_purchases"] = round(avg_gap_days / 30.44, 1)

            # Predict next purchase window
            predicted_next = last_purchase.toordinal() + avg_gap_days
            predicted_date = date.fromordinal(int(predicted_next))
            profile["predicted_next_purchase"] = str(predicted_date)
            profile["predicted_next_in_days"] = (predicted_date - TODAY).days
        else:
            profile["avg_days_between_purchases"] = ""
            profile["avg_months_between_purchases"] = ""
            profile["predicted_next_purchase"] = ""
            profile["predicted_next_in_days"] = ""
    else:
        for key in ["first_purchase_date", "last_purchase_date", "years_active",
                     "total_transactions", "transactions_per_year",
                     "days_since_last_purchase", "months_since_last_purchase",
                     "avg_days_between_purchases", "avg_months_between_purchases",
                     "predicted_next_purchase", "predicted_next_in_days"]:
            profile[key] = ""

    # -----------------------------------------------------------------------
    # Hold Strategy
    # -----------------------------------------------------------------------
    hold_years_list = []
    for _, row in properties.iterrows():
        hy = _float(row.get("derived_hold_years"))
        if hy > 0:
            hold_years_list.append(hy)

    if hold_years_list:
        avg_hold = sum(hold_years_list) / len(hold_years_list)
        profile["avg_hold_years"] = round(avg_hold, 1)

        if avg_hold < 1:
            profile["hold_strategy"] = "flipper"
        elif avg_hold < 3:
            profile["hold_strategy"] = "short_hold"
        elif avg_hold < 7:
            profile["hold_strategy"] = "mid_hold"
        else:
            profile["hold_strategy"] = "long_hold"
    else:
        profile["avg_hold_years"] = ""
        profile["hold_strategy"] = ""

    # -----------------------------------------------------------------------
    # Property Type Preference
    # -----------------------------------------------------------------------
    prop_types = []
    beds_list = []
    sqft_list = []
    year_built_list = []

    for _, row in properties.iterrows():
        ptype = str(row.get("attom_property_type", "")).strip()
        if ptype and ptype not in ("", "nan"):
            prop_types.append(ptype)
        beds = _float(row.get("attom_beds"))
        if beds > 0:
            beds_list.append(int(beds))
        sqft = _float(row.get("attom_sqft"))
        if sqft > 0:
            sqft_list.append(sqft)
        yb = _float(row.get("attom_year_built", row.get("attom_year_built_profile", "")))
        if yb > 1800:
            year_built_list.append(int(yb))

    type_counts = Counter(prop_types)
    profile["property_types"] = json.dumps(dict(type_counts))
    profile["primary_property_type"] = type_counts.most_common(1)[0][0] if type_counts else ""
    profile["avg_beds"] = round(sum(beds_list) / len(beds_list), 1) if beds_list else ""
    profile["avg_sqft"] = round(sum(sqft_list) / len(sqft_list)) if sqft_list else ""
    profile["avg_year_built"] = round(sum(year_built_list) / len(year_built_list)) if year_built_list else ""

    # -----------------------------------------------------------------------
    # Financing Pattern
    # -----------------------------------------------------------------------
    cash_count = 0
    financed_count = 0
    lenders = []
    rates = []

    for _, row in properties.iterrows():
        is_cash = row.get("derived_cash_buyer")
        if is_cash == True or str(is_cash).lower() == "true":
            cash_count += 1
        else:
            loan = _float(row.get("attom_loan_amount"))
            if loan > 0:
                financed_count += 1
                lender = str(row.get("attom_lender_name", "")).strip()
                if lender and lender not in ("", "nan"):
                    lenders.append(lender)
                rate = _float(row.get("attom_interest_rate"))
                if rate > 0:
                    rates.append(rate)

    profile["cash_purchases"] = cash_count
    profile["financed_purchases"] = financed_count
    profile["cash_buyer_pct"] = round(cash_count / n_props * 100) if n_props > 0 else 0
    profile["financing_pattern"] = "all_cash" if financed_count == 0 and cash_count > 0 else \
                                    "mostly_cash" if cash_count > financed_count else \
                                    "mostly_financed" if financed_count > cash_count else \
                                    "mixed"
    profile["unique_lenders"] = json.dumps(list(set(lenders))) if lenders else ""
    profile["avg_interest_rate"] = round(sum(rates) / len(rates), 2) if rates else ""

    # -----------------------------------------------------------------------
    # Rental / Income Signals
    # -----------------------------------------------------------------------
    rents = [_float(row.get("attom_rent_estimate")) for _, row in properties.iterrows()]
    rents = [r for r in rents if r > 0]

    if rents:
        total_monthly_rent = sum(rents)
        profile["total_monthly_rent"] = round(total_monthly_rent)
        profile["total_annual_rent"] = round(total_monthly_rent * 12)
        profile["avg_rent_per_property"] = round(total_monthly_rent / len(rents))
    else:
        profile["total_monthly_rent"] = ""
        profile["total_annual_rent"] = ""
        profile["avg_rent_per_property"] = ""

    # Portfolio equity
    equities = [_float(row.get("derived_equity")) for _, row in properties.iterrows()]
    equities = [e for e in equities if e > 0]
    if equities:
        profile["total_equity"] = round(sum(equities))
        profile["avg_equity_per_property"] = round(sum(equities) / len(equities))
    else:
        profile["total_equity"] = ""
        profile["avg_equity_per_property"] = ""

    # -----------------------------------------------------------------------
    # Permit / Development Activity
    # -----------------------------------------------------------------------
    total_permits = sum(_float(row.get("attom_permit_count")) for _, row in properties.iterrows())
    total_permit_value = sum(_float(row.get("attom_total_permit_value")) for _, row in properties.iterrows())

    profile["total_permits"] = int(total_permits) if total_permits > 0 else 0
    profile["total_permit_value"] = round(total_permit_value) if total_permit_value > 0 else 0
    profile["active_developer"] = total_permits >= 3 or total_permit_value >= 100_000

    # -----------------------------------------------------------------------
    # Investment Thesis (derived narrative classification)
    # -----------------------------------------------------------------------
    thesis_signals = []

    if profile.get("active_developer"):
        thesis_signals.append("active_developer")
    if profile.get("financing_pattern") == "all_cash":
        thesis_signals.append("cash_buyer")
    if profile.get("hold_strategy") == "flipper":
        thesis_signals.append("flipper")
    if profile.get("geo_concentrated"):
        thesis_signals.append("neighborhood_focused")
    if profile.get("geo_city_count", 0) >= 3:
        thesis_signals.append("multi_market")
    if n_props >= 10:
        thesis_signals.append("serial_acquirer")
    elif n_props >= 5:
        thesis_signals.append("portfolio_builder")
    elif n_props >= 2:
        thesis_signals.append("growing_investor")

    tpy = _float(profile.get("transactions_per_year", 0))
    if tpy >= 3:
        thesis_signals.append("high_velocity")
    elif tpy >= 1.5:
        thesis_signals.append("active_buyer")

    profile["investment_thesis_signals"] = json.dumps(thesis_signals)

    # Primary thesis label
    if "active_developer" in thesis_signals:
        thesis = "Active Developer — builds/rehabs investment properties"
    elif "flipper" in thesis_signals:
        thesis = "Fix & Flip — short holds, likely value-add strategy"
    elif "high_velocity" in thesis_signals and "cash_buyer" in thesis_signals:
        thesis = "Aggressive Cash Buyer — high-frequency, no financing delays"
    elif "serial_acquirer" in thesis_signals:
        thesis = "Serial Acquirer — large portfolio, consistent buying pattern"
    elif "neighborhood_focused" in thesis_signals:
        thesis = "Neighborhood Specialist — concentrated in specific areas"
    elif "multi_market" in thesis_signals:
        thesis = "Multi-Market Investor — diversified across cities"
    elif "growing_investor" in thesis_signals:
        thesis = "Growing Investor — actively scaling portfolio"
    else:
        thesis = "General Investor — investment property owner"

    profile["investment_thesis"] = thesis

    # -----------------------------------------------------------------------
    # Next Move Prediction
    # -----------------------------------------------------------------------
    predictions = []

    pred_next_days = profile.get("predicted_next_in_days", "")
    if isinstance(pred_next_days, (int, float)):
        if pred_next_days <= 0:
            predictions.append("OVERDUE for next purchase based on historical cadence")
        elif pred_next_days <= 90:
            predictions.append(f"Likely buying again within {pred_next_days} days based on acquisition pattern")

    if profile.get("hold_strategy") == "long_hold" and n_props >= 5:
        predictions.append("Portfolio maturity suggests possible disposition or 1031 exchange")

    if profile.get("geo_street_clustering"):
        predictions.append("Street clustering pattern suggests land assembly or neighborhood buildout")

    if profile.get("active_developer") and tpy >= 2:
        predictions.append("Active development pace — likely needs off-market land or distressed properties")

    if cash_count > 0 and n_props >= 3:
        predictions.append("Cash buying capacity — can close fast on the right deal")

    profile["next_move_predictions"] = json.dumps(predictions)
    profile["next_move_summary"] = predictions[0] if predictions else "Monitoring for next transaction signal"

    return profile


def main():
    parser = argparse.ArgumentParser(
        description="Derive investor-level investment profiles from ATTOM-enriched data"
    )
    parser.add_argument(
        "--market", type=str, default="",
        help="Market to process: fl, wake (loads from demo/showcase_7ep_{market}.csv)"
    )
    parser.add_argument(
        "--input", type=str, default="",
        help="Path to ATTOM-enriched CSV (overrides --market)"
    )
    args = parser.parse_args()

    # Determine input file
    if args.input:
        input_path = Path(args.input)
    elif args.market:
        input_path = DEMO_DIR / f"showcase_7ep_{args.market}.csv"
    else:
        print("ERROR: Must specify --market or --input")
        sys.exit(1)

    if not input_path.exists():
        print(f"ERROR: Input file not found: {input_path}")
        sys.exit(1)

    print(f"\n{'='*60}")
    print(f"  STEP 17: DERIVE INVESTMENT PROFILES")
    print(f"  Input: {input_path.name}")
    print(f"{'='*60}")

    df = pd.read_csv(input_path, dtype=str)
    print(f"\n  Loaded: {len(df)} property records")

    # Group by owner
    owners = df["owner_name"].unique()
    print(f"  Unique investors: {len(owners)}")

    profiles = []
    for owner in owners:
        owner_props = df[df["owner_name"] == owner]
        profile = derive_profile(owner, owner_props)
        profiles.append(profile)

        # Print summary
        thesis = profile.get("investment_thesis", "")
        n = profile.get("property_count", 0)
        total_val = profile.get("portfolio_total_value", "")
        tpy = profile.get("transactions_per_year", "")
        next_move = profile.get("next_move_summary", "")
        print(f"\n  {owner[:45]}")
        print(f"    Properties: {n} | Total Value: ${total_val:,}" if total_val else f"    Properties: {n}")
        print(f"    Thesis: {thesis}")
        print(f"    Txns/Year: {tpy}" if tpy else "    Txns/Year: N/A")
        print(f"    Next Move: {next_move}")

    # Save output
    result_df = pd.DataFrame(profiles)

    if args.market:
        output_path = DEMO_DIR / f"investment_profiles_{args.market}.csv"
    else:
        output_path = input_path.parent / f"investment_profiles_{input_path.stem}.csv"

    result_df.to_csv(output_path, index=False)
    print(f"\n  Output saved: {output_path}")
    print(f"  Columns: {len(result_df.columns)}")
    print(f"\n  Next step: Run 18_generate_playbook.py to create outreach playbooks")
    print()


if __name__ == "__main__":
    main()
