# tools/make_export.py
import os
import io
import zipfile
from pathlib import Path
from datetime import datetime

ROOT = Path(".").resolve()
EXPORT_DIR = ROOT / "docs" / "ai_export"
EXPORT_DIR.mkdir(parents=True, exist_ok=True)

# какие расширения выгружать с нумерацией строк
GLOB_PATTERNS = ["**/*.py", "**/*.html", "**/*.css", "**/*.js"]

# что исключать
EXCLUDE_DIRS = {".git", ".venv", "venv", "__pycache__", "node_modules", "docs/ai_export"}
EXCLUDE_FILES = set()

def is_excluded(path: Path) -> bool:
    parts = set([p.name for p in path.parents] | {path.name})
    if any(d in EXCLUDE_DIRS for d in parts):
        return True
    if path.name in EXCLUDE_FILES:
        return True
    return False

def rel(p: Path) -> str:
    return str(p.relative_to(ROOT)).replace("\\", "/")

# 1) список файлов проекта (отдельный список)
filelist = []
for pattern in GLOB_PATTERNS:
    for p in ROOT.glob(pattern):
        if p.is_file() and not is_excluded(p):
            filelist.append(p)

# 2) выгрузка с номерами строк
for p in filelist:
    dest = EXPORT_DIR / (rel(p) + ".ln.txt")
    dest.parent.mkdir(parents=True, exist_ok=True)
    with p.open("r", encoding="utf-8", errors="replace") as f:
        lines = f.readlines()
    with dest.open("w", encoding="utf-8") as out:
        for i, line in enumerate(lines, 1):
            out.write(f"{i:5}: {line.rstrip()}\n")

# 3) сохраняем filelist.txt
with (EXPORT_DIR / "filelist.txt").open("w", encoding="utf-8") as f:
    for p in sorted(filelist, key=lambda x: rel(x)):
        f.write(rel(p) + "\n")

print(f"[OK] numbered sources -> {EXPORT_DIR}")

# 4) общий ZIP проекта (исключая тяжёлые/временные директории)
STAMP = datetime.now().strftime("%Y%m%d_%H%M")
ZIP_DIR = ROOT / "docs" / "exports"
ZIP_DIR.mkdir(parents=True, exist_ok=True)
zip_path = ZIP_DIR / f"medplatforma_{STAMP}.zip"

INCLUDE_TOP = ["."]  # всё из репозитория
EXCLUDE_ZIP_DIRS = {".git", ".venv", "venv", "__pycache__", "node_modules", ".mypy_cache", ".pytest_cache"}

def zip_filter(p: Path) -> bool:
    # исключаем служебное
    parts = set([pp.name for pp in p.parents] | {p.name})
    if any(d in EXCLUDE_ZIP_DIRS for d in parts):
        return False
    return True

with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as z:
    for base in INCLUDE_TOP:
        for p in Path(base).rglob("*"):
            if p.is_file() and zip_filter(p):
                z.write(p, arcname=rel(p))

print(f"[OK] project zip -> {zip_path}")
