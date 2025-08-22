# tools/dump_routes.py
# Печатает таблицу всех маршрутов Flask из main.app

import os
from pathlib import Path
from importlib import import_module

ROOT = Path(__file__).resolve().parents[1]
import sys
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

app = import_module("main").app   # важно: у тебя main.py

def format_rule(r):
    methods = ",".join(sorted(m for m in r.methods if m not in {"HEAD","OPTIONS"}))
    return f"{r.rule:50}  endpoint={r.endpoint:30}  methods={methods}"

lines = ["# ROUTES\n"]
for r in sorted(app.url_map.iter_rules(), key=lambda x: x.rule):
    lines.append(format_rule(r))
print("\n".join(lines))
