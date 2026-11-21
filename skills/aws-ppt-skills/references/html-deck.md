# HTML Deck

The HTML deck is the finished `.pptx` converted into one `.html` file that is presented in a browser. Read this
file when the output format is `HTML만` or `PPT와 HTML 둘 다`. The slides, their order and the notes are the
deck's: the page is converted, never written.

```
build_<deck>.js → <DeckName>_raw.pptx → apply_template.py → <DeckName>.pptx → check_deck.py, render QA
                                                                  └→ deck_to_html.py → <DeckName>.html → preview_html_deck.py
```

## What the page carries

| In the deck | In the page |
|---|---|
| Text boxes, shapes (rectangle, rounded rectangle, ellipse, line with arrowheads, triangle, diamond, chevron, arrows, hexagon and other common polygons) | HTML elements at the same position and size. Text can be selected and searched |
| Native tables (`s.addTable()`, `addGrid()`) | `<table>` with the same column widths, fills and borders |
| Native charts (`addNativeChart()`: col, bar, stacked, percent, line, area, pie, doughnut, scatter, radar) | SVG drawn from the chart's own data, colors and number formats |
| Diagram pictures (`addDiagram()`) | The embedded vector SVG, with the fonts it names embedded. Without fontTools the PNG fallback is used |
| Icons (`addIcon()`) and other pictures | The same picture |
| Template chrome: background, AWS logo, copyright, page number, "Thank you!" | Pictures rendered from the template by LibreOffice, one per layout, plus a small patch per page number |
| Speaker notes | Presenter view only. The audience window never shows them |
| Fonts | `NanumSquareOTF Bold` and `D2Coding`, embedded as subsets of the characters the deck uses |

The page is one self-contained file. It loads nothing from the network, so it works from a disk, a mail
attachment, a USB drive or a static host.

## Tools

`deck_to_html.py` needs python-pptx, lxml and Pillow, and for the template chrome LibreOffice (`soffice`) and
Poppler (`pdftoppm`). fontTools is optional: without it the whole font files go into the page (up to about 6 MB more)
and diagrams use their PNG. `preview_html_deck.py` needs uv and Playwright's Chromium. All of them are checked
and installed by the `my-plugins:setup` skill.

## Convert

```bash
python3 "$SKILL_DIR/scripts/deck_to_html.py" <DeckName>.pptx
```

| Option | Use |
|---|---|
| `--out FILE` | Output path. Default: the deck's name with `.html`, next to the deck |
| `--title TEXT` | Page title shown on the browser tab. Default: the largest text of the first slide |
| `--lang ko` or `--lang en` | Language of the controls and the key help. Default: `ko` when the slides have Korean text |
| `--no-notes` | Leave the speaker notes out of the file |
| `--chrome-width N` | Pixel width of the template chrome pictures. Default 1920; 2560 or 3840 for a 4K room (a larger file) |

The input must be the deck after `apply_template.py`. A raw deck is refused, because its slides sit on empty
masters and the page would have no template.

`OK` reports the slide count, the notes, charts, tables and pictures, and the file size. Each `WARN` line names
something the page shows differently from the deck:

| WARN | What to do |
|---|---|
| `도형 '<name>'은(는) 사각형으로 표시했습니다` | The preset shape is not one the page draws. Use a shape from the table above, or accept the rectangle after looking at the slide |
| `그룹 도형은 옮기지 않았습니다` | Build the shapes without a group |
| `차트(...)는 HTML에서 그리지 못해 비워 두었습니다` | The chart kind or its data is not supported. Use a kind from the table above |
| `테마 색(schemeClr)을 쓴 요소는 색을 옮기지 못했습니다` | Take the color from `C` (an RGB value), as the helpers do |
| `글꼴 '<name>'은(는) 스킬에 없어 넣지 못했습니다` | Use `FONT` or `FONT_CODE`. Another font shows only where it is installed |
| `fontTools가 없어 ...` | Run `my-plugins:setup`. The page works, but it is larger and its diagrams are PNG |
| `노트가 없는 슬라이드가 N장 있습니다` | Every slide needs its script (Core Constraints) |
| `다이어그램 SVG가 외부 주소를 참조합니다` | Embed the picture in the SVG. An external address is empty when the room has no network |

Never edit the HTML. Change `build_<deck>.js`, then build, apply the template, lint and convert again.

## Check

```bash
uv run --no-project --with playwright==1.64.1 python "$SKILL_DIR/scripts/preview_html_deck.py" <DeckName>.html --out-dir qa-html
```

It writes `qa-html/<DeckName>-NN.png` for every slide, `<DeckName>-list.png` (the slide list) and
`<DeckName>-presenter.png` (the presenter view), and exits 1 with `WARN` lines when the page script throws, the
page asks the network for a file, a font did not load, the keys do not move the deck, the presenter window does
not follow, or a text box wrapped onto one more line than its box holds.

Compare each `qa-html` picture with the deck's `qa-NN.jpg`. Text, positions, colors and chart values must be the
same. These differences are expected and need no fix:

- LibreOffice puts a small gap between Korean and Latin text; the browser does not, so lines are slightly shorter.
- Chart tick steps, label placement and the doughnut hole follow the page's own drawing, not LibreOffice's.
- LibreOffice may leave bullets out of its picture; the page shows them, as PowerPoint does.

## What the page does not carry

- Animations, transitions and step by step reveals. The deck has none either.
- A light and dark switch. The page has the theme the deck was built with.
- Editing. Charts are drawings without "Edit Data", and text cannot be changed in the page. Changes go through the build.
- Video and audio.
- Drawing tools (pen, highlighter), a slide search and hiding a slide. The page has a laser pointer and the slide list.
- Privacy for the notes. The notes are text inside the file, readable by anyone who opens its source. Convert
  with `--no-notes` for a page that will be published or sent outside, and keep the full page for the presenter.

When the user needs one of these, say so before building and offer the `.pptx`.

## 발표자 안내

Give this guide to the user with the file, in Korean, shortened to what they asked about. The key labels are
the ones the page's own help (key `?`) shows.

### 여는 방법

- `<DeckName>.html` 파일 하나만 있으면 됩니다. 다른 파일이나 인터넷 연결이 필요 없고, 파일을 더블클릭하면 브라우저에서 열립니다.
- Chrome이나 Edge에서 여는 것을 권장합니다. 변환 검사를 Chromium에서 하기 때문입니다. 다른 브라우저를 쓸 때는 발표 장소의 장비에서 미리 한 번 열어 봅니다.
- 화면 아래의 조작 막대는 마우스를 움직이면 나타나고 잠시 뒤 사라집니다.

### 키보드 조작

| 키 | 동작 |
|---|---|
| `→  Space  PageDown` | 다음 슬라이드 |
| `←  PageUp` | 이전 슬라이드 |
| `Home  End` | 처음, 마지막 슬라이드 |
| `숫자 + Enter` | 그 번호의 슬라이드로 이동 |
| `N` | 발표자 보기 창 열기 |
| `F` | 전체 화면 |
| `G` | 슬라이드 목록. 슬라이드를 누르면 그 슬라이드로 이동 |
| `P` | 레이저 포인터 |
| `B` | 화면 가리기. 다시 누르면 돌아옴 |
| `?` | 키 도움말 |
| `Esc` | 목록, 도움말, 레이저 닫기 |

키가 듣지 않으면 슬라이드를 한 번 누른 뒤 다시 누릅니다. 휴대폰과 태블릿에서는 좌우로 밀어 넘깁니다.

### 발표자 보기

1. 청중에게 보일 창에서 `N`을 누릅니다. 발표자 보기 창이 새로 열립니다. 열리지 않으면 브라우저의 팝업 차단을 이 페이지에서 풀고 다시 누릅니다.
2. 발표자 보기 창은 내 화면에, 슬라이드 창은 프로젝터 화면에 놓고 슬라이드 창에서 `F`를 눌러 전체 화면으로 바꿉니다. 화면 설정은 확장으로 둡니다. 복제로 두면 두 화면에 같은 창이 나옵니다.
3. 화상 회의에서는 화면 전체가 아니라 슬라이드 창만 공유합니다. 노트는 발표자 보기 창에만 나옵니다.
4. 어느 창에서 넘겨도 두 창이 함께 움직입니다.

발표자 보기 창에는 현재 슬라이드, 다음 슬라이드, 발표자 노트, 창을 연 뒤 지난 시간, 현재 시각이 나옵니다. `시간 재설정`은 지난 시간을 0으로 돌리고, `A-`와 `A+`는 노트 글자 크기를 바꿉니다. `레이저`를 켜고 현재 슬라이드 위에서 마우스를 움직이면 청중 화면의 같은 자리에 붉은 점이 보입니다. `화면 가리기`는 청중 화면을 검게 가립니다.

### PDF 백업

브라우저의 인쇄에서 "PDF로 저장"을 고르면 슬라이드 한 장이 한 쪽인 PDF가 됩니다. 용지는 16:9로 맞춰져 있고, "배경 그래픽" 옵션을 켭니다. 발표자 노트는 PDF에 들어가지 않습니다.

### 발표 전 확인

1. 발표할 장비와 브라우저에서 파일을 열어 첫 슬라이드와 글꼴을 확인합니다.
2. `→`와 `←`로 넘겨 보고, `N`으로 발표자 보기 창을 열어 노트가 보이는지 확인합니다.
3. 프로젝터 화면에는 슬라이드 창만 보이는지 확인합니다.
4. `G`로 목록을 열어 원하는 슬라이드로 이동해 봅니다.
5. 문제가 생길 때 쓸 `.pptx`나 PDF 백업의 위치를 확인합니다.

### 문제가 생기면

| 증상 | 먼저 할 일 |
|---|---|
| `N`을 눌러도 창이 안 열림 | 브라우저의 팝업 차단을 풀고 다시 누릅니다. 이미 열린 창이 뒤에 있는지 봅니다 |
| 청중 화면에 노트가 보임 | 화면 공유를 멈추고 슬라이드 창만 다시 공유합니다 |
| 두 창이 따로 움직임 | 발표자 보기 창을 닫고 슬라이드 창에서 `N`을 다시 누릅니다 |
| 키가 듣지 않음 | 슬라이드를 한 번 누릅니다. 목록이나 도움말이 열려 있으면 `Esc`로 닫습니다 |
| 화면이 검게 보임 | `B`를 눌러 화면 가리기를 끕니다 |
| 전체 화면에서 나가고 싶음 | `Esc` 또는 `F`를 누릅니다 |

## Handoff

When delivering the page, tell the user in a few lines:

- the file path and size, the slide count, and the theme;
- whether the notes are in the file (`--no-notes` or not), and that anyone with the file can read them;
- the keys that matter first: `N`, `F`, `G`, `P`, `?`;
- the backup: the `.pptx` when both were made, otherwise the PDF made by printing the page;
- that the page was opened and checked in Chromium by `preview_html_deck.py`.

Putting the file on a host (an S3 bucket, GitHub Pages, an internal site) publishes it. Do it only when the user
asks, name the address and who can open it first, and use the `--no-notes` page unless the user says the notes
may be public.
