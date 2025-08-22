# tools/export_project.py
# Экспортирует:
#  - список файлов (git tracked)
#  - дамп маршрутов Flask (через main.app)
#  - шаблоны/руты с нумерацией строк (ai_export/)
#  - чек-лист (docs/CHECKLIST.md) и reference (docs/reference.md)
#  - упаковывает в ZIP docs/export_YYYY-MM-DD_HH-MM-SS.zip

import os
import sys
import io
import zipfile
from datetime import datetime
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
AI_EXPORT = DOCS / "ai_export"
TOOLS = ROOT / "tools"
EXPORTS = DOCS   # складываем ZIP сюда

def run(cmd, cwd=ROOT):
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, shell=True)
    if r.returncode != 0:
        raise RuntimeError(f"Command failed: {cmd}\nSTDOUT:\n{r.stdout}\nSTDERR:\n{r.stderr}")
    return r.stdout.strip()

def ensure_dirs():
    (DOCS).mkdir(parents=True, exist_ok=True)
    (AI_EXPORT).mkdir(parents=True, exist_ok=True)

def export_filelist():
    out = run("git ls-files")
    p = DOCS / "filelist.txt"
    p.write_text(out, encoding="utf-8")
    return p

def export_line_numbered_sources():
    patterns = ["*.py","*.html","*.css","*.js"]
    created = []
    for pat in patterns:
        for f in ROOT.rglob(pat):
            # пропускаем виртуальное окружение и .git
            if ".venv" in f.parts or ".git" in f.parts: 
                continue
            rel = f.relative_to(ROOT)
            out = AI_EXPORT / (str(rel) + ".ln.txt")
            out.parent.mkdir(parents=True, exist_ok=True)
            try:
                lines = f.read_text(encoding="utf-8", errors="ignore").splitlines()
            except Exception:
                continue
            with out.open("w", encoding="utf-8") as w:
                for i, line in enumerate(lines, 1):
                    w.write(f"{i:5}: {line}\n")
            created.append(out)
    return created

def export_routes():
    # Чтобы не дублировать код, просто вызовем tools/dump_routes.py и сохраним вывод
    try:
        out = run(f"{sys.executable} {TOOLS / 'dump_routes.py'}")
    except RuntimeError as e:
        out = str(e)
    p = DOCS / "ROUTES.md"
    p.write_text(out, encoding="utf-8")
    return p

def export_checklist_reference():
    # Заготовки, чтобы ассистент всегда видел актуальные документы
    ck = DOCS / "CHECKLIST.md"
    if not ck.exists():
        ck.write_text("# CHECKLIST (живой)\n\n- [ ] Заполнить чек-лист\n", encoding="utf-8")
    rf = DOCS / "reference.md"
    if not rf.exists():
        rf.write_text("# reference.md\n\nГлоссарий и договорённости.\n", encoding="utf-8")
    return [ck, rf]

def make_zip(note: str = ""):
    ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    zname = EXPORTS / f"export_{ts}.zip"
    with zipfile.ZipFile(zname, "w", compression=zipfile.ZIP_DEFLATED) as z:
        # вложим docs, ai_export и важные файлы
        for p in (DOCS, AI_EXPORT):
            for f in p.rglob("*"):
                if f.is_file():
                    z.write(f, f.relative_to(ROOT))
        # положим маленькую заметку
        if note:
            z.writestr("docs/NOTE.txt", note)
    return zname

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--note", default="", help="Короткая заметка к экспорту")
    args = parser.parse_args()

    ensure_dirs()
    export_filelist()
    export_line_numbered_sources()
    export_checklist_reference()
    export_routes()
    z = make_zip(args.note)
    print(f"OK: экспорт готов -> {z}")

if __name__ == "__main__":
    main()
