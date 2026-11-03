#!/usr/bin/env python3
"""Bundle every icon file under assets/ into a single icons.json.

This removes the per-file count (400+ files -> a handful) while keeping every
icon. SVGs are stored as raw text, PNGs as base64. find_icon.py and embed.py
read from this bundle instead of walking the folder tree.

Run from the skill root:  python scripts/build_bundle.py
"""
import base64
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"

# logical set name -> folder + file extension
SETS = {
    "service": ("aws-icons/service", ".svg"),
    "resource": ("aws-icons/resource", ".svg"),
    "group": ("aws-icons/group", ".svg"),
    "category": ("aws-icons/category", ".svg"),
    "agentcore-dark": ("AgentCore/dark-blue", ".png"),
    "agentcore-light": ("AgentCore/light-blue", ".png"),
}


def encode(path: Path, ext: str):
    if ext == ".svg":
        return {"type": "svg", "data": path.read_text(encoding="utf-8")}
    return {"type": "png", "data": base64.b64encode(path.read_bytes()).decode("ascii")}


def main():
    bundle = {"version": 1, "sets": {}}
    total = 0
    for name, (rel, ext) in SETS.items():
        folder = ASSETS / rel
        if not folder.exists():
            continue
        entries = {}
        for p in sorted(folder.glob(f"*{ext}")):
            entries[p.stem] = encode(p, ext)
        bundle["sets"][name] = entries
        total += len(entries)
        print(f"  {name}: {len(entries)}")

    # extra loose PNGs in AgentCore root (e.g. Bedrock.png)
    extra = {}
    for p in sorted((ASSETS / "AgentCore").glob("*.png")):
        extra[p.stem] = encode(p, ".png")
    if extra:
        bundle["sets"]["agentcore-extra"] = extra
        total += len(extra)
        print(f"  agentcore-extra: {len(extra)}")

    out = ROOT / "assets" / "icons.json"
    out.write_text(json.dumps(bundle, ensure_ascii=False), encoding="utf-8")
    size_mb = out.stat().st_size / 1024 / 1024
    print(f"Wrote {out} — {total} icons, {size_mb:.2f} MB")


if __name__ == "__main__":
    main()
