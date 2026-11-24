# Style Guide

**The single source of truth for colors, typography, and tokens.** Every diagram draws from this, not from hex values inlined in other reference files. A skin is one whole copy of this file.

**Shipped skin: AWS brand.** White paper, squid-ink text (`#232F3E`), smile-orange accent, Amazon Ember type, and the official AWS Architecture Icons ([primitive-aws-icons.md](primitive-aws-icons.md)). This file belongs to the AWS edition of the skill: the sync with the source repository never writes it, and it follows the structure of the source's style guide so that every role and section other references name exists here.

Never edit this file in an installed plugin: the folder is the plugin cache (SKILL.md §0). To use another skin, run [`onboarding.md`](onboarding.md) and keep the result as a profile ([`profiles.md`](profiles.md)).

---

## Tokens

### Semantic roles

Every token is referred to by **semantic role**, not by its hex value. Type references (`type-*.md`) and SKILL.md say `accent`, not `#EC7211`.

| Role | Purpose | Default (light) | Default (dark) |
|---|---|---|---|
| `paper` | Page background, default node fill | `#FFFFFF` (white, the background of official AWS diagrams) | `#161E2D` (dark squid) |
| `paper-2` | Diagram container bg, secondary fill | `#F2F3F3` | `#232F3E` (squid ink) |
| `ink` | Primary text, primary stroke | `#232F3E` (squid ink) | `#FFFFFF` |
| `ink-strong` | High-contrast text on accent fills | `#16191F` | `#16191F` |
| `muted` | Secondary text, default arrow stroke | `#545B64` | `#B6BEC9` |
| `soft` | Boundary labels, large or non-text marks | `#7D8998` | `#8D99A8` |
| `rule` | Hairline borders | `rgba(35,47,62,0.12)` | `rgba(255,255,255,0.12)` |
| `rule-solid` | Stronger borders, baselines | `#D5DBDB` | `rgba(255,255,255,0.25)` |
| `accent` | Focal / 1–2 max per diagram | `#EC7211` (smile orange, dark step) | `#FF9900` (smile orange) |
| `accent-tint` | Fill for accent-bordered boxes | `rgba(255,153,0,0.10)` | `rgba(255,153,0,0.14)` |
| `link` | HTTP/API calls, external arrows | `#0972D3` (Cloudscape blue) | `#539FE5` |

> **Brand palette source:** AWS brand: `squid ink #232F3E`, `smile orange #FF9900`, white. Pure `#FF9900` reads weakly as a thin stroke on white, so the light `accent` is the darker step `#EC7211`, the orange AWS uses on light UI; `#FF9900` is the accent on dark and the base of `accent-tint`. `muted`, `soft`, `rule-solid` and `link` come from the AWS and Cloudscape grey-blue ramp. Category identity colors (`#ED7100`, `#8C4FFF`, …) belong to the icons and zone borders ([primitive-aws-icons.md](primitive-aws-icons.md)) and are **not** editorial accents.

> **Examples.** The `assets/example-*.html` files are the source's examples in the source's own skin (white-smoke paper, serif titles, web fonts, smaller type), and some predate rules the documents now state. Read an example for how a type is arranged; every rule comes from SKILL.md and the type reference, and every token, font and size from this file.

### Contrast contract

Every token must clear the threshold for each role it plays, against the background it actually sits on, in both skins.

| Use | Minimum vs. its actual background |
|---|---|
| Regular text | 4.5:1 |
| Large text (24px+, or 18.7px+ at weight 600+) | 3:1 |
| Essential non-text marks: lines, arrows, borders, focus outlines, data points | 3:1 against the adjacent color |
| Decorative rules and translucent tints (`rule`, `rule-solid`, `paper-2`, `accent-tint`, fills at opacity) | No minimum, but never the only carrier of meaning |

Measured values of this skin (WCAG 2.x ratio against `paper`):

| Token | Light, on `#FFFFFF` | Dark, on `#161E2D` |
|---|---|---|
| `ink` | 13.57:1 | 16.70:1 |
| `muted` | 6.87:1 | 8.90:1 |
| `link` | 4.82:1 | 5.93:1 |
| `soft` | 3.56:1 | 5.77:1 |
| `accent` | 3.01:1 | 7.80:1 |
| `ink-strong` on an `accent` fill at 0.85 | 6.86:1 | 6.30:1 |

- **In the light skin `accent` and `soft` are not text colors.** At 3.01:1 and 3.56:1 they clear the 3:1 of a mark or of large text and miss the 4.5:1 of regular text. Use `accent` for strokes, arrows, borders, dots and the title-size focal word, and `soft` for boundary lines and large zone labels. A label, a value or a sublabel is `ink` or `muted`, also on a focal node. Where a type reference colors text `accent`, keep the stroke or the fill `accent` and set the text in `ink`, or in `ink-strong` on an `accent` fill at 0.85. Where a type reference says the default accent passes as text, that sentence is about the source's skin, not this one.
- **A token used in several roles must pass each one.** Don't assume a token is non-text because it usually is.
- **Translucent colors are composited first.** An `rgba()` fill or stroke is blended over `paper` before its ratio is measured. A value that clears the bar at full strength can fail at 0.5 opacity.
- **Surfaces other than `paper` cost contrast.** Inside an `accent-tint` box or on `paper-2` every ratio drops. Measure text placed there against that surface.

### Inversion rule (light → dark)

Any `rgba(35,47,62, X)` in light becomes `rgba(255,255,255, X)` in dark. Same opacities, RGB flipped. The accent brightens from `#EC7211` to pure `#FF9900` on dark paper.

### Series palette (multi-series chart types only)

For chart types that need to distinguish several overlapping entities (radar and the other multi-series charts), use the AWS category ramp. The "1-focal" rule still holds: `accent` is reserved for the focal series and the palette below covers the rest.

| Token | Light | Dark | Notes |
|---|---|---|---|
| `series-1` | `#8C4FFF` (purple) | `#A97FFF` | Non-focal series |
| `series-2` | `#01A88D` (teal) | `#2BC0A8` | Non-focal series |
| `series-3` | `#7AA116` (green) | `#96BE3C` | Non-focal series |
| `series-4` | `#C925D1` (magenta) | `#D95CDF` | Non-focal series |
| `series-5` | `#DD344C` (red) | `#E5626F` | Non-focal series |

Fills sit at `0.14` opacity light, `0.20` dark; strokes use the full color. **Don't backfill these tokens to non-chart types**: architecture, swimlane and the rest keep muted-ink variants.

### Terminal skin (opt-in alternate)

A self-contained palette for the terminal-window primitive (see [primitive-terminal.md](primitive-terminal.md)), a CLI-chrome register for dev-tool posts and technical social cards. It does not replace the skin above and isn't affected by onboarding; it is a second, fixed skin you opt into per diagram.

| Token | Hex | Purpose |
|---|---|---|
| `terminal-page` | `#0a0a0a` | Page background behind the window |
| `terminal-paper` | `#141414` | Window body, node fill |
| `terminal-bar` | `#1b1b1b` | Titlebar strip |
| `terminal-border` | `#2b2b2b` | Window border, hairlines |
| `terminal-ink` | `#f5f5f5` | Primary text, primary stroke |
| `terminal-muted` | `#9a9a9a` | Secondary text, sublabels, ring stroke |
| `terminal-soft` | `#5c5c5c` | Tertiary: inactive dots, spokes |
| `terminal-accent` | `#ff5a36` | The one accent: focal station, prompt sign, active dot |
| `terminal-accent-tint` | `rgba(255,90,54,0.12)` | Fill for accent-bordered boxes |

**1-accent rule still holds.** Everything that isn't `terminal-ink`, `terminal-muted` or `terminal-soft` is `terminal-accent`; never introduce a second hue.

---

## Typography

| Role | Family | Size | Weight | Usage |
|---|---|---|---|---|
| `title` | Amazon Ember | 1.75rem | 700 | Page H1 |
| `node-name` | Amazon Ember | 13px | 600 | Human-readable labels |
| `sublabel` | Amazon Ember Mono | 11px | 400 | Port, protocol, URL, field type |
| `eyebrow` | Amazon Ember Mono | 7–8px | 500, tracked 0.18em, uppercase | Type tags, axis labels the diagram reads without |
| `arrow-label` | Amazon Ember Mono | 10px | 400, tracked 0.04em | Arrow annotations, legend text, notes |
| `callout` | Amazon Ember *italic* | 14px | 400 | Editorial asides only |

These sizes hold up when a 1280-wide diagram is exported to PNG and scaled to a README or a blog column; 12 / 9 / 8px did not. They are the standard ramp of this edition ([output-spec.md](output-spec.md) carries the same numbers); a type reference or an example that shows 12 / 9 / 8 predates them. The presentation ramp (16 / 12 / 12) is unchanged.

**Size boxes from their text.** Budget 0.60em per character for the sans, 0.62em for the mono and 1em for every wide character such as Hangul: the source's budget, which `scripts/self_check.py` applies. The bundled faces fit inside it: Amazon Ember Mono advances 0.60em and Amazon Ember about 0.57em on average over letters, digits and the space (measured from the TTF files). Keep 12px clear between the longest sublabel and the box's right edge; shorten the text or widen the box before a line touches the border. A label mask for 10px text is 14px tall (baseline −11 to +3).

**Separators.** Never use the middle dot `·` (U+00B7) in visible text: labels, sublabels, chips, legends, notes, captions, zone titles. Use `/` for a pair or an alternative (`401 / 429`, `CloudWatch / X-Ray`), a comma between the fields of one item (`AVA-201, priya`) and in a list (`Guardrail, claude-auto, EMF`), and a plain space between a path and its subject (`llm-gateway /inference`). `scripts/aws_check.py` fails on a middle dot in SVG text.

### Font stack

```css
/* sans: names, titles, callouts */ font-family: 'Amazon Ember', 'Helvetica Neue', Helvetica, Arial, sans-serif;
/* mono: technical content       */ font-family: 'Amazon Ember Mono', ui-monospace, monospace;
```

There is no font `<link>`. Amazon Ember is not on Google Fonts; the skill bundles it at [`assets/fonts/`](../assets/fonts/) and `/my-plugins:setup` installs the TTFs into the user's font folder.

Installed faces: Amazon Ember Light 300, Regular 400 (and italic), Medium 500, Bold 700, Heavy 800; Amazon Ember Mono Regular 400 and Bold 700. A 600 node name renders in Bold where only the installed faces answer, and a 500 or 600 mono spec snaps to 400 or 700; both are expected. Never fake-bold the Heavy face.

### Font source

The font source decides whether a diagram makes any network request. It is a skin setting, so a saved profile carries it too.

Font source: `system`

| Value | What ships | Network |
|---|---|---|
| `web` | A font `<link>`; text renders in the linked web fonts | One stylesheet request, plus the font files |
| `system` (this skin) | No font `<link>`; every family stack resolves to an installed face or falls through to the platform's own faces | None |

In `system` mode:

- Omit the font `<link>` and the export `@import` entirely, and write no CSS `url()`: `scripts/self_check.py` rejects a `url()` that is not a fragment. Keep every `font-family` stack as written; each ends in a generic family, so a viewer without Amazon Ember gets Helvetica, Arial or the system monospace.
- A fallback face has different metrics, so keep the label padding and the 12px clearance rather than trimming boxes to the Ember measurement.
- Export with `python3 scripts/export_svg.py <file> --system-fonts`, and verify with `python3 scripts/self_check.py --offline <file>`, which fails if a Google Fonts link is present.
- To map weight 600 to the Medium face, an `@font-face` rule may name installed faces with `local()` only: [`assets/fonts/README.md`](../assets/fonts/README.md).

A profile whose brand font is a web font sets `web` and carries its own `<link>`; the rest of this section then follows the source's rules for that mode.

### Korean labels

Amazon Ember carries no Hangul. A Korean `<text>` element extends its own family, never the skin:

```svg
<text font-family="'Amazon Ember', 'Noto Sans KR', 'Noto Sans CJK KR', 'Apple SD Gothic Neo', 'Malgun Gothic', sans-serif">결제 서비스</text>
```

The Korean faces are installed fonts like the rest of this skin (`/my-plugins:setup` checks for Noto Sans CJK KR and installs it), so the same file renders with a Noto face where one is installed and with Apple SD Gothic Neo or Malgun Gothic elsewhere. A page title takes the same stack.

**Width budget.** Measure per character, not per script: **every Unicode wide or full-width character costs 1em, every other character costs its face's Latin advance** (0.60em sans, 0.62em mono), and nonspacing marks cost nothing. Sum over the string, multiply by the font size, add padding and round the box up to the next multiple of 4. `scripts/self_check.py` applies the source's budget (0.60em sans, 0.62em mono), plus any letter-spacing, to text inside a visible box and fails a label that runs more than 0.3em past the box edge. Padding, rounding and labels on paper-colored arrow-label masks are not checked, so those stay yours to hold.

Counting by script is the trap. `주문 v2.1` is two full-width syllables and five narrow characters; a formula that tallies Hangul, Latin letters and spaces drops `2`, `.` and `1` and sizes the box for four of its seven characters.

Three rules follow from Hangul metrics:

- **Sublabels stay Latin.** Ports, protocols, field types and URLs are Latin anyway: keep Amazon Ember Mono there and don't translate them. Hangul has no mono face to fall back to.
- **Floor of 12px.** Hangul goes muddy below 12px. If a Korean name doesn't fit at 12px, cut the name; don't shrink the type.
- **Arrow labels, eyebrows and legend text switch register.** Those slots are small uppercase tracked mono, which Hangul has neither a face nor legibility for. A Korean label in one of those slots is 12px sans at weight 500 with no tracking and no uppercase transform, and its mask rect grows to match (16px tall, width from the budget above, rounded to a multiple of 4). Latin labels in the same diagram keep the mono treatment.

**Load-bearing rule:** Mono is for *technical* content (ports, commands, URLs, field types). Names, titles and callouts go in Amazon Ember. Italic Ember is reserved for annotation callouts (see [primitive-annotation.md](primitive-annotation.md)). **Never JetBrains Mono** as a blanket "dev" font. This skin has no serif: AWS brand typography is one family.

### Traditional Chinese labels

Amazon Ember carries no Han. A Chinese `<text>` element extends its own family, never the skin:

```svg
<text font-family="'Amazon Ember', 'Noto Sans TC', 'PingFang TC', 'Microsoft JhengHei', sans-serif">請求項比對</text>
```

The width budget above is unchanged, and full-width punctuation (`（）「」，。：`) costs 1em as well. The three Hangul rules apply as they stand: sublabels stay Latin, 12px is the floor, and arrow labels, eyebrows and legend text switch to 12px sans at weight 500. Simplified Chinese takes the same rules with `'Noto Sans SC'`, `'PingFang SC'`, `'Microsoft YaHei'`.

### Cyrillic labels

Whether the installed Amazon Ember faces carry Cyrillic has not been checked for this skin. Extend the family of a Cyrillic `<text>` element with a face that does, `'Amazon Ember', 'Noto Sans', Arial, sans-serif` for names and `'Amazon Ember Mono', 'Noto Sans Mono', ui-monospace, monospace` for technical text, and measure a Cyrillic name in the browser: wide letters (`Ж Ш Щ Ю Ы`) run past the 0.60em average.

**Preserve printed labels.** A label the reader matches against a physical thing (a cabinet, a splice closure, a port map) carries the exact printed string. Don't transliterate it and don't re-case it; in an uppercase slot, drop the transform for that label.

---

## Stroke, radius, spacing

| Token | Value | Use |
|---|---|---|
| `stroke-thin` | `0.8` | Tag-box outlines, leaf nodes |
| `stroke-default` | `1` | Most strokes |
| `stroke-strong` | `1.2` | Emphasis strokes |
| `radius-sm` | `4` | Small tags |
| `radius-md` | `6` | Node boxes |
| `radius-lg` | `8` | Containers, rings |
| `grid` | `4` | Every coord, size, and gap is divisible by 4 (hard rule) |

---

## Node type → treatment

Semantic role combinations; reference these by name in type specs.

| Type | Fill | Stroke |
|---|---|---|
| `focal` (1–2 max) | `accent-tint` | `accent` |
| `backend` | `#ffffff` (white) | `ink` |
| `store` | `ink @ 0.05` | `muted` |
| `external` | `ink @ 0.03` | `ink @ 0.30` |
| `input` | `muted @ 0.10` | `soft` |
| `optional` | `ink @ 0.02` | `ink @ 0.20` dashed `4,3` |
| `security` | `#DD344C @ 0.05` | `#DD344C @ 0.60` dashed `4,4`, the AWS Security-Identity red |

The red of `security` is for a security boundary. A type reference that borrows the `security` treatment for another meaning, such as a blocked card or a warning, uses `accent @ 0.05` with an `accent` stroke dashed `4,4`.

AWS-specific node and zone treatments (service-icon nodes, VPC, subnet and account containers) are specified in [primitive-aws-icons.md](primitive-aws-icons.md); zone-border identity colors don't count against the accent budget.

---

## Customizing the skin

Three options, none of which writes this file:

1. **Run onboarding**: see [`onboarding.md`](onboarding.md). Give a URL, an installed skill or a folder; the skill extracts the palette and fonts and saves the result as a profile.
2. **Brand handoff**: paste your design-token JSON, map its tokens to the semantic roles above and save the result as a profile.
3. **Client profiles**: save and switch named skins, or bind one to a project, using [`profiles.md`](profiles.md).

### Constraints (don't break these)

- **Contrast**: hold every token to the [contrast contract](#contrast-contract) for the role it plays. A token under 4.5:1 on `paper` is not a text color.
- **One accent**: pick one color for `accent`. Two accents erase the focal signal. AWS icon and zone identity colors are exempt: they are identity marks, not accents.
- **No rainbow palette**: if a brand ships 8 colors, pick 3 (paper, ink, accent). The rest become `muted` variants.
- **Families**: three at most. The AWS skin runs sans and mono, Amazon Ember and Amazon Ember Mono; brand consistency outweighs the serif and sans contrast of the source's skin.
- **Paper**: the AWS skin uses pure white because official AWS architecture diagrams do. For another skin prefer a warm neutral (cream, bone, light grey); pure white without a brand mandate turns the design sterile.
- **Dot pattern is optional, not default**: the 22×22 dot pattern is an opt-in "dotted paper" variant. The default background is a clean `paper` fill. When the pattern is on, it sits at about 10% opacity of `ink` on `paper`.
- **Container is clean by default**: the diagram sits directly on the page paper, with no secondary container background or border. A framed variant (`paper-2` bg, `rule` border, 8px radius, padding) is an opt-in for card-heavy layouts.
