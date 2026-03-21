"""
Step 3: Score & Filter by ICP (Ideal Customer Profile)
=======================================================

Takes parsed property data from Step 2 and scores every record on a
0-100 point scale using signals from config/scoring_weights.json.

How scoring works:
  - Each record earns points for matching investor signals
  - Property signals:    no homestead, value range, multi-family, STR zip
  - Owner signals:       absentee, LLC, portfolio size
  - Transaction signals: cash purchase, recent buy, long hold
  - Points are additive — more signals = higher score

Records are then bucketed into tiers:
  Tier 1 (50+):  Hot leads — immediate outreach
  Tier 2 (30-49): Warm leads — email + direct mail
  Tier 3 (15-29): Nurture — long-term email only
  Discard (<15):  Not pursued

Each record also gets an ICP segment label (Portfolio Landlord,
Out-of-State Investor, STR Investor, etc.) based on which signals
matched most strongly.

Usage:
    python scripts/03_filter_icp.py --county seminole
    python scripts/03_filter_icp.py --county all
    python scripts/03_filter_icp.py --county wake --state NC
"""

import argparse
import json
import sys
from datetime import date
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import pandas as pd

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent
PARSED_DIR = PROJECT_DIR / "data" / "parsed"
FILTERED_DIR = PROJECT_DIR / "data" / "filtered"
CONFIG_FILE = PROJECT_DIR / "config" / "scoring_weights.json"
NC_CONFIG_FILE = PROJECT_DIR / "config" / "nc_scoring_weights.json"
AGENT_CONFIG_FILE = PROJECT_DIR / "config" / "agent_scoring_weights.json"

# US state codes — used to detect out-of-state vs foreign owners
US_STATES = {
    "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA", "HI", "ID",
    "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD", "MA", "MI", "MN", "MS",
    "MO", "MT", "NE", "NV", "NH", "NJ", "NM", "NY", "NC", "ND", "OH", "OK",
    "OR", "PA", "RI", "SC", "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV",
    "WI", "WY", "DC", "PR", "VI", "GU", "AS", "MP",
}


def load_config(state: str = "FL"):
    """Load scoring weights, STR zips, and tier thresholds from config."""
    config_path = NC_CONFIG_FILE if state.upper() == "NC" else CONFIG_FILE
    print(f"  Loading config: {config_path.name}")
    with open(config_path) as f:
        return json.load(f)


def build_str_zip_set(config: dict) -> set:
    """Flatten all STR-eligible zip codes into a single set for fast lookup."""
    all_zips = set()
    for region_zips in config.get("str_eligible_zips", {}).values():
        all_zips.update(region_zips)
    return all_zips


def safe_str(val) -> str:
    """Convert a value to a clean uppercase string. Handles NaN/None."""
    s = str(val).strip().upper()
    if s in ("NAN", "NONE", ""):
        return ""
    return s


def score_record(row, config: dict, str_zips: set, today: date, home_state: str = "FL") -> tuple:
    """
    Score a single record against the full ICP matrix.

    Returns:
        (total_score, list_of_matched_signal_names)
    """
    prop_signals = config["property_signals"]
    owner_signals = config["owner_signals"]
    txn_signals = config["transaction_signals"]

    score = 0
    matched = []

    # ===================================================================
    # PROPERTY SIGNALS
    # ===================================================================

    # --- No homestead exemption ---
    is_no_hmstd = safe_str(row.get("is_no_homestead", ""))
    hmstd_flag = safe_str(row.get("homestead_flag", ""))
    if is_no_hmstd in ("TRUE", "1", "YES") or hmstd_flag in ("N", "", "0"):
        score += prop_signals["no_homestead"]["points"]
        matched.append("no_homestead")

    # --- Property value range ---
    just_value = 0
    try:
        just_value = int(float(str(row.get("just_value", 0))))
    except (ValueError, TypeError):
        pass

    if 150_000 <= just_value <= 500_000:
        score += prop_signals["value_150k_500k"]["points"]
        matched.append("value_150k_500k")
    elif 500_000 < just_value <= 1_000_000:
        score += prop_signals["value_500k_1m"]["points"]
        matched.append("value_500k_1m")

    # --- Multi-family property ---
    use_code = safe_str(row.get("use_code", "")).zfill(2) if safe_str(row.get("use_code", "")) else ""
    use_desc = safe_str(row.get("use_description", ""))
    mf_config = prop_signals["multi_family"]

    if use_code in mf_config.get("use_codes", []):
        score += mf_config["points"]
        matched.append("multi_family")
    elif any(kw in use_desc for kw in mf_config.get("use_keywords", [])):
        score += mf_config["points"]
        matched.append("multi_family")

    # --- STR-eligible zip code ---
    prop_zip = safe_str(row.get("prop_zip", ""))[:5]
    if prop_zip in str_zips:
        score += prop_signals["str_eligible_zip"]["points"]
        matched.append("str_eligible_zip")

    # ===================================================================
    # OWNER SIGNALS
    # ===================================================================

    mail_state = safe_str(row.get("mail_state", ""))[:2]
    mail_zip = safe_str(row.get("mail_zip", ""))[:5]
    is_absentee = safe_str(row.get("is_absentee", ""))
    is_llc = safe_str(row.get("is_llc", ""))

    # --- Absentee: out-of-state vs in-state different zip ---
    # These are mutually exclusive — award the higher one
    if mail_state and mail_state != home_state and mail_state in US_STATES:
        score += owner_signals["absentee_out_of_state"]["points"]
        matched.append("absentee_out_of_state")
    elif mail_state and mail_state != home_state and mail_state not in US_STATES:
        # Foreign owner — treat as out-of-state (same points, different label)
        score += owner_signals["absentee_out_of_state"]["points"]
        matched.append("foreign_owner")
    elif is_absentee in ("TRUE", "1", "YES") or (mail_zip and prop_zip and mail_zip != prop_zip):
        score += owner_signals["absentee_in_state"]["points"]
        matched.append("absentee_in_state")

    # --- LLC/Corp owned ---
    if is_llc in ("TRUE", "1", "YES"):
        score += owner_signals["llc_corp_owned"]["points"]
        matched.append("llc_corp_owned")

    # --- Portfolio size (mutually exclusive — award the higher one) ---
    portfolio_count = 1
    try:
        portfolio_count = int(float(str(row.get("portfolio_count", 1))))
    except (ValueError, TypeError):
        pass

    if portfolio_count >= 5:
        score += owner_signals["portfolio_5_plus"]["points"]
        matched.append("portfolio_5_plus")
    elif portfolio_count >= 2:
        score += owner_signals["portfolio_2_to_4"]["points"]
        matched.append("portfolio_2_to_4")

    # ===================================================================
    # TRANSACTION SIGNALS
    # ===================================================================

    # --- Cash purchase ---
    is_cash = safe_str(row.get("is_cash_buyer", ""))
    if is_cash in ("TRUE", "1", "YES"):
        score += txn_signals["cash_purchase"]["points"]
        matched.append("cash_purchase")

    # --- Purchase recency ---
    sale_date_str = safe_str(row.get("sale_date", ""))
    sale_year = 0
    if sale_date_str:
        # sale_date could be "2024-03" (year-month) or "2024" or "2024-03-15"
        try:
            sale_year = int(sale_date_str[:4])
        except (ValueError, IndexError):
            pass

    if sale_year > 0:
        years_ago = today.year - sale_year

        if years_ago <= 1:
            score += txn_signals["recent_purchase_0_12mo"]["points"]
            matched.append("recent_purchase_0_12mo")
        elif years_ago <= 2:
            score += txn_signals["recent_purchase_12_24mo"]["points"]
            matched.append("recent_purchase_12_24mo")
        elif years_ago >= 5:
            score += txn_signals["long_hold_no_refi"]["points"]
            matched.append("long_hold_no_refi")

    return score, matched


def assign_icp_segment(matched_signals: list) -> str:
    """
    Based on which signals matched, assign the lead to the most
    relevant ICP segment. This determines the outreach angle.

    Priority order (if multiple segments match, pick the strongest):
    """
    signals = set(matched_signals)

    # ICP #1: Portfolio Landlord — highest value
    if "portfolio_5_plus" in signals:
        return "Portfolio Landlord (5+)"

    # ICP #7: Foreign National
    if "foreign_owner" in signals:
        return "Foreign National Investor"

    # ICP #5: Cash Buyer / BRRRR
    if "cash_purchase" in signals and ("no_homestead" in signals):
        return "Cash Buyer / BRRRR"

    # ICP #3: STR Investor
    if "str_eligible_zip" in signals and ("absentee_out_of_state" in signals or "absentee_in_state" in signals):
        return "STR Investor"

    # ICP #4: Out-of-State Investor
    if "absentee_out_of_state" in signals:
        return "Out-of-State Investor"

    # ICP #2: Self-Employed / LLC
    if "llc_corp_owned" in signals:
        return "Self-Employed / LLC Investor"

    # ICP #8: First-Time Investor
    if ("recent_purchase_0_12mo" in signals or "recent_purchase_12_24mo" in signals) and "portfolio_2_to_4" not in signals:
        return "First-Time Investor"

    # Growing portfolio
    if "portfolio_2_to_4" in signals:
        return "Growing Portfolio (2-4)"

    # Long-hold equity play
    if "long_hold_no_refi" in signals:
        return "Long-Hold Equity"

    # Generic investor (has signals but no clear segment)
    if "no_homestead" in signals:
        return "General Investor"

    return "Unclassified"


def assign_tier(score: int, tiers: dict) -> str:
    """Assign a tier label based on score and config thresholds."""
    if score >= tiers["tier_1"]["min_score"]:
        return "Tier 1 — Hot"
    elif score >= tiers["tier_2"]["min_score"]:
        return "Tier 2 — Warm"
    elif score >= tiers["tier_3"]["min_score"]:
        return "Tier 3 — Nurture"
    else:
        return "Discard"


# =========================================================================
# AGENT / BROKER SCORING — separate channel, different priorities
# =========================================================================

def load_agent_config():
    """Load agent-specific scoring weights."""
    if AGENT_CONFIG_FILE.exists():
        with open(AGENT_CONFIG_FILE) as f:
            return json.load(f)
    return None


def agent_score_record(row, config: dict, today: date, home_state: str = "FL") -> tuple:
    """
    Score a record for RE agent/broker relevance.
    Prioritizes: transaction velocity, portfolio scale, absentee status,
    cash buyer, development signals, geographic spread.

    Returns:
        (total_score, list_of_matched_signal_names)
    """
    prop_s = config["property_signals"]
    own_s = config["owner_signals"]
    txn_s = config["transaction_signals"]
    enrich_s = config.get("enrichment_signals", {})

    score = 0
    matched = []

    # --- PROPERTY SIGNALS ---

    # Investment property (no homestead)
    is_no_hmstd = safe_str(row.get("is_no_homestead", ""))
    hmstd_flag = safe_str(row.get("homestead_flag", ""))
    if is_no_hmstd in ("TRUE", "1", "YES") or hmstd_flag in ("N", "", "0"):
        score += prop_s["no_homestead"]["points"]
        matched.append("no_homestead")

    # Property value — agents care more about higher value (bigger commission)
    just_value = 0
    try:
        just_value = int(float(str(row.get("just_value", 0))))
    except (ValueError, TypeError):
        pass

    if just_value >= 1_000_000:
        score += prop_s["value_1m_plus"]["points"]
        matched.append("value_1m_plus")
    elif 500_000 < just_value < 1_000_000:
        score += prop_s["value_500k_1m"]["points"]
        matched.append("value_500k_1m")
    elif 150_000 <= just_value <= 500_000:
        score += prop_s["value_150k_500k"]["points"]
        matched.append("value_150k_500k")

    # Multi-family
    use_code = safe_str(row.get("use_code", "")).zfill(2) if safe_str(row.get("use_code", "")) else ""
    use_desc = safe_str(row.get("use_description", ""))
    mf_config = prop_s["multi_family"]
    if use_code in mf_config.get("use_codes", []):
        score += mf_config["points"]
        matched.append("multi_family")
    elif any(kw in use_desc for kw in mf_config.get("use_keywords", [])):
        score += mf_config["points"]
        matched.append("multi_family")

    # New construction (built within last 3 years)
    year_built = 0
    try:
        year_built = int(float(str(row.get("year_built", 0))))
    except (ValueError, TypeError):
        pass
    if year_built >= today.year - 3 and year_built > 0:
        score += prop_s["new_construction"]["points"]
        matched.append("new_construction")

    # High land ratio (land > 60% of total value = development potential)
    land_value = 0
    try:
        land_value = int(float(str(row.get("land_value", 0))))
    except (ValueError, TypeError):
        pass
    if just_value > 0 and land_value > 0 and (land_value / just_value) > 0.60:
        score += prop_s["high_land_ratio"]["points"]
        matched.append("high_land_ratio")

    # --- OWNER SIGNALS ---

    mail_state = safe_str(row.get("mail_state", ""))[:2]
    mail_zip = safe_str(row.get("mail_zip", ""))[:5]
    prop_zip = safe_str(row.get("prop_zip", ""))[:5]
    is_absentee = safe_str(row.get("is_absentee", ""))
    is_llc = safe_str(row.get("is_llc", ""))

    # Absentee — out-of-state is GOLD for agents (needs local representation)
    if mail_state and mail_state != home_state and mail_state in US_STATES:
        score += own_s["absentee_out_of_state"]["points"]
        matched.append("absentee_out_of_state")
    elif mail_state and mail_state != home_state and mail_state not in US_STATES:
        score += own_s["absentee_out_of_state"]["points"]
        matched.append("foreign_owner")
    elif is_absentee in ("TRUE", "1", "YES") or (mail_zip and prop_zip and mail_zip != prop_zip):
        score += own_s["absentee_in_state"]["points"]
        matched.append("absentee_in_state")

    # LLC
    if is_llc in ("TRUE", "1", "YES"):
        score += own_s["llc_corp_owned"]["points"]
        matched.append("llc_corp_owned")

    # Portfolio size — more granular tiers for agents
    portfolio_count = 1
    try:
        portfolio_count = int(float(str(row.get("portfolio_count", 1))))
    except (ValueError, TypeError):
        pass

    if portfolio_count >= 10:
        score += own_s["portfolio_10_plus"]["points"]
        matched.append("portfolio_10_plus")
    elif portfolio_count >= 5:
        score += own_s["portfolio_5_to_9"]["points"]
        matched.append("portfolio_5_to_9")
    elif portfolio_count >= 2:
        score += own_s["portfolio_2_to_4"]["points"]
        matched.append("portfolio_2_to_4")

    # --- TRANSACTION SIGNALS ---

    # Purchase recency — agents need FINER granularity (6mo vs 12mo matters)
    sale_date_str = safe_str(row.get("sale_date", ""))
    sale_year = 0
    sale_month = 0
    if sale_date_str:
        try:
            sale_year = int(sale_date_str[:4])
            if len(sale_date_str) >= 7:
                sale_month = int(sale_date_str[5:7])
        except (ValueError, IndexError):
            pass

    if sale_year > 0:
        # Calculate approximate months ago
        months_ago = (today.year - sale_year) * 12 + (today.month - (sale_month or 6))

        if months_ago <= 6:
            score += txn_s["recent_purchase_0_6mo"]["points"]
            matched.append("recent_purchase_0_6mo")
        elif months_ago <= 12:
            score += txn_s["recent_purchase_6_12mo"]["points"]
            matched.append("recent_purchase_6_12mo")
        elif months_ago <= 24:
            score += txn_s["recent_purchase_12_24mo"]["points"]
            matched.append("recent_purchase_12_24mo")

        # Long hold with large portfolio = disposition candidate
        years_ago = today.year - sale_year
        if years_ago >= 5 and portfolio_count >= 5:
            score += txn_s["long_hold_large_portfolio"]["points"]
            matched.append("long_hold_large_portfolio")

    # Cash buyer
    is_cash = safe_str(row.get("is_cash_buyer", ""))
    if is_cash in ("TRUE", "1", "YES"):
        score += txn_s["cash_buyer"]["points"]
        matched.append("cash_buyer")

    return score, matched


def assign_agent_segment(matched_signals: list, portfolio_count: int = 1) -> str:
    """Assign agent-relevant segment based on matched signals."""
    signals = set(matched_signals)

    # Serial Acquirer — highest value
    if "portfolio_10_plus" in signals:
        if "recent_purchase_0_6mo" in signals or "recent_purchase_6_12mo" in signals:
            return "Serial Acquirer (10+)"
        return "Serial Acquirer (10+)"

    # Active Developer
    if "new_construction" in signals and ("high_land_ratio" in signals or "llc_corp_owned" in signals):
        return "Active Developer"

    # Out-of-State Investor
    if "absentee_out_of_state" in signals or "foreign_owner" in signals:
        if portfolio_count >= 5:
            return "Out-of-State Investor"
        return "Out-of-State Investor"

    # High-Velocity Buyer
    if "recent_purchase_0_6mo" in signals and portfolio_count >= 3:
        return "High-Velocity Buyer"

    # Portfolio Builder
    if "portfolio_5_to_9" in signals:
        return "Portfolio Builder (5-9)"

    # Cash Buyer
    if "cash_buyer" in signals and ("recent_purchase_0_6mo" in signals or "recent_purchase_6_12mo" in signals):
        return "Cash Buyer"

    # Growing Investor
    if "portfolio_2_to_4" in signals:
        if "recent_purchase_0_6mo" in signals or "recent_purchase_6_12mo" in signals:
            return "Growing Investor (2-4)"
        return "Growing Investor (2-4)"

    # Long-Hold Disposition
    if "long_hold_large_portfolio" in signals:
        return "Long-Hold / Disposition Candidate"

    # General
    if "no_homestead" in signals:
        return "General Investor"

    return "Unclassified"


def agent_score_dataframe(df: pd.DataFrame, home_state: str = "FL") -> pd.DataFrame:
    """
    Score every row for agent/broker channel. Adds columns:
      agent_score, agent_tier, agent_signals, agent_segment
    Does NOT modify existing icp_* (LO) columns.
    """
    agent_config = load_agent_config()
    if agent_config is None:
        print("  WARNING: agent_scoring_weights.json not found. Skipping agent scoring.")
        return df

    tiers = agent_config["tiers"]
    today = date.today()

    print(f"  Agent scoring {len(df):,} records...")

    scores = []
    all_signals = []
    segments = []
    tier_labels = []

    for _, row in df.iterrows():
        portfolio_count = 1
        try:
            portfolio_count = int(float(str(row.get("portfolio_count", 1))))
        except (ValueError, TypeError):
            pass

        a_score, a_matched = agent_score_record(row, agent_config, today, home_state)
        scores.append(a_score)
        all_signals.append(", ".join(a_matched))
        segments.append(assign_agent_segment(a_matched, portfolio_count))
        tier_labels.append(assign_tier(a_score, tiers))

    df = df.copy()
    df["agent_score"] = scores
    df["agent_signals"] = all_signals
    df["agent_segment"] = segments
    df["agent_tier"] = tier_labels

    return df


def score_dataframe(df: pd.DataFrame, config: dict, home_state: str = "FL") -> pd.DataFrame:
    """
    Score every row in the DataFrame. Adds columns:
      icp_score, icp_tier, icp_signals, icp_segment
    """
    str_zips = build_str_zip_set(config)
    tiers = config["tiers"]
    today = date.today()

    print(f"  Scoring {len(df):,} records (state: {home_state})...")

    scores = []
    all_signals = []
    segments = []
    tier_labels = []

    for _, row in df.iterrows():
        score, matched = score_record(row, config, str_zips, today, home_state)
        scores.append(score)
        all_signals.append(", ".join(matched))
        segments.append(assign_icp_segment(matched))
        tier_labels.append(assign_tier(score, tiers))

    df = df.copy()
    df["icp_score"] = scores
    df["icp_signals"] = all_signals
    df["icp_segment"] = segments
    df["icp_tier"] = tier_labels

    return df


def print_summary(df: pd.DataFrame, config: dict):
    """Print a clear summary of scoring results."""

    total = len(df)
    tiers = config["tiers"]

    print()
    print("=" * 60)
    print("  SCORING SUMMARY")
    print("=" * 60)
    print(f"  Total records scored: {total:,}")
    print()

    # Tier breakdown
    print("  TIER BREAKDOWN")
    print("  " + "-" * 45)
    tier_counts = df["icp_tier"].value_counts()
    for tier_key in ["Tier 1 — Hot", "Tier 2 — Warm", "Tier 3 — Nurture", "Discard"]:
        count = tier_counts.get(tier_key, 0)
        pct = count / total * 100 if total > 0 else 0
        # Look up the action from config
        config_key = tier_key.split(" — ")[0].lower().replace(" ", "_") if "—" in tier_key else tier_key.lower()
        action = ""
        if "tier_1" in config_key or tier_key == "Tier 1 — Hot":
            action = tiers["tier_1"]["action"]
        elif "tier_2" in config_key or tier_key == "Tier 2 — Warm":
            action = tiers["tier_2"]["action"]
        elif "tier_3" in config_key or tier_key == "Tier 3 — Nurture":
            action = tiers["tier_3"]["action"]
        else:
            action = tiers["discard"]["action"]

        print(f"  {tier_key:20s}  {count:>7,}  ({pct:5.1f}%)  → {action}")

    # ICP segment breakdown (only for non-discarded)
    qualified = df[df["icp_tier"] != "Discard"]
    if not qualified.empty:
        print()
        print("  TOP ICP SEGMENTS (qualified leads only)")
        print("  " + "-" * 45)
        seg_counts = qualified["icp_segment"].value_counts().head(10)
        for seg, count in seg_counts.items():
            pct = count / len(qualified) * 100
            print(f"  {seg:35s}  {count:>6,}  ({pct:5.1f}%)")

    # Score distribution
    print()
    print("  SCORE DISTRIBUTION")
    print("  " + "-" * 45)
    brackets = [(80, 100), (60, 79), (50, 59), (40, 49), (30, 39), (20, 29), (10, 19), (0, 9)]
    for low, high in brackets:
        count = ((df["icp_score"] >= low) & (df["icp_score"] <= high)).sum()
        if count > 0:
            bar = "#" * min(count * 40 // total, 40) if total > 0 else ""
            print(f"  {low:3d}-{high:3d} pts:  {count:>7,}  {bar}")

    # Signal frequency (how often each signal fires)
    print()
    print("  SIGNAL FREQUENCY (how often each signal matches)")
    print("  " + "-" * 45)

    # Explode the comma-separated signals into individual counts
    all_signals = df["icp_signals"].str.split(", ").explode()
    all_signals = all_signals[all_signals != ""]
    signal_counts = all_signals.value_counts()

    # Build a label lookup from config
    signal_labels = {}
    for section in ["property_signals", "owner_signals", "transaction_signals"]:
        for key, val in config[section].items():
            signal_labels[key] = val.get("description", key)
    signal_labels["foreign_owner"] = "Foreign mailing address — non-US investor"

    for signal, count in signal_counts.items():
        pct = count / total * 100 if total > 0 else 0
        label = signal_labels.get(signal, signal)
        print(f"  {label[:45]:45s}  {count:>7,}  ({pct:5.1f}%)")

    # Top 10 highest-scoring leads
    print()
    print("  TOP 10 HIGHEST-SCORING LEADS")
    print("  " + "-" * 45)
    top = df.nlargest(10, "icp_score")
    for _, row in top.iterrows():
        name = str(row.get("owner_name_1", ""))[:30]
        score = row["icp_score"]
        tier = row["icp_tier"]
        segment = row["icp_segment"]
        props = row.get("portfolio_count", 1)
        print(f"  {score:3d} pts | {tier:18s} | {name:30s} | {props} props | {segment}")

    print()


def main():
    parser = argparse.ArgumentParser(
        description="Score & filter leads by ICP criteria (Step 3)"
    )
    parser.add_argument(
        "--county",
        type=str,
        required=True,
        help='County name (e.g. "seminole") or "all" to process all files in data/parsed/',
    )
    parser.add_argument(
        "--state",
        type=str,
        default="FL",
        help='State code (FL or NC). Determines scoring config and absentee detection. Default: FL',
    )
    args = parser.parse_args()

    FILTERED_DIR.mkdir(parents=True, exist_ok=True)

    home_state = args.state.strip().upper()

    # Load scoring config
    config = load_config(home_state)

    county_arg = args.county.strip().lower()

    # ---------------------------------------------------------------
    # Find parsed files to process
    # ---------------------------------------------------------------
    if county_arg == "all":
        parsed_files = sorted(PARSED_DIR.glob("*_parsed.csv"))
    else:
        county_slug = county_arg.replace(" ", "_").replace("-", "_")
        parsed_files = list(PARSED_DIR.glob(f"{county_slug}_parsed.csv"))

    if not parsed_files:
        print(f"\nNo parsed files found for '{county_arg}' in {PARSED_DIR}/")
        print(f"Run Step 2 first: python scripts/02_parse_nal.py --county {county_arg}")
        return

    print(f"\nFound {len(parsed_files)} file(s) to score.\n")

    # ---------------------------------------------------------------
    # Process each file
    # ---------------------------------------------------------------
    for filepath in parsed_files:
        county_name = filepath.stem.replace("_parsed", "")

        print("=" * 60)
        print(f"  SCORING: {county_name.upper()}")
        print("=" * 60)

        # Load parsed data
        df = pd.read_csv(filepath, dtype=str, low_memory=False)
        print(f"  Loaded {len(df):,} records from {filepath.name}")

        if df.empty:
            print("  WARNING: File is empty. Skipping.")
            continue

        # Score every record — LO channel (existing)
        scored = score_dataframe(df, config, home_state)

        # Score every record — Agent/Broker channel (new, additive)
        scored = agent_score_dataframe(scored, home_state)

        # Sort by LO score descending (best leads first)
        scored = scored.sort_values("icp_score", ascending=False)

        # Save — qualified leads only (Tier 1 + Tier 2 + Tier 3)
        qualified = scored[scored["icp_tier"] != "Discard"].copy()
        output_file = FILTERED_DIR / f"{county_name}_qualified.csv"
        qualified.to_csv(output_file, index=False)

        # Also save the full scored file (including discards) for reference
        full_output = FILTERED_DIR / f"{county_name}_all_scored.csv"
        scored.to_csv(full_output, index=False)

        # Print summary
        print_summary(scored, config)

        print(f"  SAVED (qualified only): {output_file}")
        print(f"    → {len(qualified):,} qualified leads")
        print(f"  SAVED (all scored):     {full_output}")
        print(f"    → {len(scored):,} total records")
        print()

    print("=" * 60)
    if home_state == "NC":
        print(f"  Next step: python scripts/05_enrich_contacts.py --counties {county_arg}")
        print(f"  (Skipping step 04 — NC SoS does not allow scraping)")
    else:
        print(f"  Next step: python scripts/04_sunbiz_llc_resolver.py --county {county_arg}")
    print("=" * 60)


if __name__ == "__main__":
    main()
