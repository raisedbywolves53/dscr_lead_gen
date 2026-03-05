"""
Step 15: Network Mapping
========================

Cross-references all leads to find shared connections:
co-investors, shared property managers, shared lenders,
and shared real estate agents.

What this script does:
  1. Reads enriched leads (with SunBiz officer data)
  2. Cross-references SunBiz officers across all leads
     → finds co-investors (people who share LLC officers)
  3. Cross-references DBPR PM licenses by property address
     → finds shared property managers
  4. Cross-references lenders across leads (when financing data available)
  5. Builds a relationship graph: lead → connection → other leads
  6. Outputs network map CSV + summary

Usage:
    python scripts/15_network_mapping.py
    python scripts/15_network_mapping.py --input data/enriched/top_leads_enriched.csv
"""

import argparse
import json
import re
from collections import defaultdict
from pathlib import Path

import pandas as pd

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
except ImportError:
    pass

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent
ENRICHED_DIR = PROJECT_DIR / "data" / "enriched"
SIGNALS_DIR = PROJECT_DIR / "data" / "signals"
FINANCING_DIR = PROJECT_DIR / "data" / "financing"

DEFAULT_INPUT = ENRICHED_DIR / "top_leads_enriched.csv"

# Also check for SunBiz cache from script 04
SUNBIZ_CACHE_DIR = PROJECT_DIR / "data" / "raw"

# DBPR data location (from existing pipeline)
DBPR_PATH = Path("pipeline/data/dbpr/dbpr_vacation_rentals.csv")


# ---------------------------------------------------------------------------
# Name normalization
# ---------------------------------------------------------------------------

def normalize_name(name: str) -> str:
    """Normalize a person name for comparison."""
    if not name or str(name).upper() in ("NAN", "NONE", ""):
        return ""
    name = str(name).strip().upper()
    # Remove suffixes
    for suffix in [" JR", " SR", " III", " II", " IV", " ESQ", " MD", " PHD"]:
        if name.endswith(suffix):
            name = name[:-len(suffix)].strip()
    # Remove punctuation
    name = re.sub(r"[.,']", "", name)
    # Normalize whitespace
    name = " ".join(name.split())
    return name


def normalize_entity(name: str) -> str:
    """Normalize an entity name for comparison."""
    if not name or str(name).upper() in ("NAN", "NONE", ""):
        return ""
    name = str(name).strip().upper()
    # Remove common suffixes
    for suffix in [" LLC", " L.L.C.", " L.L.C", " INC", " INC.",
                   " CORP", " CORP.", " LP", " LTD", " LTD.",
                   " CO", " CO.", " COMPANY"]:
        if name.endswith(suffix):
            name = name[:-len(suffix)].strip()
    name = re.sub(r"[.,']", "", name)
    name = " ".join(name.split())
    return name


# ---------------------------------------------------------------------------
# Parse officer strings from SunBiz data
# ---------------------------------------------------------------------------

def parse_officers(officer_str: str) -> list:
    """
    Parse the entity_officers field from SunBiz resolution.
    Format: "NAME1 (TITLE1); NAME2 (TITLE2); ..."
    Returns list of {"name": ..., "title": ...} dicts.
    """
    if not officer_str or str(officer_str).upper() in ("NAN", "NONE", ""):
        return []

    officers = []
    for entry in str(officer_str).split(";"):
        entry = entry.strip()
        if not entry:
            continue

        # Parse "NAME (TITLE)" format
        match = re.match(r"^(.+?)\s*\(([^)]+)\)\s*$", entry)
        if match:
            officers.append({
                "name": match.group(1).strip(),
                "title": match.group(2).strip(),
            })
        else:
            officers.append({"name": entry, "title": ""})

    return officers


# ---------------------------------------------------------------------------
# Network analysis functions
# ---------------------------------------------------------------------------

def find_shared_officers(leads_df: pd.DataFrame) -> list:
    """
    Find people who appear as officers in multiple leads' entities.
    Returns list of {"person": ..., "leads": [...], "entities": [...]}
    """
    # Build person → leads mapping
    person_to_leads = defaultdict(list)

    for _, row in leads_df.iterrows():
        owner = str(row.get("OWN_NAME", ""))
        officers = parse_officers(str(row.get("entity_officers", "")))
        resolved = str(row.get("resolved_person", ""))

        # Add resolved person
        if resolved and resolved.upper() not in ("NAN", "NONE", ""):
            norm = normalize_name(resolved)
            if norm:
                person_to_leads[norm].append({
                    "lead": owner,
                    "entity": owner,
                    "role": "resolved_person",
                })

        # Add all officers
        for officer in officers:
            norm = normalize_name(officer["name"])
            if norm:
                person_to_leads[norm].append({
                    "lead": owner,
                    "entity": owner,
                    "role": officer.get("title", "officer"),
                })

    # Find people connected to 2+ different leads
    shared = []
    for person, appearances in person_to_leads.items():
        unique_leads = set(a["lead"] for a in appearances)
        if len(unique_leads) >= 2:
            shared.append({
                "person": person,
                "lead_count": len(unique_leads),
                "leads": list(unique_leads),
                "entities": list(set(a["entity"] for a in appearances)),
                "roles": list(set(a["role"] for a in appearances)),
            })

    return sorted(shared, key=lambda x: x["lead_count"], reverse=True)


def find_shared_addresses(leads_df: pd.DataFrame) -> list:
    """
    Find leads that share property addresses (co-ownership or
    properties managed by same entity).
    """
    address_to_leads = defaultdict(list)

    for _, row in leads_df.iterrows():
        owner = str(row.get("OWN_NAME", ""))
        addrs = str(row.get("PHY_ADDR1", ""))

        if not addrs or addrs.upper() in ("NAN", "NONE", ""):
            continue

        # PHY_ADDR1 is pipe-delimited for portfolio owners
        for addr in addrs.split("|"):
            addr = addr.strip().upper()
            if addr and len(addr) > 5:
                # Normalize: remove unit/apt numbers for comparison
                normalized = re.sub(r"\s+(APT|UNIT|STE|#)\s*\S+", "", addr)
                normalized = " ".join(normalized.split())
                address_to_leads[normalized].append(owner)

    shared = []
    for addr, leads in address_to_leads.items():
        unique_leads = set(leads)
        if len(unique_leads) >= 2:
            shared.append({
                "address": addr,
                "lead_count": len(unique_leads),
                "leads": list(unique_leads),
                "connection_type": "shared_property_address",
            })

    return sorted(shared, key=lambda x: x["lead_count"], reverse=True)


def find_shared_lenders(financing_df: pd.DataFrame = None) -> list:
    """
    Find leads that share the same lender.
    Requires financing data from script 11 (county clerk).
    """
    if financing_df is None or financing_df.empty:
        return []

    lender_to_leads = defaultdict(list)

    for _, row in financing_df.iterrows():
        owner = str(row.get("OWN_NAME", ""))
        lender = str(row.get("lender_name", ""))

        if lender and lender.upper() not in ("NAN", "NONE", ""):
            norm_lender = lender.strip().upper()
            lender_to_leads[norm_lender].append(owner)

    shared = []
    for lender, leads in lender_to_leads.items():
        unique_leads = set(leads)
        if len(unique_leads) >= 2:
            shared.append({
                "lender": lender,
                "lead_count": len(unique_leads),
                "leads": list(unique_leads),
                "connection_type": "shared_lender",
            })

    return sorted(shared, key=lambda x: x["lead_count"], reverse=True)


def build_lead_network_summary(lead_name: str, shared_officers: list,
                                shared_addresses: list, shared_lenders: list) -> dict:
    """Build network summary for a single lead."""
    connections = []
    co_investors = []
    shared_pms = []
    shared_lender_names = []

    for so in shared_officers:
        if lead_name in so["leads"]:
            other_leads = [l for l in so["leads"] if l != lead_name]
            for other in other_leads:
                co_investors.append(f"{so['person']} → {other}")
                connections.append({
                    "type": "co_investor",
                    "via": so["person"],
                    "connected_to": other,
                })

    for sa in shared_addresses:
        if lead_name in sa["leads"]:
            other_leads = [l for l in sa["leads"] if l != lead_name]
            for other in other_leads:
                connections.append({
                    "type": "shared_address",
                    "via": sa["address"],
                    "connected_to": other,
                })

    for sl in shared_lenders:
        if lead_name in sl["leads"]:
            shared_lender_names.append(sl["lender"])
            other_leads = [l for l in sl["leads"] if l != lead_name]
            for other in other_leads:
                connections.append({
                    "type": "shared_lender",
                    "via": sl["lender"],
                    "connected_to": other,
                })

    return {
        "connection_count": len(connections),
        "co_investors": "; ".join(co_investors) if co_investors else "",
        "shared_lenders": "; ".join(shared_lender_names) if shared_lender_names else "",
        "connected_leads": "; ".join(set(c["connected_to"] for c in connections)) if connections else "",
        "network_score": min(len(connections) * 3, 15),  # 0-15 points
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Network mapping across leads (Step 15)")
    parser.add_argument("--input", type=str, default=str(DEFAULT_INPUT),
                        help=f"Input CSV (default: {DEFAULT_INPUT})")
    args = parser.parse_args()

    SIGNALS_DIR.mkdir(parents=True, exist_ok=True)

    # Load leads
    input_path = Path(args.input)
    if not input_path.exists():
        for alt in [ENRICHED_DIR / "apollo_results.csv", ENRICHED_DIR / "merged_enriched.csv"]:
            if alt.exists():
                input_path = alt
                break
        else:
            print(f"\n  ERROR: Input file not found: {args.input}")
            return

    print(f"\n  Loading leads: {input_path}")
    df = pd.read_csv(input_path, dtype=str, low_memory=False)
    print(f"  Records: {len(df)}")

    # Load financing data if available
    financing_df = None
    for county in ["palm_beach", "broward"]:
        fpath = FINANCING_DIR / f"{county}_mortgages.csv"
        if fpath.exists():
            chunk = pd.read_csv(fpath, dtype=str)
            financing_df = chunk if financing_df is None else pd.concat([financing_df, chunk])
    if financing_df is not None:
        print(f"  Financing data loaded: {len(financing_df)} mortgage records")
    else:
        print("  No financing data yet (run script 11 first for lender cross-referencing)")

    # ---------------------------------------------------------------------------
    # 1. Find shared officers (co-investors)
    # ---------------------------------------------------------------------------
    print("\n  Analyzing shared officers / co-investors...")
    shared_officers = find_shared_officers(df)
    if shared_officers:
        print(f"  Found {len(shared_officers)} shared connections:")
        for so in shared_officers[:5]:
            print(f"    {so['person']}: connects {so['lead_count']} leads — {', '.join(so['leads'][:3])}")
    else:
        print("  No shared officers found across leads")

    # ---------------------------------------------------------------------------
    # 2. Find shared property addresses
    # ---------------------------------------------------------------------------
    print("\n  Analyzing shared property addresses...")
    shared_addresses = find_shared_addresses(df)
    if shared_addresses:
        print(f"  Found {len(shared_addresses)} shared addresses:")
        for sa in shared_addresses[:5]:
            print(f"    {sa['address'][:50]}: {sa['lead_count']} leads")
    else:
        print("  No shared addresses found")

    # ---------------------------------------------------------------------------
    # 3. Find shared lenders
    # ---------------------------------------------------------------------------
    print("\n  Analyzing shared lenders...")
    shared_lenders = find_shared_lenders(financing_df)
    if shared_lenders:
        print(f"  Found {len(shared_lenders)} shared lenders:")
        for sl in shared_lenders[:5]:
            print(f"    {sl['lender'][:40]}: {sl['lead_count']} leads")
    else:
        print("  No shared lender data (financing data not yet available)")

    # ---------------------------------------------------------------------------
    # 4. Build per-lead network summary
    # ---------------------------------------------------------------------------
    print("\n  Building per-lead network summary...")

    network_cols = ["connection_count", "co_investors", "shared_lenders",
                    "connected_leads", "network_score"]
    for col in network_cols:
        df[col] = ""

    connected_count = 0
    for idx, row in df.iterrows():
        owner = str(row.get("OWN_NAME", ""))
        summary = build_lead_network_summary(owner, shared_officers,
                                              shared_addresses, shared_lenders)
        for col, val in summary.items():
            df.at[idx, col] = str(val)

        if summary["connection_count"] > 0:
            connected_count += 1

    # Save output
    output_path = SIGNALS_DIR / "network_map.csv"
    df.to_csv(output_path, index=False)

    # Save detailed connections as JSON for dossier assembly
    connections_json = {
        "shared_officers": shared_officers,
        "shared_addresses": shared_addresses,
        "shared_lenders": shared_lenders,
    }
    json_path = SIGNALS_DIR / "network_detail.json"
    with open(json_path, "w") as f:
        json.dump(connections_json, f, indent=2)

    # Summary
    print()
    print("=" * 60)
    print("  NETWORK MAPPING RESULTS")
    print("=" * 60)
    print(f"  Total leads:           {len(df)}")
    print(f"  Leads with connections: {connected_count}")
    print(f"  Shared officers:       {len(shared_officers)}")
    print(f"  Shared addresses:      {len(shared_addresses)}")
    print(f"  Shared lenders:        {len(shared_lenders)}")
    if len(df) > 0:
        print(f"  Network coverage:      {connected_count}/{len(df)} = {connected_count/len(df)*100:.0f}%")
    print()
    print(f"  Output: {output_path}")
    print(f"  Detail: {json_path}")
    print()


if __name__ == "__main__":
    main()
