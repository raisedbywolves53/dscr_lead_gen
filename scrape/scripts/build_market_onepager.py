#!/usr/bin/env python3
"""
build_market_onepager.py — Generate a market universe one-pager HTML for sales demos.

Usage:
    python scrape/scripts/build_market_onepager.py

Reads:
    scrape/data/filtered/wake_all_scored.csv
    scrape/data/filtered/wake_qualified.csv

Outputs:
    sales/demo_tearsheets/market_universe_wake.html
"""

import os
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ALL_SCORED = ROOT / "scrape/data/filtered/wake_all_scored.csv"
QUALIFIED = ROOT / "scrape/data/filtered/wake_qualified.csv"
OUTPUT = ROOT / "sales/demo_tearsheets/market_universe_wake.html"


def compute_stats():
    """Compute all stats from the data files."""
    all_df = pd.read_csv(ALL_SCORED, dtype=str)
    qual_df = pd.read_csv(QUALIFIED, dtype=str)

    stats = {}

    # 1. Totals
    stats["total_scored"] = len(all_df)
    stats["total_qualified"] = len(qual_df)
    stats["discard_count"] = stats["total_scored"] - stats["total_qualified"]

    # 2. Tier breakdown
    tier_counts = qual_df["icp_tier"].value_counts()
    tiers = []
    for label, key_fragment, color in [
        ("Tier 1 — Hot", "Hot", "#DC2626"),
        ("Tier 2 — Warm", "Warm", "#D97706"),
        ("Tier 3 — Nurture", "Nurture", "#366F78"),
    ]:
        matches = [k for k in tier_counts.index if key_fragment in k]
        count = int(tier_counts[matches[0]]) if matches else 0
        pct = round(100 * count / stats["total_qualified"], 1)
        tiers.append({"label": label, "count": count, "pct": pct, "color": color})
    stats["tiers"] = tiers

    # 3. Top segments
    seg_counts = qual_df["icp_segment"].value_counts()
    segments = []
    for seg_name, count in seg_counts.head(8).items():
        segments.append({"name": seg_name, "count": int(count)})
    stats["segments"] = segments

    # 4. Top cities
    city_counts = qual_df["prop_city"].value_counts()
    cities = []
    for city, count in city_counts.head(10).items():
        cities.append({"name": city.title(), "count": int(count)})
    stats["cities"] = cities

    # 5. Multi-property investors
    pc = pd.to_numeric(qual_df["portfolio_count"], errors="coerce")
    stats["portfolio_2plus"] = int((pc >= 2).sum())
    stats["portfolio_5plus"] = int((pc >= 5).sum())
    stats["portfolio_10plus"] = int((pc >= 10).sum())

    # 6. Recent activity (2024+)
    sd = qual_df["sale_date"].dropna()
    stats["recent_purchases"] = int((sd >= "2024-01").sum())

    # 7. Cash buyers
    cash_col = qual_df["is_cash_buyer"].str.lower()
    stats["cash_buyers"] = int((cash_col == "true").sum())

    # 8. LLC/entity owned
    llc_col = qual_df["is_llc"].str.lower()
    stats["llc_count"] = int((llc_col == "true").sum())

    # 9. Out-of-state
    oos_col = qual_df["is_absentee"].str.lower()
    stats["absentee_count"] = int((oos_col == "true").sum())

    # 10. Median property value
    vals = pd.to_numeric(qual_df["just_value"], errors="coerce").dropna()
    stats["median_value"] = int(vals.median())

    return stats


def fmt(n):
    """Format integer with commas."""
    return f"{n:,}"


def build_html(stats):
    """Generate the one-pager HTML."""
    tiers_html = ""
    for t in stats["tiers"]:
        tiers_html += f"""
        <div class="tier-row">
          <div class="tier-badge" style="background:{t['color']}">{t['label'].split('—')[1].strip()}</div>
          <div class="tier-label">{t['label']}</div>
          <div class="tier-count">{fmt(t['count'])}</div>
          <div class="tier-pct">{t['pct']}%</div>
          <div class="tier-bar-bg"><div class="tier-bar" style="width:{t['pct']}%;background:{t['color']}"></div></div>
        </div>"""

    segments_html = ""
    max_seg = stats["segments"][0]["count"] if stats["segments"] else 1
    for s in stats["segments"]:
        bar_w = round(100 * s["count"] / max_seg)
        segments_html += f"""
        <div class="seg-row">
          <div class="seg-name">{s['name']}</div>
          <div class="seg-bar-bg"><div class="seg-bar" style="width:{bar_w}%"></div></div>
          <div class="seg-count">{fmt(s['count'])}</div>
        </div>"""

    cities_html = ""
    max_city = stats["cities"][0]["count"] if stats["cities"] else 1
    for c in stats["cities"]:
        bar_w = round(100 * c["count"] / max_city)
        cities_html += f"""
        <div class="seg-row">
          <div class="seg-name">{c['name']}</div>
          <div class="seg-bar-bg"><div class="seg-bar city-bar" style="width:{bar_w}%"></div></div>
          <div class="seg-count">{fmt(c['count'])}</div>
        </div>"""

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Wake County Market Universe — Stillmind Creative</title>
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}

  :root {{
    --ocean: #366F78;
    --deep-ocean: #1b262c;
    --seafoam: #d4e8eb;
    --gold: #B4873F;
    --charcoal: #1C1917;
    --stone: #44403C;
    --pebble: #78716C;
    --mist: #E7E5E4;
    --cloud: #F5F5F4;
    --white: #FAFAF9;
    --sage: #16A34A;
    --amber: #D97706;
    --coral: #DC2626;
  }}

  @page {{
    size: letter;
    margin: 0.5in;
  }}

  body {{
    font-family: 'Inter', system-ui, sans-serif;
    color: var(--charcoal);
    background: var(--white);
    max-width: 8.5in;
    margin: 0 auto;
    padding: 28px 32px;
    font-size: 13px;
    line-height: 1.5;
  }}

  /* ── Header ── */
  .header {{
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    border-bottom: 3px solid var(--ocean);
    padding-bottom: 14px;
    margin-bottom: 24px;
  }}
  .header-left h1 {{
    font-family: 'DM Sans', sans-serif;
    font-size: 22px;
    font-weight: 700;
    color: var(--charcoal);
    letter-spacing: -0.025em;
  }}
  .header-left .subtitle {{
    font-size: 13px;
    color: var(--pebble);
    margin-top: 2px;
  }}
  .header-right {{
    text-align: right;
  }}
  .header-right .brand {{
    font-family: 'DM Sans', sans-serif;
    font-size: 11px;
    font-weight: 600;
    color: var(--ocean);
    text-transform: uppercase;
    letter-spacing: 0.1em;
  }}
  .header-right .date {{
    font-size: 11px;
    color: var(--pebble);
    margin-top: 2px;
  }}
  .header-right .conf {{
    font-size: 9px;
    color: var(--coral);
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-top: 4px;
  }}

  /* ── Hero ── */
  .hero {{
    background: linear-gradient(135deg, var(--charcoal) 0%, #292524 100%);
    color: white;
    border-radius: 10px;
    padding: 32px 36px;
    margin-bottom: 24px;
    text-align: center;
  }}
  .hero .hero-number {{
    font-family: 'DM Sans', sans-serif;
    font-size: 52px;
    font-weight: 700;
    letter-spacing: -0.03em;
    color: var(--seafoam);
    line-height: 1.1;
  }}
  .hero .hero-label {{
    font-size: 16px;
    font-weight: 500;
    color: #D6D3D1;
    margin-top: 6px;
    letter-spacing: 0.02em;
  }}
  .hero .hero-sub {{
    font-size: 12px;
    color: #A8A29E;
    margin-top: 10px;
  }}
  .hero .hero-sub span {{
    color: var(--seafoam);
    font-weight: 600;
  }}

  /* ── Stat Cards ── */
  .stat-grid {{
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 14px;
    margin-bottom: 24px;
  }}
  .stat-card {{
    background: var(--cloud);
    border-radius: 8px;
    padding: 16px 18px;
    text-align: center;
  }}
  .stat-card .stat-value {{
    font-family: 'DM Sans', sans-serif;
    font-size: 26px;
    font-weight: 700;
    color: var(--charcoal);
    letter-spacing: -0.02em;
  }}
  .stat-card .stat-label {{
    font-size: 11px;
    color: var(--pebble);
    margin-top: 2px;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    font-weight: 500;
  }}

  /* ── Section headers ── */
  .section-header {{
    font-family: 'DM Sans', sans-serif;
    font-size: 15px;
    font-weight: 700;
    color: var(--charcoal);
    margin-bottom: 12px;
    padding-bottom: 6px;
    border-bottom: 2px solid var(--mist);
    letter-spacing: -0.01em;
  }}

  /* ── Tier Breakdown ── */
  .tier-section {{
    margin-bottom: 24px;
  }}
  .tier-row {{
    display: grid;
    grid-template-columns: 58px 150px 80px 48px 1fr;
    align-items: center;
    gap: 8px;
    padding: 8px 0;
    border-bottom: 1px solid var(--mist);
  }}
  .tier-badge {{
    font-size: 10px;
    font-weight: 700;
    color: white;
    padding: 3px 8px;
    border-radius: 4px;
    text-transform: uppercase;
    text-align: center;
    letter-spacing: 0.05em;
  }}
  .tier-label {{
    font-size: 12px;
    font-weight: 500;
    color: var(--stone);
  }}
  .tier-count {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 13px;
    font-weight: 500;
    text-align: right;
  }}
  .tier-pct {{
    font-size: 11px;
    color: var(--pebble);
    text-align: right;
  }}
  .tier-bar-bg {{
    background: var(--mist);
    border-radius: 3px;
    height: 8px;
    overflow: hidden;
  }}
  .tier-bar {{
    height: 100%;
    border-radius: 3px;
    transition: width 0.3s;
  }}

  /* ── Two-column layout ── */
  .two-col {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 28px;
    margin-bottom: 24px;
  }}

  /* ── Segment / City bars ── */
  .seg-row {{
    display: grid;
    grid-template-columns: 170px 1fr 70px;
    align-items: center;
    gap: 10px;
    padding: 5px 0;
    border-bottom: 1px solid #f0efee;
  }}
  .seg-name {{
    font-size: 12px;
    font-weight: 500;
    color: var(--stone);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }}
  .seg-bar-bg {{
    background: var(--mist);
    border-radius: 3px;
    height: 7px;
    overflow: hidden;
  }}
  .seg-bar {{
    height: 100%;
    border-radius: 3px;
    background: var(--ocean);
  }}
  .seg-bar.city-bar {{
    background: var(--gold);
  }}
  .seg-count {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 12px;
    text-align: right;
    color: var(--stone);
  }}

  /* ── Portfolio Grid ── */
  .portfolio-grid {{
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 12px;
    margin-bottom: 24px;
  }}
  .portfolio-card {{
    background: var(--cloud);
    border-radius: 8px;
    padding: 16px;
    text-align: center;
    border-left: 4px solid var(--ocean);
  }}
  .portfolio-card .pf-value {{
    font-family: 'DM Sans', sans-serif;
    font-size: 28px;
    font-weight: 700;
    color: var(--deep-ocean);
  }}
  .portfolio-card .pf-label {{
    font-size: 11px;
    color: var(--pebble);
    margin-top: 2px;
    font-weight: 500;
  }}

  /* ── CTA Section ── */
  .cta-section {{
    background: linear-gradient(135deg, #1b262c 0%, #366F78 100%);
    border-radius: 10px;
    padding: 28px 32px;
    color: white;
    margin-top: 8px;
  }}
  .cta-section h2 {{
    font-family: 'DM Sans', sans-serif;
    font-size: 18px;
    font-weight: 700;
    margin-bottom: 14px;
    letter-spacing: -0.01em;
  }}
  .cta-section p {{
    font-size: 13px;
    line-height: 1.7;
    color: #CCFBF1;
    margin-bottom: 10px;
  }}
  .cta-section .highlight {{
    color: white;
    font-weight: 600;
  }}
  .cta-bullets {{
    list-style: none;
    padding: 0;
    margin: 14px 0 0 0;
  }}
  .cta-bullets li {{
    font-size: 13px;
    color: #CCFBF1;
    padding: 4px 0;
    padding-left: 20px;
    position: relative;
  }}
  .cta-bullets li::before {{
    content: "\\2713";
    position: absolute;
    left: 0;
    color: var(--seafoam);
    font-weight: 700;
  }}

  /* ── Footer ── */
  .footer {{
    margin-top: 20px;
    padding-top: 12px;
    border-top: 1px solid var(--mist);
    display: flex;
    justify-content: space-between;
    font-size: 10px;
    color: var(--pebble);
  }}

  @media print {{
    body {{ padding: 0; }}
    .cta-section {{ break-inside: avoid; }}
  }}
</style>
</head>
<body>

<!-- Header -->
<div class="header">
  <div class="header-left">
    <h1>Wake County Market Universe</h1>
    <div class="subtitle">Investment Property Intelligence &mdash; Raleigh-Cary Metro</div>
  </div>
  <div class="header-right">
    <div class="brand">Stillmind Creative</div>
    <div class="date">Prepared March 2026</div>
    <div class="conf">Prepared for Northside Realty</div>
  </div>
</div>

<!-- Hero -->
<div class="hero">
  <div class="hero-number">{fmt(stats['total_qualified'])}</div>
  <div class="hero-label">Qualified Investor Profiles in Wake County</div>
  <div class="hero-sub">Scored from <span>{fmt(stats['total_scored'])}</span> total property records &mdash; {fmt(stats['discard_count'])} filtered out as non-investor or owner-occupied</div>
</div>

<!-- Stat Cards -->
<div class="stat-grid">
  <div class="stat-card">
    <div class="stat-value">{fmt(stats['tiers'][0]['count'])}</div>
    <div class="stat-label">Tier 1 &mdash; Hot Leads</div>
  </div>
  <div class="stat-card">
    <div class="stat-value">{fmt(stats['recent_purchases'])}</div>
    <div class="stat-label">Purchased 2024&ndash;2026</div>
  </div>
  <div class="stat-card">
    <div class="stat-value">{fmt(stats['llc_count'])}</div>
    <div class="stat-label">LLC / Entity Owned</div>
  </div>
  <div class="stat-card">
    <div class="stat-value">{fmt(stats['absentee_count'])}</div>
    <div class="stat-label">Absentee Owners</div>
  </div>
</div>

<!-- Tier Breakdown -->
<div class="tier-section">
  <div class="section-header">Lead Tier Distribution</div>
  {tiers_html}
</div>

<!-- Two-column: Segments + Cities -->
<div class="two-col">
  <div>
    <div class="section-header">Investor Segments</div>
    {segments_html}
  </div>
  <div>
    <div class="section-header">Top Cities by Qualified Leads</div>
    {cities_html}
  </div>
</div>

<!-- Portfolio Depth -->
<div class="section-header">Multi-Property Investors</div>
<div class="portfolio-grid">
  <div class="portfolio-card">
    <div class="pf-value">{fmt(stats['portfolio_2plus'])}</div>
    <div class="pf-label">Own 2+ Properties</div>
  </div>
  <div class="portfolio-card">
    <div class="pf-value">{fmt(stats['portfolio_5plus'])}</div>
    <div class="pf-label">Own 5+ Properties</div>
  </div>
  <div class="portfolio-card">
    <div class="pf-value">{fmt(stats['portfolio_10plus'])}</div>
    <div class="pf-label">Own 10+ Properties</div>
  </div>
</div>

<!-- CTA: What This Means -->
<div class="cta-section">
  <h2>What This Means for Northside Realty</h2>
  <p>
    Wake County has <span class="highlight">{fmt(stats['total_qualified'])} verified investment property owners</span> &mdash;
    and <span class="highlight">{fmt(stats['tiers'][0]['count'])} are Tier 1 hot leads</span> with active portfolios,
    LLC structures, and recent transaction activity. These are investors who are buying, refinancing, and growing right now.
  </p>
  <p>
    For a brokerage with 100+ agents, this is a territory-wide investor map. Instead of cold-calling blind lists,
    your agents get scored, segmented profiles &mdash; each one tagged by opportunity type, portfolio depth, and activity signals.
  </p>
  <ul class="cta-bullets">
    <li><span class="highlight">{fmt(stats['portfolio_5plus'])} portfolio landlords</span> (5+ properties) &mdash; listing and buyer-side opportunities at scale</li>
    <li><span class="highlight">{fmt(stats['recent_purchases'])} recent buyers</span> (2024&ndash;2026) &mdash; actively deploying capital in your market right now</li>
    <li><span class="highlight">{fmt(stats['llc_count'])} LLC/entity investors</span> &mdash; sophisticated operators who transact repeatedly</li>
    <li>Every profile enrichable with contact info, mortgage details, rental estimates, and portfolio mapping</li>
  </ul>
</div>

<!-- Footer -->
<div class="footer">
  <div>Stillmind Creative &mdash; Investor Intelligence Platform</div>
  <div>Data: Wake County Tax Records, NC OneMap &bull; Scored via ICP Pipeline v3</div>
</div>

</body>
</html>"""

    return html


def main():
    print("Computing stats from Wake County data...")
    stats = compute_stats()

    print(f"  Total scored:    {fmt(stats['total_scored'])}")
    print(f"  Total qualified: {fmt(stats['total_qualified'])}")
    for t in stats["tiers"]:
        print(f"  {t['label']}: {fmt(t['count'])} ({t['pct']}%)")
    print(f"  Recent purchases (2024+): {fmt(stats['recent_purchases'])}")
    print(f"  Multi-property 2+/5+/10+: {fmt(stats['portfolio_2plus'])} / {fmt(stats['portfolio_5plus'])} / {fmt(stats['portfolio_10plus'])}")
    print(f"  LLC/entity: {fmt(stats['llc_count'])}")
    print(f"  Absentee: {fmt(stats['absentee_count'])}")

    html = build_html(stats)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(html, encoding="utf-8")
    print(f"\nWrote: {OUTPUT}")
    print(f"  Size: {OUTPUT.stat().st_size:,} bytes")


if __name__ == "__main__":
    main()
