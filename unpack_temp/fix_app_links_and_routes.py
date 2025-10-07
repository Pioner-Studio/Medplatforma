import re, sys, pathlib

ROOT = pathlib.Path(__file__).parent


def patch_file(p: pathlib.Path, rules):
    txt = p.read_text(encoding="utf-8")
    orig = txt
    for pat, repl in rules:
        txt = re.sub(pat, repl, txt, flags=re.M)
    if txt != orig:
        p.write_text(txt, encoding="utf-8")
        print(f"[fix] {p.name} patched")
    else:
        print(f"[ok ] {p.name} unchanged")


def ensure_patient_card_route(main_py: pathlib.Path):
    txt = main_py.read_text(encoding="utf-8")
    # Удаляем дубликаты декораторов на /patients/<pid>, оставляем один endpoint
    parts = re.split(r'(@app\.get\("/patients/<pid>".*?def\s+\w+\(pid\):)', txt, flags=re.S)
    if len(parts) > 3:
        # оставляем первый блок
        first = parts[0] + parts[1]
        # выкидываем остальные дубликаты определений
        rest = re.sub(
            r'@app\.get\("/patients/<pid>".*?def\s+\w+\(pid\):.*?(?=@app\.|$)',
            "",
            "".join(parts[2:]),
            flags=re.S,
        )
        txt = first + rest
    # приводим endpoint к единому
    txt = re.sub(
        r'@app\.get\("/patients/<pid>"(?:, *endpoint *= *"[^"]*")?\)',
        '@app.get("/patients/<pid>", endpoint="patient_card_page")',
        txt,
    )
    main_py.write_text(txt, encoding="utf-8")
    print("[fix] patient_card_page endpoint normalized")


def main():
    main_py = ROOT / "main.py"
    base_html = ROOT / "templates" / "base.html"

    # 1) ссылки в сайдбаре
    patch_file(
        base_html,
        [
            (r'href *= *"\/finance_view"', "href=\"{{ url_for('finance_report') }}\""),
            (r'href *= *"\/finance_report"', "href=\"{{ url_for('finance_report') }}\""),
            (r'href *= *"\/patients"?', "href=\"{{ url_for('patients_list') }}\""),
        ],
    )

    # 2) calendar redirect/endpoint
    patch_file(
        ROOT / "production_auth.py",
        [
            (r'url_for\(\s*[\'"]calendar[\'"]\s*\)', 'url_for("calendar_view")'),
        ],
    )

    # 3) normalize patients card route
    ensure_patient_card_route(main_py)

    print("DONE. Restart Flask and re-test.")


if __name__ == "__main__":
    main()
