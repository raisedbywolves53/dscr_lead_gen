"""
SunBiz lookup for showcase demo entities.
Pulls full officer/director lists for the 4 entity-owned showcase properties.

Usage: python scripts/sunbiz_showcase_lookup.py
"""

import importlib.util
import json
import sys
import time
from pathlib import Path

import pandas as pd
import requests
from bs4 import BeautifulSoup

# Reuse logic from 04_sunbiz_llc_resolver.py
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent
DEMO_DIR = PROJECT_DIR / "data" / "demo"

# Import from 04_sunbiz_llc_resolver.py (can't use normal import — starts with digit)
_spec = importlib.util.spec_from_file_location(
    "sunbiz_resolver", SCRIPT_DIR / "04_sunbiz_llc_resolver.py"
)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
create_session = _mod.create_session
search_sunbiz = _mod.search_sunbiz

# Entities to look up (STEBBINS is individual, skip)
ENTITIES = [
    "DEMIRAY HOLDINGS INC",
    "MCDOUGALL LIVING TRUST",
    "MSNO PROPERTIES LLC",
    "JSF ENTERPRISES LLC",
]


def main():
    print("SunBiz Showcase Officer Lookup")
    print("=" * 50)

    session = create_session()
    results = {}

    for i, entity in enumerate(ENTITIES):
        print(f"\n[{i+1}/{len(ENTITIES)}] Looking up: {entity}")
        result = search_sunbiz(entity, session)
        results[entity] = result

        print(f"  Status: {result.get('status', 'N/A')}")
        print(f"  Registered Agent: {result.get('registered_agent_name', 'N/A')}")
        print(f"  Officers: {result.get('officer_names', 'NONE FOUND')}")
        print(f"  Resolved Person: {result.get('resolved_person', 'N/A')}")

        if i < len(ENTITIES) - 1:
            time.sleep(3)

    # Save raw results
    cache_file = DEMO_DIR / "sunbiz_showcase_results.json"
    with open(cache_file, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nSaved raw results to {cache_file}")

    # Update showcase_enriched.csv
    csv_file = DEMO_DIR / "showcase_enriched.csv"
    if csv_file.exists():
        df = pd.read_csv(csv_file, dtype=str)
        updated = 0
        for entity, data in results.items():
            mask = df["OWN_NAME"] == entity
            if mask.any() and data.get("officer_names"):
                df.loc[mask, "officer_names"] = data["officer_names"]
                df.loc[mask, "registered_agent_name"] = data.get("registered_agent_name", "")
                df.loc[mask, "registered_agent_address"] = data.get("registered_agent_address", "")  # keep if exists
                if data.get("resolved_person"):
                    df.loc[mask, "resolved_person"] = data["resolved_person"]
                updated += mask.sum()
        df.to_csv(csv_file, index=False)
        print(f"Updated {updated} rows in {csv_file.name}")
    else:
        print(f"WARNING: {csv_file} not found, skipping CSV update")

    print("\nDone.")


if __name__ == "__main__":
    main()
