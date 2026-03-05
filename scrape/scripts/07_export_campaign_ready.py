"""
Step 7: Export Campaign-Ready Lists
=====================================

The final step. Takes validated leads and exports them into files
formatted for each outreach channel:

  A. Instantly.ai — email campaigns
  B. SMS / Dialer — Twilio, OpenPhone, etc.
  C. Direct Mail — formatted for a mailing house
  D. Apollo.io — import for enrichment + sequences

Each channel gets separate files for Tier 1 and Tier 2 leads,
so you can prioritize hot leads for immediate outreach.

Usage:
    python scripts/07_export_campaign_ready.py --county seminole
    python scripts/07_export_campaign_ready.py --county all
"""

import argparse
import re
from pathlib import Path

import pandas as pd

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent
VALIDATED_DIR = PROJECT_DIR / "data" / "validated"
CAMPAIGN_DIR = PROJECT_DIR / "data" / "campaign_ready"

# Also check earlier dirs if validation was skipped
ENRICHED_DIR = PROJECT_DIR / "data" / "enriched"
FILTERED_DIR = PROJECT_DIR / "data" / "filtered"

# ICP segment → outreach angle (what to say in the first message)
OUTREACH_ANGLES = {
    "Portfolio Landlord (5+)": (
        "You own multiple properties in Florida. DSCR lets you keep "
        "scaling without income docs or DTI limits."
    ),
    "Foreign National Investor": (
        "Foreign national? DSCR is your path to Florida real estate "
        "financing — no US tax returns or credit history needed."
    ),
    "Cash Buyer / BRRRR": (
        "You own your property free and clear. Extract up to 80% equity "
        "with zero seasoning — close in 3 weeks."
    ),
    "STR Investor": (
        "Your Airbnb/VRBO income qualifies — we use AirDNA data, "
        "not bank rent estimates."
    ),
    "Out-of-State Investor": (
        "Investing in Florida from out of state? DSCR makes it simple "
        "— no tax returns needed."
    ),
    "Self-Employed / LLC Investor": (
        "Your tax returns don't show your true income. DSCR qualifies "
        "on the property's rent — not your 1040."
    ),
    "First-Time Investor": (
        "First investment property? DSCR keeps your personal DTI clean "
        "for your next primary home purchase."
    ),
    "Growing Portfolio (2-4)": (
        "Growing your portfolio? DSCR lets you scale past conventional "
        "loan limits without income documentation."
    ),
    "Long-Hold Equity": (
        "You've held your property for years and likely have significant "
        "equity. Tap it with a DSCR cash-out refi."
    ),
    "General Investor": (
        "Florida real estate investor? DSCR loans qualify on the property's "
        "rent — no income docs, no DTI limits."
    ),
}


def split_name(full_name: str) -> tuple:
    """
    Split a full name into (first_name, last_name).
    Handles 'LAST, FIRST' and 'FIRST LAST' formats.
    """
    if not full_name or str(full_name).strip().upper() in ("NAN", "NONE", ""):
        return ("", "")

    name = str(full_name).strip()

    # "LAST, FIRST" format (common in FDOR data)
    if "," in name:
        parts = name.split(",", 1)
        last = parts[0].strip()
        first = parts[1].strip() if len(parts) > 1 else ""
        # Remove middle name/initial
        first = first.split()[0] if first else ""
        return (first.title(), last.title())

    # "FIRST LAST" format
    parts = name.split()
    if len(parts) >= 2:
        return (parts[0].title(), parts[-1].title())
    elif len(parts) == 1:
        return (parts[0].title(), "")
    return ("", "")


def get_outreach_angle(segment: str) -> str:
    """Get the outreach angle text for an ICP segment."""
    return OUTREACH_ANGLES.get(str(segment), OUTREACH_ANGLES["General Investor"])


def find_input_file(county_name: str) -> Path:
    """Find the best input file — prefer validated, then enriched, then filtered."""
    candidates = [
        VALIDATED_DIR / f"{county_name}_validated.csv",
        ENRICHED_DIR / f"{county_name}_enriched.csv",
        FILTERED_DIR / f"{county_name}_llc_resolved.csv",
        FILTERED_DIR / f"{county_name}_qualified.csv",
    ]
    for path in candidates:
        if path.exists():
            return path
    return candidates[0]


def export_county(county_name: str):
    """Generate all campaign-ready export files for one county."""

    input_file = find_input_file(county_name)
    if not input_file.exists():
        print(f"  No input file found for '{county_name}'.")
        print(f"  Run earlier pipeline steps first.")
        return

    df = pd.read_csv(input_file, dtype=str, low_memory=False)
    print(f"  Loaded {len(df):,} records from {input_file.name}")

    # Ensure key columns exist with defaults
    defaults = {
        "email_1": "", "email_2": "", "phone_1": "", "phone_2": "",
        "phone_1_type": "", "phone_1_dnc": "", "phone_2_dnc": "",
        "email_1_status": "", "email_2_status": "",
        "icp_tier": "", "icp_segment": "", "icp_score": "0",
        "owner_name_1": "", "owner_name_2": "",
        "resolved_person": "",
        "mail_street": "", "mail_city": "", "mail_state": "", "mail_zip": "",
        "prop_street": "", "prop_city": "", "prop_zip": "",
        "just_value": "0", "portfolio_count": "1",
    }
    for col, default in defaults.items():
        if col not in df.columns:
            df[col] = default

    # -------------------------------------------------------------------
    # Derive first/last name from the best name available
    # Priority: resolved_person (from SunBiz) > owner_name_1
    # -------------------------------------------------------------------
    first_names = []
    last_names = []
    company_names = []

    for _, row in df.iterrows():
        resolved = str(row.get("resolved_person", "")).strip()
        owner = str(row.get("owner_name_1", "")).strip()
        is_llc = str(row.get("is_llc", "")).lower() in ("true", "1", "yes")

        # Use resolved person name if available, otherwise owner
        person_name = resolved if resolved and resolved.upper() not in ("NAN", "NONE") else ""
        if not person_name and not is_llc:
            person_name = owner

        first, last = split_name(person_name)
        first_names.append(first)
        last_names.append(last)

        # Company name is the LLC/entity name
        company_names.append(owner if is_llc else "")

    df["first_name"] = first_names
    df["last_name"] = last_names
    df["company_name"] = company_names

    # Outreach angle from ICP segment
    df["outreach_angle"] = df["icp_segment"].apply(get_outreach_angle)

    # Property address as single string
    df["property_address"] = (
        df["prop_street"].fillna("") + ", " +
        df["prop_city"].fillna("") + " " +
        df["prop_zip"].fillna("")
    ).str.strip(", ")

    # -------------------------------------------------------------------
    # Split into tiers
    # -------------------------------------------------------------------
    tier1 = df[df["icp_tier"].str.contains("Tier 1", na=False)].copy()
    tier2 = df[df["icp_tier"].str.contains("Tier 2", na=False)].copy()

    # -------------------------------------------------------------------
    # A. Instantly.ai Email Campaign CSV
    #    Needs: email, first_name, last_name, company_name, + custom fields
    #    Only records with a valid email
    # -------------------------------------------------------------------
    def export_email(tier_df, tier_label):
        # Prefer valid/catch-all emails, but include unvalidated too
        has_email = tier_df[
            tier_df["email_1"].astype(str).str.contains("@", na=False) &
            ~tier_df["email_1_status"].isin(["invalid"])
        ].copy()

        if has_email.empty:
            return 0

        out = has_email[["email_1", "first_name", "last_name", "company_name",
                         "property_address", "just_value", "portfolio_count",
                         "icp_tier", "outreach_angle"]].copy()

        out = out.rename(columns={
            "email_1": "email",
            "just_value": "property_value",
            "portfolio_count": "portfolio_size",
            "outreach_angle": "custom_1",
        })

        filename = f"email_{tier_label}_{county_name}.csv"
        out.to_csv(CAMPAIGN_DIR / filename, index=False)
        return len(out)

    # -------------------------------------------------------------------
    # B. SMS / Dialer CSV
    #    Needs: phone, first_name, last_name, + context fields
    #    Exclude DNC numbers. Prioritize mobile.
    # -------------------------------------------------------------------
    def export_sms(tier_df, tier_label):
        has_phone = tier_df[
            tier_df["phone_1"].astype(str).str.len() >= 10
        ].copy()

        if has_phone.empty:
            return 0

        # Exclude DNC numbers
        has_phone = has_phone[
            has_phone["phone_1_dnc"].astype(str).str.lower() != "true"
        ].copy()

        if has_phone.empty:
            return 0

        out = has_phone[["phone_1", "first_name", "last_name",
                         "property_address", "just_value", "portfolio_count",
                         "icp_tier", "phone_1_dnc", "phone_1_type"]].copy()

        out = out.rename(columns={
            "phone_1": "phone",
            "just_value": "property_value",
            "portfolio_count": "portfolio_size",
            "phone_1_dnc": "is_dnc",
            "phone_1_type": "phone_type",
        })

        # Sort: mobile numbers first (better for SMS)
        out["sort_key"] = out["phone_type"].map(
            {"mobile": 0, "voip": 1, "": 2, "unknown": 2, "landline": 3}
        ).fillna(2)
        out = out.sort_values("sort_key").drop(columns=["sort_key"])

        filename = f"sms_{tier_label}_{county_name}.csv"
        out.to_csv(CAMPAIGN_DIR / filename, index=False)
        return len(out)

    # -------------------------------------------------------------------
    # C. Direct Mail CSV
    #    Needs: name, mailing address, property info
    #    Every lead with a mailing address qualifies
    # -------------------------------------------------------------------
    def export_directmail(tier_df, tier_label):
        has_address = tier_df[
            tier_df["mail_street"].astype(str).str.len() > 3
        ].copy()

        if has_address.empty:
            return 0

        out = has_address[["first_name", "last_name", "company_name",
                           "mail_street", "mail_city", "mail_state", "mail_zip",
                           "property_address", "just_value", "icp_tier"]].copy()

        out = out.rename(columns={"just_value": "property_value"})

        filename = f"directmail_{tier_label}_{county_name}.csv"
        out.to_csv(CAMPAIGN_DIR / filename, index=False)
        return len(out)

    # -------------------------------------------------------------------
    # D. Apollo.io Import CSV
    #    All tiers combined, needs: name, email, phone, company, city, state
    # -------------------------------------------------------------------
    def export_apollo(full_df):
        # Apollo is for further enrichment, so include all qualified leads
        qualified = full_df[
            full_df["icp_tier"].str.contains("Tier", na=False)
        ].copy()

        if qualified.empty:
            return 0

        out = qualified[["first_name", "last_name", "email_1", "phone_1",
                         "company_name", "mail_city", "mail_state"]].copy()

        out = out.rename(columns={
            "email_1": "email",
            "phone_1": "phone",
            "mail_city": "city",
            "mail_state": "state",
        })

        # Apollo expects a title field
        out["title"] = "Real Estate Investor"

        filename = f"apollo_import_{county_name}.csv"
        out.to_csv(CAMPAIGN_DIR / filename, index=False)
        return len(out)

    # -------------------------------------------------------------------
    # Run all exports
    # -------------------------------------------------------------------
    print("\n  Exporting campaign-ready files...\n")

    results = {}

    # Email exports
    results["email_tier1"] = export_email(tier1, "tier1")
    results["email_tier2"] = export_email(tier2, "tier2")

    # SMS exports
    results["sms_tier1"] = export_sms(tier1, "tier1")
    results["sms_tier2"] = export_sms(tier2, "tier2")

    # Direct mail exports
    results["directmail_tier1"] = export_directmail(tier1, "tier1")
    results["directmail_tier2"] = export_directmail(tier2, "tier2")

    # Apollo export (all tiers)
    results["apollo"] = export_apollo(df)

    # -------------------------------------------------------------------
    # Print final summary
    # -------------------------------------------------------------------
    print("=" * 60)
    print("  CAMPAIGN-READY EXPORT SUMMARY")
    print("=" * 60)
    print(f"  County: {county_name.upper()}")
    print()

    # Tier counts
    print("  LEADS BY TIER")
    print("  " + "-" * 45)
    print(f"  Tier 1 (Hot):     {len(tier1):>7,}")
    print(f"  Tier 2 (Warm):    {len(tier2):>7,}")
    tier3_count = df["icp_tier"].str.contains("Tier 3", na=False).sum()
    print(f"  Tier 3 (Nurture): {tier3_count:>7,}")
    print(f"  Total qualified:  {len(tier1) + len(tier2) + tier3_count:>7,}")
    print()

    # Channel breakdown
    print("  LEADS BY CHANNEL")
    print("  " + "-" * 45)
    for key, count in results.items():
        if count > 0:
            filename = f"{key}_{county_name}.csv" if key != "apollo" else f"apollo_import_{county_name}.csv"
            print(f"  {key:25s}  {count:>7,}  → {filename}")
        else:
            print(f"  {key:25s}  {count:>7,}  (no qualifying records)")
    print()

    # Contact coverage
    total = len(df)
    has_email = df["email_1"].astype(str).str.contains("@", na=False).sum()
    has_phone = df["phone_1"].astype(str).str.len().ge(10).sum()
    has_address = df["mail_street"].astype(str).str.len().gt(3).sum()
    has_name = (df["first_name"].astype(str).str.len() > 0).sum()

    print("  CONTACT COVERAGE")
    print("  " + "-" * 45)
    pct = lambda n: f"{n / total * 100:.1f}%" if total > 0 else "0%"
    print(f"  Has name:          {has_name:>7,}  ({pct(has_name)})")
    print(f"  Has email:         {has_email:>7,}  ({pct(has_email)})")
    print(f"  Has phone:         {has_phone:>7,}  ({pct(has_phone)})")
    print(f"  Has mail address:  {has_address:>7,}  ({pct(has_address)})")
    print(f"  Has email OR phone:{has_email + has_phone - df[(df['email_1'].astype(str).str.contains('@', na=False)) & (df['phone_1'].astype(str).str.len() >= 10)].shape[0]:>7,}")
    print()

    # Files created
    print("  FILES CREATED")
    print("  " + "-" * 45)
    for key, count in results.items():
        if count > 0:
            if key == "apollo":
                fname = f"apollo_import_{county_name}.csv"
            else:
                fname = f"{key}_{county_name}.csv"
            print(f"  data/campaign_ready/{fname}")
    print()


def main():
    parser = argparse.ArgumentParser(
        description="Export campaign-ready lead lists (Step 7)"
    )
    parser.add_argument(
        "--county",
        type=str,
        required=True,
        help='County name (e.g. "seminole") or "all"',
    )
    args = parser.parse_args()

    CAMPAIGN_DIR.mkdir(parents=True, exist_ok=True)

    county_arg = args.county.strip().lower()

    if county_arg == "all":
        # Find available validated/enriched/filtered files
        files = sorted(VALIDATED_DIR.glob("*_validated.csv"))
        if not files:
            files = sorted(ENRICHED_DIR.glob("*_enriched.csv"))
        if not files:
            files = sorted(FILTERED_DIR.glob("*_qualified.csv"))
        if not files:
            print("\nNo input files found. Run earlier pipeline steps first.")
            return
        counties = []
        for f in files:
            name = f.stem.split("_")[0]
            if name not in counties:
                counties.append(name)
    else:
        counties = [county_arg.replace(" ", "_").replace("-", "_")]

    for county_name in counties:
        print()
        print("=" * 60)
        print(f"  EXPORTING: {county_name.upper()}")
        print("=" * 60)
        export_county(county_name)

    print("=" * 60)
    print("  PIPELINE COMPLETE")
    print("=" * 60)
    print(f"  All campaign-ready files are in: data/campaign_ready/")
    print()
    print("  What to do next:")
    print("  1. Upload email CSVs to Instantly.ai for cold email sequences")
    print("  2. Upload SMS CSVs to your dialer (Twilio, OpenPhone, etc.)")
    print("  3. Send direct mail CSVs to your mailing house")
    print("  4. Import Apollo CSV for further enrichment + sequences")
    print()


if __name__ == "__main__":
    main()
