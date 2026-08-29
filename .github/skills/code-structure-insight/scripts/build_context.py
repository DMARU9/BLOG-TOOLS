#!/usr/bin/env python3
"""Build a single markdown context file from analyze_structure.py artifacts.

Reads the artifacts produced by trend_researcher/script/analyze_structure.py
and consolidates them into one markdown document suitable as input for an LLM that
will generate a human-readable structure report + improvement suggestions.

Usage:
  python build_context.py --artifacts <artifacts_dir> [--out <context.md>]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def _read_text(path: Path) -> str:
    if not path.exists():
        return f"_(missing: {path.name})_"
    return path.read_text(encoding="utf-8", errors="ignore").strip()


def _load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="ignore"))
    except json.JSONDecodeError:
        return {}


def complexity_blocks(cc_data: dict, limit: int = 15) -> list[dict]:
    ranked = []
    for file, blocks in cc_data.items():
        if not isinstance(blocks, list):
            continue
        for b in blocks:
            ranked.append({
                "file": file,
                "name": b.get("name"),
                "type": b.get("type"),
                "complexity": b.get("complexity", 0),
                "rank": b.get("rank"),
                "lineno": b.get("lineno"),
            })
    ranked.sort(key=lambda x: x["complexity"], reverse=True)
    return ranked[:limit]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--artifacts", type=Path, required=True,
                    help="Path to the artifacts/ directory from analyze_structure.py")
    ap.add_argument("--out", type=Path, default=None,
                    help="Output markdown path (default: <artifacts>/insight_context.md)")
    args = ap.parse_args()

    art = args.artifacts
    if not art.is_dir():
        print(f"ERROR: artifacts dir not found: {art}", file=sys.stderr)
        return 1

    out = args.out or (art / "insight_context.md")

    cc = _load_json(art / "radon_cc.json")
    mi = _load_json(art / "radon_mi.json")
    summary = _read_text(art / "summary.md")
    isolated = _read_text(art / "isolated_modules.txt")

    ranked = complexity_blocks(cc)
    high_cc = [r for r in ranked if r["complexity"] >= 11]  # rank C/D threshold

    # Maintainability-index hotspots (B or worse => < 20 is C; radon uses A>=20)
    mi_hot = []
    for f, info in mi.items():
        if isinstance(info, dict) and info.get("rank") in ("B", "C"):
            mi_hot.append((f, info.get("mi"), info.get("rank")))

    lines: list[str] = []
    lines.append("# Code Structure Insight — Context")
    lines.append("")
    lines.append(f"Source artifacts: `{art}`")
    lines.append("")
    lines.append("## 1. Complexity hotspots (radon CC, rank C/D = complexity >= 11)")
    lines.append("")
    if high_cc:
        lines.append("| Complexity | Rank | File | Block | Line |")
        lines.append("|---|---|---|---|---|")
        for r in high_cc:
            lines.append(f"| {r['complexity']} | {r['rank']} | `{r['file']}` | {r['name']} ({r['type']}) | {r['lineno']} |")
    else:
        lines.append("_No rank C/D functions found._")
    lines.append("")

    lines.append("## 2. Maintainability-index hotspots (radon MI, rank B/C)")
    lines.append("")
    if mi_hot:
        lines.append("| MI | Rank | File |")
        lines.append("|---|---|---|")
        for f, v, rk in sorted(mi_hot, key=lambda x: (x[1] or 0)):
            lines.append(f"| {v} | {rk} | `{f}` |")
    else:
        lines.append("_No low-maintainability modules found._")
    lines.append("")

    lines.append("## 3. Isolated modules (imported by nobody)")
    lines.append("")
    if isolated and isolated != "_(missing: isolated_modules.txt)_":
        for m in isolated.splitlines():
            if m.strip():
                lines.append(f"- `{m}`")
    else:
        lines.append("_No isolated modules detected._")
    lines.append("")

    lines.append("## 4. Full summary (from analyze_structure.py)")
    lines.append("")
    lines.append(summary if summary else "_(summary.md missing)_")
    lines.append("")

    lines.append("## 5. Available diagrams")
    lines.append("")
    # analyze_structure.py emits packages_<pkg>.* / classes_<pkg>.* / pydeps_<pkg>.*
    # where <pkg> is the source package name (e.g. trend_researcher). Resolve by glob.
    diagram_patterns = [
        "pyreverse/classes_*.png", "pyreverse/classes_*.svg",
        "pyreverse/packages_*.png", "pyreverse/packages_*.svg",
        "pydeps_*.png", "pydeps_*.svg",
    ]
    for pat in diagram_patterns:
        matches = sorted(art.glob(pat))
        if matches:
            for p in matches:
                lines.append(f"- `{p.relative_to(art)}` : present")
        else:
            lines.append(f"- `{pat}` : MISSING")
    lines.append("")

    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote context to {out} ({out.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
