#!/usr/bin/env python3
import os,re,json,argparse
from pathlib import Path
from fnmatch import fnmatch
EXCLUDE_DIRS={"attic",".git",".venv","venv","env","node_modules","__pycache__",".pytest_cache",".mypy_cache","dist","build",".idea",".vscode"}
EXCLUDE_FILE_GLOBS=["implement_*.py","integrate_*.py","integration_*.py","add_missing_*.py","add_*_routes*.py","add_*_api*.py","*_api_insert.py","*insert*.py","remove_*_final*.py"]
ROUTE_PATTERNS=[re.compile(r'@(?:app|[\w_]+)\.route\(\s*[\'"]([^\'"]+)[\'"]\s*(?:,\s*methods\s*=\s*\[([^\]]+)\])?\s*\)')]
RENDER_PATTERN=re.compile(r'render_template\(\s*[\'"]([^\'"]+)[\'"]')
JS_FETCH=re.compile(r'fetch\(\s*[\'"](/[^\'"]+)[\'"]')
JS_HREF=re.compile(r'(?:location|window\.location)\.href\s*=\s*[\'"](/[^\'"]+)[\'"]')
def sniff(m): 
    if not m: return ["GET"]
    return [s.strip().strip("'\"") for s in m.split(",") if s.strip()] or ["GET"]
def should_skip(p,root):
    try: parts=p.relative_to(root).parts
    except: return True
    return any(part in EXCLUDE_DIRS for part in parts)
def scan(root:Path):
    routes=[]; templates=set(); js=set()
    for p in root.rglob("*.*"):
        if should_skip(p,root): continue
        if any(fnmatch(p.name,pat) for pat in EXCLUDE_FILE_GLOBS): continue
        suf=p.suffix.lower()
        if suf not in (".py",".js",".html",".jinja",".jinja2",".j2",".ts"): continue
        try: text=p.read_text(encoding="utf-8",errors="ignore")
        except: continue
        if suf==".py":
            for rp in ROUTE_PATTERNS:
                for m in rp.finditer(text):
                    routes.append({"file":str(p),"route":m.group(1),"methods":sniff(m.group(2))})
            for t in RENDER_PATTERN.finditer(text): templates.add(t.group(1))
        if suf in (".js",".html",".ts",".jinja",".jinja2",".j2"):
            for m in JS_FETCH.finditer(text): js.add(m.group(1))
            for m in JS_HREF.finditer(text): js.add(m.group(1) or m.group(2))
    return {"routes":routes,"templates":sorted(templates),"js_calls":sorted(js)}
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--root",default=".")
    ap.add_argument("--out",default="docs/routes.json")
    a=ap.parse_args()
    root=Path(a.root).resolve()
    data=scan(root)
    Path(a.out).parent.mkdir(parents=True,exist_ok=True)
    with open(a.out,"w",encoding="utf-8") as f: json.dump(data,f,ensure_ascii=False,indent=2)
    print("=== ROUTES ==="); [print(f"{r['methods']} {r['route']}  <- {r['file']}") for r in data["routes"]]
    print("\n=== TEMPLATES ==="); [print(t) for t in data["templates"]]
    print("\n=== JS CALLS ==="); [print(u) for u in data["js_calls"]]
if __name__=="__main__": main()
