"""
Build Google Sheets MVP — 3 Sheets for DSCR Lead Gen
=====================================================

Sheet 1: "Frank's Call Sheet" — Optimized for phone outreach
Sheet 2: "Outreach Battlecards" — Full dossier for personalized email/copy
Sheet 3: "Performance Tracker" — Log outcomes, track conversions by ICP

Uses OAuth2 (desktop app) for Google Sheets API access.
First run opens browser for Google sign-in, then caches token locally.

Usage:
    python scripts/build_google_sheets.py
    python scripts/build_google_sheets.py --xlsx-only   # Export xlsx without uploading
"""

import os
import sys
import json
import argparse
from pathlib import Path

import pandas as pd
import numpy as np

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
PROJECT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_DIR / "data" / "mvp"
INPUT_FILE = DATA_DIR / "pilot_500_master.csv"
XLSX_OUTPUT = DATA_DIR / "dscr_mvp_sheets.xlsx"
TOKEN_FILE = PROJECT_DIR / "google_token.json"

# Google API scopes
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
]


# ---------------------------------------------------------------------------
# Google Auth (OAuth2 desktop flow)
# ---------------------------------------------------------------------------
def get_google_creds():
    """Authenticate via OAuth2 desktop flow. Caches token locally."""
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request

    creds = None
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            oauth_path = os.getenv("GOOGLE_OAUTH_CREDENTIALS", "")
            if not oauth_path or not Path(oauth_path).exists():
                print("ERROR: Set GOOGLE_OAUTH_CREDENTIALS in .env to your OAuth client JSON file")
                sys.exit(1)
            flow = InstalledAppFlow.from_client_secrets_file(oauth_path, SCOPES)
            creds = flow.run_local_server(port=0)

        with open(TOKEN_FILE, "w") as f:
            f.write(creds.to_json())
        print("Google auth token saved.")

    return creds


# ---------------------------------------------------------------------------
# Load and prepare data
# ---------------------------------------------------------------------------
def load_master_data():
    """Load pilot_500_master.csv and prepare for sheets."""
    if not INPUT_FILE.exists():
        print(f"ERROR: {INPUT_FILE} not found. Run the data cleanup first.")
        sys.exit(1)

    df = pd.read_csv(INPUT_FILE, dtype=str, low_memory=False)
    print(f"Loaded {len(df)} leads from {INPUT_FILE.name}")
    return df


def currency(val):
    """Format numeric string as currency."""
    try:
        v = float(val)
        if v >= 1_000_000:
            return f"${v/1_000_000:.1f}M"
        elif v >= 1_000:
            return f"${v/1_000:.0f}K"
        else:
            return f"${v:.0f}"
    except (ValueError, TypeError):
        return ""


def pct(val):
    """Format numeric string as percentage."""
    try:
        return f"{float(val)*100:.0f}%"
    except (ValueError, TypeError):
        return ""


# ---------------------------------------------------------------------------
# Sheet 1: Frank's Call Sheet
# ---------------------------------------------------------------------------
def build_call_sheet(df):
    """
    Frank's view — one row per callable lead, sorted by priority.
    Only leads with a phone number. Clean, scannable, action-oriented.
    """
    callable_df = df[df["phone_1"].notna() & (df["phone_1"] != "")].copy()

    # Sort by score descending
    callable_df["_sort_score"] = pd.to_numeric(callable_df.get("_score", 0), errors="coerce").fillna(0)
    callable_df = callable_df.sort_values("_sort_score", ascending=False)

    out = pd.DataFrame()
    out["Priority"] = range(1, len(callable_df) + 1)
    out["Contact Name"] = callable_df["contact_name"].values
    out["Phone"] = callable_df["phone_1"].values
    out["Phone 2"] = callable_df.get("phone_2", "").values
    out["Entity"] = callable_df.apply(
        lambda r: r["OWN_NAME"] if r.get("is_entity") == "True" else "", axis=1
    ).values
    out["ICP Segment"] = callable_df.get("_icp", "").values
    out["Score"] = callable_df.get("_score", "").values
    out["Properties"] = callable_df.get("property_count", "").values
    out["Portfolio Value"] = callable_df["total_portfolio_value"].apply(currency).values
    out["Current Lender"] = callable_df.get("clean_lender", "").values
    out["Est. Equity"] = callable_df["estimated_equity"].apply(currency).values
    out["Est. DSCR"] = callable_df.get("est_dscr", "").values
    out["Talking Points"] = callable_df.get("talking_points", "").values
    out["County"] = callable_df["CO_NO"].map({"60": "Palm Beach", "16": "Broward"}).fillna("").values
    out["Email"] = callable_df.get("email_1", "").values

    # Outcome tracking columns (Frank fills these in)
    out["Call Status"] = ""
    out["Call Date"] = ""
    out["Notes"] = ""
    out["Follow-Up Date"] = ""
    out["Interested?"] = ""

    # Replace NaN with empty string
    out = out.fillna("")

    print(f"  Call Sheet: {len(out)} callable leads")
    return out


# ---------------------------------------------------------------------------
# Sheet 2: Outreach Battlecards (for copy/email personalization)
# ---------------------------------------------------------------------------
def build_battlecards(df):
    """
    Full dossier per lead — everything needed to craft personalized outreach.
    All 500 leads (not just those with phones).
    """
    df_sorted = df.copy()
    df_sorted["_sort_score"] = pd.to_numeric(df_sorted.get("_score", 0), errors="coerce").fillna(0)
    df_sorted = df_sorted.sort_values("_sort_score", ascending=False)

    out = pd.DataFrame()

    # Identity
    out["Contact Name"] = df_sorted.get("contact_name", "").values
    out["Entity Name"] = df_sorted["OWN_NAME"].values
    out["ICP Segment"] = df_sorted.get("_icp", "").values
    out["Score"] = df_sorted.get("_score", "").values
    out["Email 1"] = df_sorted.get("email_1", "").values
    out["Email 2"] = df_sorted.get("email_2", "").values
    out["Phone 1"] = df_sorted.get("phone_1", "").values
    out["LinkedIn"] = df_sorted.get("apollo_linkedin", "").values

    # Portfolio overview
    out["Properties"] = df_sorted.get("property_count", "").values
    out["Portfolio Value"] = df_sorted["total_portfolio_value"].apply(currency).values
    out["Avg Property Value"] = df_sorted["avg_property_value"].apply(currency).values
    out["Property Types"] = df_sorted.get("property_types", "").values
    out["County"] = df_sorted["CO_NO"].map({"60": "Palm Beach", "16": "Broward"}).fillna("").values

    # Financing intelligence
    out["Current Lender"] = df_sorted.get("clean_lender", "").values
    out["Lender Type"] = df_sorted.get("best_lender_type", "").values
    out["Est. Loan Balance"] = df_sorted["est_remaining_balance"].apply(currency).values
    out["Est. Monthly Payment"] = df_sorted.get("est_monthly_payment", "").values
    out["Est. Interest Rate"] = df_sorted.get("attom_interest_rate", "").values
    out["Est. Equity"] = df_sorted["estimated_equity"].apply(currency).values
    out["Equity %"] = df_sorted["equity_ratio"].apply(pct).values
    out["Max Cashout (75%)"] = df_sorted["max_cashout_75"].apply(currency).values
    out["Est. DSCR"] = df_sorted.get("est_dscr", "").values

    # Rental income
    out["Est. Monthly Rent"] = df_sorted.get("est_monthly_rent", "").values
    out["Est. Annual Rent"] = df_sorted.get("est_annual_rent", "").values
    out["Rent-to-Value %"] = df_sorted.get("rent_to_value_ratio", "").values

    # Purchase behavior
    out["Total Acquisitions"] = df_sorted.get("total_acquisitions", "").values
    out["Purchases (12mo)"] = df_sorted.get("purchases_last_12mo", "").values
    out["Purchases (36mo)"] = df_sorted.get("purchases_last_36mo", "").values
    out["Avg Purchase Price"] = df_sorted["avg_purchase_price"].apply(currency).values
    out["Flip Count"] = df_sorted.get("flip_count", "").values
    out["Hold Count"] = df_sorted.get("hold_count", "").values
    out["Avg Hold Period (mo)"] = df_sorted.get("avg_hold_period_months", "").values
    out["Cash Purchase %"] = df_sorted.get("cash_purchase_pct", "").values

    # Refi signals
    out["Refi Priority"] = df_sorted.get("refi_priority", "").values
    out["Refi Signals"] = df_sorted.get("refi_signals", "").values
    out["Cash Buyer?"] = df_sorted.get("probable_cash_buyer", "").values
    out["BRRRR Exit?"] = df_sorted.get("brrrr_exit_candidate", "").values
    out["Rate Refi?"] = df_sorted.get("rate_refi_candidate", "").values
    out["Equity Harvest?"] = df_sorted.get("equity_harvest_candidate", "").values

    # Wealth signals
    out["FEC Donations"] = df_sorted.get("fec_total_donated", "").values
    out["FEC Recipients"] = df_sorted.get("fec_recipients", "").values
    out["SunBiz Entities"] = df_sorted.get("sunbiz_entity_count", "").values
    out["Wealth Score"] = df_sorted.get("wealth_signal_score", "").values

    # Entity details
    out["Officers"] = df_sorted.get("officer_names", df_sorted.get("entity_officers", "")).values
    out["Registered Agent"] = df_sorted.get("registered_agent", "").values
    out["Entity Status"] = df_sorted.get("entity_status", df_sorted.get("sunbiz_status", "")).values
    out["STR Licensed?"] = df_sorted.get("str_licensed", "").values

    # Talking points / suggested angle
    out["Talking Points"] = df_sorted.get("talking_points", "").values

    # Outreach tracking
    out["Email Sent?"] = ""
    out["Email Template Used"] = ""
    out["Personalization Notes"] = ""

    out = out.fillna("")
    print(f"  Battlecards: {len(out)} leads with full dossier")
    return out


# ---------------------------------------------------------------------------
# Sheet 3: Performance Tracker
# ---------------------------------------------------------------------------
def build_performance_tracker(df):
    """
    Conversion tracking — Frank logs outcomes, we analyze what works.
    Pre-populated with lead info, empty outcome columns.
    """
    df_sorted = df.copy()
    df_sorted["_sort_score"] = pd.to_numeric(df_sorted.get("_score", 0), errors="coerce").fillna(0)
    df_sorted = df_sorted.sort_values("_sort_score", ascending=False)

    out = pd.DataFrame()

    # Lead identity (minimal — just enough to cross-reference)
    out["Contact Name"] = df_sorted.get("contact_name", "").values
    out["Entity"] = df_sorted["OWN_NAME"].values
    out["ICP Segment"] = df_sorted.get("_icp", "").values
    out["Score"] = df_sorted.get("_score", "").values
    out["Properties"] = df_sorted.get("property_count", "").values
    out["Portfolio Value"] = df_sorted["total_portfolio_value"].apply(currency).values
    out["Current Lender"] = df_sorted.get("clean_lender", "").values
    out["County"] = df_sorted["CO_NO"].map({"60": "Palm Beach", "16": "Broward"}).fillna("").values

    # Outreach tracking
    out["Channel"] = ""           # Phone / Email / LinkedIn / Referral
    out["First Contact Date"] = ""
    out["Total Touches"] = ""
    out["Last Contact Date"] = ""

    # Outcome funnel
    out["Reached?"] = ""          # Yes/No/VM
    out["Conversation?"] = ""     # Yes/No
    out["Interest Level"] = ""    # Hot/Warm/Cold/Not Interested
    out["Objection"] = ""         # Already has lender / Not buying / Bad timing / etc
    out["Appointment Set?"] = ""  # Yes/No + Date
    out["Application?"] = ""     # Yes/No
    out["Loan Amount"] = ""
    out["Loan Type"] = ""        # Cash-out / Rate-term / Purchase / Bridge
    out["Closed?"] = ""          # Yes/No
    out["Close Date"] = ""
    out["Revenue"] = ""

    # Learning / refinement
    out["What Worked"] = ""      # Free text — what resonated
    out["What Didn't"] = ""      # Free text — what fell flat
    out["Referral Given?"] = ""  # Did they refer someone else?
    out["Notes"] = ""

    out = out.fillna("")
    print(f"  Performance Tracker: {len(out)} leads")
    return out


# ---------------------------------------------------------------------------
# Export to xlsx
# ---------------------------------------------------------------------------
def export_xlsx(call_sheet, battlecards, performance):
    """Write all 3 sheets to Excel."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    with pd.ExcelWriter(XLSX_OUTPUT, engine="openpyxl") as writer:
        call_sheet.to_excel(writer, sheet_name="Call Sheet", index=False)
        battlecards.to_excel(writer, sheet_name="Battlecards", index=False)
        performance.to_excel(writer, sheet_name="Performance", index=False)

    print(f"\nExported to {XLSX_OUTPUT}")
    print(f"  File size: {XLSX_OUTPUT.stat().st_size / 1024:.0f} KB")


# ---------------------------------------------------------------------------
# Upload to Google Sheets
# ---------------------------------------------------------------------------
def upload_to_google_sheets(call_sheet, battlecards, performance):
    """Create a Google Spreadsheet with 3 tabs and populate data."""
    try:
        from googleapiclient.discovery import build as gapi_build
    except ImportError:
        print("ERROR: Install google-api-python-client google-auth-oauthlib:")
        print("  pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib")
        return None

    from dotenv import load_dotenv
    load_dotenv()

    creds = get_google_creds()
    sheets_service = gapi_build("sheets", "v4", credentials=creds)
    drive_service = gapi_build("drive", "v3", credentials=creds)

    # Create the spreadsheet
    spreadsheet = sheets_service.spreadsheets().create(body={
        "properties": {"title": "DSCR Lead Gen — MVP Pipeline"},
        "sheets": [
            {"properties": {"title": "Call Sheet", "index": 0}},
            {"properties": {"title": "Battlecards", "index": 1}},
            {"properties": {"title": "Performance", "index": 2}},
        ],
    }).execute()

    spreadsheet_id = spreadsheet["spreadsheetId"]
    spreadsheet_url = spreadsheet["spreadsheetUrl"]
    print(f"\nCreated Google Sheet: {spreadsheet_url}")

    # Helper to write a dataframe to a sheet tab
    def write_tab(df, tab_name):
        values = [df.columns.tolist()] + df.fillna("").values.tolist()
        sheets_service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range=f"'{tab_name}'!A1",
            valueInputOption="RAW",
            body={"values": values},
        ).execute()
        print(f"  Wrote {len(df)} rows to '{tab_name}'")

    write_tab(call_sheet, "Call Sheet")
    write_tab(battlecards, "Battlecards")
    write_tab(performance, "Performance")

    # Format: freeze header row, bold headers, auto-resize
    requests_body = []
    for i, tab_name in enumerate(["Call Sheet", "Battlecards", "Performance"]):
        sheet_id = spreadsheet["sheets"][i]["properties"]["sheetId"]

        # Freeze first row
        requests_body.append({
            "updateSheetProperties": {
                "properties": {"sheetId": sheet_id, "gridProperties": {"frozenRowCount": 1}},
                "fields": "gridProperties.frozenRowCount",
            }
        })

        # Bold header row
        requests_body.append({
            "repeatCell": {
                "range": {"sheetId": sheet_id, "startRowIndex": 0, "endRowIndex": 1},
                "cell": {"userEnteredFormat": {"textFormat": {"bold": True}}},
                "fields": "userEnteredFormat.textFormat.bold",
            }
        })

    # Apply formatting
    if requests_body:
        sheets_service.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body={"requests": requests_body},
        ).execute()

    print(f"\nGoogle Sheet ready: {spreadsheet_url}")
    return spreadsheet_url


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Build DSCR MVP Google Sheets")
    parser.add_argument("--xlsx-only", action="store_true", help="Export xlsx without uploading to Google")
    args = parser.parse_args()

    from dotenv import load_dotenv
    load_dotenv()

    print("=" * 60)
    print("DSCR Lead Gen — MVP Sheet Builder")
    print("=" * 60)

    df = load_master_data()

    print("\nBuilding sheets...")
    call_sheet = build_call_sheet(df)
    battlecards = build_battlecards(df)
    performance = build_performance_tracker(df)

    # Always export xlsx as backup
    export_xlsx(call_sheet, battlecards, performance)

    if not args.xlsx_only:
        print("\nUploading to Google Sheets...")
        url = upload_to_google_sheets(call_sheet, battlecards, performance)
        if url:
            print(f"\n{'=' * 60}")
            print(f"DONE! Share this link with Frank:")
            print(f"  {url}")
            print(f"{'=' * 60}")
    else:
        print("\nSkipped Google upload (--xlsx-only mode)")
        print(f"Open {XLSX_OUTPUT} and upload to Google Drive manually")


if __name__ == "__main__":
    main()
