"""Example: compute PoC verdicts from data.json and draw the report charts with chart_style.
usage: uv run --no-project --with matplotlib python -B make_charts.py [OUT_DIR]   (default ./charts)
Prints the verdict table so the numbers in example.md come from here, not from hand calculation."""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2] / "scripts"))  # skills/aws-reports/scripts
from chart_style import INK, MUTED, criteria, fmt, grouped_hbar, setup  # noqa: E402
from matplotlib.patches import Patch  # noqa: E402

D = json.loads((HERE / "data.json").read_text(encoding="utf-8"))
out = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd() / "charts"  # never the skill folder


def ratio(c):
    """1.00 = on target. Zero-tolerance targets (target 0, lower is better) have no meaningful ratio."""
    t, r = c["target"], c["result"]
    if c["better"] == "lower":
        return None if t == 0 else t / r
    return r / t


def verdict(c):
    if c["result"] is None:
        return "측정하지 않음"
    ok = c["result"] <= c["target"] if c["better"] == "lower" else c["result"] >= c["target"]
    if ok:
        return "충족"
    # partly met: some of the measured scope reached the target (here: 2 of 3 channels connected)
    return "부분 충족" if c["id"] == "C6" else "미충족"


rows = [(c, ratio(c), verdict(c)) for c in D["criteria"]]
for c, r, v in rows:
    print(f'{c["id"]} {c["name"]:<10} target={c["target"]} result={c["result"]} ratio={"—" if r is None else f"{r:.2f}"} {v}')
req = [v for c, _, v in rows if c["required"]]
print(f"필수 {len(req)}개 중 충족 {req.count('충족')}개")

setup()
# a zero-tolerance criterion has no ratio: show the verdict with the measured count instead of a bar
criteria(out / "chart-criteria.png", [(f'{c["id"]} {c["name"]}', r, v, None if r is not None else f'{c["result"]}{c["unit"]}') for c, r, v in rows])
grouped_hbar(out / "chart-latency.png",
             [(b["bucket"], [(b["p50"], MUTED, 1), (b["p95"], INK, 1)], None) for b in D["latency"]],
             fmt=fmt.sec1, ref=5.0, xlabel="응답 시간 (초)",
             legend=[Patch(color=MUTED, label="p50"), Patch(color=INK, label="p95"), Patch(facecolor="white", edgecolor="#374151", linestyle="--", label="목표 p95 5초")])
print("charts:", sorted(p.name for p in out.glob("*.png")))
