"""Chart helpers in the aws-reports house style (matplotlib, PNG for both the Word and the HTML report).

    uv run --no-project --with matplotlib python my_charts.py      # my_charts.py does: from chart_style import *

    import sys; sys.path.insert(0, "<skill-dir>/scripts")   # run with python -B: no __pycache__ in the skill folder
    from chart_style import setup, hbar, grouped_hbar, dumbbell, lines, verdict, criteria, color_of, fmt
    setup()
    hbar("out/chart-score.png", [("c8i.2xlarge", 15210, "Intel", 8), ("c8g.2xlarge", 13890, "Graviton", 8), ...],
         fmt=fmt.int, ref=None, dots={"c8i.2xlarge": [15100, 15300]})

Rules these helpers apply (keep them when you draw a chart by hand):
- One color per vendor (Graviton orange, Intel blue, AMD green); the older generation is the same color at 50% alpha.
- Legend above the plot, left aligned, no frame. Value label at the end of every bar.
- A reference line (e.g. 1.0 = baseline) is dashed; labels get a white box so the line never runs through a number.
- A "similar" band (e.g. 0.95-1.05) is a light gray span behind the bars.
- Width 6.3 in at 220 dpi: fits the 17 cm Word text column and stays sharp in HTML.
"""
from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib import font_manager, ticker  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
from matplotlib.patches import Patch  # noqa: E402

VENDOR = {"Graviton": "#E07B2E", "Intel": "#2F6DB5", "AMD": "#2E9E6B"}
VENDOR_LABEL = {"Graviton": "AWS Graviton", "Intel": "Intel Xeon", "AMD": "AMD EPYC"}
MUTED = "#AEB6BF"
# PoC verdict colors (criteria chart). Always paired with a legend and the verdict word, never color alone.
VERDICT_COLOR = {"충족": "#2E7D5B", "부분 충족": "#C98A1B", "미충족": "#B42318", "측정하지 않음": MUTED}
INK = "#1F2937"
WIDTH_IN = 6.3

fmt = SimpleNamespace(
    int=lambda v: f"{v:,.0f}",
    f1=lambda v: f"{v:,.1f}",
    f2=lambda v: f"{v:,.2f}",
    x2=lambda v: f"{v:.2f}배",
    pct=lambda v: f"{v:+.1%}",
    pct0=lambda v: f"{v:.0%}",
    sec=lambda v: f"{v:.2f}초",
    sec1=lambda v: f"{v:.1f}초",
    ms=lambda v: f"{v:,.1f} ms",
    usd=lambda v: f"${v:,.4f}",
)


def setup(font_dirs=None):
    """Register NanumSquareOTF (and D2Coding) and set the report rcParams."""
    dirs = font_dirs or [Path.home() / ".local/share/fonts", Path.home() / ".fonts", Path.home() / "Library/Fonts", Path("/usr/share/fonts")]
    for d in map(Path, dirs):
        if d.exists():
            for f in list(d.rglob("NanumSquare*.otf")) + list(d.rglob("D2Coding*.ttf")):
                font_manager.fontManager.addfont(str(f))
    family = "NanumSquareOTF" if any(f.name == "NanumSquareOTF" for f in font_manager.fontManager.ttflist) else "sans-serif"
    if family != "NanumSquareOTF":
        print("chart_style: NanumSquareOTF not found, Korean labels may break (install it with the my-plugins setup skill)")
    plt.rcParams.update({
        "font.family": family, "font.size": 8.5, "axes.edgecolor": "#C9CED4", "axes.linewidth": 0.6,
        "xtick.color": "#4B5563", "ytick.color": INK, "axes.labelcolor": "#4B5563", "savefig.dpi": 220,
        "axes.unicode_minus": False,
    })


def color_of(vendor):
    return VENDOR.get(vendor, MUTED)


def alpha_of(gen, latest):
    """Latest generation solid, older ones 50%."""
    return 1.0 if gen is None or latest is None or float(gen) >= float(latest) else 0.5


def _legend(ax, handles):
    ax.legend(handles=handles, loc="lower left", bbox_to_anchor=(0, 1.0), ncol=4, frameon=False, fontsize=7.5, borderaxespad=0.2)


def vendor_handles(vendors):
    return [Patch(color=color_of(v), label=VENDOR_LABEL.get(v, v)) for v in vendors]


def _style(ax, grid_axis="x"):
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis=grid_axis, color="#E5E7EB", linewidth=0.6)
    ax.set_axisbelow(True)


def _save(fig, path):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)
    return str(path)


def grouped_hbar(path, rows, fmt=fmt.int, ref=None, band=None, legend=None, xlabel=None, height=None):
    """General horizontal bars, top to bottom.
    rows: [(label, [(value, color, alpha), ...], dots or None)]; several series per row are drawn as grouped bars.
    legend: list of matplotlib handles, or None."""
    n, k = len(rows), max(len(r[1]) for r in rows)
    fig, ax = plt.subplots(figsize=(WIDTH_IN, height or 0.34 * n * (1 + 0.5 * (k - 1)) + 0.7))
    bh = 0.72 / k
    vmax = max(max(v for v, _, _ in r[1]) for r in rows)
    vmax = max(vmax, max((max(r[2]) for r in rows if r[2]), default=0))
    for i, (label, series, dots) in enumerate(rows):
        y = n - 1 - i
        for j, (v, c, a) in enumerate(series):
            yy = y + (k - 1) * bh / 2 - j * bh
            ax.barh(yy, v, height=bh * 0.92, color=c, alpha=a)
            end = max([v] + list(dots or [])) if j == 0 else v
            ax.text(end + vmax * 0.012, yy, fmt(v), va="center", fontsize=7.5, color=INK, zorder=5,
                    bbox=dict(facecolor="white", edgecolor="none", pad=1.2) if ref is not None else None)
        if dots:
            ax.scatter(dots, [y] * len(dots), s=7, color="#111827", zorder=3, linewidths=0)
    ax.set_yticks(range(n))
    ax.set_yticklabels([r[0] for r in reversed(rows)])
    ax.set_xlim(0, vmax * 1.17)
    ax.xaxis.set_major_formatter(ticker.FuncFormatter((lambda v, _: f"{v:,.0f}") if vmax >= 100 else (lambda v, _: f"{v:g}")))
    if band:
        ax.axvspan(*band, color="#E5E7EB", alpha=0.6, zorder=0)
    if ref is not None:
        ax.axvline(ref, color="#374151", linestyle=(0, (3, 2)), linewidth=0.9, zorder=1.5)
    if xlabel:
        ax.set_xlabel(xlabel)
    _style(ax)
    ax.tick_params(axis="y", length=0)
    if legend:
        _legend(ax, legend)
    return _save(fig, path)


def hbar(path, items, fmt=fmt.int, ref=None, band=None, dots=None, latest_gen=None, sort=True, xlabel=None, legend=True):
    """One bar per item, colored by vendor.
    items: [(label, value, vendor, gen)]; gen may be None. dots: {label: [run values]} drawn as small points.
    latest_gen: generation drawn solid (older = 50%); default is the max gen in items."""
    if latest_gen is None:
        gens = [g for *_, g in items if g is not None]
        latest_gen = max(map(float, gens)) if gens else None
    its = sorted(items, key=lambda r: -r[1]) if sort else list(items)
    rows = [(lab, [(v, color_of(ven), alpha_of(g, latest_gen))], (dots or {}).get(lab)) for lab, v, ven, g in its]
    vendors = [v for v in VENDOR if any(r[2] == v for r in items)]
    return grouped_hbar(path, rows, fmt=fmt, ref=ref, band=band, xlabel=xlabel, legend=vendor_handles(vendors) if legend else None)


def dumbbell(path, rows, fmt=fmt.int, note_fmt=fmt.pct, labels=("이전 세대", "새 세대")):
    """Generation-over-generation change. rows: [(label, from_value, to_value, vendor)] top to bottom.
    The label after each pair shows to/from - 1."""
    fig, ax = plt.subplots(figsize=(WIDTH_IN, 0.45 * len(rows) + 0.6))
    vmax = max(max(a, b) for _, a, b, _ in rows)
    for i, (lab, a, b, ven) in enumerate(rows):
        y = len(rows) - 1 - i
        c = color_of(ven)
        ax.plot([a, b], [y, y], color=c, linewidth=1.6, alpha=0.7)
        ax.scatter([a], [y], s=34, facecolors="white", edgecolors=c, linewidths=1.4, zorder=3)
        ax.scatter([b], [y], s=34, color=c, zorder=3)
        ax.text(max(a, b) + vmax * 0.015, y, note_fmt(b / a - 1), va="center", fontsize=7.5)
    ax.set_ylim(-0.6, len(rows) - 0.4)
    ax.set_yticks(range(len(rows)))
    ax.set_yticklabels([r[0] for r in reversed(rows)])
    ax.set_xlim(0, vmax * 1.15)
    ax.xaxis.set_major_formatter(ticker.FuncFormatter(lambda v, _: fmt(v)))
    _style(ax)
    ax.tick_params(axis="y", length=0)
    _legend(ax, [Line2D([], [], marker="o", linestyle="", markerfacecolor="white", markeredgecolor="#4B5563", label=labels[0]),
                 Line2D([], [], marker="o", linestyle="", color="#4B5563", label=labels[1])])
    return _save(fig, path)


def lines(path, series, xlabel, ylabel, fmt=fmt.int, xticks=None, height=3.0):
    """Load curves etc. series: [(label, xs, ys, vendor, gen, family)]; family 'c'/'m'/... picks the marker,
    older generation is dashed. Legend (instance names) above the plot."""
    gens = [s[4] for s in series if s[4] is not None]
    latest = max(map(float, gens)) if gens else None
    markers = {}
    fig, ax = plt.subplots(figsize=(WIDTH_IN, height))
    for lab, xs, ys, ven, gen, fam in series:
        mk = markers.setdefault(fam, "osD^v<>"[len(markers) % 7])
        old = latest is not None and gen is not None and float(gen) < latest
        ax.plot(xs, ys, marker=mk, markersize=3.5, color=color_of(ven), linestyle="--" if old else "-", linewidth=1.3, label=lab)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda v, _: fmt(v)))
    if xticks:
        ax.set_xticks(xticks)
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(color="#E5E7EB", linewidth=0.6)
    ax.legend(loc="lower left", bbox_to_anchor=(0, 1.0), ncol=4, frameon=False, fontsize=7, borderaxespad=0.2)
    return _save(fig, path)


def verdict(path, rows, ref=1.0, band=(0.95, 1.05), better="Graviton", worse="Intel", fmt=fmt.x2):
    """Final price-performance verdict: rows [(scenario, ratio)] where ratio = better-vendor / other-vendor.
    Bars inside the band are gray ("비슷"), above use the `better` vendor color, below the `worse` color."""
    def c(v):
        return MUTED if band[0] <= v <= band[1] else color_of(better if v > band[1] else worse)
    pct = int(round((band[1] - 1) * 100))
    legend = [Patch(color=color_of(worse), label=f"{worse} 우위"), Patch(color=MUTED, label=f"비슷 (±{pct}%)"), Patch(color=color_of(better), label=f"{better} 우위")]
    return grouped_hbar(path, [(s, [(v, c(v), 1)], None) for s, v in rows], fmt=fmt, ref=ref, band=band, legend=legend)


def criteria(path, rows, clip=2.0, fmt=fmt.x2, xlabel="목표 대비 (1.00 = 목표값)"):
    """PoC success criteria against their targets. rows: [(criterion, ratio, verdict)] or [(criterion, ratio, verdict, note)]
    top to bottom.
    ratio = result / target when higher is better, target / result when lower is better (latency, cost, error count),
    so 1.00 is exactly on target and a met criterion reaches the dashed line. ratio None (not measured, or a criterion
    with no numeric target such as "누락 0건") draws no bar and writes the verdict word and the note instead.
    Bars longer than `clip` are cut at `clip`; the label keeps the real ratio."""
    n = len(rows)
    fig, ax = plt.subplots(figsize=(WIDTH_IN, 0.36 * n + 0.8))
    rows = [tuple(r) + (None,) * (4 - len(r)) for r in rows]
    vis = [min(r, clip) for _, r, _, _ in rows if r is not None]
    vmax = max(vis + [1.0])
    for i, (_, r, v, note) in enumerate(rows):
        y = n - 1 - i
        if r is None:
            ax.text(vmax * 0.02, y, f"{v} · {note}" if note else v, va="center", fontsize=7.5, color="#4B5563")
            continue
        w = min(r, clip)
        ax.barh(y, w, height=0.62, color=VERDICT_COLOR.get(v, MUTED))
        ax.text(w + vmax * 0.012, y, fmt(r), va="center", fontsize=7.5, color=INK, zorder=5,
                bbox=dict(facecolor="white", edgecolor="none", pad=1.2))
    ax.axvline(1.0, color="#374151", linestyle=(0, (3, 2)), linewidth=0.9, zorder=1.5)
    ax.set_yticks(range(n))
    ax.set_yticklabels([r[0] for r in reversed(rows)])
    ax.set_xlim(0, vmax * 1.18)
    ax.set_ylim(-0.6, n - 0.4)
    ax.xaxis.set_major_formatter(ticker.FuncFormatter(lambda v, _: f"{v:g}"))
    if xlabel:
        ax.set_xlabel(xlabel)
    _style(ax)
    ax.tick_params(axis="y", length=0)
    seen = [v for v in VERDICT_COLOR if any(r[2] == v and r[1] is not None for r in rows)]
    _legend(ax, [Patch(color=VERDICT_COLOR[v], label=v) for v in seen])
    return _save(fig, path)
