"""
Build Agent/Broker Tearsheets
==============================

Generates HTML investor intelligence briefs from pipeline data:
  - ATTOM-enriched property data (showcase_7ep_{market}.csv)
  - Investment profiles (investment_profiles_{market}.csv from Step 17)
  - Outreach playbooks (playbooks_{market}.json from Step 18)

Output: One HTML file per investor in sales/demo_tearsheets/

These are AGENT/BROKER channel tearsheets (RESPA compliant):
  - NO lender names, loan amounts, interest rates, or mortgage data
  - Focus: portfolio composition, transaction velocity, geographic focus,
    rental estimates, permits, and approach strategy

Usage:
    python scripts/build_agent_tearsheets.py --market wake
    python scripts/build_agent_tearsheets.py --market wake --investors "CLEAR CONSTRUCTION GROUP LLC"
"""

import argparse
import json
import sys
from datetime import date
from pathlib import Path

import pandas as pd

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent
DATA_DIR = PROJECT_DIR / "data"
DEMO_DIR = DATA_DIR / "demo"
OUTPUT_DIR = PROJECT_DIR.parent / "sales" / "demo_tearsheets"

TODAY = date.today()


def _float(val, default=0.0):
    try:
        v = float(str(val).replace(",", "").replace("$", "").strip() or 0)
        return default if pd.isna(v) else v
    except (ValueError, TypeError):
        return default


def _fmt_money(val, compact=False):
    v = _float(val)
    if v == 0:
        return "N/A"
    if compact:
        if v >= 1_000_000:
            return f"${v/1_000_000:.1f}M"
        elif v >= 1_000:
            return f"${v/1_000:.0f}K"
    return f"${v:,.0f}"


def _fmt_date(date_str):
    if not date_str or str(date_str).strip() in ("", "nan", "None"):
        return "N/A"
    s = str(date_str).strip()[:10]
    for fmt_in, fmt_out in [("%Y-%m-%d", "%b '%y"), ("%m/%d/%Y", "%b '%y"), ("%Y-%m", "%b '%y")]:
        try:
            from datetime import datetime
            return datetime.strptime(s, fmt_in).strftime(fmt_out)
        except ValueError:
            continue
    return s


def _safe(val, default=""):
    s = str(val).strip()
    return default if s in ("", "nan", "None", "NaT") else s


def build_tearsheet(profile: dict, properties: pd.DataFrame, playbook: dict) -> str:
    """Build a complete HTML tearsheet for one investor."""

    name = profile.get("investor_name", "Unknown")
    thesis = profile.get("investment_thesis", "General Investor")
    thesis_short = thesis.split(" — ")[0] if " — " in thesis else thesis

    n_props = int(_float(profile.get("property_count", 0)))
    total_val = _float(profile.get("portfolio_total_value", 0))
    price_range = _safe(profile.get("price_range"), "N/A")
    tpy = _float(profile.get("transactions_per_year", 0))
    hold_yrs = _safe(profile.get("avg_hold_years"), "N/A")
    hold_strategy = _safe(profile.get("hold_strategy"), "")
    financing = _safe(profile.get("financing_pattern"), "").replace("_", " ").title()
    cash_pct = int(_float(profile.get("cash_buyer_pct", 0)))
    geo_primary = _safe(profile.get("geo_primary_city"), "")
    geo_count = int(_float(profile.get("geo_city_count", 0)))
    total_permits = int(_float(profile.get("total_permits", 0)))
    total_permit_val = _float(profile.get("total_permit_value", 0))
    total_monthly_rent = _float(profile.get("total_monthly_rent", 0))
    total_annual_rent = _float(profile.get("total_annual_rent", 0))
    total_equity = _float(profile.get("total_equity", 0))
    last_purchase = _safe(profile.get("last_purchase_date"), "")
    days_since = int(_float(profile.get("days_since_last_purchase", 0)))
    predicted_next = _safe(profile.get("predicted_next_purchase"), "")
    avg_months = _safe(profile.get("avg_months_between_purchases"), "")
    years_active = _safe(profile.get("years_active"), "")

    # Playbook content
    behavior = playbook.get("behavior_summary", "")
    angles = playbook.get("approach_angles", [])
    opening = playbook.get("opening_script", "")
    suggestions = playbook.get("strategic_suggestions", [])
    starters = playbook.get("conversation_starters", [])

    # Determine score tier (rough estimate from signals)
    tier_label = "Priority" if tpy >= 1.5 or n_props >= 5 else "Opportunity" if n_props >= 3 else "Watch List"
    score_est = min(95, int(n_props * 8 + tpy * 10 + (15 if cash_pct > 50 else 0) + (10 if total_permits > 5 else 0)))

    # Build property rows
    prop_rows = []
    for _, row in properties.iterrows():
        addr = _safe(row.get("address"), "Unknown")
        addr_parts = addr.split(",")
        street = addr_parts[0].strip() if addr_parts else addr
        city = addr_parts[1].strip() if len(addr_parts) >= 2 else ""
        # Clean city - remove state/zip if present
        city = city.split(",")[0].strip() if city else ""
        for suffix in [" NC", " FL"]:
            city = city.replace(suffix, "").strip()

        avm = _float(row.get("attom_avm_value"))
        rent = _float(row.get("attom_rent_estimate"))
        beds = _safe(row.get("attom_beds"), "")
        sqft = _safe(row.get("attom_sqft"), "")
        year_built = _safe(row.get("attom_year_built", row.get("attom_year_built_profile", "")), "")
        permits = int(_float(row.get("attom_permit_count", 0)))
        last_sale = _safe(row.get("attom_last_sale_date"), "")
        last_price = _float(row.get("attom_last_sale_price"))
        is_cash = str(row.get("derived_cash_buyer", "")).lower() == "true"
        assessed = _float(row.get("attom_assessed_total"))
        equity = _float(row.get("derived_equity"))
        tax = _float(row.get("attom_annual_tax"))

        # Yield calc
        gross_yield = ""
        if rent > 0 and avm > 0:
            gy = (rent * 12 / avm) * 100
            gross_yield = f"{gy:.1f}%"

        # Tags
        tags = []
        if is_cash:
            tags.append(('tag-cash', f'CASH{" " + _fmt_money(last_price, True) if last_price > 0 else ""}'))
        if permits >= 5:
            tags.append(('tag-signal', f'{permits} Permits'))
        if _float(gross_yield.replace("%", "")) > 7:
            tags.append(('tag-signal', f'Yield {gross_yield}'))
        if last_sale and "2025" in last_sale or "2026" in last_sale:
            tags.append(('tag-hot', f'Recent {_fmt_date(last_sale)}'))

        prop_rows.append({
            "street": street, "city": city, "avm": avm, "rent": rent,
            "beds": beds, "sqft": sqft, "year_built": year_built,
            "permits": permits, "last_sale": last_sale, "last_price": last_price,
            "is_cash": is_cash, "assessed": assessed, "equity": equity,
            "tax": tax, "gross_yield": gross_yield, "tags": tags,
        })

    # Pick best property for deep dive (highest AVM with most data)
    deep_dive = max(prop_rows, key=lambda p: p["avm"]) if prop_rows else None

    # Signal banner headline
    signals = []
    if cash_pct >= 50:
        signals.append("Cash Buyer")
    if total_permits >= 5:
        signals.append(f"{total_permits} Permits")
    if tpy >= 2:
        signals.append(f"{tpy:.0f}+ Txns/Year")
    elif tpy >= 1:
        signals.append(f"{tpy:.1f} Txns/Year")
    if n_props >= 5:
        signals.append(f"{n_props} Properties")
    signal_headline = " | ".join(signals) if signals else thesis_short

    # --- BUILD HTML ---
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Investor Intelligence Brief &mdash; {name}</title>
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  :root {{
    --ocean: #0D9488; --deep-ocean: #0F766E; --seafoam: #99F6E4;
    --gold: #B4873F; --charcoal: #1C1917; --stone: #44403C;
    --pebble: #78716C; --mist: #E7E5E4; --cloud: #F5F5F4;
    --white: #FAFAF9; --sage: #16A34A; --amber: #D97706; --coral: #DC2626;
  }}
  @page {{ size: letter; margin: 0.5in; }}
  body {{
    font-family: 'Inter', system-ui, sans-serif; color: var(--charcoal);
    background: var(--white); max-width: 8.5in; margin: 0 auto;
    padding: 24px; font-size: 13px; line-height: 1.5;
  }}
  .header {{ display: flex; justify-content: space-between; align-items: flex-start;
    border-bottom: 3px solid var(--ocean); padding-bottom: 16px; margin-bottom: 20px; }}
  .header-left h1 {{ font-family: 'DM Sans', sans-serif; font-size: 22px;
    font-weight: 700; color: var(--charcoal); letter-spacing: -0.025em; }}
  .header-left .segment {{ display: inline-block; background: var(--ocean); color: white;
    font-size: 11px; font-weight: 600; padding: 3px 10px; border-radius: 4px;
    margin-top: 6px; letter-spacing: 0.05em; text-transform: uppercase; }}
  .header-right {{ text-align: right; }}
  .header-right .brand {{ font-family: 'DM Sans', sans-serif; font-size: 11px;
    color: var(--pebble); letter-spacing: 0.1em; text-transform: uppercase; }}
  .header-right .date {{ font-size: 11px; color: var(--pebble); margin-top: 2px; }}
  .score-badge {{ display: inline-flex; align-items: center; gap: 6px;
    background: var(--seafoam); color: var(--deep-ocean);
    font-family: 'JetBrains Mono', monospace; font-size: 13px; font-weight: 500;
    padding: 4px 12px; border-radius: 6px; margin-top: 8px; }}
  .signal-banner {{ background: linear-gradient(135deg, var(--deep-ocean), var(--ocean));
    color: white; border-radius: 8px; padding: 16px 20px; margin-bottom: 20px; }}
  .signal-banner h2 {{ font-family: 'DM Sans', sans-serif; font-size: 15px;
    font-weight: 600; margin-bottom: 4px; display: flex; align-items: center; gap: 8px; }}
  .signal-banner p {{ font-size: 13px; opacity: 0.92; line-height: 1.5; }}
  .stats-grid {{ display: grid; grid-template-columns: repeat(4, 1fr);
    gap: 12px; margin-bottom: 20px; }}
  .stat-card {{ background: var(--cloud); border: 1px solid var(--mist);
    border-radius: 8px; padding: 12px 14px; }}
  .stat-card .label {{ font-size: 10px; font-weight: 600; color: var(--pebble);
    text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 4px; }}
  .stat-card .value {{ font-family: 'JetBrains Mono', monospace; font-size: 18px;
    font-weight: 500; color: var(--charcoal); }}
  .stat-card .subtext {{ font-size: 11px; color: var(--stone); margin-top: 2px; }}
  .two-col {{ display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 20px; }}
  .section {{ margin-bottom: 16px; }}
  .section-title {{ font-family: 'DM Sans', sans-serif; font-size: 13px; font-weight: 600;
    color: var(--ocean); text-transform: uppercase; letter-spacing: 0.08em;
    margin-bottom: 8px; padding-bottom: 4px; border-bottom: 1px solid var(--mist); }}
  .prop-table {{ width: 100%; border-collapse: collapse; font-size: 12px; }}
  .prop-table th {{ text-align: left; font-size: 10px; font-weight: 600; color: var(--pebble);
    text-transform: uppercase; letter-spacing: 0.06em; padding: 6px 8px;
    border-bottom: 2px solid var(--mist); }}
  .prop-table td {{ padding: 6px 8px; border-bottom: 1px solid var(--mist); vertical-align: top; }}
  .prop-table tr:last-child td {{ border-bottom: none; }}
  .prop-table .mono {{ font-family: 'JetBrains Mono', monospace; font-size: 12px; }}
  .prop-table tr.highlight {{ background: rgba(13, 148, 136, 0.06); }}
  .tag {{ display: inline-block; font-size: 10px; font-weight: 500;
    padding: 2px 7px; border-radius: 3px; margin: 1px 2px; }}
  .tag-hot {{ background: #FEE2E2; color: #991B1B; }}
  .tag-signal {{ background: #FEF3C7; color: #92400E; }}
  .tag-info {{ background: #E0F2FE; color: #075985; }}
  .tag-cash {{ background: #D1FAE5; color: #065F46; }}
  .approach-box {{ background: var(--cloud); border-left: 4px solid var(--gold);
    border-radius: 0 8px 8px 0; padding: 14px 18px; margin-bottom: 16px; }}
  .approach-box h3 {{ font-family: 'DM Sans', sans-serif; font-size: 13px;
    font-weight: 600; color: var(--gold); margin-bottom: 6px; }}
  .approach-box p {{ font-size: 12px; color: var(--stone); line-height: 1.6; }}
  .approach-box .script {{ font-style: italic; color: var(--charcoal); background: white;
    border-radius: 4px; padding: 8px 12px; margin-top: 8px; border: 1px solid var(--mist);
    font-size: 12px; line-height: 1.5; }}
  .approach-box ul {{ margin: 8px 0 0 16px; font-size: 12px; color: var(--stone); }}
  .approach-box li {{ margin-bottom: 4px; line-height: 1.5; }}
  .playbook-section {{ background: var(--cloud); border: 1px solid var(--mist);
    border-radius: 8px; padding: 14px 18px; margin-bottom: 16px; }}
  .playbook-section h3 {{ font-family: 'DM Sans', sans-serif; font-size: 13px;
    font-weight: 600; color: var(--ocean); margin-bottom: 8px; }}
  .playbook-section ul {{ margin: 0 0 0 16px; font-size: 12px; color: var(--stone); }}
  .playbook-section li {{ margin-bottom: 6px; line-height: 1.5; }}
  .deep-dive {{ background: var(--cloud); border: 1px solid var(--mist);
    border-radius: 8px; padding: 14px 16px; }}
  .deep-dive .dd-row {{ display: flex; justify-content: space-between;
    padding: 4px 0; border-bottom: 1px solid rgba(0,0,0,0.05); font-size: 12px; }}
  .deep-dive .dd-row:last-child {{ border-bottom: none; }}
  .deep-dive .dd-label {{ color: var(--pebble); font-size: 11px; }}
  .deep-dive .dd-value {{ font-family: 'JetBrains Mono', monospace;
    font-weight: 500; font-size: 12px; }}
  .comparison-box {{ background: var(--cloud); border: 1px solid var(--mist);
    border-radius: 8px; padding: 14px 18px; margin-bottom: 16px; }}
  .comparison-box h3 {{ font-family: 'DM Sans', sans-serif; font-size: 13px;
    font-weight: 600; color: var(--ocean); margin-bottom: 8px; }}
  .comparison-row {{ display: grid; grid-template-columns: 100px 1fr;
    gap: 12px; font-size: 12px; padding: 5px 0; border-bottom: 1px solid rgba(0,0,0,0.05); }}
  .comparison-row:last-child {{ border-bottom: none; }}
  .comparison-row .comp-label {{ color: var(--pebble); font-size: 11px; font-weight: 600; }}
  .comparison-row .comp-basic {{ color: var(--stone); }}
  .comparison-row .comp-us {{ color: var(--deep-ocean); font-weight: 500; }}
  .footer {{ margin-top: 16px; padding-top: 10px; border-top: 1px solid var(--mist);
    display: flex; justify-content: space-between; font-size: 10px; color: var(--pebble); }}
  .footer .confidential {{ font-weight: 600; color: var(--stone); }}
  @media print {{
    body {{ padding: 0; font-size: 12px; }}
    .signal-banner, .stat-card, .tag, .score-badge, .approach-box,
    .comparison-box, .tag-cash, .playbook-section
    {{ -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
  }}
</style>
</head>
<body>

<!-- Header -->
<div class="header">
  <div class="header-left">
    <h1>{name}</h1>
    <span class="segment">{thesis_short}</span>
    <div class="score-badge">Agent Score: {score_est} &bull; {tier_label}</div>
  </div>
  <div class="header-right">
    <div class="brand">Stillmind Creative</div>
    <div class="brand">Investor Intelligence Brief</div>
    <div class="date">Wake County, NC &bull; Generated {TODAY.strftime('%b %Y')}</div>
  </div>
</div>

<!-- Signal Banner -->
<div class="signal-banner">
  <h2>&#9889; {signal_headline}</h2>
  <p>{behavior}</p>
</div>

<!-- Stats -->
<div class="stats-grid">
  <div class="stat-card">
    <div class="label">Properties</div>
    <div class="value">{n_props}</div>
    <div class="subtext">{geo_primary}{f' + {geo_count - 1} other' + ('s' if geo_count > 2 else '') if geo_count > 1 else ''}</div>
  </div>
  <div class="stat-card">
    <div class="label">Portfolio Value</div>
    <div class="value">{_fmt_money(total_val, True)}</div>
    <div class="subtext">AVM estimate</div>
  </div>
  <div class="stat-card">
    <div class="label">{'Permits' if total_permits > 0 else 'Est. Rent'}</div>
    <div class="value">{total_permits if total_permits > 0 else _fmt_money(total_monthly_rent, True) + '/mo'}</div>
    <div class="subtext">{_fmt_money(total_permit_val, True) + ' total value' if total_permits > 0 else _fmt_money(total_annual_rent, True) + '/yr'}</div>
  </div>
  <div class="stat-card">
    <div class="label">Acquisition Pace</div>
    <div class="value">{f'{tpy:.1f}/yr' if tpy > 0 else 'N/A'}</div>
    <div class="subtext">Last: {_fmt_date(last_purchase)}{f' ({days_since}d ago)' if days_since > 0 else ''}</div>
  </div>
</div>
"""

    # Two-column: Acquisition Pattern + Deep Dive
    html += """<div class="two-col">
  <div>
    <div class="section">
      <div class="section-title">Investment Profile</div>
      <table class="prop-table">
"""
    html += f'        <tr><td class="mono" style="color:var(--pebble)">Velocity</td><td><strong>{tpy:.1f} transactions/year</strong>{f" over {years_active}yr" if years_active and years_active != "N/A" else ""}</td></tr>\n'
    html += f'        <tr><td class="mono" style="color:var(--pebble)">Avg Hold</td><td>{hold_yrs} years &mdash; {hold_strategy.replace("_", " ")}</td></tr>\n'
    html += f'        <tr><td class="mono" style="color:var(--pebble)">Price Range</td><td>{price_range}</td></tr>\n'
    html += f'        <tr><td class="mono" style="color:var(--pebble)">Buying Style</td><td>{financing} ({cash_pct}% cash)</td></tr>\n'
    html += f'        <tr><td class="mono" style="color:var(--pebble)">Geography</td><td>{geo_primary} ({geo_count} {"city" if geo_count == 1 else "cities"})</td></tr>\n'
    if predicted_next and predicted_next != "N/A":
        html += f'        <tr><td class="mono" style="color:var(--pebble)">Next Buy Est</td><td>{_fmt_date(predicted_next)} (based on {avg_months}mo avg cadence)</td></tr>\n'

    html += """      </table>
    </div>

    <div class="section">
      <div class="section-title">Key Signals</div>
"""
    # Build signal tags
    if cash_pct >= 50:
        html += '      <span class="tag tag-cash">CASH BUYER</span>\n'
    if total_permits >= 5:
        html += f'      <span class="tag tag-signal">{total_permits} Building Permits</span>\n'
    if total_permit_val >= 50_000:
        html += f'      <span class="tag tag-signal">{_fmt_money(total_permit_val, True)} Permit Value</span>\n'
    if tpy >= 2:
        html += f'      <span class="tag tag-hot">High Velocity ({tpy:.0f}+/yr)</span>\n'
    if n_props >= 5:
        html += f'      <span class="tag tag-info">Portfolio: {n_props} Properties</span>\n'
    if geo_count == 1 and n_props >= 3:
        html += f'      <span class="tag tag-info">Concentrated in {geo_primary}</span>\n'
    if days_since > 0 and days_since < 180:
        html += f'      <span class="tag tag-hot">Active ({days_since}d since last buy)</span>\n'
    if total_monthly_rent > 0:
        html += f'      <span class="tag tag-info">Est. Rent: {_fmt_money(total_monthly_rent)}/mo</span>\n'
    if total_equity > 0:
        html += f'      <span class="tag tag-info">Equity: {_fmt_money(total_equity, True)}</span>\n'

    html += """    </div>
  </div>

  <div>
"""

    # Deep dive on best property
    if deep_dive:
        dd = deep_dive
        html += f'    <div class="section">\n'
        html += f'      <div class="section-title">Property Deep Dive &mdash; {dd["street"]}</div>\n'
        html += f'      <div class="deep-dive">\n'
        html += f'        <div class="dd-row"><span class="dd-label">AVM Estimate</span><span class="dd-value">{_fmt_money(dd["avm"])}</span></div>\n'
        if dd["rent"] > 0:
            html += f'        <div class="dd-row"><span class="dd-label">Rent Estimate</span><span class="dd-value">{_fmt_money(dd["rent"])}/mo</span></div>\n'
        if dd["gross_yield"]:
            color = "var(--sage)" if _float(dd["gross_yield"].replace("%", "")) > 6 else "var(--charcoal)"
            html += f'        <div class="dd-row"><span class="dd-label">Gross Yield</span><span class="dd-value" style="color:{color}">{dd["gross_yield"]}</span></div>\n'
        if dd["last_sale"]:
            sale_text = f'{_fmt_date(dd["last_sale"])} @ {_fmt_money(dd["last_price"])}'
            if dd["is_cash"]:
                sale_text += " CASH"
            html += f'        <div class="dd-row"><span class="dd-label">Last Sale</span><span class="dd-value">{sale_text}</span></div>\n'
        if dd["year_built"]:
            html += f'        <div class="dd-row"><span class="dd-label">Year Built</span><span class="dd-value">{dd["year_built"]}</span></div>\n'
        details = []
        if dd["beds"]:
            details.append(f'{dd["beds"]}BR')
        if dd["sqft"]:
            details.append(f'{_float(dd["sqft"]):,.0f} sqft')
        if details:
            html += f'        <div class="dd-row"><span class="dd-label">Size</span><span class="dd-value">{" &bull; ".join(details)}</span></div>\n'
        if dd["assessed"] > 0:
            html += f'        <div class="dd-row"><span class="dd-label">Assessment</span><span class="dd-value">{_fmt_money(dd["assessed"])}</span></div>\n'
        if dd["tax"] > 0:
            html += f'        <div class="dd-row"><span class="dd-label">Annual Tax</span><span class="dd-value">{_fmt_money(dd["tax"])}</span></div>\n'
        if dd["permits"] > 0:
            html += f'        <div class="dd-row"><span class="dd-label">Permits</span><span class="dd-value">{dd["permits"]}</span></div>\n'
        html += '      </div>\n    </div>\n'

    html += "  </div>\n</div>\n"

    # Full Portfolio Table
    html += f"""
<div class="section">
  <div class="section-title">Full Portfolio &mdash; {n_props} Properties</div>
  <table class="prop-table">
    <thead>
      <tr>
        <th>Address</th>
        <th>City</th>
        <th style="text-align:right">AVM Value</th>
        <th style="text-align:right">Rent/Mo</th>
        <th>Notes</th>
      </tr>
    </thead>
    <tbody>
"""
    for i, p in enumerate(sorted(prop_rows, key=lambda x: x["avm"], reverse=True)):
        highlight = ' class="highlight"' if i == 0 else ""
        tags_html = " ".join(f'<span class="tag {cls}">{txt}</span>' for cls, txt in p["tags"])
        html += f'      <tr{highlight}>\n'
        html += f'        <td>{p["street"]}</td>\n'
        html += f'        <td>{p["city"]}</td>\n'
        html += f'        <td class="mono" style="text-align:right">{_fmt_money(p["avm"])}</td>\n'
        html += f'        <td class="mono" style="text-align:right">{_fmt_money(p["rent"]) if p["rent"] > 0 else "N/A"}</td>\n'
        html += f'        <td>{tags_html}</td>\n'
        html += f'      </tr>\n'

    html += """    </tbody>
  </table>
</div>
"""

    # Approach Playbook (from Step 18)
    if angles:
        html += '<div class="approach-box">\n'
        html += '  <h3>Outreach Playbook</h3>\n'
        html += '  <ul>\n'
        for angle in angles[:4]:
            html += f'    <li><strong>{angle.get("angle", "")}:</strong> {angle.get("what_to_offer", "")}</li>\n'
        html += '  </ul>\n'
        if opening:
            html += f'  <div class="script">{opening}</div>\n'
        html += '</div>\n'

    # Strategic Suggestions
    if suggestions:
        html += '<div class="playbook-section">\n'
        html += '  <h3>Strategic Suggestions</h3>\n'
        html += '  <ul>\n'
        for s in suggestions[:5]:
            html += f'    <li>{s}</li>\n'
        html += '  </ul>\n'
        html += '</div>\n'

    # Conversation Starters
    if starters:
        html += '<div class="playbook-section">\n'
        html += '  <h3>Conversation Starters</h3>\n'
        html += '  <ul>\n'
        for s in starters[:4]:
            html += f'    <li><em>{s}</em></li>\n'
        html += '  </ul>\n'
        html += '</div>\n'

    # What Makes This Lead Different
    basic_desc = f'"{name} &mdash; {n_props} properties, {geo_primary}"'
    our_desc = f'{thesis_short}. {_fmt_money(total_val, True)} portfolio, {tpy:.1f} txns/year'
    if cash_pct >= 50:
        our_desc += f', {cash_pct}% cash buyer'
    if total_permits > 0:
        our_desc += f', {total_permits} permits ({_fmt_money(total_permit_val, True)})'
    our_desc += '. Full outreach playbook with specific approach angles and conversation starters.'

    html += f"""
<div class="comparison-box">
  <h3>What Makes This Lead Different</h3>
  <div class="comparison-row">
    <span class="comp-label">Basic List</span>
    <span class="comp-basic">{basic_desc}</span>
  </div>
  <div class="comparison-row">
    <span class="comp-label">Our Intel</span>
    <span class="comp-us">{our_desc}</span>
  </div>
</div>

<div class="footer">
  <span class="confidential">SAMPLE &mdash; CONFIDENTIAL</span>
  <span>DSCR Lead Intelligence &bull; Stillmind Creative</span>
</div>

</body>
</html>"""

    return html


def main():
    parser = argparse.ArgumentParser(description="Build agent/broker tearsheets from pipeline data")
    parser.add_argument("--market", required=True, help="Market: wake, fl")
    parser.add_argument("--investors", type=str, default="", help="Pipe-separated investor names (default: all)")
    args = parser.parse_args()

    # Load all data sources
    properties_path = DEMO_DIR / f"showcase_7ep_{args.market}.csv"
    profiles_path = DEMO_DIR / f"investment_profiles_{args.market}.csv"
    playbooks_path = DEMO_DIR / f"playbooks_{args.market}.json"

    for path, label in [(properties_path, "Properties"), (profiles_path, "Profiles"), (playbooks_path, "Playbooks")]:
        if not path.exists():
            print(f"  ERROR: {label} not found: {path}")
            sys.exit(1)

    print(f"\n{'='*60}")
    print(f"  BUILD AGENT TEARSHEETS")
    print(f"  Market: {args.market.upper()}")
    print(f"{'='*60}")

    properties_df = pd.read_csv(properties_path, dtype=str)
    profiles_df = pd.read_csv(profiles_path, dtype=str)
    with open(playbooks_path) as f:
        playbooks_list = json.load(f)

    # Index playbooks by investor name
    playbooks = {}
    for pb in playbooks_list:
        name = pb.get("_investor_name", "")
        if name:
            playbooks[name] = pb

    # Filter investors
    if args.investors:
        investor_names = [n.strip() for n in args.investors.split("|")]
    else:
        investor_names = profiles_df["investor_name"].tolist()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for investor_name in investor_names:
        profile_row = profiles_df[profiles_df["investor_name"] == investor_name]
        if len(profile_row) == 0:
            print(f"  SKIP: {investor_name} not found in profiles")
            continue

        profile = profile_row.iloc[0].to_dict()
        investor_props = properties_df[properties_df["owner_name"] == investor_name]
        playbook = playbooks.get(investor_name, {})

        if not playbook:
            print(f"  WARNING: No playbook for {investor_name}")

        html = build_tearsheet(profile, investor_props, playbook)

        # Generate filename
        safe_name = investor_name.lower().replace(" ", "_").replace(",", "")
        safe_name = "".join(c for c in safe_name if c.isalnum() or c == "_")[:50]
        filename = f"tearsheet_{safe_name}.html"
        filepath = OUTPUT_DIR / filename

        with open(filepath, "w") as f:
            f.write(html)

        print(f"  Built: {filename} ({len(investor_props)} properties)")

    print(f"\n  Output directory: {OUTPUT_DIR}")
    print(f"  Tearsheets built: {len(investor_names)}")
    print()


if __name__ == "__main__":
    main()
