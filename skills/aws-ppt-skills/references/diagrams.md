# Charts and Diagrams in aws-ppt-skills Decks

Read this when a slide needs a graph, an AWS architecture, or a structure diagram.

## 1. Routing

Decide in this order:

1. **Numbers across categories or time** (comparison, trend, share, correlation, schedule) → native chart with `addNativeChart()`. Never insert a picture of a graph.
2. **AWS architecture or cloud infrastructure** (services, VPC/subnets, data path between AWS services) → `/my-plugins:aws-diagram`.
3. **Any other structure in the slide content** (process, decision, sequence, timeline, ownership, hierarchy, overlap, positioning) → `/my-plugins:aws-diagram-design`. Its §3 selection (semantic pattern, then visual type) is the step that reads the content and decides the form.
4. **Two to four elements in a simple compare or stack** → keep the native helpers (`addSplitCompare`, `addBudgetBars`, 4-layer and step-flow patterns).

If `/my-plugins:aws-diagram-design` selects one of its chart types (bar, line, scatter, Gantt, radar), keep its type choice and emphasis, then build the chart natively from the same data.

## 2. Native charts - `addNativeChart(s, kind, data, opts)`

pptxgenjs writes a real PowerPoint chart plus an embedded Excel workbook, so the user can right-click > Edit Data and change values, series or labels later.

| kind | Use for | Notes |
|---|---|---|
| `col` / `bar` | category comparison (vertical / horizontal) | single series: one neutral color, `highlight` category in the accent |
| `stackedCol` / `stackedBar` / `percentCol` | composition, part of a whole across categories | first series is the accent by default |
| `line` / `area` | trend over time | first series accent, others gray |
| `doughnut` / `pie` | share of one total, 5 slices or fewer | labels in percent (`0%`), legend at the bottom |
| `scatter` | correlation of two variables | `data[0].values` = X values, next series = Y values |
| `radar` | 3 to 5 criteria across a few entities | keep to 2-3 series |

- `data` uses the pptxgenjs shape: `[{ name, labels: [...], values: [...] }]`.
- `opts`: `{ x, y, w, h, highlight, showValues, showLegend, valueFormat, valMin, valMax, title, colors, raw }` in design units. `highlight` is the accent index: a category for single-series col/bar/pie/doughnut (default: the largest value), a series otherwise (default: 0). `raw` passes any other pptxgenjs chart option.
- 50명 미만 (`AUDIENCE = "small"`): accent on the highlight only, everything else `C.chartNeutral` / `C.chartGrays`. 100명 이상 (`"large"`): the theme's multi-color accents.
- Default box is the body zone `(0.42, 1.50, 9.16 x 2.95)`. Two charts side by side: `w 5.30` + `w 3.68` with a 0.18 gap.
- Axis, legend and data labels use `NanumSquareOTF Bold` at 10pt design (13pt output) in `C.slate`; gridlines `C.chartGrid`; plot and chart areas stay transparent so the template background shows.
- **Gantt**: `stackedBar` with an offset series and a duration series, the offset painted as the background:

```javascript
addNativeChart(s, "stackedBar", [
  { name: "시작", labels: ["설계", "구축", "검증"], values: [0, 2, 5] },
  { name: "기간", labels: ["설계", "구축", "검증"], values: [2, 3, 2] },
], { colors: [C.bg, C.subtitleOrange], showValues: false, showLegend: false,
     raw: { catAxisOrientation: "maxMin", valAxisTitle: "주차", showValAxisTitle: true } });
```

## 3. AWS architecture - `/my-plugins:aws-diagram`

1. Invoke `/my-plugins:aws-diagram` with the Skill tool and follow it: read its `references/diagram_guide.md`, look up every icon with `find_icon.py`, compose the SVG with `bundle:` hrefs, run `embed.py`.
2. Deck settings on top of its guide:
   - Root `font-family="'NanumSquareOTF Bold', 'NanumSquareOTF_ac', sans-serif"`.
   - A full-canvas background rect in the slide color as the first drawn element: `#000000` (black theme) or `#FFFFFF` (white theme). Never leave a dark-theme diagram transparent: viewers that draw transparency as white would hide its light labels. `apply_template.py` adds the rect if it is missing and flattens the PNG fallback onto the same color.
   - viewBox matching the target box (full body 9.16 x 3.00 design ≈ 3:1, e.g. `0 0 1200 400`; half width 4.5 x 3.0 ≈ 3:2, e.g. `0 0 900 600`). Labels 16-17px, sublabels 13px at that size.
3. Theme overrides:

| Element | Black theme | White theme |
|---|---|---|
| Labels / sublabels | `#E2E4EC` / `#A6ABBE` | `#232F3E` / `#545B64` (guide default) |
| Connectors, AWS Cloud border | `#A6ABBE` | `#232F3E` |
| AWS Cloud group icon | `group/AWS-Cloud_32_Dark` | `group/AWS-Cloud_32` |
| AgentCore icons | `agentcore-light/*` (white strokes) | `agentcore-dark/*` (black strokes) |
| `resource/*` icons (dark glyphs) | on a light chip: `<rect rx="12" fill="#E2E4EC">` behind the icon | as is |
| Subnet fills (borders unchanged) | public `fill="#7AA116" fill-opacity="0.14"`, private `fill="#00A4A6" fill-opacity="0.14"` (no `rgba()`) | guide default |
| Focal label (1 per diagram) | `#FF9900` | `#E06A00` |

   The AgentCore set names describe the icon color, not the background: `agentcore-dark` icons are drawn in black (light slides), `agentcore-light` icons in white (dark slides). The `/my-plugins:aws-diagram` guide's "Dark backgrounds" table uses the same values.
4. `python3 "$SKILL_DIR/scripts/svg_to_png.py" arch.svg arch.png --background 000000` (`FFFFFF` on the white theme), then `addDiagram(s, { svg: "arch.svg", png: "arch.png", x, y, w, h, alt })`.

## 4. Structure diagrams - `/my-plugins:aws-diagram-design`

1. Invoke the skill. Use its §3 selection to read the slide content and pick the semantic pattern and visual type; load that `references/type-*.md`.
2. Style-guide gate: choose option (b) "extract from an installed skill" with this skill (`aws-ppt-skills`), or option (d) custom tokens with the table in §5.
3. Variant: **Minimal dark** for the black theme, **Minimal light** for the white theme. No dot pattern, no outer container panel.
4. Size: custom viewBox matching the target box (see §3 step 2), detail `balanced` (12 nodes or fewer), audience `engineer` for 50명 미만, `mixed` or `executive` for 100명 이상.
5. Export the diagram-only SVG with its export procedure (`references/export.md`), keep its full-canvas background in the slide color (`paper`), then `svg_to_png.py ... --background <slide color>` and `addDiagram()`.

## 5. Theme skin tokens (semantic roles for `/my-plugins:aws-diagram-design`)

| Role | Black theme | White theme |
|---|---|---|
| `paper` (page background, full-canvas rect) | `#000000` | `#FFFFFF` |
| `paper-2` (node / container fill) | `#161D26` | `#F3F3F7` |
| `ink` (primary text, primary stroke) | `#FFFFFF` | `#161D26` |
| `muted` (secondary text, default arrows) | `#A6ABBE` | `#545B64` |
| `soft` (sublabels, boundary labels) | `#7B8198` | `#7D8998` |
| `rule` (hairlines) | `#2A3140` | `#DDE1E6` |
| `rule-solid` (strong borders) | `#5E6478` | `#C9CED6` |
| `accent` (1-2 focal nodes) | `#FF9900` | `#E06A00` |
| `link` (API / external arrows) | `#41B3FF` | `#0972D3` |
| Sans font (names, titles, callouts) | `NanumSquareOTF Bold` | `NanumSquareOTF Bold` |
| Mono font (ports, commands, URLs) | `D2Coding` | `D2Coding` |

## 6. Placing a diagram - `addDiagram(s, d)`

- `d = { svg, png, x, y, w, h, alt }` in design units; the PNG is fitted (contain) and centered in the box.
- The picture is named `svg:<file>`; `apply_template.py` embeds that SVG (`asvg:svgBlip`) with the PNG as fallback. Keep the files next to the build script or pass `--assets-dir`.
- The embedded copy is normalized for every viewer: opaque backdrop in the slide color, `xlink:href` next to `href` on `<image>` (older Office SVG renderers), `width`/`height` from the viewBox. The PNG fallback is flattened onto the slide color. The SVG file on disk is not changed.
- Always give `alt` text (one sentence on what the diagram shows).
- A diagram usually replaces the stat band; give it the full body zone `(0.42, 1.45, 9.16 x 3.05)`.

## 7. QA

- `check_deck.py`: every chart has an embedded workbook; every picture without a vector SVG is flagged (a graph there is a rule violation).
- Visual: diagram colors match the theme (no dark labels or black-stroke AgentCore icons on the black theme), labels legible at slide size, one focal accent, no icon drawn by hand.
- Black theme: also look at the PNG fallback over white (`apply_template.py` flattens it; a diagram that disappears there would disappear in some viewers).
