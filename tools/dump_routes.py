# tools/dump_routes.py
from __future__ import annotations
import sys
from pathlib import Path

# гарантируем, что корень репозитория в sys.path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from main import app  # noqa: E402

def iter_route_lines():
    rules = sorted(app.url_map.iter_rules(), key=lambda r: r.rule)
    for r in rules:
        methods = ",".join(sorted(m for m in r.methods if m not in {"HEAD", "OPTIONS"}))
        yield f"{r.rule:<50}  endpoint={r.endpoint:<30}  methods={methods}"

def main():
    lines = list(iter_route_lines())

    md_path  = ROOT / "docs" / "ROUTES.md"
    txt_path = ROOT / "docs" / "ai_export" / "routes.txt"

    md_path.parent.mkdir(parents=True, exist_ok=True)
    txt_path.parent.mkdir(parents=True, exist_ok=True)

    md = "# ROUTES\n\n```\n" + "\n".join(lines) + "\n```\n"
    md_path.write_text(md, encoding="utf-8")
    txt_path.write_text("\n".join(lines), encoding="utf-8")

    print(f"[routes] {len(lines)} routes -> {md_path}")
    print(f"[routes] {len(lines)} routes -> {txt_path}")

if __name__ == "__main__":
    main()
