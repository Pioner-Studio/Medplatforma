#!/usr/bin/env python3
import sys, json, re, pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"

def fail(msg, code=1):
    print(f"[DRIFT] {msg}")
    sys.exit(code)

def main():
    ok = True

    # CHECK 1: docs/*.md существуют
    must = ["CHECKLIST.md", "ROADMAP.md", "STATUS.md"]
    for name in must:
        if not (DOCS / name).exists():
            print(f"[WARN] docs/{name} missing")
            ok = False

    # CHECK 2: в CHECKLIST.md нет пунктов «[ ]» помеченных как DONE
    # (пример примитивной проверки синтаксиса списка)
    cl = (DOCS / "CHECKLIST.md").read_text(encoding="utf-8") if (DOCS / "CHECKLIST.md").exists() else ""
    bad_lines = [ln for ln in cl.splitlines() if re.search(r"\[.\].*DONE", ln)]
    if bad_lines:
        print("[WARN] checklist odd lines:")
        for ln in bad_lines:
            print("   ", ln)
        ok = False

    # CHECK 3: ROUTES.md/TEMPLATES.md/STRUCTURE.md существуют
    for name in ["ROUTES.md", "TEMPLATES.md", "STRUCTURE.md"]:
        p = DOCS / name
        if not p.exists():
            print(f"[WARN] docs/{name} missing (run tools/generate_docs.py)")
            ok = False

    # exit
    if "--fail-on-error" in sys.argv and not ok:
        fail("Drift detected")
    print("[DRIFT] OK" if ok else "[DRIFT] WARN (non-fatal)")
    return 0

if __name__ == "__main__":
    sys.exit(main())
