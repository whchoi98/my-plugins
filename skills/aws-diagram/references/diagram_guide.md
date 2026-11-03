# AWS Architecture Diagram Guide

How to compose a correct, professional AWS architecture diagram using the bundled
official icons. Read this fully before drawing.

## The AWS visual grammar

AWS diagrams are not arbitrary boxes and arrows. They follow a nesting convention
that readers recognize instantly. Respect the containment order:

```
AWS Cloud (group)
└── Region (group)
    └── VPC (group)
        └── Availability Zone / Subnet (public or private, group)
            └── Service icons (EC2, ECS, RDS, ...)
```

Not every diagram needs every layer — a serverless diagram may skip VPC/subnets
entirely. But when you show networking (EC2, ALB, RDS, NAT), draw the containers.
Putting a private-only service (like RDS) outside a subnet box is a red flag to
any AWS reviewer.

### Group containers (borders/backgrounds, from the `group` set)
- **AWS-Cloud_32** — outermost boundary, solid dark border, small AWS logo top-left.
- **Region_32** — dashed border.
- **Virtual-private-cloud-VPC_32** — solid green border, VPC icon top-left.
- **Public-subnet_32** — green tinted fill.
- **Private-subnet_32** — blue tinted fill.
- **Corporate-data-center_32** — for on-prem / hybrid (e.g. EKS Hybrid Nodes, Direct Connect).
- **AWS-Account_32**, **Auto-Scaling-group_32**, **Server-contents_32** — as needed.

In an SVG you render these as: a rounded `<rect>` with the group's signature border
color + a small `<image>` of the group icon pinned to the top-left corner + a text
label next to it. The group icon PNGs/SVGs are 32px corner badges, NOT full frames.

### Group border colors (use these exact hex values)
- AWS Cloud: `#232F3E` (squid ink), solid 2px
- Region: `#00A4A6` (teal), dashed 2px
- VPC: `#7AA116` (green), solid 2px
- Public subnet fill: `#E9F3E6` border `#7AA116`
- Private subnet fill: `#E6F2F8` border `#00A4A6`
- On-prem/data center: `#5A6B86`, solid 2px

## Service icons

All icons live in one bundle, `assets/icons.json`, organized into sets. Reference them
by `set/name` (see "Finding the right icon"). The relevant sets:

- `service` — 307 service product icons (the primary set).
- `resource` — 47 resource-level icons (finer-grained, e.g. specific EC2 instance
  types). Prefer `service` unless you specifically need a resource variant.
- `category` — 25 category icons (Compute, Storage...), for legends/agendas.

Each service icon is a self-contained square SVG with the product's colored gradient
tile. Render at 48–64px in the diagram. Always put a text label directly below the icon
(product name), centered, ~11–13px.

**Never invent or hand-draw a service icon.** If a service isn't in the bundle,
use the closest category icon or a plain labeled rounded rect — don't approximate the
official mark.

## AgentCore icons

Bedrock AgentCore has its own icon set (not in the standard AWS package), in sets
`agentcore-light` and `agentcore-dark`:
`AI-Agent, Agentcore, Browser-Tool, Code-Interpreter, Evaluations, Gateway, Identity,
Memory, Observability, Policy-Engine, Runtime`. The `Bedrock` icon is in `agentcore-extra`.

The set names describe the **icon color**, not the background (they were packed from the
`AgentCore/dark-blue` and `AgentCore/light-blue` source folders):

- `agentcore-dark` - dark navy/black strokes → use on **white/light** backgrounds (the default diagram).
- `agentcore-light` - white strokes → use on **dark** slide backgrounds.

Use them for any agentic-AI architecture (multi-agent workflows, AgentCore Runtime,
Gateway, Memory, Identity, etc.). Picking the wrong variant makes the icon nearly
invisible: black strokes on a dark slide, white strokes on a white page.

## Finding the right icon

Do not guess names — they're specific (`Amazon-EC2`, `AWS-Lambda`, `Amazon-API-Gateway`,
`Amazon-Simple-Storage-Service`). Run:

```bash
python "$SKILL_DIR/scripts/find_icon.py" "s3" "step functions" "cloudfront"
```

It prints ranked `set/name` references. List a whole set with
`python "$SKILL_DIR/scripts/find_icon.py" --list service`.

## Composing the SVG

Output a single self-contained `.svg` (or an HTML wrapper if the user wants a web page).
Reference each icon with the `bundle:` href scheme, then run `scripts/embed.py` to inline
every icon as base64 so the final file is portable and renders anywhere:

```
<image href="bundle:service/AWS-Lambda" x="200" y="200" width="56" height="56"/>
```

Always deliver the embedded version (post-embed.py) so the diagram renders standalone.

### Skeleton

```svg
<svg viewBox="0 0 900 600" xmlns="http://www.w3.org/2000/svg" font-family="Arial, 'Pretendard', sans-serif">
  <!-- AWS Cloud boundary -->
  <rect x="20" y="20" width="860" height="560" rx="8" fill="none" stroke="#232F3E" stroke-width="2"/>
  <image href="bundle:group/AWS-Cloud_32" x="30" y="30" width="26" height="26"/>
  <text x="62" y="48" font-size="13" fill="#232F3E" font-weight="600">AWS Cloud</text>

  <!-- VPC -->
  <rect x="60" y="70" width="780" height="480" rx="6" fill="none" stroke="#7AA116" stroke-width="2"/>
  <image href="bundle:group/Virtual-private-cloud-VPC_32" x="70" y="80" width="24" height="24"/>
  <text x="100" y="97" font-size="12" fill="#7AA116" font-weight="600">VPC 10.0.0.0/16</text>

  <!-- a service node (icon + label) -->
  <image href="bundle:service/AWS-Lambda" x="200" y="200" width="56" height="56"/>
  <text x="228" y="272" font-size="12" text-anchor="middle" fill="#232F3E">Lambda</text>

  <!-- connector -->
  <line x1="256" y1="228" x2="360" y2="228" stroke="#232F3E" stroke-width="1.5" marker-end="url(#arrow)"/>
</svg>
```

Define one arrowhead marker and reuse it:

```svg
<defs>
  <marker id="arrow" markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto">
    <path d="M0,0 L8,3 L0,6 Z" fill="#232F3E"/>
  </marker>
</defs>
```

## Layout rules that make it look professional

- **Left-to-right or top-to-bottom flow.** Users/clients on the left (or top), data
  stores on the right (or bottom). Follow the request path.
- **Align icons on a grid.** Same y for a horizontal tier, same x for a vertical tier.
  Even spacing. Misaligned icons look amateurish.
- **Label everything.** Every icon gets a product-name label. Every connector that
  isn't obvious gets a verb/protocol label ("HTTPS", "invoke", "read/write").
- **Whitespace.** Don't cram. Give containers padding (≥30px inside AWS Cloud, ≥20px
  inside VPC) so nested boxes breathe.
- **Color discipline.** Icons carry their own colors; keep containers, text, and
  connectors in the AWS neutrals (squid ink `#232F3E`, group border colors above; on a
  dark slide use the "Dark backgrounds" values below). Don't add rainbow connectors.
- **One arrowhead style, consistent stroke width** (1.5–2px) for all connectors.
- **Legend** only if the diagram has non-obvious symbols.

## Dark backgrounds

Everything above assumes a white diagram. For a dark slide (black or navy), change only
these elements:

| Element | White background (default) | Dark background |
|---|---|---|
| Background | none (white page) | opaque `<rect>` in the slide color as the first drawn element |
| Labels / sublabels | `#232F3E` / `#545B64` | `#E2E4EC` / `#A6ABBE` |
| Connectors, arrowhead, AWS Cloud border | `#232F3E` | `#A6ABBE` |
| AWS Cloud badge | `group/AWS-Cloud_32` (squid-ink glyph) | `group/AWS-Cloud_32_Dark` (white glyph); logo badge `group/AWS-Cloud-logo_32_Dark` |
| AgentCore icons | `agentcore-dark/*` | `agentcore-light/*` |
| `resource/*` icons (squid-ink glyphs, e.g. `resource/Users`) | as is | on a light chip: `<rect rx="12" fill="#E2E4EC"/>` behind the icon |
| Public / private subnet fill | `#E9F3E6` / `#E6F2F8` | `fill="#7AA116" fill-opacity="0.14"` / `fill="#00A4A6" fill-opacity="0.14"` |
| Region, VPC, subnet borders; service icons | unchanged | unchanged |

- Never leave a dark-background SVG transparent: viewers that draw transparency as white
  (some slide previews, PNG fallbacks) would hide the light labels entirely.
- Use `fill-opacity` instead of `rgba()` for tints; Office's SVG renderer is safest with it.
- Group icons use the opposite naming from AgentCore: a `_Dark` group icon is drawn in
  white for dark backgrounds.

## Font

AWS decks use **Pretendard** for Korean/bilingual content and Arial/Amazon Ember for
English. Set `font-family="Arial, 'Pretendard', sans-serif"` on the root `<svg>` so it
degrades gracefully. Korean labels are fine and common for FSI customer diagrams.

## Common diagram types & which layers to draw

- **3-tier web app**: AWS Cloud > Region > VPC > public subnet (ALB) + private subnets
  (ECS/EC2, RDS). Show AZ split if HA matters.
- **Serverless**: skip VPC. API Gateway > Lambda > DynamoDB, with S3/CloudFront front.
- **Container (EKS/ECS)**: VPC > subnets > cluster; show ALB, node groups, ECR.
- **Hybrid (EKS Hybrid Nodes, Direct Connect)**: Corporate-data-center group on one side,
  AWS Cloud on the other, connected via Direct Connect / VPN / Transit Gateway icon.
- **Agentic AI (AgentCore)**: use the AgentCore icon set — Runtime, Gateway, Memory,
  Identity — plus Bedrock, and standard icons for the surrounding infra.
