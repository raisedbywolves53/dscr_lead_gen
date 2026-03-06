"""
Step 4b: SunBiz LLC Resolution for Pilot 500
=============================================

Adapter script that takes the pilot 500 CSV, identifies LLC-owned
leads that need person-name resolution, runs SunBiz lookups using
the same core logic as 04_sunbiz_llc_resolver.py, and writes
resolved results back.

Usage:
    python scrape/scripts/04b_sunbiz_pilot.py
    python scrape/scripts/04b_sunbiz_pilot.py --max-lookups 100
    python scrape/scripts/04b_sunbiz_pilot.py --dry-run
"""

import argparse
import json
import time
from pathlib import Path

import pandas as pd

# Import core SunBiz functions from script 04
from importlib.util import spec_from_file_location, module_from_spec

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent
PILOT_CSV = PROJECT_DIR / "data" / "enriched" / "pilot_500.csv"
CACHE_DIR = PROJECT_DIR / "data" / "raw"
OUTPUT_CSV = PROJECT_DIR / "data" / "filtered" / "pilot_llc_resolved.csv"

# Load script 04's functions
_spec = spec_from_file_location("sunbiz", SCRIPT_DIR / "04_sunbiz_llc_resolver.py")
_sunbiz_mod = module_from_spec(_spec)
_spec.loader.exec_module(_sunbiz_mod)

create_session = _sunbiz_mod.create_session
search_sunbiz = _sunbiz_mod.search_sunbiz
REQUEST_DELAY = _sunbiz_mod.REQUEST_DELAY
MAX_BACKOFF = _sunbiz_mod.MAX_BACKOFF
SAVE_EVERY = _sunbiz_mod.SAVE_EVERY


def load_cache() -> dict:
    """Load the pilot SunBiz cache."""
    cache_file = CACHE_DIR / "sunbiz_cache_pilot.json"
    if cache_file.exists():
        with open(cache_file) as f:
            cache = json.load(f)
        print(f"  Loaded {len(cache)} cached resolutions.")
        return cache
    return {}


def save_cache(cache: dict):
    """Save the pilot SunBiz cache."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_file = CACHE_DIR / "sunbiz_cache_pilot.json"
    with open(cache_file, "w") as f:
        json.dump(cache, f, indent=2)


def main():
    parser = argparse.ArgumentParser(description="SunBiz LLC resolution for pilot 500")
    parser.add_argument("--max-lookups", type=int, default=500,
                        help="Max SunBiz lookups (default: 500)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show what would be looked up without making requests")
    parser.add_argument("--input", type=str, default=str(PILOT_CSV),
                        help="Input CSV path")
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Pilot CSV not found: {input_path}")
        print("Run build_pilot_500.py first to generate the pilot CSV.")
        return

    df = pd.read_csv(input_path, dtype=str, low_memory=False)
    print(f"Loaded {len(df)} pilot leads from {input_path.name}")

    # Identify LLC rows needing resolution
    # is_entity = True AND resolved_person is empty/NaN
    entity_mask = df["is_entity"].astype(str).str.lower().isin(["true", "1", "yes"])
    resolved = df.get("resolved_person", pd.Series([""] * len(df), dtype=str))
    needs_resolution = entity_mask & (
        resolved.fillna("").str.strip().isin(["", "nan", "none", "NaN", "None"])
    )

    llc_count = needs_resolution.sum()
    print(f"Entity-owned leads: {entity_mask.sum()}")
    print(f"Already resolved:   {entity_mask.sum() - llc_count}")
    print(f"Need resolution:    {llc_count}")

    if llc_count == 0:
        print("All entity leads already have resolved person names.")
        OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(OUTPUT_CSV, index=False)
        print(f"Saved (unchanged): {OUTPUT_CSV}")
        return

    # Get unique entity names to look up
    unique_entities = df.loc[needs_resolution, "OWN_NAME"].dropna().unique().tolist()
    print(f"Unique LLCs to resolve: {len(unique_entities)}")

    # Load cache
    cache = load_cache()
    to_lookup = [e for e in unique_entities if e not in cache]
    already_cached = len(unique_entities) - len(to_lookup)

    if already_cached > 0:
        print(f"Already cached: {already_cached}")

    if args.dry_run:
        print(f"\nDRY RUN — would look up {min(len(to_lookup), args.max_lookups)} entities")
        for e in to_lookup[:10]:
            print(f"  {e}")
        if len(to_lookup) > 10:
            print(f"  ... and {len(to_lookup) - 10} more")
        return

    if to_lookup:
        # Prioritize by property count (entities with most properties first)
        entity_counts = (
            df.loc[needs_resolution]
            .groupby("OWN_NAME")
            .size()
            .sort_values(ascending=False)
        )
        priority_order = [e for e in entity_counts.index if e in to_lookup]
        to_lookup = priority_order[:args.max_lookups]

        print(f"Looking up {len(to_lookup)} entities...")
        print(f"Estimated time: ~{len(to_lookup) * (REQUEST_DELAY + 1) / 60:.0f} minutes")
        print()

        session = create_session()
        backoff = REQUEST_DELAY
        resolved_count = 0
        error_count = 0

        for i, entity_name in enumerate(to_lookup):
            if i > 0 and i % 10 == 0:
                print(f"  Progress: {i}/{len(to_lookup)} "
                      f"({resolved_count} resolved, {error_count} errors)")

            if i > 0 and i % SAVE_EVERY == 0:
                save_cache(cache)
                print(f"  Cache saved ({len(cache)} entries).")

            result = search_sunbiz(entity_name, session)
            cache[entity_name] = result

            if result["resolved_person"]:
                resolved_count += 1
                backoff = REQUEST_DELAY
            elif "ERROR" in result.get("status", "") or "HTTP" in result.get("status", ""):
                error_count += 1
                backoff = min(backoff * 2, MAX_BACKOFF)
                print(f"  Blocked/error on '{entity_name[:40]}'. "
                      f"Backing off {backoff:.0f}s...")
                time.sleep(backoff)
                continue

            time.sleep(REQUEST_DELAY)

        save_cache(cache)
        print(f"\nLookups complete: {resolved_count}/{len(to_lookup)} resolved")
        if error_count > 0:
            print(f"Errors: {error_count}")

    # Merge resolution data back into the pilot dataframe
    print("\nMerging resolution data...")
    for col in ["resolved_person", "registered_agent_name", "registered_agent_address",
                "officer_names", "sunbiz_filing_date", "sunbiz_status"]:
        if col not in df.columns:
            df[col] = ""

    for idx, row in df.iterrows():
        owner = str(row.get("OWN_NAME", ""))
        if owner in cache:
            res = cache[owner]
            # Only fill if currently empty
            if not str(df.at[idx, "resolved_person"]).strip() or \
               str(df.at[idx, "resolved_person"]).lower() in ("nan", "none", ""):
                df.at[idx, "resolved_person"] = res.get("resolved_person", "")
            df.at[idx, "registered_agent_name"] = res.get("registered_agent_name", "")
            df.at[idx, "registered_agent_address"] = res.get("registered_agent_address", "")
            df.at[idx, "officer_names"] = res.get("officer_names", "")
            df.at[idx, "sunbiz_filing_date"] = res.get("filing_date", "")
            df.at[idx, "sunbiz_status"] = res.get("status", "")

    # Save output
    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT_CSV, index=False)

    # Summary
    resolved_mask = df["resolved_person"].astype(str).str.strip() != ""
    resolved_mask &= ~df["resolved_person"].astype(str).str.lower().isin(["nan", "none"])
    total_resolved = resolved_mask.sum()

    print()
    print("=" * 60)
    print("  PILOT LLC RESOLUTION SUMMARY")
    print("=" * 60)
    print(f"  Total pilot leads:     {len(df)}")
    print(f"  Entity-owned:          {entity_mask.sum()}")
    print(f"  Resolved to person:    {total_resolved}")
    if entity_mask.sum() > 0:
        print(f"  Resolution rate:       {total_resolved / entity_mask.sum() * 100:.1f}%")
    print(f"  Saved: {OUTPUT_CSV}")
    print()

    # Show examples
    examples = df[resolved_mask].head(5)
    if not examples.empty:
        print("  EXAMPLE RESOLUTIONS:")
        print("  " + "-" * 55)
        for _, row in examples.iterrows():
            llc = str(row["OWN_NAME"])[:35]
            person = str(row["resolved_person"])[:30]
            print(f"  {llc:35s} -> {person}")
        print()


if __name__ == "__main__":
    main()
