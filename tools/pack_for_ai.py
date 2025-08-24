#!/usr/bin/env python3
"""
pack_for_ai.py — zip only the files we need to continue work together.

Usage examples:

  python tools/pack_for_ai.py --out exports/ai_workset.zip ^
    --include docs/CHECKLIST.md docs/ROUTES.md docs/STRUCTURE.md ^
    --include main.py routes_finance.py ^
    --include templates/finance/** templates/_layout.html ^
    --include static/css/** static/js/**

Notes:
- Globs are supported (**, *). Paths are relative to project root (this script's parent dir or CWD).
- The zip preserves relative paths.
"""

import argparse, sys, os
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
import glob

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True, help="Output zip path")
    ap.add_argument("--include", nargs="+", action="append", help="List of include globs (space-separated). You can repeat --include.")
    ap.add_argument("--root", default=".", help="Project root (default: current dir)")
    args = ap.parse_args()

    root = Path(args.root).resolve()
    out_path = Path(args.out).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    patt_list = [p for group in (args.include or []) for p in group]
    if not patt_list:
        # sensible defaults for our PC-3 flow
        patt_list = [
            "docs/CHECKLIST.md",
            "docs/ROUTES.md",
            "docs/STRUCTURE.md",
            "main.py",
            "routes_finance.py",
            "templates/finance/**",
            "templates/_layout.html",
            "static/css/**",
            "static/js/**",
        ]

    matched_files = []
    for patt in patt_list:
        # On Windows, allow backslashes
        patt = patt.replace("\\", "/")
        full_glob = str(root / patt)
        files = [Path(p) for p in glob.glob(full_glob, recursive=True) if Path(p).is_file()]
        matched_files.extend(files)

    # Deduplicate
    rels = []
    added = set()
    for p in matched_files:
        rel = p.relative_to(root)
        if rel in added:
            continue
        added.add(rel)
        rels.append(rel)

    print(f"Packing {len(rels)} files into {out_path}")
    with ZipFile(out_path, "w", ZIP_DEFLATED) as zf:
        for rel in rels:
            zf.write(root / rel, arcname=str(rel))

    print("Done.")

if __name__ == "__main__":
    main()
