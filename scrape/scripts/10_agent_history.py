"""
Step 10: Agent Representation History
=======================================

Looks up sold property listings on public real estate sites to find
which agents represented the investor on past transactions. This tells
an agent whether the investor already has a loyal agent relationship
or is open to new representation.

HOW IT WORKS:
  1. Takes property addresses from enriched data
  2. Searches Google for "[address] sold agent MLS" on public listing sites
  3. Fetches the result pages (movoto, raleighrealty, coldwellbanker, etc.)
  4. Extracts listing agent name + brokerage via pattern matching
  5. Aggregates per investor: agent_loyalty_score, unique agents, etc.

OUTPUT SIGNALS:
  - listing_agent: Agent name on the sold listing
  - listing_brokerage: Brokerage firm
  - agent_loyalty: "loyal" (same agent 2+ times), "mixed" (different agents),
                   "unknown" (no data), "builder_direct" (new construction)
  - agent_loyalty_detail: Summary of agent history

COST: Google Custom Search API = $5/1,000 queries. Each property = 1 query.
      Free tier: 100 queries/day. For demo leads, free tier is sufficient.

DATA SOURCES (public, no MLS access needed):
  - Movoto, RaleighRealty, ColdwellBanker, LongAndFoster, Compass
  - Redfin/Zillow block direct fetches but show up in Google results

Usage:
    python scripts/10_agent_history.py --market wake
    python scripts/10_agent_history.py --market wake --investors "MOYER, JONATHAN ECK, KELLY"
    python scripts/10_agent_history.py --input path/to/enriched.csv
"""

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path

import pandas as pd
import requests

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent
DATA_DIR = PROJECT_DIR / "data"
DEMO_DIR = DATA_DIR / "demo"
CACHE_DIR = DEMO_DIR / "agent_cache"

if load_dotenv:
    load_dotenv(PROJECT_DIR / ".env")
    root_env = PROJECT_DIR.parent / ".env"
    if root_env.exists():
        load_dotenv(root_env)

# Google Custom Search API (free tier: 100/day)
GOOGLE_API_KEY = os.getenv("GOOGLE_CUSTOM_SEARCH_KEY", "")
GOOGLE_CX = os.getenv("GOOGLE_CUSTOM_SEARCH_CX", "")

# Sites that show agent data publicly and don't block fetches
AGENT_SITES = [
    "movoto.com",
    "raleighrealty.com",
    "coldwellbankerhomes.com",
    "longandfoster.com",
    "compass.com",
    "hpw.com",
    "homes.com",
    "trulia.com",
]

REQUEST_DELAY = 1.0  # seconds between requests


def load_cache() -> dict:
    """Load agent lookup cache."""
    cache_file = CACHE_DIR / "agent_cache.json"
    if cache_file.exists():
        with open(cache_file) as f:
            return json.load(f)
    return {}


def save_cache(cache: dict):
    """Save agent lookup cache."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    with open(CACHE_DIR / "agent_cache.json", "w") as f:
        json.dump(cache, f, indent=2)


def search_google(query: str) -> list:
    """
    Search Google Custom Search API. Returns list of result dicts.
    Falls back to empty list if no API key configured.
    """
    if not GOOGLE_API_KEY or not GOOGLE_CX:
        return []

    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": GOOGLE_API_KEY,
        "cx": GOOGLE_CX,
        "q": query,
        "num": 5,
    }
    try:
        resp = requests.get(url, params=params, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            return data.get("items", [])
    except requests.RequestException:
        pass
    return []


def fetch_page(url: str) -> str:
    """Fetch a web page and return text content."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }
    try:
        resp = requests.get(url, headers=headers, timeout=15, allow_redirects=True)
        if resp.status_code == 200:
            return resp.text
    except requests.RequestException:
        pass
    return ""


def extract_agent_from_html(html: str) -> dict:
    """
    Extract agent name and brokerage from a property listing page.
    Uses multiple regex patterns to handle different site formats.
    """
    result = {"agent": "", "brokerage": ""}

    if not html:
        return result

    # Pattern 1: "Listing Agent: Name" or "Listed by Name"
    patterns_agent = [
        r'[Ll]isting\s*[Aa]gent[:\s]*(?:<[^>]+>)*\s*([A-Z][a-z]+ [A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)',
        r'[Ll]isted\s+[Bb]y[:\s]*(?:<[^>]+>)*\s*([A-Z][a-z]+ [A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)',
        r'"listingAgent"[:\s]*"([^"]+)"',
        r'"listing_agent_name"[:\s]*"([^"]+)"',
        r'"agentName"[:\s]*"([^"]+)"',
        r'data-agent-name="([^"]+)"',
        r'Listing\s+courtesy\s+of[:\s]*([^<\n]+?)(?:\.|,|\s*<)',
        r'listing_agent["\s:]+([A-Z][^"<\n,]+)',
    ]

    for pattern in patterns_agent:
        match = re.search(pattern, html)
        if match:
            name = match.group(1).strip()
            # Filter out non-names
            if len(name) > 3 and len(name) < 60 and not any(
                kw in name.upper() for kw in ["MLS", "REDFIN", "ZILLOW", "LLC", "INC", "COURTESY"]
            ):
                result["agent"] = name
                break

    # Pattern 2: Brokerage / Office
    patterns_broker = [
        r'[Ll]isting\s*[Oo]ffice[:\s]*(?:<[^>]+>)*\s*([^<\n]+)',
        r'[Ll]isting\s*[Ff]irm[:\s]*(?:<[^>]+>)*\s*([^<\n]+)',
        r'[Cc]ourtesy\s+of[:\s]*([^<\n.]+)',
        r'"brokerName"[:\s]*"([^"]+)"',
        r'"listing_office_name"[:\s]*"([^"]+)"',
        r'"officeName"[:\s]*"([^"]+)"',
        r'Brokerage[:\s]*(?:<[^>]+>)*\s*([^<\n]+)',
    ]

    for pattern in patterns_broker:
        match = re.search(pattern, html)
        if match:
            brokerage = match.group(1).strip()
            if len(brokerage) > 2 and len(brokerage) < 80:
                result["brokerage"] = brokerage
                break

    return result


def lookup_agent_for_property(address: str, city: str, state: str,
                              cache: dict) -> dict:
    """
    Look up the listing agent for a sold property.

    Strategy:
      1. Check cache
      2. Search Google for the address on public listing sites
      3. Fetch top results and extract agent info
      4. Cache and return
    """
    cache_key = f"{address}|{city}|{state}".upper().replace(" ", "")

    if cache_key in cache:
        return cache[cache_key]

    result = {
        "address": address,
        "listing_agent": "",
        "listing_brokerage": "",
        "source_url": "",
        "lookup_method": "",
    }

    # Build search query
    site_filter = " OR ".join(f"site:{s}" for s in AGENT_SITES[:4])
    query = f'"{address}" {city} {state} sold agent MLS ({site_filter})'

    # Try Google Custom Search first
    if GOOGLE_API_KEY:
        search_results = search_google(query)
        for sr in search_results:
            url = sr.get("link", "")
            # Skip sites that block fetches
            if any(blocked in url for blocked in ["redfin.com", "zillow.com"]):
                # But check if snippet has agent info
                snippet = sr.get("snippet", "")
                agent_info = extract_agent_from_html(snippet)
                if agent_info["agent"]:
                    result["listing_agent"] = agent_info["agent"]
                    result["listing_brokerage"] = agent_info["brokerage"]
                    result["source_url"] = url
                    result["lookup_method"] = "google_snippet"
                    cache[cache_key] = result
                    save_cache(cache)
                    return result
                continue

            # Fetch the page
            html = fetch_page(url)
            if html:
                agent_info = extract_agent_from_html(html)
                if agent_info["agent"] or agent_info["brokerage"]:
                    result["listing_agent"] = agent_info["agent"]
                    result["listing_brokerage"] = agent_info["brokerage"]
                    result["source_url"] = url
                    result["lookup_method"] = "page_fetch"
                    cache[cache_key] = result
                    save_cache(cache)
                    return result

            time.sleep(REQUEST_DELAY)

    # Fallback: try direct URL patterns on sites we know work
    direct_urls = [
        f"https://www.movoto.com/realestate/{address.lower().replace(' ', '-')}-{city.lower()}-{state.lower()}/",
        f"https://raleighrealty.com/home/{address.lower().replace(' ', '-')}-{city.lower()}-{state.lower()}/",
    ]

    for url in direct_urls:
        html = fetch_page(url)
        if html and len(html) > 1000:
            agent_info = extract_agent_from_html(html)
            if agent_info["agent"] or agent_info["brokerage"]:
                result["listing_agent"] = agent_info["agent"]
                result["listing_brokerage"] = agent_info["brokerage"]
                result["source_url"] = url
                result["lookup_method"] = "direct_fetch"
                cache[cache_key] = result
                save_cache(cache)
                return result
        time.sleep(REQUEST_DELAY)

    # No result found
    result["lookup_method"] = "not_found"
    cache[cache_key] = result
    save_cache(cache)
    return result


def analyze_agent_loyalty(agent_results: list) -> dict:
    """
    Analyze agent representation across an investor's transactions.

    Returns:
      agent_loyalty: "loyal", "mixed", "no_agent", "builder_direct", "unknown"
      agent_loyalty_detail: Human-readable summary
      unique_agents: List of unique agent names
      primary_agent: Most-used agent (if any)
    """
    agents = []
    brokerages = []
    builder_direct = 0

    for r in agent_results:
        agent = r.get("listing_agent", "").strip()
        brokerage = r.get("listing_brokerage", "").strip()

        if agent:
            agents.append(agent)
        if brokerage:
            brokerages.append(brokerage)

        # Detect builder-direct sales (seller or brokerage indicates builder)
        seller = r.get("seller_name", "")
        builder_keywords = [
            "DRB", "HORTON", "LENNAR", "PULTE", "MERITAGE", "TOLL",
            "NVR", "RYAN HOMES", "BUILDER", "CONSTRUCTION", "DEVELOPMENT",
            "BUILDER DIRECT",
        ]
        is_builder = False
        if seller and any(kw in seller.upper() for kw in builder_keywords):
            is_builder = True
        if brokerage and any(kw in brokerage.upper() for kw in builder_keywords):
            is_builder = True
        if r.get("is_builder_direct"):
            is_builder = True
        if is_builder:
            builder_direct += 1

    unique_agents = list(set(agents))
    unique_brokerages = list(set(brokerages))
    total_lookups = len(agent_results)
    found = len(agents)

    analysis = {
        "unique_agents": unique_agents,
        "unique_brokerages": unique_brokerages,
        "total_properties_checked": total_lookups,
        "agent_data_found": found,
        "builder_direct_count": builder_direct,
    }

    if found == 0 and builder_direct > 0:
        analysis["agent_loyalty"] = "builder_direct"
        analysis["agent_loyalty_detail"] = f"Bought {builder_direct} properties direct from builders — no agent relationship detected"
        analysis["primary_agent"] = ""
    elif found == 0:
        analysis["agent_loyalty"] = "unknown"
        analysis["agent_loyalty_detail"] = "No agent data found — may be unrepresented or data unavailable"
        analysis["primary_agent"] = ""
    elif len(unique_agents) == 1 and found >= 2:
        analysis["agent_loyalty"] = "loyal"
        analysis["agent_loyalty_detail"] = f"Used {unique_agents[0]} on {found} transactions — existing relationship"
        analysis["primary_agent"] = unique_agents[0]
    elif len(unique_agents) >= 2:
        analysis["agent_loyalty"] = "mixed"
        analysis["agent_loyalty_detail"] = f"Used {len(unique_agents)} different agents across {found} transactions — open to new representation"
        analysis["primary_agent"] = ""
    else:
        analysis["agent_loyalty"] = "single_transaction"
        analysis["agent_loyalty_detail"] = f"Only 1 transaction found with agent: {unique_agents[0] if unique_agents else 'unknown'}"
        analysis["primary_agent"] = unique_agents[0] if unique_agents else ""

    return analysis


def manual_entry_mode(market: str, investors: list = None):
    """
    For cases where Google API isn't configured — accept manual research
    results via CSV or inline entry. This keeps the pipeline functional
    while the automated lookup is being set up.

    Also processes ATTOM seller names to detect builder-direct sales.
    """
    properties_path = DEMO_DIR / f"showcase_7ep_{market}.csv"
    if not properties_path.exists():
        print(f"  ERROR: Properties not found: {properties_path}")
        sys.exit(1)

    df = pd.read_csv(properties_path, dtype=str)

    if investors:
        df = df[df["owner_name"].isin(investors)]

    print(f"  Properties to analyze: {len(df)}")
    print(f"  Unique investors: {df['owner_name'].nunique()}")

    # Check for ATTOM seller data (from expandedhistory cache)
    sales_cache_path = CACHE_DIR.parent / "attom_7ep_cache" / "cache_sales.json"
    seller_data = {}
    if sales_cache_path.exists():
        with open(sales_cache_path) as f:
            sales_cache = json.load(f)
        # Build seller lookup from cache
        for key, data in sales_cache.items():
            if "_error" in data:
                continue
            props = data.get("property", [])
            if not props:
                continue
            sale_history = props[0].get("salehistory", []) or props[0].get("saleHistory", [])
            if sale_history:
                addr = props[0].get("address", {}).get("oneLine", "")
                seller = sale_history[0].get("sellerName", "")
                buyer_name = sale_history[0].get("buyerName", "")
                if addr:
                    seller_data[addr.upper().replace(" ", "")] = {
                        "seller": seller,
                        "buyer": buyer_name,
                    }

    # Process each investor
    all_results = []

    for owner_name in df["owner_name"].unique():
        owner_props = df[df["owner_name"] == owner_name]
        agent_results = []

        print(f"\n  {owner_name}")

        for _, row in owner_props.iterrows():
            address = str(row.get("address", "")).strip()
            addr_key = address.upper().replace(" ", "").replace(",", "")

            # Check seller data from ATTOM
            seller_info = {}
            for cached_addr, info in seller_data.items():
                if addr_key[:20] in cached_addr or cached_addr[:20] in addr_key:
                    seller_info = info
                    break

            seller = seller_info.get("seller", "")
            is_builder = any(kw in seller.upper() for kw in [
                "DRB", "HORTON", "LENNAR", "PULTE", "MERITAGE", "TOLL",
                "NVR", "RYAN HOMES", "BUILDER", "CONSTRUCTION", "DEVELOPMENT",
                "HOMES LLC", "HOMES INC"
            ]) if seller else False

            agent_results.append({
                "address": address,
                "seller_name": seller,
                "is_builder_direct": is_builder,
                "listing_agent": "",  # To be filled by manual research or Google API
                "listing_brokerage": "",
            })

            status = f"Builder: {seller}" if is_builder else f"Seller: {seller}" if seller else "No seller data"
            print(f"    {address[:50]} — {status}")

        # Analyze loyalty
        analysis = analyze_agent_loyalty(agent_results)
        analysis["investor_name"] = owner_name
        analysis["properties"] = agent_results
        all_results.append(analysis)

        print(f"    >> {analysis['agent_loyalty']}: {analysis['agent_loyalty_detail']}")

    # Save results
    output_path = DEMO_DIR / f"agent_history_{market}.json"
    with open(output_path, "w") as f:
        json.dump(all_results, f, indent=2)
    print(f"\n  Output saved: {output_path}")

    # Also save a flat CSV for pipeline integration
    flat_rows = []
    for result in all_results:
        flat_rows.append({
            "investor_name": result["investor_name"],
            "agent_loyalty": result["agent_loyalty"],
            "agent_loyalty_detail": result["agent_loyalty_detail"],
            "primary_agent": result.get("primary_agent", ""),
            "unique_agents": json.dumps(result.get("unique_agents", [])),
            "unique_brokerages": json.dumps(result.get("unique_brokerages", [])),
            "builder_direct_count": result.get("builder_direct_count", 0),
            "total_checked": result.get("total_properties_checked", 0),
            "agent_data_found": result.get("agent_data_found", 0),
        })

    flat_df = pd.DataFrame(flat_rows)
    flat_path = DEMO_DIR / f"agent_history_{market}.csv"
    flat_df.to_csv(flat_path, index=False)
    print(f"  Flat CSV: {flat_path}")

    return all_results


def manual_override(market: str, overrides: list):
    """
    Apply manual research results to the agent history.

    overrides: list of dicts with keys:
      investor_name, address, listing_agent, listing_brokerage
    """
    output_path = DEMO_DIR / f"agent_history_{market}.json"
    if not output_path.exists():
        print(f"  ERROR: Run base analysis first")
        sys.exit(1)

    with open(output_path) as f:
        results = json.load(f)

    for override in overrides:
        inv_name = override["investor_name"]
        addr = override["address"]
        agent = override.get("listing_agent", "")
        brokerage = override.get("listing_brokerage", "")

        for result in results:
            if result["investor_name"] != inv_name:
                continue
            for prop in result["properties"]:
                if addr.upper() in prop["address"].upper():
                    prop["listing_agent"] = agent
                    prop["listing_brokerage"] = brokerage
                    print(f"  Updated: {addr} -> {agent} ({brokerage})")

    # Re-analyze loyalty for all investors after all overrides applied
    for result in results:
        analysis = analyze_agent_loyalty(result["properties"])
        inv_name = result["investor_name"]
        result.update(analysis)
        result["investor_name"] = inv_name
        print(f"  {inv_name[:45]}: {result['agent_loyalty']} — {result['agent_loyalty_detail']}")

    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"  Saved: {output_path}")

    # Rebuild flat CSV
    flat_rows = []
    for result in results:
        flat_rows.append({
            "investor_name": result["investor_name"],
            "agent_loyalty": result["agent_loyalty"],
            "agent_loyalty_detail": result["agent_loyalty_detail"],
            "primary_agent": result.get("primary_agent", ""),
            "unique_agents": json.dumps(result.get("unique_agents", [])),
            "unique_brokerages": json.dumps(result.get("unique_brokerages", [])),
            "builder_direct_count": result.get("builder_direct_count", 0),
            "total_checked": result.get("total_properties_checked", 0),
            "agent_data_found": result.get("agent_data_found", 0),
        })
    flat_df = pd.DataFrame(flat_rows)
    flat_df.to_csv(DEMO_DIR / f"agent_history_{market}.csv", index=False)


def main():
    parser = argparse.ArgumentParser(
        description="Look up agent representation history for investors"
    )
    parser.add_argument("--market", required=True, help="Market: wake, fl")
    parser.add_argument("--investors", type=str, default="",
                        help="Pipe-separated investor names")
    parser.add_argument("--apply-overrides", type=str, default="",
                        help="Path to JSON file with manual agent research results")
    args = parser.parse_args()

    print(f"\n{'='*60}")
    print(f"  STEP 10: AGENT REPRESENTATION HISTORY")
    print(f"  Market: {args.market.upper()}")
    print(f"{'='*60}")

    investors = [n.strip() for n in args.investors.split("|") if n.strip()] if args.investors else None

    if args.apply_overrides:
        with open(args.apply_overrides) as f:
            overrides = json.load(f)
        manual_override(args.market, overrides)
    else:
        # Run analysis (uses ATTOM seller data + Google API if configured)
        results = manual_entry_mode(args.market, investors)

        if not GOOGLE_API_KEY:
            print(f"\n  NOTE: Google Custom Search API not configured.")
            print(f"  To enable automated agent lookup:")
            print(f"    1. Create a Custom Search Engine at https://cse.google.com")
            print(f"    2. Get API key at https://console.cloud.google.com")
            print(f"    3. Add to scrape/.env:")
            print(f"       GOOGLE_CUSTOM_SEARCH_KEY=your_key")
            print(f"       GOOGLE_CUSTOM_SEARCH_CX=your_cx_id")
            print(f"\n  For now, apply manual research with --apply-overrides")

    print()


if __name__ == "__main__":
    main()
