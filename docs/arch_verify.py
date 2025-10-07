#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
arch_verify.py — быстрый сканер маршрутов/шаблонов для Flask/Jinja/JS
Usage:
    python arch_verify.py --root . --out routes.json
"""
import os, re, json, argparse
from pathlib import Path

ROUTE_PATTERNS = [
    re.compile(r'@(?:app|[\w_]+)\.route\(\s*[\'"]([^\'"]+)[\'"]\s*(?:,\s*methods\s*=\s*\[([^\]]+)\])?\s*\)'),
]
RENDER_PATTERNS = [
    re.compile(r'render_template\(\s*[\'"]([^\'"]+)[\'"]'),
]
JS_FETCH = re.compile(r'fetch\(\s*[\'"](/[^\'"]+)[\'"]')
JS_HREF  = re.compile(r'location\.href\s*=\s*[\'"](/[^\'"]+)[\'"]|window\.location\.href\s*=\s*[\'"](/[^\'"]+)[\'"]')

def sniff_methods(m):
    if not m: return ['GET']
    # methods=['GET','POST']
    items = [s.strip().strip("'\"") for s in m.split(',') if s.strip()]
    return items or ['GET']

def scan(root: Path):
    routes = []
    templates = set()
    js_calls = set()

    for p in root.rglob('*.*'):
        if p.suffix.lower() not in ('.py','.js','.html','.jinja','.jinja2','.j2','.ts'):
            continue
        try:
            text = p.read_text(encoding='utf-8', errors='ignore')
        except Exception:
            continue

        if p.suffix.lower() == '.py':
            for rp in ROUTE_PATTERNS:
                for m in rp.finditer(text):
                    path = m.group(1)
                    methods_raw = m.group(2)
                    methods = sniff_methods(methods_raw)
                    routes.append({'file': str(p), 'route': path, 'methods': methods})

            for m in RENDER_PATTERNS:
                for mt in m.finditer(text):
                    templates.add(mt.group(1))

        if p.suffix.lower() in ('.js', '.html', '.ts'):
            for m in JS_FETCH.finditer(text):
                js_calls.add(m.group(1))
            for m in JS_HREF.finditer(text):
                js_calls.add(m.group(1) or m.group(2))

    return {
        'routes': routes,
        'templates': sorted(templates),
        'js_calls': sorted(js_calls),
    }

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--root', default='.', help='Корень проекта')
    ap.add_argument('--out', default='routes.json', help='Куда сохранить JSON')
    args = ap.parse_args()

    root = Path(args.root).resolve()
    data = scan(root)

    with open(args.out, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    # Вывод краткого отчёта
    print('=== ROUTES ===')
    for r in data['routes']:
        print(f"{r['methods']} {r['route']}  <- {r['file']}")
    print('\n=== TEMPLATES ===')
    for t in data['templates']:
        print(t)
    print('\n=== JS CALLS ===')
    for u in data['js_calls']:
        print(u)

if __name__ == '__main__':
    main()
