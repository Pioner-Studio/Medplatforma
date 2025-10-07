# -*- coding: utf-8 -*-
import io, os, re, sys

FILES = {
    "main": "main.py",
    "base": "templates/base.html",
    "patients": "templates/patients.html",
}


def patch_file(path, patterns):
    if not os.path.exists(path):
        return False, "skip (no file)"
    with io.open(path, "r", encoding="utf-8") as f:
        src = f.read()

    orig = src
    for pat, repl in patterns:
        src = re.sub(pat, repl, src, flags=re.DOTALL)

    changed = src != orig
    if changed:
        with io.open(path, "w", encoding="utf-8") as f:
            f.write(src)
    return changed, "ok" if changed else "no changes"


def ensure_patient_route(main_path):
    with io.open(main_path, "r", encoding="utf-8") as f:
        src = f.read()
    if "def patient_card_page(" in src and 'render_template("patient_card.html"' in src:
        return False  # уже есть

    block = r"""
@app.get("/patients/<pid>")
@login_required
def patient_card_page(pid: str):
    from bson.objectid import ObjectId
    from flask import abort
    try:
        oid = ObjectId(pid)
    except Exception:
        abort(404)
    db = current_app.config["DB"]
    patient = db.patients.find_one({"_id": oid}, {"_id": 1, "full_name": 1, "phone": 1, "email": 1,
                                                  "birthdate": 1, "card_no": 1, "notes": 1, "created_at": 1})
    if not patient:
        abort(404)
    cur = db.appointments.find({"patient_id": oid}).sort("start", -1)
    appointments = []
    for a in cur:
        appointments.append({
            "start": a.get("start"),
            "doctor_name": a.get("doctor_name"),
            "service_name": a.get("service_name"),
            "status_key": a.get("status"),
            "status_title": a.get("status_title"),
            "cost": a.get("cost"),
        })
    return render_template("patient_card.html", patient=patient, appointments=appointments)
"""
    # вставим перед концом файла
    src += "\n" + block
    with io.open(main_path, "w", encoding="utf-8") as f:
        f.write(src)
    return True


def main():
    # 1) finance_report: делаем единый эндпоинт и алиасы
    changed_main = False
    patts_main = [
        # calendar → calendar_view (если вдруг ещё остались)
        (r'url_for\(\s*[\'"]calendar[\'"]\s*\)', r'url_for("calendar_view")'),
    ]
    c, msg = patch_file(FILES["main"], patts_main)
    changed_main |= c

    # Добавим/заменим роуты фин.отчёта, если нет
    with io.open(FILES["main"], "r", encoding="utf-8") as f:
        ms = f.read()
    if "def finance_report(" not in ms:
        finance_block = r"""
@app.get("/finance_report")
@login_required
def finance_report():
    data = prepare_finance_data()  # TODO: подставь свою сборку данных
    return render_template("finance_report.html", **data)

@app.get("/finance")
@login_required
def finance_legacy():
    return redirect(url_for("finance_report"))

@app.get("/finances")
@login_required
def finances_legacy2():
    return redirect(url_for("finance_report"))

@app.get("/finance_view")
@login_required
def finance_view_alias():
    return redirect(url_for("finance_report"))
"""
        with io.open(FILES["main"], "a", encoding="utf-8") as f:
            f.write("\n" + finance_block)
        changed_main = True

    # 2) patient_card_page
    if ensure_patient_route(FILES["main"]):
        changed_main = True

    # 3) сайдбар: жёстко ставим ссылку на новый эндпоинт
    patch_file(
        FILES["base"],
        [
            (
                r'href="\{\{\s*url_for\([\'"]finance[^)]*\)\s*\}\}"',
                r'href="{{ url_for(\'finance_report\') }}"',
            ),
        ],
    )

    # 4) ссылки на карточку пациента (перестраховка)
    patch_file(
        FILES["patients"],
        [
            (
                r'url_for\(\s*[\'"]patient_card_page[\'"][^)]*\)',
                r'url_for("patient_card_page", pid=p._id)',
            ),
        ],
    )

    print("DONE. Restart Flask and re-test.")


if __name__ == "__main__":
    main()
