// =============================================================================
//  consult_helpers.js
//  Reusable primitives for the "AWS Consulting Report - Light / High-Density" style.
//  Used with pptxgenjs. Import makeHelpers(pres, opts) and compose slides.
// =============================================================================

const TOKENS = {
  FONT: "NanumSquareOTF Bold",   // body + titles (everything)
  CODE_FONT: "D2Coding",         // code blocks only (SPARQL/JSON/snippets)
  color: {
    white:  "FFFFFF",
    navy:   "2C3C5A",  // FIXED AWS chrome: cover/divider/closing bg, table header rows
    navyDk: "23303F",
    ink:    "0E0E0E",  // headings
    body:   "333333",  // body text
    muted:  "7B7B7B",  // captions / meta
    panel:  "F2F2F2",  // zebra / subtle fill
    border: "D9DCE1",  // card hairline
    slideBg:         "E9ECF2",  // content-slide background (light gray, behind the container)
    container:       "FFFFFF",  // outer rounded container fill (wraps the column cards)
    containerBorder: "D7DBE3",  // outer container hairline
    pos:    "00B050",  // positive delta  (SEMANTIC, fixed - never the brand accent)
    neg:    "D92D20",  // negative delta  (SEMANTIC, fixed - never the brand accent)
    // rank-chip palette; index 1 is replaced with the brand accent at runtime
    chipBase: ["232F3E", "FB0050", "2074D5", "00B050", "FF9900"],
  },
  // Content layout: light-gray slide + an outer rounded container (CX,CY,CW,CH) that wraps
  // the title, summary band and the two column cards. IX/IW = inner content box (padded).
  geo: { CX: 0.10, CY: 0.18, CW: 9.80, CH: 5.02, RAD: 0.07, IX: 0.26, IW: 9.48, GAP: 0.10,
         TITLE_Y: 0.32, SUM_Y: 0.84, SUM_H: 0.74, BODY_Y: 1.68, BODY_H: 3.36, HDR_H: 0.30 },
};

// Derive the full accent set from a single brand color (output of extract_brand_color.py).
function deriveBrand(accentHex) {
  const h = String(accentHex || "FB0050").replace(/^#/, "");
  const r = parseInt(h.slice(0, 2), 16), g = parseInt(h.slice(2, 4), 16), b = parseInt(h.slice(4, 6), 16);
  const hx = (R, G, B) => { const c = n => Math.max(0, Math.min(255, Math.round(n))).toString(16).padStart(2, "0").toUpperCase(); return c(R) + c(G) + c(B); };
  const lum = (R, G, B) => { const f = v => { v /= 255; return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); }; return 0.2126 * f(R) + 0.7152 * f(G) + 0.0722 * f(B); };
  return {
    accent:     hx(r, g, b),
    accentDark: hx(r * 0.72, g * 0.72, b * 0.72),
    accentTint: hx(r * 0.10 + 255 * 0.90, g * 0.10 + 255 * 0.90, b * 0.10 + 255 * 0.90),
    onAccent:   lum(r, g, b) > 0.6 ? "0E0E0E" : "FFFFFF",  // white on vivid colors; dark on light ones
  };
}

// Build helpers bound to a pptxgen instance.
//   opts.accent    : brand color hex (default env ACCENT or "FB0050")
//   opts.client    : client name for the brand chip (default "요기요")
//   opts.copyright : footer line
function makeHelpers(pres, opts = {}) {
  const FONT = TOKENS.FONT;
  const brand = deriveBrand(opts.accent || process.env.ACCENT || "FB0050");
  const C = Object.assign({}, TOKENS.color, brand);
  C.chip = TOKENS.color.chipBase.slice(); C.chip[1] = C.accent;   // rank-chip #2 = accent
  const G = TOKENS.geo;
  const { CX, CY, CW, CH, RAD, IX, IW, GAP, TITLE_Y, SUM_Y, SUM_H, BODY_Y, BODY_H, HDR_H } = G;
  const COL_W = (IW - GAP) / 2, COL_L_X = IX, COL_R_X = IX + COL_W + GAP;
  const CLIENT = opts.client || "요기요";
  const LOGO = opts.logo || process.env.LOGO || null;   // optional logo image path
  const COPYRIGHT = opts.copyright || "© 2026, Amazon Web Services, Inc. or its affiliates. All rights reserved. Amazon Confidential and Trademark.";

  const fullBg = (s, color) => { s.background = { color }; };

  // CONTENT-SLIDE FRAME: light-gray background + outer rounded container that wraps everything.
  // Use on content slides instead of fullBg(s, white). Cover/divider/closing keep fullBg(s, navy).
  function contentFrame(s) {
    s.background = { color: C.slideBg };
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
      x: CX, y: CY, w: CW, h: CH, rectRadius: RAD,
      fill: { color: C.container }, line: { color: C.containerBorder, width: 1 },
      shadow: { type: "outer", color: "9AA3B2", blur: 9, offset: 3, angle: 90, opacity: 0.18 },
    });
  }

  // title with short accent bar + top-right chapter tag
  function header(s, title, chNum, chName) {
    s.addShape(pres.shapes.RECTANGLE, { x: IX, y: TITLE_Y + 0.02, w: 0.09, h: 0.42, fill: { color: C.accent }, line: { type: "none" } });
    s.addText(title, { x: IX + 0.18, y: TITLE_Y - 0.02, w: 7.7, h: 0.54, fontFace: FONT, fontSize: 24, bold: true, color: C.ink, valign: "middle", margin: 0 });
    if (chNum) {
      s.addShape(pres.shapes.RECTANGLE, { x: 8.30, y: TITLE_Y + 0.06, w: 0.30, h: 0.30, fill: { color: C.accent }, line: { type: "none" } });
      s.addText(String(chNum), { x: 8.30, y: TITLE_Y + 0.06, w: 0.30, h: 0.30, fontFace: FONT, fontSize: 12, bold: true, color: C.onAccent, align: "center", valign: "middle", margin: 0 });
      s.addText(chName, { x: 8.66, y: TITLE_Y + 0.02, w: 1.04, h: 0.38, fontFace: FONT, fontSize: 8.5, color: C.muted, valign: "middle", margin: 0, lineSpacingMultiple: 1.0 });
    }
  }

  // dense executive-summary band directly under the title (signature element). Autofit shrink.
  function summary(s, text) {
    s.addText(text, { x: IX, y: SUM_Y, w: IW, h: SUM_H, fontFace: FONT, fontSize: 10, bold: true, color: C.body, valign: "top", align: "justify", margin: 0, lineSpacingMultiple: 1.5, fit: "shrink" });
  }

  // white content card + accent header band (label in onAccent). Returns inner content rect.
  // Card + band have TOP corners rounded only (square bottom), radius matches the container.
  function card(s, x, y, w, h, label, bandColor) {
    const R = 0.07;
    s.addShape(pres.ShapeType.round2SameRect, { x, y, w, h, rectRadius: R, fill: { color: C.white }, line: { color: C.border, width: 0.75 } });
    s.addShape(pres.ShapeType.round2SameRect, { x, y, w, h: HDR_H, rectRadius: R, fill: { color: bandColor || C.accent }, line: { type: "none" } });
    s.addText(label, { x: x + 0.14, y, w: w - 0.28, h: HDR_H, fontFace: FONT, fontSize: 10.5, bold: true, color: C.onAccent, valign: "middle", margin: 0, charSpacing: 0.5 });
    return { x: x + 0.16, y: y + HDR_H + 0.08, w: w - 0.32, h: h - HDR_H - 0.16 };
  }

  // charcoal sub-card header band (for nested cards inside a column)
  function subBand(s, x, y, w, label) {
    s.addShape(pres.shapes.RECTANGLE, { x, y, w, h: 0.26, fill: { color: "4A4A4A" }, line: { type: "none" } });
    s.addText(label, { x: x + 0.10, y, w: w - 0.20, h: 0.26, fontFace: FONT, fontSize: 9.5, bold: true, color: C.white, align: "center", valign: "middle", margin: 0 });
  }

  // brand chip (client name) - shared by cover/divider/closing and footer
  function chip(s, x, y, w, h, fs, rad) {
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, rectRadius: rad, fill: { color: C.accent }, line: { type: "none" } });
    s.addText(CLIENT, { x, y, w, h, fontFace: FONT, fontSize: fs, bold: true, color: C.onAccent, align: "center", valign: "middle", margin: 0 });
  }
  const LOGO_AR = 2.831;  // logo width / height
  // dark cover/divider/closing: logo on a white rounded badge (logo bg is white -> blends)
  function clientChip(s) {
    if (!LOGO) return chip(s, 8.55, 0.36, 0.98, 0.44, 17, 0.09);
    const ih = 0.30, iw = ih * LOGO_AR, pad = 0.08;
    const pw = iw + pad * 2, ph = ih + pad * 2, px = 9.54 - pw, py = 0.34;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: px, y: py, w: pw, h: ph, rectRadius: 0.06, fill: { color: C.white }, line: { type: "none" } });
    s.addImage({ path: LOGO, x: px + pad, y: py + pad, w: iw, h: ih });
  }

  // footer: page number (center) + logo or brand chip (bottom-right). Content slides.
  function footer(s, num) {
    if (num) s.addText(String(num), { x: 4.6, y: 5.30, w: 0.8, h: 0.22, fontFace: FONT, fontSize: 9, color: C.muted, align: "center", valign: "middle", margin: 0 });
    if (!LOGO) return chip(s, 9.32, 5.28, 0.58, 0.26, 9.5, 0.06);
    const ih = 0.215, iw = ih * LOGO_AR;
    s.addImage({ path: LOGO, x: 9.66 - iw, y: 5.30, w: iw, h: ih });
  }

  // numbered analysis block: numbered main topics (number in accent) + bulleted sub-content.
  // sections: [{ h: "topic", b: ["bullet", ...] }, ...]
  function analysis(s, region, sections, o = {}) {
    const fsH = o.fsH || 11, fsB = o.fsB || 9.5;
    const rt = [];
    sections.forEach((sec, i) => {
      // big topic = numbered (number + title in ink/black, title underlined)
      rt.push({ text: `${i + 1}. `, options: { fontFace: FONT, fontSize: fsH, bold: true, color: C.ink, breakLine: false } });
      rt.push({ text: sec.h, options: { fontFace: FONT, fontSize: fsH, bold: true, color: C.ink, underline: { style: "sng" }, breakLine: true, paraSpaceBefore: i ? 6 : 0, paraSpaceAfter: 3, lineSpacingMultiple: 1.5 } });
      // sub-content = bullets
      sec.b.forEach((b) => rt.push({ text: b, options: { fontFace: FONT, fontSize: fsB, color: C.body, bullet: { characterCode: "2022", indent: 14 }, indentLevel: 1, breakLine: true, lineSpacingMultiple: 1.5, paraSpaceAfter: 1 } }));
    });
    s.addText(rt, { x: region.x, y: region.y, w: region.w, h: region.h, valign: "top", margin: 0, fit: "shrink" });
  }

  // table cell helper
  function cell(text, o = {}) {
    return { text, options: { fill: o.fill ? { color: o.fill } : undefined, color: o.color, bold: !!o.b, align: o.al || "left", valign: "middle", fontFace: FONT } };
  }

  const notes = (s, t) => s.addNotes(t);

  return {
    C, FONT, CLIENT, COPYRIGHT,
    CX, CY, CW, CH, IX, IW, GAP, COL_W, COL_L_X, COL_R_X, BODY_Y, BODY_H, HDR_H,
    fullBg, contentFrame, header, summary, card, subBand, clientChip, footer, analysis, cell, notes,
  };
}

module.exports = { TOKENS, deriveBrand, makeHelpers };
