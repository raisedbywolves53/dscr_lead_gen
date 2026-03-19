const { Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, Header, Footer,
        AlignmentType, BorderStyle, WidthType, ShadingType, VerticalAlign, PageNumber, HeadingLevel, TabStopType } = require('docx');
const fs = require('fs');

const NAVY_BLUE = "1B3A5C";
const LIGHT_GRAY = "CCCCCC";
const WHITE = "FFFFFF";

const border = { style: BorderStyle.SINGLE, size: 1, color: LIGHT_GRAY };
const borders = { top: border, bottom: border, left: border, right: border };

function createHeading1(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_1,
    children: [new TextRun({ text, bold: true, size: 32, font: "Arial", color: NAVY_BLUE })],
    spacing: { before: 240, after: 120 },
  });
}

function createHeading2(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_2,
    children: [new TextRun({ text, bold: true, size: 28, font: "Arial", color: NAVY_BLUE })],
    spacing: { before: 180, after: 100 },
  });
}

function createNormalText(text, options = {}) {
  return new Paragraph({
    children: [new TextRun({ text, font: "Arial", size: 24, ...options })],
    spacing: { after: 80 },
  });
}

function createTableHeader(cells) {
  return new TableRow({
    children: cells.map(text => new TableCell({
      borders,
      width: { size: 2340, type: WidthType.DXA },
      shading: { fill: NAVY_BLUE, type: ShadingType.CLEAR },
      margins: { top: 80, bottom: 80, left: 120, right: 120 },
      verticalAlign: VerticalAlign.CENTER,
      children: [new Paragraph({
        children: [new TextRun({ text, bold: true, font: "Arial", size: 22, color: WHITE })],
        alignment: AlignmentType.CENTER,
      })],
    }))
  });
}

function createTableRow(cells, width = 2340) {
  return new TableRow({
    children: cells.map(text => new TableCell({
      borders,
      width: { size: width, type: WidthType.DXA },
      shading: { fill: "F5F5F5", type: ShadingType.CLEAR },
      margins: { top: 80, bottom: 80, left: 120, right: 120 },
      children: [new Paragraph({
        children: [new TextRun({ text, font: "Arial", size: 22 })],
      })],
    }))
  });
}

function createTwoColTable(headerCols, rows) {
  const width = 9360;
  const colWidth = 4680;

  return new Table({
    width: { size: width, type: WidthType.DXA },
    columnWidths: [colWidth, colWidth],
    rows: [
      new TableRow({
        children: headerCols.map(text => new TableCell({
          borders,
          width: { size: colWidth, type: WidthType.DXA },
          shading: { fill: NAVY_BLUE, type: ShadingType.CLEAR },
          margins: { top: 80, bottom: 80, left: 120, right: 120 },
          verticalAlign: VerticalAlign.CENTER,
          children: [new Paragraph({
            children: [new TextRun({ text, bold: true, font: "Arial", size: 22, color: WHITE })],
            alignment: AlignmentType.CENTER,
          })],
        }))
      }),
      ...rows.map(([col1, col2]) => new TableRow({
        children: [
          new TableCell({
            borders,
            width: { size: colWidth, type: WidthType.DXA },
            margins: { top: 80, bottom: 80, left: 120, right: 120 },
            children: [new Paragraph({
              children: [new TextRun({ text: col1, font: "Arial", size: 22, bold: true })],
            })],
          }),
          new TableCell({
            borders,
            width: { size: colWidth, type: WidthType.DXA },
            margins: { top: 80, bottom: 80, left: 120, right: 120 },
            children: [new Paragraph({
              children: [new TextRun({ text: col2, font: "Arial", size: 22 })],
            })],
          }),
        ],
      }))
    ],
  });
}

function createThreeColTable(headers, rows) {
  const width = 9360;
  const colWidth = 3120;

  return new Table({
    width: { size: width, type: WidthType.DXA },
    columnWidths: [colWidth, colWidth, colWidth],
    rows: [
      new TableRow({
        children: headers.map(text => new TableCell({
          borders,
          width: { size: colWidth, type: WidthType.DXA },
          shading: { fill: NAVY_BLUE, type: ShadingType.CLEAR },
          margins: { top: 80, bottom: 80, left: 120, right: 120 },
          verticalAlign: VerticalAlign.CENTER,
          children: [new Paragraph({
            children: [new TextRun({ text, bold: true, font: "Arial", size: 22, color: WHITE })],
            alignment: AlignmentType.CENTER,
          })],
        }))
      }),
      ...rows.map(([col1, col2, col3]) => new TableRow({
        children: [
          new TableCell({
            borders,
            width: { size: colWidth, type: WidthType.DXA },
            margins: { top: 80, bottom: 80, left: 120, right: 120 },
            children: [new Paragraph({
              children: [new TextRun({ text: col1, font: "Arial", size: 22 })],
            })],
          }),
          new TableCell({
            borders,
            width: { size: colWidth, type: WidthType.DXA },
            margins: { top: 80, bottom: 80, left: 120, right: 120 },
            children: [new Paragraph({
              children: [new TextRun({ text: col2, font: "Arial", size: 22 })],
            })],
          }),
          new TableCell({
            borders,
            width: { size: colWidth, type: WidthType.DXA },
            margins: { top: 80, bottom: 80, left: 120, right: 120 },
            children: [new Paragraph({
              children: [new TextRun({ text: col3, font: "Arial", size: 22 })],
            })],
          }),
        ],
      }))
    ],
  });
}

const contentChildren = [
  // Title
  new Paragraph({
    children: [new TextRun({
      text: "ATTOM API Integration Specification",
      bold: true,
      size: 36,
      font: "Arial",
      color: NAVY_BLUE,
    })],
    spacing: { before: 240, after: 60 },
    alignment: AlignmentType.CENTER,
  }),

  new Paragraph({
    children: [new TextRun({
      text: "Still Mind Creative",
      size: 26,
      font: "Arial",
      color: "666666",
    })],
    spacing: { after: 240 },
    alignment: AlignmentType.CENTER,
  }),

  // 1. Overview
  createHeading1("1. Overview"),
  createNormalText("Still Mind Creative is building a nationwide lead generation platform for DSCR (Debt Service Coverage Ratio) mortgage lending. The platform identifies investment property owners from public records and enriches them with comprehensive financial, valuation, and transaction data."),
  createNormalText("ATTOM Data provides critical enrichment services including:"),
  new Paragraph({
    children: [new TextRun({ text: "Financing intelligence (mortgages, lenders, loan terms)", font: "Arial", size: 24 })],
    spacing: { after: 60 },
    indent: { left: 360 },
  }),
  new Paragraph({
    children: [new TextRun({ text: "Property valuations and AVM (Automated Valuation Models) with confidence scoring", font: "Arial", size: 24 })],
    spacing: { after: 60 },
    indent: { left: 360 },
  }),
  new Paragraph({
    children: [new TextRun({ text: "Rental income estimates for DSCR calculation", font: "Arial", size: 24 })],
    spacing: { after: 60 },
    indent: { left: 360 },
  }),
  new Paragraph({
    children: [new TextRun({ text: "10-year transaction history and cash purchase identification", font: "Arial", size: 24 })],
    spacing: { after: 240 },
    indent: { left: 360 },
  }),

  createNormalText("These data points power a sophisticated lead scoring engine that identifies high-probability DSCR lending opportunities by profiling investor behavior, equity position, leverage history, and rate/term refinance eligibility."),

  // 2. API Configuration
  createHeading1("2. API Configuration"),
  createTwoColTable(
    ["Parameter", "Value"],
    [
      ["Authentication", "API key in request header"],
      ["HTTP Method", "GET"],
      ["Base URL", "https://api.gateway.attomdata.com"],
      ["API Version", "v1.0.0"],
      ["Auth Header Name", "apikey"],
      ["Response Format", "JSON"],
      ["Rate Limit", "Contact ATTOM for tier details"],
    ]
  ),

  new Paragraph({ children: [new TextRun("")], spacing: { after: 240 } }),

  // 3. Endpoints Required
  createHeading1("3. Endpoints Required"),
  createHeading2("3.1 Primary Endpoints (7 total)"),

  createHeading2("/property/detailmortgageowner"),
  createNormalText("URL Path: /propertyapi/v1.0.0/property/detailmortgageowner", { bold: true }),
  createNormalText("Returns combined mortgage, owner, and property data including lender details, loan amount, interest rate, due date, and borrower information."),
  createNormalText("Example Query:"),
  createNormalText("?apn=123456789&fips=12099", { italic: true }),

  new Paragraph({ children: [new TextRun("")], spacing: { after: 180 } }),

  createHeading2("/property/expandedprofile"),
  createNormalText("URL Path: /propertyapi/v1.0.0/property/expandedprofile", { bold: true }),
  createNormalText("Provides comprehensive property characteristics, zoning information, census data, and transaction classification flags (quit claim, REO, resale vs. new construction)."),
  createNormalText("Example Query:"),
  createNormalText("?apn=123456789&fips=12099", { italic: true }),

  new Paragraph({ children: [new TextRun("")], spacing: { after: 180 } }),

  createHeading2("/attomavm/detail"),
  createNormalText("URL Path: /propertyapi/v1.0.0/attomavm/detail", { bold: true }),
  createNormalText("Current market value (AVM) with confidence score, appreciation trends, and condition-based valuations (poor/good/excellent scenarios)."),
  createNormalText("Example Query:"),
  createNormalText("?apn=123456789&fips=12099", { italic: true }),

  new Paragraph({ children: [new TextRun("")], spacing: { after: 180 } }),

  createHeading2("/valuation/rentalavm"),
  createNormalText("URL Path: /propertyapi/v1.0.0/valuation/rentalavm", { bold: true }),
  createNormalText("Property-specific rental income estimates with monthly rent, minimum, and maximum ranges for conservative and aggressive DSCR scenarios."),
  createNormalText("Example Query:"),
  createNormalText("?apn=123456789&fips=12099", { italic: true }),

  new Paragraph({ children: [new TextRun("")], spacing: { after: 180 } }),

  createHeading2("/saleshistory/detail"),
  createNormalText("URL Path: /propertyapi/v1.0.0/saleshistory/detail", { bold: true }),
  createNormalText("10-year transaction history with cash vs. mortgage purchase flags, flip detection, and price per bed/sqft comparisons."),
  createNormalText("Example Query:"),
  createNormalText("?apn=123456789&fips=12099", { italic: true }),

  new Paragraph({ children: [new TextRun("")], spacing: { after: 180 } }),

  createHeading2("/assessment/detail"),
  createNormalText("URL Path: /propertyapi/v1.0.0/assessment/detail", { bold: true }),
  createNormalText("Tax assessments, assessed and market values, land vs. improvement breakdown, and annual tax amounts for NOI calculation."),
  createNormalText("Example Query:"),
  createNormalText("?apn=123456789&fips=12099", { italic: true }),

  new Paragraph({ children: [new TextRun("")], spacing: { after: 180 } }),

  createHeading2("/property/buildingpermits"),
  createNormalText("URL Path: /propertyapi/v1.0.0/property/buildingpermits", { bold: true }),
  createNormalText("Building permit and renovation activity including permit dates, types, job values, and contractor names for investment timeline analysis."),
  createNormalText("Example Query:"),
  createNormalText("?apn=123456789&fips=12099", { italic: true }),

  new Paragraph({ children: [new TextRun("")], spacing: { after: 240 } }),

  // 4. Query Parameters
  createHeading1("4. Query Parameters"),
  createTwoColTable(
    ["Parameter", "Description & Examples"],
    [
      ["apn", "Assessor Parcel Number (APN) — Unique property identifier within county. Example: 123456789"],
      ["fips", "Federal Information Processing System (FIPS) code. Combined county code for state + county. Example: 12099 (Florida Palm Beach)"],
      ["address1", "Primary street address. Example: 123 Main Street"],
      ["address2", "Secondary address (apt/suite). Example: Suite 200"],
      ["city", "City name. Example: West Palm Beach"],
      ["state", "State abbreviation. Example: FL"],
      ["zip", "ZIP code. Example: 33401"],
    ]
  ),

  new Paragraph({ children: [new TextRun("")], spacing: { after: 240 } }),

  // 5. Data Points Requested
  createHeading1("5. Data Points Requested"),

  createHeading2("5.1 Mortgage & Financing Data"),
  createTwoColTable(
    ["Data Point", "Business Use"],
    [
      ["Lender Name", "Identify hard money vs. conventional; target hard money for refi partnerships"],
      ["Lender City & State", "Local vs. national lender competitive positioning and referral opportunity"],
      ["Title Company", "Referral network development and closing cost estimation"],
      ["Loan Amount", "Estimate current LTV; size the refinance opportunity"],
      ["Loan Date (Origination)", "Calculate loan age; ID rate refi candidates from 2022-2023 high-rate vintages"],
      ["Loan Type Code", "Distinguish conventional, FHA, VA, hard money, private equity"],
      ["Interest Rate", "Identify above-market rates for rate-and-term refinance targeting"],
      ["Interest Rate Type", "Fixed vs. ARM; ARM borrowers approaching reset = high priority lead"],
      ["Deed Type", "Confirm transaction type (warranty deed, quit claim, etc.)"],
      ["Due Date/Maturity", "Identify loans approaching maturity for refinance urgency scoring"],
      ["Loan Term", "Distinguish short-term bridge/hard money from long-term conventional"],
    ]
  ),

  new Paragraph({ children: [new TextRun("")], spacing: { after: 180 } }),

  createHeading2("5.2 Owner & Ownership Data"),
  createTwoColTable(
    ["Data Point", "Business Use"],
    [
      ["Owner Name (Full/First/Last)", "Contact ID matching; sync with skip trace results"],
      ["Owner Relationship Type", "Identify joint ownership and trust structures"],
      ["Corporate Indicator", "Flag LLC/Corp/Trust for entity resolution and B2B outreach"],
      ["Absentee Owner Status", "Core investor signal: 3x more likely to be leverageable investor"],
      ["Mailing Address", "Direct mail campaigns and out-of-state investor detection"],
      ["Owner Type & Description", "Individual vs. corporate classification for targeting"],
    ]
  ),

  new Paragraph({ children: [new TextRun("")], spacing: { after: 180 } }),

  createHeading2("5.3 Property Valuation (AVM)"),
  createTwoColTable(
    ["Data Point", "Business Use"],
    [
      ["AVM Estimated Value", "Current market value for LTV and equity estimation"],
      ["AVM Confidence Score", "Data quality indicator for value reliability weighting"],
      ["AVM High/Low Range", "Value range for conservative/aggressive LTV scenarios"],
      ["AVM Value Per SqFt", "Comp analysis and underwriting standardization"],
      ["AVM Last Month Value", "Month-over-month appreciation tracking"],
      ["AVM % Change", "Appreciation trend for equity growth identification"],
      ["AVM by Condition (Poor/Good/Excellent)", "Value sensitivity to renovations (BRRRR signal)"],
    ]
  ),

  new Paragraph({ children: [new TextRun("")], spacing: { after: 180 } }),

  createHeading2("5.4 Rental Valuation"),
  createTwoColTable(
    ["Data Point", "Business Use"],
    [
      ["Estimated Monthly Rent", "Property-specific income for DSCR calculation"],
      ["Estimated Min/Max Rent", "Conservative/aggressive DSCR scenarios"],
      ["Valuation Date", "Freshness indicator for data accuracy"],
    ]
  ),

  new Paragraph({ children: [new TextRun("")], spacing: { after: 180 } }),

  createHeading2("5.5 Assessment & Tax Data"),
  createTwoColTable(
    ["Data Point", "Business Use"],
    [
      ["Assessed Total Value", "Official tax valuation baseline"],
      ["Assessed Improvement Value", "Building component (vs. land)"],
      ["Assessed Land Value", "Land component of total assessed value"],
      ["Market Total/Improvement/Land Values", "Market-based valuations for LTV"],
      ["Improvement Percentage", "Land vs. building ratio for BRRRR analysis"],
      ["Annual Tax Amount", "Expense input for NOI calculations"],
      ["Tax Year", "Data currency verification"],
      ["Tax Per Size Unit", "Normalized tax burden comparison"],
    ]
  ),

  new Paragraph({ children: [new TextRun("")], spacing: { after: 180 } }),

  createHeading2("5.6 Sales & Transaction History"),
  createTwoColTable(
    ["Data Point", "Business Use"],
    [
      ["Sale Amount", "Historical purchase prices for equity estimation"],
      ["Sale Date", "Transaction timing for hold period and flip analysis"],
      ["Sale Document Type", "Deed type verification (warranty, quit claim)"],
      ["Sale Transaction Type", "Resale vs. new construction classification"],
      ["Cash or Mortgage Purchase", "CRITICAL: Confirms cash buyers (prime refi candidates)"],
      ["Interfamily Transfer Flag", "Filter out non-arms-length transactions"],
      ["Buyer/Seller Names", "Ownership chain analysis"],
      ["Price Per Bed/SqFt", "Normalized sale price comparisons"],
    ]
  ),

  new Paragraph({ children: [new TextRun("")], spacing: { after: 180 } }),

  createHeading2("5.7 Building & Property Characteristics"),
  createTwoColTable(
    ["Data Point", "Business Use"],
    [
      ["Building Size/Living Size/Gross Size", "Accurate sqft for rent-per-sqft calculations"],
      ["Beds/Baths (Full + Partial)", "Rental comp matching and unit type classification"],
      ["Year Built", "Age-related lending eligibility and insurance considerations"],
      ["Construction Type/Frame/Roof/Wall", "Insurance and lending qualification factors"],
      ["Condition", "Property condition assessment for BRRRR potential"],
      ["Stories/Levels", "Property type classification"],
      ["Parking Size", "Amenity factor for rental premium"],
      ["Pool Type", "Value and rental premium factor"],
      ["Zoning Type/Zoning ID", "Land use verification for commercial/mixed-use"],
      ["Census Tract/Block Group", "Demographic overlay capability"],
    ]
  ),

  new Paragraph({ children: [new TextRun("")], spacing: { after: 180 } }),

  createHeading2("5.8 Building Permits"),
  createTwoColTable(
    ["Data Point", "Business Use"],
    [
      ["Permit Date/Number/Status", "Renovation timeline tracking"],
      ["Permit Type/Description", "Type of work (BRRRR signal: reroofing, HVAC, electrical)"],
      ["Job Value", "Renovation investment amount"],
      ["Contractor/Business Name", "Investor network identification"],
      ["Previous Owner Name on Permit", "Ownership chain verification"],
    ]
  ),

  new Paragraph({ children: [new TextRun("")], spacing: { after: 180 } }),

  createHeading2("5.9 Transaction Flags"),
  createTwoColTable(
    ["Data Point", "Business Use"],
    [
      ["Quit Claim Flag", "Distress signal (non-standard transfer)"],
      ["REO Flag", "Foreclosure/bank-owned signal for opportunity identification"],
      ["Resale or New Construction", "Transaction classification"],
    ]
  ),

  new Paragraph({ children: [new TextRun("")], spacing: { after: 180 } }),

  createHeading2("5.10 Lot & Location Data"),
  createTwoColTable(
    ["Data Point", "Business Use"],
    [
      ["Lot Size (acres + sqft)", "Land value component and development potential"],
      ["Lot Depth/Frontage", "Development potential for commercial properties"],
      ["Subdivision Name", "Neighborhood-level analysis and comp analysis"],
      ["Lat/Long Coordinates", "Mapping and spatial analysis integration"],
      ["Municipality Name/Code", "Jurisdiction identification and compliance"],
    ]
  ),

  new Paragraph({ children: [new TextRun("")], spacing: { after: 240 } }),

  // 6. Expected API Volume
  createHeading1("6. Expected API Volume"),
  createThreeColTable(
    ["Metric", "Current (Q1 2026)", "Projected (12-Month Scale)"],
    [
      ["Active Markets", "2 (FL, NC)", "10-15 markets"],
      ["Leads Per Market", "3K-8K", "5K-15K"],
      ["Monthly API Calls", "5K-10K", "50K-150K"],
      ["Primary Lookup Method", "APN + FIPS", "APN + FIPS (primary); Address fallback"],
      ["Data Freshness Requirement", "Quarterly refresh", "Monthly refresh"],
    ]
  ),

  new Paragraph({ children: [new TextRun("")], spacing: { after: 240 } }),

  // 7. Example API Call
  createHeading1("7. Example API Call (Verified: March 18, 2026)"),
  createNormalText("Request:", { bold: true }),
  new Paragraph({
    children: [new TextRun("GET https://api.gateway.attomdata.com/propertyapi/v1.0.0/property/detailmortgageowner?apn=123456789&fips=12099", { font: "Courier New", size: 22 })],
    spacing: { after: 60 },
    indent: { left: 360 },
  }),

  createNormalText("Response:", { bold: true }),
  createNormalText("Status: 200 OK"),
  createNormalText("Response Size: 3.91 KB"),
  createNormalText("Response Time: 242 ms"),

  new Paragraph({ children: [new TextRun("")], spacing: { after: 240 } }),

  // 8. Target Counties
  createHeading1("8. Target Counties"),
  createThreeColTable(
    ["State", "County", "FIPS Code", "Status"],
    [
      ["Florida", "Palm Beach", "12099", "Active"],
      ["Florida", "Broward", "12011", "Active"],
      ["North Carolina", "Wake", "37183", "In Progress"],
      ["North Carolina", "Mecklenburg", "37119", "In Progress"],
    ]
  ),

  new Paragraph({ children: [new TextRun("")], spacing: { after: 240 } }),

  // 9. Contact
  createHeading1("9. Contact Information"),
  createNormalText("Zack, Still Mind Creative"),
  createNormalText("Email: admin@stillmindcreative.com"),
];

const doc = new Document({
  styles: {
    default: {
      document: {
        run: { font: "Arial", size: 24 }
      }
    },
    paragraphStyles: [
      {
        id: "Heading1",
        name: "Heading 1",
        basedOn: "Normal",
        next: "Normal",
        quickFormat: true,
        run: { size: 32, bold: true, font: "Arial", color: NAVY_BLUE },
        paragraph: { spacing: { before: 240, after: 120 }, outlineLevel: 0 }
      },
      {
        id: "Heading2",
        name: "Heading 2",
        basedOn: "Normal",
        next: "Normal",
        quickFormat: true,
        run: { size: 28, bold: true, font: "Arial", color: NAVY_BLUE },
        paragraph: { spacing: { before: 180, after: 100 }, outlineLevel: 1 }
      }
    ]
  },
  sections: [{
    properties: {
      page: {
        size: {
          width: 12240,
          height: 15840
        },
        margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 }
      }
    },
    headers: {
      default: new Header({
        children: [
          new Paragraph({
            children: [
              new TextRun("Still Mind Creative — ATTOM API Integration"),
              new TextRun("\t"),
            ],
            tabStops: [{ type: TabStopType.RIGHT, position: 10800 }],
            spacing: { after: 80 },
            border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: NAVY_BLUE, space: 1 } }
          })
        ]
      })
    },
    footers: {
      default: new Footer({
        children: [
          new Paragraph({
            children: [
              new TextRun("Prepared March 18, 2026"),
              new TextRun("\t"),
              new TextRun("Page "),
              new TextRun({ children: [PageNumber.CURRENT] })
            ],
            tabStops: [{ type: TabStopType.RIGHT, position: 10800 }],
            spacing: { before: 80 },
            border: { top: { style: BorderStyle.SINGLE, size: 6, color: NAVY_BLUE, space: 1 } }
          })
        ]
      })
    },
    children: contentChildren
  }]
});

Packer.toBuffer(doc).then(buffer => {
  fs.writeFileSync("/sessions/keen-amazing-darwin/mnt/dscr_lead_gen/ATTOM_API_Integration_Spec.docx", buffer);
  console.log("Document created successfully: ATTOM_API_Integration_Spec.docx");
});
