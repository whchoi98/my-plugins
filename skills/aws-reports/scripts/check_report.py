#!/usr/bin/env python3
"""Check a finished report (.docx and/or .html) against the aws-reports house style.

usage: python3 check_report.py report.docx report.html [--profile benchmark|poc] [--json]

--profile benchmark (default): benchmark report. First section = test setup and method, last = overall verdict.
--profile poc: PoC result report. First section = PoC overview, a success criteria section, last = verdict and next
               steps, verdict cells use the fixed vocabulary (충족 / 부분 충족 / 미충족 / 측정하지 않음).

ERROR = the file breaks the style contract (fix before handing over).
WARN  = wording or structure the user corrected before (style_terms.json, box titles, section order); review each one.
Exit code 1 when there is any ERROR.
"""
import json
import re
import sys
import zipfile
from html.parser import HTMLParser
from pathlib import Path

HERE = Path(__file__).resolve().parent
TERMS = json.loads((HERE / "style_terms.json").read_text(encoding="utf-8"))["terms"]
PROFILE = "benchmark"
FONT, MONO = "NanumSquareOTF", "D2Coding"
NOTE_FILL, CODE_FILL = "F4F6F9", "F7F8FA"
SENTENCE_END = re.compile(r"(습니다|니다|했다|이다|한다)\.?\s*$")
METHOD_HINT = re.compile(r"측정|환경|방법|조건|구성")
VERDICT_HINT = re.compile(r"종합|결론|평가|권고|요약")
POC_FIRST_HINT = re.compile(r"개요|배경|목적|범위")
POC_CRITERIA_HINT = re.compile(r"성공 기준|평가 기준|성공 조건")
POC_LAST_HINT = re.compile(r"종합|평가|결론|다음 단계|권고")
VERDICT_WORD = re.compile(r"^(충족|부분 충족|미충족|측정하지 않음)(\s*[(（].*[)）])?$")
DECISION_WORD = re.compile(r"조건부 진행|진행(을|하기를|할 것을)? 권고|진행합니다|보류|재검토|중단")
NOTE_ONE_LINE = 103  # report.mjs: caption notes up to this vlen are centered


def vlen(s):
    return sum(1.75 if re.match(r"[\u1100-\u11ff\u3130-\u318f\uac00-\ud7a3\u3000-\u303f\uff00-\uffef]", ch) else 1 for ch in s)


class Report:
    def __init__(self, name):
        self.name, self.errors, self.warns, self.info = name, [], [], {}

    def err(self, m):
        self.errors.append(m)

    def warn(self, m):
        self.warns.append(m)


def term_warnings(rep, text):
    for t in TERMS:
        if PROFILE not in t.get("profiles", ["benchmark", "poc"]):
            continue
        for m in re.finditer(t["pattern"], text):
            ctx = text[max(0, m.start() - 18): m.end() + 18].replace("\n", " ")
            rep.warn(f'용어 "{m.group(0)}" → {t["use"]} | …{ctx}…')


def structure_warnings(rep, h2s, note_titles):
    if PROFILE == "poc":
        if h2s and not POC_FIRST_HINT.search(h2s[0]):
            rep.warn(f'첫 번째 섹션이 PoC 개요가 아님: "{h2s[0]}" (poc-structure.md: 개요를 맨 앞에)')
        if h2s and not any(POC_CRITERIA_HINT.search(h) for h in h2s):
            rep.warn("성공 기준 섹션이 없음 (poc-structure.md: 2. 성공 기준)")
        if h2s and not POC_LAST_HINT.search(h2s[-1]):
            rep.warn(f'마지막 섹션이 종합 평가와 다음 단계가 아님: "{h2s[-1]}"')
    else:
        if h2s and not METHOD_HINT.search(h2s[0]):
            rep.warn(f'첫 번째 섹션이 측정 환경/방법이 아님: "{h2s[0]}" (benchmark-structure.md: 측정 환경과 방법을 맨 앞에)')
        if h2s and not VERDICT_HINT.search(h2s[-1]):
            rep.warn(f'마지막 섹션이 종합 평가가 아님: "{h2s[-1]}"')
    for t in note_titles:
        if SENTENCE_END.search(t):
            rep.warn(f'박스 제목이 문장형: "{t}" → 함축형으로 (예: "벤치마크 노드: 필수 DaemonSet만 유지")')


def table_rule_errors(rep, tables):
    """tables: [(header cells [(text, two_line, centered)], body rows [[text]])].
    A table whose header has a two-line cell centers every header cell (report.mjs tableLayout)."""
    for head, _ in tables:
        if any(two for _, two, _ in head) and not all(ctr for _, _, ctr in head):
            names = " | ".join(t for t, _, _ in head)[:60]
            rep.err(f"two-line table header is not centered in every cell: {names}")


def poc_warnings(rep, tables, lead_text):
    if PROFILE != "poc":
        return
    vt = [(h, rows) for h, rows in tables if any(t.strip() == "판정" for t, _, _ in h)]
    if not vt:
        rep.warn("'판정' 열이 있는 표가 없음 (표 1 성공 기준 판정 요약)")
    for h, rows in vt:
        k = [t.strip() for t, _, _ in h].index("판정")
        for r in rows:
            v = r[k].strip() if k < len(r) else ""
            if v and not VERDICT_WORD.match(v):
                rep.warn(f'판정 "{v}" → 충족 / 부분 충족 / 미충족 / 측정하지 않음 중 하나로 (poc-verdict-rules.md)')
    if not DECISION_WORD.search(lead_text):
        rep.warn("첫 섹션 앞(리드, 결론 문단)에 전체 판정(진행 / 조건부 진행 / 보류)이 없음")


# ---------------------------------------------------------------- docx
def texts(xml):
    return "".join(re.findall(r"<w:t(?:\s[^>]*)?>([^<]*)</w:t>", xml))


def docx_table(xml):
    rows = re.findall(r"<w:tr[ >].*?</w:tr>", xml, re.S)
    cells = [re.findall(r"<w:tc>.*?</w:tc>", r, re.S) for r in rows]
    if not cells:
        return None
    def centered(c):
        paras = re.findall(r"<w:p[ >].*?</w:p>", c, re.S)
        return bool(paras) and all('<w:jc w:val="center"/>' in p for p in paras)

    head = [(texts(c), "<w:br/>" in c or len(re.findall(r"<w:p[ >]", c)) > 1, centered(c)) for c in cells[0]]
    body = [[texts(c) for c in r] for r in cells[1:]]
    return head, body


def check_docx(path):
    rep = Report(str(path))
    z = zipfile.ZipFile(path)
    doc = z.read("word/document.xml").decode("utf-8")
    styles = z.read("word/styles.xml").decode("utf-8")
    names = z.namelist()

    m = re.search(r'<w:pgSz w:w="(\d+)" w:h="(\d+)"', doc)
    if not m or (m.group(1), m.group(2)) != ("11906", "16838"):
        rep.err(f"page size is not A4: {m.groups() if m else None}")
    mar = re.search(r'<w:pgMar ([^>]*)/>', doc)
    if not mar or not all(f'w:{k}="1134"' in mar.group(1) for k in ("top", "bottom", "left", "right")):
        rep.err("page margins are not 2 cm (1134 DXA)")
    if f'w:ascii="{FONT}"' not in styles:
        rep.err(f"default body font is not {FONT}")
    fonts_used = set(re.findall(r'w:ascii="([^"]+)"', doc))
    other = fonts_used - {FONT, MONO}
    if other:
        rep.err(f"unexpected fonts in runs: {sorted(other)}")
    rep.info["code_runs"] = doc.count(f'w:ascii="{MONO}"')

    # embedded D2Coding
    if rep.info["code_runs"]:
        ft = z.read("word/fontTable.xml").decode("utf-8") if "word/fontTable.xml" in names else ""
        km = re.search(r'w:name="D2Coding".*?w:fontKey="\{([0-9A-Fa-f-]+)\}"', ft, re.S)
        rel = re.search(r'w:name="D2Coding".*?<w:embedRegular[^>]*r:id="([^"]+)"', ft, re.S)
        if not (km and rel):
            rep.warn("D2Coding is not embedded; recipients without the font see a fallback for inline code")
        else:
            rels = z.read("word/_rels/fontTable.xml.rels").decode("utf-8")
            target = re.search(rf'Id="{rel.group(1)}"[^>]*Target="([^"]+)"', rels) or re.search(rf'Target="([^"]+)"[^>]*Id="{rel.group(1)}"', rels)
            data = bytearray(z.read("word/" + target.group(1)))
            key = km.group(1).replace("-", "")
            kb = [int(key[30 - 2 * i: 32 - 2 * i], 16) for i in range(16)]
            for i in range(32):
                data[i] ^= kb[i % 16]
            if bytes(data[:4]) not in (b"\x00\x01\x00\x00", b"true", b"OTTO"):
                rep.err("embedded D2Coding does not de-obfuscate to a font file")

    # accent bars: thick left borders on paragraphs or cells
    if re.search(r"<w:pBdr>.*?<w:left [^>]*w:sz=\"(1[2-9]|[2-9]\d)\"", doc, re.S) or re.search(r"<w:tcBorders>(?:(?!</w:tcBorders>).)*<w:left [^>]*w:sz=\"(1[2-9]|[2-9]\d)\"", doc, re.S):
        rep.err("box with a left accent bar found (style: shaded box with a thin outline only)")

    # walk body children: paragraphs and tables in order
    body = doc[doc.index("<w:body>") + 8: doc.rindex("</w:body>")]
    items = []
    depth, i, start = 0, 0, None
    for mm in re.finditer(r"<w:tbl>|</w:tbl>|<w:p[ >].*?</w:p>|<w:p/>", body, re.S):
        tok = mm.group(0)
        if tok == "<w:tbl>":
            if depth == 0:
                start = mm.start()
            depth += 1
        elif tok == "</w:tbl>":
            depth -= 1
            if depth == 0:
                items.append(("tbl", body[start: mm.end()]))
        elif depth == 0:
            items.append(("p", tok))
    fig_n = tab_n = 0
    h2s, note_titles, tables, lead = [], [], [], []
    for k, (kind, xml) in enumerate(items):
        if kind == "p" and re.match(r"(그림|표) \d+\. ", texts(xml)) and nxt_is_note(items, k):
            note = items[k + 1][1]
            centered = '<w:jc w:val="center"/>' in note
            if (vlen(texts(note).strip()) <= NOTE_ONE_LINE) != centered:
                rep.err(f"caption note alignment: {'centered' if centered else 'left'} but {vlen(texts(note).strip()):.0f} vlen "
                        f"(center when <= {NOTE_ONE_LINE}, left when longer): {texts(note)[:40]!r}")
        if not h2s and kind == "p" and '<w:pStyle w:val="Heading1"/>' not in xml:
            lead.append(texts(xml))
        nxt = next((x for x in items[k + 1:] if not (x[0] == "p" and not texts(x[1]).strip() and "<w:drawing>" not in x[1])), None)
        if kind == "p" and "<w:drawing>" in xml:
            cap = texts(nxt[1]) if nxt and nxt[0] == "p" else ""
            mc = re.match(r"그림 (\d+)\. ", cap)
            if not mc:
                rep.err(f"image without a '그림 N.' caption right below it (next text: {cap[:40]!r})")
            else:
                fig_n += 1
                if int(mc.group(1)) != fig_n:
                    rep.err(f"figure numbering jumps: expected 그림 {fig_n}, found 그림 {mc.group(1)}")
        elif kind == "tbl":
            fills = set(re.findall(r'w:fill="([0-9A-Fa-f]{6})"', xml))
            if NOTE_FILL in fills and xml.count("<w:tc>") == 1:
                t = re.search(r"<w:p[ >].*?</w:p>", xml, re.S)
                if t and "<w:b/>" in t.group(0):
                    note_titles.append(texts(t.group(0)))
                continue
            if CODE_FILL in fills and xml.count("<w:tc>") == 1:
                continue
            parsed = docx_table(xml)
            if parsed:
                tables.append(parsed)
            cap = texts(nxt[1]) if nxt and nxt[0] == "p" else ""
            mc = re.match(r"표 (\d+)\. ", cap)
            if not mc:
                rep.warn(f"table without a '표 N.' caption right below it (first cells: {texts(xml)[:40]!r})")
            else:
                tab_n += 1
                if int(mc.group(1)) != tab_n:
                    rep.err(f"table numbering jumps: expected 표 {tab_n}, found 표 {mc.group(1)}")
        elif kind == "p" and '<w:pStyle w:val="Heading1"/>' in xml:
            h2s.append(texts(xml))
    nums = [re.match(r"(\d+)\. ", h) for h in h2s]
    if h2s and all(nums):
        if [int(x.group(1)) for x in nums] != list(range(1, len(h2s) + 1)):
            rep.err(f"section numbers are not 1..N: {[h[:12] for h in h2s]}")
    rep.info.update(figures=fig_n, tables=tab_n, sections=len(h2s), headings=h2s, note_titles=note_titles)

    hdr = "".join(z.read(n).decode("utf-8") for n in names if re.match(r"word/footer\d*\.xml", n))
    if "PAGE" not in hdr or "NUMPAGES" not in hdr:
        rep.err("footer has no 'page / total' field")
    if 'w:wordWrap w:val="0"' not in styles and 'w:wordWrap w:val="false"' not in styles:
        rep.warn("Korean word-unit line breaking (w:wordWrap=0) is not set in the default paragraph style")

    alltext = texts(doc)
    table_rule_errors(rep, tables)
    term_warnings(rep, alltext)
    structure_warnings(rep, [re.sub(r"^\d+\.\s*", "", h) for h in h2s], note_titles)
    poc_warnings(rep, tables, " ".join(lead))
    return rep


def nxt_is_note(items, k):
    """the paragraph right after a caption is a caption note when it is small muted text (size 16, color 6B7280)."""
    if k + 1 >= len(items) or items[k + 1][0] != "p":
        return False
    x = items[k + 1][1]
    return bool(texts(x).strip()) and 'w:val="6B7280"' in x and '<w:sz w:val="16"/>' in x


# ---------------------------------------------------------------- html
class Walker(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack, self.text, self.h2s, self.note_titles, self.caps, self.imgs = [], [], [], [], [], []
        self.cur = None
        self.style = ""
        self.tables, self.row, self.cell, self.capnotes, self.lead = [], None, None, [], []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        cls = a.get("class", "") or ""
        if tag in ("img", "br", "meta", "link", "input"):
            if tag == "img":
                self.imgs.append(a.get("src", "")[:30])
            if tag == "br" and self.cell is not None:
                self.cell["br"] = True
            return
        self.stack.append((tag, cls))
        if tag == "table":
            self.tables.append(([], []))
        elif tag == "tr" and self.tables:
            self.row = []
        elif tag in ("th", "td") and self.row is not None:
            self.cell = {"tag": tag, "text": [], "br": False, "ctr": "ctr" in cls.split()}
        elif tag == "p" and "br-capnote" in cls.split():
            self.cell_note = {"one": "one" in cls.split(), "text": []}
        if tag == "h2" or "br-note-title" in cls.split() or tag == "figcaption" or tag == "style":
            self.cur = [tag if tag != "p" else "note", []]

    def handle_endtag(self, tag):
        if tag in ("th", "td") and self.cell is not None:
            self.row.append(self.cell)
            self.cell = None
        elif tag == "tr" and self.row is not None and self.tables:
            head, body = self.tables[-1]
            if self.row and all(c["tag"] == "th" for c in self.row) and not head:
                head.extend(("".join(c["text"]), c["br"], c["ctr"]) for c in self.row)
            else:
                body.append(["".join(c["text"]) for c in self.row])
            self.row = None
        elif tag == "p" and getattr(self, "cell_note", None) is not None:
            self.capnotes.append((self.cell_note["one"], "".join(self.cell_note["text"])))
            self.cell_note = None
        while self.stack:
            t, cls = self.stack.pop()
            if t == tag:
                break
        if self.cur and (tag == self.cur[0] or (self.cur[0] == "note" and tag == "p")):
            s = "".join(self.cur[1]).strip()
            if self.cur[0] == "h2":
                self.h2s.append(s)
            elif self.cur[0] == "note":
                self.note_titles.append(s)
            elif self.cur[0] == "figcaption":
                self.caps.append(s)
            elif self.cur[0] == "style":
                self.style = s
            self.cur = None

    def handle_data(self, d):
        if self.cell is not None:
            self.cell["text"].append(d)
        if getattr(self, "cell_note", None) is not None:
            self.cell_note["text"].append(d)
        if not self.h2s and not any(t in ("style", "script", "title") for t, _ in self.stack):
            self.lead.append(d)
        if self.cur:
            self.cur[1].append(d)
        if not any(t in ("style", "script") for t, _ in self.stack):
            self.text.append(d)


def check_html(path):
    rep = Report(str(path))
    src = Path(path).read_text(encoding="utf-8")
    w = Walker()
    w.feed(src)
    if not src.lstrip().lower().startswith("<!doctype html>"):
        rep.err("missing <!doctype html>")
    if '<meta name="viewport"' not in src:
        rep.err("missing viewport meta")
    faces = re.findall(r"@font-face\s*\{[^}]*?font-family:\s*['\"]?([^'\";]+)['\"]?\s*;[^}]*?font-weight:\s*(\d+)", src)
    rep.info["font_faces"] = faces
    if not any(f == FONT for f, _ in faces):
        rep.warn(f"{FONT} is not embedded; the page falls back to locally installed fonts")
    if re.search(r'<(img|script|link)[^>]+(src|href)="https?://', src):
        rep.warn("external resources referenced; the HTML is meant to be standalone")
    if "prefers-color-scheme:dark" not in src.replace(" ", ""):
        rep.warn("no dark mode tokens")
    if re.search(r"border-left:\s*[3-9]px", src):
        rep.err("left accent bar in CSS")
    figs = [c for c in w.caps if c.startswith("그림")]
    tabs = [c for c in w.caps if c.startswith("표")]
    for label, caps in (("그림", figs), ("표", tabs)):
        got = [int(re.match(rf"{label}\s*(\d+)\.", c).group(1)) for c in caps if re.match(rf"{label}\s*(\d+)\.", c)]
        if got != list(range(1, len(got) + 1)):
            rep.err(f"{label} numbering is not 1..N: {got}")
    if len(w.imgs) != len(figs):
        rep.err(f"{len(w.imgs)} images but {len(figs)} figure captions")
    rep.info.update(figures=len(figs), tables=len(tabs), sections=len(w.h2s), headings=w.h2s, note_titles=w.note_titles)
    for one, t in w.capnotes:
        if (vlen(t.strip()) <= NOTE_ONE_LINE) != one:
            rep.err(f"caption note alignment class: {'one' if one else 'none'} but {vlen(t.strip()):.0f} vlen: {t[:40]!r}")
    text = "".join(w.text)
    table_rule_errors(rep, [t for t in w.tables if t[0]])
    term_warnings(rep, text)
    structure_warnings(rep, [re.sub(r"^\d+\.\s*", "", h) for h in w.h2s], w.note_titles)
    poc_warnings(rep, [t for t in w.tables if t[0]], "".join(w.lead))
    return rep


def main():
    global PROFILE
    argv = sys.argv[1:]
    if "--profile" in argv:
        i = argv.index("--profile")
        PROFILE = argv[i + 1] if i + 1 < len(argv) else ""
        del argv[i: i + 2]
    if PROFILE not in ("benchmark", "poc"):
        print("--profile must be benchmark or poc")
        return 2
    args = [a for a in argv if not a.startswith("--")]
    as_json = "--json" in argv
    if not args:
        print(__doc__)
        return 2
    reps = []
    for f in args:
        reps.append(check_docx(f) if f.endswith(".docx") else check_html(f))
    if len(reps) == 2:
        a, b = reps
        for k in ("figures", "tables", "sections"):
            if a.info.get(k) != b.info.get(k):
                b.err(f"{k} differ between files: {a.info.get(k)} vs {b.info.get(k)}")
    if as_json:
        print(json.dumps([{"file": r.name, "errors": r.errors, "warnings": r.warns, "info": r.info} for r in reps], ensure_ascii=False, indent=1))
    else:
        for r in reps:
            print(f"== {r.name}")
            print(f"   sections={r.info.get('sections')} figures={r.info.get('figures')} tables={r.info.get('tables')}")
            for e in r.errors:
                print(f"   ERROR {e}")
            for x in r.warns:
                print(f"   WARN  {x}")
            if not r.errors and not r.warns:
                print("   OK")
    return 1 if any(r.errors for r in reps) else 0


if __name__ == "__main__":
    sys.exit(main())
