#!/usr/bin/env python3
"""
extract_brand_color.py  -  derive an accent palette from a customer logo.

Usage:  python extract_brand_color.py <logo.png|jpg|...>  [--json]

Strategy: ignore transparent / near-white / near-black / low-saturation (gray)
pixels (background + text + outlines), then pick the dominant *vivid* hue and
derive a coherent set of tokens for the deck:
  accent      - the brand color (header bands, title bar, chips)
  accentDark  - darker variant
  accentTint  - very light fill (e.g. highlighted table column)
  onAccent    - text color that sits on the accent (white or near-black), by contrast
"""
import sys, json
from collections import Counter
from PIL import Image

def rel_lum(r, g, b):
    s = [c / 255 for c in (r, g, b)]
    lin = [(c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4) for c in s]
    return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]

def hexs(r, g, b):
    return f"{int(round(r)):02X}{int(round(g)):02X}{int(round(b)):02X}"

def sat(r, g, b):
    mx, mn = max(r, g, b), min(r, g, b)
    return 0 if mx == 0 else (mx - mn) / mx

def extract(path):
    im = Image.open(path).convert("RGBA")
    im.thumbnail((220, 220))
    px = im.load()
    W, H = im.size
    buckets = Counter()      # quantized color -> saturation-weighted weight
    members = {}             # quantized color -> list of raw rgb (for refine)
    for y in range(H):
        for x in range(W):
            r, g, b, a = px[x, y]
            if a < 128:                       # transparent
                continue
            mx, mn = max(r, g, b), min(r, g, b)
            if mn > 235:                      # near-white (bg / paper)
                continue
            if mx < 28:                       # near-black (text / outline)
                continue
            if mx - mn < 28:                  # low-saturation gray
                continue
            key = (r >> 4, g >> 4, b >> 4)    # quantize to 4-bit/channel
            w = 1.0 + sat(r, g, b) ** 1.5 * 4 # favor vivid hues
            buckets[key] += w
            members.setdefault(key, []).append((r, g, b))

    if not buckets:                           # grayscale / monochrome logo -> fallback
        return None

    key, _ = buckets.most_common(1)[0]
    rgb = members[key]
    r = sum(c[0] for c in rgb) / len(rgb)
    g = sum(c[1] for c in rgb) / len(rgb)
    b = sum(c[2] for c in rgb) / len(rgb)

    accent = hexs(r, g, b)
    accent_dark = hexs(r * 0.72, g * 0.72, b * 0.72)
    accent_tint = hexs(r * 0.10 + 255 * 0.90, g * 0.10 + 255 * 0.90, b * 0.10 + 255 * 0.90)
    L = rel_lum(r, g, b)
    # Convention: white text on vivid brand colors; dark text only on light/pastel accents.
    on_accent = "0E0E0E" if L > 0.6 else "FFFFFF"

    return {
        "accent": accent, "accentDark": accent_dark, "accentTint": accent_tint,
        "onAccent": on_accent, "luminance": round(L, 3),
        "contrast_on_white": round(1.05 / (L + 0.05), 2),
    }

if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    as_json = "--json" in sys.argv
    if not args:
        print("usage: python extract_brand_color.py <logo> [--json]"); sys.exit(1)
    res = extract(args[0])
    if res is None:
        print("No vivid brand color found (logo may be grayscale). Use the default accent.")
        sys.exit(2)
    if as_json:
        print(json.dumps(res))
    else:
        print(f"  logo        : {args[0]}")
        print(f"  accent      : #{res['accent']}   (on-accent text: #{res['onAccent']}, contrast {res['contrast_on_white']}:1 vs white)")
        print(f"  accentDark  : #{res['accentDark']}")
        print(f"  accentTint  : #{res['accentTint']}")
