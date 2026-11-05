#!/usr/bin/env node
// Build a Word (.docx) and a standalone HTML report from one Markdown file, in the aws-reports house style.
//   node report.mjs <input.md> [--out-dir DIR] [--name BASENAME] [--only docx|html]
// Markdown conventions: ../references/markdown-spec.md (benchmark and PoC reports use the same syntax)
// npm packages (docx, marked) come from a local node_modules or the global npm folder that my-plugins:setup installs to.
import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';
import { execFileSync } from 'node:child_process';
import { fileURLToPath, pathToFileURL } from 'node:url';

// ESM imports do not read NODE_PATH, so a package that is not in a node_modules above this file is looked up by hand:
// NODE_PATH entries first, then `npm root -g`. The skill folder is the plugin cache and gets no node_modules of its own.
function npmRoots() {
  const roots = (process.env.NODE_PATH || '').split(path.delimiter).filter(Boolean);
  try { roots.push(execFileSync('npm', ['root', '-g'], { encoding: 'utf8', stdio: ['ignore', 'pipe', 'ignore'] }).trim()); } catch { /* no npm */ }
  return roots;
}
function entryOf(dir) {
  const pj = JSON.parse(fs.readFileSync(path.join(dir, 'package.json'), 'utf8'));
  let e = pj.exports && typeof pj.exports === 'object' && '.' in pj.exports ? pj.exports['.'] : pj.exports;
  if (e && typeof e === 'object') e = e.import ?? e.default ?? e.node;
  if (e && typeof e === 'object') e = e.default;
  return path.join(dir, typeof e === 'string' ? e : pj.module || pj.main || 'index.js');
}
async function load(name) {
  try { return await import(name); } catch (e) { if (e.code !== 'ERR_MODULE_NOT_FOUND') throw e; }
  for (const root of npmRoots()) {
    const dir = path.join(root, name);
    if (fs.existsSync(path.join(dir, 'package.json'))) return import(pathToFileURL(entryOf(dir)).href);
  }
  console.error(`error: npm package "${name}" not found (local node_modules, NODE_PATH, npm root -g). `
    + 'Install the report dependencies with the my-plugins setup skill: bash <plugin>/skills/setup/scripts/setup.sh install');
  process.exit(1);
}
const { Lexer } = await load('marked');
const {
  Document, Packer, Paragraph, TextRun, ImageRun, Table, TableRow, TableCell, WidthType, ShadingType, BorderStyle,
  AlignmentType, HeadingLevel, ExternalHyperlink, InternalHyperlink, Bookmark, Header, Footer, PageNumber, LevelFormat,
  VerticalAlign, TableLayoutType, CharacterSet,
} = await load('docx');

const HERE = path.dirname(fileURLToPath(import.meta.url));

// ---------- style (Word and HTML share these values)
const FONT = 'NanumSquareOTF';
const MONO = 'D2Coding';
const C = {
  ink: '1F2937', muted: '6B7280', line: 'D1D5DB', head: 'F1F3F6', note: 'F4F6F9', code: 'F7F8FA',
  link: '1D4ED8', title: '111827', h2: '1F2937', th: '374151',
};
const PAGE = { width: 11906, height: 16838, margin: 1134 }; // A4, 2 cm margins (DXA)
const TEXT_W = PAGE.width - 2 * PAGE.margin; // 9638 DXA = 17 cm
const MAX_IMG_CM = 17;

// ---------- CLI
const usage = () => console.log('usage: node report.mjs <input.md> [--out-dir DIR] [--name BASENAME] [--only docx|html]');
const die = (m) => { console.error(`error: ${m}`); process.exit(1); };
const warnings = [];
const warn = (m) => { warnings.push(m); console.error(`warn: ${m}`); };

const argv = process.argv.slice(2);
const opt = { outDir: null, name: null, only: null };
let input = null;
for (let i = 0; i < argv.length; i++) {
  const a = argv[i];
  if (a === '--out-dir') opt.outDir = argv[++i];
  else if (a === '--name') opt.name = argv[++i];
  else if (a === '--only') opt.only = argv[++i];
  else if (a === '-h' || a === '--help') { usage(); process.exit(0); }
  else if (!input) input = a;
  else die(`unexpected argument: ${a}`);
}
if (!input) { usage(); process.exit(1); }
if (opt.only && !['docx', 'html'].includes(opt.only)) die('--only must be docx or html');
const SRC = path.resolve(input);
const BASE_DIR = path.dirname(SRC);
const OUT_DIR = path.resolve(opt.outDir || BASE_DIR);
const NAME = opt.name || path.basename(SRC).replace(/\.(md|markdown)$/i, '');
fs.mkdirSync(OUT_DIR, { recursive: true });

// ---------- front matter (flat "key: value" lines)
function frontMatter(src) {
  const m = src.match(/^\uFEFF?---\r?\n([\s\S]*?)\r?\n---\r?\n/);
  if (!m) return [{}, src];
  const fm = {};
  for (const line of m[1].split(/\r?\n/)) {
    const kv = line.match(/^([A-Za-z_][\w-]*)\s*:\s*(.*)$/);
    if (kv) fm[kv[1]] = kv[2].trim().replace(/^(["'])(.*)\1$/, '$2');
  }
  return [fm, src.slice(m[0].length)];
}

// ---------- inline tokens -> spans {text, b, i, del, code, href, br}
const ENT = { '&amp;': '&', '&lt;': '<', '&gt;': '>', '&quot;': '"', '&#39;': "'", '&nbsp;': '\u00a0' };
const decode = (s) => String(s ?? '').replace(/&(amp|lt|gt|quot|#39|nbsp);/g, (e) => ENT[e]);
const soft = (s) => s.replace(/[ \t]*\r?\n[ \t]*/g, ' ');

function spans(tokens, st = {}) {
  const out = [];
  for (const t of tokens || []) {
    switch (t.type) {
      case 'text':
        if (t.tokens && t.tokens.length) out.push(...spans(t.tokens, st));
        else out.push({ ...st, text: soft(decode(t.text)) });
        break;
      case 'escape': out.push({ ...st, text: decode(t.text) }); break;
      case 'strong': out.push(...spans(t.tokens, { ...st, b: true })); break;
      case 'em': out.push(...spans(t.tokens, { ...st, i: true })); break;
      case 'del':
        // GFM also reads single tildes as strikethrough, which breaks Korean ranges like "97.1~99.4%". Only ~~text~~ is strikethrough.
        if (String(t.raw || '').startsWith('~~')) out.push(...spans(t.tokens, { ...st, del: true }));
        else out.push({ ...st, text: '~' }, ...spans(t.tokens, st), { ...st, text: '~' });
        break;
      case 'codespan': out.push({ ...st, text: decode(t.text), code: true }); break;
      case 'link': out.push(...spans(t.tokens, { ...st, href: t.href })); break;
      case 'br': out.push({ ...st, text: '', br: true }); break;
      case 'html': // inline HTML is dropped, except <br> (a manual line break, e.g. inside a table header cell)
        if (/^<br\s*\/?>$/i.test(String(t.raw ?? t.text ?? '').trim())) out.push({ ...st, text: '', br: true });
        break;
      case 'image': break; // figures are handled at block level; images inside text are reported there
      default: if (t.text) out.push({ ...st, text: soft(decode(t.text)) });
    }
  }
  return out;
}
const plain = (sp) => sp.map((s) => s.text).join('');
// trim whitespace at both ends of a span list
function trimSpans(sp) {
  const out = sp.map((s) => ({ ...s }));
  while (out.length && !out[0].br && !out[0].code && !out[0].text.trim()) out.shift();
  while (out.length && !out.at(-1).br && !out.at(-1).code && !out.at(-1).text.trim()) out.pop();
  if (out.length && !out[0].code) out[0].text = out[0].text.replace(/^\s+/, '');
  if (out.length && !out.at(-1).code) out.at(-1).text = out.at(-1).text.replace(/\s+$/, '');
  return out;
}
// remove a leading marker like "표:" or "주:" from a span list
function stripPrefix(sp, re) {
  const out = trimSpans(sp);
  if (out.length && !out[0].code) out[0].text = out[0].text.replace(re, '');
  return trimSpans(out);
}

// ---------- images
function imageInfo(href, title) {
  const file = path.resolve(BASE_DIR, decodeURI(href));
  if (!fs.existsSync(file)) die(`image not found: ${href} (resolved to ${file})`);
  const buf = fs.readFileSync(file);
  let type, w, h;
  if (buf.subarray(0, 8).equals(Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]))) {
    type = 'png'; w = buf.readUInt32BE(16); h = buf.readUInt32BE(20);
  } else if (buf[0] === 0xff && buf[1] === 0xd8) {
    type = 'jpg';
    for (let i = 2; i < buf.length - 9;) {
      if (buf[i] !== 0xff) { i++; continue; }
      const m = buf[i + 1], len = buf.readUInt16BE(i + 2);
      if (m >= 0xc0 && m <= 0xcf && ![0xc4, 0xc8, 0xcc].includes(m)) { h = buf.readUInt16BE(i + 5); w = buf.readUInt16BE(i + 7); break; }
      i += 2 + len;
    }
  } else if (/\.svg$/i.test(file)) {
    die(`SVG is not supported in Word; convert it first: uv run --no-project --with playwright python ${path.join(HERE, 'svg2png.py')} ${file}`);
  } else die(`unsupported image type (use PNG or JPEG): ${href}`);
  if (!w || !h) die(`could not read image size: ${href}`);
  const wm = String(title || '').match(/width\s*=\s*([\d.]+)\s*(cm)?/i);
  let widthCm = wm ? Number(wm[1]) : 16;
  if (widthCm > MAX_IMG_CM) { warn(`image width ${widthCm} cm > ${MAX_IMG_CM} cm text width, clamped: ${href}`); widthCm = MAX_IMG_CM; }
  return { file, buf, type, w, h, widthCm };
}

// ---------- markdown -> block model
const CAP_TABLE = /^\s*표\s*[:：]\s*/;
const CAP_FIG = /^\s*그림\s*[:：]\s*/;
const CAP_NOTE = /^\s*주\s*[:：]\s*/;
const PAGEBREAK = /^<!--\s*page-?break\s*-->\s*$/i;

function isNumeric(s) {
  const t = String(s).trim();
  return t !== '' && /^[+\-−~≈<>]?\s*[$₩€]?\s*[\d.,]+(\s*[%배xX×]|\s*(ms|s|초|분|시간|MB|MiB|GB|GiB|MHz|GHz|vCPU|rps|RPS|req\/s|ops\/s|건|개|대|회))?(\s*[(（][^)）]*[)）])?$/.test(t)
    || /^[—–-]$/.test(t);
}

function buildModel(tokens) {
  const blocks = [];
  let pendingBreak = false;
  let seenH2 = false;
  const toks = tokens.filter((t) => t.type !== 'space');
  const push = (b) => {
    if (pendingBreak) { b.pageBreak = true; pendingBreak = false; }
    b.lead = !seenH2;
    blocks.push(b);
    return b;
  };
  const paraSpans = (t) => spans(t.tokens);
  const peekPara = (i, re) => {
    const n = toks[i];
    if (n && n.type === 'paragraph' && re.test(plain(paraSpans(n)))) return stripPrefix(paraSpans(n), re);
    return null;
  };

  for (let i = 0; i < toks.length; i++) {
    const t = toks[i];
    if (t.type === 'heading') {
      let sp = trimSpans(spans(t.tokens));
      let id = null;
      const last = sp.at(-1);
      const m = last && !last.code && last.text.match(/\s*\{#([A-Za-z0-9_-]+)\}\s*$/);
      if (m) { id = m[1]; last.text = last.text.slice(0, m.index); sp = trimSpans(sp); }
      if (t.depth === 1) { push({ t: 'title', spans: sp }); continue; }
      if (t.depth === 2) seenH2 = true;
      if (t.depth > 3) warn(`heading level ${t.depth} rendered as level 3: ${plain(sp)}`);
      push({ t: t.depth === 2 ? 'h2' : 'h3', spans: sp, id });
    } else if (t.type === 'paragraph') {
      const sp = paraSpans(t);
      const imgs = (t.tokens || []).filter((x) => x.type === 'image');
      const rest = (t.tokens || []).filter((x) => x.type !== 'image' && !(x.type === 'text' && !x.text.trim()) && x.type !== 'br');
      if (imgs.length === 1 && rest.length === 0) {
        const img = imgs[0];
        const fig = push({ t: 'figure', img: imageInfo(img.href, img.title), alt: decode(img.text), caption: [{ text: decode(img.text).replace(/^\s*그림\s*\d+\s*[.:]\s*/, '') }] });
        const over = peekPara(i + 1, CAP_FIG);
        if (over) { fig.caption = over; i++; }
        const note = peekPara(i + 1, CAP_NOTE);
        if (note) { fig.note = note; i++; }
        if (!plain(fig.caption).trim()) warn(`figure without caption (alt text is the caption): ${img.href}`);
        continue;
      }
      if (imgs.length) warn('images mixed with text in one paragraph are dropped; put each image in its own paragraph');
      if (CAP_TABLE.test(plain(sp))) warn(`"표:" caption not directly after a table (leave one blank line after the table): ${plain(sp).slice(0, 40)}`);
      push({ t: 'p', spans: trimSpans(sp) });
    } else if (t.type === 'table') {
      const header = t.header.map((c) => trimSpans(spans(c.tokens)));
      let rows = t.rows.map((r) => r.map((c) => trimSpans(spans(c.tokens))));
      let caption = null;
      // a caption line written without a blank line becomes the last table row in GFM: recover it
      const lastRow = rows.at(-1);
      if (lastRow && CAP_TABLE.test(plain(lastRow[0])) && lastRow.slice(1).every((c) => !plain(c).trim())) {
        caption = stripPrefix(lastRow[0], CAP_TABLE); rows = rows.slice(0, -1);
      }
      if (!caption) { caption = peekPara(i + 1, CAP_TABLE); if (caption) i++; }
      const tbl = push({ t: 'table', header, rows, align: t.align, caption });
      const note = peekPara(i + 1, CAP_NOTE);
      if (note) { tbl.note = note; i++; }
      if (!caption) warn(`table without "표:" caption: ${header.map(plain).join(' | ').slice(0, 60)}`);
    } else if (t.type === 'blockquote') {
      push(noteBlock(t.tokens));
    } else if (t.type === 'list') {
      push(listBlock(t));
    } else if (t.type === 'code') {
      push({ t: 'code', text: t.text.replace(/\t/g, '    '), lang: t.lang || '' });
    } else if (t.type === 'html') {
      if (PAGEBREAK.test(t.text.trim())) pendingBreak = true;
      else if (!/^<!--[\s\S]*-->\s*$/.test(t.text.trim())) warn(`raw HTML block skipped: ${t.text.trim().slice(0, 40)}`);
    } else if (t.type === 'hr') {
      warn('horizontal rule ignored; use <!-- pagebreak --> for a page break');
    } else if (t.type === 'text') {
      push({ t: 'p', spans: trimSpans(spans(t.tokens || [{ type: 'text', text: t.text }])) });
    } else warn(`unsupported block skipped: ${t.type}`);
  }
  return blocks;
}

function listBlock(t) {
  return {
    t: 'list', ordered: !!t.ordered, start: t.start === '' || t.start == null ? 1 : Number(t.start),
    items: t.items.map((it) => {
      const parts = []; let sub = null;
      for (const c of it.tokens) {
        if (c.type === 'list') sub = listBlock(c);
        else if (c.type === 'text' || c.type === 'paragraph') parts.push(...(parts.length ? [{ text: ' ' }] : []), ...spans(c.tokens || [{ type: 'text', text: c.text }]));
        else if (c.type !== 'space') warn(`list item content "${c.type}" flattened`);
      }
      return { spans: trimSpans(parts), sub };
    }),
  };
}

function noteBlock(tokens) {
  const inner = tokens.filter((x) => x.type !== 'space');
  let title = null;
  const kids = [];
  inner.forEach((c, k) => {
    if (c.type === 'paragraph') {
      let sp = trimSpans(spans(c.tokens));
      if (k === 0 && sp.length && /^\[!\w+\]/.test(sp[0].text)) { sp[0].text = sp[0].text.replace(/^\[!\w+\]\s*/, ''); sp = trimSpans(sp); }
      if (k === 0 && sp.length && sp.every((s) => s.b || !s.text.trim())) { title = sp.map((s) => ({ ...s, b: false })); return; }
      kids.push({ t: 'p', spans: sp });
    } else if (c.type === 'list') kids.push(listBlock(c));
    else if (c.type === 'code') kids.push({ t: 'code', text: c.text, lang: c.lang || '' });
    else warn(`note box content "${c.type}" skipped`);
  });
  if (title && /(습니다|니다|했다|이다|한다)\.?\s*$/.test(plain(title))) {
    warn(`note box title reads as a sentence; use a noun phrase (e.g. "벤치마크 노드: 필수 DaemonSet만 유지"): ${plain(title)}`);
  }
  return { t: 'note', title, kids };
}

// ---------- column widths (CJK glyphs are wider)
const vlen = (s) => [...String(s)].reduce((a, ch) => a + (/[\u1100-\u11ff\u3130-\u318f\uac00-\ud7a3\u3000-\u303f\uff00-\uffef]/.test(ch) ? 1.75 : 1), 0);
function columnWidths(tbl) {
  const n = tbl.header.length;
  const want = tbl.header.map((h, i) => Math.min(32, Math.max(5, vlen(plain(h)) * 0.85, ...tbl.rows.map((r) => vlen(plain(r[i] || []))))));
  const sum = want.reduce((a, b) => a + b, 0);
  const w = want.map((x) => Math.floor((x / sum) * TEXT_W));
  w[0] += TEXT_W - w.reduce((a, b) => a + b, 0);
  return n ? w : [];
}
// Table layout shared by Word and HTML so both files make the same choices. These follow the user's hand edits of a
// generated Word report (2026-11-04):
// - a header that does not fit on one line in its column gets its trailing unit or parenthetical on a second line
//   ("On-Demand (USD/시간)" -> "On-Demand" / "(USD/시간)"), and every header cell of that table is then centered;
//   tables whose headers all fit keep the column alignment (numbers right) as the user left them;
// - wide tables use smaller text: 8-9 columns 7.5 pt header / 7 pt body, 10+ columns 6.5 pt.
const GLYPH_EM = 0.6; // average advance per vlen unit, in em (bold NanumSquareOTF; Hangul counted 1.75 by vlen)
const CELL_PAD = 160; // left + right cell margins (DXA)
function splitUnit(sp) {
  const m = plain(sp).match(/\s+(?=[(（][^()（）]*[)）]\s*$)/);
  if (!m || m.index === 0) return null;
  const cut = m.index, resume = cut + m[0].length;
  const out = [];
  let pos = 0, done = false;
  const brk = () => { if (!done) { out.push({ text: '', br: true }); done = true; } };
  for (const s of sp) {
    const a = pos, b = pos + s.text.length;
    pos = b;
    if (b <= cut) { out.push(s); continue; }
    if (a >= resume) { brk(); out.push(s); continue; }
    if (a < cut) out.push({ ...s, text: s.text.slice(0, cut - a) });
    brk();
    if (b > resume) out.push({ ...s, text: s.text.slice(resume - a) });
  }
  return out;
}
function tableLayout(tbl) {
  const n = tbl.header.length;
  const widths = columnWidths(tbl);
  const [headSize, bodySize] = n >= 10 ? [13, 13] : n >= 8 ? [15, 14] : [16, 16]; // half-points
  const fits = (sp, i) => vlen(plain(sp)) * GLYPH_EM * (headSize / 2) <= (widths[i] - CELL_PAD) / 20;
  let twoLine = false;
  const header = tbl.header.map((sp, i) => {
    if (sp.some((s) => s.br)) { twoLine = true; return sp; }
    if (fits(sp, i)) return sp;
    twoLine = true;
    return splitUnit(sp) || sp;
  });
  return { widths, headSize, bodySize, header, headCenter: twoLine };
}
// caption notes: centered when they fit on one line (8 pt across the 17 cm column), left-aligned when they wrap.
// The user centered exactly the notes with vlen <= 103 in the same 2026-11-04 edit.
const NOTE_ONE_LINE = 103;
const noteOneLine = (sp) => vlen(plain(sp).trim()) <= NOTE_ONE_LINE;

function columnAlign(tbl) {
  return tbl.header.map((_, i) => {
    const a = tbl.align?.[i];
    if (a === 'right' || a === 'left' || a === 'center') return a;
    if (i === 0) return 'left';
    const cells = tbl.rows.map((r) => plain(r[i] || [])).filter((x) => x.trim());
    return cells.length && cells.filter(isNumeric).length / cells.length >= 0.6 ? 'right' : 'left';
  });
}

// ---------- fonts: subsets for docx embedding and HTML @font-face
function makeFonts(model, fm) {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'bench-report-fonts-'));
  const all = [];
  const code = [];
  const walk = (sp) => sp && sp.forEach((s) => { all.push(s.text); if (s.code) code.push(s.text); });
  for (const v of Object.values(fm)) all.push(String(v));
  const visit = (b) => {
    if (!b) return;
    walk(b.spans); walk(b.caption); walk(b.note); walk(b.title);
    if (b.header) b.header.forEach(walk);
    if (b.rows) b.rows.forEach((r) => r.forEach(walk));
    if (b.items) b.items.forEach((it) => { walk(it.spans); visit(it.sub); });
    if (b.kids) b.kids.forEach(visit);
    if (b.t === 'code') { all.push(b.text); code.push(b.text); }
    if (b.alt) all.push(b.alt);
  };
  model.forEach(visit);
  all.push('0123456789 그림표. /');
  fs.writeFileSync(path.join(dir, 'text.txt'), all.join('\n'));
  fs.writeFileSync(path.join(dir, 'code.txt'), code.join('\n'));
  const py = path.join(HERE, 'fonts.py');
  const runners = [
    ['uv', ['run', '--quiet', '--no-project', '--with', 'fonttools', '--with', 'brotli', 'python', py]],
    ['python3', [py]],
  ];
  for (const [cmd, pre] of runners) {
    try {
      const out = execFileSync(cmd, [...pre, '--text-file', path.join(dir, 'text.txt'), '--code-file', path.join(dir, 'code.txt'), '--out-dir', dir],
        { encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'] });
      const res = JSON.parse(out.trim().split('\n').at(-1));
      for (const m of res.missing || []) warn(`font not found, not embedded: ${m} (install it with the my-plugins setup skill)`);
      return { ...res, dir };
    } catch (e) { /* try the next runner */ }
  }
  warn('font subsetting failed (needs uv, or python3 with fonttools+brotli); D2Coding is not embedded and the HTML falls back to locally installed fonts');
  return { docx_mono: null, html: [], dir };
}

// =====================================================================================
// Word
function renderDocx(model, fm, fonts, outFile) {
  let fig = 0, tab = 0, sec = 0, olInstance = 0;
  const out = [];
  const run = (text, o = {}) => new TextRun({ text, font: o.mono ? MONO : FONT, size: o.size, bold: o.bold, italics: o.italics, strike: o.strike, color: o.color });
  const inl = (sp, o = {}) => (sp || []).map((s) => {
    if (s.br) return new TextRun({ break: 1 });
    const size = s.code ? (o.size ? o.size - 1 : 18) : o.size;
    const r = { size, bold: o.bold || s.b, italics: s.i, strike: s.del, color: o.color, mono: s.code };
    if (s.href) {
      const kids = [new TextRun({ text: s.text, style: 'Hyperlink', font: s.code ? MONO : FONT, size, bold: r.bold })];
      return s.href.startsWith('#') ? new InternalHyperlink({ anchor: s.href.slice(1), children: kids }) : new ExternalHyperlink({ link: s.href, children: kids });
    }
    return run(s.text, r);
  });
  const body = (children, extra = {}) => new Paragraph({ children, spacing: { after: 120, line: 300 }, ...extra });
  const spacer = (after = 120) => new Paragraph({ spacing: { after }, children: [] });
  const caption = (label, n, sp) => new Paragraph({ alignment: AlignmentType.CENTER, keepLines: true, spacing: { before: 60, after: 40 },
    children: [run(`${label} ${n}. `, { bold: true, size: 18 }), ...inl(sp, { size: 18 })] });
  const capNote = (sp) => new Paragraph({ alignment: noteOneLine(sp) ? AlignmentType.CENTER : AlignmentType.LEFT,
    children: inl(sp, { size: 16, color: C.muted }), spacing: { after: 200, line: 260 } });
  const line = { style: BorderStyle.SINGLE, size: 4, color: C.line };
  const none = { style: BorderStyle.NONE, size: 0, color: 'FFFFFF' };
  const box = (children, fill) => new Table({ width: { size: TEXT_W, type: WidthType.DXA }, columnWidths: [TEXT_W], layout: TableLayoutType.FIXED,
    rows: [new TableRow({ children: [new TableCell({ width: { size: TEXT_W, type: WidthType.DXA }, borders: { top: line, bottom: line, left: line, right: line },
      shading: { type: ShadingType.CLEAR, color: 'auto', fill }, margins: { top: 140, bottom: 80, left: 220, right: 220 }, children })] })] });

  const listParas = (b, level = 0, o = {}) => {
    const inst = b.ordered ? ++olInstance : 0;
    const paras = [];
    for (const it of b.items) {
      paras.push(new Paragraph({ children: inl(it.spans, o), spacing: { after: 60, line: 290 },
        numbering: b.ordered ? { reference: 'ordered', level: Math.min(level, 1), instance: inst } : { reference: 'bullets', level: Math.min(level, 1) } }));
      if (it.sub) paras.push(...listParas(it.sub, level + 1, o));
    }
    return paras;
  };
  const codeParas = (text) => text.split('\n').map((ln) => new Paragraph({ spacing: { after: 0, line: 260 }, children: [run(ln.length ? ln : ' ', { mono: true, size: 17 })] }));

  function table(b) {
    const { widths, headSize, bodySize, header, headCenter } = tableLayout(b);
    const align = columnAlign(b).map((a) => (a === 'right' ? AlignmentType.RIGHT : a === 'center' ? AlignmentType.CENTER : AlignmentType.LEFT));
    const borders = { top: line, bottom: line, left: none, right: none };
    const cell = (sp, i, head) => new TableCell({
      width: { size: widths[i], type: WidthType.DXA }, borders, verticalAlign: VerticalAlign.CENTER,
      shading: head ? { type: ShadingType.CLEAR, color: 'auto', fill: C.head } : undefined, margins: { top: 50, bottom: 50, left: 80, right: 80 },
      children: [new Paragraph({ alignment: head && headCenter ? AlignmentType.CENTER : align[i],
        children: inl(sp, { size: head ? headSize : bodySize, bold: head, color: head ? C.th : C.ink }) })],
    });
    return new Table({ width: { size: TEXT_W, type: WidthType.DXA }, columnWidths: widths, layout: TableLayoutType.FIXED,
      rows: [new TableRow({ tableHeader: true, cantSplit: true, children: header.map((h, i) => cell(h, i, true)) }),
        ...b.rows.map((r) => new TableRow({ cantSplit: true, children: b.header.map((_, i) => cell(r[i] || [], i, false)) }))] });
  }

  // title block
  const titleBlock = model.find((b) => b.t === 'title');
  const title = fm.title || (titleBlock ? plain(titleBlock.spans) : NAME);
  if (fm.eyebrow) out.push(new Paragraph({ spacing: { after: 80 }, children: [run(fm.eyebrow, { size: 18, color: C.muted })] }));
  out.push(new Paragraph({ heading: HeadingLevel.TITLE, children: titleBlock && !fm.title ? inl(titleBlock.spans) : [run(title)] }));
  if (fm.meta) out.push(new Paragraph({ spacing: { after: 240 }, children: [run(fm.meta, { size: 17, color: C.muted })] }));
  const numbered = String(fm.numbered ?? 'true') !== 'false';

  for (const b of model) {
    switch (b.t) {
      case 'title': break;
      case 'h2':
        sec++;
        out.push(new Paragraph({ heading: HeadingLevel.HEADING_1, keepNext: true, pageBreakBefore: !!b.pageBreak,
          children: [new Bookmark({ id: b.id || `sec-${sec}`, children: [run(numbered ? `${sec}. ` : ''), ...inl(b.spans)] })] }));
        break;
      case 'h3':
        out.push(new Paragraph({ heading: HeadingLevel.HEADING_2, keepNext: true, pageBreakBefore: !!b.pageBreak,
          children: b.id ? [new Bookmark({ id: b.id, children: inl(b.spans) })] : inl(b.spans) }));
        break;
      case 'p':
        out.push(body(inl(b.spans), b.pageBreak ? { pageBreakBefore: true } : {}));
        break;
      case 'figure': {
        const wpx = Math.round((b.img.widthCm / 2.54) * 96);
        out.push(new Paragraph({ alignment: AlignmentType.CENTER, keepNext: true, pageBreakBefore: !!b.pageBreak, spacing: { before: 120, after: 0 },
          children: [new ImageRun({ type: b.img.type, data: b.img.buf, transformation: { width: wpx, height: Math.round((wpx * b.img.h) / b.img.w) },
            altText: { title: b.alt || path.basename(b.img.file), description: b.alt || '', name: path.basename(b.img.file) } })] }));
        out.push(caption('그림', ++fig, b.caption));
        out.push(b.note ? capNote(b.note) : spacer());
        break;
      }
      case 'table':
        if (b.pageBreak) out.push(new Paragraph({ pageBreakBefore: true, children: [] }));
        out.push(table(b));
        if (b.caption) out.push(caption('표', ++tab, b.caption));
        out.push(b.note ? capNote(b.note) : spacer(160));
        break;
      case 'note': {
        const kids = [];
        if (b.title) kids.push(new Paragraph({ keepNext: true, spacing: { after: 60, line: 290 }, children: inl(b.title, { bold: true }) }));
        for (const k of b.kids) {
          if (k.t === 'p') kids.push(new Paragraph({ spacing: { after: 60, line: 290 }, children: inl(k.spans) }));
          else if (k.t === 'list') kids.push(...listParas(k));
          else if (k.t === 'code') kids.push(...codeParas(k.text));
        }
        if (!kids.length) kids.push(new Paragraph({ children: [] }));
        if (b.pageBreak) out.push(new Paragraph({ pageBreakBefore: true, children: [] }));
        out.push(box(kids, C.note));
        out.push(spacer());
        break;
      }
      case 'list':
        out.push(...listParas(b));
        out.push(spacer(60));
        break;
      case 'code':
        if (b.pageBreak) out.push(new Paragraph({ pageBreakBefore: true, children: [] }));
        out.push(box(codeParas(b.text), C.code));
        out.push(spacer());
        break;
      default: warn(`docx: block ${b.t} skipped`);
    }
  }

  const headerText = fm.header || title;
  const doc = new Document({
    creator: fm.author || 'aws-reports', title, description: fm.description || '',
    fonts: fonts.docx_mono ? [{ name: MONO, data: fs.readFileSync(fonts.docx_mono), characterSet: CharacterSet.ANSI }] : undefined,
    styles: {
      default: {
        document: { run: { font: FONT, size: 20, color: C.ink, language: { value: 'ko-KR', eastAsia: 'ko-KR' } }, paragraph: { wordWrap: true } },
        title: { run: { font: FONT, size: 40, bold: true, color: C.title }, paragraph: { spacing: { after: 120 } } },
        heading1: { run: { font: FONT, size: 28, bold: true, color: C.title }, paragraph: { spacing: { before: 360, after: 140 } } },
        heading2: { run: { font: FONT, size: 23, bold: true, color: C.h2 }, paragraph: { spacing: { before: 220, after: 100 } } },
      },
      characterStyles: [{ id: 'Hyperlink', name: 'Hyperlink', basedOn: 'DefaultParagraphFont', run: { color: C.link, underline: {} } }],
    },
    numbering: { config: [
      { reference: 'bullets', levels: [
        { level: 0, format: LevelFormat.BULLET, text: '•', alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 520, hanging: 260 } } } },
        { level: 1, format: LevelFormat.BULLET, text: '–', alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 940, hanging: 260 } } } }] },
      { reference: 'ordered', levels: [
        { level: 0, format: LevelFormat.DECIMAL, text: '%1.', alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 560, hanging: 300 } } } },
        { level: 1, format: LevelFormat.DECIMAL, text: '%1.%2.', alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 1060, hanging: 440 } } } }] },
    ] },
    sections: [{
      properties: { page: { size: { width: PAGE.width, height: PAGE.height }, margin: { top: PAGE.margin, bottom: PAGE.margin, left: PAGE.margin, right: PAGE.margin, header: 567, footer: 567 } } },
      headers: { default: new Header({ children: [new Paragraph({ alignment: AlignmentType.RIGHT, children: [run(headerText, { size: 15, color: C.muted })] })] }) },
      footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [
        new TextRun({ children: [PageNumber.CURRENT], font: FONT, size: 16, color: C.muted }), run(' / ', { size: 16, color: C.muted }),
        new TextRun({ children: [PageNumber.TOTAL_PAGES], font: FONT, size: 16, color: C.muted })] })] }) },
      children: out,
    }],
  });
  return Packer.toBuffer(doc).then((buf) => { fs.writeFileSync(outFile, buf); return { fig, tab, sec, bytes: buf.length }; });
}

// =====================================================================================
// HTML (standalone: fonts and images inline)
function renderHtml(model, fm, fonts, outFile) {
  const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  const inl = (sp) => (sp || []).map((s) => {
    if (s.br) return '<br>';
    let h = esc(s.text);
    if (s.code) h = `<code>${h}</code>`;
    if (s.del) h = `<del>${h}</del>`;
    if (s.i) h = `<em>${h}</em>`;
    if (s.b) h = `<strong>${h}</strong>`;
    if (s.href) h = `<a href="${esc(s.href)}">${h}</a>`;
    return h;
  }).join('');
  let fig = 0, tab = 0, sec = 0;
  const pb = (b) => (b.pageBreak ? ' br-pb' : '');
  const list = (b) => {
    const tag = b.ordered ? 'ol' : 'ul';
    const start = b.ordered && b.start !== 1 ? ` start="${b.start}"` : '';
    return `<${tag}${start}>${b.items.map((it) => `<li>${inl(it.spans)}${it.sub ? list(it.sub) : ''}</li>`).join('')}</${tag}>`;
  };
  const code = (b) => `<pre class="br-code${pb(b)}"><code>${esc(b.text)}</code></pre>`;
  const capNote = (sp) => (sp ? `<p class="br-capnote${noteOneLine(sp) ? ' one' : ''}">${inl(sp)}</p>` : '');
  const html = [];
  let open = false;
  const numbered = String(fm.numbered ?? 'true') !== 'false';
  const titleBlock = model.find((b) => b.t === 'title');
  const title = fm.title || (titleBlock ? plain(titleBlock.spans) : NAME);
  html.push('<header class="br-head">');
  if (fm.eyebrow) html.push(`<p class="br-eyebrow">${esc(fm.eyebrow)}</p>`);
  html.push(`<h1>${titleBlock && !fm.title ? inl(titleBlock.spans) : esc(title)}</h1>`);
  if (fm.meta) html.push(`<p class="br-meta">${esc(fm.meta)}</p>`);
  html.push('</header>');
  for (const b of model) {
    switch (b.t) {
      case 'title': break;
      case 'h2':
        if (open) html.push('</section>');
        sec++;
        html.push(`<section class="br-sec${pb(b)}" id="${esc(b.id || `sec-${sec}`)}"><h2>${numbered ? `<span class="br-num">${sec}.</span> ` : ''}${inl(b.spans)}</h2>`);
        open = true;
        break;
      case 'h3': html.push(`<h3${b.id ? ` id="${esc(b.id)}"` : ''} class="${pb(b).trim()}">${inl(b.spans)}</h3>`); break;
      case 'p': html.push(`<p class="${(b.lead ? 'br-lead' : '') + pb(b)}">${inl(b.spans)}</p>`); break;
      case 'figure': {
        const mime = b.img.type === 'png' ? 'image/png' : 'image/jpeg';
        const pct = Math.round((b.img.widthCm / MAX_IMG_CM) * 100);
        html.push(`<figure class="br-fig${pb(b)}"><img src="data:${mime};base64,${b.img.buf.toString('base64')}" alt="${esc(b.alt)}" style="width:${pct}%" width="${b.img.w}" height="${b.img.h}">`
          + `<figcaption><span class="br-cap-label">그림 ${++fig}.</span> ${inl(b.caption)}</figcaption>${capNote(b.note)}</figure>`);
        break;
      }
      case 'table': {
        const al = columnAlign(b);
        const lay = tableLayout(b);
        const cls = (i) => (al[i] === 'right' ? ' class="num"' : al[i] === 'center' ? ' class="ctr"' : '');
        const n = b.header.length;
        const tcls = [n >= 10 ? 'br-xwide' : n >= 8 ? 'br-wide' : '', lay.headCenter ? 'br-head-ctr' : ''].filter(Boolean).join(' ');
        html.push(`<figure class="br-tbl${pb(b)}"><div class="br-tbl-wrap" tabindex="0"><table${tcls ? ` class="${tcls}"` : ''}><thead><tr>${lay.header.map((h, i) => `<th${lay.headCenter ? ' class="ctr"' : cls(i)}>${inl(h)}</th>`).join('')}</tr></thead><tbody>`
          + b.rows.map((r) => `<tr>${b.header.map((_, i) => `<td${cls(i)}>${inl(r[i] || [])}</td>`).join('')}</tr>`).join('')
          + `</tbody></table></div>${b.caption ? `<figcaption><span class="br-cap-label">표 ${++tab}.</span> ${inl(b.caption)}</figcaption>` : ''}`
          + `${capNote(b.note)}</figure>`);
        break;
      }
      case 'note':
        html.push(`<aside class="br-note${pb(b)}">${b.title ? `<p class="br-note-title">${inl(b.title)}</p>` : ''}`
          + b.kids.map((k) => (k.t === 'p' ? `<p>${inl(k.spans)}</p>` : k.t === 'list' ? list(k) : code(k))).join('') + '</aside>');
        break;
      case 'list': html.push(list(b)); break;
      case 'code': html.push(code(b)); break;
      default: warn(`html: block ${b.t} skipped`);
    }
  }
  if (open) html.push('</section>');

  const face = (fonts.html || []).map((f) => `@font-face{font-family:'${f.family}';font-weight:${f.weight};font-style:normal;font-display:swap;`
    + `src:url(data:font/woff2;base64,${fs.readFileSync(f.file).toString('base64')}) format('woff2'),local('${f.local}')}`).join('\n');
  const headerText = String(fm.header || title).replace(/["\\]/g, '');
  const css = `${face}
:root{--ink:#${C.ink};--muted:#${C.muted};--line:#${C.line};--head:#${C.head};--note:#${C.note};--code:#${C.code};--link:#${C.link};--title:#${C.title};--th:#${C.th};--bg:#FFFFFF;--fig:#FFFFFF;color-scheme:light dark}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--ink:#E5E7EB;--muted:#9CA3AF;--line:#3B4452;--head:#1E2633;--note:#18202B;--code:#151B23;--link:#93C5FD;--title:#F9FAFB;--th:#D1D5DB;--bg:#0E131A;--fig:#FFFFFF}}
:root[data-theme="dark"]{--ink:#E5E7EB;--muted:#9CA3AF;--line:#3B4452;--head:#1E2633;--note:#18202B;--code:#151B23;--link:#93C5FD;--title:#F9FAFB;--th:#D1D5DB;--bg:#0E131A;--fig:#FFFFFF}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--bg);color:var(--ink);font-family:'${FONT}','NanumSquare','Apple SD Gothic Neo','Malgun Gothic','Noto Sans KR',sans-serif;font-size:16px;line-height:1.75;word-break:keep-all;overflow-wrap:break-word}
main{max-width:820px;margin:0 auto;padding:48px 24px 88px}
.br-eyebrow{font-size:13px;color:var(--muted);margin:0 0 6px}
h1{font-size:30px;line-height:1.35;font-weight:700;color:var(--title);margin:0 0 8px;text-wrap:balance}
.br-meta{font-size:13px;color:var(--muted);margin:0 0 28px}
h2{font-size:22px;line-height:1.4;font-weight:700;color:var(--title);margin:56px 0 14px}
h3{font-size:18px;line-height:1.45;font-weight:700;color:var(--title);margin:32px 0 10px}
p{margin:0 0 14px}
strong{font-weight:700}
a{color:var(--link)}
code{font-family:'${MONO}',ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;font-size:.92em}
ul,ol{margin:0 0 16px;padding-left:1.5em}
li{margin:4px 0}
li>ul,li>ol{margin:4px 0 0}
figure{margin:28px 0}
.br-fig img{display:block;margin:0 auto;max-width:100%;height:auto;background:var(--fig);border-radius:4px}
figcaption{text-align:center;font-size:14px;line-height:1.6;margin-top:10px}
.br-cap-label{font-weight:700}
.br-capnote{font-size:13px;line-height:1.65;color:var(--muted);margin:6px 0 0}
.br-capnote.one{text-align:center}
.br-tbl-wrap{overflow-x:auto}
table{border-collapse:collapse;width:100%;font-size:14px;line-height:1.5;font-variant-numeric:tabular-nums}
th,td{padding:7px 10px;border-top:1px solid var(--line);border-bottom:1px solid var(--line);text-align:left;vertical-align:middle}
th{background:var(--head);color:var(--th);font-weight:700}
.num{text-align:right;white-space:nowrap}
.ctr{text-align:center}
th.ctr{white-space:normal}
table.br-wide{font-size:13px}
table.br-xwide{font-size:12px}
table.br-wide th,table.br-wide td,table.br-xwide th,table.br-xwide td{padding:6px 7px}
.br-note{background:var(--note);border:1px solid var(--line);border-radius:6px;padding:16px 20px;margin:22px 0}
.br-note-title{font-weight:700;margin:0 0 6px}
.br-note>:last-child,.br-note li:last-child{margin-bottom:0}
.br-code{background:var(--code);border:1px solid var(--line);border-radius:6px;padding:12px 16px;margin:0 0 18px;overflow-x:auto;font-size:13.5px;line-height:1.6}
.br-code code{font-size:inherit}
@media (max-width:640px){main{padding:28px 16px 64px}h1{font-size:24px}h2{font-size:19px;margin-top:44px}table{font-size:13px}.br-capnote.one{text-align:left}}
@page{size:A4;margin:20mm;@top-right{content:"${headerText}";font-size:7.5pt;color:#6B7280}@bottom-center{content:counter(page) " / " counter(pages);font-size:8pt;color:#6B7280}}
@media print{:root{--ink:#${C.ink};--muted:#${C.muted};--line:#${C.line};--head:#${C.head};--note:#${C.note};--code:#${C.code};--title:#${C.title};--bg:#FFFFFF}body{font-size:10pt}main{max-width:none;padding:0}.br-pb{break-before:page}figure,.br-note,.br-code,tr{break-inside:avoid}h2,h3{break-after:avoid}a{color:inherit}}`;
  const doc = `<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>${esc(title)}</title>
${fm.description ? `<meta name="description" content="${esc(fm.description)}">` : ''}
<style>
${css}
</style>
</head>
<body>
<main class="br">
${html.join('\n')}
</main>
</body>
</html>
`;
  fs.writeFileSync(outFile, doc);
  return { fig, tab, sec, bytes: Buffer.byteLength(doc) };
}

// =====================================================================================
const [fm, md] = frontMatter(fs.readFileSync(SRC, 'utf8'));
const model = buildModel(new Lexer({ gfm: true }).lex(md));
const fonts = makeFonts(model, fm);
const results = {};
if (opt.only !== 'html') results.docx = { file: path.join(OUT_DIR, `${NAME}.docx`), ...(await renderDocx(model, fm, fonts, path.join(OUT_DIR, `${NAME}.docx`))) };
if (opt.only !== 'docx') results.html = { file: path.join(OUT_DIR, `${NAME}.html`), ...renderHtml(model, fm, fonts, path.join(OUT_DIR, `${NAME}.html`)) };
fs.rmSync(fonts.dir, { recursive: true, force: true });
for (const [k, r] of Object.entries(results)) {
  console.log(`${k}: ${r.file} (${(r.bytes / 1024).toFixed(0)} KB) sections=${r.sec} figures=${r.fig} tables=${r.tab}`);
}
console.log(`fonts: mono embedded in docx=${!!fonts.docx_mono}, html font faces=${(fonts.html || []).length}; warnings=${warnings.length}`);
