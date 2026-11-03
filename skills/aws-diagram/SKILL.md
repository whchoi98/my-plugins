---
name: aws-diagram
description: Draw AWS architecture and cloud infrastructure diagrams using the official AWS Architecture Icon set (307 service icons, group/container icons, resource icons) plus the Bedrock AgentCore icon set. Use this skill WHENEVER the request involves drawing, sketching, or visualizing a diagram AND the topic is AWS or cloud infrastructure — trigger on any combination of a drawing verb (draw, sketch, diagram, visualize, "그려줘", "그림", "도식화") with keywords like "aws", "architecture", "아키텍처", "구성도", "다이어그램", VPC, EKS, ECS, Lambda, Bedrock, AgentCore, S3, or a described AWS system to lay out. Also trigger when the user asks for an architecture diagram of a cloud system even without naming AWS explicitly, or wants official AWS icons in a figure. Produces a self-contained SVG (or HTML) that uses real AWS product icons rather than hand-drawn approximations. For structure diagrams that are not an AWS service layout (flowchart, sequence, timeline, swimlane, org chart, ER, charts) use aws-diagram-design in this plugin instead.
---

# AWS Architecture Diagram

Draw professional AWS architecture diagrams that use the **official AWS icons**
bundled with this skill, instead of hand-drawing shapes that don't match what AWS
customers expect to see. The single most important thing this skill does: make sure
every service is rendered with its real AWS icon and every container follows AWS's
nesting convention.

## When to use

Any request that pairs a **drawing intent** with an **AWS / cloud-infra topic**. Examples:
- "AWS 아키텍처 그려줘" / "draw the architecture for this system on AWS"
- "이 구성을 다이어그램으로 만들어줘" (about an AWS stack)
- "diagram the VPC / EKS / serverless / AgentCore setup"
- "show me how CloudFront → ALB → ECS → RDS connects"
- Any figure that should contain official AWS service icons.

If the request is purely conceptual (no drawing) or not AWS-related, this skill
doesn't apply.

## Workflow

`SKILL_DIR` below means the base directory of this skill (shown when the skill loads). The working directory is the user's project, so run the scripts through it.

Follow these steps in order. Don't skip the icon lookup — guessing filenames is the
main failure mode.

### 1. Understand the architecture
Extract the components, their AWS services, and the flow (who calls what, what's
public vs private, what's on-prem). If the user gave a stack in prose or an existing
system, map each piece to an AWS service. Ask a brief clarifying question only if the
topology is genuinely ambiguous; otherwise proceed with a sensible default and note
assumptions.

### 2. Read the guide
Read `references/diagram_guide.md` in full. It defines the AWS visual grammar
(Cloud > Region > VPC > subnet nesting), the exact group border colors, layout rules,
the SVG skeleton, and the AgentCore icon set. The diagram will look wrong if you skip it.

### 3. Find the exact icons
All icons live inside a single bundle, `assets/icons.json` (not a folder of files).
For every service and container, look up its exact reference — do not type it from memory:

```bash
python "$SKILL_DIR/scripts/find_icon.py" "ec2" "api gateway" "s3" "cloudfront" "rds"
```

It prints ranked `set/name` references (e.g. `service/AWS-Lambda`, `group/AWS-Cloud_32`,
`agentcore-dark/Runtime`). Common abbreviations (alb, ecs, s3, vpc, ...) are aliased.
List a whole set with `python "$SKILL_DIR/scripts/find_icon.py" --list service`. Sets available:
`service` (307), `resource` (47), `group` (15), `category` (25),
`agentcore-dark` / `agentcore-light` (11 each), `agentcore-extra` (Bedrock).

AgentCore set names describe the icon color: `agentcore-dark` icons have dark strokes
(white/light backgrounds), `agentcore-light` icons have white strokes (dark backgrounds).

If a service has no matching icon, use the closest **category** icon or a plain labeled
rounded rect — never hand-draw a fake product mark.

### 4. Compose the SVG
Build a single `.svg` following the skeleton and layout rules in the guide. Reference
each icon with the **`bundle:` scheme** in the `href` — this is how embed.py finds it:

```xml
<image href="bundle:service/AWS-Lambda"   x="200" y="200" width="56" height="56"/>
<image href="bundle:group/AWS-Cloud_32"   x="30"  y="30"  width="26" height="26"/>
<image href="bundle:agentcore-dark/Runtime" x="80" y="80" width="52" height="52"/>
```

- Draw group containers first (AWS Cloud, VPC, subnets) as rounded rects with the
  correct border colors + a corner group-icon badge + a label.
- Place each service as an `<image href="bundle:...">` (48–64px) with a centered
  product label directly below.
- Connect with consistent 1.5–2px squid-ink (`#232F3E`) arrows using one shared
  arrowhead marker. Label non-obvious connectors (protocol / verb).
- Left→right or top→bottom flow, aligned on a grid, generous whitespace.
- Root `font-family="Arial, 'Pretendard', sans-serif"` (supports Korean labels).
- For a dark slide background, apply the guide's "Dark backgrounds" table: opaque
  background rect, light labels and connectors, `group/AWS-Cloud_32_Dark`,
  `agentcore-light/*` icons, light chips behind `resource/*` icons.

### 5. Make it portable and deliver
Inline all icons as base64 so the final file renders standalone anywhere:

```bash
python "$SKILL_DIR/scripts/embed.py" draft.svg final.svg
```

It replaces every `bundle:set/name` href with a data: URI from the bundle. Verify it
reports 0 missing icons (fix any bad refs with find_icon.py and re-run). Save the
result in the working directory (or the path the user named) and give its path; on claude.ai copy it to `/mnt/user-data/outputs/` and present it. If the user asked for an editable
web page or wants to tweak interactively, wrap the SVG in a minimal HTML file instead;
otherwise deliver the `.svg`.

## Output format

- Default deliverable: one self-contained, base64-embedded `.svg` in
  the working directory (`/mnt/user-data/outputs/` on claude.ai).
- Preserve official icon colors; keep containers/text/arrows in AWS neutrals.
- Bilingual (Korean/English) labels are expected and fine for FSI/customer diagrams.

## What NOT to do

- Don't hand-draw or approximate AWS service icons — use the bundled ones.
- Don't put private services (RDS, internal ALB) outside a subnet container.
- Don't use rainbow connectors or inconsistent arrow styles.
- Don't put `agentcore-dark` icons or squid-ink labels on a dark background, and don't
  leave a dark-background SVG transparent.
- Don't deliver an SVG that references external icon files (won't render for the user)
  — always run `embed.py` for the final version.

## Asset inventory

All 417 icons are packed into one JSON bundle (keeps the skill's file count low):

- `assets/icons.json` — the icon bundle. Sets: `service` (307 AWS service icons),
  `resource` (47), `group` (15 container icons: AWS Cloud, Region, VPC, subnets, on-prem),
  `category` (25), `agentcore-dark` / `agentcore-light` (11 Bedrock AgentCore icons each;
  dark strokes for light backgrounds / white strokes for dark backgrounds),
  `agentcore-extra` (Bedrock). SVGs stored as text, PNGs as base64.
- `references/diagram_guide.md` — conventions, colors, SVG skeleton (read this).
- `scripts/find_icon.py` — fuzzy lookup → `set/name` reference (with AWS abbreviation aliases).
- `scripts/embed.py` — inline `bundle:set/name` hrefs as base64 for a portable final SVG.
- `scripts/build_bundle.py` — rebuild `icons.json` from a `assets/` icon-folder tree
  (only needed if you re-add loose icon files and want to repack them).
