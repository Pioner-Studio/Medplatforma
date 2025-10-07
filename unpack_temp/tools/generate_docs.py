# tools/generate_docs.py
# ClubStom docs + zip generator
import argparse
import datetime as dt
import importlib.util
import io
import json
import os
from pathlib import Path
import sys
import traceback
import zipfile
import ast

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
EXPORTS = ROOT / "exports"
TEMPLATES_DIR = ROOT / "templates"
STATIC_DIR = ROOT / "static"

DOCS.mkdir(exist_ok=True)
EXPORTS.mkdir(exist_ok=True)

def _load_flask_app():
    """
    Импортирует app из main.py (или из файла, переданного через --app).
    Возвращает (app, error_text|None)
    """
    # ищем main.py в корне
    main_py = ROOT / "main.py"
    if not main_py.exists():
        return None, f"main.py не найден по пути: {main_py}"

    spec = importlib.util.spec_from_file_location("clubstom_main", main_py)
    mod = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)  # type: ignore
        app = getattr(mod, "app", None)
        if app is None:
            return None, "В main.py не найден объект Flask 'app'."
        return app, None
    except Exception:
        tb = traceback.format_exc()
        return None, tb


def _dump_routes_md(app) -> str:
    lines = ["# ROUTES", ""]
    rows = []
    dup_by_endpoint = {}

    for r in app.url_map.iter_rules():
        if r.endpoint == "static":
            continue
        methods = ",".join(sorted(m for m in r.methods if m not in {"HEAD", "OPTIONS"}))
        rows.append((str(r.rule), r.endpoint, methods))
        dup_by_endpoint.setdefault(r.endpoint, set()).add(str(r.rule))

    rows.sort(key=lambda x: (x[0], x[1]))
    lines.append("| Route | Endpoint | Methods |")
    lines.append("|---|---|---|")
    for route, endpoint, methods in rows:
        lines.append(f"| `{route}` | **{endpoint}** | {methods} |")

    # дубликаты endpoint'ов (один endpoint на разные правила — это ок,
    # но если их очень много — будем видеть внизу)
    dups = {k: v for k, v in dup_by_endpoint.items() if len(v) > 1}
    if dups:
        lines += ["", "## Endpoint duplicates (review)", ""]
        for ep, rules in sorted(dups.items()):
            lines.append(f"- **{ep}** → {', '.join(f'`{x}`' for x in sorted(rules))}")

    return "\n".join(lines) + "\n"


def _dump_templates_md() -> str:
    lines = ["# TEMPLATES", ""]
    if not TEMPLATES_DIR.exists():
        lines.append("_templates/ отсутствует_")
        return "\n".join(lines) + "\n"

    def rel(p: Path) -> str:
        return str(p.relative_to(ROOT)).replace("\\", "/")

    files = sorted(TEMPLATES_DIR.rglob("*.*"))
    lines.append("| File | Size |")
    lines.append("|---|---:|")
    for f in files:
        if f.is_file():
            lines.append(f"| `{rel(f)}` | {f.stat().st_size} |")
    return "\n".join(lines) + "\n"


def _dump_inventory_md() -> str:
    lines = ["# INVENTORY", ""]
    def tree(base: Path, title: str):
        lines.append(f"## {title}")
        if not base.exists():
            lines.append(f"_{base.name} отсутствует_")
            lines.append("")
            return
        for p in sorted(base.rglob("*")):
            if p.is_dir():
                continue
            rel = str(p.relative_to(ROOT)).replace("\\", "/")
            size = p.stat().st_size
            lines.append(f"- `{rel}` ({size} bytes)")
        lines.append("")

    tree(TEMPLATES_DIR, "templates/")
    tree(STATIC_DIR, "static/")
    return "\n".join(lines)


def _append_status_md(note: str | None):
    status = ROOT / "docs" / "STATUS.md"
    ts = dt.datetime.now().strftime("%Y-%m-%d %H:%M")
    block = [
        f"### {ts}",
        "- Экспорт маршрутов/структуры выполнен.",
    ]
    if note:
        block.append(f"- Заметка: {note}")
    block.append("")
    previous = status.read_text(encoding="utf-8") if status.exists() else "# STATUS\n\n"
    status.write_text(previous + "\n".join(block), encoding="utf-8")


def _make_zip(note: str | None) -> Path:
    ts = dt.datetime.now().strftime("%Y-%m-%d_%H-%M")
    zip_path = EXPORTS / f"clubstom_{ts}.zip"

    # что кладём
    include = [
        "main.py",
        "requirements.txt",
        "templates/",
        "static/",
        "uploads/",
        "docs/",
        "tools/",
    ]
    exclude_prefixes = {
        ".git", "__pycache__", "venv", ".venv", "exports", ".mypy_cache",
        ".pytest_cache", ".idea", ".vscode"
    }

    def allowed(path: Path) -> bool:
        parts = set(p.name for p in path.parents)
        if any(seg in exclude_prefixes for seg in parts):
            return False
        name = path.name
        if name in exclude_prefixes:
            return False
        return True

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for item in include:
            src = ROOT / item
            if not src.exists():
                continue
            if src.is_file():
                if allowed(src):
                    zf.write(src, arcname=str(src.relative_to(ROOT)))
            else:
                for f in src.rglob("*"):
                    if f.is_file() and allowed(f):
                        zf.write(f, arcname=str(f.relative_to(ROOT)))
        # manifest.json внутрь архива
        manifest = {
            "generated_at": dt.datetime.now().isoformat(timespec="seconds"),
            "note": note or "",
            "root": str(ROOT),
        }
        zf.writestr("manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2))
    return zip_path

# ---- LINT: простые проверки дублей ----

def _lint_project(app) -> tuple[list[str], int]:
    problems = []

    # 1) дубли endpoint-ов -> разные функции с одинаковым именем в url_map не поймаем,
    #   но увидим много правил на один endpoint
    endpoint_to_rules = {}
    rule_to_methods = {}
    for r in app.url_map.iter_rules():
        if r.endpoint == "static":
            continue
        endpoint_to_rules.setdefault(r.endpoint, set()).add(str(r.rule))
        rule_to_methods.setdefault(str(r.rule), set()).update(r.methods or set())

    for ep, rules in endpoint_to_rules.items():
        if len(rules) > 1:
            problems.append(f"[routes] endpoint '{ep}' обслуживает несколько правил: {sorted(rules)}")

    # 2) дубли путей (одно и то же правило добавлено много раз)
    for rule, methods in rule_to_methods.items():
        # это не строгий дубль, но если у нас одно и то же правило объявлено несколько раз,
        # обычно это признак копипасты. Отметим, если >3 методов (GET/POST/PUT/DELETE) странно.
        pass

    # 3) дубли функций в main.py
    main_py = ROOT / "main.py"
    if main_py.exists():
        tree = ast.parse(main_py.read_text(encoding="utf-8"))
        fnames = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                fnames.setdefault(node.name, 0)
                fnames[node.name] += 1
        dups = [name for name, cnt in fnames.items() if cnt > 1]
        for name in sorted(dups):
            problems.append(f"[code] функция '{name}' определена несколько раз")

    return problems, len(problems)

def main():
    parser = argparse.ArgumentParser(description="ClubStom docs/zip generator")
    parser.add_argument("--zip", action="store_true", help="сделать архив проекта в /exports")
    parser.add_argument("--note", type=str, default="", help="заметка/комментарий в STATUS.md и manifest.json")
    args = parser.parse_args()

    app, err = _load_flask_app()
    if err:
        # пишем ошибку в ROUTES.md и выходим «мягко»
        (DOCS / "ROUTES.md").write_text(
            "# ROUTES\n\n"
            "Не удалось импортировать приложение:\n\n```\n"
            + err +
            "\n```\n",
            encoding="utf-8",
        )
        print("[WARN] Ошибка импорта app. Подробности в docs/ROUTES.md")
    else:
        routes_md = _dump_routes_md(app)
        (DOCS / "ROUTES.md").write_text(routes_md, encoding="utf-8")
        print("[OK] docs/ROUTES.md обновлён")

    (DOCS / "TEMPLATES.md").write_text(_dump_templates_md(), encoding="utf-8")
    (DOCS / "INVENTORY.md").write_text(_dump_inventory_md(), encoding="utf-8")
    _append_status_md(args.note)

    if args.zip:
        path = _make_zip(args.note)
        print(f"[OK] Архив создан: {path}")

if __name__ == "__main__":
    main()
