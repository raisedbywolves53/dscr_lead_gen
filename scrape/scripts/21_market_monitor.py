"""
Step 21: Market Monitor
========================

Detects meaningful changes in investor activity by comparing current
property data against a previous snapshot. Generates an alert digest
that can be delivered via email to agents.

HOW IT WORKS:
  1. Downloads fresh property data (or uses a provided file)
  2. Loads the previous snapshot
  3. Diffs ownership, sale dates, and portfolio composition
  4. Flags meaningful changes:
     - NEW_PURCHASE: Known investor acquired a new property
     - NEW_INVESTOR: Owner crossed from 1 to 2+ properties (new investor signal)
     - PORTFOLIO_GROWTH: Investor's portfolio count increased
     - DISPOSITION: Investor sold a property (capital redeployment)
     - TIER_CHANGE: Investor moved up or down a tier
  5. Scores and ranks alerts by significance
  6. Outputs alerts CSV + HTML digest email

SCHEDULE: Weekly cron job or manual run after fresh data pull.

SNAPSHOTS: Each run saves a snapshot to data/snapshots/ so the next
run can diff against it. First run creates the baseline.

Usage:
    # First run — creates baseline snapshot
    python scripts/21_market_monitor.py --market wake --baseline

    # Subsequent runs — diff against previous snapshot
    python scripts/21_market_monitor.py --market wake

    # Use a specific fresh data file
    python scripts/21_market_monitor.py --market wake --fresh path/to/new_data.csv

    # Generate email digest
    python scripts/21_market_monitor.py --market wake --email alerts@northside-realty.com
"""

import argparse
import json
import os
import sys
from datetime import date, datetime
from pathlib import Path

import pandas as pd

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent
DATA_DIR = PROJECT_DIR / "data"
FILTERED_DIR = DATA_DIR / "filtered"
SNAPSHOT_DIR = DATA_DIR / "snapshots"
ALERTS_DIR = DATA_DIR / "alerts"

if load_dotenv:
    load_dotenv(PROJECT_DIR / ".env")

TODAY = date.today()
TODAY_STR = TODAY.strftime("%Y-%m-%d")

# Institutional exclusions (same as build_demo_crm.py)
INSTITUTIONAL_KEYWORDS = [
    "OPENDOOR", "INVITATION HOMES", "AMERICAN HOMES 4 RENT",
    "PROGRESS RESIDENTIAL", "CERBERUS", "PRETIUM", "FIRSTKEY",
    "TRICON", "AMHERST", "STARWOOD", "COLONY", "TOLL SOUTHEAST",
    "TOLL BROTHERS", "LENNAR", "PULTE", "MERITAGE", "NVR ",
    "D.R. HORTON", "DRB GROUP", "RYAN HOMES",
    "LIMITED PARTNERSHIP", "BORROWER", "CONREX", "SFR PROPERTY",
    "SMARTRESI", "PURCHASING FUND", "OPERATING CO",
]


def is_institutional(name: str) -> bool:
    upper = str(name).upper()
    return any(kw in upper for kw in INSTITUTIONAL_KEYWORDS)


def load_and_prepare(csv_path: Path) -> pd.DataFrame:
    """Load property data and prepare for diffing."""
    df = pd.read_csv(csv_path, dtype=str)

    # Standardize columns we need
    df["sale_date"] = df["sale_date"].fillna("")
    df["icp_score"] = pd.to_numeric(df.get("icp_score", 0), errors="coerce").fillna(0)
    df["icp_tier"] = df.get("icp_tier", "").fillna("")
    df["icp_segment"] = df.get("icp_segment", "").fillna("")

    return df


def build_owner_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate property data to owner level."""
    grouped = df.groupby("owner_name_1", as_index=False).agg(
        property_count=("parcel_id", "count"),
        cities=("prop_city", lambda x: "|".join(sorted(set(str(v) for v in x if str(v) != "nan")))),
        max_score=("icp_score", "max"),
        tier=("icp_tier", "first"),
        segment=("icp_segment", "first"),
        parcels=("parcel_id", lambda x: "|".join(sorted(str(v) for v in x if str(v) != "nan"))),
        latest_sale=("sale_date", lambda x: max((str(v) for v in x if str(v) not in ("", "nan")), default="")),
        addresses=("prop_street", lambda x: "|".join(str(v) for v in x if str(v) != "nan")),
    )
    return grouped


def detect_changes(prev: pd.DataFrame, curr: pd.DataFrame) -> list:
    """
    Compare previous and current owner summaries to detect changes.
    Returns list of alert dicts.
    """
    alerts = []

    prev_owners = set(prev["owner_name_1"])
    curr_owners = set(curr["owner_name_1"])

    # Index for fast lookup
    prev_idx = prev.set_index("owner_name_1")
    curr_idx = curr.set_index("owner_name_1")

    # --- Owners in both snapshots: check for changes ---
    common = prev_owners & curr_owners
    for owner in common:
        if is_institutional(owner):
            continue

        p = prev_idx.loc[owner]
        c = curr_idx.loc[owner]

        prev_count = int(p["property_count"])
        curr_count = int(c["property_count"])
        prev_parcels = set(str(p["parcels"]).split("|"))
        curr_parcels = set(str(c["parcels"]).split("|"))

        # New properties acquired
        new_parcels = curr_parcels - prev_parcels
        lost_parcels = prev_parcels - curr_parcels

        if new_parcels and curr_count > prev_count:
            # Find the new addresses
            new_addresses = []
            for parcel in new_parcels:
                # Look up address in current data
                addr_match = c.get("addresses", "")
                new_addresses.append(parcel)

            alert = {
                "alert_type": "NEW_PURCHASE",
                "owner": owner,
                "detail": f"Acquired {len(new_parcels)} new propert{'y' if len(new_parcels) == 1 else 'ies'} (portfolio: {prev_count} → {curr_count})",
                "prev_count": prev_count,
                "curr_count": curr_count,
                "new_parcels": list(new_parcels),
                "cities": c["cities"],
                "segment": c["segment"],
                "tier": c["tier"],
                "score": float(c["max_score"]),
                "significance": 8 if curr_count >= 5 else 6,
            }

            # Boost significance for high-velocity or tier upgrades
            if curr_count >= 5 and prev_count < 5:
                alert["alert_type"] = "PORTFOLIO_GROWTH"
                alert["detail"] += " — crossed 5-property threshold"
                alert["significance"] = 9

            alerts.append(alert)

        if lost_parcels and curr_count < prev_count:
            alerts.append({
                "alert_type": "DISPOSITION",
                "owner": owner,
                "detail": f"Sold {len(lost_parcels)} propert{'y' if len(lost_parcels) == 1 else 'ies'} (portfolio: {prev_count} → {curr_count})",
                "prev_count": prev_count,
                "curr_count": curr_count,
                "lost_parcels": list(lost_parcels),
                "cities": c["cities"],
                "segment": c["segment"],
                "tier": c["tier"],
                "score": float(c["max_score"]),
                "significance": 7,
            })

        # Tier changes
        prev_tier = str(p["tier"])
        curr_tier = str(c["tier"])
        if prev_tier != curr_tier and prev_tier and curr_tier:
            alerts.append({
                "alert_type": "TIER_CHANGE",
                "owner": owner,
                "detail": f"Moved from {prev_tier} to {curr_tier}",
                "prev_count": prev_count,
                "curr_count": curr_count,
                "cities": c["cities"],
                "segment": c["segment"],
                "tier": curr_tier,
                "score": float(c["max_score"]),
                "significance": 5,
            })

    # --- New multi-property owners (not in previous snapshot) ---
    new_owners = curr_owners - prev_owners
    for owner in new_owners:
        if is_institutional(owner):
            continue

        c = curr_idx.loc[owner]
        count = int(c["property_count"])

        if count >= 2:
            alerts.append({
                "alert_type": "NEW_INVESTOR",
                "owner": owner,
                "detail": f"New multi-property investor detected — {count} properties",
                "prev_count": 0,
                "curr_count": count,
                "cities": c["cities"],
                "segment": c["segment"],
                "tier": c["tier"],
                "score": float(c["max_score"]),
                "significance": 7 if count >= 3 else 5,
            })

    # Sort by significance descending
    alerts.sort(key=lambda a: a["significance"], reverse=True)

    return alerts


def build_html_digest(alerts: list, market: str, prev_date: str, curr_date: str) -> str:
    """Build an HTML email digest from alerts."""

    if not alerts:
        return "<p>No significant changes detected this period.</p>"

    # Count by type
    type_counts = {}
    for a in alerts:
        t = a["alert_type"]
        type_counts[t] = type_counts.get(t, 0) + 1

    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
  body {{ font-family: 'Inter', Arial, sans-serif; color: #1C1917; max-width: 640px; margin: 0 auto; padding: 20px; }}
  .header {{ background: linear-gradient(135deg, #1b262c, #366F78); color: white; padding: 20px 24px; border-radius: 8px; margin-bottom: 20px; }}
  .header h1 {{ font-size: 18px; margin: 0 0 4px 0; }}
  .header p {{ font-size: 13px; opacity: 0.8; margin: 0; }}
  .summary {{ display: flex; gap: 12px; margin-bottom: 20px; }}
  .summary-card {{ background: #F5F5F4; border: 1px solid #E7E5E4; border-radius: 6px; padding: 12px 16px; flex: 1; text-align: center; }}
  .summary-card .num {{ font-size: 24px; font-weight: 700; color: #366F78; }}
  .summary-card .label {{ font-size: 11px; color: #78716C; text-transform: uppercase; }}
  .alert {{ border-left: 4px solid #366F78; background: #F5F5F4; border-radius: 0 6px 6px 0; padding: 12px 16px; margin-bottom: 10px; }}
  .alert.high {{ border-left-color: #DC2626; }}
  .alert.medium {{ border-left-color: #D97706; }}
  .alert-type {{ font-size: 10px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; color: #78716C; }}
  .alert-owner {{ font-size: 14px; font-weight: 600; color: #1C1917; margin: 2px 0; }}
  .alert-detail {{ font-size: 12px; color: #44403C; }}
  .alert-meta {{ font-size: 11px; color: #78716C; margin-top: 4px; }}
  .footer {{ margin-top: 24px; padding-top: 12px; border-top: 1px solid #E7E5E4; font-size: 11px; color: #78716C; }}
</style>
</head>
<body>

<div class="header">
  <h1>Investor Activity Alert — {market.title()} County</h1>
  <p>Period: {prev_date} to {curr_date} &bull; {len(alerts)} signals detected</p>
</div>

<div class="summary">
"""
    for alert_type, label in [("NEW_PURCHASE", "New Purchases"), ("NEW_INVESTOR", "New Investors"),
                               ("DISPOSITION", "Dispositions"), ("PORTFOLIO_GROWTH", "Portfolio Growth")]:
        count = type_counts.get(alert_type, 0)
        html += f'  <div class="summary-card"><div class="num">{count}</div><div class="label">{label}</div></div>\n'

    html += "</div>\n\n"

    # Alert list (top 25)
    for alert in alerts[:25]:
        sig = alert["significance"]
        css_class = "high" if sig >= 8 else "medium" if sig >= 6 else ""
        html += f"""<div class="alert {css_class}">
  <div class="alert-type">{alert["alert_type"].replace("_", " ")}</div>
  <div class="alert-owner">{alert["owner"]}</div>
  <div class="alert-detail">{alert["detail"]}</div>
  <div class="alert-meta">{alert["segment"]} &bull; Score: {alert["score"]:.0f} &bull; {alert["cities"]}</div>
</div>
"""

    if len(alerts) > 25:
        html += f'<p style="color:#78716C;font-size:12px;">+ {len(alerts) - 25} more alerts in full report</p>\n'

    html += f"""
<div class="footer">
  DSCR Lead Intelligence &bull; Stillmind Creative<br>
  This is an automated alert. Data sourced from public property records.
</div>

</body>
</html>"""

    return html


def save_snapshot(df: pd.DataFrame, market: str, label: str = ""):
    """Save a snapshot for future diffing."""
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    tag = label if label else TODAY_STR
    path = SNAPSHOT_DIR / f"snapshot_{market}_{tag}.csv"
    df.to_csv(path, index=False)
    print(f"  Snapshot saved: {path.name}")
    return path


def get_latest_snapshot(market: str) -> Path:
    """Find the most recent snapshot for a market."""
    if not SNAPSHOT_DIR.exists():
        return None
    snapshots = sorted(SNAPSHOT_DIR.glob(f"snapshot_{market}_*.csv"))
    return snapshots[-1] if snapshots else None


def main():
    parser = argparse.ArgumentParser(description="Market monitor — detect investor activity changes")
    parser.add_argument("--market", required=True, help="Market: wake, fl")
    parser.add_argument("--baseline", action="store_true",
                        help="Create baseline snapshot (first run)")
    parser.add_argument("--fresh", type=str, default="",
                        help="Path to fresh data file (default: filtered/{market}_qualified.csv)")
    parser.add_argument("--email", type=str, default="",
                        help="Email address for digest delivery (generates HTML only for now)")
    parser.add_argument("--simulate", action="store_true",
                        help="Simulate changes for demo purposes (modifies a few records)")
    args = parser.parse_args()

    print(f"\n{'='*60}")
    print(f"  STEP 21: MARKET MONITOR")
    print(f"  Market: {args.market.upper()}")
    print(f"  Date: {TODAY_STR}")
    print(f"{'='*60}")

    # Load current data
    if args.fresh:
        fresh_path = Path(args.fresh)
    else:
        fresh_path = FILTERED_DIR / f"{args.market}_qualified.csv"

    if not fresh_path.exists():
        print(f"  ERROR: Data not found: {fresh_path}")
        sys.exit(1)

    current_df = load_and_prepare(fresh_path)
    print(f"\n  Current data: {len(current_df):,} properties")

    current_summary = build_owner_summary(current_df)
    print(f"  Unique owners: {len(current_summary):,}")

    if args.baseline:
        save_snapshot(current_summary, args.market, "baseline")
        print(f"\n  Baseline created. Run again without --baseline to detect changes.")
        print()
        return

    # Load previous snapshot
    prev_path = get_latest_snapshot(args.market)
    if not prev_path:
        print(f"\n  ERROR: No previous snapshot found.")
        print(f"  Run with --baseline first to create one.")
        sys.exit(1)

    print(f"  Previous snapshot: {prev_path.name}")
    prev_summary = pd.read_csv(prev_path, dtype=str)
    prev_summary["property_count"] = pd.to_numeric(prev_summary["property_count"], errors="coerce").fillna(0).astype(int)
    prev_summary["max_score"] = pd.to_numeric(prev_summary["max_score"], errors="coerce").fillna(0)
    print(f"  Previous owners: {len(prev_summary):,}")

    # Simulate changes for demo if requested
    if args.simulate:
        print(f"\n  SIMULATING CHANGES for demo...")
        # Pick a few owners and modify their data
        import random
        random.seed(42)

        # Simulate: add 2 properties to an existing owner
        multi_owners = current_summary[
            (current_summary["property_count"].astype(int) >= 3) &
            (current_summary["property_count"].astype(int) <= 8) &
            (~current_summary["owner_name_1"].apply(is_institutional))
        ]
        if len(multi_owners) >= 5:
            # Pick 3 owners to "grow"
            sample = multi_owners.sample(3, random_state=42)
            for idx in sample.index:
                old_count = int(current_summary.loc[idx, "property_count"])
                current_summary.loc[idx, "property_count"] = old_count + random.randint(1, 2)
                current_summary.loc[idx, "parcels"] = str(current_summary.loc[idx, "parcels"]) + f"|SIM{random.randint(1000,9999)}"
                print(f"    Simulated growth: {current_summary.loc[idx, 'owner_name_1'][:40]} ({old_count} → {current_summary.loc[idx, 'property_count']})")

            # Pick 2 owners to "sell"
            sellers = multi_owners.drop(sample.index).sample(2, random_state=99)
            for idx in sellers.index:
                old_count = int(current_summary.loc[idx, "property_count"])
                new_count = max(1, old_count - 1)
                current_summary.loc[idx, "property_count"] = new_count
                parcels = str(current_summary.loc[idx, "parcels"]).split("|")
                if len(parcels) > 1:
                    removed = parcels.pop()
                    current_summary.loc[idx, "parcels"] = "|".join(parcels)
                print(f"    Simulated sale: {current_summary.loc[idx, 'owner_name_1'][:40]} ({old_count} → {new_count})")

            # Add 3 "new" investors
            for i in range(3):
                new_owner = f"SIMULATED INVESTOR {i+1}"
                new_row = {
                    "owner_name_1": new_owner,
                    "property_count": random.randint(2, 4),
                    "cities": "RALEIGH",
                    "max_score": random.randint(35, 55),
                    "tier": "Tier 1 — Hot" if random.random() > 0.5 else "Tier 2 — Warm",
                    "segment": "Growing Portfolio (2-4)",
                    "parcels": f"SIM{random.randint(10000,99999)}|SIM{random.randint(10000,99999)}",
                    "latest_sale": "2026-03",
                    "addresses": "123 SIMULATED ST|456 SIMULATED AVE",
                }
                current_summary = pd.concat([current_summary, pd.DataFrame([new_row])], ignore_index=True)
                print(f"    Simulated new investor: {new_owner}")

    # Detect changes
    print(f"\n  Detecting changes...")
    alerts = detect_changes(prev_summary, current_summary)
    print(f"  Alerts generated: {len(alerts)}")

    if alerts:
        # Print top alerts
        print(f"\n  Top alerts:")
        for a in alerts[:10]:
            sig_bar = "#" * a["significance"]
            print(f"    [{a['alert_type']:18s}] {a['owner'][:35]}")
            print(f"      {a['detail']}")

        # Save alerts CSV
        ALERTS_DIR.mkdir(parents=True, exist_ok=True)
        alerts_df = pd.DataFrame(alerts)
        alerts_csv = ALERTS_DIR / f"alerts_{args.market}_{TODAY_STR}.csv"
        alerts_df.to_csv(alerts_csv, index=False)
        print(f"\n  Alerts CSV: {alerts_csv}")

        # Build and save HTML digest
        prev_date = prev_path.stem.split("_")[-1]
        digest_html = build_html_digest(alerts, args.market, prev_date, TODAY_STR)
        digest_path = ALERTS_DIR / f"digest_{args.market}_{TODAY_STR}.html"
        with open(digest_path, "w") as f:
            f.write(digest_html)
        print(f"  HTML digest: {digest_path}")

        if args.email:
            print(f"\n  Email delivery not yet configured.")
            print(f"  To enable: add SENDGRID_API_KEY to scrape/.env")
            print(f"  Digest HTML is ready to send manually: {digest_path}")

    else:
        print(f"\n  No significant changes detected.")

    # Save current as new snapshot
    save_snapshot(current_summary, args.market)

    print(f"\n  Next run will diff against today's snapshot.")
    print()


if __name__ == "__main__":
    main()
