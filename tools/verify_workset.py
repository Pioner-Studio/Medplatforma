# tools/verify_workset.py
from pathlib import Path
need = [
    "main.py",
    "routes_finance.py",
    "templates/finance/list.html",
    "templates/finance/add.html",
    "docs/CHECKLIST.md",
    "docs/ROUTES.md",
    "docs/STRUCTURE.md",
]
missing = [p for p in need if not Path(p).exists()]
if missing:
    print("MISSING files:")
    for p in missing: print(" -", p)
    raise SystemExit(1)
print("OK: required files present.")
