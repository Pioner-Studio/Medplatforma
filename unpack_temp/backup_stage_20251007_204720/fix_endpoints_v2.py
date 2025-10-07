# fix_endpoints_v2.py
import re, sys, pathlib

ROOT = pathlib.Path(__file__).parent
MPY = ROOT / "main.py"
BASE = ROOT / "templates" / "base.html"
PAT = ROOT / "templates" / "patients.html"


def patch_main():
    src = MPY.read_text(encoding="utf-8")

    # 1) Убрать дубли эндпоинта patient_card_page и нормализовать к patient_card
    #    Разрешаем два типичных варианта деклараций и сводим к одному.
    #    Итог: один-единственный роут /patients/<pid> с endpoint="patient_card".
    #    Функция называется patient_card (чтобы не конфликтовать по имени).
    pattern = re.compile(
        r"@app\.(?:get|route)\(\s*[\"']\/patients\/<pid>[\"'].*?\)\s*?\ndef\s+patient_card_page\s*\([^)]*\):.*?(?=\n@app\.|if __name__|$)",
        re.S,
    )
    src = pattern.sub("", src)  # вырезаем «старые» определения patient_card_page

    # Удалим возможные ещё одинарные варианты с endpoint="patient_card_page"
    src = re.sub(r'endpoint\s*=\s*["\']patient_card_page["\']', 'endpoint="patient_card"', src)

    # Если корректного обработчика нет — добавим его в конец файла.
    if 'endpoint="patient_card"' not in src and "def patient_card(" not in src:
        block = r"""

@app.get("/patients/<pid>", endpoint="patient_card")
def patient_card(pid):
    from bson import ObjectId
    from flask import render_template, abort
    p = db.patients.find_one({"_id": ObjectId(pid)})
    if not p:
        abort(404)
    # Подтянем минимальный набор связанного (история и т.п.) — если нужно, расширите.
    appts = list(db.appointments.find({"patient_id": ObjectId(pid)}).sort("start", -1))
    return render_template(
        "patient_card.html",
        patient=p,
        appointments=appts
    )
"""
        src += block

    MPY.write_text(src, encoding="utf-8")


def patch_base():
    if not BASE.exists():
        return
    html = BASE.read_text(encoding="utf-8")

    # 2) Сайдбар: «Пациенты» -> /patients (новый список), «Финансовый отчёт» -> /finance_report
    html = re.sub(
        r'href\s*=\s*"[\/]?\s*patients[^"]*"', "href=\"{{ url_for('patients_view') }}\"", html
    )
    html = re.sub(
        r'href\s*=\s*"[\/]?\s*finance[^"]*"', "href=\"{{ url_for('finance_report') }}\"", html
    )

    BASE.write_text(html, encoding="utf-8")


def patch_patients_list():
    if not PAT.exists():
        return
    html = PAT.read_text(encoding="utf-8")
    # 3) Ссылки «Карточка» в таблице пациентов должны вести на endpoint="patient_card"
    #    Ищем ссылки вида href="/patients/{{ p._id }}" или url_for('patient_card_page', pid=…)
    html = re.sub(
        r'href\s*=\s*"[\/]?\s*patients\/\{\{\s*p\._id\s*\}\}"',
        "href=\"{{ url_for('patient_card', pid=p._id) }}\"",
        html,
    )
    html = re.sub(
        r"url_for\(\s*['\"]patient_card_page['\"]\s*,\s*pid\s*=\s*([^)]+)\)",
        r"url_for('patient_card', pid=\1)",
        html,
    )
    PAT.write_text(html, encoding="utf-8")


if __name__ == "__main__":
    patch_main()
    patch_base()
    patch_patients_list()
    print("OK. Перезапустите Flask и сделайте Ctrl+F5 в браузере.")
