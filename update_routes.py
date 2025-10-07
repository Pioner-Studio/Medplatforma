#!/usr/bin/env python3
from pathlib import Path
import json, datetime

ROOT = Path(__file__).resolve().parent
DOCS = ROOT / "docs"
ROUTES_JSON = DOCS / "routes.json"

def gen_md(data: dict) -> str:
    lines = ["# ROUTES", ""]
    lines += ["| Route | Methods | File |",
              "|---|---|---|"]
    for r in sorted(data.get("routes", []), key=lambda x: x["route"]):
        methods = ",".join(r.get("methods") or [])
        lines.append(f"| `{r['route']}` | {methods} | `{Path(r['file']).as_posix()}` |")
    lines.append("")
    lines.append(f"> Auto-generated {datetime.datetime.now().isoformat(timespec='seconds')}")
    return "\n".join(lines)

def main():
    data = json.loads(ROUTES_JSON.read_text(encoding="utf-8"))
    md = gen_md(data)
    (DOCS / "ROUTES.md").write_text(md, encoding="utf-8", newline="\n")
    (ROOT / "ROUTES.md").write_text(md, encoding="utf-8", newline="\n")
    print("[update_routes] Updated docs/ROUTES.md and ROUTES.md")

if __name__ == "__main__":
    main()
