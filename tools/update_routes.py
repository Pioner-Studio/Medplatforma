# -*- coding: utf-8 -*-
"""
update_routes.py — извлекает маршруты Flask и сохраняет в docs/routes.json.
Авто-находит приложение: пробует import main/app/wsgi, фабрику create_app(),
или загружает модуль по файлу, где есть Flask(__name__).
"""
import json, sys, re, importlib, importlib.util
from pathlib import Path
from typing import Optional

REPO_ROOT = Path(__file__).resolve().parents[1]
DOCS = REPO_ROOT / "docs"
OUT = DOCS / "routes.json"


def debug(msg: str):
    print(f"[update_routes] {msg}")


def try_import(modname: str):
    try:
        return importlib.import_module(modname)
    except Exception:
        return None


def load_by_path(py_path: Path):
    try:
        spec = importlib.util.spec_from_file_location(py_path.stem, py_path)
        if not spec or not spec.loader:
            return None
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)  # type: ignore
        return mod
    except Exception:
        return None


def find_flask_module() -> Optional[object]:
    # 1) добавим корень в sys.path
    sys.path.insert(0, str(REPO_ROOT))

    # 2) популярные имена
    for name in ("main", "app", "wsgi", "run", "server"):
        mod = try_import(name)
        if mod is not None:
            return mod

    # 3) фабрики приложения
    for name in ("main", "app"):
        mod = try_import(name)
        if mod and hasattr(mod, "create_app"):
            return mod

    # 4) поиск по файлам: где встречается "Flask("
    for p in REPO_ROOT.rglob("*.py"):
        try:
            text = p.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        if "Flask(" in text:
            mod = load_by_path(p)
            if mod is not None:
                return mod
    return None


def resolve_app(mod) -> Optional[object]:
    # 1) атрибут app
    if hasattr(mod, "app"):
        return getattr(mod, "app")

    # 2) фабрика create_app()
    if hasattr(mod, "create_app"):
        try:
            app = mod.create_app()
            if app is not None:
                return app
        except Exception:
            pass

    # 3) поиск переменной вида app = Flask(__name__)
    for attr in dir(mod):
        obj = getattr(mod, attr)
        try:
            # у Flask-приложения есть url_map
            if hasattr(obj, "url_map") and hasattr(obj, "add_url_rule"):
                return obj
        except Exception:
            continue
    return None


def collect_routes(app):
    routes = []
    for rule in app.url_map.iter_rules():
        if "static" in rule.endpoint:
            continue
        routes.append(
            {
                "endpoint": rule.endpoint,
                "methods": sorted(list(rule.methods - {"HEAD", "OPTIONS"})),
                "rule": str(rule),
            }
        )
    return routes


def main():
    DOCS.mkdir(parents=True, exist_ok=True)
    debug(f"repo_root={REPO_ROOT}")

    mod = find_flask_module()
    if not mod:
        print(
            "[update_routes] ERROR: не удалось найти модуль Flask (main/app/wsgi).", file=sys.stderr
        )
        sys.exit(1)

    app = resolve_app(mod)
    if not app:
        print("[update_routes] ERROR: не удалось получить объект Flask app.", file=sys.stderr)
        sys.exit(1)

    routes = collect_routes(app)
    OUT.write_text(json.dumps(routes, ensure_ascii=False, indent=2), encoding="utf-8")
    debug(f"Saved {len(routes)} routes to {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
