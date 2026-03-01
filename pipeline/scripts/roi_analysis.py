"""
ROI Proposal for DSCR Lead Generation Pipeline

Simple, clear workbook: what it is, what it costs, how much you make.
Yellow cells are adjustable — change them and the math updates.

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
# Colors & Styles
# ---------------------------------------------------------------------------
_NAVY = '1B2A4A'
_BLUE = '4472C4'
_GREEN = '548235'
_RED = 'C00000'
_LIGHT = 'F2F2F2'
_WHITE = 'FFFFFF'
_YELLOW_BG = 'FFF2CC'

_navy_fill = PatternFill(start_color=_NAVY, end_color=_NAVY, fill_type='solid')
_blue_fill = PatternFill(start_color=_BLUE, end_color=_BLUE, fill_type='solid')
_green_fill = PatternFill(start_color=_GREEN, end_color=_GREEN, fill_type='solid')
_red_fill = PatternFill(start_color=_RED, end_color=_RED, fill_type='solid')
_light_fill = PatternFill(start_color=_LIGHT, end_color=_LIGHT, fill_type='solid')
_white_fill = PatternFill(start_color=_WHITE, end_color=_WHITE, fill_type='solid')
_yellow_fill = PatternFill(start_color=_YELLOW_BG, end_color=_YELLOW_BG, fill_type='solid')

_title_font = Font(size=20, bold=True, color=_WHITE)
_subtitle_font = Font(size=11, color=_WHITE)
_section_font = Font(size=14, bold=True, color=_WHITE)
_big_number = Font(size=28, bold=True, color=_WHITE)
_big_label = Font(size=10, color=_WHITE)
_label_font = Font(size=11, color='333333')
_label_bold = Font(size=11, bold=True, color='333333')
_value_font = Font(size=11, color='333333')
_value_bold = Font(size=11, bold=True, color='333333')
_input_font = Font(size=12, bold=True, color='7F6000')
_result_font = Font(size=14, bold=True, color=_GREEN)
_result_big = Font(size=18, bold=True, color=_GREEN)
_note_font = Font(size=9, italic=True, color='888888')
_footer_font = Font(size=8, italic=True, color='AAAAAA')

_center = Alignment(horizontal='center', vertical='center', wrap_text=True)
_left = Alignment(horizontal='left', vertical='center', wrap_text=True)

_thin = Border(bottom=Side(style='thin', color='D9D9D9'))
_yellow_border = Border(
    bottom=Side(style='thin', color='BF9000'),
    top=Side(style='thin', color='BF9000'),
    left=Side(style='thin', color='BF9000'),
    right=Side(style='thin', color='BF9000'),
)


def _setup(ws):
    ws.sheet_view.showGridLines = False
    ws.column_dimensions['A'].width = 2
    ws.column_dimensions['B'].width = 32
    ws.column_dimensions['C'].width = 22
    ws.column_dimensions['D'].width = 22
    ws.column_dimensions['E'].width = 22
    ws.column_dimensions['F'].width = 22
    ws.column_dimensions['G'].width = 2


def _merged(ws, row, start, end, value, font=None, fill=None, align=None, fmt=None):
    if start != end:
        ws.merge_cells(start_row=row, start_column=start,
                       end_row=row, end_column=end)
    cell = ws.cell(row=row, column=start, value=value)
    if font: cell.font = font
    if fill:
        cell.fill = fill
        for c in range(start, end + 1):
            ws.cell(row=row, column=c).fill = fill
    if align: cell.alignment = align
    if fmt: cell.number_format = fmt
    return cell


def _gutter(ws, row, fill):
    ws.cell(row=row, column=1).fill = fill
    ws.cell(row=row, column=7).fill = fill


def _banner(ws, title):
    row = 1
    _merged(ws, row, 2, 6, title, _title_font, _navy_fill, _center)
    ws.row_dimensions[row].height = 44
    _gutter(ws, row, _navy_fill)
    row += 1
    sub = f'Prepared {date.today().strftime("%B %d, %Y")}  |  Florida DSCR Lending'
    _merged(ws, row, 2, 6, sub, _subtitle_font, _navy_fill, _center)
    ws.row_dimensions[row].height = 24
    _gutter(ws, row, _navy_fill)
    return row + 1


def _section(ws, row, title, fill=None):
    fill = fill or _blue_fill
    _merged(ws, row, 2, 6, title, _section_font, fill, _left)
    ws.row_dimensions[row].height = 30
    return row + 1


def _label_value(ws, row, label, value, fmt=None, bold_val=False, alt=False):
    """Write a label in B-C and a value in D."""
    ws.merge_cells(start_row=row, start_column=2, end_row=row, end_column=3)
    c1 = ws.cell(row=row, column=2, value=label)
    c1.font = _label_bold
    c1.alignment = _left
    c1.border = _thin
    c2 = ws.cell(row=row, column=4, value=value)
    c2.font = _value_bold if bold_val else _value_font
    c2.alignment = _center
    c2.border = _thin
    if fmt: c2.number_format = fmt
    if alt:
        for c in range(2, 7):
            ws.cell(row=row, column=c).fill = _light_fill
    ws.row_dimensions[row].height = 26
    return row + 1


def _input_row(ws, row, label, value, fmt=None):
    """Write a label in B-C and a yellow editable cell in D."""
    ws.merge_cells(start_row=row, start_column=2, end_row=row, end_column=3)
    c1 = ws.cell(row=row, column=2, value=label)
    c1.font = _label_bold
    c1.alignment = _left
    c1.border = _thin
    c2 = ws.cell(row=row, column=4, value=value)
    c2.font = _input_font
    c2.fill = _yellow_fill
    c2.border = _yellow_border
    c2.alignment = _center
    if fmt: c2.number_format = fmt
    ws.row_dimensions[row].height = 28
    return row + 1


def _formula_row(ws, row, label, formula, fmt=None, bold=False, result=False):
    """Write a label in B-C and a formula cell in D."""
    ws.merge_cells(start_row=row, start_column=2, end_row=row, end_column=3)
    c1 = ws.cell(row=row, column=2, value=label)
    c1.font = _label_bold
    c1.alignment = _left
    c1.border = _thin
    c2 = ws.cell(row=row, column=4, value=formula)
    c2.font = _result_big if result else (_result_font if bold else _value_font)
    c2.alignment = _center
    c2.border = _thin
    if fmt: c2.number_format = fmt
    ws.row_dimensions[row].height = 30 if result else 26
    return row + 1


def _kpi_row(ws, row, tiles):
    """Write a row of KPI tiles. Each tile: (value, label, fill)."""
    cols_per = 5 // len(tiles)
    # Value row
    col = 2
    for val, label, fill in tiles:
        end = min(col + cols_per - 1, 6)
        _merged(ws, row, col, end, val, _big_number, fill, _center)
        col = end + 1
    ws.row_dimensions[row].height = 55
    row += 1
    # Label row
    col = 2
    for val, label, fill in tiles:
        end = min(col + cols_per - 1, 6)
        _merged(ws, row, col, end, label, _big_label, fill, _center)
        col = end + 1
    ws.row_dimensions[row].height = 22
    return row + 1


# ---------------------------------------------------------------------------
# Tab 1: The Opportunity
# ---------------------------------------------------------------------------
def _build_opportunity(wb):
    ws = wb.active
    ws.title = 'The Opportunity'
    _setup(ws)

    row = _banner(ws, 'DSCR LEAD GENERATION')
    row += 1

    # Big numbers
    row = _section(ws, row, 'WHAT WE BUILT')

    row = _kpi_row(ws, row, [
        ('39,353', 'Qualified Investor Leads\n(Palm Beach alone)', _navy_fill),
        ('77', 'Hot Leads Ready to Call', _red_fill),
    ])
    row += 1

    # Plain English explanation
    bullets = [
        'We pull every property record in Florida from public tax rolls (free).',
        'We filter for investment properties only \u2014 no homeowners, no noise.',
        'We identify who owns them: individuals, LLCs, foreign buyers, serial investors.',
        'We score and rank every lead so you call the best ones first.',
        'We match against vacation rental licenses to find STR operators.',
        'We resolve LLCs to real human names you can actually call.',
    ]
    row = _section(ws, row, 'HOW IT WORKS')
    for i, bullet in enumerate(bullets):
        _merged(ws, row, 2, 6, f'  {i+1}.  {bullet}', _label_font, None, _left)
        ws.row_dimensions[row].height = 26
        if i % 2 == 1:
            for c in range(2, 7):
                ws.cell(row=row, column=c).fill = _light_fill
        row += 1

    row += 1

    # What's in the leads
    row = _section(ws, row, 'WHAT YOU GET FOR EACH LEAD')
    fields = [
        ('Owner name & mailing address', 'From FL tax records'),
        ('# of investment properties', 'Portfolio size at a glance'),
        ('Total portfolio value', 'Assessed value across all holdings'),
        ('Investor type', 'Serial, STR operator, foreign, entity, etc.'),
        ('Lead score (0\u2013100)', 'Higher = better DSCR candidate'),
        ('Refi signals', 'Cash buyer, equity harvest, rate refi, BRRRR'),
        ('Phone (when available)', 'From vacation rental licenses & enrichment'),
    ]
    for i, (field, desc) in enumerate(fields):
        ws.cell(row=row, column=2, value=field).font = _label_bold
        ws.cell(row=row, column=2).alignment = _left
        ws.cell(row=row, column=2).border = _thin
        ws.merge_cells(start_row=row, start_column=3, end_row=row, end_column=6)
        ws.cell(row=row, column=3, value=desc).font = _value_font
        ws.cell(row=row, column=3).alignment = _left
        ws.cell(row=row, column=3).border = _thin
        if i % 2 == 1:
            for c in range(2, 7):
                ws.cell(row=row, column=c).fill = _light_fill
        ws.row_dimensions[row].height = 24
        row += 1

    row += 1

    # Scale
    row = _section(ws, row, 'THE SCALE', fill=_green_fill)
    scale = [
        ('Palm Beach County (done)', '39,353 leads'),
        ('South Florida (3 counties)', '~120,000 leads'),
        ('All 67 FL counties', '~470,000 leads'),
    ]
    for i, (geo, count) in enumerate(scale):
        ws.cell(row=row, column=2, value=geo).font = _label_bold
        ws.cell(row=row, column=2).alignment = _left
        ws.cell(row=row, column=2).border = _thin
        ws.merge_cells(start_row=row, start_column=3, end_row=row, end_column=6)
        ws.cell(row=row, column=3, value=count).font = _value_bold
        ws.cell(row=row, column=3).alignment = _center
        ws.cell(row=row, column=3).border = _thin
        if i % 2 == 1:
            for c in range(2, 7):
                ws.cell(row=row, column=c).fill = _light_fill
        ws.row_dimensions[row].height = 26
        row += 1

    row += 1
    _merged(ws, row, 2, 6,
        'All data comes from free public sources. No subscriptions required to start.',
        _note_font, _white_fill, _left)


# ---------------------------------------------------------------------------
# Tab 2: Your Calculator
# ---------------------------------------------------------------------------
def _build_calculator(wb):
    ws = wb.create_sheet('Your Calculator')
    _setup(ws)

    row = _banner(ws, 'YOUR REVENUE CALCULATOR')
    row += 1

    # --- YOUR INPUTS ---
    row = _section(ws, row, 'YOUR INPUTS (CHANGE THE YELLOW CELLS)')

    refs = {}

    row = _input_row(ws, row, 'Average DSCR Loan Size', 400000, '$#,##0')
    refs['loan'] = row - 1

    row = _input_row(ws, row, 'Your Comp Per Loan (bps)', 150, '#,##0')
    refs['bps'] = row - 1

    row = _input_row(ws, row, 'Leads You Work Per Month', 500, '#,##0')
    refs['worked'] = row - 1

    row = _input_row(ws, row, 'Close Rate (% of leads worked)', 0.02, '0.0%')
    refs['close'] = row - 1

    row = _input_row(ws, row, 'Monthly Data Costs (optional tools)', 0, '$#,##0')
    refs['cost'] = row - 1

    row += 1

    # --- THE MATH ---
    row = _section(ws, row, 'THE MATH')

    lr = f'D{refs["loan"]}'
    br = f'D{refs["bps"]}'
    wr = f'D{refs["worked"]}'
    cr = f'D{refs["close"]}'
    co = f'D{refs["cost"]}'

    row = _formula_row(ws, row, 'Your Revenue Per Closed Loan',
        f'={lr}*{br}/10000', '$#,##0')
    rev_ref = f'D{row - 1}'

    row = _formula_row(ws, row, 'Closings Per Month',
        f'=ROUND({wr}*{cr},1)', '#,##0.0')
    close_ref = f'D{row - 1}'

    row = _formula_row(ws, row, 'Monthly Revenue',
        f'={close_ref}*{rev_ref}', '$#,##0', bold=True)
    monthly_ref = f'D{row - 1}'

    row = _formula_row(ws, row, 'Monthly Profit (after data costs)',
        f'={monthly_ref}-{co}', '$#,##0', bold=True)
    profit_ref = f'D{row - 1}'

    row += 1

    # --- THE ANSWER ---
    row = _section(ws, row, 'YOUR ANNUAL NUMBERS', fill=_green_fill)

    row = _formula_row(ws, row, 'Annual Revenue',
        f'={monthly_ref}*12', '$#,##0', result=True)
    annual_ref = f'D{row - 1}'

    row = _formula_row(ws, row, 'Annual Data Costs',
        f'={co}*12', '$#,##0')
    annual_cost_ref = f'D{row - 1}'

    row = _formula_row(ws, row, 'Annual Profit',
        f'={profit_ref}*12', '$#,##0', result=True)

    row = _formula_row(ws, row, 'ROI on Data Spend',
        f'=IF({annual_cost_ref}=0,"\u221e (free)",ROUND({annual_ref}/{annual_cost_ref},0)&"x")')

    row += 1

    # --- SCENARIOS ---
    row = _section(ws, row, 'WHAT IF?')

    _merged(ws, row, 2, 6,
        'Try changing the yellow cells above. Here are some scenarios:',
        _note_font, _white_fill, _left)
    row += 1

    scenarios = [
        ('Conservative: 1% close, 300 leads/mo',
         '300 leads x 1% = 3 closings x $6K = $18K/mo'),
        ('Base case: 2% close, 500 leads/mo',
         '500 leads x 2% = 10 closings x $6K = $60K/mo'),
        ('Aggressive: 3% close, 800 leads/mo',
         '800 leads x 3% = 24 closings x $6K = $144K/mo'),
    ]
    for i, (scenario, math) in enumerate(scenarios):
        ws.cell(row=row, column=2, value=scenario).font = _label_bold
        ws.cell(row=row, column=2).alignment = _left
        ws.cell(row=row, column=2).border = _thin
        ws.merge_cells(start_row=row, start_column=3, end_row=row, end_column=6)
        ws.cell(row=row, column=3, value=math).font = _value_font
        ws.cell(row=row, column=3).alignment = _left
        ws.cell(row=row, column=3).border = _thin
        if i % 2 == 1:
            for c in range(2, 7):
                ws.cell(row=row, column=c).fill = _light_fill
        ws.row_dimensions[row].height = 28
        row += 1

    row += 1
    _merged(ws, row, 2, 6,
        'Assumes $400K avg loan, 150 bps comp ($6K/loan). '
        'Adjust yellow cells to match your numbers.',
        _note_font, _white_fill, _left)


# ---------------------------------------------------------------------------
# Tab 3: What It Costs
# ---------------------------------------------------------------------------
def _build_costs(wb):
    ws = wb.create_sheet('What It Costs')
    _setup(ws)

    row = _banner(ws, 'WHAT IT COSTS')
    row += 1

    # Free tier
    row = _section(ws, row, 'FREE \u2014 WHAT YOU HAVE TODAY', fill=_green_fill)

    free_items = [
        ('FL Property Tax Records (FDOR)', '$0', 'Every property in Florida'),
        ('FL Corporation Search (SunBiz)', '$0', 'LLC to real name resolution'),
        ('FL Vacation Rental Licenses (DBPR)', '$0', 'STR operator identification + phones'),
        ('SEC Fund Filings (EDGAR)', '$0', 'Fund manager / syndicator detection'),
    ]
    for i, (source, cost, what) in enumerate(free_items):
        ws.cell(row=row, column=2, value=source).font = _label_bold
        ws.cell(row=row, column=2).alignment = _left
        ws.cell(row=row, column=2).border = _thin
        ws.cell(row=row, column=3, value=cost).font = Font(size=11, bold=True, color=_GREEN)
        ws.cell(row=row, column=3).alignment = _center
        ws.cell(row=row, column=3).border = _thin
        ws.merge_cells(start_row=row, start_column=4, end_row=row, end_column=6)
        ws.cell(row=row, column=4, value=what).font = _value_font
        ws.cell(row=row, column=4).alignment = _left
        ws.cell(row=row, column=4).border = _thin
        if i % 2 == 1:
            for c in range(2, 7):
                ws.cell(row=row, column=c).fill = _light_fill
        ws.row_dimensions[row].height = 26
        row += 1

    row += 1

    # Optional upgrades
    row = _section(ws, row, 'OPTIONAL \u2014 ADD WHEN READY')

    _merged(ws, row, 2, 6,
        'These are optional tools to get phone numbers and emails for more leads. '
        'Not required to start. Add them when you\'re ready to scale outreach.',
        _note_font, _white_fill, _left)
    ws.row_dimensions[row].height = 36
    row += 1

    paid_items = [
        ('Apollo.io (email/phone lookup)', 49, '25K contacts/month'),
        ('PropStream (property data + skip trace)', 99, 'MLS comps, mortgage data, phones'),
        ('RentCast (rental estimates)', 74, 'Rental comps for DSCR underwriting'),
    ]
    cost_rows = []
    for i, (source, cost, what) in enumerate(paid_items):
        ws.cell(row=row, column=2, value=source).font = _label_bold
        ws.cell(row=row, column=2).alignment = _left
        ws.cell(row=row, column=2).border = _thin
        c = ws.cell(row=row, column=3, value=cost)
        c.font = _input_font
        c.fill = _yellow_fill
        c.border = _yellow_border
        c.alignment = _center
        c.number_format = '$#,##0'
        cost_rows.append(row)
        ws.merge_cells(start_row=row, start_column=4, end_row=row, end_column=6)
        ws.cell(row=row, column=4, value=what).font = _value_font
        ws.cell(row=row, column=4).alignment = _left
        ws.cell(row=row, column=4).border = _thin
        if i % 2 == 1:
            for c_idx in range(2, 7):
                ws.cell(row=row, column=c_idx).fill = _light_fill
        ws.row_dimensions[row].height = 26
        row += 1

    # Total
    row += 1
    ws.merge_cells(start_row=row, start_column=2, end_row=row, end_column=2)
    ws.cell(row=row, column=2, value='Monthly Total (if all added)').font = _label_bold
    ws.cell(row=row, column=2).alignment = _left
    sum_parts = '+'.join(f'C{r}' for r in cost_rows)
    c = ws.cell(row=row, column=3, value=f'={sum_parts}')
    c.font = Font(size=12, bold=True, color=_RED)
    c.alignment = _center
    c.number_format = '$#,##0'
    ws.row_dimensions[row].height = 28
    row += 2

    # Comparison
    row = _section(ws, row, 'FOR CONTEXT')

    comparisons = [
        ('This pipeline (free tier)', '$0/mo', '39,000+ scored leads per county'),
        ('This pipeline (full tools)', '$222/mo', '+ phone/email for 60-70% of leads'),
        ('Buying leads from a vendor', '$100\u2013250 each', '40\u2013100 leads/month, no scoring'),
        ('Facebook/Google ads', '$25\u201375 each', 'Inbound but unqualified'),
    ]
    for i, (source, cost, notes) in enumerate(comparisons):
        ws.cell(row=row, column=2, value=source).font = _label_bold
        ws.cell(row=row, column=2).alignment = _left
        ws.cell(row=row, column=2).border = _thin
        ws.cell(row=row, column=3, value=cost).font = _value_bold
        ws.cell(row=row, column=3).alignment = _center
        ws.cell(row=row, column=3).border = _thin
        ws.merge_cells(start_row=row, start_column=4, end_row=row, end_column=6)
        ws.cell(row=row, column=4, value=notes).font = _value_font
        ws.cell(row=row, column=4).alignment = _left
        ws.cell(row=row, column=4).border = _thin
        if i % 2 == 1:
            for c_idx in range(2, 7):
                ws.cell(row=row, column=c_idx).fill = _light_fill
        ws.row_dimensions[row].height = 26
        row += 1

    row += 1
    _merged(ws, row, 2, 6,
        'Tip: Enter your monthly tool costs in the yellow cells above, '
        'then copy the total to the "Monthly Data Costs" cell on the Calculator tab.',
        _note_font, _white_fill, _left)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    today = date.today().isoformat()
    out_path = OUTPUT_DIR / f'roi_analysis_{today}.xlsx'

    wb = Workbook()

    _build_opportunity(wb)
    _build_calculator(wb)
    _build_costs(wb)

    wb.save(str(out_path))
    print(f"Proposal saved: {out_path}")
    print(f"  3 tabs: The Opportunity, Your Calculator, What It Costs")
    print(f"  Yellow cells are adjustable \u2014 formulas update automatically")


if __name__ == '__main__':
    main()
