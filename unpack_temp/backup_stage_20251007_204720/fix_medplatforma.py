# fix_medplatforma.py
# Патчит patient_card.html и production_auth.py, делает .bak бэкапы рядом.

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent


# ---------- helpers ----------
def backup(p: Path):
    bak = p.with_suffix(p.suffix + ".bak")
    bak.write_text(p.read_text(encoding="utf-8"), encoding="utf-8")
    return bak


def save(p: Path, text: str):
    p.write_text(text, encoding="utf-8")


# ---------- Part A: patient_card.html ----------
pc_path = ROOT / "templates" / "patient_card.html"
if pc_path.exists():
    src = pc_path.read_text(encoding="utf-8")
    backup(pc_path)

    # 1) вставим helpers $/on/setOnClick один раз (если их нет)
    helpers = (
        "<script>\n"
        "  // safe bind helpers (auto-inserted)\n"
        "  const $id = (s) => document.getElementById(s);\n"
        "  const on  = (id, type, fn, opts) => { const el = $id(id); if (el) el.addEventListener(type, fn, opts||false); };\n"
        "  const setOnClick = (id, fn) => { const el = $id(id); if (el) el.onclick = fn; };\n"
        "</script>\n"
    )

    if "const $id = (s) => document.getElementById(s);" not in src:
        # вставляем helpers перед самым первым <script> на странице
        src = re.sub(r"(<script\b)", helpers + r"\1", src, count=1, flags=re.IGNORECASE)

    # 2) замены прямых присваиваний/слушателей на безопасные

    # document.getElementById('X').onclick = something;
    src = re.sub(
        r"""document\.getElementById\(\s*'([^']+)'\s*\)\.onclick\s*=\s*""",
        r"setOnClick('\1', ",
        src,
        flags=re.IGNORECASE,
    )

    # document.getElementById("X").onclick = ...
    src = re.sub(
        r"""document\.getElementById\(\s*"([^"]+)"\s*\)\.onclick\s*=\s*""",
        r"setOnClick('\1', ",
        src,
        flags=re.IGNORECASE,
    )

    # document.getElementById('X').onchange = ...
    src = re.sub(
        r"""document\.getElementById\(\s*'([^']+)'\s*\)\.on(change|input|submit)\s*=\s*""",
        lambda m: f"on('{m.group(1)}','{m.group(2)}', ",
        src,
        flags=re.IGNORECASE,
    )
    src = re.sub(
        r"""document\.getElementById\(\s*"([^"]+)"\s*\)\.on(change|input|submit)\s*=\s*""",
        lambda m: f"on('{m.group(1)}','{m.group(2)}', ",
        src,
        flags=re.IGNORECASE,
    )

    # document.getElementById('X').addEventListener('evt',
    src = re.sub(
        r"""document\.getElementById\(\s*'([^']+)'\s*\)\.addEventListener\(\s*'([^']+)'\s*,""",
        r"on('\1','\2',",
        src,
        flags=re.IGNORECASE,
    )
    src = re.sub(
        r"""document\.getElementById\(\s*"([^"]+)"\s*\)\.addEventListener\(\s*"([^"]+)"\s*,""",
        r"on('\1','\2',",
        src,
        flags=re.IGNORECASE,
    )

    # Закрыть открытые скобки после замен (добавим ) там, где раньше был конец выражения ;)
    # Обычно после присваивания шли функции/лямбды и ; — скобка уже будет закрыта исходным кодом.

    save(pc_path, src)
    print(f"[fix] patient_card.html patched (backup: {pc_path.name}.bak)")
else:
    print("[skip] templates/patient_card.html not found")

# ---------- Part B: production_auth.py ----------
pa_path = ROOT / "production_auth.py"
if pa_path.exists():
    text = pa_path.read_text(encoding="utf-8")
    backup(pa_path)

    # 1) дефолтный аватар → на существующий файл
    # заменяем значение по умолчанию 'default.jpg' на 'investor_avatar.png'
    text_new = re.sub(
        r"""("avatar"\s*:\s*user\.get\(\s*["']avatar["']\s*\)\s*or\s*)["']default\.jpg["']""",
        r'''\1"investor_avatar.png"''',
        text,
        flags=re.IGNORECASE,
    )

    # 2) (опционально) нормализация роли при логине: .strip().lower()
    text_new = re.sub(
        r"""("role"\s*:\s*user\.get\(\s*["']role["']\s*\)\s*or\s*["']registrar["'])""",
        r"""str(\1).strip().lower()""",
        text_new,
        flags=re.IGNORECASE,
    )
    text_new = re.sub(
        r"""session\["role"\]\s*=\s*user\.get\(\s*["']role["']\s*\)\s*or\s*["']registrar["']""",
        r"""session["role"] = str(user.get("role") or "registrar").strip().lower()""",
        text_new,
        flags=re.IGNORECASE,
    )

    save(pa_path, text_new)
    print(f"[fix] production_auth.py patched (backup: {pa_path.name}.bak)")
else:
    print("[skip] production_auth.py not found")

print("DONE. Перезапусти Flask и проверь консоль (ошибок по onclick быть не должно).")
