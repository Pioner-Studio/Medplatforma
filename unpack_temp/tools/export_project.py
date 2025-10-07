# tools/export_project.py
from __future__ import annotations
import os, sys, io, textwrap, zipfile, subprocess
from datetime import datetime
from pathlib import Path

# ---------- настройки ----------
PROJECT_ROOT = Path(__file__).resolve().parents[1]
EXPORT_BASE  = PROJECT_ROOT / "docs" / "ai_export"
DOCS_DIR     = PROJECT_ROOT / "docs"
TEMPLATES_DIR= PROJECT_ROOT / "templates"
INCLUDE_GLOBS= ("*.py","*.html","*.css","*.js")
EXCLUDE_DIRS = {".git", ".venv", "__pycache__", "node_modules", "dist", "build"}
TREE_SKIP    = EXCLUDE_DIRS | {"docs", "static/avatars", "static/ztl"}

# ---------- вспомогательные ----------
def ts() -> str:
    return datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

def rel(p: Path) -> str:
    return str(p.relative_to(PROJECT_ROOT)).replace("\\","/")

def ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)

def number_lines(text: str) -> str:
    out = io.StringIO()
    for i, line in enumerate(text.splitlines(True), 1):
        out.write(f"{i:5}: {line}")
    return out.getvalue()

def tree(root: Path, skip: set[str]) -> str:
    lines = []
    for base, dirs, files in os.walk(root):
        b = Path(base)
        r = rel(b)
        name = "." if b == root else r
        depth = 0 if b == root else len(r.split("/"))
        # фильтр папок «на месте», чтобы os.walk внутрь не заходил
        dirs[:] = sorted([d for d in dirs if d not in skip and not d.startswith(".")])
        files = sorted([f for f in files if not f.startswith(".")])
        prefix = "    " * depth
        if b != root:
            lines.append(f"{prefix}{b.name}/")
        for f in files:
            lines.append(f"{prefix}    {f}")
    return "\n".join(lines)

def git_ls_files() -> list[str]:
    try:
        out = subprocess.check_output(["git","ls-files"], cwd=PROJECT_ROOT, text=True, stderr=subprocess.DEVNULL)
        return [ln.strip() for ln in out.splitlines() if ln.strip()]
    except Exception:
        # fallback: просто пройтись по диску
        files = []
        for base, dirs, fs in os.walk(PROJECT_ROOT):
            b = Path(base)
            if b.name in EXCLUDE_DIRS: 
                dirs[:] = []  # внутрь не идём
                continue
            dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS and not d.startswith(".")]
            for f in fs:
                if f.startswith("."): 
                    continue
                files.append(rel(b/ f))
        return files

# ---------- попытка импортировать Flask-приложение ----------
def load_flask_app():
    sys.path.insert(0, str(PROJECT_ROOT))
    try:
        from main import app  # type: ignore
        return app
    except Exception as e:
        print(f"[warn] Не удалось импортировать main.app: {e}")
        return None

# ---------- выгрузка маршрутов ----------
def dump_routes(app, out_dir: Path) -> str:
    routes_md = out_dir / "ROUTES.md"
    routes_txt = out_dir / "routes.txt"
    if app is None:
        routes_md.write_text("# ROUTES (не удалось импортировать Flask-приложение)\n", encoding="utf-8")
        routes_txt.write_text("Импорт main.app не удался — маршруты недоступны.\n", encoding="utf-8")
        return "0"

    rules = sorted(app.url_map.iter_rules(), key=lambda r: r.rule)
    lines_md = ["# ROUTES", ""]
    lines_txt = []
    cnt = 0
    for r in rules:
        methods = ",".join(sorted(m for m in r.methods if m not in {"HEAD","OPTIONS"}))
        lines_md.append(f"- `{r.rule}`  → **{r.endpoint}**  _[{methods}]_")
        lines_txt.append(f"{r.rule:50} endpoint={r.endpoint:25} methods={methods}")
        cnt += 1
    routes_md.write_text("\n".join(lines_md) + "\n", encoding="utf-8")
    routes_txt.write_text("\n".join(lines_txt) + "\n", encoding="utf-8")
    return str(cnt)

# ---------- выгрузка шаблонов и исходников со строками ----------
def dump_sources(out_dir: Path) -> dict[str,int]:
    stats = {"files":0, "templates":0}
    for pat in INCLUDE_GLOBS:
        for p in PROJECT_ROOT.rglob(pat):
            # пропустим мусор
            if any(part in EXCLUDE_DIRS for part in p.parts): 
                continue
            if "/." in rel(p): 
                continue
            data = p.read_text(encoding="utf-8", errors="ignore")
            numbered = number_lines(data)
            target = out_dir / (rel(p) + ".ln.txt")
            ensure_dir(target.parent)
            target.write_text(numbered, encoding="utf-8")
            stats["files"] += 1
            if p.suffix == ".html":
                stats["templates"] += 1
    return stats

# ---------- структура проекта ----------
def dump_structure(out_dir: Path) -> None:
    STRUCT = out_dir / "STRUCTURE.md"
    TREE = tree(PROJECT_ROOT, TREE_SKIP)
    STRUCT.write_text("# STRUCTURE\n\n```\n"+TREE+"\n```\n", encoding="utf-8")

# ---------- чек-лист ----------
CHECKLIST_TEMPLATE = """# CHECKLIST

- [ ] Подтянуть `main.py` и запустить приложение локально
- [ ] Проверить авторизацию и доступ к MongoDB (переменная `MONGO_URI` в `.env`)
- [ ] Заполнить демо-данные при необходимости (скрипты `seed_*.py`)
- [ ] Проверить ключевые экраны: Календарь, Пациенты, Сообщения, Отчёты
- [ ] Сделать ежедневную синхронизацию (commit → push), создать `docs.zip`
- [ ] Отметить прогресс в `docs/ROADMAP.md` и `docs/STATUS.md`
"""

def update_checklist(out_dir: Path) -> None:
    checklist_dst = out_dir / "CHECKLIST.md"
    repo_checklist = DOCS_DIR / "CHECKLIST.md"
    if repo_checklist.exists():
        checklist_dst.write_text(repo_checklist.read_text(encoding="utf-8"), encoding="utf-8")
    else:
        checklist_dst.write_text(CHECKLIST_TEMPLATE, encoding="utf-8")

# ---------- статус ----------
def write_status(out_dir: Path, routes_count: str, files_cnt: int, tmpl_cnt: int) -> None:
    status = out_dir / "STATUS.md"
    status.write_text(textwrap.dedent(f"""
        # STATUS
        - timestamp: {datetime.now().isoformat(timespec="seconds")}
        - routes: {routes_count}
        - files (with line numbers): {files_cnt}
        - templates: {tmpl_cnt}
    """).strip()+"\n", encoding="utf-8")

# ---------- упаковка в zip ----------
def pack_zip(subdir: Path) -> Path:
    zip_path = DOCS_DIR / f"export_{subdir.name}.zip"
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for p in subdir.rglob("*"):
            if p.is_file():
                z.write(p, arcname=str(Path("ai_export")/subdir.name/p.relative_to(subdir)))
    return zip_path

# ---------- основная процедура ----------
def main():
    os.chdir(PROJECT_ROOT)
    ensure_dir(EXPORT_BASE)
    subdir = EXPORT_BASE / ts()
    ensure_dir(subdir)

    app = load_flask_app()
    routes_count = dump_routes(app, subdir)
    stats = dump_sources(subdir)
    dump_structure(subdir)
    update_checklist(subdir)
    write_status(subdir, routes_count, stats["files"], stats["templates"])

    # список файлов по git
    (subdir / "INVENTORY.md").write_text(
        "# INVENTORY (git ls-files)\n\n" + "\n".join(f"- {p}" for p in git_ls_files()) + "\n",
        encoding="utf-8"
    )

    zip_path = pack_zip(subdir)
    print(f"[ok] Экспорт готов: {rel(subdir)}")
    print(f"[ok] Архив: {rel(zip_path)}")

if __name__ == "__main__":
    main()
