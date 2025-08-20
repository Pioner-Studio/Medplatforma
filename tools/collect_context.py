import argparse, inspect, pathlib, re, sys
from textwrap import indent

ROOT = pathlib.Path(__file__).resolve().parents[1]

def read(path: pathlib.Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")

def find_app():
    sys.path.insert(0, str(ROOT))
    # подстрой под свой вход: main.py с app
    from main import app  # noqa: E402
    return app

def dump_routes():
    app = find_app()
    rows = []
    for r in sorted(app.url_map.iter_rules(), key=lambda x: x.rule):
        methods = ",".join(sorted(m for m in r.methods if m not in {"HEAD","OPTIONS"}))
        rows.append(f"- `{r.rule}`  → **{r.endpoint}**  [{methods}]")
    print("# ROUTES\n")
    print("\n".join(rows))

def dump_endpoint(name: str):
    app = find_app()
    view = app.view_functions.get(name)
    if not view:
        sys.exit(f"Endpoint '{name}' not found")
    src = inspect.getsource(view)
    file = inspect.getsourcefile(view)
    print(f"=== BEGIN ENDPOINT: {name} ({file}) ===")
    print(src.rstrip())
    print("=== END ENDPOINT ===")
    # попробуем показать декораторы маршрутов из исходника файла
    if file:
        text = read(pathlib.Path(file))
        # грубо: ищем все @app.route(...) прямо над функцией
        pat = re.compile(rf"(@app\.route\([^)]+\)\s*\n)+def\s+{view.__name__}\b", re.M)
        m = pat.search(text)
        if m:
            print("\n# Decorators\n")
            print(indent(m.group(0).split("def")[0].rstrip(), "    "))

def dump_template(path: str):
    p = ROOT / path
    if not p.exists():
        sys.exit(f"Template not found: {p}")
    print(f"=== BEGIN FILE: {path} ===")
    print(read(p).rstrip())
    print("=== END FILE ===")

def dump_bundle(patterns):
    print("# REVIEW BUNDLE\n")
    for pat in patterns:
        for p in sorted(ROOT.glob(pat)):
            if p.is_file():
                print(f"\n=== BEGIN FILE: {p.relative_to(ROOT)} ===")
                print(read(p).rstrip())
                print("=== END FILE ===")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--routes", action="store_true")
    ap.add_argument("--endpoint")
    ap.add_argument("--template")
    ap.add_argument("--bundle", nargs="+")
    args = ap.parse_args()

    try:
        if args.routes:
            dump_routes()
        elif args.endpoint:
            dump_endpoint(args.endpoint)
        elif args.template:
            dump_template(args.template)
        elif args.bundle:
            dump_bundle(args.bundle)
        else:
            print("Use --routes | --endpoint <name> | --template <path> | --bundle <globs...>")
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        raise
