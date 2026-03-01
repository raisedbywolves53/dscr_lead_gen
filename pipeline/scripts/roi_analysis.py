"""
ROI Analysis Workbook for DSCR Lead Generation Pipeline

Standalone script — no pipeline inputs needed. All data is hardcoded
assumptions derived from actual Palm Beach pipeline results + vendor
pricing research.

Output: pipeline/output/roi_analysis_YYYY-MM-DD.xlsx

Usage:
    python3 pipeline/scripts/roi_analysis.py
"""

from pathlib import Path
from datetime import date
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

OUTPUT_DIR = Path("pipeline/output")

# ---------------------------------------------------------------------------
# Color palette (matches 06_score_and_output.py)
# ---------------------------------------------------------------------------
_NAVY = '1B2A4A'
_ACCENT_BLUE = '4472C4'
_HOT_RED = 'C00000'
_WARM_ORANGE = 'ED7D31'
_MONEY_GREEN = '548235'
_LIGHT_BG = 'F2F2F2'
_WHITE = 'FFFFFF'
_INPUT_YELLOW = 'FFF2CC'

# Pre-built fills
_navy_fill = PatternFill(start_color=_NAVY, end_color=_NAVY, fill_type='solid')
_blue_fill = PatternFill(start_color=_ACCENT_BLUE, end_color=_ACCENT_BLUE, fill_type='solid')
_red_fill = PatternFill(start_color=_HOT_RED, end_color=_HOT_RED, fill_type='solid')
_orange_fill = PatternFill(start_color=_WARM_ORANGE, end_color=_WARM_ORANGE, fill_type='solid')
_green_fill = PatternFill(start_color=_MONEY_GREEN, end_color=_MONEY_GREEN, fill_type='solid')
_light_fill = PatternFill(start_color=_LIGHT_BG, end_color=_LIGHT_BG, fill_type='solid')
_white_fill = PatternFill(start_color=_WHITE, end_color=_WHITE, fill_type='solid')
_yellow_fill = PatternFill(start_color=_INPUT_YELLOW, end_color=_INPUT_YELLOW, fill_type='solid')

# Fonts
_banner_font = Font(size=18, bold=True, color=_WHITE)
_subtitle_font = Font(size=10, color=_WHITE)
_section_font = Font(size=13, bold=True, color=_WHITE)
_kpi_value_font = Font(size=20, bold=True, color=_WHITE)
_kpi_label_font = Font(size=9, color=_WHITE)
_table_header_font = Font(size=10, bold=True, color=_WHITE)
_table_cell_font = Font(size=10, color='333333')
_table_cell_bold = Font(size=10, bold=True, color='333333')
_input_font = Font(size=10, bold=True, color='7F6000')
_input_label_font = Font(size=10, color='333333')
_footer_font = Font(size=8, italic=True, color='999999')
_note_font = Font(size=9, italic=True, color='666666')

# Alignments
_center = Alignment(horizontal='center', vertical='center', wrap_text=True)
_left = Alignment(horizontal='left', vertical='center', wrap_text=True)
_right = Alignment(horizontal='right', vertical='center')

_thin_border = Border(bottom=Side(style='thin', color='D9D9D9'))
_yellow_border = Border(
    bottom=Side(style='thin', color='BF9000'),
    top=Side(style='thin', color='BF9000'),
    left=Side(style='thin', color='BF9000'),
    right=Side(style='thin', color='BF9000'),
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_merged(ws, start_col, end_col, row, value,
                  font=None, fill=None, alignment=None, number_format=None):
    """Write a value into a merged cell range, applying fill to every cell."""
    if start_col != end_col:
        ws.merge_cells(start_row=row, start_column=start_col,
                       end_row=row, end_column=end_col)
    cell = ws.cell(row=row, column=start_col, value=value)
    if font:
        cell.font = font
    if fill:
        cell.fill = fill
    if alignment:
        cell.alignment = alignment
    if number_format:
        cell.number_format = number_format
    if fill:
        for c in range(start_col, end_col + 1):
            ws.cell(row=row, column=c).fill = fill


def _setup_sheet(ws):
    """Standard sheet setup: hide gridlines, set column widths."""
    ws.sheet_view.showGridLines = False
    ws.column_dimensions['A'].width = 2
    for col_letter in ['B', 'C', 'D', 'E', 'F', 'G']:
        ws.column_dimensions[col_letter].width = 22
    ws.column_dimensions['H'].width = 2


def _gutter_fill(ws, row, fill=None):
    """Fill gutter columns A and H."""
    if fill:
        ws.cell(row=row, column=1).fill = fill
        ws.cell(row=row, column=8).fill = fill


def _write_banner(ws, title):
    """Write the standard navy banner rows 1-2. Returns next row."""
    row = 1
    _write_merged(ws, 2, 7, row, title,
                  font=_banner_font, fill=_navy_fill, alignment=_center)
    ws.row_dimensions[row].height = 40
    _gutter_fill(ws, row, _navy_fill)
    row += 1

    subtitle = (f'Generated {date.today().strftime("%B %d, %Y")}  |  '
                f'CrossCountry Mortgage  |  Florida DSCR Lending')
    _write_merged(ws, 2, 7, row, subtitle,
                  font=_subtitle_font, fill=_navy_fill, alignment=_center)
    ws.row_dimensions[row].height = 22
    _gutter_fill(ws, row, _navy_fill)
    row += 1
    return row


def _write_section_header(ws, row, title, fill=None):
    """Write a section header bar. Returns next row."""
    fill = fill or _blue_fill
    _write_merged(ws, 2, 7, row, title,
                  font=_section_font, fill=fill, alignment=_left)
    ws.row_dimensions[row].height = 28
    return row + 1


def _write_table_header(ws, row, headers):
    """Write a table header row across columns B-G. Returns next row."""
    for i, hdr in enumerate(headers):
        cell = ws.cell(row=row, column=2 + i, value=hdr)
        cell.font = _table_header_font
        cell.fill = _navy_fill
        cell.alignment = _center
    ws.row_dimensions[row].height = 24
    return row + 1


def _write_table_row(ws, row, values, bold_first=True, alt=False):
    """Write a data row across columns B-G. Returns next row."""
    for i, v in enumerate(values):
        cell = ws.cell(row=row, column=2 + i, value=v)
        cell.font = _table_cell_bold if (i == 0 and bold_first) else _table_cell_font
        cell.alignment = _center if i > 0 else _left
        cell.border = _thin_border
        if alt:
            cell.fill = _light_fill
    ws.row_dimensions[row].height = 22
    return row + 1


def _write_input_cell(ws, row, col, value, number_format=None):
    """Write a yellow editable input cell."""
    cell = ws.cell(row=row, column=col, value=value)
    cell.font = _input_font
    cell.fill = _yellow_fill
    cell.border = _yellow_border
    cell.alignment = _center
    if number_format:
        cell.number_format = number_format
    return cell


def _write_formula_cell(ws, row, col, formula, number_format=None, bold=False):
    """Write a formula cell."""
    cell = ws.cell(row=row, column=col, value=formula)
    cell.font = _table_cell_bold if bold else _table_cell_font
    cell.alignment = _center
    cell.border = _thin_border
    if number_format:
        cell.number_format = number_format
    return cell


def _write_label(ws, row, col, text, bold=False, end_col=None):
    """Write a label cell."""
    if end_col and end_col > col:
        ws.merge_cells(start_row=row, start_column=col,
                       end_row=row, end_column=end_col)
    cell = ws.cell(row=row, column=col, value=text)
    cell.font = _table_cell_bold if bold else _table_cell_font
    cell.alignment = _left
    cell.border = _thin_border
    return cell


def _write_kpi_tiles(ws, row, tiles):
    """Write a row of 3 KPI tiles (value row + label row). Returns next row."""
    for i, (val, label, fill) in enumerate(tiles):
        col_start = 2 + i * 2
        col_end = col_start + 1
        _write_merged(ws, col_start, col_end, row, val,
                      font=_kpi_value_font, fill=fill, alignment=_center)
    ws.row_dimensions[row].height = 45
    row += 1

    for i, (val, label, fill) in enumerate(tiles):
        col_start = 2 + i * 2
        col_end = col_start + 1
        _write_merged(ws, col_start, col_end, row, label,
                      font=_kpi_label_font, fill=fill, alignment=_center)
    ws.row_dimensions[row].height = 20
    row += 1
    return row


# ---------------------------------------------------------------------------
# Tab 1: Executive Summary
# ---------------------------------------------------------------------------

def _build_summary(wb):
    ws = wb.active
    ws.title = 'Executive Summary'
    _setup_sheet(ws)

    row = _write_banner(ws, 'DSCR LEAD GENERATION \u2014 ROI ANALYSIS')
    row += 1  # spacer

    # KPI tiles row 1
    row = _write_section_header(ws, row, 'KEY METRICS')
    tiles1 = [
        ('470K+', 'Est. FL Investor Leads', _navy_fill),
        ('$6,000', 'Revenue Per Closed Loan', _green_fill),
        ('100x+', 'ROI vs Lead Vendors', _red_fill),
    ]
    row = _write_kpi_tiles(ws, row, tiles1)

    # KPI tiles row 2
    tiles2 = [
        ('$0', 'CPL \u2014 Tier 1 (Free)', _green_fill),
        ('$0.54', 'CPL \u2014 Tier 2 (Enhanced)', _blue_fill),
        ('$72K\u2013$360K', 'Annual Revenue Potential', _money_green_fill if False else _green_fill),
    ]
    row = _write_kpi_tiles(ws, row, tiles2)
    row += 1  # spacer

    # Bottom-line comparison table
    row = _write_section_header(ws, row, 'BOTTOM LINE \u2014 TIER COMPARISON')
    row = _write_table_header(ws, row,
        ['Metric', 'Tier 1: Free', 'Tier 2: Enhanced', 'Tier 3: Full', '', ''])

    data_rows = [
        ('Monthly Data Cost',       '$0',     '$222',    '$592',   '', ''),
        ('Contactable Leads (3-Co)', '~6,700', '~73K',  '~104K', '', ''),
        ('Expected Closings/Mo',    '1\u20132',  '5\u201310',  '10\u201320', '', ''),
        ('Monthly Revenue',         '$6K\u2013$12K', '$30K\u2013$60K', '$60K\u2013$120K', '', ''),
        ('Monthly ROI',             '\u221e (free)', '135x\u2013270x', '101x\u2013202x', '', ''),
    ]
    for i, vals in enumerate(data_rows):
        row = _write_table_row(ws, row, vals, alt=(i % 2 == 1))

    row += 1
    # Key assumptions note
    _write_merged(ws, 2, 7, row, (
        'Key Assumptions: $400K avg loan, 150 bps LO comp ($6K/loan), '
        '500 leads worked/mo. Yellow cells on other tabs are editable.'),
        font=_note_font, fill=_white_fill, alignment=_left)
    row += 1

    _write_merged(ws, 2, 7, row,
        'See individual tabs for detailed breakdowns and editable inputs.',
        font=_footer_font, fill=_white_fill, alignment=_left)


# ---------------------------------------------------------------------------
# Tab 2: Lead Volume Estimates
# ---------------------------------------------------------------------------

def _build_lead_volume(wb):
    ws = wb.create_sheet('Lead Volume')
    _setup_sheet(ws)

    row = _write_banner(ws, 'LEAD VOLUME ESTIMATES BY PHASE')
    row += 1

    # Editable assumptions section
    row = _write_section_header(ws, row, 'ASSUMPTIONS (EDIT YELLOW CELLS)')
    # Row labels in B-C, values in D
    assumptions = [
        ('Investor Filter Rate', 0.053, '0%'),
        ('STR License Rate', 0.012, '0.0%'),
        ('Multi-Property Rate (2+)', 0.34, '0.0%'),
        ('Foreign/Entity-OOS Rate', 0.66, '0.0%'),
        ('Hot Lead Rate (score 60+)', 0.034, '0.00%'),
        ('Warm Lead Rate (score 40-59)', 0.15, '0.0%'),
    ]
    # Store cell refs for these assumptions
    assumption_rows = {}
    for label, default, fmt in assumptions:
        _write_label(ws, row, 2, label, bold=True, end_col=4)
        _write_input_cell(ws, row, 5, default, number_format=fmt)
        assumption_rows[label] = row
        ws.row_dimensions[row].height = 24
        row += 1

    filter_rate_ref = f'$E${assumption_rows["Investor Filter Rate"]}'
    str_rate_ref = f'$E${assumption_rows["STR License Rate"]}'
    multi_rate_ref = f'$E${assumption_rows["Multi-Property Rate (2+)"]}'
    hot_rate_ref = f'$E${assumption_rows["Hot Lead Rate (score 60+)"]}'
    warm_rate_ref = f'$E${assumption_rows["Warm Lead Rate (score 40-59)"]}'

    row += 1

    # Phase 1: South Florida (3 counties)
    row = _write_section_header(ws, row, 'PHASE 1 \u2014 SOUTH FLORIDA (3 COUNTIES)')
    row = _write_table_header(ws, row,
        ['County', 'Est. Parcels', 'Investor Leads', 'STR Leads', 'Hot Leads', 'Warm Leads'])

    phase1 = [
        ('Palm Beach', 654000),
        ('Broward', 750000),
        ('Miami-Dade', 900000),
    ]
    phase1_first_row = row
    for i, (county, parcels) in enumerate(phase1):
        _write_label(ws, row, 2, county, bold=True)
        _write_input_cell(ws, row, 3, parcels, number_format='#,##0')
        cr = f'C{row}'
        _write_formula_cell(ws, row, 4, f'=ROUND({cr}*{filter_rate_ref},0)', '#,##0')
        _write_formula_cell(ws, row, 5, f'=ROUND(D{row}*{str_rate_ref},0)', '#,##0')
        _write_formula_cell(ws, row, 6, f'=ROUND(D{row}*{hot_rate_ref},0)', '#,##0')
        _write_formula_cell(ws, row, 7, f'=ROUND(D{row}*{warm_rate_ref},0)', '#,##0')
        ws.row_dimensions[row].height = 22
        row += 1
    phase1_last_row = row - 1

    # Phase 1 total
    _write_label(ws, row, 2, 'Phase 1 Total', bold=True)
    for col_idx in range(3, 8):
        cl = get_column_letter(col_idx)
        _write_formula_cell(ws, row, col_idx,
            f'=SUM({cl}{phase1_first_row}:{cl}{phase1_last_row})',
            '#,##0', bold=True)
    ws.row_dimensions[row].height = 24
    p1_total_row = row
    row += 2

    # Phase 2: Metro Florida (16 counties)
    row = _write_section_header(ws, row, 'PHASE 2 \u2014 METRO FLORIDA (16 COUNTIES)')
    row = _write_table_header(ws, row,
        ['County', 'Est. Parcels', 'Investor Leads', 'STR Leads', 'Hot Leads', 'Warm Leads'])

    phase2 = [
        ('Hillsborough', 520000), ('Orange', 480000), ('Duval', 400000),
        ('Pinellas', 360000), ('Lee', 340000), ('Collier', 210000),
        ('Sarasota', 230000), ('Manatee', 200000), ('Seminole', 180000),
        ('Osceola', 170000), ('Volusia', 250000), ('Brevard', 260000),
        ('Pasco', 230000), ('Polk', 300000), ('St. Lucie', 160000),
        ('Martin', 85000),
    ]
    phase2_first_row = row
    for i, (county, parcels) in enumerate(phase2):
        _write_label(ws, row, 2, county, bold=(i == 0))
        _write_input_cell(ws, row, 3, parcels, number_format='#,##0')
        cr = f'C{row}'
        _write_formula_cell(ws, row, 4, f'=ROUND({cr}*{filter_rate_ref},0)', '#,##0')
        _write_formula_cell(ws, row, 5, f'=ROUND(D{row}*{str_rate_ref},0)', '#,##0')
        _write_formula_cell(ws, row, 6, f'=ROUND(D{row}*{hot_rate_ref},0)', '#,##0')
        _write_formula_cell(ws, row, 7, f'=ROUND(D{row}*{warm_rate_ref},0)', '#,##0')
        ws.row_dimensions[row].height = 22
        row += 1
    phase2_last_row = row - 1

    _write_label(ws, row, 2, 'Phase 2 Total', bold=True)
    for col_idx in range(3, 8):
        cl = get_column_letter(col_idx)
        _write_formula_cell(ws, row, col_idx,
            f'=SUM({cl}{phase2_first_row}:{cl}{phase2_last_row})',
            '#,##0', bold=True)
    ws.row_dimensions[row].height = 24
    p2_total_row = row
    row += 2

    # Phase 3: Remaining 48 counties
    row = _write_section_header(ws, row, 'PHASE 3 \u2014 REMAINING 48 COUNTIES')
    row = _write_table_header(ws, row,
        ['County', 'Est. Parcels', 'Investor Leads', 'STR Leads', 'Hot Leads', 'Warm Leads'])
    _write_label(ws, row, 2, 'Remaining 48 Counties', bold=True)
    _write_input_cell(ws, row, 3, 3500000, number_format='#,##0')
    _write_formula_cell(ws, row, 4, f'=ROUND(C{row}*{filter_rate_ref},0)', '#,##0')
    _write_formula_cell(ws, row, 5, f'=ROUND(D{row}*{str_rate_ref},0)', '#,##0')
    _write_formula_cell(ws, row, 6, f'=ROUND(D{row}*{hot_rate_ref},0)', '#,##0')
    _write_formula_cell(ws, row, 7, f'=ROUND(D{row}*{warm_rate_ref},0)', '#,##0')
    ws.row_dimensions[row].height = 24
    p3_row = row
    row += 2

    # Grand total
    row = _write_section_header(ws, row, 'STATEWIDE TOTAL', fill=_green_fill)
    _write_label(ws, row, 2, 'All 67 Counties', bold=True)
    for col_idx in range(3, 8):
        cl = get_column_letter(col_idx)
        _write_formula_cell(ws, row, col_idx,
            f'={cl}{p1_total_row}+{cl}{p2_total_row}+{cl}{p3_row}',
            '#,##0', bold=True)
    ws.row_dimensions[row].height = 28
    row += 2

    _write_merged(ws, 2, 7, row,
        'Parcel estimates based on FL DOR records. Palm Beach is actual data; '
        'others estimated from county population/property ratios.',
        font=_note_font, fill=_white_fill, alignment=_left)


# ---------------------------------------------------------------------------
# Tab 3: Data Stack & Costs
# ---------------------------------------------------------------------------

def _build_data_stack(wb):
    ws = wb.create_sheet('Data Stack & Costs')
    _setup_sheet(ws)

    row = _write_banner(ws, 'DATA STACK & COSTS')
    row += 1

    # Tier 1: Free
    row = _write_section_header(ws, row, 'TIER 1 \u2014 FREE ($0/MONTH)', fill=_green_fill)
    row = _write_table_header(ws, row,
        ['Data Source', 'Monthly Cost', 'What It Provides', '', '', ''])

    tier1_items = [
        ('FDOR (FL Dept of Revenue)', '$0', 'Property records, ownership, values, sale history'),
        ('SunBiz (FL Corporations)', '$0', 'LLC/Trust to human name resolution'),
        ('DBPR (FL Licensing)', '$0', 'Vacation rental license verification + phone'),
        ('SEC EDGAR', '$0', 'Fund manager / syndicator identification'),
        ('Apollo.io (Free Tier)', '$0', '10K free credits/mo \u2014 email/phone lookup'),
    ]
    for i, (source, cost, desc) in enumerate(tier1_items):
        _write_label(ws, row, 2, source, bold=True)
        ws.cell(row=row, column=3, value=cost)
        ws.cell(row=row, column=3).font = _table_cell_bold
        ws.cell(row=row, column=3).alignment = _center
        ws.cell(row=row, column=3).fill = _light_fill if i % 2 else _white_fill
        _write_label(ws, row, 4, desc, end_col=7)
        ws.row_dimensions[row].height = 22
        row += 1

    # Tier 1 total
    _write_label(ws, row, 2, 'Tier 1 Total', bold=True)
    cell = ws.cell(row=row, column=3, value='$0')
    cell.font = Font(size=12, bold=True, color=_MONEY_GREEN)
    cell.alignment = _center
    t1_total_row = row
    row += 2

    # Tier 2: Enhanced
    row = _write_section_header(ws, row, 'TIER 2 \u2014 ENHANCED ($222/MONTH)', fill=_blue_fill)
    row = _write_table_header(ws, row,
        ['Data Source', 'Monthly Cost', 'What It Adds', '', '', ''])

    tier2_items = [
        ('Everything in Tier 1', '$0', 'Base pipeline (all free sources)'),
        ('PropStream', 99, 'MLS comps, mortgage data, skip trace credits'),
        ('Apollo Basic Plan', 49, '25K credits/mo, mobile phones, emails'),
        ('RentCast', 74, 'Rental estimates, vacancy, rental comps'),
    ]
    tier2_cost_rows = []
    for i, (source, cost, desc) in enumerate(tier2_items):
        _write_label(ws, row, 2, source, bold=True)
        if isinstance(cost, int):
            _write_input_cell(ws, row, 3, cost, number_format='$#,##0')
            tier2_cost_rows.append(row)
        else:
            ws.cell(row=row, column=3, value=cost)
            ws.cell(row=row, column=3).font = _table_cell_font
            ws.cell(row=row, column=3).alignment = _center
        _write_label(ws, row, 4, desc, end_col=7)
        ws.row_dimensions[row].height = 22
        row += 1

    _write_label(ws, row, 2, 'Tier 2 Total', bold=True)
    sum_parts = '+'.join(f'C{r}' for r in tier2_cost_rows)
    _write_formula_cell(ws, row, 3, f'={sum_parts}', '$#,##0', bold=True)
    t2_total_row = row
    row += 2

    # Tier 3: Full
    row = _write_section_header(ws, row, 'TIER 3 \u2014 FULL STACK ($592/MONTH)', fill=_orange_fill)
    row = _write_table_header(ws, row,
        ['Data Source', 'Monthly Cost', 'What It Adds', '', '', ''])

    tier3_items = [
        ('Everything in Tier 2', None, 'Enhanced pipeline (Tier 2 stack)'),
        ('AirDNA', 100, 'STR revenue data, occupancy, market analytics'),
        ('BatchLeads', 119, 'List building, skip trace, driving for dollars'),
        ('BatchData Skip Trace', 150, 'High-volume skip tracing (80%+ hit rate)'),
    ]
    tier3_cost_rows = []
    for i, (source, cost, desc) in enumerate(tier3_items):
        _write_label(ws, row, 2, source, bold=True)
        if isinstance(cost, int):
            _write_input_cell(ws, row, 3, cost, number_format='$#,##0')
            tier3_cost_rows.append(row)
        else:
            t2_ref = f'C{t2_total_row}'
            ws.cell(row=row, column=3, value=f'={t2_ref}')
            ws.cell(row=row, column=3).font = _table_cell_font
            ws.cell(row=row, column=3).alignment = _center
            ws.cell(row=row, column=3).number_format = '$#,##0'
        _write_label(ws, row, 4, desc, end_col=7)
        ws.row_dimensions[row].height = 22
        row += 1

    _write_label(ws, row, 2, 'Tier 3 Total', bold=True)
    t3_sum_parts = '+'.join(f'C{r}' for r in tier3_cost_rows)
    _write_formula_cell(ws, row, 3, f'=C{t2_total_row}+{t3_sum_parts}', '$#,##0', bold=True)
    t3_total_row = row
    row += 2

    # Coverage comparison
    row = _write_section_header(ws, row, 'COVERAGE COMPARISON')
    row = _write_table_header(ws, row,
        ['Metric', 'Tier 1: Free', 'Tier 2: Enhanced', 'Tier 3: Full', '', ''])

    coverage = [
        ('Monthly Cost', f'=C{t1_total_row}', f'=C{t2_total_row}', f'=C{t3_total_row}'),
        ('Phone Coverage', '<1%', '60\u201370%', '80\u201385%'),
        ('Email Coverage', '<1%', '40\u201350%', '65\u201375%'),
        ('Skip Trace Capacity', '0', '25K/mo', '100K+/mo'),
        ('Rental Data', 'DBPR only', '+ rental comps', '+ STR revenue/occ'),
        ('Property Data', 'FDOR (tax rolls)', '+ MLS/mortgage', '+ driving for $'),
    ]
    for i, vals in enumerate(coverage):
        _write_label(ws, row, 2, vals[0], bold=True)
        for j, v in enumerate(vals[1:], start=1):
            cell = ws.cell(row=row, column=2 + j, value=v)
            cell.font = _table_cell_font
            cell.alignment = _center
            cell.border = _thin_border
            if i == 0:
                cell.number_format = '$#,##0'
        if i % 2 == 1:
            for j in range(2, 8):
                ws.cell(row=row, column=j).fill = _light_fill
        ws.row_dimensions[row].height = 22
        row += 1

    # Store tier cost row refs for other sheets
    ws.sheet_properties.customProperties = None  # openpyxl doesn't support custom props easily
    # We'll use defined names instead
    return t1_total_row, t2_total_row, t3_total_row


# ---------------------------------------------------------------------------
# Tab 4: Revenue Model
# ---------------------------------------------------------------------------

def _build_revenue_model(wb, cost_sheet_name, t2_total_row, t3_total_row):
    ws = wb.create_sheet('Revenue Model')
    _setup_sheet(ws)

    row = _write_banner(ws, 'REVENUE MODEL & PROJECTIONS')
    row += 1

    # Variable inputs
    row = _write_section_header(ws, row, 'VARIABLE INPUTS (EDIT YELLOW CELLS)')

    inputs = {}

    _write_label(ws, row, 2, 'Average DSCR Loan Size', bold=True, end_col=4)
    _write_input_cell(ws, row, 5, 400000, number_format='$#,##0')
    inputs['loan_size'] = row
    ws.row_dimensions[row].height = 24
    row += 1

    _write_label(ws, row, 2, 'LO Compensation (bps)', bold=True, end_col=4)
    _write_input_cell(ws, row, 5, 150, number_format='#,##0')
    inputs['lo_bps'] = row
    ws.row_dimensions[row].height = 24
    row += 1

    _write_label(ws, row, 2, 'Close Rate \u2014 Hot Leads (60+)', bold=True, end_col=4)
    _write_input_cell(ws, row, 5, 0.10, number_format='0%')
    inputs['close_hot'] = row
    ws.row_dimensions[row].height = 24
    row += 1

    _write_label(ws, row, 2, 'Close Rate \u2014 Warm Leads (40-59)', bold=True, end_col=4)
    _write_input_cell(ws, row, 5, 0.05, number_format='0%')
    inputs['close_warm'] = row
    ws.row_dimensions[row].height = 24
    row += 1

    _write_label(ws, row, 2, 'Close Rate \u2014 Cold Leads (<50)', bold=True, end_col=4)
    _write_input_cell(ws, row, 5, 0.01, number_format='0%')
    inputs['close_cold'] = row
    ws.row_dimensions[row].height = 24
    row += 1

    _write_label(ws, row, 2, 'Leads Worked Per Month', bold=True, end_col=4)
    _write_input_cell(ws, row, 5, 500, number_format='#,##0')
    inputs['leads_per_mo'] = row
    ws.row_dimensions[row].height = 24
    row += 1

    _write_label(ws, row, 2, 'Hot Lead % of Worked', bold=True, end_col=4)
    _write_input_cell(ws, row, 5, 0.10, number_format='0%')
    inputs['hot_pct'] = row
    ws.row_dimensions[row].height = 24
    row += 1

    _write_label(ws, row, 2, 'Warm Lead % of Worked', bold=True, end_col=4)
    _write_input_cell(ws, row, 5, 0.35, number_format='0%')
    inputs['warm_pct'] = row
    ws.row_dimensions[row].height = 24
    row += 1

    row += 1

    # Calculated values
    row = _write_section_header(ws, row, 'CALCULATED PROJECTIONS')

    loan_ref = f'E{inputs["loan_size"]}'
    bps_ref = f'E{inputs["lo_bps"]}'
    close_hot_ref = f'E{inputs["close_hot"]}'
    close_warm_ref = f'E{inputs["close_warm"]}'
    close_cold_ref = f'E{inputs["close_cold"]}'
    leads_ref = f'E{inputs["leads_per_mo"]}'
    hot_pct_ref = f'E{inputs["hot_pct"]}'
    warm_pct_ref = f'E{inputs["warm_pct"]}'

    # Revenue per loan
    _write_label(ws, row, 2, 'Revenue Per Closed Loan', bold=True, end_col=4)
    _write_formula_cell(ws, row, 5,
        f'={loan_ref}*{bps_ref}/10000', '$#,##0', bold=True)
    rev_per_loan_ref = f'E{row}'
    ws.row_dimensions[row].height = 24
    row += 1

    # Monthly leads breakdown
    _write_label(ws, row, 2, 'Hot Leads Worked/Mo', bold=True, end_col=4)
    _write_formula_cell(ws, row, 5,
        f'=ROUND({leads_ref}*{hot_pct_ref},0)', '#,##0')
    hot_worked_ref = f'E{row}'
    ws.row_dimensions[row].height = 24
    row += 1

    _write_label(ws, row, 2, 'Warm Leads Worked/Mo', bold=True, end_col=4)
    _write_formula_cell(ws, row, 5,
        f'=ROUND({leads_ref}*{warm_pct_ref},0)', '#,##0')
    warm_worked_ref = f'E{row}'
    ws.row_dimensions[row].height = 24
    row += 1

    _write_label(ws, row, 2, 'Cold Leads Worked/Mo', bold=True, end_col=4)
    _write_formula_cell(ws, row, 5,
        f'={leads_ref}-{hot_worked_ref}-{warm_worked_ref}', '#,##0')
    cold_worked_ref = f'E{row}'
    ws.row_dimensions[row].height = 24
    row += 1

    row += 1

    # Closings per month
    _write_label(ws, row, 2, 'Hot Closings/Mo', bold=True, end_col=4)
    _write_formula_cell(ws, row, 5,
        f'=ROUND({hot_worked_ref}*{close_hot_ref},1)', '#,##0.0')
    hot_close_ref = f'E{row}'
    ws.row_dimensions[row].height = 24
    row += 1

    _write_label(ws, row, 2, 'Warm Closings/Mo', bold=True, end_col=4)
    _write_formula_cell(ws, row, 5,
        f'=ROUND({warm_worked_ref}*{close_warm_ref},1)', '#,##0.0')
    warm_close_ref = f'E{row}'
    ws.row_dimensions[row].height = 24
    row += 1

    _write_label(ws, row, 2, 'Cold Closings/Mo', bold=True, end_col=4)
    _write_formula_cell(ws, row, 5,
        f'=ROUND({cold_worked_ref}*{close_cold_ref},1)', '#,##0.0')
    cold_close_ref = f'E{row}'
    ws.row_dimensions[row].height = 24
    row += 1

    _write_label(ws, row, 2, 'Total Closings/Mo', bold=True, end_col=4)
    _write_formula_cell(ws, row, 5,
        f'={hot_close_ref}+{warm_close_ref}+{cold_close_ref}', '#,##0.0', bold=True)
    total_close_ref = f'E{row}'
    ws.row_dimensions[row].height = 24
    row += 1

    row += 1

    # Revenue
    row = _write_section_header(ws, row, 'REVENUE & ROI', fill=_green_fill)

    _write_label(ws, row, 2, 'Monthly Revenue', bold=True, end_col=4)
    _write_formula_cell(ws, row, 5,
        f'={total_close_ref}*{rev_per_loan_ref}', '$#,##0', bold=True)
    monthly_rev_ref = f'E{row}'
    ws.row_dimensions[row].height = 24
    row += 1

    _write_label(ws, row, 2, 'Annual Revenue', bold=True, end_col=4)
    _write_formula_cell(ws, row, 5,
        f'={monthly_rev_ref}*12', '$#,##0', bold=True)
    annual_rev_ref = f'E{row}'
    ws.row_dimensions[row].height = 24
    row += 1

    row += 1

    # ROI by tier
    row = _write_table_header(ws, row,
        ['ROI Metric', 'Tier 1: Free', 'Tier 2: $222/mo', 'Tier 3: $592/mo', '', ''])

    t2_cost = f"'{cost_sheet_name}'!C{t2_total_row}"
    t3_cost = f"'{cost_sheet_name}'!C{t3_total_row}"

    _write_label(ws, row, 2, 'Annual Data Cost', bold=True)
    ws.cell(row=row, column=3, value='$0').font = _table_cell_font
    ws.cell(row=row, column=3).alignment = _center
    _write_formula_cell(ws, row, 4, f'={t2_cost}*12', '$#,##0')
    _write_formula_cell(ws, row, 5, f'={t3_cost}*12', '$#,##0')
    t2_annual_cost_ref = f'D{row}'
    t3_annual_cost_ref = f'E{row}'
    ws.row_dimensions[row].height = 22
    row += 1

    _write_label(ws, row, 2, 'Annual Revenue', bold=True)
    for c in [3, 4, 5]:
        ws.cell(row=row, column=c, value=f'={annual_rev_ref}')
        ws.cell(row=row, column=c).font = _table_cell_font
        ws.cell(row=row, column=c).alignment = _center
        ws.cell(row=row, column=c).number_format = '$#,##0'
    ws.row_dimensions[row].height = 22
    row += 1

    _write_label(ws, row, 2, 'Annual ROI', bold=True)
    ws.cell(row=row, column=3, value='\u221e (free)').font = _table_cell_bold
    ws.cell(row=row, column=3).alignment = _center
    _write_formula_cell(ws, row, 4,
        f'=IF({t2_annual_cost_ref}=0,"N/A",{annual_rev_ref}/{t2_annual_cost_ref})',
        '#,##0"x"', bold=True)
    _write_formula_cell(ws, row, 5,
        f'=IF({t3_annual_cost_ref}=0,"N/A",{annual_rev_ref}/{t3_annual_cost_ref})',
        '#,##0"x"', bold=True)
    ws.row_dimensions[row].height = 22
    row += 1

    _write_label(ws, row, 2, 'Break-Even (Days)', bold=True)
    ws.cell(row=row, column=3, value='Day 0').font = _table_cell_font
    ws.cell(row=row, column=3).alignment = _center
    _write_formula_cell(ws, row, 4,
        f'=IF({monthly_rev_ref}=0,"N/A",ROUND({t2_cost}/{monthly_rev_ref}*30,0))',
        '#,##0')
    _write_formula_cell(ws, row, 5,
        f'=IF({monthly_rev_ref}=0,"N/A",ROUND({t3_cost}/{monthly_rev_ref}*30,0))',
        '#,##0')
    ws.row_dimensions[row].height = 22
    row += 2

    # Conservative scenario
    row = _write_section_header(ws, row, 'CONSERVATIVE SCENARIO (1/4 OF BASE)')

    _write_label(ws, row, 2, 'Monthly Closings (conservative)', bold=True, end_col=4)
    _write_formula_cell(ws, row, 5,
        f'=ROUND({total_close_ref}/4,1)', '#,##0.0')
    cons_close_ref = f'E{row}'
    ws.row_dimensions[row].height = 24
    row += 1

    _write_label(ws, row, 2, 'Monthly Revenue (conservative)', bold=True, end_col=4)
    _write_formula_cell(ws, row, 5,
        f'={cons_close_ref}*{rev_per_loan_ref}', '$#,##0', bold=True)
    cons_monthly_ref = f'E{row}'
    ws.row_dimensions[row].height = 24
    row += 1

    _write_label(ws, row, 2, 'Annual Revenue (conservative)', bold=True, end_col=4)
    _write_formula_cell(ws, row, 5,
        f'={cons_monthly_ref}*12', '$#,##0', bold=True)
    ws.row_dimensions[row].height = 24
    row += 1

    _write_label(ws, row, 2, 'Tier 2 ROI (conservative)', bold=True, end_col=4)
    _write_formula_cell(ws, row, 5,
        f'=IF({t2_annual_cost_ref}=0,"N/A",{cons_monthly_ref}*12/{t2_annual_cost_ref})',
        '#,##0"x"', bold=True)
    ws.row_dimensions[row].height = 24


# ---------------------------------------------------------------------------
# Tab 5: Cost Per Lead Analysis
# ---------------------------------------------------------------------------

def _build_cpl(wb, cost_sheet_name, t2_total_row, t3_total_row):
    ws = wb.create_sheet('Cost Per Lead')
    _setup_sheet(ws)

    row = _write_banner(ws, 'COST PER LEAD ANALYSIS')
    row += 1

    # Lead counts for Phase 1 (3 counties)
    row = _write_section_header(ws, row, 'PHASE 1 LEAD COUNTS (EDIT YELLOW CELLS)')

    counts = {}

    _write_label(ws, row, 2, 'Raw Investor Leads (3 counties)', bold=True, end_col=4)
    _write_input_cell(ws, row, 5, 122000, number_format='#,##0')
    counts['raw'] = row
    ws.row_dimensions[row].height = 24
    row += 1

    _write_label(ws, row, 2, 'Contactable Leads (Tier 2: 60%)', bold=True, end_col=4)
    _write_formula_cell(ws, row, 5, f'=ROUND(E{counts["raw"]}*0.6,0)', '#,##0')
    counts['contactable'] = row
    ws.row_dimensions[row].height = 24
    row += 1

    _write_label(ws, row, 2, 'Qualified Leads (score 40+)', bold=True, end_col=4)
    _write_input_cell(ws, row, 5, 18300, number_format='#,##0')
    counts['qualified'] = row
    ws.row_dimensions[row].height = 24
    row += 1

    _write_label(ws, row, 2, 'Hot Leads (score 60+)', bold=True, end_col=4)
    _write_input_cell(ws, row, 5, 4150, number_format='#,##0')
    counts['hot'] = row
    ws.row_dimensions[row].height = 24
    row += 1

    row += 1

    # CPL by tier
    row = _write_section_header(ws, row, 'COST PER LEAD BY TIER')

    t2_monthly = f"'{cost_sheet_name}'!C{t2_total_row}"
    t3_monthly = f"'{cost_sheet_name}'!C{t3_total_row}"

    row = _write_table_header(ws, row,
        ['Lead Type', 'Tier 1: Free', 'Tier 2: Enhanced', 'Tier 3: Full', '', ''])

    raw_ref = f'E{counts["raw"]}'
    contact_ref = f'E{counts["contactable"]}'
    qual_ref = f'E{counts["qualified"]}'
    hot_ref = f'E{counts["hot"]}'

    lead_types = [
        ('Per Raw Lead', raw_ref),
        ('Per Contactable Lead', contact_ref),
        ('Per Qualified Lead (40+)', qual_ref),
        ('Per Hot Lead (60+)', hot_ref),
    ]
    for i, (label, count_ref) in enumerate(lead_types):
        _write_label(ws, row, 2, label, bold=True)
        ws.cell(row=row, column=3, value='$0.00').font = _table_cell_font
        ws.cell(row=row, column=3).alignment = _center
        _write_formula_cell(ws, row, 4,
            f'=IF({count_ref}=0,"N/A",{t2_monthly}/{count_ref})', '$#,##0.000')
        _write_formula_cell(ws, row, 5,
            f'=IF({count_ref}=0,"N/A",{t3_monthly}/{count_ref})', '$#,##0.000')
        if i % 2 == 1:
            for c in range(2, 8):
                ws.cell(row=row, column=c).fill = _light_fill
        ws.row_dimensions[row].height = 22
        row += 1

    row += 1

    # Vendor comparison
    row = _write_section_header(ws, row, 'VS INDUSTRY BENCHMARKS')
    row = _write_table_header(ws, row,
        ['Source', 'Cost Per Lead', 'Lead Quality', 'Volume', '', ''])

    vendors = [
        ('Our Pipeline (Tier 1)', '$0.00', 'Scored + segmented', '122K+'),
        ('Our Pipeline (Tier 2)', '$0.54/qualified', 'Enriched + scored', '122K+'),
        ('PropStream DIY', '$0.10\u2013$0.25', 'Raw list only', 'Unlimited'),
        ('DSCR Lead Vendor', '$100\u2013$250/lead', 'Exclusive, pre-qualified', '40\u2013100/mo'),
        ('Facebook/Google Ads', '$25\u2013$75/lead', 'Inbound, unqualified', 'Variable'),
        ('Zillow/Realtor Leads', '$20\u2013$50/lead', 'Buyer intent, not investor', 'Variable'),
    ]
    for i, (source, cpl, quality, volume) in enumerate(vendors):
        _write_label(ws, row, 2, source, bold=True)
        ws.cell(row=row, column=3, value=cpl).font = _table_cell_font
        ws.cell(row=row, column=3).alignment = _center
        ws.cell(row=row, column=4, value=quality).font = _table_cell_font
        ws.cell(row=row, column=4).alignment = _center
        ws.cell(row=row, column=5, value=volume).font = _table_cell_font
        ws.cell(row=row, column=5).alignment = _center
        for c in range(2, 8):
            ws.cell(row=row, column=c).border = _thin_border
            if i % 2 == 1:
                ws.cell(row=row, column=c).fill = _light_fill
        ws.row_dimensions[row].height = 22
        row += 1

    row += 1

    # "What $222/month buys you" KPI tiles
    row = _write_section_header(ws, row, 'WHAT $222/MONTH BUYS YOU', fill=_green_fill)

    tiles = [
        ('122K', 'Raw Investor Leads', _navy_fill),
        ('73K', 'Contactable Leads', _blue_fill),
        ('4,150', 'Hot Leads (60+)', _red_fill),
    ]
    row = _write_kpi_tiles(ws, row, tiles)

    _write_merged(ws, 2, 7, row,
        'vs. buying 40 exclusive leads at $100 each = $4,000/mo for FEWER leads',
        font=Font(size=11, bold=True, color=_HOT_RED),
        fill=_white_fill, alignment=_center)
    ws.row_dimensions[row].height = 28


# ---------------------------------------------------------------------------
# Tab 6: Implementation Timeline
# ---------------------------------------------------------------------------

def _build_timeline(wb):
    ws = wb.create_sheet('Timeline')
    _setup_sheet(ws)

    row = _write_banner(ws, 'IMPLEMENTATION TIMELINE')
    row += 1

    # Phase 1
    row = _write_section_header(ws, row, 'PHASE 1 \u2014 WEEKS 1\u20134: LAUNCH', fill=_green_fill)
    row = _write_table_header(ws, row,
        ['Week', 'Task', 'Details', '', '', ''])

    phase1_tasks = [
        ('Week 1', 'Download 3 county NAL files',
         'Palm Beach (done), Broward, Miami-Dade from FDOR site'),
        ('Week 1', 'Run pipeline on all 3 counties',
         'FDOR filter + refi detection + SunBiz + DBPR + scoring'),
        ('Week 2', 'Set up Tier 2 data stack',
         'PropStream ($99) + Apollo Basic ($49) + RentCast ($74)'),
        ('Week 2\u20133', 'First enrichment batch',
         'Skip trace top 5K leads (score 40+) via Apollo/PropStream'),
        ('Week 3\u20134', 'Start outreach',
         'Call/email hot leads (60+), drip campaign for warm leads'),
        ('Week 4', 'Review & optimize',
         'Measure contact rates, close rates, adjust scoring weights'),
    ]
    for i, (week, task, details) in enumerate(phase1_tasks):
        _write_label(ws, row, 2, week, bold=True)
        ws.cell(row=row, column=3, value=task).font = _table_cell_bold
        ws.cell(row=row, column=3).alignment = _left
        _write_label(ws, row, 4, details, end_col=7)
        for c in range(2, 8):
            ws.cell(row=row, column=c).border = _thin_border
            if i % 2 == 1:
                ws.cell(row=row, column=c).fill = _light_fill
        ws.row_dimensions[row].height = 28
        row += 1

    row += 1

    # Phase 2
    row = _write_section_header(ws, row, 'PHASE 2 \u2014 WEEKS 5\u201312: EXPAND', fill=_blue_fill)
    row = _write_table_header(ws, row,
        ['Week', 'Task', 'Details', '', '', ''])

    phase2_tasks = [
        ('Week 5\u20136', 'Add 16 metro counties',
         'Hillsborough, Orange, Duval, Pinellas, Lee, Collier, etc.'),
        ('Week 6\u20138', 'Batch enrichment',
         'Skip trace top leads in each county as pipeline completes'),
        ('Week 8\u201310', 'Referral partner activation',
         'Connect with RE agents, title cos, insurance agents in each market'),
        ('Week 10\u201312', 'Scale outreach',
         'Expand calling capacity, launch market-specific email campaigns'),
    ]
    for i, (week, task, details) in enumerate(phase2_tasks):
        _write_label(ws, row, 2, week, bold=True)
        ws.cell(row=row, column=3, value=task).font = _table_cell_bold
        ws.cell(row=row, column=3).alignment = _left
        _write_label(ws, row, 4, details, end_col=7)
        for c in range(2, 8):
            ws.cell(row=row, column=c).border = _thin_border
            if i % 2 == 1:
                ws.cell(row=row, column=c).fill = _light_fill
        ws.row_dimensions[row].height = 28
        row += 1

    row += 1

    # Phase 3
    row = _write_section_header(ws, row, 'PHASE 3 \u2014 WEEKS 13\u201324: FULL STATE', fill=_orange_fill)
    row = _write_table_header(ws, row,
        ['Week', 'Task', 'Details', '', '', ''])

    phase3_tasks = [
        ('Week 13\u201316', 'Add remaining 48 counties',
         'Batch download and process all remaining FL counties'),
        ('Week 16\u201320', 'Selective enrichment',
         'Focus skip trace budget on highest-scoring leads statewide'),
        ('Week 20\u201324', 'Full state coverage',
         'All 67 counties live, ~470K qualified investor leads in database'),
        ('Ongoing', 'Monthly refresh',
         'Re-run pipeline quarterly to catch new purchases and sales'),
    ]
    for i, (week, task, details) in enumerate(phase3_tasks):
        _write_label(ws, row, 2, week, bold=True)
        ws.cell(row=row, column=3, value=task).font = _table_cell_bold
        ws.cell(row=row, column=3).alignment = _left
        _write_label(ws, row, 4, details, end_col=7)
        for c in range(2, 8):
            ws.cell(row=row, column=c).border = _thin_border
            if i % 2 == 1:
                ws.cell(row=row, column=c).fill = _light_fill
        ws.row_dimensions[row].height = 28
        row += 1

    row += 1

    # Processing benchmarks
    row = _write_section_header(ws, row, 'PROCESSING TIME BENCHMARKS (PER COUNTY)')
    row = _write_table_header(ws, row,
        ['Pipeline Step', 'Time', 'Notes', '', '', ''])

    benchmarks = [
        ('FDOR Download', '5\u201310 min', 'Depends on county size; Palm Beach NAL = 343MB'),
        ('FDOR Filter', '2\u20133 min', 'Chunked processing for large counties'),
        ('Refi Detection', '1\u20132 min', 'Runs on filtered output'),
        ('SunBiz Resolution', '17 min/500', '2-sec delay per lookup; cache helps on re-runs'),
        ('DBPR STR Matching', '1\u20132 min', 'Fuzzy address matching'),
        ('Contact Enrichment', '30\u201360 min', 'Rate-limited; 3-sec delay per lookup'),
        ('Scoring + Excel', '<1 min', 'Fast; all in-memory'),
        ('Full Pipeline', '~60 min', 'Per county, first run (cached runs ~15 min)'),
    ]
    for i, (step, time, notes) in enumerate(benchmarks):
        _write_label(ws, row, 2, step, bold=True)
        ws.cell(row=row, column=3, value=time).font = _table_cell_font
        ws.cell(row=row, column=3).alignment = _center
        _write_label(ws, row, 4, notes, end_col=7)
        for c in range(2, 8):
            ws.cell(row=row, column=c).border = _thin_border
            if i % 2 == 1:
                ws.cell(row=row, column=c).fill = _light_fill
        ws.row_dimensions[row].height = 22
        row += 1


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    today = date.today().isoformat()
    out_path = OUTPUT_DIR / f'roi_analysis_{today}.xlsx'

    wb = Workbook()

    # Tab 1: Executive Summary
    _build_summary(wb)

    # Tab 2: Lead Volume
    _build_lead_volume(wb)

    # Tab 3: Data Stack & Costs
    t1_row, t2_row, t3_row = _build_data_stack(wb)
    cost_sheet_name = 'Data Stack & Costs'

    # Tab 4: Revenue Model
    _build_revenue_model(wb, cost_sheet_name, t2_row, t3_row)

    # Tab 5: Cost Per Lead
    _build_cpl(wb, cost_sheet_name, t2_row, t3_row)

    # Tab 6: Implementation Timeline
    _build_timeline(wb)

    wb.save(str(out_path))
    print(f"ROI analysis workbook saved to: {out_path}")
    print(f"  6 tabs: Executive Summary, Lead Volume, Data Stack & Costs, "
          f"Revenue Model, Cost Per Lead, Timeline")
    print(f"  Yellow cells are editable inputs \u2014 formulas auto-recalculate")


if __name__ == '__main__':
    main()
