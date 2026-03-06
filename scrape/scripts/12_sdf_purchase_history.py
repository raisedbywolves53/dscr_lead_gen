"""
Step 12: FDOR SDF Purchase History
====================================

Downloads and parses FDOR SDF (Sales Data File) files to build complete
purchase/sale history for each lead in our pipeline.

The SDF files are free public records from the Florida Department of Revenue,
same portal as the NAL files. Each county's SDF contains EVERY recorded sale
for EVERY parcel — sale date, price, buyer, seller, deed type, and
qualification code (arms-length vs non-arms-length).

What this script does:
  1. Downloads SDF ZIP files for target counties
  2. Parses them using chunked reading (files can be 100MB+)
  3. Matches sales records to leads by owner name or parcel ID
  4. Derives per-lead metrics: acquisitions, dispositions, flips, hold periods,
     purchase frequency, average price, cash purchase indicators, etc.
  5. Saves output to data/history/purchase_history.csv

Usage:
    python scripts/12_sdf_purchase_history.py
    python scripts/12_sdf_purchase_history.py --counties "palm_beach,broward"
    python scripts/12_sdf_purchase_history.py --input data/enriched/top_leads_enriched.csv
    python scripts/12_sdf_purchase_history.py --dry-run

Data Source:
    FDOR SDF files — https://publicfiles.tax.state.fl.us/Co_SDF/
    Free, public records under Florida Statute 119.
"""

import argparse
import hashlib
import json
import os
import re
import sys
import time
import zipfile
from datetime import datetime, timedelta
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import pandas as pd

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False
    print("WARNING: requests library not installed. Run: pip install requests")

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
HISTORY_DIR = PROJECT_DIR / "data" / "history"
CACHE_DIR = HISTORY_DIR / "sdf_cache"
DEFAULT_INPUT = PROJECT_DIR / "data" / "enriched" / "top_leads_enriched.csv"
DEFAULT_OUTPUT = HISTORY_DIR / "purchase_history.csv"

# ---------------------------------------------------------------------------
# Florida county name → FDOR county code (alphabetical, 01-67)
# ---------------------------------------------------------------------------
FL_COUNTIES = {
    "alachua": "01", "baker": "02", "bay": "03", "bradford": "04",
    "brevard": "05", "broward": "16", "calhoun": "07", "charlotte": "08",
    "citrus": "09", "clay": "10", "collier": "11", "columbia": "12",
    "dade": "13", "desoto": "14", "dixie": "15", "duval": "16",
    "escambia": "17", "flagler": "18", "franklin": "19", "gadsden": "20",
    "gilchrist": "21", "glades": "22", "gulf": "23", "hamilton": "24",
    "hardee": "25", "hendry": "26", "hernando": "27", "highlands": "28",
    "hillsborough": "29", "holmes": "30", "indian_river": "31",
    "jackson": "32", "jefferson": "33", "lafayette": "34", "lake": "35",
    "lee": "36", "leon": "37", "levy": "38", "liberty": "39",
    "madison": "40", "manatee": "41", "marion": "42", "martin": "43",
    "monroe": "44", "nassau": "45", "okaloosa": "46", "okeechobee": "47",
    "orange": "48", "osceola": "49", "palm_beach": "60", "pasco": "51",
    "pinellas": "52", "polk": "53", "putnam": "54", "st_johns": "55",
    "st_lucie": "56", "santa_rosa": "57", "sarasota": "58",
    "seminole": "59", "sumter": "60", "suwannee": "61", "taylor": "62",
    "union": "63", "volusia": "64", "wakulla": "65", "walton": "66",
    "washington": "67", "miami_dade": "13",
}

# ---------------------------------------------------------------------------
# SDF download URL patterns to try (FDOR has changed URLs over time)
# ---------------------------------------------------------------------------
SDF_URL_PATTERNS = [
    "https://publicfiles.tax.state.fl.us/Co_SDF/{code}_2024.zip",
    "https://publicfiles.tax.state.fl.us/sdf/{code}_2024.zip",
    "https://publicfiles.tax.state.fl.us/Co_SDF/{code}_2023.zip",
    "https://publicfiles.tax.state.fl.us/sdf/{code}_2023.zip",
]

# ---------------------------------------------------------------------------
# SDF column detection — common column name patterns in FDOR SDF files
# ---------------------------------------------------------------------------
# The SDF format uses pipe-delimited or tab-delimited text. Column names may
# vary slightly between years. We detect them by matching known patterns.
SDF_COLUMN_MAP = {
    # Target field → list of possible column names (case-insensitive)
    "county_code": ["CO_NO", "COUNTY_CODE", "CNTY_CD", "CO_CD"],
    "parcel_id":   ["PARCEL_ID", "PARCEL", "PCL_ID", "PARCEL_NO", "PARCELID"],
    "sale_month":  ["SALE_MO", "SALEMO", "S_MO"],
    "sale_year":   ["SALE_YR", "SALEYR", "S_YR"],
    "sale_price":  ["SALE_PRC", "SALE_PRICE", "SALEPRC", "PRICE", "SALE_PRC1"],
    "grantor":     ["GRANTOR", "GRANTOR1", "SELLER", "GRANTOR_NAME"],
    "grantee":     ["GRANTEE", "GRANTEE1", "BUYER", "GRANTEE_NAME"],
    "deed_code":   ["DEED_CD", "DEED_CODE", "DEED_TYPE", "DEEDCD"],
    "vi_code":     ["VI_CD", "VICD", "VAC_IMP", "VACANT_IMPROVED"],
    "qual_code":   ["QUAL_CD", "QUALCD", "QUAL_CODE", "QUALIFICATION_CODE"],
}

# Chunk size for reading large SDF files
CHUNK_SIZE = 50_000


# ===========================================================================
# Download SDF files
# ===========================================================================

def resolve_county_code(county_name: str) -> str:
    """Look up the FDOR code for a county name. Returns None if not found."""
    # Normalize: lowercase, replace spaces and hyphens with underscores
    normalized = county_name.strip().lower().replace(" ", "_").replace("-", "_")
    code = FL_COUNTIES.get(normalized)
    if code:
        return code

    # Try without underscores (e.g., "palmbeach" → "palm_beach")
    for key, val in FL_COUNTIES.items():
        if key.replace("_", "") == normalized.replace("_", ""):
            return val

    return None


def download_sdf(county_name: str, dry_run: bool = False) -> Path:
    """
    Download the SDF ZIP for a county. Tries multiple URL patterns.
    Returns the path to the extracted CSV/TXT, or None on failure.
    """
    code = resolve_county_code(county_name)
    if not code:
        print(f"  ERROR: Unknown county '{county_name}'.")
        print(f"  Known counties: {', '.join(sorted(FL_COUNTIES.keys()))}")
        return None

    HISTORY_DIR.mkdir(parents=True, exist_ok=True)

    # Check if we already have extracted data
    for ext in [".txt", ".csv"]:
        for year in ["2025", "2024", "2023"]:
            candidate = HISTORY_DIR / f"{code}_{year}_sdf{ext}"
            if candidate.exists() and candidate.stat().st_size > 0:
                size_mb = candidate.stat().st_size / (1024 * 1024)
                print(f"  Already have SDF data: {candidate.name} ({size_mb:.1f} MB)")
                return candidate

    if dry_run:
        print(f"  [DRY RUN] Would download SDF for {county_name} (code {code})")
        for pattern in SDF_URL_PATTERNS:
            print(f"    Would try: {pattern.format(code=code)}")
        return None

    if not HAS_REQUESTS:
        print("  ERROR: requests library required for download.")
        return None

    # Try each URL pattern
    for pattern in SDF_URL_PATTERNS:
        url = pattern.format(code=code)
        print(f"  Trying: {url}")

        try:
            resp = requests.get(url, timeout=120, stream=True)
            if resp.status_code == 200:
                # Save the ZIP
                zip_path = HISTORY_DIR / f"{code}_sdf.zip"
                total_size = int(resp.headers.get("content-length", 0))
                downloaded = 0

                with open(zip_path, "wb") as f:
                    for chunk in resp.iter_content(chunk_size=8192):
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0:
                            pct = downloaded / total_size * 100
                            print(f"\r  Downloading... {pct:.0f}%", end="", flush=True)

                print(f"\r  Downloaded: {zip_path.name} ({downloaded / (1024*1024):.1f} MB)        ")

                # Extract
                try:
                    extracted_path = _extract_sdf_zip(zip_path, code)
                    zip_path.unlink(missing_ok=True)
                    return extracted_path
                except Exception as e:
                    print(f"  ERROR extracting ZIP: {e}")
                    zip_path.unlink(missing_ok=True)
                    continue

            else:
                print(f"    Status {resp.status_code} — skipping this URL")

        except requests.RequestException as e:
            print(f"    Request error: {e}")
            continue

    # All URL patterns failed
    print()
    print(f"  Could not auto-download SDF for {county_name} (code {code}).")
    print(f"  Please download manually from the FDOR data portal:")
    print(f"    https://floridarevenue.com/property/dataportal/")
    print(f"  Look for: Sales Data Files > SDF > county code {code}")
    print(f"  Save the extracted file to: {HISTORY_DIR}/{code}_2024_sdf.txt")
    print()
    return None


def _extract_sdf_zip(zip_path: Path, code: str) -> Path:
    """Extract the first CSV/TXT file from an SDF ZIP archive."""
    with zipfile.ZipFile(zip_path, "r") as z:
        # Look for data files inside the ZIP
        data_files = [
            f for f in z.namelist()
            if f.lower().endswith((".csv", ".txt"))
            and not f.startswith("__MACOSX")
            and not f.startswith(".")
        ]

        if not data_files:
            raise ValueError(f"No CSV/TXT files found in ZIP. Contents: {z.namelist()}")

        # Pick the largest file (the actual data, not a readme)
        data_files.sort(key=lambda f: z.getinfo(f).file_size, reverse=True)
        target = data_files[0]
        print(f"  Extracting: {target}")

        z.extract(target, HISTORY_DIR)
        extracted = HISTORY_DIR / target

        # Determine year from filename or ZIP name
        year = "2024"
        if "2023" in str(zip_path) or "2023" in target:
            year = "2023"

        # Rename to standard format
        ext = extracted.suffix
        final_path = HISTORY_DIR / f"{code}_{year}_sdf{ext}"
        extracted.rename(final_path)

        size_mb = final_path.stat().st_size / (1024 * 1024)
        print(f"  Saved: {final_path.name} ({size_mb:.1f} MB)")
        return final_path


# ===========================================================================
# Parse SDF files
# ===========================================================================

def detect_delimiter(file_path: Path) -> str:
    """Read the first few lines and detect whether file is pipe or tab delimited."""
    with open(file_path, "r", encoding="latin-1", errors="replace") as f:
        header = f.readline()
        second = f.readline()

    # Count delimiters in header
    pipes = header.count("|")
    tabs = header.count("\t")
    commas = header.count(",")

    if pipes > tabs and pipes > commas:
        return "|"
    elif tabs > commas:
        return "\t"
    else:
        return ","


def detect_columns(header_cols: list) -> dict:
    """
    Map actual column names in the file to our standard field names.
    Returns a dict: {standard_name: actual_column_name}.
    """
    # Uppercase all header columns for comparison
    upper_cols = {col.upper().strip(): col for col in header_cols}

    mapping = {}
    for standard_name, candidates in SDF_COLUMN_MAP.items():
        for candidate in candidates:
            if candidate.upper() in upper_cols:
                mapping[standard_name] = upper_cols[candidate.upper()]
                break

    return mapping


def parse_sdf_cached(file_path: Path) -> pd.DataFrame:
    """
    Parse an SDF file into a DataFrame. Uses a parquet cache to avoid
    re-parsing the huge text file on every run.
    """
    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    # Build cache key from file path and modification time
    file_stat = file_path.stat()
    cache_key = hashlib.md5(
        f"{file_path.name}:{file_stat.st_size}:{file_stat.st_mtime}".encode()
    ).hexdigest()[:12]
    cache_path = CACHE_DIR / f"{file_path.stem}_{cache_key}.parquet"

    if cache_path.exists():
        size_mb = cache_path.stat().st_size / (1024 * 1024)
        print(f"  Loading cached SDF data: {cache_path.name} ({size_mb:.1f} MB)")
        return pd.read_parquet(cache_path)

    print(f"  Parsing SDF file: {file_path.name} (this may take a minute)...")

    # Detect delimiter
    delimiter = detect_delimiter(file_path)
    print(f"  Detected delimiter: {'pipe' if delimiter == '|' else 'tab' if delimiter == chr(9) else 'comma'}")

    # Read header to detect columns
    header_df = pd.read_csv(
        file_path,
        sep=delimiter,
        nrows=0,
        encoding="latin-1",
        dtype=str,
    )
    actual_cols = list(header_df.columns)
    col_map = detect_columns(actual_cols)

    print(f"  Found {len(actual_cols)} columns, mapped {len(col_map)} standard fields")
    for std, actual in col_map.items():
        print(f"    {std} → {actual}")

    if "parcel_id" not in col_map:
        print("  WARNING: Could not detect PARCEL_ID column. Trying first column.")
        col_map["parcel_id"] = actual_cols[0]

    # Determine which columns to load (only the ones we need)
    usecols = list(col_map.values())

    # Read in chunks
    chunks = []
    total_rows = 0
    reader = pd.read_csv(
        file_path,
        sep=delimiter,
        chunksize=CHUNK_SIZE,
        encoding="latin-1",
        dtype=str,
        usecols=usecols,
        on_bad_lines="skip",
    )

    for i, chunk in enumerate(reader):
        total_rows += len(chunk)
        chunks.append(chunk)
        if (i + 1) % 5 == 0:
            print(f"    Read {total_rows:,} rows...", flush=True)

    df = pd.concat(chunks, ignore_index=True)
    print(f"  Total rows parsed: {total_rows:,}")

    # Rename columns to standard names
    reverse_map = {actual: std for std, actual in col_map.items()}
    df.rename(columns=reverse_map, inplace=True)

    # Clean up key fields
    if "parcel_id" in df.columns:
        df["parcel_id"] = df["parcel_id"].astype(str).str.strip()

    # Parse sale price to numeric
    if "sale_price" in df.columns:
        df["sale_price"] = pd.to_numeric(
            df["sale_price"].astype(str).str.replace(",", "").str.strip(),
            errors="coerce"
        ).fillna(0).astype(int)

    # Build a sale_date column from month + year
    if "sale_month" in df.columns and "sale_year" in df.columns:
        df["sale_month"] = pd.to_numeric(df["sale_month"], errors="coerce").fillna(1).astype(int)
        df["sale_year"] = pd.to_numeric(df["sale_year"], errors="coerce").fillna(0).astype(int)
        # Create a date (use first of month)
        df["sale_date"] = pd.to_datetime(
            df["sale_year"].astype(str) + "-" + df["sale_month"].astype(str).str.zfill(2) + "-01",
            format="%Y-%m-%d",
            errors="coerce",
        )
    else:
        df["sale_date"] = pd.NaT

    # Uppercase name fields for matching
    for col in ["grantor", "grantee"]:
        if col in df.columns:
            df[col] = df[col].astype(str).str.upper().str.strip()

    # Cache as parquet for fast reload
    try:
        df.to_parquet(cache_path, index=False)
        size_mb = cache_path.stat().st_size / (1024 * 1024)
        print(f"  Cached parsed data: {cache_path.name} ({size_mb:.1f} MB)")
    except Exception as e:
        print(f"  WARNING: Could not cache parquet (pyarrow may not be installed): {e}")
        print(f"  Install with: pip install pyarrow")

    return df


# ===========================================================================
# Match sales to leads
# ===========================================================================

def normalize_name(name: str) -> str:
    """Normalize a name for fuzzy matching: uppercase, remove punctuation, extra spaces."""
    if not name or pd.isna(name):
        return ""
    name = str(name).upper().strip()
    # Remove common suffixes that may differ between SDF and lead data
    name = re.sub(r"\b(LLC|INC|CORP|LTD|LP|LLLP|TRUST|TR|ETAL|ET AL|JTRS|JT TEN)\b", "", name)
    # Remove punctuation
    name = re.sub(r"[^A-Z0-9 ]", "", name)
    # Collapse whitespace
    name = re.sub(r"\s+", " ", name).strip()
    return name


def build_name_lookup(sdf_df: pd.DataFrame) -> dict:
    """
    Build a dictionary from normalized name → list of row indices in the SDF
    for both GRANTOR and GRANTEE fields. This allows O(1) lookup per lead name.
    """
    print("  Building name lookup index...")
    name_index = {}

    for col in ["grantor", "grantee"]:
        if col not in sdf_df.columns:
            continue
        for idx, name in sdf_df[col].items():
            norm = normalize_name(name)
            if len(norm) < 3:  # skip blanks and very short names
                continue
            if norm not in name_index:
                name_index[norm] = {"as_buyer": [], "as_seller": []}
            if col == "grantee":
                name_index[norm]["as_buyer"].append(idx)
            else:
                name_index[norm]["as_seller"].append(idx)

    print(f"  Name index: {len(name_index):,} unique names")
    return name_index


def build_parcel_lookup(sdf_df: pd.DataFrame) -> dict:
    """Build parcel_id → list of row indices for parcel-based matching."""
    print("  Building parcel lookup index...")
    parcel_index = {}

    if "parcel_id" not in sdf_df.columns:
        return parcel_index

    for idx, pid in sdf_df["parcel_id"].items():
        pid = str(pid).strip()
        if len(pid) < 3:
            continue
        if pid not in parcel_index:
            parcel_index[pid] = []
        parcel_index[pid].append(idx)

    print(f"  Parcel index: {len(parcel_index):,} unique parcels")
    return parcel_index


def match_lead_sales(
    lead_row: pd.Series,
    sdf_df: pd.DataFrame,
    name_index: dict,
    parcel_index: dict,
) -> pd.DataFrame:
    """
    Find all SDF sales records matching a single lead, by:
      1. Owner name (OWN_NAME) appearing as GRANTEE or GRANTOR
      2. Parcel IDs from the lead's property data
    Returns a DataFrame of matching sales records.
    """
    matching_indices = set()

    # --- Match by owner name ---
    own_name = str(lead_row.get("OWN_NAME", lead_row.get("own_name", ""))).strip()
    norm_name = normalize_name(own_name)

    if norm_name and norm_name in name_index:
        entry = name_index[norm_name]
        matching_indices.update(entry.get("as_buyer", []))
        matching_indices.update(entry.get("as_seller", []))

    # Also try resolved person name if available
    for person_col in ["resolved_name", "person_name", "RESOLVED_NAME"]:
        person_name = str(lead_row.get(person_col, "")).strip()
        if person_name and person_name.lower() not in ("nan", "none", ""):
            norm_person = normalize_name(person_name)
            if norm_person and norm_person in name_index:
                entry = name_index[norm_person]
                matching_indices.update(entry.get("as_buyer", []))
                matching_indices.update(entry.get("as_seller", []))

    # --- Match by parcel ID ---
    for parcel_col in ["PARCEL_ID", "parcel_id", "PCL_ID"]:
        pid = str(lead_row.get(parcel_col, "")).strip()
        if pid and pid.lower() not in ("nan", "none", "") and pid in parcel_index:
            matching_indices.update(parcel_index[pid])

    # Also check PHY_ADDR1 for pipe-delimited parcel lists (from aggregated data)
    # This handles the case where multiple parcels are stored in one field
    for addr_col in ["PHY_ADDR1", "phy_addr1"]:
        addr = str(lead_row.get(addr_col, "")).strip()
        if "|" in addr:
            # These are pipe-delimited addresses, not parcel IDs — skip
            pass

    if not matching_indices:
        return pd.DataFrame()

    return sdf_df.loc[list(matching_indices)].copy()


# ===========================================================================
# Derive per-lead metrics
# ===========================================================================

def derive_metrics(sales_df: pd.DataFrame, lead_name: str) -> dict:
    """
    Given all sales records for a lead, derive purchase history metrics.
    """
    now = datetime.now()
    twelve_mo_ago = now - timedelta(days=365)
    thirty_six_mo_ago = now - timedelta(days=365 * 3)

    norm_lead = normalize_name(lead_name)

    # Split into acquisitions (lead is GRANTEE/buyer) and dispositions (lead is GRANTOR/seller)
    acquisitions = pd.DataFrame()
    dispositions = pd.DataFrame()

    if "grantee" in sales_df.columns:
        buyer_mask = sales_df["grantee"].apply(lambda x: normalize_name(x) == norm_lead)
        acquisitions = sales_df[buyer_mask].copy()

    if "grantor" in sales_df.columns:
        seller_mask = sales_df["grantor"].apply(lambda x: normalize_name(x) == norm_lead)
        dispositions = sales_df[seller_mask].copy()

    # If we matched by parcel only and can't distinguish buyer/seller,
    # treat all records as general transactions
    all_sales = sales_df.copy()

    # When no grantor/grantee available, use all_sales as the transaction source
    has_buyer_seller = len(acquisitions) > 0 or len(dispositions) > 0
    transaction_source = acquisitions if has_buyer_seller else all_sales

    # Count acquisitions and dispositions
    total_acquisitions = len(acquisitions) if has_buyer_seller else len(all_sales)
    total_dispositions = len(dispositions)

    # Filter to valid dates
    if has_buyer_seller:
        acq_dated = acquisitions[acquisitions["sale_date"].notna()] if len(acquisitions) > 0 else pd.DataFrame()
        disp_dated = dispositions[dispositions["sale_date"].notna()] if len(dispositions) > 0 else pd.DataFrame()
    else:
        acq_dated = all_sales[all_sales["sale_date"].notna()] if len(all_sales) > 0 else pd.DataFrame()
        disp_dated = pd.DataFrame()

    # Purchases in last 12 and 36 months
    purchases_12mo = 0
    purchases_36mo = 0
    if len(acq_dated) > 0:
        purchases_12mo = int((acq_dated["sale_date"] >= twelve_mo_ago).sum())
        purchases_36mo = int((acq_dated["sale_date"] >= thirty_six_mo_ago).sum())

    # Average purchase price (exclude $0 and $100 non-arms-length transfers)
    real_purchases = transaction_source[transaction_source["sale_price"] > 100] if len(transaction_source) > 0 else pd.DataFrame()
    avg_purchase_price = int(real_purchases["sale_price"].mean()) if len(real_purchases) > 0 else 0

    # Most recent purchase
    most_recent_date = ""
    most_recent_price = 0
    if len(acq_dated) > 0:
        latest = acq_dated.sort_values("sale_date", ascending=False).iloc[0]
        most_recent_date = latest["sale_date"].strftime("%Y-%m-%d") if pd.notna(latest["sale_date"]) else ""
        most_recent_price = int(latest.get("sale_price", 0))

    # Flip detection: properties bought and sold within 12 months
    flip_count = 0
    hold_count = 0
    hold_periods = []

    if len(acq_dated) > 0 and len(disp_dated) > 0:
        # For each acquisition, check if there's a disposition of the same parcel
        for _, acq in acq_dated.iterrows():
            acq_parcel = str(acq.get("parcel_id", "")).strip()
            acq_date = acq["sale_date"]

            if not acq_parcel or pd.isna(acq_date):
                continue

            # Find dispositions of the same parcel after the acquisition
            matching_disps = disp_dated[
                (disp_dated["parcel_id"].astype(str).str.strip() == acq_parcel)
                & (disp_dated["sale_date"] > acq_date)
            ]

            if len(matching_disps) > 0:
                first_disp = matching_disps.sort_values("sale_date").iloc[0]
                hold_months = (first_disp["sale_date"] - acq_date).days / 30.44
                hold_periods.append(hold_months)

                if hold_months <= 12:
                    flip_count += 1
                else:
                    hold_count += 1
            else:
                # Still holding — count as a hold
                hold_months = (now - acq_date).days / 30.44
                hold_periods.append(hold_months)
                hold_count += 1

    avg_hold_period = round(sum(hold_periods) / len(hold_periods), 1) if hold_periods else 0

    # Off-market / non-arms-length transfers ($0 or $100 sale price)
    off_market_count = 0
    if len(all_sales) > 0:
        off_market_count = int((all_sales["sale_price"] <= 100).sum())

    # Cash purchase percentage (estimated: qual_code or cross-reference later)
    # For now, we flag purchases where qualification code suggests non-standard
    cash_purchase_pct = 0.0
    if "qual_code" in all_sales.columns and len(real_purchases) > 0:
        # Qual codes vary, but "U" typically means unqualified/non-arms-length
        # This is a rough proxy — true cash detection needs mortgage data (Step 11)
        pass  # Will be refined when cross-referenced with county clerk data

    # Purchase frequency (average months between sequential purchases)
    purchase_frequency = 0
    if len(acq_dated) >= 2:
        sorted_dates = acq_dated["sale_date"].sort_values()
        diffs = sorted_dates.diff().dropna()
        avg_days = diffs.dt.days.mean()
        purchase_frequency = round(avg_days / 30.44, 1) if avg_days > 0 else 0

    return {
        "total_acquisitions": total_acquisitions,
        "total_dispositions": total_dispositions,
        "purchases_last_12mo": purchases_12mo,
        "purchases_last_36mo": purchases_36mo,
        "avg_purchase_price": avg_purchase_price,
        "most_recent_purchase_date": most_recent_date,
        "most_recent_purchase_price": most_recent_price,
        "flip_count": flip_count,
        "hold_count": hold_count,
        "avg_hold_period_months": avg_hold_period,
        "cash_purchase_pct": round(cash_purchase_pct, 1),
        "off_market_count": off_market_count,
        "purchase_frequency_months": purchase_frequency,
        "total_sales_records": len(all_sales),
    }


# ===========================================================================
# Main
# ===========================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Step 12: FDOR SDF Purchase History Analysis"
    )
    parser.add_argument(
        "--counties",
        type=str,
        default="palm_beach,broward",
        help='Comma-separated county names (default: "palm_beach,broward")',
    )
    parser.add_argument(
        "--input",
        type=str,
        default=str(DEFAULT_INPUT),
        help=f"Input leads CSV (default: {DEFAULT_INPUT})",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=str(DEFAULT_OUTPUT),
        help=f"Output CSV path (default: {DEFAULT_OUTPUT})",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be downloaded without downloading",
    )
    args = parser.parse_args()

    print()
    print("=" * 70)
    print("  STEP 12: FDOR SDF PURCHASE HISTORY")
    print("=" * 70)
    print()

    counties = [c.strip() for c in args.counties.split(",")]
    input_path = Path(args.input)
    output_path = Path(args.output)

    print(f"  Counties:  {', '.join(counties)}")
    print(f"  Input:     {input_path}")
    print(f"  Output:    {output_path}")
    print()

    # -------------------------------------------------------------------
    # 1. Download SDF files for target counties
    # -------------------------------------------------------------------
    print("-" * 50)
    print("PHASE 1: Download SDF files")
    print("-" * 50)

    sdf_files = {}
    for county in counties:
        print(f"\n  [{county.upper()}]")
        sdf_path = download_sdf(county, dry_run=args.dry_run)
        if sdf_path:
            sdf_files[county] = sdf_path

    if args.dry_run:
        print("\n[DRY RUN] No files downloaded. Exiting.")
        return

    if not sdf_files:
        print("\n  ERROR: No SDF files available. Cannot proceed.")
        print("  Download SDF files manually and place in:")
        print(f"    {HISTORY_DIR}/")
        sys.exit(1)

    # -------------------------------------------------------------------
    # 2. Parse SDF files
    # -------------------------------------------------------------------
    print()
    print("-" * 50)
    print("PHASE 2: Parse SDF files")
    print("-" * 50)

    sdf_frames = []
    for county, path in sdf_files.items():
        print(f"\n  [{county.upper()}]")
        df = parse_sdf_cached(path)
        sdf_frames.append(df)

    sdf_all = pd.concat(sdf_frames, ignore_index=True)
    print(f"\n  Combined SDF data: {len(sdf_all):,} total sales records")

    # -------------------------------------------------------------------
    # 3. Build lookup indices
    # -------------------------------------------------------------------
    print()
    print("-" * 50)
    print("PHASE 3: Build lookup indices")
    print("-" * 50)

    name_index = build_name_lookup(sdf_all)
    parcel_index = build_parcel_lookup(sdf_all)

    # -------------------------------------------------------------------
    # 3.5 Resolve owner names to parcel IDs via Property Appraiser APIs
    # -------------------------------------------------------------------
    print()
    print("-" * 50)
    print("PHASE 3.5: Resolve owner names to parcels (PAO API)")
    print("-" * 50)

    if not input_path.exists():
        print(f"\n  ERROR: Input file not found: {input_path}")
        print(f"  Run earlier pipeline steps first, or specify --input.")
        sys.exit(1)

    leads = pd.read_csv(input_path, dtype=str)
    print(f"\n  Loaded {len(leads):,} leads from {input_path.name}")

    # Determine which column has the owner name
    name_col = None
    for col in ["OWN_NAME", "own_name", "OWNER_NAME", "owner_name", "name"]:
        if col in leads.columns:
            name_col = col
            break

    if not name_col:
        print("  ERROR: Cannot find owner name column in leads file.")
        print(f"  Available columns: {list(leads.columns)}")
        sys.exit(1)

    print(f"  Using name column: {name_col}")

    # Cache for PAO lookups
    pao_cache_path = CACHE_DIR / "pao_parcel_cache.json"
    pao_cache = {}
    if pao_cache_path.exists():
        with open(pao_cache_path, "r") as f:
            pao_cache = json.load(f)
        print(f"  PAO cache: {len(pao_cache)} entries loaded")

    # Build owner→parcels mapping via PAO APIs
    owner_parcels = {}
    lookups_needed = 0
    lookups_done = 0

    for _, lead in leads.iterrows():
        owner_name = str(lead.get(name_col, "")).strip()
        co_no = str(lead.get("CO_NO", "")).strip()
        if not owner_name:
            continue

        cache_key = f"{co_no}:{owner_name}"
        if cache_key in pao_cache:
            owner_parcels[owner_name] = pao_cache[cache_key]
        else:
            lookups_needed += 1

    print(f"  Need PAO lookups: {lookups_needed}")
    print(f"  Already cached:   {len(pao_cache) - (len(leads) - lookups_needed - len([1 for _,l in leads.iterrows() if not str(l.get(name_col,'')).strip()]))}")

    if lookups_needed > 0 and HAS_REQUESTS:
        print(f"\n  Resolving owner names to parcels via Property Appraiser APIs...")
        print(f"  Estimated time: ~{lookups_needed * 0.5:.0f}s ({lookups_needed * 0.5 / 60:.1f} min)\n")

        for i, (_, lead) in enumerate(leads.iterrows()):
            owner_name = str(lead.get(name_col, "")).strip()
            co_no = str(lead.get("CO_NO", "")).strip()
            if not owner_name:
                continue

            cache_key = f"{co_no}:{owner_name}"
            if cache_key in pao_cache:
                continue

            parcels = []
            try:
                if co_no == "60":
                    # Palm Beach County PAO
                    resp = requests.post(
                        "https://pbcpao.gov/AutoComplete/GetOwners",
                        data={"ownerName": owner_name},
                        headers={"User-Agent": "Mozilla/5.0"},
                        timeout=10,
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        parcels = [item["pcn"] for item in data if item.get("pcn")]
                elif co_no == "16":
                    # Broward County PA
                    resp = requests.post(
                        "https://web.bcpa.net/BcpaClient/search.aspx/GetData",
                        json={
                            "value": owner_name,
                            "cities": "", "orderBy": "", "pageNumber": "1",
                            "pageCount": "50", "arrayOfValues": "",
                            "selectedFromList": "false", "totalCount": "0",
                        },
                        headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"},
                        timeout=10,
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        rows = data.get("d", {}).get("Data", []) if isinstance(data.get("d"), dict) else []
                        parcels = [r.get("folioNumber", "") for r in rows if r.get("folioNumber")]
            except Exception as e:
                pass  # silently skip failures

            pao_cache[cache_key] = parcels
            owner_parcels[owner_name] = parcels
            lookups_done += 1

            if lookups_done % 50 == 0:
                print(f"  Resolved {lookups_done}/{lookups_needed}... ({sum(len(v) for v in owner_parcels.values() if v)} total parcels)")
                # Save cache periodically
                with open(pao_cache_path, "w") as f:
                    json.dump(pao_cache, f)

            time.sleep(0.3)  # rate limit

        # Final cache save
        with open(pao_cache_path, "w") as f:
            json.dump(pao_cache, f)

    total_parcels = sum(len(v) for v in owner_parcels.values() if v)
    owners_with_parcels = sum(1 for v in owner_parcels.values() if v)
    print(f"\n  Resolved: {owners_with_parcels} owners → {total_parcels} parcels")

    # Add resolved parcels to the parcel index match
    for owner_name, parcels in owner_parcels.items():
        for pid in parcels:
            pid_clean = str(pid).strip().strip('"')
            if pid_clean in parcel_index:
                # Already indexed — these will be found during matching
                pass

    # -------------------------------------------------------------------
    # 4. Match sales to leads
    # -------------------------------------------------------------------
    print()
    print("-" * 50)
    print("PHASE 4: Match sales to leads")
    print("-" * 50)

    print(f"  Matching {len(leads):,} leads against {len(sdf_all):,} SDF records")

    # Process each lead
    results = []
    matched_count = 0

    for i, (idx, lead) in enumerate(leads.iterrows()):
        owner_name = str(lead.get(name_col, "")).strip()

        if i > 0 and i % 100 == 0:
            print(f"  Processed {i:,}/{len(leads):,} leads... ({matched_count} matched)")

        # Get resolved parcels for this owner
        lead_parcels = owner_parcels.get(owner_name, [])

        # Match via parcel index using resolved parcels
        matching_indices = set()
        for pid in lead_parcels:
            pid_clean = str(pid).strip().strip('"')
            if pid_clean in parcel_index:
                matching_indices.update(parcel_index[pid_clean])

        # Also try name index (in case SDF has grantor/grantee)
        norm_name = normalize_name(owner_name)
        if norm_name and norm_name in name_index:
            entry = name_index[norm_name]
            matching_indices.update(entry.get("as_buyer", []))
            matching_indices.update(entry.get("as_seller", []))

        if matching_indices:
            sales = sdf_all.loc[list(matching_indices)].copy()
        else:
            sales = pd.DataFrame()

        if len(sales) > 0:
            matched_count += 1
            metrics = derive_metrics(sales, owner_name)
        else:
            metrics = {
                "total_acquisitions": 0,
                "total_dispositions": 0,
                "purchases_last_12mo": 0,
                "purchases_last_36mo": 0,
                "avg_purchase_price": 0,
                "most_recent_purchase_date": "",
                "most_recent_purchase_price": 0,
                "flip_count": 0,
                "hold_count": 0,
                "avg_hold_period_months": 0,
                "cash_purchase_pct": 0,
                "off_market_count": 0,
                "purchase_frequency_months": 0,
                "total_sales_records": 0,
            }

        # Carry forward key identifying columns from the lead
        row = {name_col: owner_name}
        for carry_col in ["PARCEL_ID", "parcel_id", "PHY_ADDR1", "phy_addr1",
                          "resolved_name", "person_name", "entity_name",
                          "icp_score", "icp_segment"]:
            if carry_col in lead.index:
                row[carry_col] = lead[carry_col]

        row.update(metrics)
        results.append(row)

    print(f"\n  Matching complete: {matched_count}/{len(leads)} leads have purchase history")

    # -------------------------------------------------------------------
    # 5. Save output
    # -------------------------------------------------------------------
    print()
    print("-" * 50)
    print("PHASE 5: Save output")
    print("-" * 50)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    result_df = pd.DataFrame(results)
    result_df.to_csv(output_path, index=False)
    print(f"\n  Saved: {output_path}")
    print(f"  Rows:  {len(result_df):,}")

    # -------------------------------------------------------------------
    # Summary stats
    # -------------------------------------------------------------------
    print()
    print("=" * 70)
    print("  SUMMARY")
    print("=" * 70)

    has_history = result_df[result_df["total_sales_records"] > 0]
    print(f"  Total leads processed:          {len(result_df):,}")
    print(f"  Leads with purchase history:    {len(has_history):,} ({len(has_history)/len(result_df)*100:.1f}%)")

    if len(has_history) > 0:
        print(f"  Avg acquisitions per lead:      {has_history['total_acquisitions'].mean():.1f}")
        print(f"  Avg dispositions per lead:      {has_history['total_dispositions'].mean():.1f}")

        active_12 = has_history[has_history["purchases_last_12mo"] > 0]
        active_36 = has_history[has_history["purchases_last_36mo"] > 0]
        flippers = has_history[has_history["flip_count"] > 0]

        print(f"  Active buyers (last 12mo):      {len(active_12):,}")
        print(f"  Active buyers (last 36mo):      {len(active_36):,}")
        print(f"  Flippers detected:              {len(flippers):,}")

        avg_price = has_history[has_history["avg_purchase_price"] > 0]["avg_purchase_price"]
        if len(avg_price) > 0:
            print(f"  Avg purchase price:             ${avg_price.mean():,.0f}")

        off_market = has_history[has_history["off_market_count"] > 0]
        print(f"  Leads with off-market deals:    {len(off_market):,}")

    print()
    print(f"  Next step: python scripts/13_rental_estimates.py")
    print()


if __name__ == "__main__":
    main()
