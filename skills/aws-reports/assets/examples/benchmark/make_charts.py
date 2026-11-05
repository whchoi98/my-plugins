"""Example: draw the report charts from data.json with chart_style.
usage: uv run --no-project --with matplotlib python -B make_charts.py [OUT_DIR]   (default ./charts)"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2] / "scripts"))  # skills/aws-reports/scripts
from chart_style import dumbbell, fmt, hbar, setup, verdict  # noqa: E402

setup()
D = json.loads((HERE / "data.json").read_text(encoding="utf-8"))
out = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd() / "charts"  # never the skill folder

hbar(out / "chart-score.png", [(r["instance"], r["score"], r["vendor"], r["gen"]) for r in D["score"]], fmt=fmt.int)
hbar(out / "chart-ppd.png", [(r["instance"], r["rel_ppd"], r["vendor"], r["gen"]) for r in D["score"]], fmt=fmt.x2, ref=1.0)
dumbbell(out / "chart-gen.png", [(f'{r["from"].split(".")[0]} → {r["to"].split(".")[0]}', r["score_from"], r["score_to"], r["vendor"]) for r in D["gen"]],
         labels=("7세대", "8세대"))
verdict(out / "chart-verdict.png", [(r["scenario"], r["ppd_ratio"]) for r in D["verdict"]])
print("charts:", sorted(p.name for p in out.glob("*.png")))
