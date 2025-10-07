#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
arch_verify.py — быстрый сканер маршрутов/шаблонов для Flask/Jinja/JS
Usage:
    python arch_verify.py --root . --out routes.json
"""

import os, re, json, argparse
from pathlib import Path
from fnmatch import fnmatch  # NEW

# Каталоги, которые игнорируем при сканировании
EXCLUDE_DIRS = {
    "attic",
    ".git",
    ".venv",
    "venv",
    "env",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    "dist",
    "build",
    ".idea",
    ".vscode",
}

# Файлы (по шаблонам), которые не сканируем даже если лежат в корне проекта
EXCLUDE_FILE_GLOBS = [
    "implement_*.py",
    "add_missing_*.py",
    "add_*_routes*.py",
    "*_api_insert.py",
    "*insert*.py",
    "remove_*_final*.py",
]

ROUTE_PATTERNS = [
    re.compile(
        r'@(?:app|[\w_]+)\.route\(\s*[\'"]([^\'"]+)[\'"]\s*(?:,\s*methods\s*=\s*\[([^\]]+)\])?\s*\)'
    ),
]
RENDER_PATTERNS = [
    re.compile(r'render_template\(\s*[\'"]([^\'"]+)[\'"]'),
]
JS_FETCH = re.compile(r'fetch\(\s*[\'"](/[^\'"]+)[\'"]')
JS_HREF = re.compile(
    r'location\.href\s*=\s*[\'"](/[^\'"]+)[\'"]|window\.location\.href\s*=\s*[\'"](/[^\'"]+)[\'"]'
)


def sniff_methods(m):
    if not m:
        return ["GET"]
    # methods=['GET','POST']
    items = [s.strip().strip("'\"") for s in m.split(",") if s.strip()]
    return items or ["GET"]


def should_skip(path: Path, root: Path) -> bool:
    """Пропускаем всё, что внутри EXCLUDE_DIRS."""
    try:
        rel_parts = path.relative_to(root).parts
    except ValueError:
        return True
    for part in rel_parts:
        if part in EXCLUDE_DIRS:
            return True
    return False


def scan(root: Path):
    routes = []
    templates = set()
    js_calls = set()

    for p in root.rglob("*.*"):
        if should_skip(p, root):
            continue
        # NEW: пропускаем временные/одноразовые файлы по шаблонам
        if any(fnmatch(p.name, pat) for pat in EXCLUDE_FILE_GLOBS):
            continue

        suffix = p.suffix.lower()
        if suffix not in (".py", ".js", ".html", ".jinja", ".jinja2", ".j2", ".ts"):
            continue

        try:
            text = p.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue

        if suffix == ".py":
            for rp in ROUTE_PATTERNS:
                for m in rp.finditer(text):
                    path = m.group(1)
                    methods_raw = m.group(2)
                    methods = sniff_methods(methods_raw)
                    routes.append({"file": str(p), "route": path, "methods": methods})

            for m in RENDER_PATTERNS:
                for mt in m.finditer(text):
                    templates.add(mt.group(1))

        if suffix in (".js", ".html", ".ts", ".jinja", ".jinja2", ".j2"):
            for m in JS_FETCH.finditer(text):
                js_calls.add(m.group(1))
            for m in JS_HREF.finditer(text):
                js_calls.add(m.group(1) or m.group(2))

    return {
        "routes": routes,
        "templates": sorted(templates),
        "js_calls": sorted(js_calls),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".", help="Корень проекта")
    ap.add_argument("--out", default="routes.json", help="Куда сохранить JSON")
    args = ap.parse_args()

    root = Path(args.root).resolve()
    data = scan(root)

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    # Краткий отчёт
    print("=== ROUTES ===")
    for r in data["routes"]:
        print(f"{r['methods']} {r['route']}  <- {r['file']}")
    print("\n=== TEMPLATES ===")
    for t in data["templates"]:
        print(t)
    print("\n=== JS CALLS ===")
    for u in data["js_calls"]:
        print(u)


if __name__ == "__main__":
    main()
