# Dossier PDF Redesign — Visual Sales Brief

## The Problem

The current `scrape/scripts/build_dossier_pdf.py` generates a McKinsey-style label:value text dump. It works for analysts but not for salespeople. A loan officer picking up the phone needs to scan a one-pager in 60 seconds and immediately understand three things:

1. **Who is this?** — Name, score, tier, portfolio size
2. **What do they own?** — Properties, equity, debt, DSCR, contact info
3. **What's the opportunity?** — Which product to pitch, what angle to use

The current version answers these with 40+ rows of `Label: Value` text in two columns. No visual hierarchy. No charts. No way to scan it fast.

## What We Want Instead

A visual sales brief that tells a story top-to-bottom. Tables, charts, and signal badges instead of text walls. Think: the one-pager a private equity analyst hands to a partner before a call.

## Design Reference

Use this as the visual inspiration:

**HubSpot CRM Contact Record / Deal Summary layout** — the card-based KPI + contact + activity pattern:
- Top banner with name/score/tier
- Row of 4 KPI metric cards (Portfolio Value, Total Equity, Equity Ratio, Est. DSCR)
- Two-panel middle section: left = contact details, right = visual charts
- Full-width property table with navy header, alternating rows, totals
- Bottom callout box with talking points

## Story Flow (Top to Bottom)

### Act 1: "Who is this?" (y=0-46mm)

**Header bar** — Navy band across full width. Logo left, owner name in large bold white, subtitle line showing `segment | property count | county`. Score indicator top-right (0-100, color-coded: green 50+, amber 30-49, red <30). Tier badge (HOT/WARM) next to it.

**4 KPI cards** — Full-width row of metric boxes with accent top border:
- Portfolio Value | Total Equity | Equity Ratio | Est. DSCR

### Act 2: "What do they own?" (y=48-~table end)

**Left panel (~93mm wide):**
- Contact info rows: phone (with mobile/landline pill badge), email, mailing address
- Entity details if LLC (registered agent, officers, status)
- Opportunity signal pills — colored badges: BRRRR EXIT, EQUITY HARVEST, RATE REFI, OUT-OF-STATE, STR LICENSED, REFI PRIORITY

**Right panel (~93mm wide):**
- **Equity vs Debt chart** — horizontal stacked bar, green=equity / red=debt, with dollar labels inside each segment and cash-out potential callout below
- **DSCR gauge** — semicircle with red (<1.0) / amber (1.0-1.25) / green (>1.25) zones, needle at actual DSCR, value displayed large below, rent + NOI summary line

**Property Portfolio Table** (full width, below the two panels):
```
 #  | Property Address         | Est. Value | Lender     | Rate  | Loan   | Equity
 1  | 5684 Via De La Plata Cir | $376K      | Wachovia   | Fixed | $150K  | $226K
 2  | 16097 Poppy Seed Cir     | $376K      | --         | --    | --     | $376K
 ...
 TOTAL | 11 Properties          | $4.1M      |            |       | $150K  | $4.0M
```

- Navy header row, alternating white/gray data rows, light blue totals row
- Per-property value = avg_property_value (best estimate we have)
- ATTOM loan placed on the matched property address, `--` for the rest
- Totals row sums everything

### Act 3: "How to Win the Business" (bottom)

- Light gray box with accent-blue left border
- Title: "HOW TO WIN THE BUSINESS" in bold navy
- Talking points paragraph (from existing `build_talking_points()`)
- Compact acquisition history line: `Purchases: 12mo: X | 36mo: X | Avg: $XXX | Flips: X`

**Footer:** Confidential | Still Mind Creative | Source: Public Records + Enrichment APIs

## Dynamic Portfolio Size Rules

| Properties | Table Font | Row Height | Max Rows Shown              | Charts            |
|-----------|-----------|-----------|----------------------------|-------------------|
| 1-3       | 7.5pt     | 5.5mm     | All                         | Both full size    |
| 4-8       | 7.5pt     | 5.5mm     | All                         | Both full size    |
| 9-15      | 6.5pt     | 4.5mm     | All                         | Both, compressed  |
| 16+       | 6.0pt     | 4.0mm     | Top 10 + "...and N more"   | Both compressed   |

**Single-page always.** If content exceeds page 1, truncate the property table (show fewer rows + overflow line) rather than spilling to page 2.

## Property Address Parsing

Split `PHY_ADDR1` on `|`, title-case each, truncate at 40 chars. If `len(addresses) < property_count`, add "...and N more properties" overflow row. Match ATTOM loan to correct address by comparing `attom_property_address` against the address list.

## Charts (matplotlib, rendered to temp PNG, embedded in PDF)

1. **Score donut** — partial-ring donut, colored by tier, score number centered, "SCORE" label below
2. **Equity/Debt bar** — horizontal stacked bar, green=equity/red=debt, dollar labels inside segments, cash-out callout below
3. **DSCR gauge** — semicircle with 3 color zones (red/amber/green), needle at actual DSCR, large value below, rent+NOI summary

All charts: 150 dpi, transparent background, saved to tempdir, cleaned up after. If data is missing (no DSCR, no equity), skip that chart and reclaim the space.

## Missing Data Handling

Every section is conditional. No phone -> skip phone row. No DSCR -> skip gauge. No ATTOM loan -> all property rows show "--" for lender/rate/loan, equity = full value. No signals -> skip signal section. Layout calculates y-positions dynamically based on what's present.

## What NOT to Change

Keep all existing helpers intact:
- `fc()`, `fp()`, `fv()`, `fphone()`, `fprop_types()`, `clean_name()`, `redact()`
- `build_talking_points()` — generates the insight paragraph
- `build_csv_export()` — CRM-ready CSV export
- `main()` — CLI entry point with `--input`, `--output-dir`, `--redacted` flags

Only rewrite: `DossierPDF` class and `generate_dossier()` function.

## Technical Stack

- **PDF generation:** fpdf2 (`from fpdf import FPDF`)
- **Charts:** matplotlib (render to PNG, embed in PDF)
- **Data:** pandas Series (one row per investor)
- **Page:** Letter size (215.9 x 279.4mm), portrait, no auto page break

## Test Commands

```bash
# FL samples (richest data — 6 leads with property counts: 11, 8, 3, 3, 4, 2)
python scripts/build_dossier_pdf.py --input data/enriched/fl_client_samples.csv

# Redacted samples
python scripts/build_dossier_pdf.py --input data/enriched/fl_client_samples.csv --redacted

# Wake County (33 leads, sparser data)
python scripts/build_dossier_pdf.py --input data/enriched/wake_samples_enriched.csv
```

Output goes to `data/dossiers/`. Verify:
- Charts render as proper shapes (donut is round, gauge is a semicircle, bar fills its space)
- No text overlapping charts
- Property table adjusts font/rows per portfolio size
- Redacted version masks phone/email/addresses with XXXX
- Score donut color matches tier
- Everything fits on one page
