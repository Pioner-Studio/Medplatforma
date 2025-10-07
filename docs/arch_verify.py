# -*- coding: utf-8 -*-
"""
Простой сканер: находит Flask-роуты и шаблоны render_template, пишет в docs/routes.json.
Запуск: python docs/arch_verify.py --root . --out docs/routes.json
"""
import argparse, json, re, sys
from pathlib import Path

ROUTE_RE = re.compile(r'@[\w\.]+\.route\(\s*[\'"]([^\'"]+)[\'"]')
RENDER_RE = re.compile(r'render_template\(\s*[\'"]([^\'"]+)[\'"]')

def scan(root: Path):
    data = []
    for p in root.rglob("*.py"):
        try:
            text = p.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        for m in ROUTE_RE.finditer(text):
            route = m.group(1)
            data.append({"type": "route", "path": str(p), "route": route})
        for m in RENDER_RE.finditer(text):
            tpl = m.group(1)
            data.append({"type": "template", "path": str(p), "template": tpl})
    return {"routes": data}

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--out", default="docs/routes.json")
    args = ap.parse_args()
    result = scan(Path(args.root))
    Path(args.out).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {args.out} with {len(result['routes'])} items")
