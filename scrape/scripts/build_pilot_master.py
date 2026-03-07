#!/usr/bin/env python3
"""
Build pilot 500 master dataset with DSCR fixes, lender cleanup,
contact names, and talking points. Then create Tracerfy phone gap files.

Usage:
    python scrape/scripts/build_pilot_master.py
"""

import os
import re
import pandas as pd
import numpy as np

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INPUT = os.path.join(BASE, "data_gdrive_import", "data", "enriched", "pilot_500_enriched.csv")
MVP_DIR = os.path.join(BASE, "data", "mvp")
os.makedirs(MVP_DIR, exist_ok=True)

MASTER_OUT = os.path.join(MVP_DIR, "pilot_500_master.csv")
PHONE_GAP_OUT = os.path.join(MVP_DIR, "tracerfy_phone_gap.csv")
TRACERFY_UPLOAD_OUT = os.path.join(MVP_DIR, "tracerfy_upload_phones.csv")

# ──────────────────────────────────────────────
# Load data
# ──────────────────────────────────────────────
print("Loading pilot data...")
df = pd.read_csv(INPUT, dtype=str)
print(f"  Loaded {len(df)} rows, {len(df.columns)} columns")

# Convert numeric columns
num_cols = [
    "est_monthly_rent", "est_monthly_payment", "est_monthly_debt_service",
    "est_dscr", "est_remaining_balance", "equity_ratio",
    "property_count", "total_portfolio_value", "purchases_last_12mo",
    "flip_count", "attom_interest_rate", "est_portfolio_equity",
    "est_equity_pct", "est_original_loan", "most_recent_purchase_price",
]
for c in num_cols:
    if c in df.columns:
        df[c] = pd.to_numeric(df[c], errors="coerce")

# Convert boolean columns
for c in ["is_entity", "probable_cash_buyer"]:
    if c in df.columns:
        df[c] = df[c].map({"True": True, "False": False})

# ──────────────────────────────────────────────
# TASK 1.1: Fix DSCR calculation
# ──────────────────────────────────────────────
print("\n--- TASK 1.1: Fix DSCR calculation ---")
df["est_monthly_debt_service"] = df["est_monthly_payment"]
df["est_annual_debt_service"] = df["est_monthly_payment"] * 12
df["est_dscr"] = np.where(
    df["est_monthly_payment"] > 0,
    df["est_monthly_rent"] / df["est_monthly_payment"],
    np.nan,
)

has_dscr = df["est_dscr"].notna().sum()
print(f"  DSCR calculated for {has_dscr} leads (where est_monthly_payment > 0)")
print(f"  DSCR range: {df['est_dscr'].min():.2f} - {df['est_dscr'].max():.2f}")
print(f"  Median DSCR: {df['est_dscr'].median():.2f}")
above_1 = (df["est_dscr"] >= 1.0).sum()
print(f"  Leads with DSCR >= 1.0: {above_1}")

# ──────────────────────────────────────────────
# TASK 1.2: Clean lender names
# ──────────────────────────────────────────────
print("\n--- TASK 1.2: Clean lender names ---")

MERS_PATTERNS = [
    "MORTGAGE ELECTRONIC REGISTRATION SYSTEMS INC",
    "MORTGAGE ELECTRONIC REGISTRATION SYSTEMS",
    "MORTGAGE ELECTRONIC REGISTRATION SYSTEM",
    "MERS INC",
]


def clean_lender(raw):
    if pd.isna(raw) or not raw.strip():
        return np.nan
    s = raw.strip()
    # Check if MERS is present
    has_mers = False
    for pat in MERS_PATTERNS:
        if pat in s.upper():
            has_mers = True
            break
    if not has_mers:
        return s.strip()

    # Remove MERS portion and extract the real lender
    cleaned = s
    for pat in MERS_PATTERNS:
        cleaned = re.sub(re.escape(pat), "", cleaned, flags=re.IGNORECASE)
    # Clean up extra spaces
    cleaned = re.sub(r"\s{2,}", " ", cleaned).strip()
    # Remove trailing/leading commas, slashes
    cleaned = cleaned.strip(",/ ")

    if not cleaned or len(cleaned) < 3:
        return "MERS (Unknown Originator)"
    return cleaned


df["clean_lender"] = df["best_lender"].apply(clean_lender)

lender_counts = df["clean_lender"].notna().sum()
mers_unknown = (df["clean_lender"] == "MERS (Unknown Originator)").sum()
print(f"  Lenders cleaned: {lender_counts}")
print(f"  MERS (Unknown Originator): {mers_unknown}")
# Show some before/after examples
mers_mask = df["best_lender"].str.contains("MERS|MORTGAGE ELECTRONIC", case=False, na=False)
if mers_mask.any():
    examples = df.loc[mers_mask, ["best_lender", "clean_lender"]].head(5)
    print("  Sample MERS cleanup:")
    for _, row in examples.iterrows():
        print(f"    {row['best_lender'][:60]}... => {row['clean_lender']}")

# ──────────────────────────────────────────────
# TASK 1.3: Person name cleanup
# ──────────────────────────────────────────────
print("\n--- TASK 1.3: Person name cleanup ---")


def parse_own_name(name):
    """Parse 'LAST FIRST' or 'LAST FIRST MIDDLE' into 'First Last'."""
    if pd.isna(name) or not name.strip():
        return None
    name = name.strip().rstrip("&").strip()
    parts = name.split()
    if len(parts) < 2:
        return name.title()
    last = parts[0]
    first = parts[1]
    return f"{first.title()} {last.title()}"


def parse_resolved_person(name):
    """Parse 'LAST, FIRST' or 'Last, First' into 'First Last'."""
    if pd.isna(name) or not name.strip():
        return None
    name = name.strip()
    # Check for entity-like names (law offices, etc.)
    entity_indicators = ["LLC", "INC", "CORP", "PL", "PA", "LLP", "TRUST", "ASSOCIATION", "OFFICES"]
    if any(ind in name.upper() for ind in entity_indicators):
        return None
    if "," in name:
        parts = name.split(",", 1)
        last = parts[0].strip()
        first = parts[1].strip().split()[0] if parts[1].strip() else ""
        if first:
            return f"{first.title()} {last.title()}"
        return last.title()
    # Already in "First Last" format
    parts = name.strip().split()
    return " ".join(p.title() for p in parts)


def build_contact_name(row):
    # Priority 1: resolved_person (for entities that were resolved)
    rp = parse_resolved_person(row.get("resolved_person"))
    if rp:
        return rp

    # Priority 2: attom owner first/last (real person data)
    af = row.get("attom_owner1_first")
    al = row.get("attom_owner1_last")
    if pd.notna(af) and str(af).strip() and pd.notna(al) and str(al).strip():
        al_str = str(al).strip()
        # attom_owner1_last sometimes has entity names - skip those
        entity_indicators = ["LLC", "INC", "CORP", "TRUST"]
        if not any(ind in al_str.upper() for ind in entity_indicators):
            return f"{str(af).strip().split()[0].title()} {al_str.title()}"

    # Priority 3: Non-entity OWN_NAME parsing
    is_ent = row.get("is_entity")
    own = row.get("OWN_NAME")
    # Catch mis-classified entities (CRA, HOA, CDD, ASSN, etc.)
    if pd.notna(own):
        own_upper = str(own).upper()
        pseudo_entity_indicators = ["CRA", "CDD", "HOA", "ASSN", "ASSOCIATION", "PROPERTY OWNERS",
                                     "CONDOMINIUM", "CONDO", "CLUB", "CHURCH", "MINISTRY",
                                     "FOUNDATION", "COUNTY", "CITY OF", "TOWN OF", "STATE OF"]
        if any(ind in own_upper for ind in pseudo_entity_indicators):
            return f"{own.strip().title()} (Entity)"
    if not is_ent:
        parsed = parse_own_name(own)
        if parsed:
            return parsed

    # Priority 4: Entity name with suffix
    own = row.get("OWN_NAME")
    if pd.notna(own) and own.strip():
        return f"{own.strip().title()} (Entity)"
    return None


df["contact_name"] = df.apply(build_contact_name, axis=1)

named = df["contact_name"].notna().sum()
entity_suffix = df["contact_name"].str.contains("(Entity)", na=False).sum()
print(f"  Contact names assigned: {named}/{len(df)}")
print(f"  With (Entity) suffix: {entity_suffix}")
print(f"  Real person names: {named - entity_suffix}")
print("  Sample names:", df["contact_name"].dropna().head(10).tolist())

# ──────────────────────────────────────────────
# TASK 1.4: Create talking_points field
# ──────────────────────────────────────────────
print("\n--- TASK 1.4: Create talking points ---")


def format_dollar(val):
    if pd.isna(val) or val == 0:
        return "$0"
    if val >= 1_000_000:
        return f"${val / 1_000_000:.1f}M"
    if val >= 1_000:
        return f"${val / 1_000:.0f}K"
    return f"${val:,.0f}"


def build_talking_points(row):
    parts = []

    # Portfolio summary
    prop_count = row.get("property_count", 0)
    total_val = row.get("total_portfolio_value", 0)
    prop_count = int(prop_count) if pd.notna(prop_count) and prop_count > 0 else 0
    total_val = total_val if pd.notna(total_val) and total_val > 0 else 0

    lender = row.get("clean_lender")
    lender_str = f"Current lender: {lender}." if pd.notna(lender) and lender else ""

    if prop_count > 0:
        parts.append(
            f"{prop_count}-property portfolio worth {format_dollar(total_val)}. {lender_str}".strip()
        )
    elif lender_str:
        parts.append(lender_str)

    # Refi angles
    angles = []
    if row.get("probable_cash_buyer") == True:
        angles.append("Probable cash buyer - strong candidate for cash-out refi to fund next acquisition.")

    eq_ratio = row.get("equity_ratio")
    if pd.notna(eq_ratio) and eq_ratio > 0.5:
        angles.append(f"High equity position ({eq_ratio * 100:.0f}%) - cash-out refi opportunity.")

    remaining = row.get("est_remaining_balance")
    portfolio = row.get("total_portfolio_value")
    if (
        pd.notna(remaining)
        and pd.notna(portfolio)
        and portfolio > 0
        and remaining > 0
        and (remaining / portfolio) < 0.3
    ):
        angles.append("Low leverage - significant untapped equity.")

    purchases = row.get("purchases_last_12mo")
    if pd.notna(purchases) and purchases > 0:
        angles.append(
            f"Active buyer ({int(purchases)} purchase{'s' if purchases > 1 else ''} in 12mo) - likely needs ongoing financing."
        )

    flips = row.get("flip_count")
    if pd.notna(flips) and flips > 0:
        angles.append(
            f"Flipper profile ({int(flips)} flip{'s' if flips > 1 else ''}) - may need bridge/fix-and-flip financing."
        )

    rate = row.get("attom_interest_rate")
    if pd.notna(rate) and rate > 6:
        angles.append(f"Current rate {rate:.1f}% - may benefit from rate-and-term refi.")

    if angles:
        parts.append(" ".join(angles[:3]))  # Cap at 3 angles to keep it concise

    return " ".join(parts) if parts else ""


df["talking_points"] = df.apply(build_talking_points, axis=1)

has_tp = (df["talking_points"].str.len() > 0).sum()
print(f"  Talking points generated: {has_tp}/{len(df)}")
print("  Sample:")
for tp in df["talking_points"].dropna().head(3).tolist():
    print(f"    {tp[:120]}...")

# ──────────────────────────────────────────────
# Save master dataset
# ──────────────────────────────────────────────
print(f"\n--- Saving master dataset to {MASTER_OUT} ---")
df.to_csv(MASTER_OUT, index=False)
print(f"  Saved {len(df)} rows, {len(df.columns)} columns")

# ──────────────────────────────────────────────
# TASK 2: Phone gap analysis
# ──────────────────────────────────────────────
print("\n\n=== TASK 2: Phone gap analysis ===")
phone_gap = df[df["phone_1"].isna()].copy()
gap_cols = [
    "OWN_NAME", "resolved_person", "contact_name",
    "OWN_ADDR1", "OWN_CITY", "OWN_STATE", "OWN_ZIPCD", "is_entity",
]
phone_gap_out = phone_gap[gap_cols]
phone_gap_out.to_csv(PHONE_GAP_OUT, index=False)
print(f"  Leads needing phones: {len(phone_gap_out)} of {len(df)} ({len(phone_gap_out)/len(df)*100:.1f}%)")
entity_gap = phone_gap_out["is_entity"].sum()
print(f"  Of those, entities: {entity_gap}, persons: {len(phone_gap_out) - entity_gap}")

# ──────────────────────────────────────────────
# TASK 3: Tracerfy upload CSV
# ──────────────────────────────────────────────
print("\n\n=== TASK 3: Tracerfy upload CSV ===")


def split_contact_name(row):
    cn = row.get("contact_name")
    if pd.isna(cn) or not str(cn).strip():
        # Use entity name as last name
        own = row.get("OWN_NAME")
        if pd.notna(own):
            return "", own.strip()
        return "", ""

    cn = str(cn).strip()
    # Remove (Entity) suffix
    if cn.endswith("(Entity)"):
        entity_name = cn.replace("(Entity)", "").strip()
        return "", entity_name

    parts = cn.split()
    if len(parts) == 1:
        return "", parts[0]
    first = parts[0]
    last = " ".join(parts[1:])
    return first, last


# Build upload dataframe
upload_rows = []
for _, row in phone_gap.iterrows():
    first, last = split_contact_name(row)
    # Use OWN_STATE_DOM for 2-letter codes if available, else map full state names
    state = row.get("OWN_STATE_DOM") if pd.notna(row.get("OWN_STATE_DOM")) else row.get("OWN_STATE", "")
    # Map full state names to abbreviations
    state_map = {
        "Florida": "FL", "Connecticut": "CT", "New Jersey": "NJ",
        "California": "CA", "Massachusetts": "MA", "Vermont": "VT",
        "New York": "NY", "Texas": "TX", "Georgia": "GA",
        "Pennsylvania": "PA", "Illinois": "IL", "Ohio": "OH",
        "Virginia": "VA", "Maryland": "MD", "Colorado": "CO",
        "Michigan": "MI", "North Carolina": "NC", "South Carolina": "SC",
        "Tennessee": "TN", "Arizona": "AZ", "Nevada": "NV",
        "Washington": "WA", "Oregon": "OR", "Minnesota": "MN",
        "Wisconsin": "WI", "Indiana": "IN", "Missouri": "MO",
        "Louisiana": "LA", "Alabama": "AL", "Kentucky": "KY",
        "Delaware": "DE", "District of Columbia": "DC",
        "Federated States of Micro": "FM",
    }
    state_str = str(state).strip()
    if len(state_str) > 2:
        state_str = state_map.get(state_str, state_str)

    upload_rows.append({
        "First Name": first,
        "Last Name": last,
        "Address": str(row.get("OWN_ADDR1", "")).strip(),
        "City": str(row.get("OWN_CITY", "")).strip(),
        "State": state_str,
        "Zip": str(row.get("OWN_ZIPCD", "")).strip(),
    })

upload_df = pd.DataFrame(upload_rows)
upload_df.to_csv(TRACERFY_UPLOAD_OUT, index=False)
print(f"  Tracerfy upload file: {len(upload_df)} rows")
has_first = (upload_df["First Name"].str.len() > 0).sum()
print(f"  With first name: {has_first}")
print(f"  Entity-only (no first name): {len(upload_df) - has_first}")
print(f"  Estimated Tracerfy cost at ~45% match rate: ${len(upload_df) * 0.45 * 0.02:.2f}")
print()
print("  Sample rows:")
print(upload_df.head(5).to_string(index=False))

print("\n\n=== SUMMARY ===")
print(f"  Master dataset: {MASTER_OUT}")
print(f"    {len(df)} rows, {len(df.columns)} columns")
print(f"  Phone gap file: {PHONE_GAP_OUT}")
print(f"    {len(phone_gap_out)} leads needing phones")
print(f"  Tracerfy upload: {TRACERFY_UPLOAD_OUT}")
print(f"    {len(upload_df)} rows ready for upload")
