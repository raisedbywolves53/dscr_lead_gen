/**
 * DSCR Lead Intelligence Pitchbook Generator
 *
 * Generates a 16-slide 16:9 PPTX using pptxgenjs.
 * Run: node build.js
 * Output: dscr_pitchbook.pptx (same directory)
 */

const pptxgen = require("pptxgenjs");
const path = require("path");

// ─── Design Tokens ───────────────────────────────────────────────────────────
const C = {
  navy: "1a237e",
  teal: "00796b",
  orange: "e65100",
  lightBg: "F7F5F2",
  darkBg: "1B262C",
  cardDark: "233840",
  bodyLight: "E8ECF0",
  white: "FFFFFF",
  black: "000000",
  darkText: "212121",
  mutedText: "6B7280",
  greenCheck: "2E7D32",
  redX: "C62828",
  tealLight: "E0F2F1",
  orangeLight: "FFF3E0",
};

const FONT = { header: "Trebuchet MS", body: "Calibri" };

function makeShadow() {
  return {
    type: "outer",
    color: "000000",
    blur: 6,
    offset: 2,
    angle: 135,
    opacity: 0.12,
  };
}

// ─── Helpers ─────────────────────────────────────────────────────────────────

function addCard(slide, x, y, w, h, opts = {}) {
  const fill = opts.fill || C.white;
  slide.addShape("rect", {
    x,
    y,
    w,
    h,
    fill: { color: fill },
    rectRadius: 0.08,
    shadow: makeShadow(),
  });
  // accent bar on left
  if (opts.accent !== false) {
    const accentColor = opts.accentColor || C.teal;
    slide.addShape("rect", {
      x,
      y,
      w: 0.06,
      h,
      fill: { color: accentColor },
      rectRadius: 0.03,
    });
  }
}

function addDarkCard(slide, x, y, w, h, opts = {}) {
  const fill = opts.fill || C.cardDark;
  slide.addShape("rect", {
    x,
    y,
    w,
    h,
    fill: { color: fill },
    rectRadius: 0.08,
    shadow: makeShadow(),
  });
  if (opts.accent !== false) {
    const accentColor = opts.accentColor || C.teal;
    slide.addShape("rect", {
      x,
      y,
      w: 0.06,
      h,
      fill: { color: accentColor },
      rectRadius: 0.03,
    });
  }
}

function lightSlide(pres, title) {
  const slide = pres.addSlide();
  slide.background = { fill: C.lightBg };
  if (title) {
    slide.addText(title, {
      x: 0.6,
      y: 0.25,
      w: 9,
      h: 0.55,
      fontSize: 26,
      fontFace: FONT.header,
      color: C.navy,
      bold: true,
    });
  }
  return slide;
}

function darkSlide(pres, title) {
  const slide = pres.addSlide();
  slide.background = { fill: C.darkBg };
  if (title) {
    slide.addText(title, {
      x: 0.6,
      y: 0.25,
      w: 9,
      h: 0.55,
      fontSize: 26,
      fontFace: FONT.header,
      color: C.white,
      bold: true,
    });
  }
  return slide;
}

// ─── Slide Builders ──────────────────────────────────────────────────────────

function slide01_title(pres) {
  const slide = pres.addSlide();
  slide.background = { fill: C.darkBg };

  // Accent bar at top
  slide.addShape("rect", {
    x: 0,
    y: 0,
    w: 10,
    h: 0.06,
    fill: { color: C.teal },
  });

  slide.addText("DSCR Lead Intelligence", {
    x: 0.8,
    y: 1.4,
    w: 8.4,
    h: 0.9,
    fontSize: 42,
    fontFace: FONT.header,
    color: C.white,
    bold: true,
  });

  slide.addText("Still Mind Creative", {
    x: 0.8,
    y: 2.3,
    w: 8.4,
    h: 0.55,
    fontSize: 22,
    fontFace: FONT.header,
    color: C.teal,
    bold: false,
  });

  slide.addText("Scored, Enriched Investor Dossiers \u2014 Built From Public Records", {
    x: 0.8,
    y: 3.1,
    w: 8.4,
    h: 0.5,
    fontSize: 16,
    fontFace: FONT.body,
    color: C.bodyLight,
  });

  slide.addText("Prepared for [Loan Officer Name]  \u00B7  March 2026", {
    x: 0.8,
    y: 4.6,
    w: 8.4,
    h: 0.4,
    fontSize: 13,
    fontFace: FONT.body,
    color: C.mutedText,
  });

  // Bottom accent bar
  slide.addShape("rect", {
    x: 0,
    y: 5.57,
    w: 10,
    h: 0.06,
    fill: { color: C.orange },
  });
}

function slide02_problem(pres) {
  const slide = lightSlide(pres, "The Problem With Investor Lead Lists");

  const cards = [
    {
      icon: "\u267B",
      title: "Recycled Data",
      body: "Every LO in your market is buying the same PropStream list. No edge, no differentiation.",
    },
    {
      icon: "\u2753",
      title: "No Scoring",
      body: "500 names with zero intelligence. Who\u2019s actually a DSCR candidate? You\u2019re guessing.",
    },
    {
      icon: "\u260E",
      title: "Wrong Numbers",
      body: "40\u201360% of skip-traced phone numbers are disconnected or wrong person. Wasted dials.",
    },
    {
      icon: "\u26A0",
      title: "Zero Intel",
      body: "Name, address, phone. That\u2019s it. No portfolio data, no equity estimates, no talking points.",
    },
  ];

  const positions = [
    { x: 0.5, y: 1.1 },
    { x: 5.1, y: 1.1 },
    { x: 0.5, y: 3.15 },
    { x: 5.1, y: 3.15 },
  ];

  cards.forEach((c, i) => {
    const px = positions[i].x;
    const py = positions[i].y;
    const cw = 4.4;
    const ch = 1.8;

    addCard(slide, px, py, cw, ch, { accentColor: C.orange });

    slide.addText(c.icon + "  " + c.title, {
      x: px + 0.2,
      y: py + 0.18,
      w: cw - 0.4,
      h: 0.4,
      fontSize: 16,
      fontFace: FONT.header,
      color: C.navy,
      bold: true,
    });

    slide.addText(c.body, {
      x: px + 0.2,
      y: py + 0.65,
      w: cw - 0.4,
      h: 1.0,
      fontSize: 12,
      fontFace: FONT.body,
      color: C.darkText,
      valign: "top",
    });
  });
}

function slide03_whatif(pres) {
  const slide = darkSlide(pres, null);

  slide.addText(
    "What if you only called investors\nwho actually need DSCR financing?",
    {
      x: 1.0,
      y: 1.6,
      w: 8.0,
      h: 1.4,
      fontSize: 28,
      fontFace: FONT.header,
      color: C.white,
      bold: true,
      align: "center",
    }
  );

  slide.addText(
    "And you knew their portfolio size, equity position, lender, rate,\nand exactly what to say?",
    {
      x: 1.5,
      y: 3.3,
      w: 7.0,
      h: 0.9,
      fontSize: 15,
      fontFace: FONT.body,
      color: C.bodyLight,
      align: "center",
    }
  );

  // Decorative teal bar
  slide.addShape("rect", {
    x: 4.2,
    y: 4.5,
    w: 1.6,
    h: 0.04,
    fill: { color: C.teal },
  });
}

function slide04_whatWeBuilt(pres) {
  const slide = lightSlide(pres, "What We Built");

  const steps = [
    { num: "1", title: "Public\nRecords", body: "County property rolls, tax assessor, deeds" },
    { num: "2", title: "ICP\nScoring", body: "12 signals, weighted scoring, tier assignment" },
    { num: "3", title: "Entity\nResolution", body: "LLC \u2192 real person via Secretary of State" },
    { num: "4", title: "Skip Trace\n+ Validate", body: "Verified phone, email, phone type" },
    { num: "5", title: "Investor\nDossier", body: "Full profile with talking points" },
  ];

  const startX = 0.3;
  const gap = 0.12;
  const cw = (10 - startX * 2 - gap * 4) / 5;

  steps.forEach((s, i) => {
    const px = startX + i * (cw + gap);
    const py = 1.2;
    const ch = 2.6;

    addCard(slide, px, py, cw, ch, { accentColor: C.teal });

    // Step number circle
    slide.addShape("ellipse", {
      x: px + cw / 2 - 0.22,
      y: py + 0.2,
      w: 0.44,
      h: 0.44,
      fill: { color: C.teal },
    });
    slide.addText(s.num, {
      x: px + cw / 2 - 0.22,
      y: py + 0.2,
      w: 0.44,
      h: 0.44,
      fontSize: 16,
      fontFace: FONT.header,
      color: C.white,
      bold: true,
      align: "center",
      valign: "middle",
    });

    slide.addText(s.title, {
      x: px + 0.1,
      y: py + 0.75,
      w: cw - 0.2,
      h: 0.6,
      fontSize: 12,
      fontFace: FONT.header,
      color: C.navy,
      bold: true,
      align: "center",
      valign: "middle",
    });

    slide.addText(s.body, {
      x: px + 0.1,
      y: py + 1.4,
      w: cw - 0.2,
      h: 1.0,
      fontSize: 10,
      fontFace: FONT.body,
      color: C.darkText,
      align: "center",
      valign: "top",
    });

    // Arrow connector between cards
    if (i < steps.length - 1) {
      slide.addText("\u25B6", {
        x: px + cw - 0.02,
        y: py + ch / 2 - 0.2,
        w: gap + 0.04,
        h: 0.4,
        fontSize: 14,
        fontFace: FONT.body,
        color: C.teal,
        align: "center",
        valign: "middle",
      });
    }
  });

  slide.addText(
    "Data from 6+ public sources. No purchased lists. No recycled leads.",
    {
      x: 1.0,
      y: 4.2,
      w: 8.0,
      h: 0.4,
      fontSize: 13,
      fontFace: FONT.body,
      color: C.mutedText,
      align: "center",
      italic: true,
    }
  );
}

function slide05_dossier1(pres) {
  const slide = lightSlide(pres, "Sample Investor Dossier");

  // Main dossier card
  addCard(slide, 0.5, 1.1, 9.0, 4.1, { accentColor: C.navy });

  // Header row inside card
  slide.addShape("rect", {
    x: 0.56,
    y: 1.1,
    w: 8.88,
    h: 0.65,
    fill: { color: C.navy },
    rectRadius: 0.06,
  });

  slide.addText("Apex Property Group Inc", {
    x: 0.75,
    y: 1.12,
    w: 5.0,
    h: 0.65,
    fontSize: 18,
    fontFace: FONT.header,
    color: C.white,
    bold: true,
    valign: "middle",
  });

  // Score badge
  slide.addShape("rect", {
    x: 7.2,
    y: 1.2,
    w: 1.0,
    h: 0.45,
    fill: { color: C.teal },
    rectRadius: 0.06,
  });
  slide.addText("70 / 100", {
    x: 7.2,
    y: 1.2,
    w: 1.0,
    h: 0.45,
    fontSize: 14,
    fontFace: FONT.header,
    color: C.white,
    bold: true,
    align: "center",
    valign: "middle",
  });

  // Tier badge
  slide.addShape("rect", {
    x: 8.35,
    y: 1.2,
    w: 0.85,
    h: 0.45,
    fill: { color: C.orange },
    rectRadius: 0.06,
  });
  slide.addText("Tier 1", {
    x: 8.35,
    y: 1.2,
    w: 0.85,
    h: 0.45,
    fontSize: 12,
    fontFace: FONT.header,
    color: C.white,
    bold: true,
    align: "center",
    valign: "middle",
  });

  // Contact section
  slide.addText("\u2588 Contact Information", {
    x: 0.75,
    y: 1.95,
    w: 4.0,
    h: 0.35,
    fontSize: 12,
    fontFace: FONT.header,
    color: C.teal,
    bold: true,
  });

  const contactLines = [
    "Decision Maker:   James R. Whitfield",
    "Phone (Mobile):   (919) 555-0142  \u2713 Verified",
    "Email:            j.whitfield@apexpropgroup.com  \u2713 Valid",
    "Entity Status:    Active LLC \u2014 NC Secretary of State",
  ];
  slide.addText(contactLines.join("\n"), {
    x: 0.75,
    y: 2.3,
    w: 4.2,
    h: 1.2,
    fontSize: 10.5,
    fontFace: FONT.body,
    color: C.darkText,
    lineSpacing: 18,
    valign: "top",
  });

  // Portfolio section
  slide.addText("\u2588 Portfolio Summary", {
    x: 5.2,
    y: 1.95,
    w: 4.0,
    h: 0.35,
    fontSize: 12,
    fontFace: FONT.header,
    color: C.teal,
    bold: true,
  });

  const portfolioLines = [
    "Properties:       26 investment properties",
    "Total Value:      $4,200,000",
    "Total Equity:     $3,100,000 (74%)",
    "Avg Hold Period:  3.2 years",
  ];
  slide.addText(portfolioLines.join("\n"), {
    x: 5.2,
    y: 2.3,
    w: 4.2,
    h: 1.0,
    fontSize: 10.5,
    fontFace: FONT.body,
    color: C.darkText,
    lineSpacing: 18,
    valign: "top",
  });

  // Financing section
  slide.addText("\u2588 Financing Intelligence", {
    x: 0.75,
    y: 3.55,
    w: 4.0,
    h: 0.35,
    fontSize: 12,
    fontFace: FONT.header,
    color: C.orange,
    bold: true,
  });

  const financeLines = [
    "Current Lender:    Hard money (private)",
    "Current Rate:      12.0%",
    "Maturity:          8 months",
    "Refi Priority:     \u2B06 HIGH",
  ];
  slide.addText(financeLines.join("\n"), {
    x: 0.75,
    y: 3.9,
    w: 4.2,
    h: 1.1,
    fontSize: 10.5,
    fontFace: FONT.body,
    color: C.darkText,
    lineSpacing: 18,
    valign: "top",
  });

  // Refi signal callout
  slide.addShape("rect", {
    x: 5.2,
    y: 3.55,
    w: 4.1,
    h: 1.45,
    fill: { color: C.orangeLight },
    rectRadius: 0.06,
  });
  slide.addText("\u26A1 HIGH REFI PRIORITY", {
    x: 5.4,
    y: 3.6,
    w: 3.7,
    h: 0.35,
    fontSize: 12,
    fontFace: FONT.header,
    color: C.orange,
    bold: true,
  });
  slide.addText(
    "Hard money at 12% with 8-month maturity. DSCR refi at 7.5% saves significant monthly cash flow across 26 properties. Balloon approaching \u2014 time-sensitive opportunity.",
    {
      x: 5.4,
      y: 3.95,
      w: 3.7,
      h: 1.0,
      fontSize: 10,
      fontFace: FONT.body,
      color: C.darkText,
      valign: "top",
    }
  );
}

function slide06_dossier2(pres) {
  const slide = lightSlide(pres, "Per-Property Detail + Talking Points");

  // Property table
  const tableHeader = [
    { text: "Address", options: { bold: true, color: C.white, fill: { color: C.navy }, fontSize: 9, fontFace: FONT.header } },
    { text: "Value", options: { bold: true, color: C.white, fill: { color: C.navy }, fontSize: 9, fontFace: FONT.header } },
    { text: "Lender", options: { bold: true, color: C.white, fill: { color: C.navy }, fontSize: 9, fontFace: FONT.header } },
    { text: "Rate", options: { bold: true, color: C.white, fill: { color: C.navy }, fontSize: 9, fontFace: FONT.header } },
    { text: "Maturity", options: { bold: true, color: C.white, fill: { color: C.navy }, fontSize: 9, fontFace: FONT.header } },
    { text: "Equity", options: { bold: true, color: C.white, fill: { color: C.navy }, fontSize: 9, fontFace: FONT.header } },
  ];

  const rowStyle = { fontSize: 9, fontFace: FONT.body, color: C.darkText };
  const altFill = { fill: { color: "EEF0F2" } };
  const rows = [
    ["412 Oak Ridge Dr, Raleigh", "$185,000", "Hard Money LLC", "12.0%", "8 mo", "$142,000"],
    ["8901 Sunset Blvd, Cary", "$210,000", "Hard Money LLC", "12.0%", "8 mo", "$158,000"],
    ["1533 Pine Valley Ln, Durham", "$165,000", "Wells Fargo", "6.5%", "28 yr", "$95,000"],
    ["207 Maple Creek Ct, Apex", "$195,000", "Hard Money LLC", "11.5%", "10 mo", "$150,000"],
    ["6644 Elm St, Raleigh", "$140,000", "Cash Purchase", "\u2014", "\u2014", "$140,000"],
    ["903 Birch Hill Rd, Garner", "$175,000", "Private Lender", "13.0%", "6 mo", "$110,000"],
    ["2210 Cedar Park Way, Cary", "$225,000", "Hard Money LLC", "12.0%", "8 mo", "$170,000"],
    ["5518 Willow Springs, Holly Spgs", "$155,000", "Cash Purchase", "\u2014", "\u2014", "$155,000"],
  ];

  const tableRows = [tableHeader];
  rows.forEach((r, i) => {
    const cells = r.map((text) => {
      const opts = { ...rowStyle };
      if (i % 2 === 1) opts.fill = { color: "EEF0F2" };
      return { text, options: opts };
    });
    tableRows.push(cells);
  });

  slide.addTable(tableRows, {
    x: 0.4,
    y: 1.05,
    w: 9.2,
    colW: [2.2, 0.95, 1.5, 0.75, 0.85, 0.95],
    border: { pt: 0.5, color: "D0D0D0" },
    rowH: 0.28,
  });

  // Talking points card
  addCard(slide, 0.4, 3.7, 9.2, 1.7, { accentColor: C.teal });

  slide.addText("\u2588 Talking Points", {
    x: 0.65,
    y: 3.8,
    w: 4.0,
    h: 0.3,
    fontSize: 13,
    fontFace: FONT.header,
    color: C.teal,
    bold: true,
  });

  const talkingPoints = [
    {
      text: "\u2022  Your hard money loans at 12% are costing thousands per month \u2014 a DSCR refi at 7.5% saves significant cash flow across your portfolio",
    },
    {
      text: "\u2022  8 months until maturity on your primary loans \u2014 let\u2019s get ahead of the balloon",
    },
    {
      text: "\u2022  With $3.1M in equity, you\u2019re well-positioned for a cash-out refi to fund your next acquisition",
    },
  ];

  slide.addText(talkingPoints, {
    x: 0.65,
    y: 4.15,
    w: 8.7,
    h: 1.15,
    fontSize: 11,
    fontFace: FONT.body,
    color: C.darkText,
    lineSpacing: 17,
    valign: "top",
  });
}

function slide07_byTheNumbers(pres) {
  const slide = darkSlide(pres, "By The Numbers");

  const stats = [
    { num: "684,895", label: "Properties Analyzed" },
    { num: "65,942", label: "Tier 1 Investor Leads" },
    { num: "12", label: "Scoring Signals" },
    { num: "157", label: "Data Fields Per Lead" },
  ];

  const cw = 2.0;
  const gap = 0.27;
  const totalW = cw * 4 + gap * 3;
  const startX = (10 - totalW) / 2;

  stats.forEach((s, i) => {
    const px = startX + i * (cw + gap);
    const py = 1.6;
    const ch = 2.4;

    addDarkCard(slide, px, py, cw, ch, { accentColor: C.teal });

    slide.addText(s.num, {
      x: px,
      y: py + 0.35,
      w: cw,
      h: 0.8,
      fontSize: 32,
      fontFace: FONT.header,
      color: C.teal,
      bold: true,
      align: "center",
      valign: "middle",
    });

    slide.addText(s.label, {
      x: px + 0.15,
      y: py + 1.3,
      w: cw - 0.3,
      h: 0.7,
      fontSize: 13,
      fontFace: FONT.body,
      color: C.bodyLight,
      align: "center",
      valign: "top",
    });
  });
}

function slide08_howWeScore(pres) {
  const slide = lightSlide(pres, "How We Score Investors");

  const signals = [
    { icon: "\uD83C\uDFE0", title: "Portfolio 5+", pts: "+20 pts", body: "Owns 5+ investment properties in your market" },
    { icon: "\u2708", title: "Out-of-State", pts: "+15 pts", body: "Mailing address outside the state = confirmed investor" },
    { icon: "\uD83D\uDCB5", title: "Cash Buyer", pts: "+15 pts", body: "No recorded mortgage = prime cash-out refi candidate" },
    { icon: "\uD83C\uDFE2", title: "LLC / Entity", pts: "+10 pts", body: "Structured as LLC/Corp/Trust = sophisticated investor" },
    { icon: "\uD83C\uDFAF", title: "Value Sweet Spot", pts: "+10 pts", body: "$150K\u2013$500K = highest-volume DSCR loan range" },
    { icon: "\uD83D\uDD11", title: "Recent Purchase", pts: "+10 pts", body: "Bought within 12 months = active acquirer" },
  ];

  const cols = 3;
  const cw = 2.8;
  const ch = 1.55;
  const gapX = 0.2;
  const gapY = 0.2;
  const totalW = cw * cols + gapX * (cols - 1);
  const startX = (10 - totalW) / 2;

  signals.forEach((s, i) => {
    const col = i % cols;
    const row = Math.floor(i / cols);
    const px = startX + col * (cw + gapX);
    const py = 1.15 + row * (ch + gapY);

    addCard(slide, px, py, cw, ch, { accentColor: C.navy });

    slide.addText(s.icon + "  " + s.title, {
      x: px + 0.18,
      y: py + 0.12,
      w: cw - 0.35,
      h: 0.35,
      fontSize: 13,
      fontFace: FONT.header,
      color: C.navy,
      bold: true,
    });

    // Points badge
    slide.addShape("rect", {
      x: px + cw - 0.9,
      y: py + 0.14,
      w: 0.7,
      h: 0.28,
      fill: { color: C.tealLight },
      rectRadius: 0.04,
    });
    slide.addText(s.pts, {
      x: px + cw - 0.9,
      y: py + 0.14,
      w: 0.7,
      h: 0.28,
      fontSize: 9,
      fontFace: FONT.header,
      color: C.teal,
      bold: true,
      align: "center",
      valign: "middle",
    });

    slide.addText(s.body, {
      x: px + 0.18,
      y: py + 0.55,
      w: cw - 0.35,
      h: 0.85,
      fontSize: 10.5,
      fontFace: FONT.body,
      color: C.darkText,
      valign: "top",
    });
  });
}

function slide09_program1(pres) {
  const slide = lightSlide(pres, "Program 1: Deal Intelligence");

  slide.addText("You make the calls. We give you the intel.", {
    x: 0.6,
    y: 0.72,
    w: 8.0,
    h: 0.35,
    fontSize: 14,
    fontFace: FONT.body,
    color: C.mutedText,
    italic: true,
  });

  // Bullets card
  addCard(slide, 0.5, 1.2, 5.2, 2.8, { accentColor: C.teal });

  slide.addText("\u2588 What\u2019s Included", {
    x: 0.75,
    y: 1.3,
    w: 4.5,
    h: 0.3,
    fontSize: 12,
    fontFace: FONT.header,
    color: C.teal,
    bold: true,
  });

  const bullets = [
    "Scored investor leads matched to your market",
    "Verified phone + email for every lead",
    "Full portfolio analysis (property count, value, equity)",
    "Financing intel (lender, rate, maturity, refi signals)",
    "Entity resolution (LLC \u2192 real decision maker)",
    "Personalized talking points per investor",
    "Monthly refresh with new leads + updated data",
  ];

  slide.addText(
    bullets.map((b) => ({ text: "\u2022  " + b + "\n" })),
    {
      x: 0.75,
      y: 1.65,
      w: 4.75,
      h: 2.2,
      fontSize: 10.5,
      fontFace: FONT.body,
      color: C.darkText,
      lineSpacing: 16,
      valign: "top",
    }
  );

  // Pricing table
  addCard(slide, 5.9, 1.2, 3.7, 2.8, { accentColor: C.orange });

  slide.addText("\u2588 Pricing", {
    x: 6.15,
    y: 1.3,
    w: 3.2,
    h: 0.3,
    fontSize: 12,
    fontFace: FONT.header,
    color: C.orange,
    bold: true,
  });

  const pricingHeader = [
    { text: "Tier", options: { bold: true, color: C.white, fill: { color: C.navy }, fontSize: 9, fontFace: FONT.header } },
    { text: "Price", options: { bold: true, color: C.white, fill: { color: C.navy }, fontSize: 9, fontFace: FONT.header } },
    { text: "Leads/Mo", options: { bold: true, color: C.white, fill: { color: C.navy }, fontSize: 9, fontFace: FONT.header } },
  ];

  const pricingRows = [
    pricingHeader,
    [
      { text: "Starter", options: { fontSize: 9, fontFace: FONT.body, bold: true } },
      { text: "$1,500/mo", options: { fontSize: 9, fontFace: FONT.body } },
      { text: "250 \u2022 2 counties", options: { fontSize: 9, fontFace: FONT.body } },
    ],
    [
      { text: "Pro", options: { fontSize: 9, fontFace: FONT.body, bold: true, fill: { color: "EEF0F2" } } },
      { text: "$3,000/mo", options: { fontSize: 9, fontFace: FONT.body, fill: { color: "EEF0F2" } } },
      { text: "750 \u2022 5 counties", options: { fontSize: 9, fontFace: FONT.body, fill: { color: "EEF0F2" } } },
    ],
    [
      { text: "Enterprise", options: { fontSize: 9, fontFace: FONT.body, bold: true } },
      { text: "$5,000/mo", options: { fontSize: 9, fontFace: FONT.body } },
      { text: "Full state \u2022 Weekly", options: { fontSize: 9, fontFace: FONT.body } },
    ],
  ];

  slide.addTable(pricingRows, {
    x: 6.1,
    y: 1.7,
    w: 3.3,
    colW: [0.95, 1.05, 1.3],
    border: { pt: 0.5, color: "D0D0D0" },
    rowH: 0.3,
  });

  // Refresh note
  slide.addText("Starter: monthly refresh  |  Pro: bi-weekly  |  Enterprise: weekly", {
    x: 6.1,
    y: 3.0,
    w: 3.3,
    h: 0.3,
    fontSize: 8,
    fontFace: FONT.body,
    color: C.mutedText,
    align: "center",
  });
}

function slide10_program2(pres) {
  const slide = lightSlide(pres, "Program 2: Done-For-You Outbound");

  slide.addText("We run the campaigns. You take the meetings.", {
    x: 0.6,
    y: 0.72,
    w: 8.0,
    h: 0.35,
    fontSize: 14,
    fontFace: FONT.body,
    color: C.mutedText,
    italic: true,
  });

  // Bullets card
  addCard(slide, 0.5, 1.2, 5.2, 2.8, { accentColor: C.teal });

  slide.addText("\u2588 What\u2019s Included", {
    x: 0.75,
    y: 1.3,
    w: 4.5,
    h: 0.3,
    fontSize: 12,
    fontFace: FONT.header,
    color: C.teal,
    bold: true,
  });

  const bullets = [
    "Everything in Deal Intelligence, plus:",
    "Multi-channel outreach (email + direct mail + LinkedIn)",
    "Custom email sequences written for DSCR",
    "Campaign management and A/B testing",
    "Lead nurturing and follow-up automation",
    "Weekly reporting on opens, replies, meetings booked",
    "Dedicated campaign manager",
  ];

  slide.addText(
    bullets.map((b) => ({ text: "\u2022  " + b + "\n" })),
    {
      x: 0.75,
      y: 1.65,
      w: 4.75,
      h: 2.2,
      fontSize: 10.5,
      fontFace: FONT.body,
      color: C.darkText,
      lineSpacing: 16,
      valign: "top",
    }
  );

  // Pricing table
  addCard(slide, 5.9, 1.2, 3.7, 2.8, { accentColor: C.orange });

  slide.addText("\u2588 Pricing", {
    x: 6.15,
    y: 1.3,
    w: 3.2,
    h: 0.3,
    fontSize: 12,
    fontFace: FONT.header,
    color: C.orange,
    bold: true,
  });

  const pricingHeader = [
    { text: "Tier", options: { bold: true, color: C.white, fill: { color: C.navy }, fontSize: 9, fontFace: FONT.header } },
    { text: "Price", options: { bold: true, color: C.white, fill: { color: C.navy }, fontSize: 9, fontFace: FONT.header } },
    { text: "Scope", options: { bold: true, color: C.white, fill: { color: C.navy }, fontSize: 9, fontFace: FONT.header } },
  ];

  const pricingRows = [
    pricingHeader,
    [
      { text: "Launch", options: { fontSize: 9, fontFace: FONT.body, bold: true } },
      { text: "$3,500/mo", options: { fontSize: 9, fontFace: FONT.body } },
      { text: "500 leads + email + DM", options: { fontSize: 9, fontFace: FONT.body } },
    ],
    [
      { text: "Growth", options: { fontSize: 9, fontFace: FONT.body, bold: true, fill: { color: "EEF0F2" } } },
      { text: "$5,000/mo", options: { fontSize: 9, fontFace: FONT.body, fill: { color: "EEF0F2" } } },
      { text: "1K leads + email + DM + LI", options: { fontSize: 9, fontFace: FONT.body, fill: { color: "EEF0F2" } } },
    ],
    [
      { text: "Scale", options: { fontSize: 9, fontFace: FONT.body, bold: true } },
      { text: "$7,500/mo", options: { fontSize: 9, fontFace: FONT.body } },
      { text: "2K+ leads + full multi-ch", options: { fontSize: 9, fontFace: FONT.body } },
    ],
  ];

  slide.addTable(pricingRows, {
    x: 6.1,
    y: 1.7,
    w: 3.3,
    colW: [0.85, 1.05, 1.4],
    border: { pt: 0.5, color: "D0D0D0" },
    rowH: 0.3,
  });
}

function slide11_theMath(pres) {
  const slide = darkSlide(pres, "The Math");

  const stats = [
    { label: "Avg DSCR Commission", value: "$6,000", sub: "1\u20132.5% on $300K\u2013$500K" },
    { label: "Pilot Cost", value: "$500", sub: "100 Tier 1 dossiers" },
    { label: "Deals to Break Even\non Pilot", value: "1", sub: "" },
    { label: "Starter Monthly Cost", value: "$1,500", sub: "250 leads/mo" },
    { label: "Deals to Break Even\non Starter", value: "1", sub: "" },
    { label: "Repeat Investor LTV", value: "$30,000+", sub: "5+ loans over time" },
  ];

  const cols = 3;
  const cw = 2.65;
  const ch = 1.5;
  const gapX = 0.2;
  const gapY = 0.2;
  const totalW = cw * cols + gapX * (cols - 1);
  const startX = (10 - totalW) / 2;

  stats.forEach((s, i) => {
    const col = i % cols;
    const row = Math.floor(i / cols);
    const px = startX + col * (cw + gapX);
    const py = 1.15 + row * (ch + gapY);

    addDarkCard(slide, px, py, cw, ch, { accentColor: i < 3 ? C.teal : C.orange });

    slide.addText(s.value, {
      x: px + 0.15,
      y: py + 0.15,
      w: cw - 0.3,
      h: 0.6,
      fontSize: 28,
      fontFace: FONT.header,
      color: i < 3 ? C.teal : C.orange,
      bold: true,
      align: "center",
      valign: "middle",
    });

    slide.addText(s.label, {
      x: px + 0.15,
      y: py + 0.75,
      w: cw - 0.3,
      h: 0.45,
      fontSize: 11,
      fontFace: FONT.body,
      color: C.bodyLight,
      align: "center",
      valign: "top",
    });

    if (s.sub) {
      slide.addText(s.sub, {
        x: px + 0.15,
        y: py + 1.15,
        w: cw - 0.3,
        h: 0.25,
        fontSize: 9,
        fontFace: FONT.body,
        color: C.mutedText,
        align: "center",
        valign: "top",
      });
    }
  });

  slide.addText(
    "One funded deal pays for the pilot 12x over. One repeat investor relationship covers a full year of Pro.",
    {
      x: 1.0,
      y: 4.3,
      w: 8.0,
      h: 0.5,
      fontSize: 13,
      fontFace: FONT.body,
      color: C.bodyLight,
      align: "center",
      italic: true,
    }
  );
}

function slide12_competition(pres) {
  const slide = lightSlide(pres, "vs. What You Use Now");

  const hdrOpts = { bold: true, color: C.white, fill: { color: C.navy }, fontSize: 8.5, fontFace: FONT.header, align: "center" };
  const cellOpts = { fontSize: 8.5, fontFace: FONT.body, color: C.darkText, align: "center" };
  const altOpts = { ...cellOpts, fill: { color: "EEF0F2" } };
  const usCell = { ...cellOpts, bold: true, color: C.teal };
  const usAlt = { ...usCell, fill: { color: "EEF0F2" } };
  const featOpts = { fontSize: 8.5, fontFace: FONT.body, color: C.darkText, bold: true, align: "left" };
  const featAlt = { ...featOpts, fill: { color: "EEF0F2" } };

  const G = "\u2713";
  const X = "\u2717";

  const header = [
    { text: "Feature", options: { ...hdrOpts, align: "left" } },
    { text: "Us", options: hdrOpts },
    { text: "PropStream", options: hdrOpts },
    { text: "Zillow", options: hdrOpts },
    { text: "Lead Gen\nAgency", options: hdrOpts },
    { text: "DIY\nCold Call", options: hdrOpts },
  ];

  const data = [
    ["Investor scoring", "12 signals", "Basic filters", X, "Varies", X],
    ["Entity resolution", G + " SoS", X, X, "Rarely", X],
    ["Per-property mortgage", G, "Partial", X, X, X],
    ["Verified contact", "Phone+email", "Email only", X, "Varies", "Skip trace"],
    ["Talking points", G + " AI-gen", X, X, "Generic", X],
    ["Exclusivity", G + " Market", X, X, "Varies", G],
    ["Cost", "$1,500/mo", "$99/mo", "Free", "$3K\u201310K", "Your time"],
    ["Intelligence depth", "157 fields", "~20 fields", "~5 fields", "~30 fields", "~5 fields"],
  ];

  const rows = [header];
  data.forEach((r, ri) => {
    const isAlt = ri % 2 === 1;
    const row = r.map((text, ci) => {
      let opts;
      if (ci === 0) opts = isAlt ? featAlt : featOpts;
      else if (ci === 1) opts = isAlt ? usAlt : usCell;
      else opts = isAlt ? altOpts : cellOpts;

      // Color checkmarks and X marks
      if (text === G) return { text, options: { ...opts, color: C.greenCheck, fontSize: 12 } };
      if (text === X) return { text, options: { ...opts, color: C.redX, fontSize: 12 } };
      if (typeof text === "string" && text.startsWith(G)) return { text, options: { ...opts, color: C.greenCheck } };
      return { text, options: opts };
    });
    rows.push(row);
  });

  slide.addTable(rows, {
    x: 0.3,
    y: 1.05,
    w: 9.4,
    colW: [1.55, 1.15, 1.15, 1.0, 1.15, 1.0],
    border: { pt: 0.5, color: "D0D0D0" },
    rowH: 0.38,
  });
}

function slide13_howItWorks(pres) {
  const slide = lightSlide(pres, "How It Works");

  const steps = [
    { num: "1", title: "Kickoff Call", body: "30-min call to define your target market, counties, and ideal investor profile" },
    { num: "2", title: "Market Analysis", body: "We pull every property record in your market and score against 12 investor signals" },
    { num: "3", title: "Enrichment", body: "Entity resolution, skip trace, phone/email validation, mortgage data, wealth signals" },
    { num: "4", title: "Delivery", body: "Fully enriched dossiers delivered via Google Sheets with walkthrough call" },
    { num: "5", title: "Monthly Refresh", body: "New leads added, existing data updated, stale contacts removed" },
  ];

  const cardW = 8.4;
  const cardH = 0.65;
  const gap = 0.12;
  const startX = 0.8;
  const startY = 1.15;

  steps.forEach((s, i) => {
    const py = startY + i * (cardH + gap);

    addCard(slide, startX, py, cardW, cardH, { accentColor: C.teal });

    // Step number circle
    slide.addShape("ellipse", {
      x: startX + 0.2,
      y: py + 0.1,
      w: 0.44,
      h: 0.44,
      fill: { color: C.navy },
    });
    slide.addText(s.num, {
      x: startX + 0.2,
      y: py + 0.1,
      w: 0.44,
      h: 0.44,
      fontSize: 15,
      fontFace: FONT.header,
      color: C.white,
      bold: true,
      align: "center",
      valign: "middle",
    });

    slide.addText(s.title, {
      x: startX + 0.8,
      y: py + 0.02,
      w: 2.0,
      h: cardH - 0.04,
      fontSize: 13,
      fontFace: FONT.header,
      color: C.navy,
      bold: true,
      valign: "middle",
    });

    slide.addText(s.body, {
      x: startX + 2.8,
      y: py + 0.02,
      w: 5.2,
      h: cardH - 0.04,
      fontSize: 11,
      fontFace: FONT.body,
      color: C.darkText,
      valign: "middle",
    });
  });
}

function slide14_pilot(pres) {
  const slide = pres.addSlide();
  slide.background = { fill: C.darkBg };

  // Teal top accent
  slide.addShape("rect", {
    x: 0,
    y: 0,
    w: 10,
    h: 0.06,
    fill: { color: C.teal },
  });

  slide.addText("Start Here: $500 Pilot", {
    x: 0.6,
    y: 0.3,
    w: 9,
    h: 0.55,
    fontSize: 26,
    fontFace: FONT.header,
    color: C.white,
    bold: true,
  });

  // Big centered card
  const cx = 1.2;
  const cy = 1.15;
  const cw = 7.6;
  const ch = 3.5;

  addDarkCard(slide, cx, cy, cw, ch, { accentColor: C.teal });

  slide.addText("100 Tier 1 Investor Dossiers", {
    x: cx + 0.4,
    y: cy + 0.2,
    w: cw - 0.8,
    h: 0.5,
    fontSize: 22,
    fontFace: FONT.header,
    color: C.teal,
    bold: true,
    align: "center",
  });

  const items = [
    "One county of your choice",
    "Fully enriched: phone, email, portfolio, financing, talking points",
    "30-minute walkthrough call included",
    "Delivered in 5 business days",
    "Zero risk: if fewer than 80% of contacts are valid, we re-run at no charge",
  ];

  slide.addText(
    items.map((t) => ({ text: "\u2713  " + t + "\n" })),
    {
      x: cx + 1.0,
      y: cy + 0.85,
      w: cw - 2.0,
      h: 2.2,
      fontSize: 13,
      fontFace: FONT.body,
      color: C.bodyLight,
      lineSpacing: 22,
      valign: "top",
    }
  );

  slide.addText("One closed deal from this list = 12x ROI", {
    x: 1.0,
    y: 4.85,
    w: 8.0,
    h: 0.4,
    fontSize: 16,
    fontFace: FONT.header,
    color: C.orange,
    bold: true,
    align: "center",
  });
}

function slide15_faq(pres) {
  const slide = lightSlide(pres, "Common Questions");

  const faqs = [
    { q: "Is the data exclusive?", a: "Yes. We limit to 3 clients per county to prevent overlap." },
    { q: "How fresh is the data?", a: "Property records update quarterly. Contact data is validated at delivery." },
    { q: "What if leads don\u2019t convert?", a: "Our pilot guarantee: 80%+ valid contacts or we re-run free." },
    { q: "How is this different from PropStream?", a: "PropStream gives you a search tool. We give you scored, enriched dossiers with talking points \u2014 ready to call." },
    { q: "Can I choose specific zip codes?", a: "Yes. Pilot and Starter let you target specific zips within your counties." },
    { q: "What\u2019s the contract?", a: "Pilot is one-time. Subscriptions are month-to-month, cancel anytime." },
  ];

  const cols = 2;
  const cw = 4.3;
  const ch = 1.15;
  const gapX = 0.3;
  const gapY = 0.15;
  const totalW = cw * cols + gapX;
  const startX = (10 - totalW) / 2;

  faqs.forEach((f, i) => {
    const col = i % cols;
    const row = Math.floor(i / cols);
    const px = startX + col * (cw + gapX);
    const py = 1.1 + row * (ch + gapY);

    addCard(slide, px, py, cw, ch, { accentColor: C.navy });

    slide.addText(f.q, {
      x: px + 0.2,
      y: py + 0.1,
      w: cw - 0.35,
      h: 0.32,
      fontSize: 11,
      fontFace: FONT.header,
      color: C.navy,
      bold: true,
    });

    slide.addText(f.a, {
      x: px + 0.2,
      y: py + 0.45,
      w: cw - 0.35,
      h: 0.6,
      fontSize: 10,
      fontFace: FONT.body,
      color: C.darkText,
      valign: "top",
    });
  });
}

function slide16_about(pres) {
  const slide = darkSlide(pres, "About Still Mind Creative");

  // Bio card - left
  addDarkCard(slide, 0.5, 1.15, 4.3, 3.5, { accentColor: C.teal });

  slide.addText("Zack Lewis", {
    x: 0.75,
    y: 1.3,
    w: 3.8,
    h: 0.45,
    fontSize: 20,
    fontFace: FONT.header,
    color: C.white,
    bold: true,
  });

  slide.addText("Founder", {
    x: 0.75,
    y: 1.72,
    w: 3.8,
    h: 0.3,
    fontSize: 12,
    fontFace: FONT.body,
    color: C.teal,
  });

  const bioLines = [
    "Former marketing lead for the largest mortgage team in the United States.",
    "",
    "Built this system after seeing LOs waste thousands on garbage lead lists.",
    "",
    "Every lead in our system comes from public records, scored by real signals, and enriched with verified contact data.",
  ];

  slide.addText(bioLines.join("\n"), {
    x: 0.75,
    y: 2.15,
    w: 3.8,
    h: 2.3,
    fontSize: 11,
    fontFace: FONT.body,
    color: C.bodyLight,
    lineSpacing: 16,
    valign: "top",
  });

  // Contact card - right
  addDarkCard(slide, 5.2, 1.15, 4.3, 3.5, { accentColor: C.orange });

  slide.addText("Still Mind Creative, LLC", {
    x: 5.45,
    y: 1.3,
    w: 3.8,
    h: 0.45,
    fontSize: 18,
    fontFace: FONT.header,
    color: C.white,
    bold: true,
  });

  const contactItems = [
    "\u2709  zack@stillmindcreative.com",
    "\u260E  [phone]",
    "\uD83C\uDF10  stillmindcreative.com",
  ];

  slide.addText(contactItems.join("\n\n"), {
    x: 5.45,
    y: 2.1,
    w: 3.8,
    h: 2.0,
    fontSize: 13,
    fontFace: FONT.body,
    color: C.bodyLight,
    lineSpacing: 22,
    valign: "top",
  });

  // Bottom accent bar
  slide.addShape("rect", {
    x: 0,
    y: 5.57,
    w: 10,
    h: 0.06,
    fill: { color: C.teal },
  });
}

// ─── Main ────────────────────────────────────────────────────────────────────

async function main() {
  const pres = new pptxgen();
  pres.layout = "LAYOUT_16x9";
  pres.author = "Still Mind Creative";
  pres.title = "DSCR Lead Intelligence";
  pres.subject = "Pitchbook";

  slide01_title(pres);
  slide02_problem(pres);
  slide03_whatif(pres);
  slide04_whatWeBuilt(pres);
  slide05_dossier1(pres);
  slide06_dossier2(pres);
  slide07_byTheNumbers(pres);
  slide08_howWeScore(pres);
  slide09_program1(pres);
  slide10_program2(pres);
  slide11_theMath(pres);
  slide12_competition(pres);
  slide13_howItWorks(pres);
  slide14_pilot(pres);
  slide15_faq(pres);
  slide16_about(pres);

  const outPath = path.join(__dirname, "dscr_pitchbook.pptx");
  await pres.writeFile({ fileName: outPath });
  console.log("Pitchbook saved to: " + outPath);
}

main().catch((err) => {
  console.error("Build failed:", err);
  process.exit(1);
});
