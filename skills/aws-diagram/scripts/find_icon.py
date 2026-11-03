#!/usr/bin/env python3
"""Find icons in the bundled assets/icons.json.

Usage:
  python scripts/find_icon.py ec2
  python scripts/find_icon.py "api gateway" lambda s3   # multiple at once
  python scripts/find_icon.py --list service            # list a whole set

Prints ranked matches as `set/name`. Icons live inside assets/icons.json
(one file, not hundreds), so reference them by `set/name` and let extract.py
pull the actual SVG/PNG out when you build a diagram. Fuzzy, case/hyphen-
insensitive, with common AWS abbreviation aliases.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BUNDLE = json.loads((ROOT / "assets" / "icons.json").read_text(encoding="utf-8"))
SETS = BUNDLE["sets"]

ALIASES = {
    "alb": "elastic load balancing", "nlb": "elastic load balancing",
    "elb": "elastic load balancing", "load balancer": "elastic load balancing",
    "ecs": "elastic container service", "ecr": "elastic container registry",
    "eks": "elastic kubernetes service", "s3": "simple storage service",
    "sqs": "simple queue service", "sns": "simple notification service",
    "ses": "simple email service", "rds": "relational database service",
    "vpc": "virtual private cloud", "ddb": "dynamodb", "apigw": "api gateway",
    "asg": "ec2 auto scaling", "iam": "identity and access management",
    "kms": "key management service", "efs": "elastic file system",
    "ebs": "elastic block store", "msk": "managed streaming for apache kafka",
    "sfn": "step functions", "step functions": "step functions",
}


def norm(s: str) -> str:
    return "".join(c for c in s.lower() if c.isalnum())


def score(query: str, name: str) -> int:
    q, n = norm(query), norm(name)
    if q == n:
        return 100
    if n.endswith(q) or n.startswith(q):
        return 80
    if q in n:
        return 60
    qt = set(query.lower().replace("-", " ").split())
    nt = set(name.lower().replace("-", " ").split())
    if qt & nt:
        return 30 + 5 * len(qt & nt)
    return 0


def search(query: str, k: int = 5):
    ql = query.lower().strip()
    queries = [query] + ([ALIASES[ql]] if ql in ALIASES else [])
    results = []
    for setname, entries in SETS.items():
        for name in entries:
            s = max(score(q, name) for q in queries)
            if s > 0:
                results.append((s, f"{setname}/{name}"))
    results.sort(key=lambda r: -r[0])
    return results[:k]


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        print("Available sets:", ", ".join(f"{k} ({len(v)})" for k, v in SETS.items()))
        sys.exit(1)
    if args[0] == "--list":
        setname = args[1] if len(args) > 1 else "service"
        for name in sorted(SETS.get(setname, {})):
            print(f"{setname}/{name}")
        return
    for query in args:
        print(f"# {query}")
        hits = search(query)
        if not hits:
            print("  (no match — try: python scripts/find_icon.py --list service)")
        for s, ref in hits:
            print(f"  [{s:3}] {ref}")
        print()


if __name__ == "__main__":
    main()
