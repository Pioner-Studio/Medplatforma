<!-- GENERATED: 2025-09-08 10:14:00 -->
# MedPlatforma Source Bundle
Generated: 2025-09-08 10:14:00

## Included files
- .\main.py
- .\routes\routes_finance.py
- .\templates\_layout.html
- .\templates\404.html
- .\templates\action_log.html
- .\templates\add_doctor.html
- .\templates\add_event.html
- .\templates\add_expense.html
- .\templates\add_patient.html
- .\templates\add_payment.html
- .\templates\add_room.html
- .\templates\add_service.html
- .\templates\add_xray.html
- .\templates\add_ztl.html
- .\templates\backup.html
- .\templates\base.html
- .\templates\cabinet_card.html
- .\templates\calendar.backup.html
- .\templates\calendar.html
- .\templates\close_appointment.html
- .\templates\data_tools.html
- .\templates\debtors.html
- .\templates\doctor_card.html
- .\templates\doctors.html
- .\templates\edit_doctor.html
- .\templates\edit_event.html
- .\templates\edit_patient.html
- .\templates\edit_room.html
- .\templates\edit_service.html
- .\templates\expenses.html
- .\templates\finance\add.html
- .\templates\finance\cashbox.html
- .\templates\finance\list.html
- .\templates\finance\print.html
- .\templates\finance_report.html
- .\templates\import_doctors.html
- .\templates\import_patients.html
- .\templates\journal.html
- .\templates\login.html
- .\templates\logs.html
- .\templates\messages.html
- .\templates\partners.html
- .\templates\patient_card.html
- .\templates\patients.html
- .\templates\reports.html
- .\templates\roadmap.html
- .\templates\roadmap_missing.html
- .\templates\rooms.html
- .\templates\schedule\list.html
- .\templates\services.html
- .\templates\sidebar.html
- .\templates\staff.html
- .\templates\tasks.html
- .\templates\topbar.html
- .\templates\xray_room.html
- .\templates\ztl.html

---

=== BEGIN FILE: .\main.py ===

~~~python
# ======== STD LIB ========
import os
import sys
import json
import uuid
import logging
import re
import io
import csv
import calendar
import argparse
import click
from collections import OrderedDict
from datetime import datetime, timedelta, time
from pathlib import Path

# Если используешь конкретные функции из urllib.parse — лучше импортировать явно:
# from urllib.parse import quote_plus  # пример

# ======== THIRD-PARTY ========
from dotenv import load_dotenv
from flask import (
    Flask,
    Response,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    send_file,
    session,
    url_for,
    send_from_directory,
)
from markupsafe import Markup
from pymongo import MongoClient, ReturnDocument
from bson.objectid import ObjectId  # <-- выбираем ровно этот вариант и больше нигде не дублируем

# (не обязательно) красочный лог — установишь при желании:
try:
    from colorlog import ColoredFormatter
except Exception:
    ColoredFormatter = None
try:
    import colorama

    colorama.just_fix_windows_console()
except Exception:
    pass

# ======== ENV ========
load_dotenv()


def _to_oid(v):
    try:
        return ObjectId(v) if v else None
    except Exception:
        return None


# --- optional (markdown может отсутствовать)
try:
    import pandas as pd  # для экспортов/отчётов
except Exception:
    pd = None

try:
    import markdown  # pip install markdown
except Exception:
    markdown = None


# --- helpers (каноничные)
def oid(s):
    try:
        return ObjectId(s)
    except Exception:
        return None


# --- contacts helpers ---------------------------------------------------------
import re

_PHONE_RE = re.compile(r"\D+")


def _clean_phone(p: str) -> str:
    if not p:
        return ""
    digits = _PHONE_RE.sub("", str(p))
    if not digits:
        return ""
    if digits.startswith("8") and len(digits) == 11:
        digits = "7" + digits[1:]
    if not digits.startswith("+"):
        digits = "+" + digits
    return digits


def _normalize_contacts(src: dict | None) -> dict:
    src = src or {}
    phone = _clean_phone(src.get("phone", ""))
    return {
        "phone": phone,
        "email": (src.get("email") or "").strip(),
        "whatsapp": _clean_phone(src.get("whatsapp") or phone),
        "telegram": (src.get("telegram") or "").lstrip("@").strip(),  # username без @
        "max": (src.get("max") or "").strip(),
    }


# -------------------------------------------------------------------------------


def _serialize_patient(p):
    return {
        "id": str(p.get("_id")),
        "full_name": p.get("full_name") or "",
        "phone": p.get("phone") or "",
        "birthdate": (p.get("birthdate") or p.get("birth_date") or "") or "",
        "card_no": p.get("card_no"),
        "created_at": p.get("created_at"),
    }


def iso_now(dt=None):
    """YYYY-MM-DDTHH:MM (локальное время)."""
    return (dt or datetime.now()).strftime("%Y-%m-%dT%H:%M")


def write_log(action, comment="", obj="", extra=None):
    """Лёгкое журналирование действий пользователя."""
    log = {
        "datetime": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "user": session.get("user_name", "Гость"),
        "role": session.get("user_role", ""),
        "avatar_url": session.get("avatar_url", "/static/avatars/demo-user.png"),
        "ip": request.remote_addr,
        "action": action,
        "object": obj,
        "comment": comment,
    }
    if extra and isinstance(extra, dict):
        log.update(extra)
    db.logs.insert_one(log)


# --- Flask app + конфиг из .env
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev")

# --- JSON: всегда UTF-8 (без \uXXXX)
app.config["JSON_AS_ASCII"] = False
try:
    # Flask ≥2.3
    app.json.ensure_ascii = False
except Exception:
    pass

# Авто-перезагрузка шаблонов и отключение cache статики в dev
app.config.update(
    TEMPLATES_AUTO_RELOAD=True,
    SEND_FILE_MAX_AGE_DEFAULT=0,
    JSON_AS_ASCII=False,  # ← добавь эту строку
)

# --- JSON UTF-8 ENFORCE (drop-in) -------------------------------------------
# Flask<2.3 читает JSON_AS_ASCII, Flask>=2.3 — app.json.ensure_ascii
app.config["JSON_AS_ASCII"] = False
try:
    app.json.ensure_ascii = False  # Flask 2.3+
except Exception:
    pass


@app.after_request
def _force_utf8_json(resp):
    # Если это JSON-ответ — всегда укажем charset, чтобы клиенты (в т.ч. PS5) не путались
    ctype = resp.headers.get("Content-Type", "")
    if ctype.startswith("application/json") and "charset=" not in ctype.lower():
        resp.headers["Content-Type"] = "application/json; charset=utf-8"
    return resp


# ---------------------------------------------------------------------------

# Mongo (через .env)
MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME", "medplatforma")

if not MONGO_URI:
    raise RuntimeError("MONGO_URI is not set. Put it into .env")

client = MongoClient(MONGO_URI)

# Быстрая проверка соединения/авторизации
try:
    client.admin.command("ping")
except Exception as e:
    # Выведет понятное сообщение в консоль, если доступ не настроен
    raise RuntimeError(f"MongoDB auth/connection failed: {e}")

db = client[DB_NAME]

# --- Rooms bootstrap (идемпотентно) ---
from datetime import datetime

DEFAULT_ROOMS = ["Детский", "Ортопедия", "Хирургия", "Ортодонтия", "Терапия", "Кастомный"]


def ensure_rooms():
    try:
        existing = set(x.get("name") for x in db.rooms.find({}, {"name": 1}))
        missing = [n for n in DEFAULT_ROOMS if n not in existing]
        if missing:
            docs = [{"name": n, "created_at": datetime.utcnow()} for n in missing]
            db.rooms.insert_many(docs)
            print(f"[init] created rooms: {', '.join(missing)}")
    except Exception as e:
        print("[init] ensure_rooms error:", e)


@app.route("/api/patients/<id>", methods=["GET"])
def api_patient_get(id):
    _id = oid(id)
    if not _id:
        return jsonify({"ok": False, "error": "bad_id"}), 400
    p = db.patients.find_one({"_id": _id})
    if not p:
        return jsonify({"ok": False, "error": "not_found"}), 404
    return jsonify({"ok": True, "item": _serialize_patient(p)})


@app.route("/api/patients/<id>/update", methods=["POST"])
def api_patient_update(id):
    _id = oid(id)
    if not _id:
        return jsonify({"ok": False, "error": "bad_id"}), 400
    data = request.get_json(silent=True) or {}

    upd = {}
    if "full_name" in data:
        upd["full_name"] = (data.get("full_name") or "").strip()
    if "phone" in data:
        upd["phone"] = (data.get("phone") or "").strip()
    if "birth_date" in data or "birthdate" in data:
        upd["birth_date"] = (data.get("birth_date") or data.get("birthdate") or "").strip()
    if "card_no" in data:
        try:
            upd["card_no"] = int(data["card_no"]) if data["card_no"] not in (None, "") else None
        except Exception:
            return jsonify({"ok": False, "error": "bad_card_no"}), 400

    if not upd:
        return jsonify({"ok": False, "error": "empty"}), 400

    r = db.patients.update_one({"_id": _id}, {"$set": upd})
    if not r.matched_count:
        return jsonify({"ok": False, "error": "not_found"}), 404

    p = db.patients.find_one({"_id": _id})
    return jsonify({"ok": True, "item": _serialize_patient(p)})


# --- Patient contacts (короткая карточка + готовые ссылки) ---
@app.get("/api/patients/<id>/contacts")
def api_patient_contacts_min(id):
    import re

    _id = oid(id)
    if not _id:
        return jsonify({"ok": False, "error": "bad_id"}), 400

    fld = {
        "full_name": 1,
        "phone": 1,
        "whatsapp": 1,
        "telegram": 1,
        "email": 1,
        "max": 1,
    }
    doc = db.patients.find_one({"_id": _id}, fld)
    if not doc:
        return jsonify({"ok": False, "error": "not_found"}), 404

    def clean_phone(v: str) -> str:
        return re.sub(r"\D+", "", v or "")

    phone = (doc.get("phone") or "").strip()
    wa = (doc.get("whatsapp") or phone).strip()
    tg = (doc.get("telegram") or "").strip().lstrip("@")
    mail = (doc.get("email") or "").strip()
    mx = (doc.get("max") or "").strip()

    links = {}
    if phone:
        links["tel"] = f"tel:{phone}"
    wa_num = clean_phone(wa)
    if wa_num:
        links["wa"] = f"https://wa.me/{wa_num}"
    if tg:
        links["tg"] = f"https://t.me/{tg}"
    if mail:
        links["mail"] = f"mailto:{mail}"
    if mx:
        # если у вас иная схема логина Max — поправьте тут
        links["max"] = f"https://web.max.ru/{mx}"

    return jsonify(
        {
            "ok": True,
            "id": str(doc["_id"]),
            "full_name": doc.get("full_name") or "",
            "contacts": {
                "phone": phone,
                "whatsapp": wa,
                "telegram": tg,
                "email": mail,
                "max": mx,
            },
            "links": links,  # <— важно для mpOpenContact
        }
    )


# --- helpers: contact links ---------------------------------------------------
def _build_contact_links(c: dict) -> dict:
    phone = (c.get("phone") or "").strip()
    wa = (c.get("whatsapp") or phone).strip()
    tg = (c.get("telegram") or "").strip().lstrip("@")
    mx = (c.get("max") or "").strip()

    def digits(s):
        import re

        return re.sub(r"\D+", "", s or "")

    links = {}
    if phone:
        links["tel"] = f"tel:{digits(phone) or phone}"
    if wa:
        links["whatsapp"] = f"https://wa.me/{digits(wa)}"
    if tg:
        links["telegram"] = f"https://t.me/{tg}"
    # Публичной доки по deep-link Max нет; открываем веб-клиент.
    # Когда появится схема — подменим тут на корректную.
    links["max"] = "https://web.max.ru/"
    return links


# --- 2.2 MINI-API: пациенты (короткие словари для селектов/автокомплита) ---
@app.get("/api/patients/min")
def api_patients_min_list():
    """
    GET /api/patients/min?q=иванов&limit=20
    Возвращает короткие карточки пациентов для выпадающих списков/поиска.
    """
    q = (request.args.get("q") or "").strip()
    try:
        limit = min(50, max(1, int(request.args.get("limit", 20))))
    except Exception:
        limit = 20

    flt = {}
    if q:
        flt = {
            "$or": [
                {"full_name": {"$regex": re.escape(q), "$options": "i"}},
                {"phone": {"$regex": re.escape(q), "$options": "i"}},
                {"card_no": {"$regex": re.escape(q), "$options": "i"}},
            ]
        }

    cur = (
        db.patients.find(flt, {"full_name": 1, "phone": 1, "birthdate": 1, "card_no": 1})
        .sort("full_name", 1)
        .limit(limit)
    )

    items = [
        {
            "id": str(p["_id"]),
            "name": p.get("full_name", ""),
            "phone": p.get("phone", ""),
            "birthdate": p.get("birthdate", ""),  # строкой 'YYYY-MM-DD' если есть
            "card_no": p.get("card_no", ""),
        }
        for p in cur
    ]

    return jsonify({"ok": True, "items": items})

    # Забираем только поля контактов, + базовые для удобства фронта
    proj = {
        "full_name": 1,
        "phone": 1,
        "email": 1,
        "telegram": 1,
        "whatsapp": 1,
        "max": 1,  # "Макс" как отдельный канал (по аналогии с WhatsApp)
        "card_no": 1,
    }
    p = db.patients.find_one({"_id": _id}, proj)
    if not p:
        return jsonify({"ok": False, "error": "not_found"}), 404

    # Нормализация — возвращаем только строки, пустые -> ""
    item = {
        "id": str(p["_id"]),
        "full_name": s(p.get("full_name")),
        "card_no": s(p.get("card_no")),
        "phone": s(p.get("phone")),
        "email": s(p.get("email")),
        "telegram": s(p.get("telegram")),
        "whatsapp": s(p.get("whatsapp")),
        "max": s(p.get("max")),  # просто значение; ссылку уточним отдельно
    }

    # На стороне UI потом можно строить ссылки:
    #  - tel: <phone>
    #  - mailto: <email>
    #  - WhatsApp: https://wa.me/<digits_only(phone)>
    #  - Telegram: https://t.me/<handle_or_phone>
    #  - Max: https://web.max.ru/  (глубокую ссылку уточним спецификацией)
    return jsonify({"ok": True, "item": item})


# --- /2.2 MINI-API ---


# --- mini: один пациент (короткая карточка) -------------------------------
@app.get("/api/patients/<id>/min", endpoint="api_patient_min_by_id")
def api_patient_min_by_id(id):
    _id = oid(id)
    if not _id:
        return jsonify({"ok": False, "error": "bad_id"}), 400

    p = db.patients.find_one(
        {"_id": _id}, {"full_name": 1, "phone": 1, "birthdate": 1, "card_no": 1}
    )
    if not p:
        return jsonify({"ok": False, "error": "not_found"}), 404

    item = {
        "id": str(p["_id"]),
        "name": p.get("full_name", ""),
        "phone": p.get("phone", ""),
        "birthdate": p.get("birthdate", ""),
        "card_no": p.get("card_no", ""),
    }
    return jsonify({"ok": True, "item": item})


# --------------------------------------------------------------------------


@app.route("/patients/<id>")
def patient_card_page(id):
    return render_template("patient_card.html", pid=id)


# Запускаем инициализацию кабинетов при старте приложения (совместимо с Flask 3.x)
try:
    # если ensure_rooms не использует current_app/глобалы Flask, контекст не обязателен;
    # но так безопаснее для любых будущих изменений:
    with app.app_context():
        ensure_rooms()
    print("[init] ensure_rooms: done")
except Exception as e:
    print("[init] ensure_rooms error:", e)

# --- /Rooms bootstrap ---

# Регистрируем блюпринты
from routes_schedule import bp as schedule_bp

app.register_blueprint(schedule_bp, url_prefix="/schedule")

# ВАЖНО: отдаём DB блюпринтам/роутам
app.config["DB"] = db

# --- финмодуль: импорт и регистрация блюпринта ---
try:
    # в routes_finance.py блюпринт называется bp
    from routes_finance import bp as bp_finance

    # url_prefix уже задан внутри файла: Blueprint("finance", ..., url_prefix="/finance")
    app.register_blueprint(bp_finance)
except Exception as e:
    print(f"[WARN] routes_finance не подключён: {e}")


def parse_iso(dt_str):
    # FullCalendar шлет ISO, иногда без миллисекунд
    # Пример: '2025-08-10T00:00:00Z' или '2025-08-10'
    if not dt_str:
        return None
    try:
        # варианты с 'Z'
        if dt_str.endswith("Z"):
            return datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
        return datetime.fromisoformat(dt_str)
    except Exception:
        # последний шанс
        return (
            datetime.strptime(dt_str[:19], "%Y-%m-%dT%H:%M:%S")
            if "T" in dt_str
            else datetime.strptime(dt_str, "%Y-%m-%d")
        )


def to_dt(s):
    """Parse various user date strings -> datetime | None.
    Supports: 'YYYY-MM-DDTHH:MM', 'YYYY-MM-DD HH:MM', 'MM/DD/YYYY hh:mm AM/PM', 'DD.MM.YYYY HH:MM'.
    If a datetime is passed, returns as is.
    """
    if isinstance(s, datetime):
        return s
    if not s:
        return None
    if isinstance(s, (int, float)):
        try:
            return datetime.fromtimestamp(s)
        except Exception:
            return None
    ss = str(s).strip()
    # normalize common separators
    try_formats = [
        "%Y-%m-%dT%H:%M",
        "%Y-%m-%d %H:%M",
        "%m/%d/%Y %I:%M %p",
        "%d.%m.%Y %H:%M",
    ]
    for fmt in try_formats:
        try:
            if fmt == "%Y-%m-%dT%H:%M":
                s2 = ss.replace(" ", "T")
                return datetime.strptime(s2[:16], fmt)
            return datetime.strptime(ss[:16] if "I" not in fmt else ss, fmt)
        except Exception:
            continue
    return None


def parse_local_dt(s: str) -> datetime | None:
    """Принимает 'YYYY-MM-DDTHH:MM' или 'YYYY-MM-DD HH:MM', возвращает datetime (naive)."""
    if not s:
        return None
    s = s.strip()
    try:
        if "T" in s:
            return datetime.strptime(s[:16], "%Y-%m-%dT%H:%M")
        return datetime.strptime(s[:16], "%Y-%m-%d %H:%M")
    except Exception:
        return None


def add_minutes(dt: datetime, minutes: int) -> datetime:
    return dt + timedelta(minutes=int(minutes or 0))


# --- Slot validation (09:00–21:00; шаг 15 мин) ---
from datetime import time

WORK_START = time(9, 0)
WORK_END = time(21, 0)


def _is_15m_step(dt):
    return (dt.minute % 15 == 0) and (dt.second == 0)


def _within_hours(dt):
    t = dt.time()
    # Конец включительно: 21:00 разрешено как граница окончания
    return WORK_START <= t <= WORK_END


def validate_slot_bounds(start_dt, end_dt):
    if not (_within_hours(start_dt) and _within_hours(end_dt)):
        return "out_of_hours"
    if not (_is_15m_step(start_dt) or start_dt == start_dt.replace(second=0)) or not (
        _is_15m_step(end_dt) or end_dt == end_dt.replace(second=0)
    ):
        return "bad_step"
    if end_dt <= start_dt:
        return "bad_range"
    return None


# --- /Slot validation ---


def minutes_until(dt, now=None) -> int | None:
    if not dt:
        return None
    now = now or datetime.now()
    return int((dt - now).total_seconds() // 60)


def calc_room_status_now(room_doc, now=None):
    """'available' | 'occupied' | 'maintenance' на текущий момент."""
    if room_doc.get("status") == "maintenance":
        return "maintenance"
    now = now or datetime.now()
    busy_now = db.appointments.find_one(
        {"room_id": room_doc["_id"], "start": {"$lte": now}, "end": {"$gt": now}}
    )
    return "occupied" if busy_now else "available"


def get_next_event_for_room(room_id, now=None):
    """Ближайший будущий приём по room_id (>= now) или None."""
    now = now or datetime.now()
    cur = (
        db.appointments.find({"room_id": room_id, "start": {"$gte": now}}).sort("start", 1).limit(1)
    )
    for a in cur:
        return a
    return None


def is_now_between(start_dt, end_dt, now=None) -> bool:
    now = now or datetime.now()
    return bool(start_dt and end_dt and start_dt <= now < end_dt)


def fmt_hm(dt) -> str:
    if not dt:
        return ""
    if isinstance(dt, str):
        dt = to_dt(dt)
    return dt.strftime("%H:%M") if dt else ""


def to_minutes(t: str) -> int:
    h, m = map(int, t.split(":"))
    return h * 60 + m


def from_minutes(x: int) -> str:
    h = x // 60
    m = x % 60
    return f"{h:02d}:{m:02d}"


def clinic_hours(date_dt):
    # рабочие часы по умолчанию (можно вынести в настройки)
    return "08:00", "20:00"


def recalc_room_status(room_id):
    """Переcчитает статус кабинета на текущий момент времени и сохранит в rooms.status.
    Правило: если есть приём, пересекающий now → occupied; иначе available.
    (maintenance имеет приоритет и не затирается.)"""
    if not room_id:
        return
    room = db.rooms.find_one({"_id": ObjectId(room_id)})
    if not room:
        return
    if room.get("status") == "maintenance":
        # обслуживание вручную выставляют — не трогаем
        return
    now = datetime.now()
    busy = db.appointments.find_one(
        {"room_id": ObjectId(room_id), "start": {"$lte": now}, "end": {"$gt": now}}
    )
    new_status = "occupied" if busy else "available"
    db.rooms.update_one(
        {"_id": ObjectId(room_id)},
        {"$set": {"status": new_status, "updated_at": datetime.utcnow()}},
    )


def s(val):  # безопасная строка
    return (val or "").strip()


def parse_date_yyyy_mm_dd(val):
    """Принимаем 'YYYY-MM-DD' -> возвращаем ту же строку (храним строкой)"""
    v = s(val)
    if not v:
        return ""
    # лёгкая валидация
    try:
        datetime.strptime(v, "%Y-%m-%d")
        return v
    except Exception:
        return ""


def next_seq(name: str) -> int:
    """Глобальный инкремент в MongoDB (коллекция counters)."""
    doc = db.counters.find_one_and_update(
        {"_id": name}, {"$inc": {"seq": 1}}, upsert=True, return_document=ReturnDocument.AFTER
    )
    return int(doc.get("seq", 1))


def make_card_no() -> str:
    """Формируем номер карточки вида CT-000123."""
    n = next_seq("patient_card_no")
    return f"CT-{n:06d}"


def main():
    parser = argparse.ArgumentParser(description="ClubStom docs/zip generator")
    parser.add_argument("--zip", action="store_true", help="сделать архив проекта в /exports")
    parser.add_argument("--note", type=str, default="", help="заметка/комментарий")
    parser.add_argument("--lint", action="store_true", help="проверить дубли и вывести отчёт")
    args = parser.parse_args()

    app, err = _load_flask_app()
    if err:
        (DOCS / "ROUTES.md").write_text(
            "# ROUTES\n\nНе удалось импортировать приложение:\n\n```\n" + err + "\n```\n",
            encoding="utf-8",
        )
        print("[WARN] Ошибка импорта app. Подробности в docs/ROUTES.md")
    else:
        routes_md = _dump_routes_md(app)
        (DOCS / "ROUTES.md").write_text(routes_md, encoding="utf-8")
        print("[OK] docs/ROUTES.md обновлён")

        if args.lint:
            problems, count = _lint_project(app)
            report = "# LINT REPORT\n\n"
            if count == 0:
                report += "Проблем не найдено ✅\n"
            else:
                report += "\n".join(f"- {p}" for p in problems) + "\n"
            (DOCS / "LINT.md").write_text(report, encoding="utf-8")
            print(f"[OK] docs/LINT.md создан ({count} проблем)")


@app.route("/roadmap")
def roadmap_view():
    md_path = Path(app.root_path) / "roadmap_clubstom.md"
    if not md_path.exists():
        return render_template("roadmap_missing.html"), 404

    text = md_path.read_text(encoding="utf-8")
    if markdown:
        html = markdown.markdown(text, extensions=["tables", "fenced_code", "toc"])
    else:
        # Фолбэк: показываем как pre, если markdown не установлен
        html = f"<pre style='white-space:pre-wrap'>{text}</pre>"

    return render_template("roadmap.html", content=Markup(html))


@app.route("/api/free_slots", methods=["POST"])
def api_free_slots():
    """
    Вход: {doctor_id, room_name, date: 'YYYY-MM-DD', duration_min: 30}
    Выход: ["09:00","09:30",...]
    Логика: берём все приёмы врача И/ИЛИ кабинета на дату, вычитаем из рабочего окна.
    """
    data = request.get_json(force=True, silent=True) or {}
    doctor_id = data.get("doctor_id") or ""
    room_name = data.get("room_name") or ""
    date_s = data.get("date") or ""
    duration = int(data.get("duration_min") or 30)
    if not doctor_id or not date_s:
        return jsonify({"ok": False, "error": "bad_params"}), 400

    try:
        day = datetime.strptime(date_s, "%Y-%m-%d").date()
    except Exception:
        return jsonify({"ok": False, "error": "bad_date"}), 400

    # границы дня
    start_day = datetime.combine(day, datetime.min.time())
    end_day = start_day + timedelta(days=1)

    # маппим кабинет по имени в _id (если передан)
    room = db.rooms.find_one({"name": room_name}, {"_id": 1}) if room_name else None
    room_id = room["_id"] if room else None

    # собираем занятость (врач + по возможности кабинет)
    match = {"start": {"$lt": end_day}, "end": {"$gt": start_day}}
    try:
        match["doctor_id"] = ObjectId(doctor_id)
    except Exception:
        match["doctor_id"] = doctor_id  # вдруг уже строкой
    if room_id:
        match["room_id"] = room_id

    busy = []
    for a in db.appointments.find(match, {"start": 1, "end": 1}).sort("start", 1):
        s = to_dt(a["start"])
        e = to_dt(a["end"])
        if not (s and e):
            continue
        if s.date() != day:
            s = datetime.combine(day, datetime.min.time())
        if e.date() != day:
            e = datetime.combine(day, datetime.max.time())
        busy.append((s, e))

    # рабочее окно клиники (можно заменить на расписание врача)
    wh_start_s, wh_end_s = clinic_hours(day)
    wh_start = datetime.combine(day, datetime.strptime(wh_start_s, "%H:%M").time())
    wh_end = datetime.combine(day, datetime.strptime(wh_end_s, "%H:%M").time())

    # шаг 5 минут, выдаём старты, которые не пересекаются с busy
    step = 5
    free = []
    t = wh_start
    delta = timedelta(minutes=duration)
    while t + delta <= wh_end:
        slot_ok = True
        for s, e in busy:
            if (t < e) and (t + delta > s):
                slot_ok = False
                break
        if slot_ok:
            free.append(t.strftime("%H:%M"))
        t += timedelta(minutes=step)

    return jsonify({"ok": True, "slots": free})


# ======= АВТОРИЗАЦИЯ =======
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        password = request.form.get("password", "")
        if password == "demo":
            session["user_id"] = "demo"
            session["user_role"] = "admin"
            session["user_name"] = "Демо Пользователь"
            session["avatar_url"] = "/static/avatars/demo-user.png"
            return redirect(url_for("calendar_view"))
        else:
            flash("Неверный пароль! Введите 'demo'", "danger")
    return render_template("login.html")


@app.route("/logout")
def logout():
    write_log("logout", comment="Выход из системы", obj="Выход")
    session.clear()
    return redirect(url_for("login"))


# --- Маршрут: Главный календарь ---
@app.route("/")
def home():
    return redirect(url_for("calendar_view"))


@app.route("/favicon.ico")
def favicon():
    # отдадим имеющуюся картинку как фавикон, чтобы убрать 404
    return send_from_directory(
        os.path.join(app.root_path, "static"),
        "logo_test123.png",  # если положишь favicon.ico — укажи его тут
        mimetype="image/png",
    )


@app.route("/calendar")
def calendar_view():
    if "user_id" not in session:
        return redirect(url_for("login"))

    doctors = list(db.doctors.find())
    patients = list(db.patients.find())

    rooms = list(db.rooms.find({}, {"name": 1, "status": 1}).sort("name", 1))
    cabinets = [r["name"] for r in rooms]

    now = datetime.now()

    # Считаем статус "на сейчас" + ближайший приём (если свободен)
    room_info = {}
    for r in rooms:
        state = calc_room_status_now(r, now)  # 'available'|'occupied'|'maintenance'
        text = (
            "Обслуживание"
            if state == "maintenance"
            else ("Занят" if state == "occupied" else "Свободен")
        )
        color = (
            "#d97706" if state == "maintenance" else ("#cc0000" if state == "occupied" else "green")
        )

        next_info = None
        if state == "available":
            a = get_next_event_for_room(r["_id"], now)
            if a:
                sdt = a.get("start")
                in_min = minutes_until(sdt, now)
                srv = (
                    db.services.find_one({"_id": a.get("service_id")}, {"name": 1})
                    if a.get("service_id")
                    else None
                )
                pat = (
                    db.patients.find_one({"_id": a.get("patient_id")}, {"full_name": 1})
                    if a.get("patient_id")
                    else None
                )
                next_info = {
                    "start": sdt.strftime("%Y-%m-%dT%H:%M") if isinstance(sdt, datetime) else "",
                    "service": (srv or {}).get("name", ""),
                    "patient": (pat or {}).get("full_name", ""),
                    "in_minutes": in_min,
                }

        room_info[r["name"]] = {"state": state, "text": text, "color": color, "next": next_info}

    total_rooms = len(cabinets)
    free_rooms = sum(1 for nfo in room_info.values() if nfo["state"] == "available")

    return render_template(
        "calendar.html",
        metrics={"total_rooms": total_rooms, "free_rooms": free_rooms},
        room_info=room_info,
        cabinets=cabinets,
        doctors=doctors,
        patients=patients,
    )


@app.route("/api/rooms/status_now")
def api_rooms_status_now():
    now = datetime.now()
    rooms = list(db.rooms.find({}, {"name": 1, "status": 1}))
    result = {}
    for r in rooms:
        state = calc_room_status_now(r, now)
        text = (
            "Обслуживание"
            if state == "maintenance"
            else ("Занят" if state == "occupied" else "Свободен")
        )
        color = (
            "#d97706" if state == "maintenance" else ("#cc0000" if state == "occupied" else "green")
        )

        next_info = None
        if state == "available":
            a = get_next_event_for_room(r["_id"], now)
            if a:
                sdt = a.get("start")
                in_min = minutes_until(sdt, now)
                srv = (
                    db.services.find_one({"_id": a.get("service_id")}, {"name": 1})
                    if a.get("service_id")
                    else None
                )
                pat = (
                    db.patients.find_one({"_id": a.get("patient_id")}, {"full_name": 1})
                    if a.get("patient_id")
                    else None
                )
                next_info = {
                    "start": sdt.strftime("%Y-%m-%dT%H:%M") if isinstance(sdt, datetime) else "",
                    "service": (srv or {}).get("name", ""),
                    "patient": (pat or {}).get("full_name", ""),
                    "in_minutes": in_min,
                }
        result[r["name"]] = {"state": state, "text": text, "color": color, "next": next_info}
    return jsonify(result)


@app.route("/api/rooms/today_details")
def api_rooms_today_details():
    room_name = request.args.get("room", "").strip()
    if not room_name:
        return jsonify({"ok": False, "error": "no_room"}), 400

    room = db.rooms.find_one({"name": room_name}, {"_id": 1, "name": 1})
    if not room:
        return jsonify({"ok": False, "error": "room_not_found"}), 404

    now = datetime.now()
    start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end_of_day = start_of_day + timedelta(days=1)

    appts = list(
        db.appointments.find(
            {"room_id": room["_id"], "start": {"$lt": end_of_day}, "end": {"$gt": start_of_day}}
        ).sort("start", 1)
    )

    d_ids, p_ids, s_ids = set(), set(), set()
    for a in appts:
        if a.get("doctor_id"):
            d_ids.add(a["doctor_id"])
        if a.get("patient_id"):
            p_ids.add(a["patient_id"])
        if a.get("service_id"):
            s_ids.add(a["service_id"])

    doctors = (
        {d["_id"]: d for d in db.doctors.find({"_id": {"$in": list(d_ids)}}, {"full_name": 1})}
        if d_ids
        else {}
    )
    patients = (
        {p["_id"]: p for p in db.patients.find({"_id": {"$in": list(p_ids)}}, {"full_name": 1})}
        if p_ids
        else {}
    )
    services = (
        {s["_id"]: s for s in db.services.find({"_id": {"$in": list(s_ids)}}, {"name": 1})}
        if s_ids
        else {}
    )

    items = []
    for a in appts:
        sdt = a.get("start")
        edt = a.get("end")
        items.append(
            {
                "start": fmt_hm(sdt),
                "end": fmt_hm(edt),
                "doctor": doctors.get(a.get("doctor_id"), {}).get("full_name", "—"),
                "patient": patients.get(a.get("patient_id"), {}).get("full_name", "—"),
                "service": services.get(a.get("service_id"), {}).get("name", "—"),
                "status": a.get("status_key", "scheduled"),
                "is_now": is_now_between(sdt, edt, now),
            }
        )

    return jsonify({"ok": True, "room": room_name, "items": items})


@app.route("/update_event_time", methods=["POST"])
def update_event_time():
    data = request.get_json()
    event_id = data.get("id")
    new_datetime = data.get("new_datetime")
    if event_id and new_datetime:
        db.events.update_one({"_id": ObjectId(event_id)}, {"$set": {"datetime": new_datetime}})
        return jsonify({"ok": True})
    return jsonify({"ok": False})


@app.route("/export_calendar")
def export_calendar():
    write_log("export", comment="Экспорт календаря", obj="Календарь")

    appts = list(db.appointments.find())
    doctors = {str(d["_id"]): d for d in db.doctors.find({}, {"full_name": 1})}
    patients = {str(p["_id"]): p for p in db.patients.find({}, {"full_name": 1})}
    services = {str(s["_id"]): s for s in db.services.find({}, {"name": 1})}
    rooms = {str(r["_id"]): r for r in db.rooms.find({}, {"name": 1})}

    output = io.StringIO()
    writer = csv.writer(output, delimiter=";")
    writer.writerow(
        ["start", "end", "doctor", "patient", "service", "room", "sum", "status", "comment"]
    )

    for a in appts:
        did = str(a.get("doctor_id", "") or "")
        pid = str(a.get("patient_id", "") or "")
        sid = str(a.get("service_id", "") or "")
        rid = str(a.get("room_id", "") or "")

        start = to_dt(a.get("start"))
        end = to_dt(a.get("end"))

        writer.writerow(
            [
                start.strftime("%Y-%m-%d %H:%M") if start else "",
                end.strftime("%Y-%m-%d %H:%M") if end else "",
                doctors.get(did, {}).get("full_name", ""),
                patients.get(pid, {}).get("full_name", ""),
                services.get(sid, {}).get("name", ""),
                rooms.get(rid, {}).get("name", ""),
                a.get("sum", ""),
                a.get("status_key", ""),
                a.get("comment", ""),
            ]
        )
    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=calendar.csv"},
    )


def get_status_color(status):
    return {
        "Первичный": "#82B4FF",
        "Повторный": "#FFD366",
        "Оплачен": "#B4F0C0",
        "Отказ": "#FF7474",
        "Новый": "#D4D4D4",
    }.get(status, "#D4D4D4")


# --- Маршрут: Добавление события ---
@app.route("/add_event", methods=["GET", "POST"])
def add_event():
    if "user_id" not in session:
        return redirect(url_for("login"))

    # Справочники для формы
    doctors = list(db.doctors.find({}, {"full_name": 1}).sort("full_name", 1))
    patients = list(db.patients.find({}, {"full_name": 1}).sort("full_name", 1))
    services = list(
        db.services.find({"is_active": True}, {"name": 1, "duration_min": 1}).sort("name", 1)
    )
    rooms = list(db.rooms.find({}, {"name": 1, "status": 1}).sort("name", 1))

    if request.method == "POST":
        # 1) Читаем поля
        doctor_id_s = request.form.get("doctor_id") or ""
        patient_id_s = request.form.get("patient_id") or ""
        service_id_s = request.form.get("service_id") or ""
        room_id_s = request.form.get("room_id") or ""
        start_s = request.form.get("start") or ""  # datetime-local
        end_s = request.form.get("end") or ""  # опционально

        comment = (request.form.get("comment") or "").strip()
        status_key = (request.form.get("status_key") or "scheduled").strip()

        # 2) Преобразуем ID
        try:
            doctor_id = ObjectId(doctor_id_s) if doctor_id_s else None
        except:
            doctor_id = None
        try:
            patient_id = ObjectId(patient_id_s) if patient_id_s else None
        except:
            patient_id = None
        try:
            service_id = ObjectId(service_id_s) if service_id_s else None
        except:
            service_id = None
        try:
            room_id = ObjectId(room_id_s) if room_id_s else None
        except:
            room_id = None

        # 3) Валидация обязательных полей
        errors = []
        if not room_id:
            errors.append("Выберите кабинет.")
        if not service_id:
            errors.append("Выберите услугу.")
        if not doctor_id:
            errors.append("Выберите врача.")
        if not patient_id:
            errors.append("Выберите пациента.")
        start_dt = parse_local_dt(start_s)
        if not start_dt:
            errors.append("Укажите дату и время начала.")

        # 4) Длительность и конец приёма
        end_dt = parse_local_dt(end_s) if end_s else None
        if not end_dt and start_dt and service_id:
            srv = db.services.find_one({"_id": service_id}, {"duration_min": 1}) or {}
            dur = int(srv.get("duration_min") or 30)
            end_dt = add_minutes(start_dt, dur)

        if not end_dt or (start_dt and end_dt <= start_dt):
            errors.append("Некорректный интервал приёма.")

        if errors:
            for e in errors:
                flash(e, "danger")
            return render_template(
                "add_event.html", doctors=doctors, patients=patients, services=services, rooms=rooms
            )

        # 5) Проверка конфликта по кабинету
        conflict = db.appointments.find_one(
            {"room_id": room_id, "start": {"$lt": end_dt}, "end": {"$gt": start_dt}}
        )
        if conflict:
            flash("В этот интервал кабинет занят.", "danger")
            return render_template(
                "add_event.html", doctors=doctors, patients=patients, services=services, rooms=rooms
            )

        # 6) Создаём приём
        appt = {
            "doctor_id": doctor_id,
            "patient_id": patient_id,
            "service_id": service_id,
            "room_id": room_id,
            "start": start_dt,
            "end": end_dt,
            "status_key": status_key,
            "comment": comment,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }
        db.appointments.insert_one(appt)

        # 7) Обновим статус кабинета (если используешь эту функцию)
        try:
            recalc_room_status(room_id)
        except Exception:
            pass

        flash("Запись создана.", "success")
        return redirect(url_for("calendar_view"))

    # GET — отрисовка формы
    return render_template(
        "add_event.html", doctors=doctors, patients=patients, services=services, rooms=rooms
    )


@app.route("/edit_event/<event_id>", methods=["GET", "POST"])
def edit_event(event_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    appt = db.appointments.find_one({"_id": ObjectId(event_id)})
    if not appt:
        flash("Запись не найдена.", "danger")
        return redirect(url_for("calendar_view"))

    doctors = list(db.doctors.find().sort("full_name", 1))
    patients = list(db.patients.find().sort("full_name", 1))
    rooms = list(db.rooms.find({}, {"name": 1}).sort("name", 1))
    services = list(db.services.find({}, {"name": 1, "duration_min": 1}).sort("name", 1))

    if request.method == "POST":
        doctor_id = request.form["doctor_id"]
        patient_id = request.form["patient_id"]
        room_name = request.form["cabinet"]
        service_id = request.form.get("service_id") or None

        # дата/время
        start_raw = request.form["datetime"][:16]
        start_dt = to_dt(start_raw)
        if not start_dt:
            flash("Некорректная дата/время.", "danger")
            return render_template(
                "edit_event.html",
                event=appt,
                doctors=doctors,
                patients=patients,
                cabinets=[r["name"] for r in rooms],
                services=services,
            )

        room = db.rooms.find_one({"name": room_name})
        if not room:
            flash("Кабинет не найден.", "danger")
            return render_template(
                "edit_event.html",
                event=appt,
                doctors=doctors,
                patients=patients,
                cabinets=[r["name"] for r in rooms],
                services=services,
            )

        srv = db.services.find_one({"_id": ObjectId(service_id)}) if service_id else None
        duration = int(srv.get("duration_min", 30)) if srv else 30
        end_dt = add_minutes(start_dt, duration)

        # Проверка занятости кабинета (исключая текущую запись)
        busy = db.appointments.find_one(
            {
                "_id": {"$ne": appt["_id"]},
                "room_id": room["_id"],
                "start": {"$lt": end_dt},
                "end": {"$gt": start_dt},
            }
        )
        if busy:
            flash("Кабинет занят на это время.", "danger")
            return render_template(
                "edit_event.html",
                event=appt,
                doctors=doctors,
                patients=patients,
                cabinets=[r["name"] for r in rooms],
                services=services,
            )

        db.appointments.update_one(
            {"_id": appt["_id"]},
            {
                "$set": {
                    "doctor_id": ObjectId(doctor_id),
                    "patient_id": ObjectId(patient_id),
                    "room_id": room["_id"],
                    "service_id": ObjectId(service_id) if service_id else None,
                    "start": start_dt,
                    "end": end_dt,
                    "status_key": request.form.get(
                        "status_key", appt.get("status_key", "scheduled")
                    ),
                    "comment": request.form.get("comment", appt.get("comment", "")),
                    "sum": int(request.form.get("sum", appt.get("sum", 0)) or 0),
                }
            },
        )

        flash("Запись обновлена.", "success")
        return redirect(url_for("calendar_view"))

    # GET — подготовим данные для формы
    # Преобразуем для шаблона datetime-local
    start_val = appt.get("start")
    start_local = (
        start_val.strftime("%Y-%m-%dT%H:%M")
        if isinstance(start_val, datetime)
        else (to_dt(start_val) or datetime.now()).strftime("%Y-%m-%dT%H:%M")
    )

    # Текущие значения
    current_room_name = ""
    if appt.get("room_id"):
        r = db.rooms.find_one({"_id": appt["room_id"]})
        current_room_name = r["name"] if r else ""

    return render_template(
        "edit_event.html",
        event=appt,
        start_local=start_local,
        doctors=doctors,
        patients=patients,
        cabinets=[r["name"] for r in rooms],
        services=services,
        current_room_name=current_room_name,
    )


@app.route("/api/busy_slots", methods=["POST"])
def api_busy_slots():
    data = request.get_json()
    doctor_id = data.get("doctor_id")
    date = data.get("date")
    # Получаем все события этого врача на эту дату
    slots = []
    for ev in db.events.find({"doctor_id": doctor_id}):
        ev_date = ev["start"][:10] if "start" in ev else ""
        if ev_date == date:
            # пример: если 'start': "2025-07-10T15:00"
            time_part = ev["start"].split("T")[1][:5]
            slots.append(time_part)
    return jsonify({"slots": slots})


@app.route("/busy_slots/<doctor_id>")
def busy_slots(doctor_id):
    # Получаем все записи врача за сегодня/неделю (или за весь календарь)
    from datetime import datetime, timedelta

    start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=14)  # например, 2 недели вперёд

    events = list(
        db.events.find(
            {"doctor_id": doctor_id, "start": {"$gte": start.isoformat(), "$lt": end.isoformat()}}
        )
    )
    # Возвращаем список интервалов (начало и конец)
    busy = []
    for e in events:
        busy.append({"start": e["start"], "end": e.get("end", e["start"])})
    return jsonify(busy)


# ======= ВРАЧИ =======
@app.route("/doctors")
def doctors():
    if "user_id" not in session:
        return redirect(url_for("login"))
    doctors = list(db.doctors.find())
    for d in doctors:
        d["_id"] = str(d["_id"])
    return render_template("doctors.html", doctors=doctors)


@app.route("/add_doctor", methods=["GET", "POST"])
def add_doctor():
    if "user_id" not in session:
        return redirect(url_for("login"))
    if request.method == "POST":
        doctor = {
            "full_name": request.form.get("full_name", ""),
            "specialization": request.form.get("specialization", ""),
            "email": request.form.get("email", ""),
            "phone": request.form.get("phone", ""),
            "avatar_url": request.form.get("avatar_url", "/static/avatars/demo-doctor.png"),
            "status": request.form.get("status", "активен"),
        }
        db.doctors.insert_one(doctor)
        write_log("add_doctor", comment=f"Добавлен врач {doctor['full_name']}", obj="Врач")
        return redirect(url_for("doctors"))
    return render_template("add_doctor.html")


@app.route("/doctor_card/<doctor_id>")
def doctor_card(doctor_id):
    doctor = db.doctors.find_one({"_id": ObjectId(doctor_id)})
    if not doctor:
        return "Врач не найден", 404
    appointments = list(db.events.find({"doctor_id": doctor_id}))
    return render_template("doctor_card.html", doctor=doctor, appointments=appointments)


@app.route("/doctor_busy_slots/<doctor_id>")
def doctor_busy_slots(doctor_id):
    # Находим все события по doctor_id (за ближайшие 30 дней, чтобы не тянуть всё подряд)
    from datetime import datetime, timedelta

    start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=30)
    events = list(
        db.events.find(
            {"doctor_id": doctor_id, "start": {"$gte": start.isoformat(), "$lt": end.isoformat()}}
        )
    )
    # Для каждого события возвращаем start и end
    busy = []
    for e in events:
        busy.append({"start": e["start"], "end": e.get("end", e["start"])})
    return jsonify({"busy_slots": busy})


from flask import jsonify, request


@app.route("/api/doctor_schedule", methods=["POST"])
def doctor_schedule():
    """
    Вход:  { doctor_id }
    Выход: { ok: true, schedule: { "0": {"start":"09:00","end":"21:00"}, ..., "6": {...} } }
    """
    payload = request.get_json(force=True, silent=True) or {}
    did = _to_oid(payload.get("doctor_id"))
    if not did:
        return jsonify({"ok": False, "error": "not_found"}), 404

    doc = db.doctors.find_one({"_id": did}, {"schedule": 1})
    if not doc:
        return jsonify({"ok": False, "error": "not_found"}), 404

    schedule = doc.get("schedule", {})  # ожидаемый словарь с ключами "0"..."6"
    return jsonify(ok=True, schedule=schedule)


# ======= ФИНАНСЫ =======
@app.route("/finance_report")
def finance_report():
    operations = list(db.finance.find())
    # ---- Фильтры из формы ----
    search = request.args.get("search", "").strip()
    type_filter = request.args.get("type", "")
    status_filter = request.args.get("status", "")

    # --- Фильтруем ---
    def match(op):
        ok = True
        if search:
            ok &= (
                search.lower() in op.get("doctor", "").lower()
                or search.lower() in op.get("patient", "").lower()
                or search.lower() in op.get("service", "").lower()
            )
        if type_filter:
            ok &= op.get("type", "") == type_filter
        if status_filter:
            ok &= op.get("status", "").lower() == status_filter.lower()
        return ok

    filtered_ops = [op for op in operations if match(op)]

    # --- Статистика по операциям ---
    income_ops = [int(op["amount"]) for op in filtered_ops if op["type"] == "Доход"]
    expense_ops = [int(op["amount"]) for op in filtered_ops if op["type"] == "Расход"]

    income = sum(income_ops)
    expenses = sum(expense_ops)
    debtors_count = 4  # demo
    debtors_sum = 32000  # demo
    avg_check = int(sum(income_ops) / len(income_ops)) if income_ops else 0

    # --- Для новых summary-полей (максимально топ) ---
    operations_count = len(filtered_ops)
    paid_ops = [op for op in filtered_ops if op.get("status") == "оплачен"]
    paid_count = len(paid_ops)
    paid_percent = int(100 * paid_count / operations_count) if operations_count else 0

    # Топ врач и услуга (по количеству операций)
    from collections import Counter

    top_doctor = Counter([op["doctor"] for op in filtered_ops if op.get("doctor")]).most_common(1)
    top_service = Counter([op["service"] for op in filtered_ops if op.get("service")]).most_common(
        1
    )
    top_doctor = top_doctor[0][0] if top_doctor else "—"
    top_service = top_service[0][0] if top_service else "—"

    # --- График по месяцам ---
    months = OrderedDict()
    for op in filtered_ops:
        m = op["date"].split(".")[1]  # MM
        months.setdefault(m, {"income": 0, "expenses": 0})
        if op["type"] == "Доход":
            months[m]["income"] += int(op["amount"])
        else:
            months[m]["expenses"] += int(op["amount"])
    chart_data = {
        "labels": [calendar.month_abbr[int(m)] for m in months.keys()],
        "datasets": [
            {
                "label": "Доходы",
                "borderColor": "#22c55e",
                "backgroundColor": "#dcfce7",
                "data": [v["income"] for v in months.values()],
                "tension": 0.4,
            },
            {
                "label": "Расходы",
                "borderColor": "#ef4444",
                "backgroundColor": "#fee2e2",
                "data": [v["expenses"] for v in months.values()],
                "tension": 0.4,
            },
        ],
    }

    summary = {
        "income": income,
        "expenses": expenses,
        "debtors_count": debtors_count,
        "debtors_sum": debtors_sum,
        "month_name": "июль",  # можно сделать динамично!
        "avg_check": avg_check,
        "operations_count": operations_count,
        "paid_count": paid_count,
        "paid_percent": paid_percent,
        "top_doctor": top_doctor,
        "top_service": top_service,
    }

    return render_template(
        "finance_report.html", summary=summary, operations=filtered_ops, chart_data=chart_data
    )


@app.route("/finance_report/export")
def finance_report_export():
    write_log("export", comment="Экспорт финансового отчёта", obj="Финансовый отчёт")
    operations = list(db.finance.find())
    income_sum = sum(int(op["amount"]) for op in operations if op["type"] == "Доход")
    expense_sum = sum(int(op["amount"]) for op in operations if op["type"] == "Расход")
    income_ops = [int(op["amount"]) for op in operations if op["type"] == "Доход"]
    avg_check = int(sum(income_ops) / len(income_ops)) if income_ops else 0
    debtors_count = 4  # demo
    debtors_sum = 32000  # demo
    report_month = "июль"

    data = {
        "Доходы": [income_sum],
        "Расходы": [expense_sum],
        "Средний чек": [avg_check],
        "Должники (чел)": [debtors_count],
        "Долги (₽)": [debtors_sum],
        "Месяц": [report_month],
    }
    format = request.args.get("format", "xlsx")
    if format == "csv":
        output = io.StringIO()
        df = pd.DataFrame(data)
        df.to_csv(output, index=False, sep=";")
        output.seek(0)
        return send_file(
            io.BytesIO(output.getvalue().encode("utf-8")),
            as_attachment=True,
            download_name="finance_report.csv",
            mimetype="text/csv",
        )
    else:
        output = io.BytesIO()
        df = pd.DataFrame(data)
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            df.to_excel(writer, index=False, sheet_name="Финансы")
        output.seek(0)
        return send_file(
            output,
            as_attachment=True,
            download_name="finance_report.xlsx",
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )


# ======= ОСНОВНЫЕ СТРАНИЦЫ/МОДУЛИ (ЗАГЛУШКИ) =======
@app.route("/tasks")
def tasks():
    if "user_id" not in session:
        return redirect(url_for("login"))
    # Формируем задачи для шаблона:
    tasks = list(db.tasks.find())
    for t in tasks:
        t["_id"] = str(t["_id"])
        assignee = (
            db.doctors.find_one({"_id": ObjectId(t.get("assigned_to", ""))})
            if t.get("assigned_to")
            else None
        )
        t["assigned_name"] = assignee["full_name"] if assignee else "Без исполнителя"
        t["assigned_avatar_url"] = (
            assignee["avatar_url"]
            if assignee and "avatar_url" in assignee
            else "/static/avatars/demo-user.png"
        )
    doctors = list(db.doctors.find())
    return render_template(
        "tasks.html", tasks=tasks, doctors=doctors
    )  # <-- ВОТ ЭТО ДОЛЖНО БЫТЬ ВНУТРИ ФУНКЦИИ!


@app.route("/add_task", methods=["POST"])
def add_task():
    task = {
        "title": request.form.get("title", ""),
        "description": request.form.get("description", ""),
        "assigned_to": request.form.get("assigned_to", ""),
        "due_date": request.form.get("due_date", ""),
        "status": "active",
        "priority": request.form.get("priority", "normal"),
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }
    db.tasks.insert_one(task)
    return redirect(url_for("tasks"))


@app.route("/mark_task_done/<task_id>")
def mark_task_done(task_id):
    db.tasks.update_one({"_id": ObjectId(task_id)}, {"$set": {"status": "done"}})
    write_log("task_done", comment=f"Задача {task_id} отмечена выполненной", obj="Задача")
    return redirect(url_for("tasks"))


@app.route("/task/<task_id>")
def task_card(task_id):
    if "user_id" not in session:
        return redirect(url_for("login"))
    task = db.tasks.find_one({"_id": ObjectId(task_id)})
    if not task:
        return "Задача не найдена", 404
    # Можно добавить подгрузку исполнителя, если нужно
    assignee = (
        db.doctors.find_one({"_id": ObjectId(task.get("assigned_to", ""))})
        if task.get("assigned_to")
        else None
    )
    task["assigned_name"] = assignee["full_name"] if assignee else ""
    task["assigned_avatar_url"] = (
        assignee["avatar_url"]
        if assignee and "avatar_url" in assignee
        else "/static/avatars/demo-user.png"
    )
    return render_template("task_card.html", task=task)


@app.route("/messages")
def messages():
    chats = list(db.messages.find())
    user_name = "Иванова Анна (админ)"  # Для демо
    return render_template("messages.html", chats=chats, user_name=user_name)


@app.route("/ztl")
def ztl():
    ztls = list(db.ztl.find({}))  # Забираем все лабораторные работы
    patients = {str(p["_id"]): p for p in db.patients.find()}
    doctors = {str(d["_id"]): d for d in db.doctors.find()}

    # Приводим ObjectId к строкам
    for w in ztls:
        for key in ["_id", "patient_id", "doctor_id"]:
            if key in w and isinstance(w[key], ObjectId):
                w[key] = str(w[key])

    return render_template("ztl.html", ztls=ztls, patients=patients, doctors=doctors)


@app.route("/add_ztl", methods=["GET", "POST"])
def add_ztl():
    if request.method == "POST":
        file = request.files.get("file")
        file_url = ""
        if file and file.filename:
            save_path = f"static/ztl/{file.filename}"
            file.save(save_path)
            file_url = "/" + save_path
        else:
            file_url = "/static/ztl/demo_ztl_1.png"
        ztl = {
            "patient_id": ObjectId(request.form["patient_id"]),
            "doctor_id": ObjectId(request.form["doctor_id"]),
            "type": request.form["type"],
            "order_date": request.form["order_date"],
            "due_date": request.form["due_date"],
            "status": request.form["status"],
            "comment": request.form.get("comment", ""),
            "file_url": file_url,
            "created_at": datetime.now().strftime("%Y-%m-%d"),
        }
        db.ztl.insert_one(ztl)
        return redirect(url_for("ztl"))
    patients = list(db.patients.find())
    doctors = list(db.doctors.find())
    return render_template("add_ztl.html", patients=patients, doctors=doctors)


@app.route("/partners")
def partners():
    # Получаем всех пациентов
    patients = list(db.patients.find())

    # Словарь для быстрого доступа: id (строкой) -> пациент
    patients_map = {str(p["_id"]): p for p in patients}

    # Словарь рефералов: id пригласителя -> список приглашённых пациентов
    referrals = {}
    for p in patients:
        inviter_id = str(p.get("invited_by")) if p.get("invited_by") else None
        if inviter_id:
            referrals.setdefault(inviter_id, []).append(p)
    return render_template(
        "partners.html",
        patients=patients,  # Список всех пациентов
        patients_map=patients_map,  # Быстрый доступ по id (для пригласителей)
        referrals=referrals,  # Кто кого пригласил
    )


@app.route("/logs")
def logs():
    write_log("logs_view", comment="Просмотр журнала действий", obj="Логи")
    logs = list(db.logs.find().sort("datetime", -1))  # Сортируем по дате
    return render_template("journal.html", logs=logs)


@app.route("/backup")
def backup():
    if "user_id" not in session:
        return redirect(url_for("login"))
    return render_template("backup.html")


@app.route("/profile")
def profile():
    return render_template("profile.html")


@app.route("/settings")
def settings():
    return render_template("settings.html")


@app.route("/data_tools", methods=["GET", "POST"])
def data_tools():
    # ... подгружаем историю экспорта/импорта
    history = list(db.imports.find().sort("datetime", -1))
    return render_template("data_tools.html", history=history)


@app.route("/export_data")
def export_data():
    # collection: patients, doctors, events, finance
    collection = request.args.get("collection", "patients")
    format = request.args.get("format", "xlsx")
    data = list(db[collection].find())
    # ... превратить ObjectId в строки для экспорта
    for d in data:
        d["_id"] = str(d["_id"])
    df = pd.DataFrame(data)
    output = io.BytesIO()
    filename = f"{collection}_{datetime.now().strftime('%Y-%m-%d_%H-%M')}.{format}"
    if format == "csv":
        output = io.StringIO()
        df.to_csv(output, index=False, sep=";")
        output.seek(0)
        return Response(
            output.getvalue(),
            mimetype="text/csv",
            headers={"Content-Disposition": f"attachment;filename={filename}"},
        )
    else:
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            df.to_excel(writer, index=False)
        output.seek(0)
        return send_file(
            output,
            as_attachment=True,
            download_name=filename,
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )


@app.route("/import_data", methods=["POST"])
def import_data():
    file = request.files["file"]
    collection = request.form["collection"]
    filename = file.filename
    result = ""
    try:
        if filename.endswith(".csv"):
            df = pd.read_csv(file, sep=";")
        else:
            df = pd.read_excel(file)
        # Валидация, подготовка
        db[collection].insert_many(df.to_dict("records"))
        result = f"Успешно ({len(df)} записей)"
    except Exception as e:
        result = f"Ошибка: {e}"
    # Логирование
    db.imports.insert_one(
        {
            "datetime": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "user": session.get("user_name", "гость"),
            "operation": "импорт",
            "collection": collection,
            "filename": filename,
            "result": result,
        }
    )
    flash(result)
    return redirect(url_for("data_tools"))


# ======= 404 =======
@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404


@app.route("/cabinet/<cabinet_name>")
def cabinet_card(cabinet_name):
    events = list(db.events.find({"cabinet": cabinet_name}))
    doctors = list(db.doctors.find())
    patients = list(db.patients.find())
    return render_template(
        "cabinet_card.html", cabinet=cabinet_name, events=events, doctors=doctors, patients=patients
    )


@app.route("/api/events")
def api_events():
    # 1) Диапазон, который шлёт FullCalendar
    start_str = request.args.get("start")
    end_str = request.args.get("end")
    patient_id = (request.args.get("patient_id") or "").strip()

    # 2) Фильтры (поддерживаем и id, и имена)
    doctor_id = request.args.get("doctor_id")
    room_id = request.args.get("room_id")
    room_name = request.args.get("room_name")
    service_id = request.args.get("service_id")
    service_name = request.args.get("service_name")

    start_dt = parse_iso(start_str)
    end_dt = parse_iso(end_str)

    # 3) Базовый запрос: пересечение диапазона
    q = {}
    if start_dt and end_dt:
        q["start"] = {"$lt": end_dt}
        q["end"] = {"$gt": start_dt}

    # 4) Фильтр по врачу
    if doctor_id:
        try:
            q["doctor_id"] = ObjectId(doctor_id)
        except Exception:
            pass

    # 5) Фильтр по кабинету
    if room_id:
        try:
            q["room_id"] = ObjectId(room_id)
        except Exception:
            pass
    elif room_name:
        r = db.rooms.find_one({"name": room_name}, {"_id": 1})
        if r:
            q["room_id"] = r["_id"]

    # 6) Фильтр по услуге
    if service_id:
        try:
            q["service_id"] = ObjectId(service_id)
        except Exception:
            pass
    elif service_name:
        s = db.services.find_one({"name": service_name}, {"_id": 1})
        if s:
            q["service_id"] = s["_id"]

    # 6+) Фильтр по пациенту
    if patient_id:
        try:
            q["patient_id"] = ObjectId(patient_id)
        except Exception:
            pass

    # 7) Справочники для названий/цветов
    doctors_map = {str(d["_id"]): d for d in db.doctors.find({}, {"full_name": 1, "avatar": 1})}
    patients_map = {str(p["_id"]): p for p in db.patients.find({}, {"full_name": 1, "avatar": 1})}
    services_map = {
        str(s["_id"]): s for s in db.services.find({}, {"name": 1, "color": 1, "duration_min": 1})
    }
    status_map = {
        s["key"]: s for s in db.visit_statuses.find({}, {"key": 1, "title": 1, "color": 1})
    }
    rooms_map = {str(r["_id"]): r for r in db.rooms.find({}, {"name": 1})}

    # 8) Формируем ответ в формате FullCalendar
    events = []
    cursor = db.appointments.find(q).sort("start", 1)

    for a in cursor:
        # --- нормализуем ID как строки (могут быть None)
        did = str(a.get("doctor_id") or "")
        pid = str(a.get("patient_id") or "")
        sid = str(a.get("service_id") or "")
        rid = str(a.get("room_id") or "")

        # --- гарантируем тип datetime
        a_start = to_dt(a.get("start"))
        if not a_start:
            # битая запись без даты — пропускаем
            continue

        a_end = to_dt(a.get("end"))
        if not a_end:
            # если нет end — считаем по длительности услуги (если есть), иначе 30 мин
            dur = services_map.get(sid, {}).get("duration_min", 30)
            try:
                dur = int(dur)
            except Exception:
                dur = 30
            a_end = add_minutes(a_start, dur)

        # --- справочники
        doc = doctors_map.get(did, {})
        pat = patients_map.get(pid, {})
        srv = services_map.get(sid, {})
        rm = rooms_map.get(rid, {})
        st = status_map.get(a.get("status_key", "scheduled"), {})

        # --- заголовок события
        title = f'{srv.get("name", "Услуга")} — {pat.get("full_name", "Пациент")}'

        events.append(
            {
                "id": str(a["_id"]),
                "title": title,
                "start": a_start.isoformat(),
                "end": a_end.isoformat(),
                "backgroundColor": st.get("color") or srv.get("color") or "#3498db",
                "borderColor": st.get("color") or srv.get("color") or "#3498db",
                "extendedProps": {
                    "patient": pat.get("full_name"),
                    "doctor": doc.get("full_name"),
                    "service": srv.get("name"),
                    "room": rm.get("name"),
                    "status": st.get("title"),
                    "doctor_id": did,
                    "patient_id": pid,
                    "service_id": sid,
                    "room_id": rid,
                },
            }
        )

    return jsonify(events)


@app.route("/api/services/<id>")
def api_service_get(id):
    try:
        oid = ObjectId(id)
    except Exception:
        return jsonify({"ok": False, "error": "bad_id"}), 400
    s = db.services.find_one({"_id": oid}, {"name": 1, "duration_min": 1, "price": 1, "color": 1})
    if not s:
        return jsonify({"ok": False, "error": "not_found"}), 404
    return jsonify(
        {
            "ok": True,
            "item": {
                "id": str(s["_id"]),
                "name": s.get("name"),
                "duration_min": int(s.get("duration_min") or 30),
                "price": s.get("price"),
                "color": s.get("color"),
            },
        }
    )


# 1) Справочники для модалки (РАСШИРЕНО: +patients, +rooms)
@app.route("/api/dicts", methods=["GET"])
def api_dicts():
    _db = app.config.get("DB", db)
    # на случай, если у тебя DB кладётся в app.config

    # Врачи
    docs = list(db.doctors.find({}, {"full_name": 1}))
    doctors = [{"id": str(x["_id"]), "name": x.get("full_name", "")} for x in docs]

    # Услуги
    srvs = list(db.services.find({}, {"name": 1, "duration_min": 1, "price": 1}))
    services = [
        {
            "id": str(x["_id"]),
            "name": x.get("name", ""),
            "duration_min": int(x.get("duration_min") or 30),
            "price": x.get("price", 0),
        }
        for x in srvs
    ]

    # Пациенты
    pats = list(db.patients.find({}, {"full_name": 1, "birthdate": 1}))
    patients = [
        {
            "id": str(p["_id"]),
            "name": p.get("full_name", "Без имени"),
            "birthdate": p.get("birthdate"),
        }
        for p in pats
    ]

    # Кабинеты
    rms = list(db.rooms.find({}, {"name": 1}))
    rooms = [{"id": str(r["_id"]), "name": r.get("name", "Кабинет")} for r in rms]

    return jsonify(
        {
            "ok": True,
            "doctors": doctors,
            "services": services,
            "patients": patients,
            "rooms": rooms,
        }
    )


# --- 2.2: занятость кабинета на день ---
@app.route("/api/rooms/busy")
def api_room_busy():
    """
    GET /api/rooms/busy?room_id=<oid|str>&date=YYYY-MM-DD
    Возвращает интервалы занятости кабинета на указанный день:
    { ok: True, items: [{start:'HH:MM', end:'HH:MM'}, ...] }
    """
    room_id = request.args.get("room_id", "").strip()
    date_s = request.args.get("date", "").strip()

    if not room_id or not date_s:
        return jsonify({"ok": False, "error": "bad_params"}), 400

    try:
        room_oid = ObjectId(room_id)
    except Exception:
        # допускаем, что к нам пришло имя кабинета — попробуем найти
        room = db.rooms.find_one({"name": room_id}, {"_id": 1})
        if not room:
            return jsonify({"ok": False, "error": "room_not_found"}), 404
        room_oid = room["_id"]

    try:
        day_start = datetime.strptime(date_s, "%Y-%m-%d")
    except Exception:
        return jsonify({"ok": False, "error": "bad_date"}), 400

    day_end = day_start + timedelta(days=1)

    # Берём все приёмы в этом кабинете, пересекающие день
    cur = db.appointments.find(
        {"room_id": room_oid, "start": {"$lt": day_end}, "end": {"$gt": day_start}},
        {"start": 1, "end": 1},
    )

    items = []
    for a in cur:
        st = max(a.get("start"), day_start)
        en = min(a.get("end"), day_end)
        if not isinstance(st, datetime) or not isinstance(en, datetime) or en <= st:
            continue
        items.append(
            {
                "start": st.strftime("%H:%M"),
                "end": en.strftime("%H:%M"),
            }
        )

    # Отсортируем по началу
    items.sort(key=lambda x: x["start"])
    return jsonify({"ok": True, "items": items})


# === Удаление приёма ===
@app.route("/delete_appointment/<id>", methods=["POST"])
def delete_appointment(id):
    try:
        oid = ObjectId(id)
    except Exception:
        return jsonify({"ok": False, "error": "bad_id"}), 400

    appt = db.appointments.find_one({"_id": oid}, {"room_id": 1})
    if not appt:
        return jsonify({"ok": False, "error": "not_found"}), 404

    room_id = appt.get("room_id")

    db.appointments.delete_one({"_id": oid})

    try:
        write_log("delete_appointment", obj=str(oid))
    except Exception:
        pass

    # Пересчитать статус...

    return jsonify({"ok": True})


# --- 2.3.1: получить запись для модалки ---
@app.route("/api/appointments/<id>")
def api_appointment_get(id):
    try:
        oid = ObjectId(id)
    except Exception:
        return jsonify({"ok": False, "error": "bad_id"}), 400

    a = db.appointments.find_one({"_id": oid})
    if not a:
        return jsonify({"ok": False, "error": "not_found"}), 404

    def strid(v):  # аккуратно приводим к строке
        return str(v) if isinstance(v, ObjectId) else (v or "")

    def fmt(dt):
        return dt.strftime("%Y-%m-%dT%H:%M") if isinstance(dt, datetime) else ""

    return jsonify(
        {
            "ok": True,
            "item": {
                "id": str(a["_id"]),
                "doctor_id": strid(a.get("doctor_id")),
                "patient_id": strid(a.get("patient_id")),
                "service_id": strid(a.get("service_id")),
                "room_id": strid(a.get("room_id")),
                "status_key": a.get("status_key", "scheduled"),
                "comment": a.get("comment", ""),
                "start": fmt(a.get("start")),
                "end": fmt(a.get("end")),
            },
        }
    )


# --- 2.3.2: полное обновление записи из модалки ---


@app.route("/api/appointments/<id>/update", methods=["POST"])
def api_appointment_update(id):
    data = request.get_json(force=True, silent=True) or {}
    try:
        oid = ObjectId(id)
    except Exception:
        return jsonify({"ok": False, "error": "bad_id"}), 400

    a = db.appointments.find_one({"_id": oid})
    if not a:
        return jsonify({"ok": False, "error": "not_found"}), 404

    updates = {}

    def as_oid(val):
        if not val:
            return None
        try:
            return ObjectId(val)
        except Exception:
            return None

    doc_oid = as_oid(data.get("doctor_id"))
    pat_oid = as_oid(data.get("patient_id"))
    srv_oid = as_oid(data.get("service_id"))
    room_oid = as_oid(data.get("room_id")) or a.get("room_id")

    if doc_oid:
        updates["doctor_id"] = doc_oid
    if pat_oid:
        updates["patient_id"] = pat_oid
    if srv_oid:
        updates["service_id"] = srv_oid
    if room_oid:
        updates["room_id"] = room_oid

    if "status_key" in data:
        updates["status_key"] = (data.get("status_key") or "scheduled").strip()
    if "comment" in data:
        updates["comment"] = (data.get("comment") or "").strip()

    start_dt = to_dt(data.get("start")) or a.get("start")
    end_dt = to_dt(data.get("end")) or a.get("end")

    if not end_dt:
        dur = 30
        if srv_oid:
            srv = db.services.find_one({"_id": srv_oid}, {"duration_min": 1}) or {}
            try:
                dur = int(srv.get("duration_min", 30))
            except Exception:
                dur = 30
        end_dt = start_dt + timedelta(minutes=dur)

    if not isinstance(start_dt, datetime) or not isinstance(end_dt, datetime) or end_dt <= start_dt:
        return jsonify({"ok": False, "error": "bad_dates"}), 400

    updates["start"] = start_dt
    updates["end"] = end_dt

    if room_oid:
        conflict = db.appointments.find_one(
            {
                "_id": {"$ne": oid},
                "room_id": room_oid,
                "start": {"$lt": end_dt},
                "end": {"$gt": start_dt},
            }
        )
        if conflict:
            return jsonify({"ok": False, "error": "room_conflict"}), 409

    db.appointments.update_one({"_id": oid}, {"$set": updates})
    try:
        recalc_room_status(room_oid)
        write_log(
            "update_appointment",
            obj=str(oid),
            extra={"start": start_dt.isoformat(), "end": end_dt.isoformat()},
        )
    except Exception:
        pass
    return jsonify({"ok": True})


@app.route("/api/appointments/update_time", methods=["POST"])
def api_appointments_update_time():
    data = request.get_json(force=True, silent=True) or {}
    appt_id = data.get("id")
    start_s = data.get("start")
    end_s = data.get("end")
    if not appt_id or not start_s or not end_s:
        return jsonify({"ok": False, "error": "bad_params"}), 400
    try:
        oid = ObjectId(appt_id)
    except Exception:
        return jsonify({"ok": False, "error": "bad_id"}), 400
    start_dt = to_dt(start_s)
    end_dt = to_dt(end_s)
    if not isinstance(start_dt, datetime) or not isinstance(end_dt, datetime) or end_dt <= start_dt:
        return jsonify({"ok": False, "error": "bad_datetime"}), 400

    # серверная валидация окна/шага
    err = validate_slot_bounds(start_dt, end_dt)
    if err:
        return jsonify({"ok": False, "error": err}), 400

    appt = db.appointments.find_one({"_id": oid}, {"room_id": 1})
    if not appt:
        return jsonify({"ok": False, "error": "not_found"}), 404
    room_id = appt.get("room_id")
    # conflict by room
    if room_id:
        conflict = db.appointments.find_one(
            {
                "_id": {"$ne": oid},
                "room_id": room_id,
                "start": {"$lt": end_dt},
                "end": {"$gt": start_dt},
            }
        )
        if conflict:
            return jsonify({"ok": False, "error": "room_conflict"}), 409
    db.appointments.update_one({"_id": oid}, {"$set": {"start": start_dt, "end": end_dt}})
    try:
        if room_id:
            recalc_room_status(room_id)
        write_log(
            "move_appointment",
            obj=str(oid),
            extra={"start": start_dt.isoformat(), "end": end_dt.isoformat()},
        )
    except Exception:
        pass
    return jsonify({"ok": True})


# --- DELETE appointment (все совместимые варианты) ---
@app.route("/api/appointments/<id>", methods=["DELETE"])
def api_appointments_delete_by_id(id):
    oid = _to_oid(id)
    if not oid:
        return jsonify({"ok": False, "error": "bad_id"}), 400
    db.appointments.delete_one({"_id": oid})
    return jsonify({"ok": True})


@app.route("/api/appointments/delete", methods=["POST"])
def api_appointments_delete_post():
    payload = request.get_json(force=True, silent=True) or {}
    return api_appointments_delete_by_id(payload.get("id"))


@app.route("/schedule/api/delete", methods=["POST"])
def schedule_api_delete_proxy():
    return api_appointments_delete_post()


# лёгкие справочники для фронта
@app.route("/api/services_min")
def api_services_min():
    items = []
    for s in db.services.find({}, {"name": 1, "duration_min": 1}).sort("name", 1):
        items.append(
            {"id": str(s["_id"]), "name": s["name"], "duration_min": s.get("duration_min", 30)}
        )
    return jsonify(items)


@app.route("/api/visit_statuses_min")
def api_visit_statuses_min():
    items = []
    for s in db.visit_statuses.find({}, {"key": 1, "title": 1}).sort("title", 1):
        items.append({"key": s["key"], "title": s["title"]})
    return jsonify(items)


@app.route("/api/finance/record", methods=["POST"])
def api_finance_record():
    data = request.get_json(force=True, silent=True) or {}
    pid = oid(data.get("patient_id"))
    kind = data.get("kind")  # payment | deposit | expense | payroll | procurement
    amount = int(data.get("amount", 0) or 0)
    source = data.get("source")  # alpha | sber | cash
    comment = (data.get("comment") or "").strip()
    doctor_id = oid(data.get("doctor_id")) if data.get("doctor_id") else None
    service_id = oid(data.get("service_id")) if data.get("service_id") else None
    expense_cat = data.get("expense_cat")  # rent/procurement/marketing/dividends/other

    if not kind or amount <= 0:
        return jsonify({"ok": False, "error": "bad_params"}), 400

    # строго из прайса: если указан service_id при payment — добавим сервис-чардж (чтобы долг считался)
    ts = datetime.now()
    doc = {
        "patient_id": pid,
        "kind": kind,
        "amount": amount,
        "source": source,
        "comment": comment,
        "doctor_id": doctor_id,
        "service_id": service_id,
        "expense_cat": expense_cat,
        "ts": ts,
        "ts_iso": ts.strftime("%Y-%m-%dT%H:%M"),
    }
    db.ledger.insert_one(doc)

    # если выбрана услуга и это оплата услуги — добавим строку service_charge (если её ещё нет на этот визит)
    if kind == "payment" and service_id:
        s = db.services.find_one({"_id": service_id}, {"price": 1})
        price = int((s or {}).get("price", 0) or 0)
        if price > 0:
            db.ledger.insert_one(
                {
                    "patient_id": pid,
                    "kind": "service_charge",
                    "amount": price,
                    "source": None,
                    "comment": f"Начисление за услугу",
                    "service_id": service_id,
                    "ts": ts,
                    "ts_iso": doc["ts_iso"],
                }
            )

    return jsonify({"ok": True})


@app.route("/api/chat/<id>/send", methods=["POST"])
def api_chat_send(id):
    _id = oid(id)
    if not _id:
        return jsonify({"ok": False, "error": "bad_id"}), 400
    data = request.get_json(force=True, silent=True) or {}
    text = (data.get("text") or "").strip()
    if not text:
        return jsonify({"ok": False, "error": "empty"}), 400
    ts = datetime.now()
    db.messages.insert_one(
        {
            "patient_id": _id,
            "from": "admin",  # дальше можем хранить user_id роли (админ/куратор)
            "text": text,
            "ts": ts,
            "ts_iso": ts.strftime("%Y-%m-%dT%H:%M"),
        }
    )
    return jsonify({"ok": True})


# ===================== УСЛУГИ (services) =====================


def _service_form_data():
    """Считываем и валидируем поля формы услуги."""
    name = (request.form.get("name") or "").strip()
    code = (request.form.get("code") or "").strip().upper()
    description = (request.form.get("description") or "").strip()
    price = request.form.get("price") or ""
    duration_min = request.form.get("duration_min") or ""
    color = request.form.get("color") or "#3498db"
    is_active = True if request.form.get("is_active") == "on" else False

    errors = []
    if not name:
        errors.append("Название обязательно.")
    if not code:
        errors.append("Код обязателен.")
    try:
        price = int(price)
        if price < 0:
            errors.append("Цена не может быть отрицательной.")
    except ValueError:
        errors.append("Цена должна быть числом.")
    try:
        duration_min = int(duration_min)
        if duration_min <= 0:
            errors.append("Длительность должна быть > 0.")
    except ValueError:
        errors.append("Длительность должна быть числом.")

    data = {
        "name": name,
        "code": code,
        "description": description,
        "price": price if not isinstance(price, str) else 0,
        "duration_min": duration_min if not isinstance(duration_min, str) else 30,
        "color": color,
        "is_active": is_active,
    }
    return data, errors


@app.route("/services")
def services_list():
    q = {}
    status = request.args.get("status")
    if status == "active":
        q["is_active"] = True
    elif status == "archived":
        q["is_active"] = False

    items = list(db.services.find(q).sort([("is_active", -1), ("name", 1)]))
    return render_template("services.html", items=items)


@app.route("/add_service", methods=["GET", "POST"])
def add_service():
    if request.method == "POST":
        data, errors = _service_form_data()
        # проверка уникальности кода
        if db.services.find_one({"code": data["code"]}):
            errors.append("Код услуги уже используется.")
        if errors:
            for e in errors:
                flash(e, "danger")
            return render_template("add_service.html", form=data)
        data["created_at"] = datetime.utcnow()
        data["updated_at"] = datetime.utcnow()
        db.services.insert_one(data)
        flash("Услуга добавлена.", "success")
        return redirect(url_for("services_list"))
    # GET
    return render_template(
        "add_service.html",
        form={"color": "#3498db", "duration_min": 30, "price": 0, "is_active": True},
    )


@app.route("/edit_service/<id>", methods=["GET", "POST"])
def edit_service(id):
    item = db.services.find_one({"_id": ObjectId(id)})
    if not item:
        flash("Услуга не найдена.", "danger")
        return redirect(url_for("services_list"))

    if request.method == "POST":
        data, errors = _service_form_data()
        # уникальность кода (не считая текущую запись)
        other = db.services.find_one({"code": data["code"], "_id": {"$ne": ObjectId(id)}})
        if other:
            errors.append("Код услуги уже используется.")
        if errors:
            for e in errors:
                flash(e, "danger")
            # вернуть введённые данные
            item.update(data)
            return render_template("edit_service.html", item=item)
        db.services.update_one(
            {"_id": ObjectId(id)}, {"$set": {**data, "updated_at": datetime.utcnow()}}
        )
        flash("Изменения сохранены.", "success")
        return redirect(url_for("services_list"))

    return render_template("edit_service.html", item=item)


@app.route("/delete_service/<id>", methods=["POST"])
def delete_service(id):
    db.services.delete_one({"_id": ObjectId(id)})
    flash("Услуга удалена.", "success")
    return redirect(url_for("services_list"))


# =================== /УСЛУГИ (services) ======================

# ===================== КАБИНЕТЫ (rooms) =====================

# Справочники для удобного выбора в формах
ROOM_TYPES = [
    ("Терапия", "Терапия"),
    ("Хирургия", "Хирургия"),
    ("Рентген", "Рентген"),
    ("Гигиена", "Гигиена"),
    ("Ортопедия", "Ортопедия"),
    ("Ортодонтия", "Ортодонтия"),
]
ROOM_STATUSES = [
    ("available", "Свободен"),
    ("occupied", "Занят"),
    ("maintenance", "Обслуживание"),
]


def _room_form_data():
    name = (request.form.get("name") or "").strip()
    rtype = (request.form.get("type") or "").strip()
    status = (request.form.get("status") or "available").strip()
    color = (request.form.get("color") or "#1abc9c").strip()
    errors = []
    if not name:
        errors.append("Название кабинета обязательно.")
    if rtype not in [t[0] for t in ROOM_TYPES]:
        errors.append("Некорректный тип кабинета.")
    if status not in [s[0] for s in ROOM_STATUSES]:
        errors.append("Некорректный статус кабинета.")
    return {"name": name, "type": rtype, "status": status, "color": color}, errors


@app.route("/rooms")
def rooms_list():
    items = list(db.rooms.find({}).sort([("name", 1)]))
    # Для тултипа статуса на русском
    status_title = dict(ROOM_STATUSES)
    return render_template("rooms.html", items=items, status_title=status_title)


@app.route("/add_room", methods=["GET", "POST"])
def add_room():
    if request.method == "POST":
        data, errors = _room_form_data()
        # уникальность имени кабинета
        if db.rooms.find_one({"name": data["name"]}):
            errors.append("Кабинет с таким названием уже существует.")
        if errors:
            for e in errors:
                flash(e, "danger")
            return render_template(
                "add_room.html", form=data, ROOM_TYPES=ROOM_TYPES, ROOM_STATUSES=ROOM_STATUSES
            )
        data["created_at"] = datetime.utcnow()
        data["updated_at"] = datetime.utcnow()
        db.rooms.insert_one(data)
        flash("Кабинет добавлен.", "success")
        return redirect(url_for("rooms_list"))

    # GET
    return render_template(
        "add_room.html",
        form={"type": "Терапия", "status": "available", "color": "#1abc9c"},
        ROOM_TYPES=ROOM_TYPES,
        ROOM_STATUSES=ROOM_STATUSES,
    )


@app.route("/edit_room/<id>", methods=["GET", "POST"])
def edit_room(id):
    item = db.rooms.find_one({"_id": ObjectId(id)})
    if not item:
        flash("Кабинет не найден.", "danger")
        return redirect(url_for("rooms_list"))

    if request.method == "POST":
        data, errors = _room_form_data()
        # уникальность имени (кроме текущего)
        other = db.rooms.find_one({"name": data["name"], "_id": {"$ne": ObjectId(id)}})
        if other:
            errors.append("Кабинет с таким названием уже существует.")
        if errors:
            for e in errors:
                flash(e, "danger")
            item.update(data)
            return render_template(
                "edit_room.html", item=item, ROOM_TYPES=ROOM_TYPES, ROOM_STATUSES=ROOM_STATUSES
            )
        db.rooms.update_one(
            {"_id": ObjectId(id)}, {"$set": {**data, "updated_at": datetime.utcnow()}}
        )
        flash("Изменения сохранены.", "success")
        return redirect(url_for("rooms_list"))

    return render_template(
        "edit_room.html", item=item, ROOM_TYPES=ROOM_TYPES, ROOM_STATUSES=ROOM_STATUSES
    )


@app.route("/delete_room/<id>", methods=["POST"])
def delete_room(id):
    db.rooms.delete_one({"_id": ObjectId(id)})
    flash("Кабинет удалён.", "success")
    return redirect(url_for("rooms_list"))


# =================== /КАБИНЕТЫ (rooms) ======================

# ===================== ПАЦИЕНТЫ (patients) =====================


def _patient_form_data():
    full_name = (request.form.get("full_name") or "").strip()
    birthday = (request.form.get("birthday") or "").strip()  # 'YYYY-MM-DD'
    gender = (request.form.get("gender") or "").strip()  # male/female/other
    phone = (request.form.get("phone") or "").strip()
    email = (request.form.get("email") or "").strip()
    whatsapp = (request.form.get("whatsapp") or "").strip()
    telegram = (request.form.get("telegram") or "").strip()
    city = (request.form.get("city") or "").strip()
    street = (request.form.get("street") or "").strip()
    zipc = (request.form.get("zip") or "").strip()
    notes = (request.form.get("notes") or "").strip()
    avatar = (
        request.form.get("avatar") or ""
    ).strip()  # относительный путь '/static/avatars/patients/p1.jpg'

    errors = []
    if not full_name:
        errors.append("ФИО обязательно.")
    # простая валидация даты
    bdate = None
    if birthday:
        try:
            bdate = datetime.strptime(birthday, "%Y-%m-%d")
        except ValueError:
            errors.append("Дата рождения должна быть в формате ГГГГ-ММ-ДД.")

    data = {
        "full_name": full_name,
        "birthday": bdate,
        "gender": gender or "other",
        "contacts": {"phone": phone, "email": email, "whatsapp": whatsapp, "telegram": telegram},
        "address": {"city": city, "street": street, "zip": zipc},
        "notes": notes,
        "avatar": avatar or "/static/avatars/patients/default.jpg",
        "updated_at": datetime.utcnow(),
    }
    return data, errors


@app.route("/patients")
def patients_list():
    q = {}
    # Поиск по ФИО или телефону/почте
    search = (request.args.get("q") or "").strip()
    if search:
        q = {
            "$or": [
                {"full_name": {"$regex": search, "$options": "i"}},
                {"contacts.phone": {"$regex": search, "$options": "i"}},
                {"contacts.email": {"$regex": search, "$options": "i"}},
            ]
        }

    items = list(db.patients.find(q).sort([("full_name", 1)]))

    # НОРМАЛИЗАЦИЯ: гарантируем contacts/avatar/адреса, строковый _id
    for p in items:
        p["_id"] = str(p.get("_id"))
        # contacts
        contacts = p.get("contacts") or {}
        if not isinstance(contacts, dict):
            contacts = {}
        contacts.setdefault("phone", "")
        contacts.setdefault("email", "")
        contacts.setdefault("whatsapp", "")
        contacts.setdefault("telegram", "")
        p["contacts"] = contacts
        # avatar
        if not p.get("avatar"):
            p["avatar"] = "/static/avatars/patients/default.jpg"
        # address
        addr = p.get("address") or {}
        if not isinstance(addr, dict):
            addr = {}
        addr.setdefault("city", "")
        addr.setdefault("street", "")
        addr.setdefault("zip", "")
        p["address"] = addr

    # Быстрый счётчик визитов
    appts_count = {}
    if items:
        ids = [ObjectId(p["_id"]) for p in items if p.get("_id")]
        if ids:
            pipeline = [
                {"$match": {"patient_id": {"$in": ids}}},
                {"$group": {"_id": "$patient_id", "cnt": {"$sum": 1}}},
            ]
            for r in db.appointments.aggregate(pipeline):
                appts_count[str(r["_id"])] = r["cnt"]

    return render_template("patients.html", items=items, appts_count=appts_count, search=search)


@app.route("/add_patient", methods=["GET", "POST"])
def add_patient():
    if request.method == "POST":
        data, errors = _patient_form_data()
        if errors:
            for e in errors:
                flash(e, "danger")
            return render_template("add_patient.html", form=data)
        data["created_at"] = datetime.utcnow()
        db.patients.insert_one(data)
        flash("Пациент добавлен.", "success")
        return redirect(url_for("patients_list"))
    # GET
    return render_template("add_patient.html", form={})


@app.route("/edit_patient/<id>", methods=["GET", "POST"])
def edit_patient(id):
    item = db.patients.find_one({"_id": ObjectId(id)})
    if not item:
        flash("Пациент не найден.", "danger")
        return redirect(url_for("patients_list"))

    if request.method == "POST":
        data, errors = _patient_form_data()
        if errors:
            for e in errors:
                flash(e, "danger")
            # подставим обратно введённые значения
            item.update(data)
            return render_template("edit_patient.html", item=item)
        db.patients.update_one({"_id": ObjectId(id)}, {"$set": data})
        flash("Изменения сохранены.", "success")
        return redirect(url_for("patients_list"))

    # GET
    return render_template("edit_patient.html", item=item)


@app.route("/delete_patient/<id>", methods=["POST"])
def delete_patient(id):
    db.patients.delete_one({"_id": ObjectId(id)})
    # связанные визиты умышленно не трогаем (историчность)
    flash("Пациент удалён.", "success")
    return redirect(url_for("patients_list"))


@app.route("/patient_card/<id>")
def patient_card(id):
    try:
        oid = ObjectId(id)
    except Exception:
        flash("Некорректный ID пациента.", "danger")
        return redirect(url_for("patients_list"))

    p = db.patients.find_one({"_id": oid})
    if not p:
        flash("Пациент не найден.", "danger")
        return redirect(url_for("patients_list"))

    # Нормализуем поля, чтоб шаблон не падал
    p.setdefault("card_no", "")
    p.setdefault("sex", "")
    p.setdefault("birthdate", "")  # храним строкой 'YYYY-MM-DD'
    p.setdefault("phone", "")
    p.setdefault("email", "")
    p.setdefault("full_name", "")
    p.setdefault("notes", "")

    # Анкета
    q = p.get("questionary", {}) or {}
    questionary = {
        "allergy": s(q.get("allergy")),
        "chronic": s(q.get("chronic")),
        "surgeries": s(q.get("surgeries")),
        "medications": s(q.get("medications")),
        "infections": s(q.get("infections")),
        "pregnancy": s(q.get("pregnancy")),
        "other": s(q.get("other")),
    }

    return render_template("patient_card.html", p=p, questionary=questionary)


@app.route("/api/patients/<id>/update_info", methods=["POST"])
def api_patient_update_info(id):
    try:
        oid = ObjectId(id)
    except Exception:
        return jsonify({"ok": False, "error": "bad_id"}), 400

    p = db.patients.find_one({"_id": oid})
    if not p:
        return jsonify({"ok": False, "error": "not_found"}), 404

    data = request.get_json(force=True, silent=True) or {}

    upd = {
        "full_name": s(data.get("full_name")),
        "phone": s(data.get("phone")),
        "email": s(data.get("email")),
        "sex": s(data.get("sex")),  # 'm' | 'f' | ''
        "birthdate": parse_date_yyyy_mm_dd(data.get("birthdate")),
        "notes": s(data.get("notes")),
    }

    # card_no можно менять вручную (или сгенерировать отдельной кнопкой)
    if "card_no" in data:
        upd["card_no"] = s(data.get("card_no"))

    db.patients.update_one({"_id": oid}, {"$set": upd})
    return jsonify({"ok": True})


@app.route("/api/patients/<id>/update_questionary", methods=["POST"])
def api_patient_update_questionary(id):
    try:
        oid = ObjectId(id)
    except Exception:
        return jsonify({"ok": False, "error": "bad_id"}), 400

    if not db.patients.find_one({"_id": oid}):
        return jsonify({"ok": False, "error": "not_found"}), 404

    data = request.get_json(force=True, silent=True) or {}
    q = {
        "allergy": s(data.get("allergy")),
        "chronic": s(data.get("chronic")),
        "surgeries": s(data.get("surgeries")),
        "medications": s(data.get("medications")),
        "infections": s(data.get("infections")),
        "pregnancy": s(data.get("pregnancy")),
        "other": s(data.get("other")),
    }
    db.patients.update_one({"_id": oid}, {"$set": {"questionary": q}})
    return jsonify({"ok": True})


@app.route("/api/patients/<id>/generate_card_no", methods=["POST"])
def api_patient_generate_card_no(id):
    try:
        oid = ObjectId(id)
    except Exception:
        return jsonify({"ok": False, "error": "bad_id"}), 400

    p = db.patients.find_one({"_id": oid})
    if not p:
        return jsonify({"ok": False, "error": "not_found"}), 404

    if s(p.get("card_no")):
        return jsonify({"ok": False, "error": "already_exists"}), 409

    cn = make_card_no()
    db.patients.update_one({"_id": oid}, {"$set": {"card_no": cn}})
    return jsonify({"ok": True, "card_no": cn})


@app.route("/api/patients/<id>/full")
def api_patient_full(id):
    _id = oid(id)
    if not _id:
        return jsonify({"ok": False, "error": "bad_id"}), 400

    p = db.patients.find_one({"_id": _id})
    if not p:
        return jsonify({"ok": False, "error": "not_found"}), 404

    # ledger (финансовые операции)
    ledger = []
    for x in db.ledger.find({"patient_id": _id}).sort("ts", -1).limit(200):
        # подтянем имя услуги
        sname = ""
        sid = x.get("service_id")
        if sid:
            svc = db.services.find_one({"_id": sid}, {"name": 1})
            sname = svc.get("name", "") if svc else ""
        ledger.append(
            {
                "ts": x.get("ts_iso") or iso_now(x.get("ts")),
                "kind": x.get("kind", ""),
                "amount": int(x.get("amount", 0) or 0),
                "source": x.get("source", ""),
                "service_name": sname,
                "comment": x.get("comment", ""),
            }
        )

    # долги/депозит: простая модель
    # debt = сумма услуг (kind=service_charge) - оплаты (kind=payment) - списания с депозита (kind=deposit_use)
    # deposit = внесено (kind=deposit) - использовано (kind=deposit_use)
    svc_total = sum(
        int(x.get("amount", 0) or 0)
        for x in db.ledger.find({"patient_id": _id, "kind": "service_charge"})
    )
    pay_total = sum(
        int(x.get("amount", 0) or 0) for x in db.ledger.find({"patient_id": _id, "kind": "payment"})
    )
    dep_in = sum(
        int(x.get("amount", 0) or 0) for x in db.ledger.find({"patient_id": _id, "kind": "deposit"})
    )
    dep_use = sum(
        int(x.get("amount", 0) or 0)
        for x in db.ledger.find({"patient_id": _id, "kind": "deposit_use"})
    )

    debt = max(0, svc_total - pay_total - dep_use)
    deposit = max(0, dep_in - dep_use)

    # простые агрегаты для карточки
    plans = list(db.plans.find({"patient_id": _id}, {"title": 1, "comment": 1}).sort("created", -1))
    plans = [{"title": pl.get("title", ""), "comment": pl.get("comment", "")} for pl in plans]

    # последние визиты
    appts = []
    for a in db.appointments.find({"patient_id": _id}).sort("start", -1).limit(20):
        appts.append({"start": iso_now(a.get("start")), "title": a.get("title") or "Визит"})

    survey = db.surveys.find_one({"patient_id": _id}) or {}
    survey = {
        "allergy": survey.get("allergy", ""),
        "chronic": survey.get("chronic", ""),
        "surgeries": survey.get("surgeries", ""),
        "other": survey.get("other", ""),
    }

    tasks = []
    for t in db.tasks.find({"patient_id": _id}).sort("created", -1).limit(50):
        tasks.append(
            {
                "title": t.get("title", ""),
                "status": t.get("status", "в работе"),
                "deadline": t.get("deadline_iso", ""),
            }
        )

    chat = []
    for m in db.messages.find({"patient_id": _id}).sort("ts", -1).limit(50):
        chat.append(
            {
                "from": m.get("from", "admin"),
                "ts": m.get("ts_iso") or iso_now(m.get("ts")),
                "text": m.get("text", ""),
            }
        )
    chat.reverse()

    return jsonify(
        {
            "ok": True,
            "patient": {
                "id": id,
                "full_name": p.get("full_name", ""),
                "card_number": p.get("card_number", ""),
            },
            "stats": {
                "debt": debt,
                "deposit": deposit,
                "incash": pay_total,  # условно показываем суммы оплат как "в кассе (пациент)"
            },
            "ledger": ledger,
            "plans": plans,
            "appts": appts,
            "survey": survey,
            "tasks": tasks,
            "chat": chat,
        }
    )

    # нормализация полей, чтобы шаблон не падал
    p["_id"] = str(p["_id"])
    contacts = p.get("contacts") or {}
    if not isinstance(contacts, dict):
        contacts = {}
    contacts.setdefault("phone", "")
    contacts.setdefault("email", "")
    contacts.setdefault("whatsapp", "")
    contacts.setdefault("telegram", "")
    p["contacts"] = contacts

    addr = p.get("address") or {}
    if not isinstance(addr, dict):
        addr = {}
    addr.setdefault("city", "")
    addr.setdefault("street", "")
    addr.setdefault("zip", "")
    p["address"] = addr

    if not p.get("avatar"):
        p["avatar"] = "/static/avatars/patients/default.jpg"

    # последние 50 визитов пациента
    visits = list(
        db.appointments.find({"patient_id": ObjectId(p["_id"])}).sort("start", -1).limit(50)
    )

    # справочники для отображения
    doctor_map = {str(d["_id"]): d for d in db.doctors.find({}, {"full_name": 1})}
    service_map = {
        str(s["_id"]): s
        for s in db.services.find({}, {"name": 1, "price": 1, "color": 1, "duration_min": 1})
    }
    room_map = {str(r["_id"]): r for r in db.rooms.find({}, {"name": 1})}
    status_map = {
        s["key"]: s for s in db.visit_statuses.find({}, {"key": 1, "title": 1, "color": 1})
    }

    # приводим события к удобному виду
    visits_view = []
    for v in visits:
        sid = str(v.get("service_id") or "")
        did = str(v.get("doctor_id") or "")
        rid = str(v.get("room_id") or "")
        st_key = v.get("status_key", "")
        v_start = to_dt(v.get("start"))
        v_end = to_dt(v.get("end"))
        if not v_start:
            continue
        if not v_end:
            dur = service_map.get(sid, {}).get("duration_min", 30)
            try:
                dur = int(dur)
            except:
                dur = 30
            v_end = add_minutes(v_start, dur)

        visits_view.append(
            {
                "_id": str(v["_id"]),
                "start_iso": v_start.strftime("%Y-%m-%d %H:%M"),
                "end_iso": v_end.strftime("%Y-%m-%d %H:%M"),
                "doctor": doctor_map.get(did, {}).get("full_name", "—"),
                "service": service_map.get(sid, {}).get("name", "—"),
                "service_price": service_map.get(sid, {}).get("price", None),
                "room": room_map.get(rid, {}).get("name", "—"),
                "status": status_map.get(st_key, {}).get("title", "—"),
                "status_color": status_map.get(st_key, {}).get("color", "#3498db"),
                "sum": v.get("sum", 0),
                "comment": v.get("comment", ""),
            }
        )

    return render_template("patient_card.html", p=p, visits=visits_view)


# ============== ПАЦИЕНТ: просмотр/редактирование ==============


@app.get("/patients/<pid>")
def patient_view(pid):
    p = db.patients.find_one({"_id": ObjectId(pid)})
    if not p:
        abort(404)
    return render_template("patient_view.html", p=p)


@app.get("/patients/<pid>/edit")
def patient_edit_form(pid):
    p = db.patients.find_one({"_id": ObjectId(pid)})
    if not p:
        abort(404)
    return render_template("patient_edit.html", p=p)


@app.post("/patients/<pid>/edit")
def patient_edit_save(pid):
    data = request.form.to_dict()
    # нормализация
    upd = {
        "last_name": data.get("last_name", "").strip(),
        "first_name": data.get("first_name", "").strip(),
        "middle_name": data.get("middle_name", "").strip(),
        "birth_date": data.get("birth_date") or None,
        "sex": data.get("sex") or None,
        "phone_mobile": data.get("phone_mobile", "").strip(),
        "phone_home": data.get("phone_home", "").strip(),
        "email": data.get("email", "").strip(),
        "representative_name": data.get("representative_name", "").strip(),
        "representative_phone": data.get("representative_phone", "").strip(),
        "address": {
            "region": data.get("addr_region", "").strip(),
            "city": data.get("addr_city", "").strip(),
            "street": data.get("addr_street", "").strip(),
            "house": data.get("addr_house", "").strip(),
            "apt": data.get("addr_apt", "").strip(),
        },
        "primary_doctor_id": data.get("primary_doctor_id") or None,
        "coordinator_id": data.get("coordinator_id") or None,
        "company_id": data.get("company_id") or None,
        "tags": [t.strip() for t in (data.get("tags") or "").split(",") if t.strip()],
        "updated_at": datetime.utcnow(),
    }
    # авто-№ карты если пуст
    if not data.get("card_no"):
        upd["card_no"] = next_card_no()
    else:
        upd["card_no"] = data["card_no"].strip()

    db.patients.update_one({"_id": ObjectId(pid)}, {"$set": upd})
    flash("Изменения сохранены", "ok")
    return redirect(url_for("patient_view", pid=pid))


def next_card_no():
    # простой автоинкремент, без гонок для одиночной инстанции
    last = (
        db.patients.find({"card_no": {"$exists": True, "$ne": None}})
        .sort([("card_no", -1)])
        .limit(1)
    )
    last = list(last)
    try:
        n = int(last[0]["card_no"].lstrip("№").strip()) + 1 if last else 1
    except Exception:
        n = 1
    return f"№{n}"


# ============== АНКЕТА ==============


@app.get("/patients/<pid>/questionnaire")
def questionnaire_form(pid):
    p = db.patients.find_one({"_id": ObjectId(pid)})
    if not p:
        abort(404)
    qs = p.get("questionnaire") or {"version": 1, "answers": []}
    return render_template("patient_questionnaire.html", p=p, qs=qs)


@app.post("/patients/<pid>/questionnaire")
def questionnaire_save(pid):
    payload = request.get_json(force=True, silent=True) or {}
    qs = {"version": 1, "answers": payload.get("answers", [])}
    db.patients.update_one(
        {"_id": ObjectId(pid)}, {"$set": {"questionnaire": qs, "updated_at": datetime.utcnow()}}
    )
    return jsonify(ok=True)


# --- ROUTES.md auto-refresh on startup (write to docs/ and project root) --
# DOCS dir exists
DOCS = Path(app.root_path) / "docs"
DOCS.mkdir(parents=True, exist_ok=True)

# fallback: define _dump_routes_md if откуда-то не подтянулся
if "_dump_routes_md" not in globals():

    def _dump_routes_md(flask_app):
        lines = []
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        lines.append("# Flask routes map\n")
        lines.append(f"_generated: {ts}_\n")
        lines.append("\n| Rule | Endpoint | Methods |")
        lines.append("|------|----------|---------|")
        for r in sorted(flask_app.url_map.iter_rules(), key=lambda x: str(x.rule)):
            methods = ",".join(sorted(m for m in r.methods if m not in {"HEAD", "OPTIONS"}))
            lines.append(f"| `{r.rule}` | `{r.endpoint}` | `{methods}` |")
        lines.append("")
        return "\n".join(lines)


try:
    md = _dump_routes_md(app)
    p_docs = DOCS / "ROUTES.md"
    p_root = Path(app.root_path) / "ROUTES.md"  # дублируем в корень
    p_docs.write_text(md, encoding="utf-8")
    p_root.write_text(md, encoding="utf-8")
    print(f"[OK] ROUTES.md updated:\n - {p_docs}\n - {p_root}")
except Exception as e:
    print(f"[WARN] ROUTES.md update failed: {e}")


# === API: создать пациента (для модалки календаря) ===
@app.route("/api/patients", methods=["POST"])
def api_patients_create():
    data = request.get_json(silent=True) or {}
    full_name = (data.get("full_name") or "").strip()
    if not full_name:
        return jsonify({"ok": False, "error": "full_name_required"}), 400

    doc = {
        "full_name": full_name,
        "phone": (data.get("phone") or "").strip(),
        "birth_date": (data.get("birth_date") or data.get("birthdate") or "").strip(),
        "card_no": data.get("card_no"),
        "created_at": datetime.utcnow(),
    }

    # ← вот здесь и должен быть блок авто-нумерации (НЕ на уровне модуля!)
    if not doc.get("card_no"):
        seq = db.counters.find_one_and_update(
            {"_id": "patient_card_no"},
            {"$inc": {"seq": 1}},
            upsert=True,
            return_document=ReturnDocument.AFTER,
        )
        doc["card_no"] = int(seq.get("seq", 1))

    ins = db.patients.insert_one(doc)
    return jsonify({"ok": True, "id": str(ins.inserted_id), "full_name": doc["full_name"]})


# === API: создать запись (appointments.create) ===============================


def _parse_dt(value: str) -> datetime:
    """
    Принимает 'YYYY-MM-DDTHH:MM' | 'YYYY-MM-DDTHH:MM:SS' | c суффиксом 'Z'.
    Возвращает datetime (naive, UTC-агностичный).
    """
    if not value:
        raise ValueError("empty datetime")
    v = value.strip().replace("Z", "")
    # добавим секунды при необходимости
    if len(v) == 16:  # 'YYYY-MM-DDTHH:MM'
        v = v + ":00"
    try:
        return datetime.fromisoformat(v[:19])
    except Exception:
        # запасные варианты
        for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M"):
            try:
                return datetime.strptime(v[:19], fmt)
            except Exception:
                pass
    raise ValueError(f"bad datetime: {value}")


@app.route("/api/appointments/create_core", methods=["POST"])
def api_appointments_create():
    """
    Создать приём (запись в календаре).
    Ожидает JSON:
    {
      start, end, room_id, doctor_id, patient_id, service_id,
      note? (строка), status_key? ("scheduled" по умолчанию)
    }
    Возвращает: { ok: true, id } | { ok:false, error }
    """
    payload = request.get_json(silent=True) or {}

    # обязательные поля
    room_id = payload.get("room_id") or ""
    doctor_id = payload.get("doctor_id") or ""
    patient_id = payload.get("patient_id") or ""
    service_id = payload.get("service_id") or ""
    start_raw = payload.get("start") or ""
    end_raw = payload.get("end") or start_raw

    if not (room_id and doctor_id and patient_id and service_id and start_raw):
        return jsonify({"ok": False, "error": "required_fields"}), 400

    try:
        start_dt = _parse_dt(start_raw)
        end_dt = _parse_dt(end_raw)
    except ValueError:
        return jsonify({"ok": False, "error": "bad_datetime"}), 400

    # серверная валидация окна/шага
    err = validate_slot_bounds(start_dt, end_dt)
    if err:
        # фронт корректно поймёт эти коды
        return jsonify({"ok": False, "error": err}), 400

    if end_dt <= start_dt:
        return jsonify({"ok": False, "error": "bad_range"}), 400

    room_oid = _to_oid(room_id)
    doctor_oid = _to_oid(doctor_id)
    patient_oid = _to_oid(patient_id)
    service_oid = _to_oid(service_id)

    if not all([room_oid, doctor_oid, patient_oid, service_oid]):
        return jsonify({"ok": False, "error": "bad_id"}), 400

    # --- конфликт по КАБИНЕТУ (пересечение интервалов)
    # условие пересечения: (existing.start < new.end) AND (existing.end > new.start)
    room_conflict = db.appointments.find_one(
        {
            "room_id": room_oid,
            "start": {"$lt": end_dt},
            "end": {"$gt": start_dt},
            # можно исключить "cancelled", если у вас такие записи есть:
            # "status_key": {"$ne": "cancelled"}
        },
        {"_id": 1},
    )
    if room_conflict:
        # фронт понимает и "conflict", и "room_conflict"
        return jsonify({"ok": False, "error": "room_conflict"}), 409

    # --- (необязательно) конфликт по ВРАЧУ
    doctor_conflict = db.appointments.find_one(
        {
            "doctor_id": doctor_oid,
            "start": {"$lt": end_dt},
            "end": {"$gt": start_dt},
            # "status_key": {"$ne": "cancelled"}
        },
        {"_id": 1},
    )
    if doctor_conflict:
        return jsonify({"ok": False, "error": "conflict"}), 409

    doc = {
        "start": start_dt,
        "end": end_dt,
        "room_id": room_oid,
        "doctor_id": doctor_oid,
        "patient_id": patient_oid,
        "service_id": service_oid,
        "status_key": (payload.get("status_key") or "scheduled"),
        "note": (payload.get("note") or "").strip(),
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }
    ins = db.appointments.insert_one(doc)

    # (опционально) лог
    try:
        write_log(
            "create_appointment",
            obj=str(ins.inserted_id),
            extra={
                "room_id": str(room_oid),
                "doctor_id": str(doctor_oid),
                "patient_id": str(patient_oid),
                "service_id": str(service_oid),
                "start": start_dt.isoformat(),
                "end": end_dt.isoformat(),
            },
        )
    except Exception:
        pass

    return jsonify({"ok": True, "id": str(ins.inserted_id)})


# --- unified aliases for creation (одна точка входа, без дублей endpoints) ---
@app.route("/api/appointments", methods=["POST"])
@app.route("/api/appointments/create", methods=["POST"])
@app.route("/schedule/api/create", methods=["POST"])
def api_appointments_create_router():
    return api_appointments_create()


# === END create appointment ===================================================


@app.get("/healthz")
def healthz():
    try:
        # единое имя переменной БД
        return jsonify({"ok": True, "db": DB_NAME})
    except Exception as e:
        # на случай, если где-то ещё осталось старое имя — покажем безопасно
        return jsonify({"ok": False, "error": str(e)}), 500


# === Patients: list, search, page ==================================================
@app.route("/api/patients/search", methods=["GET"])
def api_patients_search():
    """
    Короткий поиск для автокомплита (календарь/поисковая строка).
    Параметры: q, limit?
    """
    q = (request.args.get("q") or "").strip()
    try:
        limit = min(20, max(1, int(request.args.get("limit", 7))))
    except Exception:
        limit = 7

    if not q:
        return jsonify({"ok": True, "items": []})

    flt = {
        "$or": [
            {"full_name": {"$regex": re.escape(q), "$options": "i"}},
            {"phone": {"$regex": re.escape(q), "$options": "i"}},
        ]
    }
    cursor = db.patients.find(flt).sort([("full_name", 1)]).limit(limit)
    items = [
        {"id": str(x["_id"]), "name": x.get("full_name", ""), "phone": x.get("phone", "")}
        for x in cursor
    ]
    return jsonify({"ok": True, "items": items})


def ensure_patient_card_nos():
    cur = db.patients.find(
        {"$or": [{"card_no": {"$exists": False}}, {"card_no": None}]}, {"_id": 1}
    )
    count = 0
    for p in cur:
        seq = db.counters.find_one_and_update(
            {"_id": "patient_card_no"},
            {"$inc": {"seq": 1}},
            upsert=True,
            return_document=ReturnDocument.AFTER,
        )
        db.patients.update_one({"_id": p["_id"]}, {"$set": {"card_no": int(seq.get("seq", 1))}})
        count += 1
    print(f"[init] backfilled patient card_no: {count}")


@app.cli.command("backfill-card-nos")
def backfill_card_nos_cmd():
    """One-off пронумеровать пациентов без card_no."""
    with app.app_context():
        ensure_patient_card_nos()


# === BEGIN: repair-patient-names (robust) =====================================
@app.cli.command("repair-patient-names")
@click.option("--apply", is_flag=True, help="Сохранить изменения (по умолчанию только показать)")
@click.option("--limit", type=int, default=0, help="Ограничить кол-во записей (0 = все)")
def repair_patient_names(apply: bool, limit: int):
    """
    Чинит mojibake в full_name, например 'Ð�Ð²Ð°Ð½' -> 'Иван'.
    Логика:
      1) Проходим по всем пациентам (или limit).
      2) Пробуем name.encode('latin1').decode('utf-8').
      3) Применяем только если результат содержит кириллицу и отличается от исходного.
    """
    import re

    CYR = re.compile(r"[\u0400-\u04FF]")  # диапазон кириллицы

    scanned = 0
    fixed = 0

    cur = db.patients.find({}, {"full_name": 1})
    if limit and limit > 0:
        cur = cur.limit(int(limit))

    for p in cur:
        name = p.get("full_name") or ""
        if not isinstance(name, str) or not name:
            continue
        scanned += 1

        try:
            candidate = name.encode("latin1").decode("utf-8")
        except Exception:
            candidate = name

        # исправляем только если реально стало «по-русски» и строка изменилась
        if candidate != name and CYR.search(candidate):
            click.echo(f"{p['_id']}: {name!r} -> {candidate!r}")
            if apply:
                db.patients.update_one({"_id": p["_id"]}, {"$set": {"full_name": candidate}})
                fixed += 1

    click.echo(f"Scanned: {scanned}, Fixed: {fixed}")


# === END: repair-patient-names ===============================================

# ======= ЗАПУСК =======
if __name__ == "__main__":
    # На Windows отключаем перезагрузчик, чтобы не ловить WinError 10038 в Werkzeug
    app.run(debug=True, use_reloader=False)
~~~

=== END FILE: .\main.py ===

=== BEGIN FILE: .\routes\routes_finance.py ===

~~~python
# routes/routes_finance.py
from flask import Blueprint, jsonify, request
from pymongo import MongoClient
import os

bp_finance = Blueprint("finance", __name__)

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
client = MongoClient(MONGO_URI)
db = client["medplatforma"]
services = db["services"]

# Получить все услуги
@bp_finance.route("/services", methods=["GET"])
def get_services():
    data = list(services.find({}, {"_id": 0}))
    return jsonify(data)

# Добавить услугу (только из прайса)
@bp_finance.route("/services", methods=["POST"])
def add_service():
    payload = request.json
    if not payload.get("code") or not payload.get("name") or not payload.get("price"):
        return jsonify({"error": "code, name и price обязательны"}), 400
    
    existing = services.find_one({"code": payload["code"]})
    if existing:
        return jsonify({"error": "Услуга с таким code уже есть"}), 400

    services.insert_one(payload)
    return jsonify({"status": "ok"})
~~~

=== END FILE: .\routes\routes_finance.py ===

=== BEGIN FILE: .\templates\_layout.html ===

~~~html
<!doctype html>
<html lang="ru">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{% block title %}MedPlatforma{% endblock %}</title>
  <style>
    body{font-family:-apple-system,BlinkMacSystemFont,Segoe UI,Roboto,Helvetica,Arial,sans-serif;
         background:#f6f7fb;margin:0;color:#222}
    .topbar{background:#1b1f3b;color:#fff;padding:10px 14px;font-weight:600}
    .container{max-width:1200px;margin:0 auto;padding:14px}
    a{color:#2e6cff;text-decoration:none}
    a:hover{text-decoration:underline}
  </style>
  {% block head %}{% endblock %}
</head>
<body>
  <div class="topbar">MedPlatforma</div>
  <div class="container">
    {% block content %}{% endblock %}
  </div>
  {% block scripts %}{% endblock %}
</body>
</html>
~~~

=== END FILE: .\templates\_layout.html ===

=== BEGIN FILE: .\templates\404.html ===

~~~html
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <title>Страница не найдена</title>
</head>
<body>
    <h1>404 — Такой страницы нет</h1>
    <p>Возможно, вы ошиблись адресом.</p>
    <a href="{{ url_for('calendar_view') }}">На главную</a>
</body>
</html>
~~~

=== END FILE: .\templates\404.html ===

=== BEGIN FILE: .\templates\action_log.html ===

~~~html
{% extends "base.html" %}
{% block content %}
<h2>Журнал действий</h2>
<div class="card shadow" style="max-width:1250px;margin:32px auto 0 auto;padding:34px 24px;">
  <table class="action-log-table" style="width:100%;border-radius:20px;overflow:hidden;">
    <thead>
      <tr>
        <th>Дата/Время</th>
        <th>Пользователь</th>
        <th>Роль</th>
        <th>Действие</th>
        <th>Объект</th>
        <th>Комментарий</th>
      </tr>
    </thead>
    <tbody>
      {% for log in logs %}
      <tr>
        <td style="color:#888;">{{ log.time }}</td>
        <td>
          <img src="{{ log.avatar_url or '/static/avatars/staff_1.png' }}" class="avatar mini-avatar" style="width:38px;height:38px;vertical-align:middle;margin-right:10px;">
          {{ log.user }}
        </td>
        <td>
          <span class="badge bg-light text-primary">{{ log.role }}</span>
        </td>
        <td>
          {% if log.action == 'created' %}
            <span class="badge bg-light" style="color:#22c55e;"><b>Создание</b></span>
          {% elif log.action == 'edited' %}
            <span class="badge bg-light" style="color:#eab308;"><b>Изменение</b></span>
          {% elif log.action == 'deleted' %}
            <span class="badge bg-light" style="color:#ef4444;"><b>Удаление</b></span>
          {% else %}
            <span class="badge bg-light">{{ log.action|capitalize }}</span>
          {% endif %}
        </td>
        <td>{{ log.object }}</td>
        <td>{{ log.comment }}</td>
      </tr>
      {% endfor %}
    </tbody>
  </table>
</div>
{% endblock %}
~~~

=== END FILE: .\templates\action_log.html ===

=== BEGIN FILE: .\templates\add_doctor.html ===

~~~html
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <title>Добавить врача</title>
    <link href="https://fonts.googleapis.com/css?family=Montserrat:400,600&display=swap" rel="stylesheet">
    <style>
        body { font-family: 'Montserrat', sans-serif; background: #f7f8fa;}
        .form-card { width: 400px; margin: 40px auto; background: #fff; border-radius: 22px; box-shadow: 0 6px 32px rgba(20,40,80,.08); padding: 32px;}
        .form-label { font-size: 1rem; font-weight: 600; margin-bottom: 4px; display: block;}
        .form-input { width: 100%; border: 1px solid #ccd; border-radius: 8px; padding: 8px; margin-bottom: 14px; font-size: 1rem;}
        .submit-btn { background: #445be2; color: #fff; border: none; border-radius: 10px; padding: 10px 20px; font-weight: 600; cursor: pointer; transition: background 0.2s;}
        .submit-btn:hover { background: #2236a7;}
    </style>
</head>
<body>
    <form class="form-card" method="POST">
        <label class="form-label">ФИО</label>
        <input class="form-input" type="text" name="full_name" required>
        <label class="form-label">Специализация</label>
        <input class="form-input" type="text" name="specialization" required>
        <label class="form-label">E-mail</label>
        <input class="form-input" type="email" name="email">
        <label class="form-label">Телефон</label>
        <input class="form-input" type="text" name="phone">
        <label class="form-label">Ссылка на аватар (необязательно)</label>
        <input class="form-input" type="text" name="avatar_url">
        <button class="submit-btn" type="submit">Добавить врача</button>
    </form>
</body>
</html>
~~~

=== END FILE: .\templates\add_doctor.html ===

=== BEGIN FILE: .\templates\add_event.html ===

~~~html
{% extends "base.html" %}
{% block content %}
<h2 style="margin:8px 0 14px;">Добавить запись</h2>

<form method="post" style="display:grid;grid-template-columns:1fr 1fr;gap:16px;max-width:900px;">
  <!-- Врач -->
  <label>
    <div>Врач</div>
    <select name="doctor_id" required style="width:100%;padding:8px;border:1px solid #dbeafd;border-radius:8px;">
      <option value="">— выберите —</option>
      {% for d in doctors %}
        <option value="{{ d._id }}">{{ d.full_name }}</option>
      {% endfor %}
    </select>
  </label>

  <!-- Пациент -->
  <label>
    <div>Пациент</div>
    <select name="patient_id" required style="width:100%;padding:8px;border:1px solid #dbeafd;border-radius:8px;">
      <option value="">— выберите —</option>
      {% for p in patients %}
        <option value="{{ p._id }}">{{ p.full_name }}</option>
      {% endfor %}
    </select>
  </label>

  <!-- Услуга -->
  <label>
    <div>Услуга</div>
    <select id="service_id" name="service_id" required style="width:100%;padding:8px;border:1px solid #dbeafd;border-radius:8px;">
      <option value="">— выберите —</option>
      {% for s in services %}
        <option value="{{ s._id }}" data-dur="{{ s.duration_min or 30 }}">{{ s.name }}</option>
      {% endfor %}
    </select>
    <small id="service_hint" style="opacity:.7;"></small>
  </label>

  <!-- Кабинет -->
  <label>
    <div>Кабинет</div>
    <select id="room_id" name="room_id" required style="width:100%;padding:8px;border:1px solid #dbeafd;border-radius:8px;">
      <option value="">— выберите —</option>
      {% for r in rooms %}
        <option value="{{ r._id }}">{{ r.name }}</option>
      {% endfor %}
    </select>
    <small id="busy_hint" style="opacity:.75;"></small>
  </label>

  <!-- Начало -->
  <label>
    <div>Начало</div>
    <input id="start" type="datetime-local" name="start" required step="300"
           style="width:100%;padding:8px;border:1px solid #dbeafd;border-radius:8px;">
  </label>

  <!-- Конец (ставим автоматом, можно поправить) -->
  <label>
    <div>Конец</div>
    <input id="end" type="datetime-local" name="end" step="300"
           style="width:100%;padding:8px;border:1px solid #dbeafd;border-radius:8px;">
    <small style="opacity:.7;">Если не укажете, подставится длительность услуги.</small>
  </label>

  <!-- Статус -->
  <label>
    <div>Статус</div>
    <select name="status_key" style="width:100%;padding:8px;border:1px solid #dbeafd;border-radius:8px;">
      <option value="scheduled">Запланирован</option>
      <option value="arrived">Прибыл</option>
      <option value="done">Завершён</option>
      <option value="cancelled">Отменён</option>
    </select>
  </label>

  <!-- Комментарий -->
  <label style="grid-column:1/-1;">
    <div>Комментарий</div>
    <textarea name="comment" rows="3" style="width:100%;padding:8px;border:1px solid #dbeafd;border-radius:8px;"></textarea>
  </label>

  <div style="grid-column:1/-1;display:flex;gap:12px;">
    <button type="submit" class="btn-main" style="background:#1976d2;color:#fff;border-radius:8px;padding:10px 18px;">Создать</button>
    <a href="{{ url_for('calendar_view') }}" class="btn" style="padding:10px 14px;border:1px solid #dbeafd;border-radius:8px;">Отмена</a>
  </div>
</form>
{% endblock %}

{% block scripts %}
<script>
(function(){
  const serviceSel = document.getElementById('service_id');
  const startInp   = document.getElementById('start');
  const endInp     = document.getElementById('end');
  const hint       = document.getElementById('service_hint');
  const roomSel    = document.getElementById('room_id');
  const busyHint   = document.getElementById('busy_hint');

  function isoLocal(dt){
    // YYYY-MM-DDTHH:MM
    const pad = n => String(n).padStart(2,'0');
    return dt.getFullYear()+"-"+pad(dt.getMonth()+1)+"-"+pad(dt.getDate())+"T"+pad(dt.getHours())+":"+pad(dt.getMinutes());
  }

  function addMinutes(dt, m){ return new Date(dt.getTime() + m*60000); }

  function recalcEnd(){
    const sId = serviceSel.value;
    const sVal = startInp.value;
    if (!sId || !sVal) return;
    const durAttr = serviceSel.selectedOptions[0]?.getAttribute('data-dur');
    const dur = parseInt(durAttr || '30', 10);
    const start = new Date(sVal);
    const end = addMinutes(start, dur);
    endInp.value = isoLocal(end);
    hint.textContent = `Длительность: ${dur} мин. Конец: ${endInp.value.split('T')[1]}`;
  }

  serviceSel?.addEventListener('change', recalcEnd);
  startInp?.addEventListener('change', recalcEnd);

  // Подсказка занятых интервалов по кабинету и дате
  function refreshBusy(){
    const roomId = roomSel.value;
    const sVal = startInp.value;
    if (!roomId || !sVal) { busyHint.textContent = ''; return; }
    const date = sVal.split('T')[0];
    fetch(`/api/rooms/busy?room_id=${encodeURIComponent(roomId)}&date=${date}`)
      .then(r => r.json())
      .then(data => {
        if (!data.ok) { busyHint.textContent = 'Не удалось загрузить занятость'; return; }
        if (!data.items.length) { busyHint.textContent = 'Свободно весь день'; return; }
        const txt = data.items.map(i => `${i.start}–${i.end}`).join(', ');
        busyHint.textContent = `Занято: ${txt}`;
      })
      .catch(()=> busyHint.textContent = 'Ошибка сети');
  }

  roomSel?.addEventListener('change', refreshBusy);
  startInp?.addEventListener('change', refreshBusy);

})();
</script>
{% endblock %}
~~~

=== END FILE: .\templates\add_event.html ===

=== BEGIN FILE: .\templates\add_expense.html ===

~~~html
{% extends 'base.html' %}
{% block title %}Добавить расход{% endblock %}
{% block content %}
<div style="max-width:500px;margin:0 auto;background:#fff;border-radius:20px;box-shadow:0 6px 32px rgba(20,40,80,.08);padding:38px;">
    <h2>Добавить расход</h2>
    <form method="POST">
        <label>Дата:<br>
            <input type="date" name="date" required style="width:180px;margin-bottom:14px;">
        </label><br>
        <label>Категория:<br>
            <input type="text" name="category" required placeholder="Аренда / ЗП / Материалы и т.д." style="width:220px;margin-bottom:14px;">
        </label><br>
        <label>Сумма:<br>
            <input type="number" name="amount" required style="width:120px;margin-bottom:14px;">
        </label><br>
        <label>Комментарий:<br>
            <input type="text" name="comment" style="width:300px;margin-bottom:16px;">
        </label><br>
        <button type="submit" style="background:#445be2;color:#fff;border:none;border-radius:8px;padding:9px 19px;font-weight:700;cursor:pointer;">Добавить</button>
    </form>
</div>
{% endblock %}
~~~

=== END FILE: .\templates\add_expense.html ===

=== BEGIN FILE: .\templates\add_patient.html ===

~~~html
{% extends "base.html" %}
{% block content %}
<h2>Добавить пациента</h2>

<form method="post" style="background:#fff;border-radius:12px;box-shadow:0 1px 8px #e3eaf9b7;padding:16px;max-width:860px;">
  <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">
    <label>ФИО
      <input type="text" name="full_name" value="{{ form.full_name or '' }}" required>
    </label>
    <label>Дата рождения
      <input type="date" name="birthday" value="{{ form.birthday or '' }}">
    </label>

    <label>Пол
      <select name="gender">
        <option value="male"   {% if form.gender=='male' %}selected{% endif %}>Мужской</option>
        <option value="female" {% if form.gender=='female' %}selected{% endif %}>Женский</option>
        <option value="other"  {% if form.gender=='other' %}selected{% endif %}>Другое</option>
      </select>
    </label>
    <label>Аватар (путь)
      <input type="text" name="avatar" value="{{ form.avatar or '' }}" placeholder="/static/avatars/patients/p1.jpg">
    </label>

    <label>Телефон
      <input type="text" name="phone" value="{{ form.contacts.phone or '' }}">
    </label>
    <label>Email
      <input type="email" name="email" value="{{ form.contacts.email or '' }}">
    </label>

    <label>WhatsApp
      <input type="text" name="whatsapp" value="{{ form.contacts.whatsapp or '' }}">
    </label>
    <label>Telegram
      <input type="text" name="telegram" value="{{ form.contacts.telegram or '' }}" placeholder="@username">
    </label>

    <label>Город
      <input type="text" name="city" value="{{ form.address.city or '' }}">
    </label>
    <label>Улица/дом
      <input type="text" name="street" value="{{ form.address.street or '' }}">
    </label>
    <label>Индекс
      <input type="text" name="zip" value="{{ form.address.zip or '' }}">
    </label>

    <label style="grid-column:1/-1;">Заметки
      <textarea name="notes" rows="4">{{ form.notes or '' }}</textarea>
    </label>
  </div>

  <div style="margin-top:14px;display:flex;gap:10px;">
    <button type="submit" class="btn-main" style="background:#1976d2;color:#fff;padding:8px 14px;border-radius:8px;">Сохранить</button>
    <a href="{{ url_for('patients_list') }}">Отмена</a>
  </div>
</form>
{% endblock %}
~~~

=== END FILE: .\templates\add_patient.html ===

=== BEGIN FILE: .\templates\add_payment.html ===

~~~html
{% extends 'base.html' %}
{% block title %}Добавить оплату{% endblock %}
{% block content %}
<div style="max-width:450px; margin:0 auto; background:#fff; border-radius:20px; box-shadow:0 6px 32px rgba(20,40,80,.08); padding:38px 42px;">
    <h2 style="font-size:1.6rem; font-weight:700; margin-bottom:28px;">Добавить оплату</h2>
    <form method="POST">
        <div style="font-weight:600; margin-bottom:9px;">ФИО пациента:</div>
        <div style="margin-bottom:18px;">{{ patient.full_name }}</div>
        <div style="font-weight:600; margin-bottom:6px;">Сумма оплаты (₽):</div>
        <input name="amount" type="number" min="0" step="0.01" required style="width:100%; padding:10px; border-radius:8px; border:1px solid #ccd; margin-bottom:18px; font-size:1.1rem;">
        <div style="font-weight:600; margin-bottom:6px;">Комментарий (необязательно):</div>
        <textarea name="comment" rows="2" style="width:100%; padding:10px; border-radius:8px; border:1px solid #ccd; margin-bottom:18px; font-size:1.05rem;"></textarea>
        <button type="submit" style="background:#13b949; color:#fff; border:none; border-radius:10px; padding:11px 32px; font-weight:700; font-size:1.09rem; cursor:pointer;">Добавить оплату</button>
    </form>
</div>
{% endblock %}
~~~

=== END FILE: .\templates\add_payment.html ===

=== BEGIN FILE: .\templates\add_room.html ===

~~~html
{% extends "base.html" %}
{% block content %}
<h2>Добавить кабинет</h2>

<form method="post" style="background:#fff;border-radius:12px;box-shadow:0 1px 8px #e3eaf9b7;padding:16px;max-width:720px;">
  <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">
    <label>Название
      <input type="text" name="name" value="{{ form.name or '' }}" required>
    </label>

    <label>Тип
      <select name="type" required>
        {% for v,t in ROOM_TYPES %}
          <option value="{{ v }}" {% if form.type==v %}selected{% endif %}>{{ t }}</option>
        {% endfor %}
      </select>
    </label>

    <label>Статус
      <select name="status" required>
        {% for v,t in ROOM_STATUSES %}
          <option value="{{ v }}" {% if form.status==v %}selected{% endif %}>{{ t }}</option>
        {% endfor %}
      </select>
    </label>

    <label>Цвет
      <input type="color" name="color" value="{{ form.color or '#1abc9c' }}" style="height:42px;">
    </label>
  </div>

  <div style="margin-top:14px;display:flex;gap:10px;">
    <button type="submit" class="btn-main" style="background:#1976d2;color:#fff;padding:8px 14px;border-radius:8px;">Сохранить</button>
    <a href="{{ url_for('rooms_list') }}">Отмена</a>
  </div>
</form>
{% endblock %}
~~~

=== END FILE: .\templates\add_room.html ===

=== BEGIN FILE: .\templates\add_service.html ===

~~~html
{% extends "base.html" %}
{% block content %}
<h2>Добавить услугу</h2>

<form method="post" style="background:#fff;border-radius:12px;box-shadow:0 1px 8px #e3eaf9b7;padding:16px;max-width:720px;">
  <div style="display:grid;grid-template-columns:1fr 180px;gap:12px;">
    <label>Название
      <input type="text" name="name" value="{{ form.name or '' }}" required>
    </label>
    <label>Код
      <input type="text" name="code" value="{{ form.code or '' }}" placeholder="CONSULT / FILL ..." required>
    </label>

    <label>Цена, ₽
      <input type="number" name="price" value="{{ form.price or 0 }}" min="0" step="1">
    </label>
    <label>Длительность (мин)
      <input type="number" name="duration_min" value="{{ form.duration_min or 30 }}" min="5" step="5">
    </label>

    <label>Цвет
      <input type="color" name="color" value="{{ form.color or '#3498db' }}" style="height:42px;">
    </label>
    <label style="display:flex;align-items:center;gap:8px;margin-top:26px;">
      <input type="checkbox" name="is_active" {% if form.is_active %}checked{% endif %}> Активна
    </label>

    <label style="grid-column:1/-1;">Описание
      <textarea name="description" rows="4">{{ form.description or '' }}</textarea>
    </label>
  </div>

  <div style="margin-top:14px;display:flex;gap:10px;">
    <button type="submit" class="btn-main" style="background:#1976d2;color:#fff;padding:8px 14px;border-radius:8px;">Сохранить</button>
    <a href="{{ url_for('services_list') }}">Отмена</a>
  </div>
</form>
{% endblock %}
~~~

=== END FILE: .\templates\add_service.html ===

=== BEGIN FILE: .\templates\add_xray.html ===

~~~html
{% extends "base.html" %}
{% block content %}
<h2>Добавить рентген-снимок</h2>
<form method="post" enctype="multipart/form-data" class="card shadow p-4" style="max-width:440px;">
    <div class="mb-3">
        <label>Пациент:</label>
        <select name="patient_id" class="form-select" required>
            {% for p in patients %}
            <option value="{{ p._id }}">{{ p.full_name }}</option>
            {% endfor %}
        </select>
    </div>
    <div class="mb-3">
        <label>Врач:</label>
        <select name="doctor_id" class="form-select" required>
            {% for d in doctors %}
            <option value="{{ d._id }}">{{ d.full_name }}</option>
            {% endfor %}
        </select>
    </div>
    <div class="mb-3">
        <label>Тип снимка:</label>
        <select name="type" class="form-select">
            <option>Панорама</option>
            <option>Прицельный</option>
            <option>КТ</option>
        </select>
    </div>
    <div class="mb-3">
        <label>Файл снимка (JPG/PNG):</label>
        <input type="file" name="image" accept="image/*" class="form-control" required>
    </div>
    <div class="mb-3">
        <label>Краткое заключение:</label>
        <input type="text" name="comment" class="form-control">
    </div>
    <div class="mb-3">
        <label>Развёрнутое заключение:</label>
        <textarea name="report" class="form-control" rows="2"></textarea>
    </div>
    <button type="submit" class="btn btn-primary">Загрузить</button>
</form>
{% endblock %}
~~~

=== END FILE: .\templates\add_xray.html ===

=== BEGIN FILE: .\templates\add_ztl.html ===

~~~html
{% extends "base.html" %}
{% block content %}
<h2>Добавить работу в лабораторию (ZTL)</h2>
<form method="post" enctype="multipart/form-data" class="card shadow p-4" style="max-width:440px;">
    <div class="mb-3">
        <label>Пациент:</label>
        <select name="patient_id" class="form-select" required>
            {% for p in patients %}
            <option value="{{ p._id }}">{{ p.full_name }}</option>
            {% endfor %}
        </select>
    </div>
    <div class="mb-3">
        <label>Врач:</label>
        <select name="doctor_id" class="form-select" required>
            {% for d in doctors %}
            <option value="{{ d._id }}">{{ d.full_name }}</option>
            {% endfor %}
        </select>
    </div>
    <div class="mb-3">
        <label>Тип работы:</label>
        <select name="type" class="form-select">
            <option>Коронка</option>
            <option>Винир</option>
            <option>Брекеты</option>
            <option>Протез</option>
            <option>Каппа</option>
        </select>
    </div>
    <div class="mb-3">
        <label>Файл (фото, 3D, pdf):</label>
        <input type="file" name="file" accept="image/*,.pdf,.stl,.obj" class="form-control">
    </div>
    <div class="mb-3">
        <label>Дата заказа:</label>
        <input type="date" name="order_date" class="form-control" required value="{{ (now or '').split('T')[0] }}">
    </div>
    <div class="mb-3">
        <label>Срок исполнения:</label>
        <input type="date" name="due_date" class="form-control" required>
    </div>
    <div class="mb-3">
        <label>Статус:</label>
        <select name="status" class="form-select">
            <option>В работе</option>
            <option>Готово</option>
            <option>Выдано</option>
            <option>Ожидает оплаты</option>
        </select>
    </div>
    <div class="mb-3">
        <label>Комментарий:</label>
        <textarea name="comment" class="form-control" rows="2"></textarea>
    </div>
    <button type="submit" class="btn btn-primary">Добавить</button>
</form>
{% endblock %}
~~~

=== END FILE: .\templates\add_ztl.html ===

=== BEGIN FILE: .\templates\backup.html ===

~~~html
<h2>Бэкап данных (экспорт коллекций)</h2>
<ul>
  <li><a href="{{ url_for('backup_collection', collection='patients') }}">Скачать пациентов (CSV)</a></li>
  <li><a href="{{ url_for('backup_collection', collection='doctors') }}">Скачать врачей (CSV)</a></li>
  <li><a href="{{ url_for('backup_collection', collection='events') }}">Скачать события (CSV)</a></li>
  <li><a href="{{ url_for('backup_collection', collection='payments') }}">Скачать оплаты (CSV)</a></li>
  <li><a href="{{ url_for('backup_collection', collection='logs') }}">Скачать логи (CSV)</a></li>
</ul>
~~~

=== END FILE: .\templates\backup.html ===

=== BEGIN FILE: .\templates\base.html ===

~~~html
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <title>{% block title %}Medplatforma{% endblock %}</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link href="https://fonts.googleapis.com/css?family=Montserrat:400,600&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css">
    <link rel="stylesheet" href="{{ url_for('static', filename='style.css') }}">
    {% block head %}{% endblock %}
</head>
<body class="">
  <div class="layout">
    <aside class="sidebar">
      {% include 'sidebar.html' %}
    </aside>
    <div class="main-area">
      {% include 'topbar.html' %}
      <main class="content">
        {% block content %}{% endblock %}
      </main>
    </div>
  </div>

  {% block scripts %}
  <script>
    // Открытие меню профиля
    function toggleProfileMenu() {
      let menu = document.getElementById('profileMenu');
      menu.style.display = (menu.style.display === 'flex' ? 'none' : 'flex');
    }
    window.onclick = function(e) {
      let menu = document.getElementById('profileMenu');
      if (menu && e.target.closest('.profile-block') == null && e.target.closest('.profile-menu') == null) {
        menu.style.display = 'none';
      }
    };

    // --- Переключатель темы ---
    document.addEventListener("DOMContentLoaded", function() {
      const themeBtn = document.getElementById('themeToggleBtn');
      if (themeBtn) {
        themeBtn.onclick = function() {
          const sun = this.querySelector('.theme-sun');
          const moon = this.querySelector('.theme-moon');
          const body = document.body;
          if (sun && sun.style.display !== 'none') {
            sun.style.display = 'none';
            moon.style.display = 'inline';
            body.classList.add('dark-theme');
          } else {
            if (sun) sun.style.display = 'inline';
            if (moon) moon.style.display = 'none';
            body.classList.remove('dark-theme');
          }
        };
      }
    });
    // Можно добавить сохранение выбора темы в localStorage, если надо.
  </script>
  {% endblock %}
  <script>
function toggleProfileMenu() {
  let menu = document.getElementById('profileMenu');
  menu.style.display = (menu.style.display === 'flex' ? 'none' : 'flex');
}
window.onclick = function(e) {
  let menu = document.getElementById('profileMenu');
  if (menu && e.target.closest('.profile-block') == null && e.target.closest('.profile-menu') == null) {
    menu.style.display = 'none';
  }
}

// Переключение темы
document.addEventListener('DOMContentLoaded', function() {
  const themeBtn = document.getElementById('themeToggleBtn');
  const sunIcon = document.querySelector('.theme-sun');
  const moonIcon = document.querySelector('.theme-moon');
  // Сохраняем тему между сессиями
  if (localStorage.getItem('theme') === 'dark') {
    document.body.classList.add('dark-theme');
    sunIcon.style.display = 'none';
    moonIcon.style.display = 'inline';
  }
  themeBtn.onclick = function() {
    if (document.body.classList.contains('dark-theme')) {
      document.body.classList.remove('dark-theme');
      sunIcon.style.display = 'inline';
      moonIcon.style.display = 'none';
      localStorage.setItem('theme', 'light');
    } else {
      document.body.classList.add('dark-theme');
      sunIcon.style.display = 'none';
      moonIcon.style.display = 'inline';
      localStorage.setItem('theme', 'dark');
    }
  }
});
</script>
</body>
</html>
~~~

=== END FILE: .\templates\base.html ===

=== BEGIN FILE: .\templates\cabinet_card.html ===

~~~html
{% extends "base.html" %}

{% block content %}
<h2>События в {{ cabinet }}</h2>
<ul>
  {% for e in events %}
    <li>
      {{ e.start }} — {{ e.title or '' }}
      <!-- можно добавить больше инфы: врач, пациент, статус -->
    </li>
  {% endfor %}
</ul>
<a href="/calendar" class="btn-main">← Назад к календарю</a>
{% endblock %}
~~~

=== END FILE: .\templates\cabinet_card.html ===

=== BEGIN FILE: .\templates\calendar.backup.html ===

~~~html
{% extends "base.html" %} {% block content %}

<!-- Метрики и действия -->
<div
  style="
    display: flex;
    align-items: center;
    gap: 22px;
    padding: 6px 0 6px 12px;
    background: #fff;
    border-radius: 14px;
    box-shadow: 0 1px 8px #e3eaf9b7;
    margin-bottom: 10px;
  "
>
  <span title="Всего кабинетов">
    <i class="fa-solid fa-house-chimney-medical" style="color: #467fe3"></i>
    <b>{{ metrics.total_rooms }}</b>
  </span>
  <span title="Свободные">
    <i class="fa-solid fa-circle-check" style="color: #21ba45"></i>
    <b>{{ metrics.free_rooms }}</b>
  </span>
  <span style="margin-left: auto; display: flex; gap: 12px">
    <a
      href="{{ url_for('add_event') }}"
      class="btn-main"
      style="
        background: #1976d2;
        color: #fff;
        font-weight: 600;
        border-radius: 8px;
        padding: 8px 22px;
        font-size: 1.07em;
        display: flex;
        align-items: center;
        gap: 8px;
        text-decoration: none;
      "
    >
      <i class="fa-solid fa-plus"></i> Добавить запись
    </a>
    <a
      href="{{ url_for('export_calendar') }}"
      class="btn-main btn-export"
      style="
        background: #fff;
        color: #3185cb;
        border: 1.5px solid #dbeafd;
        font-weight: 600;
        border-radius: 8px;
        padding: 8px 18px;
        font-size: 1.07em;
        display: flex;
        align-items: center;
        gap: 8px;
        text-decoration: none;
      "
    >
      <i class="fa-solid fa-file-arrow-down"></i> Выгрузка
    </a>
  </span>
</div>

<!-- Кабинеты и их статус -->
<div
  id="roomsBar"
  style="display: flex; gap: 36px; margin: 14px 0 12px 8px; flex-wrap: wrap"
>
  {% for cab in cabinets %} {% set info = room_info.get(cab) if room_info else
  None %}
  <span
    data-room-name="{{ cab }}"
    style="font-size: 1.12em; font-weight: 600; cursor: default"
  >
    {{ cab }} —
    <b
      class="room-status-text"
      style="color:{{ info.color if info else 'inherit' }}"
    >
      {{ info.text if info else '—' }}
    </b>
    <span
      class="room-next"
      style="opacity: 0.7; font-weight: 500; margin-left: 8px"
    >
      {% if info and info.state == 'available' and info.next %} {% set t =
      info.next.start.split('T')[1] if info.next.start else '' %} Ближайший: {{
      t }} {% if info.next.in_minutes is not none %} (через {% if
      info.next.in_minutes < 0 %}0 мин {% elif info.next.in_minutes < 60 %}{{
      info.next.in_minutes }} мин {% else %}{{ (info.next.in_minutes // 60)|int
      }} ч {{ (info.next.in_minutes % 60)|int }} мин {% endif %} ) {% endif %}
      {% if info.next.service or info.next.patient %} • {{ info.next.service
      }}{% if info.next.service and info.next.patient %} — {% endif %}{{
      info.next.patient }} {% endif %} {% endif %}
    </span>
  </span>
  {% endfor %}
</div>

<!-- Легенда/фильтры -->
<div
  style="
    display: flex;
    gap: 30px;
    align-items: center;
    font-size: 1.01em;
    margin-bottom: 12px;
    margin-left: 8px;
  "
>
  <span
    ><span
      style="
        background: #a2c6fa;
        border: 1.5px solid #dde7f7;
        width: 18px;
        height: 18px;
        display: inline-block;
        border-radius: 4px;
        margin-right: 6px;
      "
    ></span
    >Первичный</span
  >
  <span
    ><span
      style="
        background: #fbc7c0;
        border: 1.5px solid #fde7e7;
        width: 18px;
        height: 18px;
        display: inline-block;
        border-radius: 4px;
        margin-right: 6px;
      "
    ></span
    >Отказ</span
  >
  <span
    ><span
      style="
        background: #fde8a5;
        border: 1.5px solid #f7e9c5;
        width: 18px;
        height: 18px;
        display: inline-block;
        border-radius: 4px;
        margin-right: 6px;
      "
    ></span
    >Повторный</span
  >
  <span
    ><span
      style="
        background: #b4f0c0;
        border: 1.5px solid #cefad5;
        width: 18px;
        height: 18px;
        display: inline-block;
        border-radius: 4px;
        margin-right: 6px;
      "
    ></span
    >Оплачен</span
  >
</div>

<div
  class="calendar-filters"
  style="display: flex; gap: 12px; align-items: center; margin-bottom: 18px"
>
  <select id="doctorFilter" class="filter-select">
    <option value="">Все врачи</option>
    {% for doc in doctors %}
    <option value="{{ doc._id }}">{{ doc.full_name }}</option>
    {% endfor %}
  </select>

  <div style="position: relative">
    <input
      type="text"
      id="patientSearch"
      class="filter-input"
      placeholder="Поиск пациента..."
      style="
        padding: 7px 18px;
        border-radius: 8px;
        border: 1px solid #dde7f7;
        min-width: 180px;
      "
    />
    <ul
      id="patientSearchList"
      class="search-list"
      style="
        display: none;
        position: absolute;
        z-index: 1000;
        background: #fff;
        border-radius: 10px;
        box-shadow: 0 2px 12px #eee;
        margin: 0;
        padding: 0;
        list-style: none;
        max-height: 250px;
        overflow-y: auto;
        left: 0;
        top: 36px;
        width: 100%;
      "
    ></ul>
  </div>

  <select id="serviceFilter" class="filter-select">
    <option value="">Все услуги</option>
  </select>

  <select id="cabinetFilter" class="filter-select">
    <option value="">Все кабинеты</option>
    {% for cab in cabinets %}
    <option value="{{ cab }}">{{ cab }}</option>
    {% endfor %}
  </select>

  <button id="resetFilters" style="margin-left: 10px">Сбросить</button>
</div>

<!-- Календарь -->
<div
  id="calendar"
  style="
    background: #fff;
    border-radius: 12px;
    box-shadow: 0 1px 8px #e3eaf9b7;
    padding: 8px;
    min-height: 72vh;
  "
></div>

<!-- Модалка -->
<div
  id="quickModal"
  style="
    display: none;
    position: fixed;
    inset: 0;
    background: rgba(0, 0, 0, 0.35);
    z-index: 9999;
  "
>
  <div
    style="
      background: #fff;
      max-width: 680px;
      margin: 7vh auto;
      padding: 18px;
      border-radius: 12px;
      box-shadow: 0 8px 28px rgba(0, 0, 0, 0.08);
    "
  >
    <div
      style="display: flex; align-items: center; gap: 8px; margin-bottom: 12px"
    >
      <h3 style="margin: 0; flex: 1">Редактировать запись</h3>
      <button
        id="qmClose"
        type="button"
        style="
          border: none;
          background: #eee;
          border-radius: 8px;
          padding: 6px 10px;
          cursor: pointer;
        "
      >
        ×
      </button>
    </div>

    <form
      id="qmForm"
      style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px"
    >
      <input type="hidden" id="qm_id" />

      <label
        >Врач
        <select
          id="qm_doctor"
          class="filter-select"
          required
          style="width: 100%"
        ></select>
      </label>

      <label
        >Пациент
        <div style="display: flex; gap: 8px; align-items: center; width: 100%">
          <select
            id="qm_patient"
            class="filter-select"
            required
            style="width: 100%"
          ></select>
        <!-- ==== CONTACT BAR (над календарём) ==== -->
        <div class="btn-group" role="group" aria-label="Контакты пациента">
          <button type="button" class="btn btn-light" title="Позвонить"
                  onclick="mpOpenContact('tel')">📞</button>
          <button type="button" class="btn btn-light" title="WhatsApp"
                  onclick="mpOpenContact('wa')">🟢</button>
          <button type="button" class="btn btn-light" title="Telegram"
                  onclick="mpOpenContact('tg')">✈️</button>
          <button type="button" class="btn btn-light" title="E-mail"
                  onclick="mpOpenContact('mail')">✉️</button>
          <button type="button" class="btn btn-light" title="Max"
                  onclick="mpOpenContact('max')">Ⓜ️</button>
         </div>
<!-- ======================================= -->

          <button
            type="button"
            id="qm_patient_add"
            class="btn"
            style="white-space: nowrap"
          >
            + Новый
          </button>
        </div>

        <!-- инлайн-форма создания пациента -->
        <div
          id="qm_patient_new"
          style="display: none; margin-top: 8px; width: 100%"
        >
          <div class="qm-patient-grid">
            <input
              id="qm_new_full_name"
              type="text"
              placeholder="ФИО полностью"
              autocomplete="name"
            />
            <input
              id="qm_new_phone"
              type="tel"
              inputmode="tel"
              pattern="[\+\d\s\-\(\)]{6,}"
              title="+7 999 123-45-67"
              placeholder="+7 999 123-45-67"
            />
            <input id="qm_new_birth" type="date" placeholder="Дата рождения" />
            <div class="qm-patient-actions">
              <button
                type="button"
                id="qm_patient_save"
                class="btn btn-primary"
              >
                Создать
              </button>
              <button type="button" id="qm_patient_cancel" class="btn">
                Отмена
              </button>
            </div>
          </div>
        </div>
        <!-- Панель быстрых контактов -->
        <div
          id="qm_contact_bar"
          style="
            display: flex;
            gap: 10px;
            align-items: center;
            margin: 6px 0 2px 0;
          "
        >
          <a
            id="cb_tel"
            class="btn"
            target="_blank"
            rel="noopener"
            title="Позвонить"
            style="padding: 4px 8px"
            >📞 Tel</a
          >
          <a
            id="cb_wa"
            class="btn"
            target="_blank"
            rel="noopener"
            title="WhatsApp"
            style="padding: 4px 8px"
            >🟢 WA</a
          >
          <a
            id="cb_tg"
            class="btn"
            target="_blank"
            rel="noopener"
            title="Telegram"
            style="padding: 4px 8px"
            >🔵 TG</a
          >
          <a
            id="cb_max"
            class="btn"
            target="_blank"
            rel="noopener"
            title="Max"
            style="padding: 4px 8px"
            >🟣 Max</a
          >
          <a
            id="cb_email"
            class="btn"
            target="_blank"
            rel="noopener"
            title="Email"
            style="padding: 4px 8px"
            >✉️ Mail</a
          >
          <small id="cb_hint" style="opacity: 0.7; margin-left: 6px"></small>
        </div>
      </label>
      <label
        >Услуга
        <select
          id="qm_service"
          class="filter-select"
          required
          style="width: 100%"
        ></select>
        <small id="qm_service_hint" style="opacity: 0.7"></small>
      </label>

      <label
        >Кабинет
        <select
          id="qm_room"
          class="filter-select"
          required
          style="width: 100%"
        ></select>
      </label>

      <label
        >Начало
        <input
          type="datetime-local"
          id="qm_start"
          required
          step="300"
          style="width: 100%"
        />
      </label>

      <label
        >Окончание
        <input
          type="datetime-local"
          id="qm_end"
          step="300"
          style="width: 100%"
        />
      </label>

      <label
        >Статус
        <select
          id="qm_status"
          class="filter-select"
          required
          style="width: 100%"
        >
          <option value="scheduled">Запланирован</option>
          <option value="arrived">Прибыл</option>
          <option value="done">Завершён</option>
          <option value="cancelled">Отменён</option>
        </select>
      </label>

      <label style="grid-column: 1 / -1"
        >Комментарий
        <textarea id="qm_comment" rows="3" style="width: 100%"></textarea>
      </label>

      <div
        style="
          grid-column: 1/-1;
          display: flex;
          gap: 8px;
          align-items: center;
          margin-top: -4px;
        "
      >
        <button
          type="button"
          class="btn"
          id="btn_plus_15"
          style="
            border: 1px solid #dbeafd;
            border-radius: 8px;
            padding: 6px 10px;
          "
        >
          +15 мин
        </button>
        <button
          type="button"
          class="btn"
          id="btn_plus_30"
          style="
            border: 1px solid #dbeafd;
            border-radius: 8px;
            padding: 6px 10px;
          "
        >
          +30 мин
        </button>
        <button
          type="button"
          class="btn"
          id="btn_plus_60"
          style="
            border: 1px solid #dbeafd;
            border-radius: 8px;
            padding: 6px 10px;
          "
        >
          +60 мин
        </button>
        <span style="opacity: 0.6; margin: 0 6px">|</span>
        <button
          type="button"
          class="btn"
          id="btn_move_tomorrow"
          style="
            border: 1px solid #dbeafd;
            border-radius: 8px;
            padding: 6px 10px;
          "
        >
          На завтра (то же время)
        </button>
        <span style="opacity: 0.6; margin: 0 6px">|</span>
        <button
          type="button"
          class="btn"
          id="btn_first_free"
          style="
            border: 1px solid #dbeafd;
            border-radius: 8px;
            padding: 6px 10px;
          "
        >
          Первый свободный слот (кабинет)
        </button>
      </div>
      <small
        id="qm_warn"
        style="grid-column: 1/-1; color: #b45309; display: none"
        >Предупреждение</small
      >

      <div
        style="
          grid-column: 1/-1;
          display: flex;
          justify-content: flex-end;
          gap: 8px;
        "
      >
        <button
          type="button"
          id="qmDelete"
          class="btn"
          style="background: #fee2e2; border: 1px solid #fecaca"
        >
          Удалить
        </button>
        <button type="submit" class="btn btn-primary">Сохранить</button>
      </div>
    </form>
  </div>
</div>

<!-- Toasts -->
<div
  id="toastStack"
  style="
    position: fixed;
    right: 16px;
    top: 16px;
    z-index: 10000;
    display: flex;
    flex-direction: column;
    gap: 8px;
  "
></div>

{% endblock %} {% block scripts %}
<link
  rel="stylesheet"
  href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css"
/>
<link
  href="https://cdn.jsdelivr.net/npm/fullcalendar@6.1.11/index.global.min.css"
  rel="stylesheet"
/>
<script src="https://cdn.jsdelivr.net/npm/fullcalendar@6.1.11/index.global.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/fullcalendar@6.1.11/locales-all.global.min.js"></script>

<style>
  /* форма нового пациента — стабильно, без «вылазов» */
  #quickModal .qm-patient-grid {
    display: grid;
    grid-template-columns: 1fr;
    gap: 8px;
    align-items: center;
  }
  #quickModal .qm-patient-grid input {
    width: 100%;
    height: 36px;
    padding: 8px 10px;
    border: 1px solid #dbeafd;
    border-radius: 8px;
    box-sizing: border-box;
  }
  #quickModal .qm-patient-grid input:focus {
    outline: none;
    border-color: #a5c5ff;
    box-shadow: 0 0 0 3px rgba(73, 133, 255, 0.12);
  }
  #quickModal .qm-patient-actions {
    display: flex;
    gap: 8px;
    justify-content: flex-start;
  }
  @media (min-width: 740px) {
    #quickModal .qm-patient-grid {
      grid-template-columns: 1fr 1fr;
    }
    #quickModal .qm-patient-grid > :first-child {
      grid-column: 1 / -1;
    } /* ФИО */
    #quickModal .qm-patient-actions {
      grid-column: 1 / -1;
    }
  }
  @media (min-width: 900px) {
    #quickModal .qm-patient-grid {
      grid-template-columns: 1fr 180px;
    }
  }
</style>

<script>
  // --- простой toast ---
  function showToast(msg, type = "info", ms = 2200) {
    const stack = document.getElementById("toastStack");
    if (!stack) {
      alert(msg);
      return;
    }
    const el = document.createElement("div");
    el.textContent = msg;
    el.style.cssText = `
      background:${
        type === "error" ? "#fee2e2" : type === "ok" ? "#e6ffed" : "#eef2ff"
      };
      color:${
        type === "error" ? "#991b1b" : type === "ok" ? "#065f46" : "#1e40af"
      };
      border:1px solid ${
        type === "error" ? "#fecaca" : type === "ok" ? "#bbf7d0" : "#c7d2fe"
      };
      box-shadow:0 6px 18px rgba(0,0,0,.08);padding:10px 14px;border-radius:10px;font-weight:600;max-width:420px`;
    stack.appendChild(el);
    setTimeout(() => {
      el.style.transition = "opacity .25s";
      el.style.opacity = "0";
      setTimeout(() => el.remove(), 260);
    }, ms);
  }
</script>

<script>
  document.addEventListener("DOMContentLoaded", () => {
    // ---------- helpers ----------
    const $ = (s) => document.querySelector(s);
    const addMin = (d, m) => new Date(d.getTime() + m * 60000);
    const pad2 = (n) => String(n).padStart(2, "0");
    const fmtISO = (d) =>
      `${d.getFullYear()}-${pad2(d.getMonth() + 1)}-${pad2(d.getDate())}T${pad2(
        d.getHours()
      )}:${pad2(d.getMinutes())}`;

    // кэш словарей
    window.__DICT_CACHE__ = window.__DICT_CACHE__ || null;

    // Универсальная заливка options
    function fillOptions(selectEl, items, selectedId = "") {
      if (!selectEl) return;
      const toId = (x) => x._id ?? x.id ?? "";
      const toName = (x) => x.full_name ?? x.name ?? "";
      const html = (items || [])
        .map((x) => {
          const id = toId(x),
            name = toName(x);
          return `<option value="${id}">${name}</option>`;
        })
        .join("");
      selectEl.innerHTML = html;
      if (selectedId) selectEl.value = selectedId;
      if (!selectEl.value || selectEl.value === "undefined") {
        const first = selectEl.querySelector("option")?.value || "";
        selectEl.value = first;
      }
    }

    // Загрузка словарей (нормализация)
    async function loadDictsOnce() {
      if (window.__DICT_CACHE__) return window.__DICT_CACHE__;
      const r = await fetch("/api/dicts");
      const raw = await r.json();
      if (!raw?.ok) throw new Error("dicts load failed");

      const norm = (arr) =>
        (arr || []).map((x) => ({
          id: x._id ?? x.id ?? "",
          name: x.full_name ?? x.name ?? "",
          duration_min: x.duration_min,
        }));
      const data = {
        ok: true,
        doctors: norm(raw.doctors),
        patients: norm(raw.patients),
        rooms: norm(raw.rooms),
        services: norm(raw.services).map((s) => ({
          ...s,
          duration_min: s.duration_min ?? 30,
        })),
      };
      window.__DICT_CACHE__ = data;
      return data;
    }

    // ---------- элементы модалки ----------
    const qm = {
      modal: $("#quickModal"),
      close: $("#qmClose"),
      form: $("#qmForm"),
      id: $("#qm_id"),
      doctor: $("#qm_doctor"),
      patient: $("#qm_patient"),
      service: $("#qm_service"),
      serviceHint: $("#qm_service_hint"),
      room: $("#qm_room"),
      start: $("#qm_start"),
      end: $("#qm_end"),
      status: $("#qm_status"),
      comment: $("#qm_comment"),
      warn: $("#qm_warn"),
      btnDel: $("#qmDelete"),
      btnPlus15: document.querySelector("#quickModal #btn_plus_15"),
      btnPlus30: document.querySelector("#quickModal #btn_plus_30"),
      btnPlus60: document.querySelector("#quickModal #btn_plus_60"),
      btnTomorrow: document.querySelector("#quickModal #btn_move_tomorrow"),
      btnFirstFree: document.querySelector("#quickModal #btn_first_free"),

      // блок «Новый пациент»
      patientAddBtn: document.getElementById("qm_patient_add"),
      patientNewRow: document.getElementById("qm_patient_new"),
      newFullName: document.getElementById("qm_new_full_name"),
      newPhone: document.getElementById("qm_new_phone"),
      newBirth: document.getElementById("qm_new_birth"),
      patientSaveBtn: document.getElementById("qm_patient_save"),
      patientCancelBtn: document.getElementById("qm_patient_cancel"),
    };

<script>
// --- contacts bar (Tel/WA/TG/Max/Mail) ---------------------------------
function setDisabledAnchor(a, disabled) {
  if (!a) return;
  if (disabled) {
    a.setAttribute("aria-disabled", "true");
    a.style.opacity = ".5";
    a.style.pointerEvents = "none";
    a.removeAttribute("href");
  } else {
    a.removeAttribute("aria-disabled");
    a.style.opacity = "1";
    a.style.pointerEvents = "auto";
  }
}
function onlyDigits(s){ return String(s||"").replace(/\D+/g,""); }

async function fillContactBar(patientId) {
  const tel = document.getElementById("cb_tel");
  const wa  = document.getElementById("cb_wa");
  const tg  = document.getElementById("cb_tg");
  const mx  = document.getElementById("cb_max");
  const em  = document.getElementById("cb_email");
  const hint= document.getElementById("cb_hint");

  [tel,wa,tg,mx,em].forEach(a => setDisabledAnchor(a, true));
  if (hint) hint.textContent = "";
  if (!patientId) return;

  try {
    const r = await fetch(`/api/patients/${encodeURIComponent(patientId)}/contacts`);
    const data = await r.json();
    if (!r.ok || !data.ok) return;

    const c = data.contacts || {};
    const phonePlus = (c.phone || "").trim();
    const phone     = onlyDigits(phonePlus);
    const waNum     = onlyDigits(c.whatsapp || c.phone || "");
    const mail      = (c.email || "").trim();
    const tgHandle  = (c.telegram || "").replace(/^@/, "").trim();

    if (phonePlus) { tel.href = `tel:${phonePlus}`; setDisabledAnchor(tel,false); }
    if (waNum)     { wa.href  = `https://wa.me/${waNum}`; setDisabledAnchor(wa,false); }
    if (tgHandle)  { tg.href  = `https://t.me/${tgHandle}`; setDisabledAnchor(tg,false); }
    else if (phone){ tg.href  = `https://t.me/+${phone}`; setDisabledAnchor(tg,false); }

    // Max: аналог WhatsApp — открываем веб-клиент; при появлении deep-link подменим тут
    mx.href = `https://web.max.ru/`;
    setDisabledAnchor(mx,false);

    if (mail) { em.href = `mailto:${encodeURIComponent(mail)}`; setDisabledAnchor(em,false); }

    if (hint) {
      const parts = [];
      if (phonePlus) parts.push(phonePlus);
      if (mail) parts.push(mail);
      hint.textContent = parts.join(" • ");
    }
  } catch {}
}
// при смене выбранного пациента — обновить панель
qm.patient?.addEventListener("change", () => fillContactBar(qm.patient.value));
</script>

    // --- создание пациента из модалки ---
    qm.patientAddBtn?.addEventListener("click", () => {
      qm.patientNewRow.style.display = "block";
      qm.newFullName?.focus();
    });
    qm.patientCancelBtn?.addEventListener("click", () => {
      qm.patientNewRow.style.display = "none";
      if (qm.newFullName) qm.newFullName.value = "";
      if (qm.newPhone) qm.newPhone.value = "";
      if (qm.newBirth) qm.newBirth.value = "";
    });
    qm.patientSaveBtn?.addEventListener("click", async () => {
      const full_name = (qm.newFullName?.value || "").trim();
      const phone = (qm.newPhone?.value || "").trim();
      const birth_date = (qm.newBirth?.value || "").trim();
      if (!full_name) {
        showToast("Укажи ФИО пациента", "error");
        return;
      }
      try {
        const r = await fetch("/api/patients", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ full_name, phone, birth_date }),
        });
        const data = await r.json().catch(() => ({}));
        if (!r.ok || !data.ok) {
          showToast(
            data?.error || `Ошибка создания (HTTP ${r.status})`,
            "error"
          );
          return;
        }
        const opt = document.createElement("option");
        opt.value = data.id;
        opt.textContent = data.full_name || full_name;
        qm.patient?.appendChild(opt);
        qm.patient.value = data.id;
        qm.newFullName.value = "";
        qm.newPhone.value = "";
        qm.newBirth.value = "";
        qm.patientNewRow.style.display = "none";
        if (window.__DICT_CACHE__) {
          window.__DICT_CACHE__.patients.unshift({
            id: data.id,
            name: data.full_name || full_name,
          });
        }
        showToast("Пациент создан", "ok");
      } catch {
        showToast("Сеть недоступна", "error");
      }
    });

    function isValidSelectValue(v) {
      return v && v !== "undefined" && v !== "null";
    }
    function updateFirstFreeBtnState() {
      const enable =
        isValidSelectValue(qm.room?.value) &&
        isValidSelectValue(qm.service?.value) &&
        !!qm.start?.value;
      if (qm.btnFirstFree) {
        qm.btnFirstFree.disabled = !enable;
        qm.btnFirstFree.style.opacity = enable ? "1" : "0.6";
        qm.btnFirstFree.style.pointerEvents = enable ? "auto" : "none";
      }
    }
    [qm.room, qm.service, qm.start].forEach((el) =>
      el?.addEventListener("change", updateFirstFreeBtnState)
    );

    const qmTitle = document.querySelector("#quickModal h3");
    const qmDeleteBtn = document.getElementById("qmDelete");
    function setModalMode(mode) {
      if (!qmTitle) return;
      if (mode === "create") {
        qmTitle.textContent = "Новая запись";
        qmDeleteBtn?.setAttribute("disabled", "disabled");
        qmDeleteBtn?.classList.add("disabled");
      } else {
        qmTitle.textContent = "Редактировать запись";
        qmDeleteBtn?.removeAttribute("disabled");
        qmDeleteBtn?.classList.remove("disabled");
      }
    }
    function openModal() {
      if (qm.modal) qm.modal.style.display = "block";
    }
    function closeModal() {
      if (qm.modal) qm.modal.style.display = "none";
    }
    qm.close?.addEventListener("click", closeModal);
    window.addEventListener("keydown", (e) => {
      if (e.key === "Escape") closeModal();
    });

    // время
    function setStartEnd(ns, ne) {
      if (qm.start) qm.start.value = fmtISO(ns);
      if (qm.end) qm.end.value = fmtISO(ne);
    }
    function shiftAppointment(minutes) {
      if (!qm.start?.value) return;
      const s = new Date(qm.start.value);
      const e = qm.end?.value ? new Date(qm.end.value) : s;
      const dur = Math.max(5, Math.round((e - s) / 60000));
      const ns = addMin(s, minutes),
        ne = addMin(ns, dur);
      setStartEnd(ns, ne);
    }
    qm.btnPlus15?.addEventListener("click", () => shiftAppointment(15));
    qm.btnPlus30?.addEventListener("click", () => shiftAppointment(30));
    qm.btnPlus60?.addEventListener("click", () => shiftAppointment(60));
    qm.btnTomorrow?.addEventListener("click", () => {
      if (!qm.start?.value) return;
      const s = new Date(qm.start.value);
      const e = qm.end?.value ? new Date(qm.end.value) : s;
      const dur = Math.max(5, Math.round((e - s) / 60000));
      s.setDate(s.getDate() + 1);
      setStartEnd(s, addMin(s, dur));
    });

    // первый свободный слот в кабинете
    async function moveToFirstFreeInRoom() {
      const roomId = qm.room?.value,
        sid = qm.service?.value;
      if (
        !isValidSelectValue(roomId) ||
        !isValidSelectValue(sid) ||
        !qm.start?.value
      ) {
        showToast("Выбери кабинет, услугу и время начала", "error");
        updateFirstFreeBtnState();
        return;
      }
      const d = await loadDictsOnce();
      const sRec = d.services.find((x) => x.id === sid);
      const dur = parseInt(sRec?.duration_min ?? 30, 10);

      let cursor = new Date(qm.start.value);
      const limit = new Date();
      limit.setDate(limit.getDate() + 7);

      while (cursor < limit) {
        const day = `${cursor.getFullYear()}-${String(
          cursor.getMonth() + 1
        ).padStart(2, "0")}-${String(cursor.getDate()).padStart(2, "0")}`;
        const resp = await fetch(
          `/api/rooms/busy?room_id=${encodeURIComponent(roomId)}&date=${day}`
        );
        if (!resp.ok) {
          showToast("Не удалось проверить занятость кабинета", "error");
          return;
        }
        const data = await resp.json();
        if (!data.ok) {
          showToast("Не удалось проверить занятость кабинета", "error");
          return;
        }

        const busy = (data.items || [])
          .map((i) => {
            const [sh, sm] = i.start.split(":").map(Number),
              [eh, em] = i.end.split(":").map(Number);
            return { s: sh * 60 + sm, e: eh * 60 + em };
          })
          .sort((a, b) => a.s - b.s);

        const st = cursor.getHours() * 60 + cursor.getMinutes(),
          en = st + dur;
        const overlap = busy.some((b) => !(en <= b.s || st >= b.e));
        if (!overlap) {
          setStartEnd(cursor, addMin(cursor, dur));
          return;
        }
        cursor = addMin(cursor, 5);
      }
      showToast("Не найден свободный слот в ближайшие 7 дней", "error");
    }
    qm.btnFirstFree?.addEventListener("click", moveToFirstFreeInRoom);

    // длительность/подсказка
    async function recalcEndByService() {
      if (!qm.service?.value || !qm.start?.value) return;
      const d = await loadDictsOnce();
      const srv = d.services.find((s) => s.id === qm.service.value);
      const dur = parseInt(srv?.duration_min ?? 30, 10);
      const s = new Date(qm.start.value),
        e = addMin(s, isFinite(dur) ? dur : 30);
      if (qm.end) qm.end.value = fmtISO(e);
      if (qm.serviceHint)
        qm.serviceHint.textContent = `Длительность услуги: ${
          isFinite(dur) ? dur : 30
        } мин.`;
    }

    // мягкая проверка графика врача
    async function checkDoctorWorking() {
      const start = qm.start?.value;
      if (!qm.doctor?.value || !start) {
        qm.warn && (qm.warn.style.display = "none");
        return;
      }
      try {
        const r = await fetch("/api/doctor_schedule", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ doctor_id: qm.doctor.value }),
        });
        if (!r.ok) {
          qm.warn && (qm.warn.style.display = "none");
          return;
        }
        const data = await r.json();
        const sched = data?.schedule || {};
        const s = new Date(start);
        const e = qm.end?.value ? new Date(qm.end.value) : new Date(start);
        const dow = (s.getDay() + 6) % 7;
        const day = sched[String(dow)];
        if (!day || !day.start || !day.end) {
          qm.warn && (qm.warn.style.display = "none");
          return;
        }
        const hm2m = (hm) => {
          const [h, m] = hm.split(":").map(Number);
          return h * 60 + m;
        };
        const st = s.getHours() * 60 + s.getMinutes(),
          en = e.getHours() * 60 + e.getMinutes();
        const outside = st < hm2m(day.start) || en > hm2m(day.end);
        if (outside) {
          qm.warn.textContent = `Время вне графика врача (${day.start}–${day.end}). Сохранение возможно.`;
          qm.warn.style.display = "block";
        } else {
          qm.warn.style.display = "none";
        }
      } catch {
        qm.warn && (qm.warn.style.display = "none");
      }
    }

    // ---------- FullCalendar ----------
    const calEl = document.getElementById("calendar");
    const calendar = new FullCalendar.Calendar(calEl, {
      initialView: "timeGridWeek",
      locale: "ru",
      buttonText: {
        today: "сегодня",
        month: "месяц",
        week: "неделя",
        day: "день",
      },
      allDayText: "Весь день",
      timeZone: "local",
      firstDay: 1,
      height: "auto",
      headerToolbar: {
        left: "prev,next today",
        center: "title",
        right: "dayGridMonth,timeGridWeek,timeGridDay",
      },
      slotDuration: "00:15:00",
      snapDuration: "00:15:00",
      slotMinTime: "09:00:00",
      slotMaxTime: "21:00:00",
      businessHours: {
        daysOfWeek: [1, 2, 3, 4, 5, 6],
        startTime: "09:00",
        endTime: "21:00",
      },

      editable: true,
      eventDurationEditable: true,
      eventStartEditable: true,
      eventOverlap: true,

      events: (fetchInfo, success, failure) => {
        const params = new URLSearchParams({
          start: fetchInfo.startStr,
          end: fetchInfo.endStr,
        });
        const doctorSel = $("#doctorFilter"),
          serviceSel = $("#serviceFilter"),
          cabinetSel = $("#cabinetFilter");
        if (doctorSel?.value) params.set("doctor_id", doctorSel.value);
        if (serviceSel?.value) params.set("service_id", serviceSel.value);
        if (cabinetSel?.value) params.set("room_name", cabinetSel.value); // фильтр по имени кабинета
        fetch("/api/events?" + params.toString())
          .then((r) => r.json())
          .then((data) => success(data))
          .catch((err) => {
            console.error("events load error", err);
            failure(err);
          });
      },

      eventDidMount(info) {
        const p = info.event.extendedProps || {};
        info.el.title = [p.service, p.patient, p.status]
          .filter(Boolean)
          .join(" • ");
      },

      eventDrop: saveMoveOrResize,
      eventResize: saveMoveOrResize,

      eventClick: async (info) => {
        setModalMode("edit");
        await openQuickModal(info.event.id);
      },

      dateClick: async (arg) => {
        try {
          const d = await loadDictsOnce();
          const doctorSel = document.getElementById("doctorFilter");
          fillOptions(qm.doctor, d.doctors, doctorSel?.value || "");
          fillOptions(qm.patient, d.patients);
          fillOptions(qm.service, d.services);
          fillOptions(qm.room, d.rooms);
          await fillContactBar(qm.patient?.value || "");


          const roundTo = 15;
          const s = new Date(arg.date);
          s.setMinutes(Math.round(s.getMinutes() / roundTo) * roundTo, 0, 0);
          const e = addMin(s, 30);

          if (qm.id) qm.id.value = "";
          if (qm.start) qm.start.value = fmtISO(s);
          if (qm.end) qm.end.value = fmtISO(e);

          updateFirstFreeBtnState();
          await recalcEndByService().catch(() => {});
          await checkDoctorWorking().catch(() => {});

          setModalMode("create");
          openModal();
        } catch (e) {
          console.error(e);
          showToast("Не удалось открыть форму создания", "error");
        }
      },
    });
    calendar.render();

    async function saveMoveOrResize(info) {
      const payload = {
        id: info.event.id,
        start: info.event.startStr,
        end: info.event.endStr || info.event.startStr,
      };
      try {
        const r = await fetch("/api/appointments/update_time", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });
        const data = await r.json();
        if (!data.ok) {
          alert(
            data.error === "room_conflict"
              ? "Конфликт: кабинет занят"
              : "Ошибка сохранения"
          );
          info.revert();
          return;
        }
        calendar.refetchEvents();
      } catch {
        alert("Сеть недоступна");
        info.revert();
      }
    }

    // открыть существующую
    async function openQuickModal(id) {
      try {
        const d = await loadDictsOnce();
        fillOptions(qm.doctor, d.doctors);
        fillOptions(qm.patient, d.patients);
        fillOptions(qm.service, d.services);
        fillOptions(qm.room, d.rooms);

        const r = await fetch(`/api/appointments/${id}`);
        const data = await r.json();
        if (!data.ok) {
          showToast("Не удалось получить запись", "error");
          return;
        }
        const it = data.item;

        if (qm.id) qm.id.value = it.id || "";
        if (qm.doctor) qm.doctor.value = it.doctor_id || "";
        if (qm.patient) qm.patient.value = it.patient_id || "";
        await fillContactBar(qm.patient?.value || "");
        if (qm.service) qm.service.value = it.service_id || "";
        if (qm.room) qm.room.value = it.room_id || "";
        if (qm.start) qm.start.value = (it.start || "").slice(0, 16);
        if (qm.end) qm.end.value = (it.end || "").slice(0, 16);
        if (qm.status) qm.status.value = it.status_key || "scheduled";
        if (qm.comment) qm.comment.value = it.comment || "";

        qm.service?.addEventListener(
          "change",
          () => {
            recalcEndByService();
            checkDoctorWorking();
          },
          { once: true }
        );
        qm.start?.addEventListener(
          "change",
          () => {
            recalcEndByService();
            checkDoctorWorking();
          },
          { once: true }
        );
        qm.end?.addEventListener("change", checkDoctorWorking, { once: true });
        qm.doctor?.addEventListener("change", checkDoctorWorking, {
          once: true,
        });

        await recalcEndByService();
        await checkDoctorWorking();
        setModalMode("edit");
        openModal();
      } catch (e) {
        console.error(e);
        showToast("Ошибка открытия модалки", "error");
      }
    }

    // submit / delete
    qm.form?.addEventListener("submit", async (ev) => {
      ev.preventDefault();
      const base = {
        doctor_id: qm.doctor?.value || "",
        patient_id: qm.patient?.value || "",
        service_id: qm.service?.value || "",
        room_id: qm.room?.value || "",
        start: qm.start?.value || "",
        end: qm.end?.value || "",
        status_key: qm.status?.value || "scheduled",
        comment: qm.comment?.value || "",
      };

      // CREATE
      if (!qm.id?.value) {
        if (
          !base.doctor_id ||
          !base.patient_id ||
          !base.service_id ||
          !base.room_id
        ) {
          showToast("Заполни поля: врач, пациент, услуга, кабинет", "error");
          return;
        }
        const payload = {
          start: base.start,
          end: base.end,
          room_id: base.room_id,
          doctor_id: base.doctor_id,
          patient_id: base.patient_id,
          service_id: base.service_id,
          note: base.comment || "",
        };
        let ok = false,
          lastErr = "";
        const endpoints = [
          "/api/appointments",
          "/api/appointments/create",
          "/schedule/api/create",
        ];
        for (const url of endpoints) {
          try {
            const r = await fetch(url, {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify(payload),
            });
            const data = await r.json().catch(() => ({}));
            if (
              r.status === 409 ||
              data?.error === "conflict" ||
              data?.error === "room_conflict"
            ) {
              showToast("Конфликт: кабинет/врач занят", "error");
              return;
            }
            if (r.ok && (data?.ok ?? true)) {
              ok = true;
              break;
            }
            lastErr = data?.error || `HTTP ${r.status}`;
          } catch {
            lastErr = "network";
          }
        }
        if (!ok) {
          showToast(
            `Ошибка создания${lastErr ? ` (${lastErr})` : ""}`,
            "error"
          );
          return;
        }
        showToast("Запись создана", "ok");
      }
      // UPDATE
      else {
        const r = await fetch(`/api/appointments/${qm.id.value}/update`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(base),
        });
        const data = await r.json();
        if (!r.ok || !data.ok) {
          const err =
            data?.error === "room_conflict"
              ? "Конфликт: кабинет занят"
              : "Ошибка сохранения";
          showToast(err, "error");
          return;
        }
        showToast("Изменения сохранены", "ok");
      }

      closeModal();
      calendar.refetchEvents();
    });

    // удаление
    qm.btnDel?.addEventListener("click", async () => {
      const id = qm.id?.value;
      if (!id) {
        showToast("Эта запись ещё не сохранена", "error");
        return;
      }
      if (!confirm("Удалить запись?")) return;
      const candidates = [
        { url: "/schedule/api/delete", body: { id } },
        { url: "/api/appointments/delete", body: { id } },
        {
          url: `/api/appointments/${encodeURIComponent(id)}`,
          method: "DELETE",
          body: {},
        },
      ];
      let ok = false;
      for (const c of candidates) {
        try {
          const r = await fetch(c.url, {
            method: c.method || "POST",
            headers: { "Content-Type": "application/json" },
            body: Object.keys(c.body || {}).length
              ? JSON.stringify(c.body)
              : undefined,
          });
          const data = await r.json().catch(() => ({}));
          if (r.ok && (data.ok ?? true)) {
            ok = true;
            break;
          }
        } catch {}
      }
      if (!ok) {
        showToast("Не удалось удалить", "error");
        return;
      }
      closeModal();
      calendar.refetchEvents();
      showToast("Запись удалена", "ok");
    });
  }); // DOMContentLoaded
</script>

<!-- MP-CONTACTS: JS -->
<script>
async function mpOpenContact(type, patientId) {
  try {
    if (!patientId) {
      const sel = document.getElementById('patient'); // <select id="patient"> в модалке
      if (sel) patientId = sel.value;
    }
    if (!patientId) { alert('Не выбран пациент'); return; }

    const res = await fetch(`/api/patients/${patientId}/contacts`, { cache: 'no-store' });
    if (!res.ok) { alert('Контакты недоступны'); return; }

    const j = await res.json();
    if (!j.ok) { alert('Контакты не найдены'); return; }

    const L = j.links || {};
    const url = L[type];
    if (!url) { alert('Нет ссылки для: ' + type); return; }

    window.open(url, '_blank', 'noopener');
  } catch (e) {
    console.error(e);
    alert('Ошибка открытия контакта');
  }
}
</script>
<!-- /MP-CONTACTS: JS -->


{% endblock %}
~~~

=== END FILE: .\templates\calendar.backup.html ===

=== BEGIN FILE: .\templates\calendar.html ===

~~~html
{% extends "base.html" %} {% block content %}

<!-- Метрики и действия -->
<div
  style="
    display: flex;
    align-items: center;
    gap: 22px;
    padding: 6px 0 6px 12px;
    background: #fff;
    border-radius: 14px;
    box-shadow: 0 1px 8px #e3eaf9b7;
    margin-bottom: 10px;
  "
>
  <span title="Всего кабинетов">
    <i class="fa-solid fa-house-chimney-medical" style="color: #467fe3"></i>
    <b>{{ metrics.total_rooms }}</b>
  </span>
  <span title="Свободные">
    <i class="fa-solid fa-circle-check" style="color: #21ba45"></i>
    <b>{{ metrics.free_rooms }}</b>
  </span>
  <span style="margin-left: auto; display: flex; gap: 12px">
    <a
      href="{{ url_for('add_event') }}"
      class="btn-main"
      style="
        background: #1976d2;
        color: #fff;
        font-weight: 600;
        border-radius: 8px;
        padding: 8px 22px;
        font-size: 1.07em;
        display: flex;
        align-items: center;
        gap: 8px;
        text-decoration: none;
      "
    >
      <i class="fa-solid fa-plus"></i> Добавить запись
    </a>
    <a
      href="{{ url_for('export_calendar') }}"
      class="btn-main btn-export"
      style="
        background: #fff;
        color: #3185cb;
        border: 1.5px solid #dbeafd;
        font-weight: 600;
        border-radius: 8px;
        padding: 8px 18px;
        font-size: 1.07em;
        display: flex;
        align-items: center;
        gap: 8px;
        text-decoration: none;
      "
    >
      <i class="fa-solid fa-file-arrow-down"></i> Выгрузка
    </a>
  </span>
</div>

<!-- Кабинеты и их статус -->
<div
  id="roomsBar"
  style="display: flex; gap: 36px; margin: 14px 0 12px 8px; flex-wrap: wrap"
>
  {% for cab in cabinets %} {% set info = room_info.get(cab) if room_info else
  None %}
  <span
    data-room-name="{{ cab }}"
    style="font-size: 1.12em; font-weight: 600; cursor: default"
  >
    {{ cab }} —
    <b
      class="room-status-text"
      style="color:{{ info.color if info else 'inherit' }}"
    >
      {{ info.text if info else '—' }}
    </b>
    <span
      class="room-next"
      style="opacity: 0.7; font-weight: 500; margin-left: 8px"
    >
      {% if info and info.state == 'available' and info.next %} {% set t =
      info.next.start.split('T')[1] if info.next.start else '' %} Ближайший: {{
      t }} {% if info.next.in_minutes is not none %} (через {% if
      info.next.in_minutes < 0 %}0 мин {% elif info.next.in_minutes < 60 %}{{
      info.next.in_minutes }} мин {% else %}{{ (info.next.in_minutes // 60)|int
      }} ч {{ (info.next.in_minutes % 60)|int }} мин {% endif %} ) {% endif %}
      {% if info.next.service or info.next.patient %} • {{ info.next.service
      }}{% if info.next.service and info.next.patient %} — {% endif %}{{
      info.next.patient }} {% endif %} {% endif %}
    </span>
  </span>
  {% endfor %}
</div>

<!-- Легенда/фильтры -->
<div
  style="
    display: flex;
    gap: 30px;
    align-items: center;
    font-size: 1.01em;
    margin-bottom: 12px;
    margin-left: 8px;
  "
>
  <span
    ><span
      style="
        background: #a2c6fa;
        border: 1.5px solid #dde7f7;
        width: 18px;
        height: 18px;
        display: inline-block;
        border-radius: 4px;
        margin-right: 6px;
      "
    ></span
    >Первичный</span
  >
  <span
    ><span
      style="
        background: #fbc7c0;
        border: 1.5px solid #fde7e7;
        width: 18px;
        height: 18px;
        display: inline-block;
        border-radius: 4px;
        margin-right: 6px;
      "
    ></span
    >Отказ</span
  >
  <span
    ><span
      style="
        background: #fde8a5;
        border: 1.5px solid #f7e9c5;
        width: 18px;
        height: 18px;
        display: inline-block;
        border-radius: 4px;
        margin-right: 6px;
      "
    ></span
    >Повторный</span
  >
  <span
    ><span
      style="
        background: #b4f0c0;
        border: 1.5px solid #cefad5;
        width: 18px;
        height: 18px;
        display: inline-block;
        border-radius: 4px;
        margin-right: 6px;
      "
    ></span
    >Оплачен</span
  >
</div>

<div
  class="calendar-filters"
  style="display: flex; gap: 12px; align-items: center; margin-bottom: 18px"
>
  <select id="doctorFilter" class="filter-select">
    <option value="">Все врачи</option>
    {% for doc in doctors %}
    <option value="{{ doc._id }}">{{ doc.full_name }}</option>
    {% endfor %}
  </select>

  <!-- ПОИСК ПАЦИЕНТА -->
  <div class="ps-wrap" style="position: relative; max-width: 320px">
    <input
      id="psInput"
      class="form-control"
      type="text"
      autocomplete="off"
      placeholder="Поиск пациента..."
    />
    <div
      id="psDrop"
      class="ps-drop"
      style="
        display: none;
        position: absolute;
        left: 0;
        right: 0;
        top: 100%;
        z-index: 4000;
        background: #fff;
        border: 1px solid #e5e7eb;
        border-top: 0;
        max-height: 280px;
        overflow: auto;
        border-radius: 0 0 8px 8px;
      "
    ></div>
  </div>

  <select id="serviceFilter" class="filter-select">
    <option value="">Все услуги</option>
  </select>

  <select id="cabinetFilter" class="filter-select">
    <option value="">Все кабинеты</option>
    {% for cab in cabinets %}
    <option value="{{ cab }}">{{ cab }}</option>
    {% endfor %}
  </select>

  <button id="btnResetFilters" class="btn btn-light">Сбросить</button>
</div>

<!-- Календарь -->
<div
  id="calendar"
  style="
    background: #fff;
    border-radius: 12px;
    box-shadow: 0 1px 8px #e3eaf9b7;
    padding: 8px;
    min-height: 72vh;
  "
></div>

<!-- Модалка -->
<div
  id="quickModal"
  style="
    display: none;
    position: fixed;
    inset: 0;
    background: rgba(0, 0, 0, 0.35);
    z-index: 9999;
  "
>
  <div
    style="
      background: #fff;
      max-width: 680px;
      margin: 7vh auto;
      padding: 18px;
      border-radius: 12px;
      box-shadow: 0 8px 28px rgba(0, 0, 0, 0.08);
    "
  >
    <div
      style="display: flex; align-items: center; gap: 8px; margin-bottom: 12px"
    >
      <h3 style="margin: 0; flex: 1">Редактировать запись</h3>
      <button
        id="qmClose"
        type="button"
        style="
          border: none;
          background: #eee;
          border-radius: 8px;
          padding: 6px 10px;
          cursor: pointer;
        "
      >
        ×
      </button>
    </div>

    <form
      id="qmForm"
      style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px"
    >
      <input type="hidden" id="qm_id" />

      <label
        >Врач
        <select
          id="qm_doctor"
          class="filter-select"
          required
          style="width: 100%"
        ></select>
      </label>

      <label
        >Пациент
        <div style="display: flex; gap: 8px; align-items: center; width: 100%">
          <select
            id="qm_patient"
            class="filter-select"
            required
            style="width: 100%"
          ></select>
          <!-- ==== CONTACT BAR (над календарём) ==== -->
          <div class="btn-group" role="group" aria-label="Контакты пациента">
            {% if patient is defined and patient %}
            <button
              type="button"
              class="btn btn-light"
              title="Позвонить"
              onclick="mpOpenContact('tel')"
            >
              📞
            </button>
            <button
              type="button"
              class="btn btn-light"
              title="WhatsApp"
              onclick="mpOpenContact('wa')"
            >
              🟢
            </button>
            <button
              type="button"
              class="btn btn-light"
              title="Telegram"
              onclick="mpOpenContact('tg')"
            >
              ✈️
            </button>
            <button
              type="button"
              class="btn btn-light"
              title="E-mail"
              onclick="mpOpenContact('mail')"
            >
              ✉️
            </button>
            <button
              type="button"
              class="btn btn-light"
              title="Max"
              onclick="mpOpenContact('max')"
            >
              Ⓜ️
            </button>
            {% endif %}
          </div>
          <!-- ======================================= -->

          <button
            type="button"
            id="qm_patient_add"
            class="btn"
            style="white-space: nowrap"
          >
            + Новый
          </button>
        </div>

        <!-- инлайн-форма создания пациента -->
        <div
          id="qm_patient_new"
          style="display: none; margin-top: 8px; width: 100%"
        >
          <div class="qm-patient-grid">
            <input
              id="qm_new_full_name"
              type="text"
              placeholder="ФИО полностью"
              autocomplete="name"
            />
            <input
              id="qm_new_phone"
              type="tel"
              inputmode="tel"
              pattern="[\+\d\s\-\(\)]{6,}"
              title="+7 999 123-45-67"
              placeholder="+7 999 123-45-67"
            />
            <input id="qm_new_birth" type="date" placeholder="Дата рождения" />
            <div class="qm-patient-actions">
              <button
                type="button"
                id="qm_patient_save"
                class="btn btn-primary"
              >
                Создать
              </button>
              <button type="button" id="qm_patient_cancel" class="btn">
                Отмена
              </button>
            </div>
          </div>
        </div>
        <!-- Панель быстрых контактов -->
        <div
          id="qm_contact_bar"
          style="
            display: flex;
            gap: 10px;
            align-items: center;
            margin: 6px 0 2px 0;
          "
        >
          <a
            id="cb_tel"
            class="btn"
            target="_blank"
            rel="noopener"
            title="Позвонить"
            style="padding: 4px 8px"
            >📞 Tel</a
          >
          <a
            id="cb_wa"
            class="btn"
            target="_blank"
            rel="noopener"
            title="WhatsApp"
            style="padding: 4px 8px"
            >🟢 WA</a
          >
          <a
            id="cb_tg"
            class="btn"
            target="_blank"
            rel="noopener"
            title="Telegram"
            style="padding: 4px 8px"
            >🔵 TG</a
          >
          <a
            id="cb_max"
            class="btn"
            target="_blank"
            rel="noopener"
            title="Max"
            style="padding: 4px 8px"
            >🟣 Max</a
          >
          <a
            id="cb_email"
            class="btn"
            target="_blank"
            rel="noopener"
            title="Email"
            style="padding: 4px 8px"
            >✉️ Mail</a
          >
          <small id="cb_hint" style="opacity: 0.7; margin-left: 6px"></small>
        </div>
      </label>
      <label
        >Услуга
        <select
          id="qm_service"
          class="filter-select"
          required
          style="width: 100%"
        ></select>
        <small id="qm_service_hint" style="opacity: 0.7"></small>
      </label>

      <label
        >Кабинет
        <select
          id="qm_room"
          class="filter-select"
          required
          style="width: 100%"
        ></select>
      </label>

      <label
        >Начало
        <input
          type="datetime-local"
          id="qm_start"
          required
          step="300"
          style="width: 100%"
        />
      </label>

      <label
        >Окончание
        <input
          type="datetime-local"
          id="qm_end"
          step="300"
          style="width: 100%"
        />
      </label>

      <label
        >Статус
        <select
          id="qm_status"
          class="filter-select"
          required
          style="width: 100%"
        >
          <option value="scheduled">Запланирован</option>
          <option value="arrived">Прибыл</option>
          <option value="done">Завершён</option>
          <option value="cancelled">Отменён</option>
        </select>
      </label>

      <label style="grid-column: 1 / -1"
        >Комментарий
        <textarea id="qm_comment" rows="3" style="width: 100%"></textarea>
      </label>

      <div
        style="
          grid-column: 1/-1;
          display: flex;
          gap: 8px;
          align-items: center;
          margin-top: -4px;
        "
      >
        <button
          type="button"
          class="btn"
          id="btn_plus_15"
          style="
            border: 1px solid #dbeafd;
            border-radius: 8px;
            padding: 6px 10px;
          "
        >
          +15 мин
        </button>
        <button
          type="button"
          class="btn"
          id="btn_plus_30"
          style="
            border: 1px solid #dbeafd;
            border-radius: 8px;
            padding: 6px 10px;
          "
        >
          +30 мин
        </button>
        <button
          type="button"
          class="btn"
          id="btn_plus_60"
          style="
            border: 1px solid #dbeafd;
            border-radius: 8px;
            padding: 6px 10px;
          "
        >
          +60 мин
        </button>
        <span style="opacity: 0.6; margin: 0 6px">|</span>
        <button
          type="button"
          class="btn"
          id="btn_move_tomorrow"
          style="
            border: 1px solid #dbeafd;
            border-radius: 8px;
            padding: 6px 10px;
          "
        >
          На завтра (то же время)
        </button>
        <span style="opacity: 0.6; margin: 0 6px">|</span>
        <button
          type="button"
          class="btn"
          id="btn_first_free"
          style="
            border: 1px solid #dbeafd;
            border-radius: 8px;
            padding: 6px 10px;
          "
        >
          Первый свободный слот (кабинет)
        </button>
      </div>
      <small
        id="qm_warn"
        style="grid-column: 1/-1; color: #b45309; display: none"
        >Предупреждение</small
      >

      <div
        style="
          grid-column: 1/-1;
          display: flex;
          justify-content: flex-end;
          gap: 8px;
        "
      >
        <button
          type="button"
          id="qmDelete"
          class="btn"
          style="background: #fee2e2; border: 1px solid #fecaca"
        >
          Удалить
        </button>
        <button type="submit" class="btn btn-primary">Сохранить</button>
      </div>
    </form>
  </div>
</div>

<!-- Toasts -->
<div
  id="toastStack"
  style="
    position: fixed;
    right: 16px;
    top: 16px;
    z-index: 10000;
    display: flex;
    flex-direction: column;
    gap: 8px;
  "
></div>

{% endblock %} {% block scripts %}
<link
  rel="stylesheet"
  href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css"
/>
<link
  href="https://cdn.jsdelivr.net/npm/fullcalendar@6.1.11/index.global.min.css"
  rel="stylesheet"
/>
<script src="https://cdn.jsdelivr.net/npm/fullcalendar@6.1.11/index.global.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/fullcalendar@6.1.11/locales-all.global.min.js"></script>

<style>
  /* форма нового пациента — стабильно, без «вылазов» */
  #quickModal .qm-patient-grid {
    display: grid;
    grid-template-columns: 1fr;
    gap: 8px;
    align-items: center;
  }
  #quickModal .qm-patient-grid input {
    width: 100%;
    height: 36px;
    padding: 8px 10px;
    border: 1px solid #dbeafd;
    border-radius: 8px;
    box-sizing: border-box;
  }
  #quickModal .qm-patient-grid input:focus {
    outline: none;
    border-color: #a5c5ff;
    box-shadow: 0 0 0 3px rgba(73, 133, 255, 0.12);
  }
  #quickModal .qm-patient-actions {
    display: flex;
    gap: 8px;
    justify-content: flex-start;
  }
  @media (min-width: 740px) {
    #quickModal .qm-patient-grid {
      grid-template-columns: 1fr 1fr;
    }
    #quickModal .qm-patient-grid > :first-child {
      grid-column: 1 / -1;
    } /* ФИО */
    #quickModal .qm-patient-actions {
      grid-column: 1 / -1;
    }
  }
  @media (min-width: 900px) {
    #quickModal .qm-patient-grid {
      grid-template-columns: 1fr 180px;
    }
  }
</style>

<script>
  // --- простой toast ---
  function showToast(msg, type = "info", ms = 2200) {
    const stack = document.getElementById("toastStack");
    if (!stack) {
      alert(msg);
      return;
    }
    const el = document.createElement("div");
    el.textContent = msg;
    el.style.cssText = `
      background:${
        type === "error" ? "#fee2e2" : type === "ok" ? "#e6ffed" : "#eef2ff"
      };
      color:${
        type === "error" ? "#991b1b" : type === "ok" ? "#065f46" : "#1e40af"
      };
      border:1px solid ${
        type === "error" ? "#fecaca" : type === "ok" ? "#bbf7d0" : "#c7d2fe"
      };
      box-shadow:0 6px 18px rgba(0,0,0,.08);padding:10px 14px;border-radius:10px;font-weight:600;max-width:420px`;
    stack.appendChild(el);
    setTimeout(() => {
      el.style.transition = "opacity .25s";
      el.style.opacity = "0";
      setTimeout(() => el.remove(), 260);
    }, ms);
  }
</script>
<script>
  document.addEventListener("DOMContentLoaded", () => {
    // ---------- helpers ----------
    const $ = (s) => document.querySelector(s);
    const addMin = (d, m) => new Date(d.getTime() + m * 60000);
    const pad2 = (n) => String(n).padStart(2, "0");
    const fmtISO = (d) =>
      `${d.getFullYear()}-${pad2(d.getMonth() + 1)}-${pad2(d.getDate())}T${pad2(
        d.getHours()
      )}:${pad2(d.getMinutes())}`;

    // кэш словарей
    window.__DICT_CACHE__ = window.__DICT_CACHE__ || null;

    // Универсальная заливка options
    function fillOptions(selectEl, items, selectedId = "") {
      if (!selectEl) return;
      const toId = (x) => x._id ?? x.id ?? "";
      const toName = (x) => x.full_name ?? x.name ?? "";
      const html = (items || [])
        .map((x) => {
          const id = toId(x),
            name = toName(x);
          return `<option value="${id}">${name}</option>`;
        })
        .join("");
      selectEl.innerHTML = html;
      if (selectedId) selectEl.value = selectedId;
      if (!selectEl.value || selectEl.value === "undefined") {
        const first = selectEl.querySelector("option")?.value || "";
        selectEl.value = first;
      }
    }

    // Загрузка словарей (нормализация)
    async function loadDictsOnce() {
      if (window.__DICT_CACHE__) return window.__DICT_CACHE__;
      const r = await fetch("/api/dicts");
      const raw = await r.json();
      if (!raw?.ok) throw new Error("dicts load failed");

      const norm = (arr) =>
        (arr || []).map((x) => ({
          id: x._id ?? x.id ?? "",
          name: x.full_name ?? x.name ?? "",
          duration_min: x.duration_min,
        }));
      const data = {
        ok: true,
        doctors: norm(raw.doctors),
        patients: norm(raw.patients),
        rooms: norm(raw.rooms),
        services: norm(raw.services).map((s) => ({
          ...s,
          duration_min: s.duration_min ?? 30,
        })),
      };
      window.__DICT_CACHE__ = data;
      return data;
    }

    // ---------- элементы модалки ----------
    const qm = {
      modal: $("#quickModal"),
      close: $("#qmClose"),
      form: $("#qmForm"),
      id: $("#qm_id"),
      doctor: $("#qm_doctor"),
      patient: $("#qm_patient"),
      service: $("#qm_service"),
      serviceHint: $("#qm_service_hint"),
      room: $("#qm_room"),
      start: $("#qm_start"),
      end: $("#qm_end"),
      status: $("#qm_status"),
      comment: $("#qm_comment"),
      warn: $("#qm_warn"),
      btnDel: $("#qmDelete"),
      btnPlus15: document.querySelector("#quickModal #btn_plus_15"),
      btnPlus30: document.querySelector("#quickModal #btn_plus_30"),
      btnPlus60: document.querySelector("#quickModal #btn_plus_60"),
      btnTomorrow: document.querySelector("#quickModal #btn_move_tomorrow"),
      btnFirstFree: document.querySelector("#quickModal #btn_first_free"),

      // блок «Новый пациент»
      patientAddBtn: document.getElementById("qm_patient_add"),
      patientNewRow: document.getElementById("qm_patient_new"),
      newFullName: document.getElementById("qm_new_full_name"),
      newPhone: document.getElementById("qm_new_phone"),
      newBirth: document.getElementById("qm_new_birth"),
      patientSaveBtn: document.getElementById("qm_patient_save"),
      patientCancelBtn: document.getElementById("qm_patient_cancel"),
    };

    function hideNewPatientRow() {
      if (!qm) return;
      if (qm.patientNewRow) qm.patientNewRow.style.display = "none";
      if (qm.newFullName) qm.newFullName.value = "";
      if (qm.newPhone) qm.newPhone.value = "";
      if (qm.newBirth) qm.newBirth.value = "";
    }

    // --- contacts bar (Tel/WA/TG/Max/Mail) ---------------------------------
    function setDisabledAnchor(a, disabled) {
      if (!a) return;
      if (disabled) {
        a.setAttribute("aria-disabled", "true");
        a.style.opacity = ".5";
        a.style.pointerEvents = "none";
        a.removeAttribute("href");
      } else {
        a.removeAttribute("aria-disabled");
        a.style.opacity = "1";
        a.style.pointerEvents = "auto";
      }
    }
    function onlyDigits(s) {
      return String(s || "").replace(/\D+/g, "");
    }

    async function fillContactBar(patientId) {
      const tel = document.getElementById("cb_tel");
      const wa = document.getElementById("cb_wa");
      const tg = document.getElementById("cb_tg");
      const mx = document.getElementById("cb_max");
      const em = document.getElementById("cb_email");
      const hint = document.getElementById("cb_hint");

      [tel, wa, tg, mx, em].forEach((a) => setDisabledAnchor(a, true));
      if (hint) hint.textContent = "";
      if (!patientId) return;

      try {
        const r = await fetch(
          `/api/patients/${encodeURIComponent(patientId)}/contacts`
        );
        const data = await r.json();
        if (!r.ok || !data.ok) return;

        const c = data.contacts || {};
        const phonePlus = (c.phone || "").trim();
        const phone = onlyDigits(phonePlus);
        const waNum = onlyDigits(c.whatsapp || c.phone || "");
        const mail = (c.email || "").trim();
        const tgHandle = (c.telegram || "").replace(/^@/, "").trim();

        if (phonePlus) {
          tel.href = `tel:${phonePlus}`;
          setDisabledAnchor(tel, false);
        }
        if (waNum) {
          wa.href = `https://wa.me/${waNum}`;
          setDisabledAnchor(wa, false);
        }
        if (tgHandle) {
          tg.href = `https://t.me/${tgHandle}`;
          setDisabledAnchor(tg, false);
        } else if (phone) {
          tg.href = `https://t.me/+${phone}`;
          setDisabledAnchor(tg, false);
        }

        // Max: аналог WhatsApp — открываем веб-клиент; при появлении deep-link подменим тут
        mx.href = `https://web.max.ru/`;
        setDisabledAnchor(mx, false);

        if (mail) {
          em.href = `mailto:${encodeURIComponent(mail)}`;
          setDisabledAnchor(em, false);
        }

        if (hint) {
          const parts = [];
          if (phonePlus) parts.push(phonePlus);
          if (mail) parts.push(mail);
          hint.textContent = parts.join(" • ");
        }
      } catch {}
    }
    // при смене выбранного пациента — обновить панель
    qm.patient?.addEventListener("change", () =>
      fillContactBar(qm.patient.value)
    );
    // --- создание пациента из модалки ---
    qm.patientAddBtn?.addEventListener("click", () => {
      qm.patientNewRow.style.display = "block";
      qm.newFullName?.focus();
    });
    qm.patientCancelBtn?.addEventListener("click", () => {
      qm.patientNewRow.style.display = "none";
      if (qm.newFullName) qm.newFullName.value = "";
      if (qm.newPhone) qm.newPhone.value = "";
      if (qm.newBirth) qm.newBirth.value = "";
    });
    qm.patientSaveBtn?.addEventListener("click", async () => {
      const full_name = (qm.newFullName?.value || "").trim();
      const phone = (qm.newPhone?.value || "").trim();
      const birth_date = (qm.newBirth?.value || "").trim();
      if (!full_name) {
        showToast("Укажи ФИО пациента", "error");
        return;
      }
      try {
        const r = await fetch("/api/patients", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ full_name, phone, birth_date }),
        });
        const data = await r.json().catch(() => ({}));
        if (!r.ok || !data.ok) {
          showToast(
            data?.error || `Ошибка создания (HTTP ${r.status})`,
            "error"
          );
          return;
        }
        const opt = document.createElement("option");
        opt.value = data.id;
        opt.textContent = data.full_name || full_name;
        qm.patient?.appendChild(opt);
        qm.patient.value = data.id;
        qm.newFullName.value = "";
        qm.newPhone.value = "";
        qm.newBirth.value = "";
        qm.patientNewRow.style.display = "none";
        if (window.__DICT_CACHE__) {
          window.__DICT_CACHE__.patients.unshift({
            id: data.id,
            name: data.full_name || full_name,
          });
        }
        showToast("Пациент создан", "ok");
      } catch {
        showToast("Сеть недоступна", "error");
      }
    });

    function isValidSelectValue(v) {
      return v && v !== "undefined" && v !== "null";
    }
    function updateFirstFreeBtnState() {
      const enable =
        isValidSelectValue(qm.room?.value) &&
        isValidSelectValue(qm.service?.value) &&
        !!qm.start?.value;
      if (qm.btnFirstFree) {
        qm.btnFirstFree.disabled = !enable;
        qm.btnFirstFree.style.opacity = enable ? "1" : "0.6";
        qm.btnFirstFree.style.pointerEvents = enable ? "auto" : "none";
      }
    }
    [qm.room, qm.service, qm.start].forEach((el) =>
      el?.addEventListener("change", updateFirstFreeBtnState)
    );

    const qmTitle = document.querySelector("#quickModal h3");
    const qmDeleteBtn = document.getElementById("qmDelete");
    function setModalMode(mode) {
      hideNewPatientRow(); // при любом режиме закрываем и чистим мини-форму
      if (!qmTitle) return;
      if (mode === "create") {
        qmTitle.textContent = "Новая запись";
        qmDeleteBtn?.setAttribute("disabled", "disabled");
        qmDeleteBtn?.classList.add("disabled");
      } else {
        qmTitle.textContent = "Редактировать запись";
        qmDeleteBtn?.removeAttribute("disabled");
        qmDeleteBtn?.classList.remove("disabled");
      }
    }
    function openModal() {
      if (qm.modal) qm.modal.style.display = "block";
    }
    function closeModal() {
      if (qm.modal) qm.modal.style.display = "none";
    }
    qm.close?.addEventListener("click", closeModal);
    window.addEventListener("keydown", (e) => {
      if (e.key === "Escape") closeModal();
    });

    // время
    function setStartEnd(ns, ne) {
      if (qm.start) qm.start.value = fmtISO(ns);
      if (qm.end) qm.end.value = fmtISO(ne);
    }
    function shiftAppointment(minutes) {
      if (!qm.start?.value) return;
      const s = new Date(qm.start.value);
      const e = qm.end?.value ? new Date(qm.end.value) : s;
      const dur = Math.max(5, Math.round((e - s) / 60000));
      const ns = addMin(s, minutes),
        ne = addMin(ns, dur);
      setStartEnd(ns, ne);
    }
    qm.btnPlus15?.addEventListener("click", () => shiftAppointment(15));
    qm.btnPlus30?.addEventListener("click", () => shiftAppointment(30));
    qm.btnPlus60?.addEventListener("click", () => shiftAppointment(60));
    qm.btnTomorrow?.addEventListener("click", () => {
      if (!qm.start?.value) return;
      const s = new Date(qm.start.value);
      const e = qm.end?.value ? new Date(qm.end.value) : s;
      const dur = Math.max(5, Math.round((e - s) / 60000));
      s.setDate(s.getDate() + 1);
      setStartEnd(s, addMin(s, dur));
    });

    // первый свободный слот в кабинете
    async function moveToFirstFreeInRoom() {
      const roomId = qm.room?.value,
        sid = qm.service?.value;
      if (
        !isValidSelectValue(roomId) ||
        !isValidSelectValue(sid) ||
        !qm.start?.value
      ) {
        showToast("Выбери кабинет, услугу и время начала", "error");
        updateFirstFreeBtnState();
        return;
      }
      const d = await loadDictsOnce();
      const sRec = d.services.find((x) => x.id === sid);
      const dur = parseInt(sRec?.duration_min ?? 30, 10);

      let cursor = new Date(qm.start.value);
      const limit = new Date();
      limit.setDate(limit.getDate() + 7);

      while (cursor < limit) {
        const day = `${cursor.getFullYear()}-${String(
          cursor.getMonth() + 1
        ).padStart(2, "0")}-${String(cursor.getDate()).padStart(2, "0")}`;
        const resp = await fetch(
          `/api/rooms/busy?room_id=${encodeURIComponent(roomId)}&date=${day}`
        );
        if (!resp.ok) {
          showToast("Не удалось проверить занятость кабинета", "error");
          return;
        }
        const data = await resp.json();
        if (!data.ok) {
          showToast("Не удалось проверить занятость кабинета", "error");
          return;
        }

        const busy = (data.items || [])
          .map((i) => {
            const [sh, sm] = i.start.split(":").map(Number),
              [eh, em] = i.end.split(":").map(Number);
            return { s: sh * 60 + sm, e: eh * 60 + em };
          })
          .sort((a, b) => a.s - b.s);

        const st = cursor.getHours() * 60 + cursor.getMinutes(),
          en = st + dur;
        const overlap = busy.some((b) => !(en <= b.s || st >= b.e));
        if (!overlap) {
          setStartEnd(cursor, addMin(cursor, dur));
          return;
        }
        cursor = addMin(cursor, 5);
      }
      showToast("Не найден свободный слот в ближайшие 7 дней", "error");
    }
    qm.btnFirstFree?.addEventListener("click", moveToFirstFreeInRoom);

    // длительность/подсказка
    async function recalcEndByService() {
      if (!qm.service?.value || !qm.start?.value) return;
      const d = await loadDictsOnce();
      const srv = d.services.find((s) => s.id === qm.service.value);
      const dur = parseInt(srv?.duration_min ?? 30, 10);
      const s = new Date(qm.start.value),
        e = addMin(s, isFinite(dur) ? dur : 30);
      if (qm.end) qm.end.value = fmtISO(e);
      if (qm.serviceHint)
        qm.serviceHint.textContent = `Длительность услуги: ${
          isFinite(dur) ? dur : 30
        } мин.`;
    }

    // мягкая проверка графика врача
    async function checkDoctorWorking() {
      const start = qm.start?.value;
      if (!qm.doctor?.value || !start) {
        qm.warn && (qm.warn.style.display = "none");
        return;
      }
      try {
        const r = await fetch("/api/doctor_schedule", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ doctor_id: qm.doctor.value }),
        });
        if (!r.ok) {
          qm.warn && (qm.warn.style.display = "none");
          return;
        }
        const data = await r.json();
        const sched = data?.schedule || {};
        const s = new Date(start);
        const e = qm.end?.value ? new Date(qm.end.value) : new Date(start);
        const dow = (s.getDay() + 6) % 7;
        const day = sched[String(dow)];
        if (!day || !day.start || !day.end) {
          qm.warn && (qm.warn.style.display = "none");
          return;
        }
        const hm2m = (hm) => {
          const [h, m] = hm.split(":").map(Number);
          return h * 60 + m;
        };
        const st = s.getHours() * 60 + s.getMinutes(),
          en = e.getHours() * 60 + e.getMinutes();
        const outside = st < hm2m(day.start) || en > hm2m(day.end);
        if (outside) {
          qm.warn.textContent = `Время вне графика врача (${day.start}–${day.end}). Сохранение возможно.`;
          qm.warn.style.display = "block";
        } else {
          qm.warn.style.display = "none";
        }
      } catch {
        qm.warn && (qm.warn.style.display = "none");
      }
    }

    // ---------- FullCalendar ----------
    // глобальное состояние фильтра по пациенту (мини-поиск наверху)
    window.__PS_SELECTED_PATIENT_ID__ = window.__PS_SELECTED_PATIENT_ID__ || "";

    // берём именно DOM-элемент календаря
    const calEl = document.getElementById("calendar");

    const calendar = new FullCalendar.Calendar(calEl, {
      initialView: "timeGridWeek",
      locale: "ru",
      buttonText: {
        today: "сегодня",
        month: "месяц",
        week: "неделя",
        day: "день",
      },
      allDayText: "Весь день",
      timeZone: "local",
      firstDay: 1,
      height: "auto",
      headerToolbar: {
        left: "prev,next today",
        center: "title",
        right: "dayGridMonth,timeGridWeek,timeGridDay",
      },
      slotDuration: "00:15:00",
      snapDuration: "00:15:00",
      slotMinTime: "09:00:00",
      slotMaxTime: "21:00:00",
      businessHours: {
        daysOfWeek: [1, 2, 3, 4, 5, 6],
        startTime: "09:00",
        endTime: "21:00",
      },

      editable: true,
      eventDurationEditable: true,
      eventStartEditable: true,
      eventOverlap: true,

      // ЗАГРУЗКА СОБЫТИЙ
      events: (fetchInfo, success, failure) => {
        const params = new URLSearchParams({
          start: fetchInfo.startStr,
          end: fetchInfo.endStr,
        });

        const doctorSel = document.querySelector("#doctorFilter");
        const serviceSel = document.querySelector("#serviceFilter");
        const cabinetSel = document.querySelector("#cabinetFilter");

        if (doctorSel?.value) params.set("doctor_id", doctorSel.value);
        if (serviceSel?.value) params.set("service_id", serviceSel.value);
        if (cabinetSel?.value) params.set("room_name", cabinetSel.value);

        // Фильтр по пациенту: ИЗБЕГАЕМ обращения к переменной calendar до инициализации!
        const psInput = document.getElementById("psInput");
        let pid = (psInput?.dataset?.selId || "").trim();
        if (!pid) pid = (window.__PS_SELECTED_PATIENT_ID__ || "").trim();
        if (pid) params.set("patient_id", pid);

        fetch("/api/events?" + params.toString())
          .then((r) => r.json())
          .then((data) => success(data))
          .catch((err) => {
            console.error("events load error", err);
            failure(err);
          });
      },

      eventDidMount(info) {
        const p = info.event.extendedProps || {};
        info.el.title = [p.service, p.patient, p.status]
          .filter(Boolean)
          .join(" • ");
      },

      eventDrop: saveMoveOrResize,
      eventResize: saveMoveOrResize,

      eventClick: async (info) => {
        setModalMode("edit");
        await openQuickModal(info.event.id);
      },

      dateClick: async (arg) => {
        try {
          const d = await loadDictsOnce();
          const doctorSel = document.getElementById("doctorFilter");
          fillOptions(qm.doctor, d.doctors, doctorSel?.value || "");
          fillOptions(qm.patient, d.patients);
          fillOptions(qm.service, d.services);
          fillOptions(qm.room, d.rooms);
          await fillContactBar(qm.patient?.value || "");

          hideNewPatientRow(); // по умолчанию скрыто; откроется только по кнопке «+ Новый»

          const roundTo = 15;
          const s = new Date(arg.date);
          s.setMinutes(Math.round(s.getMinutes() / roundTo) * roundTo, 0, 0);
          const e = new Date(s.getTime() + 30 * 60000);

          if (qm.id) qm.id.value = "";
          if (qm.start)
            qm.start.value = `${s.getFullYear()}-${String(
              s.getMonth() + 1
            ).padStart(2, "0")}-${String(s.getDate()).padStart(
              2,
              "0"
            )}T${String(s.getHours()).padStart(2, "0")}:${String(
              s.getMinutes()
            ).padStart(2, "0")}`;
          if (qm.end)
            qm.end.value = `${e.getFullYear()}-${String(
              e.getMonth() + 1
            ).padStart(2, "0")}-${String(e.getDate()).padStart(
              2,
              "0"
            )}T${String(e.getHours()).padStart(2, "0")}:${String(
              e.getMinutes()
            ).padStart(2, "0")}`;

          updateFirstFreeBtnState();
          await recalcEndByService().catch(() => {});
          await checkDoctorWorking().catch(() => {});

          setModalMode("create");
          openModal();
        } catch (e) {
          console.error(e);
          showToast("Не удалось открыть форму создания", "error");
        }
      },
    });

    window.calendar = calendar;
    calendar.render();

    async function saveMoveOrResize(info) {
      const payload = {
        id: info.event.id,
        start: info.event.startStr,
        end: info.event.endStr || info.event.startStr,
      };
      try {
        const r = await fetch("/api/appointments/update_time", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });
        const data = await r.json();
        if (!data.ok) {
          alert(
            data.error === "room_conflict"
              ? "Конфликт: кабинет занят"
              : "Ошибка сохранения"
          );
          info.revert();
          return;
        }
        calendar.refetchEvents();
      } catch {
        alert("Сеть недоступна");
        info.revert();
      }
    }

    // открыть существующую
    async function openQuickModal(id) {
      try {
        const d = await loadDictsOnce();
        fillOptions(qm.doctor, d.doctors);
        fillOptions(qm.patient, d.patients);
        fillOptions(qm.service, d.services);
        fillOptions(qm.room, d.rooms);

        hideNewPatientRow(); // всегда скрываем «Новый пациент» в режиме редактирования

        const r = await fetch(`/api/appointments/${id}`);
        const data = await r.json();
        if (!data.ok) {
          showToast("Не удалось получить запись", "error");
          return;
        }
        const it = data.item;

        if (qm.id) qm.id.value = it.id || "";
        if (qm.doctor) qm.doctor.value = it.doctor_id || "";
        if (qm.patient) qm.patient.value = it.patient_id || "";
        await fillContactBar(qm.patient?.value || "");
        if (qm.service) qm.service.value = it.service_id || "";
        if (qm.room) qm.room.value = it.room_id || "";
        if (qm.start) qm.start.value = (it.start || "").slice(0, 16);
        if (qm.end) qm.end.value = (it.end || "").slice(0, 16);
        if (qm.status) qm.status.value = it.status_key || "scheduled";
        if (qm.comment) qm.comment.value = it.comment || "";

        qm.service?.addEventListener(
          "change",
          () => {
            recalcEndByService();
            checkDoctorWorking();
          },
          { once: true }
        );
        qm.start?.addEventListener(
          "change",
          () => {
            recalcEndByService();
            checkDoctorWorking();
          },
          { once: true }
        );
        qm.end?.addEventListener("change", checkDoctorWorking, { once: true });
        qm.doctor?.addEventListener("change", checkDoctorWorking, {
          once: true,
        });

        await recalcEndByService();
        await checkDoctorWorking();
        setModalMode("edit");
        openModal();
      } catch (e) {
        console.error(e);
        showToast("Ошибка открытия модалки", "error");
      }
    }

    // submit / delete
    qm.form?.addEventListener("submit", async (ev) => {
      ev.preventDefault();
      // [MP] Автосоздание пациента при сохранении (если заполнен блок "Новый")
      async function mpEnsurePatientSelected() {
        let patientId = (qm.patient?.value || "").trim();
        const full_name = (qm.newFullName?.value || "").trim();
        const phone = (qm.newPhone?.value || "").trim();
        const birth_date = (qm.newBirth?.value || "").trim();

        // если пользователь что-то ввёл в "Новый пациент"
        if (full_name) {
          const needCreate =
            !patientId ||
            confirm(
              `Создать нового пациента «${full_name}» и использовать его вместо выбранного?`
            );
          if (needCreate) {
            try {
              const r = await fetch("/api/patients", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ full_name, phone, birth_date }),
              });
              const data = await r.json().catch(() => ({}));
              if (!r.ok || !(data.ok ?? true) || !data.id) {
                showToast(
                  data?.error || `Ошибка создания пациента (HTTP ${r.status})`,
                  "error"
                );
                return null; // отменяем сохранение
              }
              // добавить в селект и выбрать
              const opt = document.createElement("option");
              opt.value = data.id;
              opt.textContent = data.full_name || full_name;
              qm.patient?.appendChild(opt);
              qm.patient.value = data.id;
              patientId = data.id;

              // обновить кэш, очистить и скрыть блок "Новый"
              if (window.__DICT_CACHE__) {
                window.__DICT_CACHE__.patients?.unshift({
                  id: data.id,
                  name: data.full_name || full_name,
                });
              }
              if (qm.patientNewRow) qm.patientNewRow.style.display = "none";
              if (qm.newFullName) qm.newFullName.value = "";
              if (qm.newPhone) qm.newPhone.value = "";
              if (qm.newBirth) qm.newBirth.value = "";
              showToast("Пациент создан", "ok");
            } catch {
              showToast("Сеть недоступна (создание пациента)", "error");
              return null; // отменяем сохранение
            }
          }
        }
        return patientId;
      }

      const ensuredPatientId = await mpEnsurePatientSelected();
      if (!ensuredPatientId) return; // ошибка/отмена — не продолжаем сохранение

      const base = {
        doctor_id: qm.doctor?.value || "",
        patient_id: ensuredPatientId,
        service_id: qm.service?.value || "",
        room_id: qm.room?.value || "",
        start: qm.start?.value || "",
        end: qm.end?.value || "",
        status_key: qm.status?.value || "scheduled",
        comment: qm.comment?.value || "",
      };

      // CREATE
      if (!qm.id?.value) {
        if (
          !base.doctor_id ||
          !base.patient_id ||
          !base.service_id ||
          !base.room_id
        ) {
          showToast("Заполни поля: врач, пациент, услуга, кабинет", "error");
          return;
        }
        const payload = {
          start: base.start,
          end: base.end,
          room_id: base.room_id,
          doctor_id: base.doctor_id,
          patient_id: base.patient_id,
          service_id: base.service_id,
          note: base.comment || "",
        };
        let ok = false,
          lastErr = "";
        const endpoints = [
          "/api/appointments",
          "/api/appointments/create",
          "/schedule/api/create",
        ];
        for (const url of endpoints) {
          try {
            const r = await fetch(url, {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify(payload),
            });
            const data = await r.json().catch(() => ({}));
            if (
              r.status === 409 ||
              data?.error === "conflict" ||
              data?.error === "room_conflict"
            ) {
              showToast("Конфликт: кабинет/врач занят", "error");
              return;
            }
            if (r.ok && (data?.ok ?? true)) {
              ok = true;
              break;
            }
            lastErr = data?.error || `HTTP ${r.status}`;
          } catch {
            lastErr = "network";
          }
        }
        if (!ok) {
          showToast(
            `Ошибка создания${lastErr ? ` (${lastErr})` : ""}`,
            "error"
          );
          return;
        }
        showToast("Запись создана", "ok");
      }
      // UPDATE
      else {
        const r = await fetch(`/api/appointments/${qm.id.value}/update`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(base),
        });
        const data = await r.json();
        if (!r.ok || !data.ok) {
          const err =
            data?.error === "room_conflict"
              ? "Конфликт: кабинет занят"
              : "Ошибка сохранения";
          showToast(err, "error");
          return;
        }
        showToast("Изменения сохранены", "ok");
      }

      closeModal();
      calendar.refetchEvents();
    });

    // удаление
    qm.btnDel?.addEventListener("click", async () => {
      const id = qm.id?.value;
      if (!id) {
        showToast("Эта запись ещё не сохранена", "error");
        return;
      }
      if (!confirm("Удалить запись?")) return;
      const candidates = [
        { url: "/schedule/api/delete", body: { id } },
        { url: "/api/appointments/delete", body: { id } },
        {
          url: `/api/appointments/${encodeURIComponent(id)}`,
          method: "DELETE",
          body: {},
        },
      ];
      let ok = false;
      for (const c of candidates) {
        try {
          const r = await fetch(c.url, {
            method: c.method || "POST",
            headers: { "Content-Type": "application/json" },
            body: Object.keys(c.body || {}).length
              ? JSON.stringify(c.body)
              : undefined,
          });
          const data = await r.json().catch(() => ({}));
          if (r.ok && (data.ok ?? true)) {
            ok = true;
            break;
          }
        } catch {}
      }
      if (!ok) {
        showToast("Не удалось удалить", "error");
        return;
      }
      closeModal();
      calendar.refetchEvents();
      showToast("Запись удалена", "ok");
    });
  }); // DOMContentLoaded
</script>

<script>
  // === MINI SEARCH (patients) — единый рабочий вариант =========================
  (function () {
    const psInput = document.getElementById("psInput");
    const psDrop = document.getElementById("psDrop");
    if (!psInput || !psDrop) return;

    // Общая переменная фильтра (её читает загрузка событий календаря)
    window.__PS_SELECTED_PATIENT_ID__ = window.__PS_SELECTED_PATIENT_ID__ || "";

    // Поверх календаря и кликабельно
    psDrop.style.zIndex = "4000";
    psDrop.style.pointerEvents = "auto";

    // Утилиты
    function debounce(fn, ms = 250) {
      let t;
      return (...a) => {
        clearTimeout(t);
        t = setTimeout(() => fn(...a), ms);
      };
    }
    function hideDrop() {
      psDrop.style.display = "none";
      psDrop.innerHTML = "";
    }
    function showDrop() {
      psDrop.style.display = "block";
    }

    function renderDrop(items) {
      if (!items?.length) {
        hideDrop();
        return;
      }
      psDrop.innerHTML = items
        .map(
          (i) => `
      <div class="ps-item" data-id="${i.id}" data-name="${i.name}"
           style="padding:8px 10px; cursor:pointer; border-top:1px solid #f0f2f5;">
        <div style="display:flex; justify-content:space-between; gap:8px;">
          <span class="ps-name">${i.name}</span>
          <small style="opacity:.6">${i.birthdate || ""}${
            i.card_no ? " · #" + i.card_no : ""
          }</small>
        </div>
      </div>
    `
        )
        .join("");
      showDrop();
    }

    // Выбор пациента: записываем и в dataset, и в глобалку → перезагрузка событий
    function applyPatientFilter(id, name) {
      const selId = (id || "").trim();
      const selName = (name || "").trim();

      // Запоминаем в двух местах (любой из путей будет прочитан events loader'ом)
      psInput.dataset.selId = selId;
      window.__PS_SELECTED_PATIENT_ID__ = selId;

      // Отображаем имя в инпуте
      psInput.value = selName;

      // Прячем выпадашку и перегружаем события
      hideDrop();
      // На случай, если календарь ещё не успел инициализироваться — пробуем чуть позже
      const refetch = () =>
        window.calendar &&
        typeof window.calendar.refetchEvents === "function" &&
        window.calendar.refetchEvents();
      refetch() || setTimeout(refetch, 0);
    }

    // Поиск (debounce)
    const search = debounce(async () => {
      const q = (psInput.value || "").trim();
      if (q.length < 2) {
        hideDrop();
        return;
      }
      try {
        const r = await fetch(
          `/api/patients/min?q=${encodeURIComponent(q)}&limit=8`,
          { cache: "no-store" }
        );
        const data = await r.json().catch(() => ({}));
        if (!r.ok || !data?.ok) {
          hideDrop();
          return;
        }
        renderDrop(data.items || []);
      } catch {
        hideDrop();
      }
    }, 220);

    // Слушатели
    psInput.addEventListener("input", search);
    psInput.addEventListener("focus", search);

    // Выбор — на mousedown, чтобы не ловить blur
    psDrop.addEventListener("mousedown", (e) => {
      const item = e.target.closest(".ps-item");
      if (!item) return;
      e.preventDefault();
      e.stopPropagation();
      e.stopImmediatePropagation();
      applyPatientFilter(
        item.dataset.id,
        item.dataset.name || item.querySelector(".ps-name")?.textContent || ""
      );
    });

    // Клик вне — закрыть
    document.addEventListener("click", (e) => {
      if (e.target === psInput) return;
      if (psDrop.contains(e.target)) return;
      hideDrop();
    });

    // Enter — выбрать первый пункт
    psInput.addEventListener("keydown", (e) => {
      if (e.key !== "Enter") return;
      const first = psDrop.querySelector(".ps-item");
      if (!first) return;
      e.preventDefault();
      first.dispatchEvent(
        new MouseEvent("mousedown", { bubbles: true, cancelable: true })
      );
    });

    // «Сбросить» — очистить фильтр по пациенту
    document
      .getElementById("btnResetFilters")
      ?.addEventListener("click", () => {
        delete psInput.dataset.selId;
        window.__PS_SELECTED_PATIENT_ID__ = "";
        psInput.value = "";
        hideDrop();
        window.calendar &&
          window.calendar.refetchEvents &&
          window.calendar.refetchEvents();
      });
  })();
</script>

<!-- MP-CONTACTS: JS -->
<script>
  async function mpOpenContact(type, patientId) {
    function normPhone(s) {
      const d = (s || "").replace(/\D+/g, "");
      if (!d) return "";
      // нормализуем к формату 7xxxxxxxxxx
      if (d.startsWith("8") && d.length === 11) return "7" + d.slice(1);
      if (d.startsWith("7") && d.length === 11) return d;
      if (d.length === 10) return "7" + d; // без кода страны
      return d;
    }
    function buildLink(t, contacts, linksFromServer) {
      // если сервер прислал готовые ссылки — используем их
      if (linksFromServer && linksFromServer[t]) return linksFromServer[t];

      const phone = normPhone(contacts?.phone || contacts?.whatsapp || "");
      const tg = (contacts?.telegram || "").replace(/^@/, "");
      const mail = (contacts?.email || "").trim();
      const max = (contacts?.max || "").trim();

      switch (t) {
        case "tel":
          return phone ? `tel:+${phone}` : null;
        case "wa":
          return phone ? `https://wa.me/${phone}` : null;
        case "tg":
          // если есть ник — открываем по нику, иначе по телефону
          return tg
            ? `https://t.me/${encodeURIComponent(tg)}`
            : phone
            ? `https://t.me/+${phone}`
            : null;
        case "mail":
          return mail ? `mailto:${mail}` : null;
        case "max":
          // Макс «как WhatsApp»: пробуем открыть web.max.ru с телефоном,
          // если формат не подходит — просто открываем главную
          if (phone) return `https://web.max.ru/?phone=${phone}`;
          return `https://web.max.ru/`;
        default:
          return null;
      }
    }

    try {
      if (!patientId) {
        const sel = document.getElementById("patient"); // <select id="patient"> в модалке
        if (sel) patientId = sel.value;
      }
      if (!patientId) {
        alert("Не выбран пациент");
        return;
      }

      const res = await fetch(
        `/api/patients/${encodeURIComponent(patientId)}/contacts`,
        { cache: "no-store" }
      );
      if (!res.ok) {
        alert("Контакты недоступны");
        return;
      }

      const j = await res.json().catch(() => ({}));
      if (!j.ok) {
        alert("Контакты не найдены");
        return;
      }

      const url = buildLink(type, j.contacts || {}, j.links || null);
      if (!url) {
        alert("Нет ссылки для: " + type);
        return;
      }

      window.open(url, "_blank", "noopener");
    } catch (e) {
      console.error(e);
      alert("Ошибка открытия контакта");
    }
  }
</script>

<!-- /MP-CONTACTS: JS -->

{% endblock %}
~~~

=== END FILE: .\templates\calendar.html ===

=== BEGIN FILE: .\templates\close_appointment.html ===

~~~html
{% extends 'base.html' %}
{% block title %}Закрыть приём{% endblock %}
{% block content %}
<div style="max-width:600px;margin:0 auto;background:#fff;border-radius:20px;box-shadow:0 6px 32px rgba(20,40,80,.08);padding:38px;">
    <h2 style="font-size:1.4rem;font-weight:700;margin-bottom:18px;">Закрыть приём для пациента: <span style="color:#445be2;">{{ patient.full_name }}</span></h2>
    <form method="POST">
        <label>Что сделано (описание)</label>
        <textarea name="done" rows="2" style="width:100%;padding:10px;margin-bottom:18px;border-radius:8px;border:1px solid #ccd;"></textarea>

        <label>Услуги:</label>
        <table style="width:100%;margin-bottom:18px;">
            <tr>
                <th style="text-align:left;">Услуга</th>
                <th style="text-align:center;">Цена</th>
                <th style="text-align:center;">Кол-во</th>
            </tr>
            {% for i, s in enumerate(price_list) %}
            <tr>
                <td>{{ s.name }}</td>
                <td style="text-align:center;">{{ s.price }}</td>
                <td style="text-align:center;">
                    <input type="number" min="0" name="qty_{{i}}" value="0" style="width:60px;">
                </td>
            </tr>
            {% endfor %}
        </table>

        <label>План лечения (по необходимости)</label>
        <textarea name="plan" rows="2" style="width:100%;padding:10px;margin-bottom:22px;border-radius:8px;border:1px solid #ccd;"></textarea>

        <button type="submit" style="background:#445be2;color:#fff;border:none;border-radius:10px;padding:12px 32px;font-weight:700;font-size:1.09rem;cursor:pointer;">Закрыть приём</button>
    </form>
</div>
{% endblock %}
~~~

=== END FILE: .\templates\close_appointment.html ===

=== BEGIN FILE: .\templates\data_tools.html ===

~~~html
{% extends "base.html" %}
{% block content %}
<div class="data-tools-container">

  <h2>Экспорт / Импорт данных</h2>
  <div class="export-import-section">

    <!-- Экспорт -->
    <div class="export-block">
      <h3>Экспорт</h3>
      <form method="get" action="{{ url_for('export_data') }}">
        <label>Что выгрузить:</label>
        <select name="collection" class="filter-select">
          <option value="patients">Пациенты</option>
          <option value="doctors">Врачи</option>
          <option value="events">События</option>
          <option value="finance">Финансы</option>
        </select>
        <button type="submit" name="format" value="xlsx" class="btn btn-success">Excel</button>
        <button type="submit" name="format" value="csv" class="btn btn-outline-primary">CSV</button>
      </form>
      <small>Файл будет полностью совместим с Google Таблицами и Excel. Структура данных — готова к повторному импорту.</small>
    </div>

    <!-- Импорт -->
    <div class="import-block">
      <h3>Импорт</h3>
      <form method="post" action="{{ url_for('import_data') }}" enctype="multipart/form-data">
        <label>Что загружать:</label>
        <select name="collection" class="filter-select">
          <option value="patients">Пациенты</option>
          <option value="doctors">Врачи</option>
          <option value="events">События</option>
          <option value="finance">Финансы</option>
        </select>
        <input type="file" name="file" accept=".xlsx,.csv">
        <button type="submit" class="btn btn-primary">Импортировать</button>
        <a href="/static/templates/patients_template.xlsx" class="btn btn-link" download>Скачать шаблон Excel Пациенты</a>
      </form>
      <small>Структура файла: первая строка — названия столбцов (name, phone, email, ...). Все поля — в кодировке UTF-8.</small>
    </div>
  </div>

  <!-- История загрузок/выгрузок -->
  <div class="import-export-history">
    <h4>История загрузок и выгрузок</h4>
    <table class="table table-history">
      <thead>
        <tr>
          <th>Дата/Время</th>
          <th>Пользователь</th>
          <th>Операция</th>
          <th>Коллекция</th>
          <th>Файл</th>
          <th>Результат</th>
        </tr>
      </thead>
      <tbody>
        {% for h in history %}
        <tr>
          <td>{{ h.datetime }}</td>
          <td>{{ h.user }}</td>
          <td>{{ h.operation }}</td>
          <td>{{ h.collection }}</td>
          <td>{{ h.filename }}</td>
          <td>{{ h.result }}</td>
        </tr>
        {% else %}
        <tr><td colspan="6" style="text-align:center;color:#bbb;">Нет истории</td></tr>
        {% endfor %}
      </tbody>
    </table>
  </div>

</div>
<style>
.data-tools-container { padding:30px 0 0 0; }
.export-import-section { display: flex; gap: 46px; margin-bottom: 34px;}
.export-block, .import-block { background: #fff; border-radius: 19px; box-shadow:0 2px 22px #e3eaf92a; padding:26px 30px; min-width:320px; }
.table-history { margin-top:14px; }
</style>
{% endblock %}
~~~

=== END FILE: .\templates\data_tools.html ===

=== BEGIN FILE: .\templates\debtors.html ===

~~~html
{% extends "base.html" %}
{% block content %}
<h2>Должники/Депозиты</h2>
<table>
  <tr><th>Пациент</th><th>Долг</th></tr>
  {% for d in debtors %}
    <tr>
      <td>{{ d.full_name }}</td>
      <td>{{ d.debt }}</td>
    </tr>
  {% endfor %}
</table>
{% endblock %}
~~~

=== END FILE: .\templates\debtors.html ===

=== BEGIN FILE: .\templates\doctor_card.html ===

~~~html
{% extends 'base.html' %}
{% block content %}
<div class="doctor-card">
  <!-- Верх -->
  <div class="doctor-card-header">
    <div class="doctor-avatar">
      <img src="{{ doctor.avatar_url or '/static/avatars/doctor_default.png' }}" alt="avatar">
    </div>
    <div class="doctor-main-info">
      <h2>{{ doctor.full_name }}</h2>
      <div class="doctor-status">{{ doctor.position or 'Врач' }}</div>
      <div class="doctor-actions">
        <a href="/edit_doctor/{{ doctor._id }}" class="btn-main btn-edit"><i class="fa fa-edit"></i> Редактировать</a>
        <a href="tel:{{ doctor.phone }}" class="btn-main btn-call"><i class="fa fa-phone"></i> Позвонить</a>
        <a href="mailto:{{ doctor.email }}" class="btn-main btn-email"><i class="fa fa-envelope"></i> Email</a>
        <a href="/add_file/{{ doctor._id }}" class="btn-main btn-file"><i class="fa fa-upload"></i> Документы</a>
        <a href="/add_appointment/{{ doctor._id }}" class="btn-main btn-appt"><i class="fa fa-calendar-plus"></i> Записать пациента</a>
      </div>
    </div>
  </div>

  <!-- Вкладки -->
  <div class="tabs">
    <button class="tab-btn active" data-tab="info">Инфо</button>
    <button class="tab-btn" data-tab="schedule">Расписание</button>
    <button class="tab-btn" data-tab="reviews">Отзывы</button>
    <button class="tab-btn" data-tab="docs">Документы</button>
    <button class="tab-btn" data-tab="gallery">До/После</button>
  </div>

  <!-- Контент вкладок -->
  <div class="tab-content active" id="tab-info">
    <div class="doctor-info-sections">
      <div class="doctor-block">
        <h3>Основное</h3>
        <p><b>Специализация:</b> {{ doctor.specialization }}</p>
        <p><b>Телефон:</b> {{ doctor.phone }}</p>
        <p><b>Email:</b> {{ doctor.email }}</p>
        <p><b>Опыт работы:</b> {{ doctor.experience }} лет</p>
        <p><b>В клинике с:</b> {{ doctor.since }}</p>
      </div>
      <div class="doctor-block">
        <h3>Образование и квалификация</h3>
        <p>{{ doctor.education or "—" }}</p>
        <p>{{ doctor.certificates or "" }}</p>
      </div>
      <div class="doctor-block">
        <h3>Биография</h3>
        <p>{{ doctor.bio or "—" }}</p>
      </div>
    </div>
  </div>

  <div class="tab-content" id="tab-schedule">
    <div class="doctor-schedule-section">
      <h3>Расписание врача</h3>
      <div id="doctor-calendar"></div>
    </div>
  </div>

  <div class="tab-content" id="tab-reviews">
    <div class="doctor-history-section">
      <h3>Отзывы пациентов</h3>
      <div class="doctor-reviews">
        {% for review in doctor.reviews %}
          <div class="review-block">
            <div class="review-rating">{% for i in range(review.stars) %}★{% endfor %}</div>
            <div class="review-text">"{{ review.text }}"</div>
            <div class="review-date">{{ review.date }}</div>
          </div>
        {% endfor %}
      </div>
    </div>
  </div>

  <div class="tab-content" id="tab-docs">
    <div class="doctor-files-section">
      <h3>Документы и сертификаты</h3>
      <div class="doctor-files">
        {% for file in doctor.files %}
          <div class="file-preview">
            {% if file.type == 'image' %}
              <img src="{{ file.url }}" alt="file" />
            {% elif file.type == 'pdf' %}
              <a href="{{ file.url }}" target="_blank"><i class="fa fa-file-pdf"></i> PDF файл</a>
            {% endif %}
            <div class="file-name">{{ file.name }}</div>
          </div>
        {% endfor %}
        <a href="/add_file/{{ doctor._id }}" class="btn-main btn-file-upload"><i class="fa fa-upload"></i> Загрузить</a>
      </div>
    </div>
  </div>

  <div class="tab-content" id="tab-gallery">
    <div class="doctor-gallery-section">
      <h3>Галерея работ “До / После”</h3>
      <div class="gallery-row">
        {% for case in doctor.cases %}
        <div class="gallery-case">
          <div class="gallery-label">До</div>
          <img src="{{ case.before }}" alt="before">
          <div class="gallery-label">После</div>
          <img src="{{ case.after }}" alt="after">
        </div>
        {% endfor %}
      </div>
    </div>
  </div>
</div>
<script src="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css"></script>
<link href="https://cdn.jsdelivr.net/npm/fullcalendar@6.1.11/index.global.min.css" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/fullcalendar@6.1.11/index.global.min.js"></script>
<script>
document.addEventListener('DOMContentLoaded', function() {
  // Табы
  const tabBtns = document.querySelectorAll('.tab-btn');
  const tabContents = document.querySelectorAll('.tab-content');
  tabBtns.forEach(btn => {
    btn.addEventListener('click', function() {
      tabBtns.forEach(b => b.classList.remove('active'));
      tabContents.forEach(tc => tc.classList.remove('active'));
      this.classList.add('active');
      document.getElementById('tab-' + this.dataset.tab).classList.add('active');
      // При показе расписания — рендер календаря
      if (this.dataset.tab === "schedule" && !window.doctorCalRendered) {
        renderDoctorCalendar();
        window.doctorCalRendered = true;
      }
    });
  });

  // FullCalendar для расписания врача
  window.renderDoctorCalendar = function() {
    var calendarEl = document.getElementById('doctor-calendar');
    var events = [
      {% for ev in doctor.events %}
      {
        title: "{{ ev.title|e }}",
        start: "{{ ev.start }}",
        end: "{{ ev.end }}",
        backgroundColor: "{{ ev.color|default('#A2C6FA') }}",
        borderColor: "{{ ev.color|default('#A2C6FA') }}",
        // ... другие поля
      },
      {% endfor %}
    ];
    var calendar = new FullCalendar.Calendar(calendarEl, {
      initialView: 'timeGridWeek',
      locale: 'ru',
      slotMinTime: "08:00:00",
      slotMaxTime: "20:00:00",
      allDayText: 'Весь день',
      headerToolbar: { left: '', center: 'title', right: '' },
      events: events,
      height: 370,
      nowIndicator: true
    });
    calendar.render();
  };
});
</script>

{% endblock %}
~~~

=== END FILE: .\templates\doctor_card.html ===

=== BEGIN FILE: .\templates\doctors.html ===

~~~html
{% extends "base.html" %}
{% block content %}
<h2>Список врачей</h2>
<form method="get" class="doctors-filters" style="margin-bottom: 18px;">
  <select name="specialization" onchange="this.form.submit()" class="filter-select">
    <option value="">Все специальности</option>
    {% set all_specs = doctors | map(attribute='specialization') | list %}
    {% for spec in all_specs|unique %}
      {% if spec %}
        <option value="{{ spec }}" {% if request.args.get('specialization') == spec %}selected{% endif %}>{{ spec }}</option>
      {% endif %}
    {% endfor %}
  </select>
  <a href="{{ url_for('add_doctor') }}" class="btn-add-doc">
    <i class="fa fa-user-plus"></i> Добавить врача
  </a>
</form>
<div class="doctors-list">
  {% for doc in doctors %}
    <div class="doctor-card-row">
      <div class="avatar-zone">
        <img src="{{ doc.avatar_url or '/static/avatars/demo-doctor.png' }}" alt="avatar" class="avatar-doctor">
      </div>
      <div class="info-zone">
        <div class="doctor-name">{{ doc.full_name }}</div>
        <div class="doctor-meta">
          <span class="special">{{ doc.specialization }}</span>
          <span class="email"><i class="fa fa-envelope"></i> {{ doc.email }}</span>
          <span class="phone"><i class="fa fa-phone"></i> {{ doc.phone }}</span>
        </div>
        {% if doc.schedule %}
          <div class="doctor-schedule-mini">
            <b>Расписание:</b>
            <ul>
              {% for wd in range(1, 7) %}
                {% if doc.schedule[wd|string] %}
                  <li>
                    {{ ['Пн','Вт','Ср','Чт','Пт','Сб'][wd-1] }}:
                    {{ doc.schedule[wd|string].start }}–{{ doc.schedule[wd|string].end }}
                  </li>
                {% endif %}
              {% endfor %}
              {% if not (doc.schedule['1'] or doc.schedule['2'] or doc.schedule['3'] or doc.schedule['4'] or doc.schedule['5'] or doc.schedule['6']) %}
                <li style="color:#db2828;">Выходные</li>
              {% endif %}
            </ul>
          </div>
        {% endif %}
      </div>
      <div class="status-zone">
        <span class="doc-status {{ 'active' if doc.status == 'активен' else 'inactive' }}">{{ doc.status }}</span>
      </div>
      <div class="actions-zone">
        <a href="{{ url_for('doctor_card', doctor_id=doc._id) }}" class="btn-main">Подробнее</a>
      </div>
    </div>
  {% endfor %}
</div>
{% endblock %}

{% block head %}
<style>
.doctors-list {
  margin-top: 30px;
  display: flex;
  flex-direction: column;
  gap: 18px;
}
.doctor-card-row {
  display: flex;
  align-items: center;
  gap: 28px;
  background: #fff;
  border-radius: 18px;
  box-shadow: 0 4px 12px #0001;
  padding: 16px 28px;
  font-family: 'Montserrat', sans-serif;
  min-height: 84px;
  transition: box-shadow 0.2s;
}
.doctor-card-row:hover {
  box-shadow: 0 8px 18px #0002;
}
.avatar-zone {
  flex: none;
  width: 64px; height: 64px;
  display: flex; align-items: center; justify-content: center;
}
.avatar-doctor {
  width: 60px; height: 60px;
  border-radius: 16px;
  object-fit: cover;
  border: 2px solid #e5e7eb;
  background: #fafaff;
}
.info-zone {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 3px;
}
.doctor-name {
  font-size: 1.18em;
  font-weight: 600;
  color: #222;
}
.doctor-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 18px;
  font-size: 0.98em;
  color: #6d7892;
  margin-top: 2px;
  align-items: center;
}
.special {
  color: #3887f6;
  font-weight: 500;
}
.doctor-schedule-mini {
  margin-top: 7px;
  font-size: 0.97em;
  color: #4867ae;
  background: #f4f8ff;
  border-radius: 6px;
  padding: 6px 13px 6px 13px;
  display: inline-block;
  box-shadow: 0 1px 3px #e8edfa;
}
.doctor-schedule-mini ul {
  margin: 4px 0 0 0;
  padding-left: 18px;
}
.doctor-schedule-mini li {
  margin-bottom: 1px;
  list-style: disc;
}
.status-zone {
  min-width: 78px;
  text-align: center;
  font-size: 1.12em;
  font-weight: 600;
}
.doc-status.active {
  color: #21c400;
}
.doc-status.inactive {
  color: #f54040;
}
.actions-zone {
  display: flex;
  flex-direction: column;
  gap: 8px;
  min-width: 120px;
  align-items: flex-end;
}
.btn-main {
  padding: 6px 18px;
  background: #2196f3;
  color: #fff;
  border-radius: 8px;
  font-weight: 500;
  text-decoration: none;
  font-size: 0.97em;
  margin-bottom: 3px;
  transition: background 0.2s;
}
.btn-main:hover {
  background: #1767a2;
}
</style>
{% endblock %}
~~~

=== END FILE: .\templates\doctors.html ===

=== BEGIN FILE: .\templates\edit_doctor.html ===

~~~html
{% extends 'base.html' %}
{% block title %}Редактировать врача{% endblock %}
{% block content %}
<div style="max-width:440px; margin:0 auto; background:#fff; border-radius:20px; box-shadow:0 6px 32px rgba(20,40,80,.08); padding:38px 42px;">
    <h2 style="font-size:1.5rem; font-weight:700; margin-bottom:28px;">Редактировать данные врача</h2>
    <form method="POST">
        <label style="font-weight:600; margin-bottom:5px;">ФИО</label>
        <input name="full_name" type="text" required value="{{ doctor.full_name }}" style="width:100%; padding:10px; border-radius:8px; border:1px solid #ccd; margin-bottom:18px;">
        <label style="font-weight:600; margin-bottom:5px;">Специализация</label>
        <input name="specialization" type="text" value="{{ doctor.specialization }}" style="width:100%; padding:10px; border-radius:8px; border:1px solid #ccd; margin-bottom:18px;">
        <label style="font-weight:600; margin-bottom:5px;">E-mail</label>
        <input name="email" type="email" value="{{ doctor.email }}" style="width:100%; padding:10px; border-radius:8px; border:1px solid #ccd; margin-bottom:18px;">
        <label style="font-weight:600; margin-bottom:5px;">Телефон</label>
        <input name="phone" type="text" value="{{ doctor.phone }}" style="width:100%; padding:10px; border-radius:8px; border:1px solid #ccd; margin-bottom:18px;">
        <label style="font-weight:600; margin-bottom:5px;">Ссылка на аватар</label>
        <input name="avatar_url" type="text" value="{{ doctor.avatar_url }}" style="width:100%; padding:10px; border-radius:8px; border:1px solid #ccd; margin-bottom:22px;">
        <button type="submit" style="background:#445be2; color:#fff; border:none; border-radius:10px; padding:12px 28px; font-weight:700; font-size:1.07rem; cursor:pointer;">Сохранить</button>
    </form>
</div>
{% endblock %}
~~~

=== END FILE: .\templates\edit_doctor.html ===

=== BEGIN FILE: .\templates\edit_event.html ===

~~~html
{% extends "base.html" %}
{% block content %}
<div class="card" style="padding:20px;max-width:720px;margin:0 auto;">
  <h2>Редактировать запись</h2>
  <form method="post">
    <label>Врач</label>
    <select name="doctor_id" required>
      {% for d in doctors %}
        <option value="{{ d._id }}" {% if event.doctor_id == d._id %}selected{% endif %}>{{ d.full_name }}</option>
      {% endfor %}
    </select>

    <label>Пациент</label>
    <select name="patient_id" required>
      {% for p in patients %}
        <option value="{{ p._id }}" {% if event.patient_id == p._id %}selected{% endif %}>{{ p.full_name }}</option>
      {% endfor %}
    </select>

    <label>Кабинет</label>
    <select name="cabinet" required>
      {% for name in cabinets %}
        <option value="{{ name }}" {% if current_room_name == name %}selected{% endif %}>{{ name }}</option>
      {% endfor %}
    </select>

    <label>Услуга</label>
    <select name="service_id">
      <option value="">Без услуги</option>
      {% for s in services %}
        <option value="{{ s._id }}" {% if event.service_id == s._id %}selected{% endif %}>
          {{ s.name }} ({{ s.duration_min }} мин)
        </option>
      {% endfor %}
    </select>

    <label>Дата и время</label>
    <input type="datetime-local" name="datetime" value="{{ start_local }}" required>

    <label>Статус</label>
    <select name="status_key">
      <option value="scheduled"  {% if event.status_key=='scheduled' %}selected{% endif %}>Запланировано</option>
      <option value="checked_in" {% if event.status_key=='checked_in' %}selected{% endif %}>Пришёл</option>
      <option value="done"       {% if event.status_key=='done' %}selected{% endif %}>Выполнено</option>
      <option value="canceled"   {% if event.status_key=='canceled' %}selected{% endif %}>Отменено</option>
    </select>

    <label>Сумма</label>
    <input type="number" name="sum" value="{{ event.sum or 0 }}">

    <label>Комментарий</label>
    <textarea name="comment" rows="3">{{ event.comment or '' }}</textarea>

    <div style="margin-top:16px;">
      <button type="submit" class="btn btn-primary">Сохранить</button>
      <a href="{{ url_for('calendar_view') }}" class="btn">Отмена</a>
    </div>
  </form>
</div>
{% endblock %}
~~~

=== END FILE: .\templates\edit_event.html ===

=== BEGIN FILE: .\templates\edit_patient.html ===

~~~html
{% extends "base.html" %}
{% block content %}
<h2>Редактировать пациента</h2>

<form method="post" style="background:#fff;border-radius:12px;box-shadow:0 1px 8px #e3eaf9b7;padding:16px;max-width:860px;">
  <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">
    <label>ФИО
      <input type="text" name="full_name" value="{{ item.full_name }}" required>
    </label>
    <label>Дата рождения
      <input type="date" name="birthday" value="{{ item.birthday.strftime('%Y-%m-%d') if item.birthday else '' }}">
    </label>

    <label>Пол
      <select name="gender">
        <option value="male"   {% if item.gender=='male' %}selected{% endif %}>Мужской</option>
        <option value="female" {% if item.gender=='female' %}selected{% endif %}>Женский</option>
        <option value="other"  {% if item.gender=='other' %}selected{% endif %}>Другое</option>
      </select>
    </label>
    <label>Аватар (путь)
      <input type="text" name="avatar" value="{{ item.avatar or '' }}" placeholder="/static/avatars/patients/p1.jpg">
    </label>

    <label>Телефон
      <input type="text" name="phone" value="{{ item.contacts.phone }}">
    </label>
    <label>Email
      <input type="email" name="email" value="{{ item.contacts.email }}">
    </label>

    <label>WhatsApp
      <input type="text" name="whatsapp" value="{{ item.contacts.whatsapp }}">
    </label>
    <label>Telegram
      <input type="text" name="telegram" value="{{ item.contacts.telegram }}">
    </label>

    <label>Город
      <input type="text" name="city" value="{{ item.address.city }}">
    </label>
    <label>Улица/дом
      <input type="text" name="street" value="{{ item.address.street }}">
    </label>
    <label>Индекс
      <input type="text" name="zip" value="{{ item.address.zip }}">
    </label>

    <label style="grid-column:1/-1;">Заметки
      <textarea name="notes" rows="4">{{ item.notes or '' }}</textarea>
    </label>
  </div>

  <div style="margin-top:14px;display:flex;gap:10px;">
    <button type="submit" class="btn-main" style="background:#1976d2;color:#fff;padding:8px 14px;border-radius:8px;">Сохранить</button>
    <a href="{{ url_for('patients_list') }}">Отмена</a>
  </div>
</form>
{% endblock %}
~~~

=== END FILE: .\templates\edit_patient.html ===

=== BEGIN FILE: .\templates\edit_room.html ===

~~~html
{% extends "base.html" %}
{% block content %}
<h2>Редактировать кабинет</h2>

<form method="post" style="background:#fff;border-radius:12px;box-shadow:0 1px 8px #e3eaf9b7;padding:16px;max-width:720px;">
  <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">
    <label>Название
      <input type="text" name="name" value="{{ item.name }}" required>
    </label>

    <label>Тип
      <select name="type" required>
        {% for v,t in ROOM_TYPES %}
          <option value="{{ v }}" {% if item.type==v %}selected{% endif %}>{{ t }}</option>
        {% endfor %}
      </select>
    </label>

    <label>Статус
      <select name="status" required>
        {% for v,t in ROOM_STATUSES %}
          <option value="{{ v }}" {% if item.status==v %}selected{% endif %}>{{ t }}</option>
        {% endfor %}
      </select>
    </label>

    <label>Цвет
      <input type="color" name="color" value="{{ item.color or '#1abc9c' }}" style="height:42px;">
    </label>
  </div>

  <div style="margin-top:14px;display:flex;gap:10px;">
    <button type="submit" class="btn-main" style="background:#1976d2;color:#fff;padding:8px 14px;border-radius:8px;">Сохранить</button>
    <a href="{{ url_for('rooms_list') }}">Отмена</a>
  </div>
</form>
{% endblock %}
~~~

=== END FILE: .\templates\edit_room.html ===

=== BEGIN FILE: .\templates\edit_service.html ===

~~~html
{% extends "base.html" %}
{% block content %}
<h2>Редактировать услугу</h2>

<form method="post" style="background:#fff;border-radius:12px;box-shadow:0 1px 8px #e3eaf9b7;padding:16px;max-width:720px;">
  <div style="display:grid;grid-template-columns:1fr 180px;gap:12px;">
    <label>Название
      <input type="text" name="name" value="{{ item.name }}" required>
    </label>
    <label>Код
      <input type="text" name="code" value="{{ item.code }}" required>
    </label>

    <label>Цена, ₽
      <input type="number" name="price" value="{{ item.price }}" min="0" step="1">
    </label>
    <label>Длительность (мин)
      <input type="number" name="duration_min" value="{{ item.duration_min }}" min="5" step="5">
    </label>

    <label>Цвет
      <input type="color" name="color" value="{{ item.color or '#3498db' }}" style="height:42px;">
    </label>
    <label style="display:flex;align-items:center;gap:8px;margin-top:26px;">
      <input type="checkbox" name="is_active" {% if item.is_active %}checked{% endif %}> Активна
    </label>

    <label style="grid-column:1/-1;">Описание
      <textarea name="description" rows="4">{{ item.description or '' }}</textarea>
    </label>
  </div>

  <div style="margin-top:14px;display:flex;gap:10px;">
    <button type="submit" class="btn-main" style="background:#1976d2;color:#fff;padding:8px 14px;border-radius:8px;">Сохранить</button>
    <a href="{{ url_for('services_list') }}">Отмена</a>
  </div>
</form>
{% endblock %}
~~~

=== END FILE: .\templates\edit_service.html ===

=== BEGIN FILE: .\templates\expenses.html ===

~~~html
{% extends 'base.html' %}
{% block title %}Учёт расходов{% endblock %}
{% block content %}
<div style="max-width:900px;margin:0 auto;background:#fff;border-radius:20px;box-shadow:0 6px 32px rgba(20,40,80,.08);padding:38px;">
    <h2>Учёт расходов</h2>
    <div><b>Общий доход:</b> <span style="color:#25c045">{{ total_income|round(2) }} ₽</span></div>
    <div><b>Общие расходы:</b> <span style="color:red;">{{ total_expenses|round(2) }} ₽</span></div>
    <div><b>Чистая прибыль:</b> <span style="color:{{ 'green' if profit >= 0 else 'red' }};font-weight:700;">{{ profit|round(2) }} ₽</span></div>
    <hr style="margin:24px 0;">
    <table style="width:100%;">
        <tr>
            <th>Дата</th>
            <th>Категория</th>
            <th>Сумма</th>
            <th>Комментарий</th>
        </tr>
        {% for e in expenses %}
        <tr>
            <td>{{ e.date }}</td>
            <td>{{ e.category }}</td>
            <td>{{ e.amount|round(2) }} ₽</td>
            <td>{{ e.comment }}</td>
        </tr>
        {% endfor %}
    </table>
    <a href="/add_expense" style="margin-top:24px;display:inline-block;background:#445be2;color:#fff;padding:9px 18px;border-radius:8px;font-weight:700;">Добавить расход</a>
</div>
{% endblock %}
~~~

=== END FILE: .\templates\expenses.html ===

=== BEGIN FILE: .\templates\finance\add.html ===

~~~html
{% extends "_layout.html" %} {% block content %}
<div class="cs-wrap">
  <h1 class="cs-h1">Внести операцию</h1>
  <form method="post" action="/finance/add" class="cs-form" id="financeAddForm">
    <div class="cs-row">
      <label class="cs-label">Тип</label>
      <select name="type" class="cs-input" id="typeSel" required>
        <option value="income">Доход (оплата услуги)</option>
        <option value="expense">Расход</option>
        <option value="deposit">Депозит</option>
        <option value="salary">ЗП</option>
        <option value="purchase">Деньги на закупку</option>
      </select>
    </div>

    {% if preset_type %}
    <script>
      window.__preset_type__ = "{{ preset_type }}";
    </script>
    {% endif %}
    <input
      type="hidden"
      name="category"
      id="hiddenCategory"
      value="{{ preset_category or '' }}"
    />

    <div class="cs-row" id="amountRow" style="display: none">
      <label class="cs-label">Сумма</label>
      <input
        type="number"
        min="0"
        step="1"
        name="amount"
        class="cs-input"
        placeholder="0"
      />
    </div>

    <div class="cs-row">
      <label class="cs-label">Источник</label>
      <select name="source" class="cs-input">
        <option value="">—</option>
        <option value="alpha">Альфа</option>
        <option value="sber">Сбер</option>
        <option value="cash">Нал</option>
      </select>
    </div>

    <div class="cs-row">
      <label class="cs-label">Услуга (цена строго из прайса)</label>
      <select name="service_id" class="cs-input" id="svcSel">
        <option value="">—</option>
        {% for s in (services or []) %}
        <option value="{{ s._id }}" data-price="{{ s.price|default(0) }}">
          {{ s.name }} — {{ s.price|default(0) }} ₽
        </option>
        {% endfor %}
      </select>
      <div class="cs-hint" id="priceHint">Цена: —</div>
    </div>

    <div class="cs-row">
      <label class="cs-label">Комментарий</label>
      <input
        type="text"
        name="note"
        class="cs-input"
        placeholder="необязательно"
      />
    </div>

    <div class="cs-actions">
      <button class="cs-btn">Сохранить</button>
      <a class="cs-link" href="/finance">Отмена</a>
    </div>
  </form>
</div>

<script>
  (function () {
    const PRESET_TYPE = "{{ preset_type or '' }}";
    const PRESET_CATEGORY = "{{ preset_category or '' }}";

    const params = new URLSearchParams(location.search);
    const typeSel = document.getElementById("typeSel");
    const amountRow = document.getElementById("amountRow");
    const hiddenCategory = document.getElementById("hiddenCategory");

    // тип из query или пресета
    if (params.get("type")) typeSel.value = params.get("type");
    if (PRESET_TYPE) typeSel.value = PRESET_TYPE;

    // категория из query или пресета
    const cat = PRESET_CATEGORY || params.get("category") || "";
    if (hiddenCategory) hiddenCategory.value = cat;

    function toggleRows() {
      const isIncome = typeSel.value === "income";
      // сумма видна для НЕ доходов
      if (amountRow) amountRow.style.display = isIncome ? "none" : "";
      // услуга видна только для доходов
      const svcRow = document.getElementById("svcSel")?.closest(".cs-row");
      if (svcRow) svcRow.style.display = isIncome ? "" : "none";
    }
    typeSel.addEventListener("change", toggleRows);
    toggleRows();

    // подсказка цены услуги
    const svcSel = document.getElementById("svcSel");
    const hint = document.getElementById("priceHint");
    function updateHint() {
      const opt = svcSel?.options[svcSel.selectedIndex];
      const p = opt ? opt.getAttribute("data-price") : null;
      if (hint) hint.textContent = p ? "Цена: " + p + " ₽" : "Цена: —";
    }
    if (svcSel && hint) {
      svcSel.addEventListener("change", updateHint);
      updateHint();
    }
  })();
</script>

<style>
  .cs-wrap {
    max-width: 720px;
    margin: 0 auto;
    padding: 8px 12px 28px;
  }
  .cs-h1 {
    font-size: 28px;
    margin: 10px 0 14px;
  }
  .cs-form {
    display: flex;
    flex-direction: column;
    gap: 12px;
  }
  .cs-row {
    display: flex;
    flex-direction: column;
    gap: 6px;
  }
  .cs-label {
    font-size: 13px;
    color: #555;
  }
  .cs-input {
    padding: 8px 10px;
    border: 1px solid #d6d7dc;
    border-radius: 10px;
  }
  .cs-actions {
    display: flex;
    gap: 12px;
    align-items: center;
    margin-top: 8px;
  }
  .cs-btn {
    background: #2e6cff;
    color: #fff;
    border: 0;
    border-radius: 10px;
    padding: 10px 18px;
    cursor: pointer;
  }
  .cs-hint {
    font-size: 12px;
    color: #666;
  }
</style>
{% endblock %}
~~~

=== END FILE: .\templates\finance\add.html ===

=== BEGIN FILE: .\templates\finance\cashbox.html ===

~~~html
{% extends "_layout.html" %} {% block content %}
<h1 class="h1">Касса</h1>

<div class="grid" style="grid-template-columns: 240px 240px; gap: 16px">
  <div class="card">
    <div class="muted">Доходы</div>
    <div style="font-size: 28px; font-weight: 700">
      {{ income|default(0) }} ₽
    </div>
  </div>
  <div class="card">
    <div class="muted">Расходы</div>
    <div style="font-size: 28px; font-weight: 700">
      {{ expense|default(0) }} ₽
    </div>
  </div>
</div>

<div class="space"></div>

<div class="card">
  <div class="muted" style="margin-bottom: 8px">Поступления по источникам</div>
  <div class="toolbar">
    <span class="pill">Альфа — {{ by_source.alpha|default(0) }} ₽</span>
    <span class="pill">Сбер — {{ by_source.sber|default(0) }} ₽</span>
    <span class="pill">Нал — {{ by_source.cash|default(0) }} ₽</span>
  </div>

  <div class="muted" style="margin: 12px 0 8px">Расходы по категориям</div>
  <div class="toolbar" style="display: flex; gap: 8px; flex-wrap: wrap">
    {% set CAT_RU =
    {"purchase":"Закупка","marketing":"Маркетинг","dividends":"Дивиденды","rent":"Аренда"}
    %} {% if by_category %} {% for cat, sum in by_category.items() %}
    <a
      class="pill"
      href="/finance?type=expense&category={{ cat }}"
      title="Открыть операции категории «{{ CAT_RU.get(cat,cat) }}»"
    >
      {{ CAT_RU.get(cat,cat) }} — {{ sum }} ₽
    </a>
    {% endfor %} {% else %}
    <span class="muted">нет данных</span>
    {% endif %}
  </div>

  <div style="margin-top: 10px">
    <a class="link" href="/finance?type=expense">Все расходы</a>
  </div>

  <div class="space"></div>
  <div>
    <a class="link" href="/finance/export/csv?type=expense"
      >Экспорт расходов (CSV)</a
    >
    ·
    <a class="link" href="/finance/export/json?type=expense"
      >Экспорт расходов (JSON)</a
    >
  </div>

  <div class="space"></div>
  <div>
    Фильтр: <a class="link" href="/finance?source=alpha">Альфа</a> ·
    <a class="link" href="/finance?source=sber">Сбер</a> ·
    <a class="link" href="/finance?source=cash">Нал</a>
  </div>
</div>
{% endblock %}
~~~

=== END FILE: .\templates\finance\cashbox.html ===

=== BEGIN FILE: .\templates\finance\list.html ===

~~~html
{% extends "_layout.html" %}
{% block content %}

<h1 class="cs-h1">Финансы</h1>

<!-- Верхняя панель действий: скачать/импорт -->
<div class="cs-toolbar" style="margin:8px 0; display:flex; gap:12px; align-items:center;">
  <!-- Экспорт (учитываем текущие фильтры) -->
  <a class="cs-link" href="/finance/export/csv?type={{ f_type }}&source={{ f_source }}&category={{ f_category }}">Скачать CSV</a>
  <a class="cs-link" href="/finance/export/json?type={{ f_type }}&source={{ f_source }}&category={{ f_category }}">Скачать JSON</a>

  <!-- Импорт JSON -->
  <form method="post" action="/finance/import/json" enctype="multipart/form-data" style="display:flex; gap:6px;">
    <input type="file" name="file" accept="application/json" class="cs-input" required>
    <button class="cs-btn">Импорт JSON</button>
  </form>
</div>

<!-- МЕТРИКИ -->
<div class="cs-cards">
  <div class="cs-card"><div class="cs-metric-label">Доходы</div><div class="cs-metric-value">{{ income|default(0) }} ₽</div></div>
  <div class="cs-card"><div class="cs-metric-label">Расходы</div><div class="cs-metric-value">{{ expense|default(0) }} ₽</div></div>

  <div class="cs-card">
    <div class="cs-metric-label">Поступления по источникам</div>
    <ul class="cs-ul">
      <li><span class="cs-pill">alpha</span> {{ by_source.alpha|default(0) }} ₽</li>
      <li><span class="cs-pill">sber</span>  {{ by_source.sber|default(0)  }} ₽</li>
      <li><span class="cs-pill">cash</span>  {{ by_source.cash|default(0)  }} ₽</li>
    </ul>
  </div>
</div>

<!-- === ФИЛЬТРЫ (ОТДЕЛЬНАЯ ФОРМА!) === -->
<form method="get" action="/finance" class="cs-toolbar">
  <!-- Тип -->
  <select name="type" class="cs-input" title="Тип">
    <option value="">Все типы</option>
    <option value="income"   {{ 'selected' if f_type=='income'   else '' }}>Доход</option>
    <option value="expense"  {{ 'selected' if f_type=='expense'  else '' }}>Расход</option>
    <option value="deposit"  {{ 'selected' if f_type=='deposit'  else '' }}>Депозит</option>
    <option value="salary"   {{ 'selected' if f_type=='salary'   else '' }}>ЗП</option>
    <option value="purchase" {{ 'selected' if f_type=='purchase' else '' }}>Закупка</option>
  </select>

  <!-- Категория расхода -->
  <select name="category" class="cs-input" title="Категория">
    <option value="">Любая категория</option>
    <option value="purchase"  {{ 'selected' if f_category=='purchase'  else '' }}>Закупка</option>
    <option value="rent"      {{ 'selected' if f_category=='rent'      else '' }}>Аренда</option>
    <option value="marketing" {{ 'selected' if f_category=='marketing' else '' }}>Маркетинг</option>
    <option value="dividends" {{ 'selected' if f_category=='dividends' else '' }}>Дивиденды</option>
  </select>

  <!-- Источник -->
  <select name="source" class="cs-input" title="Источник">
    <option value="">Любой источник</option>
    <option value="alpha" {{ 'selected' if f_source=='alpha' else '' }}>Альфа</option>
    <option value="sber"  {{ 'selected' if f_source=='sber'  else '' }}>Сбер</option>
    <option value="cash"  {{ 'selected' if f_source=='cash'  else '' }}>Нал</option>
  </select>

  <button type="submit" class="cs-btn">Фильтр</button>

  <span style="margin-left:8px">Быстрые операции:</span>
  <a class="cs-link" href="/finance/add?type=expense&category=rent">Аренда</a>
  <a class="cs-link" href="/finance/add?type=expense&category=marketing">Маркетинг</a>
  <a class="cs-link" href="/finance/add?type=expense&category=dividends">Дивиденды</a>
  <a class="cs-link" href="/finance/add?type=purchase">Касса</a>
</form>

<!-- ТАБЛИЦА -->
<div class="cs-table-wrap">
  <table class="cs-table">
    <thead>
      <tr>
        <th>Время</th><th>Тип</th><th>Источник</th><th>Сумма</th><th>Услуга</th><th>Категория</th><th>Комментарий</th>
      </tr>
    </thead>
    <tbody>
      {% set CAT_RU = {"purchase":"Закупка","marketing":"Маркетинг","dividends":"Дивиденды","rent":"Аренда"} %}
      {% for it in (items or []) %}
      <tr>
        <td>{{ it.ts }}</td>
        <td>{{ it.type }}</td>
        <td>{{ it.source }}</td>
        <td>{{ it.amount }} ₽</td>
        <td>{{ it.service_name }}</td>
        <td>{{ CAT_RU.get(it.category, '—') }}</td>
        <td>{{ it.note }}</td>
      </tr>
      {% else %}
      <tr><td colspan="7" class="cs-empty">Записей нет</td></tr>
      {% endfor %}
    </tbody>
  </table>
</div>

{% endblock %}
~~~

=== END FILE: .\templates\finance\list.html ===

=== BEGIN FILE: .\templates\finance\print.html ===

~~~html
{% extends "_layout.html" %} {% block content %}
<h1 class="h1">Финансовые операции — печать</h1>

<style>
  @media print {
    .noprint {
      display: none;
    }
    body {
      background: #fff;
    }
  }
  table.print {
    width: 100%;
    border-collapse: collapse;
    font-size: 14px;
  }
  table.print th,
  table.print td {
    border: 1px solid #e5e7eb;
    padding: 6px 8px;
  }
  table.print th {
    background: #f8fafc;
    text-align: left;
  }
</style>

<div class="noprint" style="margin-bottom: 10px">
  <a class="cs-btn" href="#" onclick="window.print()">Печать</a>
  <a class="cs-link" href="/finance">Назад в «Финансы»</a>
</div>

<table class="print">
  <thead>
    <tr>
      <th>Время</th>
      <th>Тип</th>
      <th>Источник</th>
      <th>Сумма</th>
      <th>Услуга</th>
      <th>Категория</th>
      <th>Комментарий</th>
    </tr>
  </thead>
  <tbody>
    {% for it in (items or []) %}
    <tr>
      <td>{{ it.ts }}</td>
      <td>{{ it.type }}</td>
      <td>{{ it.source }}</td>
      <td>{{ it.amount }} ₽</td>
      <td>{{ it.service_name }}</td>
      <td>{{ it.category_ru }}</td>
      <td>{{ it.note }}</td>
    </tr>
    {% else %}
    <tr>
      <td colspan="7" class="cs-empty">Записей нет</td>
    </tr>
    {% endfor %}
  </tbody>
</table>
{% endblock %}
~~~

=== END FILE: .\templates\finance\print.html ===

=== BEGIN FILE: .\templates\finance_report.html ===

~~~html
{% extends "base.html" %}
{% block content %}

<div class="finance-dashboard">

  <!-- --- Карточки-индикаторы --- -->
  <div class="finance-indicators-row">
    <div class="finance-card income">
      <div class="finance-label">Доходы</div>
      <div class="finance-value">{{ summary.income | int }} ₽</div>
      <div class="finance-detail">за {{ summary.month_name }}</div>
    </div>
    <div class="finance-card expense">
      <div class="finance-label">Расходы</div>
      <div class="finance-value">{{ summary.expenses | int }} ₽</div>
      <div class="finance-detail">за {{ summary.month_name }}</div>
    </div>
    <div class="finance-card deposit">
      <div class="finance-label">Должники / Депозиты</div>
      <div class="finance-value">{{ summary.debtors_count }} чел / {{ summary.debtors_sum | int }} ₽</div>
      <div class="finance-detail">на сегодня</div>
    </div>
    <div class="finance-card avg">
      <div class="finance-label">Средний чек</div>
      <div class="finance-value">{{ summary.avg_check | int }} ₽</div>
      <div class="finance-detail">по {{ summary.month_name }}</div>
    </div>
    <div class="finance-export">
      <a href="/export_excel" class="btn btn-success">Выгрузить в Excel</a>
      <a href="/export_csv" class="btn btn-outline-primary">CSV</a>
      <button class="btn btn-outline-secondary" disabled style="opacity:0.7;">PDF (скоро)</button>
    </div>
  </div>

  <!-- --- Фильтр по периоду (можно позже сделать активным) --- -->
  <div class="finance-period-controls">
    <select class="filter-select" style="font-size:1.09em;">
      <option>Месяц</option>
      <option>Квартал</option>
      <option>Год</option>
    </select>
  </div>

  <!-- --- Компактный график --- -->
  <div class="finance-graph-card">
    <canvas id="financeChart" height="110"></canvas>
  </div>

  <!-- --- Сводная статистика --- -->
  <div class="finance-summary-row">
    <div>Операций за период: <b>{{ summary.operations_count }}</b></div>
    <div>Оплачено: <b>{{ summary.paid_count }}</b></div>
    <div>Процент оплат: <b>{{ summary.paid_percent }}%</b></div>
    <div>Топ врач: <b>{{ summary.top_doctor }}</b></div>
    <div>Топ услуга: <b>{{ summary.top_service }}</b></div>
  </div>

  <!-- --- Фильтры для таблицы --- -->
  <form method="get" class="finance-table-filters">
    <input type="text" name="search" placeholder="Поиск по пациенту, врачу, услуге..." value="{{ request.args.get('search','') }}">
    <select name="type" class="filter-select">
      <option value="">Тип</option>
      <option value="Доход">Доход</option>
      <option value="Расход">Расход</option>
    </select>
    <select name="status" class="filter-select">
      <option value="">Статус</option>
      <option value="новый">Новый</option>
      <option value="оплачен">Оплачен</option>
      <option value="отменён">Отменён</option>
      <option value="депозит">Депозит</option>
    </select>
    <button class="btn btn-outline-primary" type="submit">Фильтр</button>
  </form>

  <!-- --- Таблица операций --- -->
  <div class="finance-table-card">
    <table class="finance-table">
      <thead>
        <tr>
          <th>Дата</th>
          <th>Врач</th>
          <th>Пациент</th>
          <th>Услуга</th>
          <th>Тип</th>
          <th>Сумма</th>
          <th>Статус</th>
          <th>Комментарий</th>
        </tr>
      </thead>
      <tbody>
        {% for op in operations %}
        <tr>
          <td>{{ op.date }}</td>
          <td>
            <img src="{{ op.doctor_avatar_url or '/static/avatars/doctor.png' }}" class="mini-avatar"> {{ op.doctor }}
          </td>
          <td>
            <img src="{{ op.patient_avatar_url or '/static/avatars/patient.png' }}" class="mini-avatar"> {{ op.patient }}
          </td>
          <td>{{ op.service }}</td>
          <td>
            <span class="badge badge-{{ 'income' if op.type == 'Доход' else 'expense' }}">{{ op.type }}</span>
          </td>
          <td style="color:{{ '#24bb2a' if op.type == 'Доход' else '#e24343' }};"><b>{{ op.amount }} ₽</b></td>
          <td>
            <span class="badge badge-status badge-{{ op.status|lower }}">{{ op.status }}</span>
          </td>
          <td>{{ op.comment }}</td>
        </tr>
        {% endfor %}
      </tbody>
    </table>
  </div>

</div>

<!-- --- Chart.js --- -->
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<script>
document.addEventListener('DOMContentLoaded', function() {
  var ctx = document.getElementById('financeChart').getContext('2d');
  var data = {{ chart_data | safe }};
  new Chart(ctx, {
    type: 'line',
    data: data,
    options: {
      responsive: true,
      plugins: { legend: { display: true } },
      scales: { y: { beginAtZero: false } }
    }
  });
});
</script>

<style>
.finance-dashboard { padding: 20px 0; }
.finance-indicators-row {
  display: flex; flex-wrap: wrap; gap: 24px; align-items: flex-start;
  margin-bottom: 28px;
}
.finance-card {
  background: #fff;
  border-radius: 19px;
  box-shadow: 0 2px 22px #e3eaf93a;
  padding: 30px 38px 23px 32px;
  min-width: 220px;
  max-width: 270px;
  flex: 1;
  margin: 0 10px 0 0;
  display: flex; flex-direction: column; align-items: flex-start;
}
.finance-card.income { border-left: 6px solid #2ce148;}
.finance-card.expense { border-left: 6px solid #f6494c;}
.finance-card.deposit { border-left: 6px solid #2176bd;}
.finance-card.avg { border-left: 6px solid #ffbb23;}
.finance-label { color: #b3b8c3; font-size: 1em; font-weight: 600; margin-bottom: 8px;}
.finance-value { font-size: 2.12em; font-weight: 900; color: #233a59; letter-spacing: 1px; }
.finance-detail { font-size: 1.03em; color: #6d7892; margin-top: 7px; }
.finance-export {
  display: flex; flex-direction: column; gap: 8px; margin-left: 24px; align-items: flex-end; justify-content: center;
}
.finance-export .btn { min-width: 170px; }
.finance-graph-card {
  margin: 16px auto 0 auto;
  padding: 12px 12px 18px 12px;
  background: #fff;
  border-radius: 18px;
  max-width: 880px;
  min-width: 350px;
  box-shadow: 0 2px 20px #e8eef95c;
}
.finance-summary-row {
  display: flex;
  gap: 36px;
  padding: 18px 0 14px 4px;
  font-size: 1.09em;
  color: #7d8899;
  font-weight: 600;
}
.finance-period-controls {
  margin: 18px 0 12px 0;
  display: flex; justify-content: flex-end; align-items: center;
}
.finance-table-filters {
  display: flex; gap: 16px; margin-bottom: 14px; align-items: center;
}
.finance-table-card {
  background: #fff; border-radius: 18px;
  box-shadow: 0 2px 22px #e3eaf92a;
  padding: 22px 10px;
  margin-top: 18px;
}
.finance-table {
  width: 100%; border-collapse: separate; border-spacing: 0;
  font-size: 1.13em;
}
.finance-table th, .finance-table td { padding: 12px 10px; text-align: left; vertical-align: middle;}
.finance-table thead th { background: #f6fbff; position: sticky; top: 0; z-index: 1;}
.finance-table tbody tr { border-bottom: 1px solid #f2f6fd; transition: background .13s; }
.finance-table tbody tr:hover { background: #f3faff; }
.badge {
  display: inline-block; font-weight: 600;
  font-size: .99em; padding: 5px 15px; border-radius: 7px;
}
.badge-income { background: #c9ffe6; color: #1aa957; }
.badge-expense { background: #ffe1e1; color: #e64a4a; }
.badge-status { margin-left: 0; }
.badge-новый    { background: #fff7d6; color: #b49a25;}
.badge-оплачен  { background: #dafbe5; color: #18954e;}
.badge-отменён  { background: #ffdbdb; color: #e24343;}
.badge-депозит  { background: #e7f2fd; color: #2176bd;}
.mini-avatar {
  width: 28px; height: 28px;
  border-radius: 50%; object-fit: cover; margin-right: 7px;
  background: #f7fafd; box-shadow: 0 1px 6px #e3eaf9;
  vertical-align: middle;
}
@media (max-width: 1080px) {
  .finance-indicators-row { flex-direction: column; gap: 12px; }
  .finance-card { max-width: 100%; min-width: 140px; }
}
</style>
{% endblock %}
~~~

=== END FILE: .\templates\finance_report.html ===

=== BEGIN FILE: .\templates\import_doctors.html ===

~~~html
{% extends 'base.html' %}
{% block content %}
{% if preview_data %}
  <h3>Предпросмотр данных</h3>
  <form method="post" action="{{ url_for('import_doctors_confirm') }}">
    <input type="hidden" name="csv_data" value="{{ request.files['file'].stream.read().decode('utf-8-sig') | tojson }}">
    <table border="1" cellpadding="3">
      <tr>
        <th>ФИО</th>
        <th>Специализация</th>
        <th>Телефон</th>
        <th>Email</th>
        <th>Статус</th>
        <th>Ошибки</th>
      </tr>
      {% for item in preview_data %}
        <tr {% if item.errors %} style="background:#ffb3b3"{% endif %}>
          <td>{{ item.row.full_name }}</td>
          <td>{{ item.row.specialization }}</td>
          <td>{{ item.row.phone }}</td>
          <td>{{ item.row.email }}</td>
          <td>{{ item.row.status }}</td>
          <td>
            {% if item.errors %}
              <span style="color:red">{{ item.errors|join(', ') }}</span>
            {% else %}
              -
            {% endif %}
          </td>
        </tr>
      {% endfor %}
    </table>
    {% if show_confirm %}
      <button type="submit">Подтвердить импорт</button>
    {% endif %}
  </form>
{% endif %}
<h2>Импорт врачей из Excel (CSV)</h2>
<form method="post" enctype="multipart/form-data" style="margin:32px 0;">
    <input type="file" name="file" accept=".csv" required>
    <button class="btn btn-success" type="submit">Загрузить</button>
</form>
<div style="margin-top:18px;">
    <b>Формат CSV (разделитель — точка с запятой):</b><br>
    full_name;specialization;phone;email;status
</div>
{% endblock %}
~~~

=== END FILE: .\templates\import_doctors.html ===

=== BEGIN FILE: .\templates\import_patients.html ===

~~~html
<h2>Импорт пациентов</h2>

<a href="{{ url_for('import_template_patients') }}" class="btn" style="margin-bottom:15px;display:inline-block;">
  Скачать шаблон CSV для импорта пациентов
</a>

<form method="post" enctype="multipart/form-data" style="margin-top:10px;">
    <label for="file">Выберите CSV-файл:</label>
    <input type="file" name="file" id="file" required>
    <button type="submit">Импортировать</button>
</form>

{% if preview_data %}
  <h3>Предпросмотр данных</h3>
  <form method="post" action="{{ url_for('import_patients_confirm') }}">
    <input type="hidden" name="csv_data" value="{{ request.files['file'].stream.read().decode('utf-8-sig') | tojson }}">
    <table border="1" cellpadding="3">
      <tr>
        <th>ФИО</th>
        <th>Дата рождения</th>
        <th>Телефон</th>
        <th>Email</th>
        <th>Долг</th>
        <th>Депозит</th>
        <th>Ошибки</th>
      </tr>
      {% for item in preview_data %}
        <tr {% if item.errors %} style="background:#ffb3b3"{% endif %}>
          <td>{{ item.row.full_name }}</td>
          <td>{{ item.row.dob }}</td>
          <td>{{ item.row.phone }}</td>
          <td>{{ item.row.email }}</td>
          <td>{{ item.row.debt }}</td>
          <td>{{ item.row.deposit }}</td>
          <td>
            {% if item.errors %}
              <span style="color:red">{{ item.errors|join(', ') }}</span>
            {% else %}
              -
            {% endif %}
          </td>
        </tr>
      {% endfor %}
    </table>
    {% if show_confirm %}
      <button type="submit">Подтвердить импорт</button>
    {% endif %}
  </form>
{% endif %}

{% if message %}
  <div class="alert">{{ message }}</div>
{% endif %}

<p>
  <b>Внимание:</b> Используйте шаблон, чтобы не было ошибок. <br>
  Допустимые поля: <br>
  <code>full_name, dob, phone, passport, email, referral, debt, deposit, partner_points</code>
</p>
~~~

=== END FILE: .\templates\import_patients.html ===

=== BEGIN FILE: .\templates\journal.html ===

~~~html
{% extends "base.html" %}
{% block content %}
<h2>Журнал действий</h2>
<div class="card shadow p-4" style="max-width:1100px;margin:0 auto;">
  <table class="table action-table" style="width:100%;">
    <thead>
      <tr>
        <th>Дата/Время</th>
        <th>Пользователь</th>
        <th>Роль</th>
        <th>Действие</th>
        <th>Объект</th>
        <th>Комментарий</th>
      </tr>
    </thead>
    <tbody>
      {% for log in logs %}
      <tr>
        <td>{{ log.time }}</td>
        <td>
          <img src="{{ log.avatar_url }}" class="mini-avatar" style="width:28px;height:28px;border-radius:50%;margin-right:7px;">
          {{ log.user }}
        </td>
        <td>{{ log.role }}</td>
        <td>
          <span class="badge badge-info">{{ log.action_type }}</span>
        </td>
        <td>{{ log.target }}</td>
        <td>{{ log.comment or '' }}</td>
      </tr>
      {% endfor %}
    </tbody>
  </table>
</div>
{% endblock %}
~~~

=== END FILE: .\templates\journal.html ===

=== BEGIN FILE: .\templates\login.html ===

~~~html
{% extends 'base.html' %}
{% block title %}Вход в систему{% endblock %}
{% block content %}
<div style="max-width:400px; margin:60px auto; background:#fff; border-radius:20px; box-shadow:0 4px 24px rgba(20,40,80,.11); padding:36px 32px;">
    <h2 style="font-size:1.6rem; font-weight:700; margin-bottom:24px;">Вход в Medplatforma</h2>
    <form method="POST">
        <label style="font-weight:600;">E-mail</label>
        <input name="email" type="text" required style="width:100%; padding:11px; border-radius:8px; border:1px solid #ccd; margin-bottom:20px;">
        <label style="font-weight:600;">Пароль</label>
        <input name="password" type="password">
        <button type="submit" style="background:#445be2; color:#fff; border:none; border-radius:10px; padding:11px 28px; font-weight:700; font-size:1.08rem; cursor:pointer;">Войти</button>
    </form>
    {% with messages = get_flashed_messages(with_categories=true) %}
        {% if messages %}
            {% for category, message in messages %}
                <div style="color:#d91f3c; margin-top:18px;">{{ message }}</div>
            {% endfor %}
        {% endif %}
    {% endwith %}
</div>
{% endblock %}
~~~

=== END FILE: .\templates\login.html ===

=== BEGIN FILE: .\templates\logs.html ===

~~~html
{% extends "base.html" %}
{% block content %}

<div class="journal-header" style="display:flex;justify-content:space-between;align-items:center;">
  <h2>Журнал действий</h2>
  <a href="{{ url_for('export_logs', **request.args) }}" class="btn btn-outline-primary">Выгрузить видимое в CSV</a>
</div>

<form method="get" class="journal-filters" style="display:flex;gap:18px;align-items:center;margin-bottom:18px;">
  <input type="text" name="search" placeholder="Поиск по пользователю или действию..." value="{{ request.args.get('search','') }}">
  <select name="role">
    <option value="">Все роли</option>
    {% for r in roles %}
      <option value="{{ r }}" {% if r == selected_role %}selected{% endif %}>{{ r }}</option>
    {% endfor %}
  </select>
  <input type="date" name="start_date" value="{{ start_date }}">
  <input type="date" name="end_date" value="{{ end_date }}">
  <button type="submit" class="btn btn-outline-primary">Фильтр</button>
</form>

<div style="overflow-x:auto;">
<table class="journal-table" style="width:100%;background:#fff;border-radius:18px;box-shadow:0 2px 22px #e3eaf92a;">
  <thead>
    <tr>
      <th>Дата/Время</th>
      <th>Пользователь</th>
      <th>Роль</th>
      <th>IP</th>
      <th>Действие</th>
      <th>Объект</th>
      <th>Комментарий</th>
    </tr>
  </thead>
  <tbody>
    {% for log in logs %}
      <tr>
        <td>{{ log.datetime or "" }}</td>
        <td>
          {% if log.avatar_url %}
            <img src="{{ log.avatar_url }}" style="width:28px;height:28px;border-radius:50%;margin-right:5px;vertical-align:middle;">
          {% endif %}
          {{ log.user or "" }}
        </td>
        <td>{{ log.role or "" }}</td>
        <td style="color:#788;">{{ log.ip or "" }}</td>
        <td>{{ log.action or "" }}</td>
        <td>{{ log.object or "" }}</td>
        <td style="max-width:240px;white-space:normal;">{{ log.comment or "" }}</td>
      </tr>
    {% else %}
      <tr><td colspan="7" style="color:#aaa;text-align:center;">Нет записей</td></tr>
    {% endfor %}
  </tbody>
</table>
</div>
{% endblock %}
~~~

=== END FILE: .\templates\logs.html ===

=== BEGIN FILE: .\templates\messages.html ===

~~~html
{% extends "base.html" %}
{% block content %}
<div class="chat-container">
  <div class="chat-sidebar">
    <div class="chat-sidebar-title">Чаты</div>
    {% for chat in chats %}
      <div class="chat-sidebar-row {% if loop.first %}active{% endif %}">
        <img src="{{ chat.avatar or '/static/avatars/demo-user.png' }}" class="chat-avatar">
        <div class="chat-info">
          <div class="chat-title">{{ chat.title or chat.participants|join(', ') }}</div>
          <div class="chat-last">
            <span style="color:#8697b6;">
              {{ chat.messages[-1].sender }}:
              {{ chat.messages[-1].text[:26] }}{% if chat.messages[-1].text|length > 26 %}...{% endif %}
            </span>
            {% if not chat.messages[-1].read %}
              <span class="chat-badge">NEW</span>
            {% endif %}
          </div>
        </div>
        <div class="chat-time">{{ chat.messages[-1].timestamp[-5:] }}</div>
      </div>
    {% endfor %}
  </div>
  <div class="chat-main">
    <div class="chat-header">
      <img src="{{ chats[0].avatar or '/static/avatars/demo-user.png' }}" class="chat-header-avatar">
      <div>
        <div class="chat-header-title">{{ chats[0].title or chats[0].participants|join(', ') }}</div>
        <div class="chat-header-members">Участники: {{ chats[0].participants|join(', ') }}</div>
      </div>
    </div>
    <div class="chat-messages" id="chat-messages">
      {% for msg in chats[0].messages %}
        <div class="msg-bubble {% if msg.sender == user_name %}own{% endif %}">
          <img src="{{ msg.avatar or '/static/avatars/demo-user.png' }}" class="msg-avatar">
          <div class="msg-body">
            <div class="msg-meta">
              <span class="msg-author">{{ msg.sender }}</span>
              <span class="msg-role">{{ msg.role }}</span>
              <span class="msg-time">{{ msg.timestamp[-5:] }}</span>
            </div>
            <div class="msg-text">{{ msg.text }}</div>
          </div>
        </div>
      {% endfor %}
    </div>
    <form id="send-form" class="chat-input-wrap" onsubmit="return false;">
      <input type="text" class="chat-input" placeholder="Введите сообщение..." autocomplete="off" disabled>
      <button class="btn-send" disabled><i class="fa fa-paper-plane"></i> Отправить</button>
    </form>
    <div class="chat-demo-note">* Демо: отправка сообщений пока неактивна</div>
  </div>
</div>
{% endblock %}
~~~

=== END FILE: .\templates\messages.html ===

=== BEGIN FILE: .\templates\partners.html ===

~~~html
{% extends "base.html" %}
{% block content %}
<div class="partners-wrap">
  <h2 class="partners-title">Партнёрская программа</h2>
  <div class="partners-table-zone">
    <table class="partners-table">
      <thead>
        <tr>
          <th>Пациент</th>
          <th>Пригласил</th>
          <th>Рефералы</th>
        </tr>
      </thead>
      <tbody>
      {% for patient in patients %}
        <tr>
          <!-- Пациент (кликабельно) -->
          <td>
            <a href="{{ url_for('patient_card', id=patient._id) }}" class="partner-link">
              <img src="{{ patient.avatar_url }}" class="mini-avatar avatar-shadow">
              <span>{{ patient.full_name }}</span>
            </a>
          </td>
          <!-- Пригласил -->
          <td>
            {# Найдём пригласителя по patients_map #}
            {% set inviter = patient.invited_by and patients_map.get(patient.invited_by|string) %}
            {% if inviter %}
              <a href="{{ url_for('patient_card', id=inviter._id) }}" class="partner-link" style="color:#3797bc;">
                <img src="{{ inviter.avatar_url }}" class="mini-avatar avatar-shadow">
                <span>{{ inviter.full_name }}</span>
              </a>
            {% else %}
              <span class="badge-none">— нет</span>
            {% endif %}
          </td>
          <!-- Рефералы -->
          <td>
            {% set refs = referrals[patient._id|string] if patient._id|string in referrals else [] %}
            {% if refs and refs|length > 0 %}
              {% for ref in refs %}
                <a href="{{ url_for('patient_card', id=ref._id) }}" class="partner-link" style="color:#2aa44d;">
                  <img src="{{ ref.avatar_url }}" class="mini-avatar avatar-shadow">
                  <span>{{ ref.full_name }}</span>
                </a>
                {% if not loop.last %}<span style="margin:0 5px;color:#b2b6c3;">,</span>{% endif %}
              {% endfor %}
            {% else %}
              <span class="badge-none">— нет</span>
            {% endif %}
          </td>
        </tr>
      {% endfor %}
      </tbody>
    </table>
  </div>
</div>

<style>
.partners-wrap {
  display: flex; flex-direction: column; align-items: center; padding-top: 36px;
}
.partners-title {
  text-align: center;
  font-size: 2.45em;
  font-weight: 800;
  margin-bottom: 32px;
  color: #233a59;
  letter-spacing: 0.04em;
}
.partners-table-zone {
  background: #fff;
  border-radius: 28px;
  box-shadow: 0 6px 38px #cde7fa26;
  padding: 26px 30px 26px 30px;
  min-width: 720px;
  max-width: 980px;
}
.partners-table {
  width: 100%;
  border-collapse: separate;
  border-spacing: 0;
  font-size: 1.17em;
}
.partners-table thead tr {
  background: #f6fbff;
}
.partners-table th, .partners-table td {
  padding: 15px 14px;
  text-align: left;
  vertical-align: middle;
}
.partners-table tbody tr {
  border-bottom: 1px solid #f0f3fa;
  transition: background 0.12s;
}
.partners-table tbody tr:hover {
  background: #f4faff;
}
.partner-link {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  text-decoration: none;
  color: #2465c3;
  font-weight: 600;
  font-size: 1em;
  transition: color 0.14s;
}
.partner-link:hover {
  color: #183d66;
}
.mini-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  object-fit: cover;
  background: #f7fafd;
}
.avatar-shadow {
  box-shadow: 0 1px 8px #d1e4fa6b;
}
.badge-none {
  background: #f4f7fa;
  color: #c1c8d1;
  border-radius: 8px;
  padding: 5px 17px;
  font-size: .98em;
  font-weight: 600;
  letter-spacing: .01em;
  display: inline-block;
}
</style>
{% endblock %}
~~~

=== END FILE: .\templates\partners.html ===

=== BEGIN FILE: .\templates\patient_card.html ===

~~~html
{% extends "base.html" %} {% block content %}

<h2 style="margin: 8px 0 12px 0">Карточка пациента</h2>
<a href="/patients" class="btn" style="margin-bottom: 10px">↩︎ К списку</a>

<div
  style="
    background: #fff;
    border-radius: 12px;
    box-shadow: 0 1px 8px #e3eaf9b7;
    padding: 12px;
    max-width: 760px;
  "
>
  <form id="f" style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px">
    <label style="grid-column: 1/-1"
      >ФИО
      <input
        type="text"
        id="full_name"
        class="filter-input"
        required
        style="width: 100%"
      />
    </label>

    <label
      >Телефон
      <input
        type="tel"
        id="phone"
        class="filter-input"
        placeholder="+79991234567"
      />
    </label>

    <label
      >Дата рождения
      <input type="date" id="birth_date" class="filter-input" />
    </label>

    <label
      >№ карты
      <input
        type="number"
        id="card_no"
        class="filter-input"
        min="1"
        step="1"
        placeholder="авто"
      />
    </label>

    <div
      style="
        grid-column: 1/-1;
        display: flex;
        gap: 8px;
        justify-content: flex-end;
        margin-top: 4px;
      "
    >
      <a href="/patients" class="btn">Отмена</a>
      <button type="submit" class="btn btn-primary">Сохранить</button>
    </div>
  </form>
</div>

{% endblock %} {% block scripts %}
<script>
  (function () {
    const pid = "{{ pid }}";
    const $ = (s) => document.querySelector(s);
    const f = $("#f");

    async function load() {
      try {
        const r = await fetch(`/api/patients/${pid}`);
        const data = await r.json();
        if (!data.ok) throw new Error(data.error || "error");
        const it = data.item;
        $("#full_name").value = it.full_name || "";
        $("#phone").value = it.phone || "";
        $("#birth_date").value = (it.birthdate || "").toString().slice(0, 10);
        $("#card_no").value = it.card_no ?? "";
      } catch (e) {
        alert("Не удалось загрузить карточку");
        location.href = "/patients";
      }
    }

    f.addEventListener("submit", async (ev) => {
      ev.preventDefault();
      const payload = {
        full_name: $("#full_name").value.trim(),
        phone: $("#phone").value.trim(),
        birth_date: $("#birth_date").value || "",
        card_no:
          $("#card_no").value === "" ? null : Number($("#card_no").value),
      };
      try {
        const r = await fetch(`/api/patients/${pid}/update`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });
        const data = await r.json();
        if (!r.ok || !data.ok) {
          alert(data.error || "Ошибка сохранения");
          return;
        }
        alert("Сохранено");
        location.href = "/patients";
      } catch {
        alert("Сеть недоступна");
      }
    });

    load();
  })();
</script>
{% endblock %}
~~~

=== END FILE: .\templates\patient_card.html ===

=== BEGIN FILE: .\templates\patients.html ===

~~~html
{% extends "base.html" %} {% block content %}

<h2 style="margin: 8px 0 12px 0">Пациенты</h2>

<div style="display: flex; gap: 10px; align-items: center; margin-bottom: 10px">
  <input
    id="q"
    type="text"
    placeholder="Поиск (ФИО / телефон / №карты)"
    style="
      padding: 8px 12px;
      border: 1px solid #dde7f7;
      border-radius: 8px;
      min-width: 260px;
    "
  />
  <button id="btnSearch" class="btn">Искать</button>
  <span style="opacity: 0.6">|</span>
  <a href="/calendar" class="btn">↩︎ В календарь</a>
</div>

<div
  style="
    background: #fff;
    border-radius: 12px;
    box-shadow: 0 1px 8px #e3eaf9b7;
    padding: 10px;
  "
>
  <table style="width: 100%; border-collapse: collapse">
    <thead>
      <tr style="text-align: left; border-bottom: 1px solid #eef2ff">
        <th style="padding: 8px">№ карты</th>
        <th style="padding: 8px">ФИО</th>
        <th style="padding: 8px">Телефон</th>
        <th style="padding: 8px">Дата рождения</th>
      </tr>
    </thead>
    <tbody id="tblBody">
      <tr>
        <td colspan="4" style="padding: 12px; opacity: 0.6">Загрузка…</td>
      </tr>
    </tbody>
  </table>

  <div
    id="pager"
    style="display: flex; gap: 8px; align-items: center; margin-top: 10px"
  >
    <button id="prev" class="btn">‹ Назад</button>
    <span id="pgInfo" style="opacity: 0.8"></span>
    <button id="next" class="btn">Вперёд ›</button>
  </div>
</div>

{% endblock %} {% block scripts %}
<script>
  (function () {
    let page = 1,
      per_page = 50,
      total = 0;

    const $ = (s) => document.querySelector(s);
    const q = $("#q"),
      tbody = $("#tblBody"),
      pgInfo = $("#pgInfo");

    async function load() {
      const url = new URL("/api/patients", location.origin);
      if (q.value.trim()) url.searchParams.set("q", q.value.trim());
      url.searchParams.set("page", page);
      url.searchParams.set("per_page", per_page);

      tbody.innerHTML = `<tr><td colspan="4" style="padding:12px; opacity:.6">Загрузка…</td></tr>`;
      try {
        const r = await fetch(url);
        const data = await r.json();
        total = data.total || 0;

        if (!data.items || !data.items.length) {
          tbody.innerHTML = `<tr><td colspan="4" style="padding:12px; opacity:.6">Ничего не найдено</td></tr>`;
        } else {
          tbody.innerHTML = (data.items || [])
            .map(
              (it) => `
            <tr style="border-top:1px solid #f3f4f6">
              <td style="padding:8px; width:110px">${it.card_no ?? "—"}</td>
              <td style="padding:8px">
                <a href="/patients/${
                  it.id
                }" style="text-decoration:none; color:#1f6feb">${
                it.full_name || "—"
              }</a>
              </td>
              <td style="padding:8px">${it.phone || "—"}</td>
              <td style="padding:8px">${
                (it.birthdate || "").toString().slice(0, 10) || "—"
              }</td>
            </tr>
          `
            )
            .join("");
        }

        const pages = Math.max(1, Math.ceil(total / per_page));
        pgInfo.textContent = `Стр. ${page} из ${pages} • всего ${total}`;
        $("#prev").disabled = page <= 1;
        $("#next").disabled = page >= pages;
      } catch (e) {
        tbody.innerHTML = `<tr><td colspan="4" style="padding:12px; color:#991b1b; background:#fee2e2; border:1px solid #fecaca">Ошибка загрузки</td></tr>`;
        pgInfo.textContent = "";
      }
    }

    $("#btnSearch").addEventListener("click", () => {
      page = 1;
      load();
    });
    q.addEventListener("keydown", (e) => {
      if (e.key === "Enter") {
        page = 1;
        load();
      }
    });
    $("#prev").addEventListener("click", () => {
      if (page > 1) {
        page--;
        load();
      }
    });
    $("#next").addEventListener("click", () => {
      page++;
      load();
    });

    load();
  })();
</script>
{% endblock %}
~~~

=== END FILE: .\templates\patients.html ===

=== BEGIN FILE: .\templates\reports.html ===

~~~html
{% extends 'base.html' %}
{% block title %}Отчёты{% endblock %}
{% block content %}
<div style="max-width:900px; margin:0 auto; background:#fff; border-radius:24px; box-shadow:0 6px 32px rgba(20,40,80,.08); padding:36px 40px;">
    <h2 style="font-size:2.1rem; font-weight:700; margin-bottom:24px;">Отчёты</h2>
    <ul>
        <li>Финансовый отчёт по клинике</li>
        <li>Отчёт по пациентам</li>
        <li>Отчёт по приёмам</li>
        <li>Отчёт по задолженностям</li>
        <!-- Сделай как список или таблицу, по задаче -->
    </ul>
</div>
{% endblock %}
~~~

=== END FILE: .\templates\reports.html ===

=== BEGIN FILE: .\templates\roadmap.html ===

~~~html
{% extends "base.html" %}
{% block content %}
<div style="background:#fff;border-radius:12px;box-shadow:0 1px 8px #e3eaf9b7;padding:16px;">
  <div style="display:flex;align-items:center;gap:12px;margin-bottom:10px;">
    <h2 style="margin:0;flex:1;">ClubStom — Roadmap</h2>
    <a href="{{ url_for('roadmap_view') }}" class="btn-main" style="text-decoration:none;background:#1976d2;color:#fff;border-radius:8px;padding:8px 14px;">Обновить</a>
  </div>
  <div id="roadmap-body">
    {{ content|safe }}
  </div>
</div>
{% endblock %}
~~~

=== END FILE: .\templates\roadmap.html ===

=== BEGIN FILE: .\templates\roadmap_missing.html ===

~~~html
{% extends "base.html" %}
{% block content %}
<div style="background:#fff;border-radius:12px;box-shadow:0 1px 8px #e3eaf9b7;padding:16px;">
  <h2 style="margin-top:0">Roadmap не найден</h2>
  <p>Положите файл <code>roadmap_clubstom.md</code> в корень проекта (рядом с <code>app.py</code>), затем перезагрузите страницу.</p>
</div>
{% endblock %}
~~~

=== END FILE: .\templates\roadmap_missing.html ===

=== BEGIN FILE: .\templates\rooms.html ===

~~~html
{% extends "base.html" %}
{% block content %}

<div class="card" style="background:#fff;border-radius:12px;box-shadow:0 1px 8px #e3eaf9b7;padding:16px;">
  <div style="display:flex;gap:12px;align-items:center;justify-content:space-between;flex-wrap:wrap;">
    <h2 style="margin:0;">Кабинеты</h2>
    <a href="{{ url_for('add_room') }}" class="btn-main" style="background:#1976d2;color:#fff;padding:8px 14px;border-radius:8px;text-decoration:none;">Добавить кабинет</a>
  </div>

  <div style="overflow:auto;margin-top:12px;">
    <table style="width:100%;border-collapse:collapse;">
      <thead>
        <tr style="background:#f6f9ff;">
          <th style="text-align:left;padding:10px;border-bottom:1px solid #eef2fb;">Название</th>
          <th style="text-align:left;padding:10px;border-bottom:1px solid #eef2fb;">Тип</th>
          <th style="text-align:center;padding:10px;border-bottom:1px solid #eef2fb;">Статус</th>
          <th style="text-align:center;padding:10px;border-bottom:1px solid #eef2fb;">Цвет</th>
          <th style="width:180px;padding:10px;border-bottom:1px solid #eef2fb;">Действия</th>
        </tr>
      </thead>
      <tbody>
        {% for r in items %}
        <tr>
          <td style="padding:10px;border-bottom:1px solid #f1f4fb;">{{ r.name }}</td>
          <td style="padding:10px;border-bottom:1px solid #f1f4fb;">{{ r.type }}</td>
          <td style="padding:10px;border-bottom:1px solid #f1f4fb;text-align:center;">
            {% set st_title = status_title.get(r.status, r.status) %}
            {% if r.status == 'available' %}<span style="color:#27ae60;" title="{{ st_title }}">{{ st_title }}</span>
            {% elif r.status == 'occupied' %}<span style="color:#e67e22;" title="{{ st_title }}">{{ st_title }}</span>
            {% else %}<span style="color:#c0392b;" title="{{ st_title }}">{{ st_title }}</span>
            {% endif %}
          </td>
          <td style="padding:10px;border-bottom:1px solid #f1f4fb;text-align:center;">
            <span style="display:inline-block;width:22px;height:22px;border-radius:6px;border:1px solid #e3eaf9;background:{{ r.color }}"></span>
          </td>
          <td style="padding:10px;border-bottom:1px solid #f1f4fb;">
            <a href="{{ url_for('edit_room', id=r._id) }}" style="margin-right:8px;">Редактировать</a>
            <form action="{{ url_for('delete_room', id=r._id) }}" method="post" style="display:inline;" onsubmit="return confirm('Удалить кабинет «{{ r.name }}»?');">
              <button type="submit" style="color:#c0392b;background:#fff;border:1px solid #f1d6d6;border-radius:6px;padding:4px 8px;">Удалить</button>
            </form>
          </td>
        </tr>
        {% else %}
        <tr><td colspan="5" style="padding:18px;text-align:center;color:#8592a6;">Кабинетов пока нет</td></tr>
        {% endfor %}
      </tbody>
    </table>
  </div>
</div>

{% endblock %}
~~~

=== END FILE: .\templates\rooms.html ===

=== BEGIN FILE: .\templates\schedule\list.html ===

~~~html
{% extends "base.html" %} {% block title %}Расписание — {{ date_str }}{%
endblock %} {% block head %}

<style>
  .grid {
    display: grid;
    grid-template-columns: 100px 1fr;
    gap: 12px;
  }
  .rooms {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: 8px;
  }
  .slot {
    border: 1px solid #e5e7eb;
    border-radius: 8px;
    padding: 6px;
    background: #fff;
    min-height: 34px;
  }
  .muted {
    color: #6b7280;
  }
  .toolbar a {
    margin-right: 10px;
  }
  .pill {
    display: inline-block;
    padding: 3px 8px;
    border: 1px solid #e5e7eb;
    border-radius: 999px;
    background: #fff;
  }
  form.inline {
    display: flex;
    gap: 6px;
    flex-wrap: wrap;
  }
  input,
  select {
    border: 1px solid #d1d5db;
    border-radius: 6px;
    padding: 4px 6px;
  }
  .room-head {
    font-weight: 600;
    margin-bottom: 6px;
  }
  .timecell {
    color: #6b7280;
  }
</style>
{% endblock %} {% block content %}
<h1>Расписание</h1>

<div class="toolbar" style="margin-bottom: 10px">
  <a class="pill" href="/schedule?date={{ prev_day }}">← Назад</a>
  <a class="pill" href="/schedule?date={{ today }}">Сегодня</a>
  <a class="pill" href="/schedule?date={{ next_day }}">Вперёд →</a>
  <span class="muted" style="margin-left: 10px">День: {{ date_str }}</span>
</div>

<div class="grid">
  <!-- Левая колонка — время -->
  <div>
    {% for t in slots %}
    <div class="timecell" style="height: 34px">{{ t }}</div>
    {% endfor %}
  </div>

  <!-- Правая колонка — комнаты со слотами -->
  <div class="rooms">
    {% for r in rooms %}
    <div>
      <div class="room-head">{{ r.name }}</div>
      {% for t in slots %} {% set k = (t, r.code) %}
      <div class="slot">
        {% if cell.get(k) %} {% for ap in cell.get(k) %}
        <div>
          <b>{{ ap.patient_name or "Пациент" }}</b> — {{ ap.duration or 15 }}
          мин.
          <span class="muted">{{ ap.doctor_name or "" }}</span>
        </div>
        {% if ap.note %}
        <div class="muted">{{ ap.note }}</div>
        {% endif %} {% endfor %} {% else %}
        <!-- Быстрое добавление записи в пустой слот -->
        <form class="inline" method="post" action="/schedule/add">
          <input type="hidden" name="date" value="{{ date_str }}" />
          <input type="hidden" name="room" value="{{ r.code }}" />
          <input type="hidden" name="time" value="{{ t }}" />
          <select name="duration">
            <option value="15">15</option>
            <option value="30">30</option>
            <option value="60">60</option>
          </select>
          <input name="patient_name" placeholder="Пациент" required />
          <input name="doctor_name" placeholder="Врач" />
          <button>OK</button>
        </form>
        {% endif %}
      </div>
      {% endfor %}
    </div>
    {% endfor %}
  </div>
</div>
{% endblock %}
~~~

=== END FILE: .\templates\schedule\list.html ===

=== BEGIN FILE: .\templates\services.html ===

~~~html
{% extends "base.html" %}
{% block content %}

<div class="card" style="background:#fff;border-radius:12px;box-shadow:0 1px 8px #e3eaf9b7;padding:16px;">
  <div style="display:flex;gap:12px;align-items:center;justify-content:space-between;flex-wrap:wrap;">
    <h2 style="margin:0;">Услуги</h2>
    <div style="display:flex;gap:8px;align-items:center;">
      <a href="{{ url_for('add_service') }}" class="btn-main" style="background:#1976d2;color:#fff;padding:8px 14px;border-radius:8px;text-decoration:none;">Добавить услугу</a>
      <form method="get" action="{{ url_for('services_list') }}" style="display:flex;gap:8px;align-items:center;">
        <select name="status" class="filter-select">
          <option value="">Все</option>
          <option value="active" {{ 'selected' if request.args.get('status')=='active' else '' }}>Активные</option>
          <option value="archived" {{ 'selected' if request.args.get('status')=='archived' else '' }}>Архив</option>
        </select>
        <button type="submit">Фильтр</button>
      </form>
    </div>
  </div>

  <div style="overflow:auto;margin-top:12px;">
    <table style="width:100%;border-collapse:collapse;">
      <thead>
        <tr style="background:#f6f9ff;">
          <th style="text-align:left;padding:10px;border-bottom:1px solid #eef2fb;">Название</th>
          <th style="text-align:left;padding:10px;border-bottom:1px solid #eef2fb;">Код</th>
          <th style="text-align:right;padding:10px;border-bottom:1px solid #eef2fb;">Цена, ₽</th>
          <th style="text-align:right;padding:10px;border-bottom:1px solid #eef2fb;">Длит., мин</th>
          <th style="text-align:center;padding:10px;border-bottom:1px solid #eef2fb;">Цвет</th>
          <th style="text-align:center;padding:10px;border-bottom:1px solid #eef2fb;">Статус</th>
          <th style="width:180px;padding:10px;border-bottom:1px solid #eef2fb;">Действия</th>
        </tr>
      </thead>
      <tbody>
        {% for s in items %}
        <tr>
          <td style="padding:10px;border-bottom:1px solid #f1f4fb;">{{ s.name }}</td>
          <td style="padding:10px;border-bottom:1px solid #f1f4fb;"><code>{{ s.code }}</code></td>
          <td style="padding:10px;border-bottom:1px solid #f1f4fb;text-align:right;">{{ "{:,}".format(s.price).replace(","," ") }}</td>
          <td style="padding:10px;border-bottom:1px solid #f1f4fb;text-align:right;">{{ s.duration_min }}</td>
          <td style="padding:10px;border-bottom:1px solid #f1f4fb;text-align:center;">
            <span style="display:inline-block;width:22px;height:22px;border-radius:6px;border:1px solid #e3eaf9;background:{{ s.color }}"></span>
          </td>
          <td style="padding:10px;border-bottom:1px solid #f1f4fb;text-align:center;">
            {% if s.is_active %}<span style="color:#27ae60;">Активна</span>{% else %}<span style="color:#c0392b;">Архив</span>{% endif %}
          </td>
          <td style="padding:10px;border-bottom:1px solid #f1f4fb;">
            <a href="{{ url_for('edit_service', id=s._id) }}" style="margin-right:8px;">Редактировать</a>
            <form action="{{ url_for('delete_service', id=s._id) }}" method="post" style="display:inline;" onsubmit="return confirm('Удалить услугу «{{ s.name }}»?');">
              <button type="submit" style="color:#c0392b;background:#fff;border:1px solid #f1d6d6;border-radius:6px;padding:4px 8px;">Удалить</button>
            </form>
          </td>
        </tr>
        {% else %}
        <tr><td colspan="7" style="padding:18px;text-align:center;color:#8592a6;">Пока нет услуг</td></tr>
        {% endfor %}
      </tbody>
    </table>
  </div>
</div>

{% endblock %}
~~~

=== END FILE: .\templates\services.html ===

=== BEGIN FILE: .\templates\sidebar.html ===

~~~html
<aside class="sidebar">
  <div
    class="sidebar-header"
    style="padding: 24px 0 50px 0; display: flex; justify-content: center"
  >
    <img
      src="{{ url_for('static', filename='logo_test123.png') }}"
      alt="ClubStom"
      class="sidebar-logo-img"
    />
  </div>
  <nav>
    <ul>
      <li>
        <a
          href="{{ url_for('calendar_view') }}"
          class="{% if '/calendar' in request.path or request.path == '/' %}active{% endif %}"
        >
          <i class="fa-solid fa-calendar-days"></i> Расписание
        </a>
      </li>
      <li>
        <a
          href="{{ url_for('patients_list') }}"
          class="{% if '/patients' in request.path %}active{% endif %}"
        >
          <i class="fa-solid fa-user-injured"></i> Пациенты
        </a>
      </li>
      <li>
        <a
          href="{{ url_for('doctors') }}"
          class="{% if '/doctors' in request.path %}active{% endif %}"
        >
          <i class="fa-solid fa-user-md"></i> Врачи
        </a>
      </li>
      <li>
        <a
          href="{{ url_for('tasks') }}"
          class="{% if '/tasks' in request.path %}active{% endif %}"
        >
          <i class="fa-solid fa-list-check"></i> Задачи
        </a>
      </li>
      <li>
        <a
          href="{{ url_for('messages') }}"
          class="{% if '/messages' in request.path %}active{% endif %}"
        >
          <i class="fa-solid fa-comments"></i> Сообщения
        </a>
      </li>

      <li>
        <a href="{{ url_for('rooms_list') }}"
          ><i class="fa-solid fa-door-open"></i> Кабинеты</a
        >
      </li>
      <li>
        <a href="{{ url_for('services_list') }}"
          ><i class="fa-solid fa-list-check"></i> Услуги</a
        >
      </li>
      <li>
        <a href="{{ url_for('patients_list') }}"
          ><i class="fa-solid fa-user-injured"></i> Пациенты</a
        >
      </li>
      <li>
        <a
          href="{{ url_for('ztl') }}"
          class="{% if '/ztl' in request.path %}active{% endif %}"
        >
          <i class="fa-solid fa-flask"></i> ЗТЛ
        </a>
      </li>
      <li>
        <a
          href="{{ url_for('partners') }}"
          class="{% if '/partners' in request.path %}active{% endif %}"
        >
          <i class="fa-solid fa-handshake"></i> Партнерская программа
        </a>
      </li>
      <li>
        <a
          href="{{ url_for('finance_report') }}"
          class="{% if '/finance_report' in request.path %}active{% endif %}"
        >
          <i class="fa-solid fa-file-invoice-dollar"></i> Финансовый отчёт
        </a>
      </li>
      <li>
        <a
          href="{{ url_for('logs') }}"
          class="{% if '/logs' in request.path %}active{% endif %}"
        >
          <i class="fa-solid fa-book"></i> Журнал действий
        </a>
      </li>
      <li>
        <a
          href="{{ url_for('data_tools') }}"
          class="{% if '/data_tools' in request.path %}active{% endif %}"
        >
          <i class="fa-solid fa-cloud-arrow-down"></i> Экспорт / Импорт
        </a>
      </li>
    </ul>
  </nav>
</aside>
~~~

=== END FILE: .\templates\sidebar.html ===

=== BEGIN FILE: .\templates\staff.html ===

~~~html
{% extends 'base.html' %}
{% block title %}Сотрудники и структура клиники{% endblock %}
{% block content %}
<div style="max-width:950px; margin:0 auto; background:#fff; border-radius:24px; box-shadow:0 6px 32px rgba(20,40,80,.08); padding:34px 44px;">
    <h2 style="font-size:2.1rem; font-weight:700; margin-bottom:28px;">Структура клиники</h2>
    <table style="width:100%; background:#fff; border-radius:18px; font-size:1.11rem;">
        <thead style="background:#f2f6ff;">
            <tr>
                <th>ФИО</th>
                <th>Должность</th>
                <th>Телефон</th>
                <th>Email</th>
                <th>Роль</th>
                <th>Статус</th>
            </tr>
        </thead>
        <tbody>
        {% for staff in staff_list %}
            <tr style="border-bottom:1px solid #f0f0f0;">
                <td style="font-weight:600;">
                    <img src="{{ staff.avatar_url or '/static/avatars/demo-staff.png' }}" alt="avatar" style="width:36px; height:36px; border-radius:50%; object-fit:cover; margin-right:8px; vertical-align:middle;">
                    {{ staff.full_name }}
                </td>
                <td>{{ staff.position }}</td>
                <td>{{ staff.phone }}</td>
                <td>{{ staff.email }}</td>
                <td>{{ staff.role }}</td>
                <td style="color: {% if staff.status == 'активен' %}#13b949{% else %}#d91f3c{% endif %}; font-weight:600;">
                    {{ staff.status|capitalize }}
                </td>
            </tr>
        {% else %}
            <tr>
                <td colspan="6" style="text-align:center; color:#aaa; padding:26px;">Пока нет сотрудников</td>
            </tr>
        {% endfor %}
        </tbody>
    </table>
</div>
{% endblock %}
~~~

=== END FILE: .\templates\staff.html ===

=== BEGIN FILE: .\templates\tasks.html ===

~~~html
{% extends "base.html" %}
{% block content %}
<h2>Задачи</h2>
<div style="display:flex;gap:14px;align-items:center;margin-bottom:24px;">
  <select class="filter-select">
    <option>Все исполнители</option>
    <!-- ... -->
  </select>
  <select class="filter-select">
    <option>Все приоритеты</option>
    <!-- ... -->
  </select>
  <select class="filter-select">
    <option>Все статусы</option>
    <!-- ... -->
  </select>
  <a href="{{ url_for('add_task') }}" class="btn-add-task">
    <i class="fa fa-plus"></i> Добавить задачу
  </a>
</div>

<div class="tasks-table-wrap">
  <table class="tasks-table">
    <thead>
      <tr>
        <th>Задача</th>
        <th>Описание</th>
        <th>Исполнитель</th>
        <th>Крайний срок</th>
        <th>Статус</th>
        <th>Приоритет</th>
        <th>Действия</th>
      </tr>
    </thead>
    <tbody>
      {% for task in tasks %}
      <tr>
        <td><b>{{ task.title }}</b></td>
        <td>{{ task.description or task.desc or '-' }}</td>
        <td>
          <span class="user-avatar">
            {% if task.assigned_avatar_url %}
              <img src="{{ task.assigned_avatar_url }}" alt="">
            {% else %}
              ?
            {% endif %}
          </span>
          {{ task.assigned_name or 'Без исполнителя' }}
        </td>
        <td>{{ task.due_date or task.deadline or '-' }}</td>
        <td>
          {% if task.status == 'done' %}
            <span class="badge badge-done">Выполнена</span>
          {% elif task.status == 'active' %}
            <span class="badge badge-open">Открыта</span>
          {% elif task.status == 'overdue' %}
            <span class="badge badge-overdue">Просрочена</span>
          {% else %}
            <span class="badge badge-other">{{ task.status or '-' }}</span>
          {% endif %}
        </td>
        <td>
          {% if task.priority == 'high' %}
            <span class="badge badge-high">Высокий</span>
          {% elif task.priority == 'low' %}
            <span class="badge badge-low">Низкий</span>
          {% elif task.priority == 'normal' %}
            <span class="badge badge-norm">Нормальный</span>
          {% else %}
            <span class="badge badge-norm">{{ task.priority or '-' }}</span>
          {% endif %}
        </td>
        <td>
          <a href="{{ url_for('task_card', task_id=task._id) }}" class="btn-more">
            Подробнее <i class="fa fa-angle-right"></i>
          </a>
        </td>
      </tr>
      {% endfor %}
    </tbody>
  </table>
</div>
{% endblock %}

{% block head %}
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
<style>
.btn-add-task {
  display:inline-flex;align-items:center;gap:8px;
  background:linear-gradient(90deg,#2196f3 60%,#21b445 100%);
  color:#fff;font-weight:700;border-radius:10px;
  padding:12px 28px;font-size:1.1em;box-shadow:0 4px 16px #b5e3cb22;
  border:none;text-decoration:none;transition:.14s;background-size:200%;
}
.btn-add-task:hover {background-position:right;color:#fff;}
.btn-add-task i {font-size:1.2em;}
.tasks-table-wrap {
  background:#fff;border-radius:20px;box-shadow:0 4px 26px #d7eafc40;
  padding:22px;margin-top:10px;overflow-x:auto;
}
.tasks-table {width:100%;border-collapse:collapse;font-family:'Montserrat',sans-serif;font-size:1.08em;}
.tasks-table thead tr {background:#f6fbff;}
.tasks-table th, .tasks-table td {padding:13px 10px;}
.tasks-table th {font-size:1.01em;color:#175ecb;font-weight:700;}
.tasks-table tbody tr {transition:background .18s;}
.tasks-table tbody tr:hover {background:#f2f7fe;}
.user-avatar {
  display:inline-block;vertical-align:middle;background:#e6eefb;color:#215fa6;
  border-radius:50%;width:32px;height:32px;text-align:center;line-height:32px;font-weight:700;margin-right:7px;font-size:1.07em;
  box-shadow:0 1px 6px #e3eaf9;
}
.user-avatar img {width:32px;height:32px;border-radius:50%;object-fit:cover;}
.badge {display:inline-flex;align-items:center;gap:6px;padding:3px 12px;border-radius:9px;font-size:0.99em;font-weight:600;}
.badge-done     {background:#e7fbe6; color:#21b445;}
.badge-open     {background:#e7f1fd; color:#2176bd;}
.badge-overdue  {background:#ffeaea; color:#d82222;}
.badge-high     {background:#f0e8ff; color:#7b3ef0;}
.badge-low      {background:#fff9e5; color:#e6ac00;}
.badge-norm     {background:#e8f4ff; color:#1567a0;}
.badge-other    {background:#f4e6ff; color:#ae3ef0;}
.btn-more {
  background:#e9f4ff;color:#2176bd;border-radius:8px;
  border:none;font-weight:600;padding:8px 22px;font-size:1em;transition:.16s;text-decoration:none;display:inline-flex;align-items:center;gap:7px;
}
.btn-more:hover {background:#d6e7fc;color:#105492;}
</style>
{% endblock %}
~~~

=== END FILE: .\templates\tasks.html ===

=== BEGIN FILE: .\templates\topbar.html ===

~~~html
<header class="topbar">
  <div class="topbar-center">
  <div class="topbar-status">
    <span class="topbar-task">
      <i class="fa-solid fa-list-check"></i>
      <b>3</b> открытые задачи
    </span>
    <span class="topbar-rating">
      <i class="fa-solid fa-star" style="color:#f7ba07"></i>
      4.9
    </span>
    <span class="topbar-online">
      <i class="fa-solid fa-user-group"></i>
      <b>5</b> пациентов в клинике
    </span>
    <span class="topbar-news">
      <i class="fa-solid fa-bullhorn"></i>
      <b>Новое:</b> Завтра рабочий день до 17:00
    </span>
  </div>
</div>
  <div class="topbar-right">
    <!-- Колокольчик -->
    <button class="topbar-icon-btn" id="notifBellBtn">
      <i class="fa-regular fa-bell"></i>
      <span class="notif-badge" id="notifBadge" style="display:inline;">3</span>
    </button>

    <!-- Переключатель темы -->
    <button id="themeToggleBtn" class="topbar-icon-btn">
      <i class="fa-solid fa-sun theme-sun" style="color: #ffd700;"></i>
      <i class="fa-solid fa-moon theme-moon" style="display:none; color:#4667b9;"></i>
    </button>

    <!-- Профиль + меню -->
    <div class="profile-block" onclick="toggleProfileMenu()" tabindex="0" style="margin-left:20px; position:relative;">
      <img src="{{ url_for('static', filename='investor_avatar.png') }}" alt="Профиль" class="profile-avatar">
      <span class="profile-name">{{ session.get('user_name', 'Инвестор Инвесторович') }}</span>
      <i class="fa fa-chevron-down" style="margin-left:7px; font-size:0.9em; color:#bbb"></i>
      <div class="profile-menu" id="profileMenu" tabindex="0">
  <a href="{{ url_for('profile') }}"><i class="fa fa-user"></i> Личный кабинет</a>
  <a href="#"><i class="fa fa-cog"></i> Настройки</a>
  <a href="#"><i class="fa fa-question-circle"></i> Помощь</a>
  <a href="{{ url_for('logout') }}"><i class="fa fa-sign-out-alt"></i> Выйти</a>
</div>
    </div>
  </div>
</header>
~~~

=== END FILE: .\templates\topbar.html ===

=== BEGIN FILE: .\templates\xray_room.html ===

~~~html
{% extends "base.html" %}
{% block content %}
<div class="xray-cabinet-wrap">
    <div class="xray-header-row">
        <h2>Рентген-кабинет</h2>
        <a href="{{ url_for('add_xray') }}" class="btn-main">
            <i class="fa fa-plus"></i> Добавить снимок
        </a>
    </div>
    <form method="get" class="xray-filters">
        <select name="patient" class="filter-select">
            <option value="">Все пациенты</option>
            {% for p in patients.values() %}
            <option value="{{ p['_id'] }}">{{ p['full_name'] }}</option>
            {% endfor %}
        </select>
        <select name="doctor" class="filter-select">
            <option value="">Все врачи</option>
            {% for d in doctors.values() %}
            <option value="{{ d['_id'] }}">{{ d['full_name'] }}</option>
            {% endfor %}
        </select>
        <select name="type" class="filter-select">
            <option value="">Все типы</option>
            <option>Панорама</option>
            <option>Прицельный</option>
            <option>КТ</option>
        </select>
        <input type="date" name="date" class="filter-select">
        <button type="submit" class="btn btn-secondary">Фильтр</button>
    </form>

    <div class="xray-table-zone">
        <table class="xray-table">
            <thead>
                <tr>
                    <th>Дата</th>
                    <th>Пациент</th>
                    <th>Врач</th>
                    <th>Тип</th>
                    <th>Превью</th>
                    <th>Заключение</th>
                    <th>Действия</th>
                </tr>
            </thead>
            <tbody>
                {% for x in xrays %}
                <tr>
                    <td style="font-weight:600;font-size:1.09em;">{{ x.date }}</td>
                    <td>
                        <div class="xray-cell">
                            <img src="{{ patients[x.patient_id]['avatar_url'] if x.patient_id in patients else '/static/avatars/demo-patient.png' }}" class="xray-avatar">
                            <div>
                                <b>{{ patients[x.patient_id]['full_name'] if x.patient_id in patients else "—" }}</b>
                                <div class="xray-meta">{{ patients[x.patient_id]['phone'] if x.patient_id in patients else "" }}</div>
                            </div>
                        </div>
                    </td>
                    <td>
                        <div class="xray-cell">
                            <img src="{{ doctors[x.doctor_id]['avatar_url'] if x.doctor_id in doctors else '/static/avatars/demo-doctor.png' }}" class="xray-avatar">
                            <div>
                                <b>{{ doctors[x.doctor_id]['full_name'] if x.doctor_id in doctors else "—" }}</b>
                                <div class="xray-meta">{{ doctors[x.doctor_id]['specialty'] if x.doctor_id in doctors else "" }}</div>
                            </div>
                        </div>
                    </td>
                    <td>
                        <span class="xray-badge {{ x.type }}">{{ x.type }}</span>
                    </td>
                    <td>
                        <img src="{{ x.image_url }}" class="xray-img-preview"
                             onclick="showXrayModal('{{ x.image_url }}', '{{ x.comment|e }}', '{{ x.report|e }}')" alt="X-ray">
                    </td>
                    <td>
                        <span>{{ x.comment or '-' }}</span>
                    </td>
                    <td>
                        <a href="{{ x.image_url }}" download class="btn-download">
                            <i class="fa fa-download"></i> Скачать
                        </a>
                    </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
</div>

<!-- Модалка для увеличения снимка -->
<div class="modal" id="xrayModal" style="display:none;">
    <div class="modal-content" style="max-width:670px;">
        <span class="close" onclick="document.getElementById('xrayModal').style.display='none'">&times;</span>
        <img id="modalXrayImg" src="" style="width:98%;border-radius:14px;box-shadow:0 4px 22px #8fc7fa44;margin-bottom:16px;">
        <div id="modalComment" style="margin-bottom:8px;color:#2563eb;font-weight:500;"></div>
        <div id="modalReport" style="font-size:1.13em;color:#222;"></div>
    </div>
</div>
<script>
function showXrayModal(url, comment, report) {
    document.getElementById('modalXrayImg').src = url;
    document.getElementById('modalComment').innerText = comment || '';
    document.getElementById('modalReport').innerText = report || '';
    document.getElementById('xrayModal').style.display = 'flex';
}
window.onclick = function(e) {
    let modal = document.getElementById('xrayModal');
    if (e.target === modal) modal.style.display = 'none';
}
</script>

{% block head %}
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
<style>
.xray-cabinet-wrap { max-width: 1250px; margin: 0 auto; padding: 38px 0 36px 0; }
.xray-header-row {
    display: flex; align-items: center; justify-content: space-between; margin-bottom: 32px;
}
.xray-filters {
    display: flex; gap: 14px; margin-bottom: 30px; flex-wrap: wrap; align-items: center;
}
.xray-table-zone {
    background: #fff; border-radius: 20px; box-shadow: 0 4px 26px #e3eaf935;
    padding: 22px 26px; margin-top: 0;
}
.xray-table { width: 100%; border-collapse: separate; border-spacing: 0; font-size: 1.07em; }
.xray-table th, .xray-table td { padding: 15px 8px; vertical-align: middle; text-align: center; }
.xray-table th { background: #f4f8ff; color: #145dbd; font-size: 1.04em; }
.xray-table tbody tr { transition: background .13s; border-bottom: 1.5px solid #f1f4fa; }
.xray-table tbody tr:hover { background: #f5fafd; }
.xray-avatar { width: 38px; height: 38px; border-radius: 10px; object-fit: cover; margin-right: 8px; box-shadow:0 2px 8px #b9e4fa22; }
.xray-cell { display: flex; align-items: center; gap: 8px; text-align: left; }
.xray-meta { font-size: 0.98em; color: #8493b5; }
.xray-badge { display: inline-block; padding: 6px 15px; border-radius: 8px; font-size: 0.97em; font-weight: 600; color: #fff; margin-bottom: 2px;}
.xray-badge.Панорама { background: #2196f3; }
.xray-badge.КТ { background: #21b445; }
.xray-badge.Прицельный { background: #ffa600; color: #222;}
.xray-img-preview {
    width: 62px; height: 62px; object-fit: cover; border-radius: 11px;
    box-shadow: 0 2px 10px #a7d4fd33; transition: transform .17s, box-shadow .17s;
    cursor: pointer;
    border: 1.5px solid #e5ecf7;
}
.xray-img-preview:hover {
    transform: scale(1.12) rotate(-2.5deg);
    box-shadow: 0 6px 24px #2196f333;
}
.btn-main {
    display:inline-flex;align-items:center;gap:9px;
    background:linear-gradient(90deg,#2196f3 60%,#21b445 100%);
    color:#fff;font-weight:700;border-radius:10px;
    padding:12px 28px;font-size:1.08em;box-shadow:0 4px 16px #b5e3cb22;
    border:none;text-decoration:none;transition:.14s;background-size:200%;
}
.btn-main:hover {background-position:right;color:#fff;}
.btn-download {
    display: inline-flex; align-items: center; gap: 7px;
    padding: 7px 17px; font-size: 0.97em; font-weight: 600;
    background: #e8f3ff; color: #2576c6; border-radius: 8px; border: none;
    box-shadow: 0 2px 7px #e3eaf933; text-decoration: none;
    transition: background .13s, color .13s;
}
.btn-download:hover { background: #d1eaff; color: #1859b3; }
.modal { align-items: center; justify-content: center; }
.modal-content { animation: xraypop .3s; }
@keyframes xraypop {
    from { opacity:0; transform: scale(0.94);}
    to   { opacity:1; transform: scale(1);}
}
</style>
{% endblock %}
{% endblock %}
~~~

=== END FILE: .\templates\xray_room.html ===

=== BEGIN FILE: .\templates\ztl.html ===

~~~html
{% extends "base.html" %}
{% block content %}
<div class="ztl-cabinet-wrap">
    <div class="ztl-header-row">
        <h2>Зуботехническая лаборатория (ZTL)</h2>
        <a href="{{ url_for('add_ztl') }}" class="btn-add-ztl">
            <i class="fa fa-plus"></i> Добавить работу
        </a>
    </div>

    <form method="get" class="ztl-filters">
        <select name="patient" class="filter-select">
            <option value="">Все пациенты</option>
            {% for p in patients.values() %}
            <option value="{{ p['_id'] }}">{{ p['full_name'] }}</option>
            {% endfor %}
        </select>
        <select name="doctor" class="filter-select">
            <option value="">Все врачи</option>
            {% for d in doctors.values() %}
            <option value="{{ d['_id'] }}">{{ d['full_name'] }}</option>
            {% endfor %}
        </select>
        <select name="type" class="filter-select">
            <option value="">Все типы</option>
            <option>Коронка</option>
            <option>Винир</option>
            <option>Брекеты</option>
            <option>Протез</option>
            <option>Каппа</option>
        </select>
        <select name="status" class="filter-select">
            <option value="">Все статусы</option>
            <option>В работе</option>
            <option>Готово</option>
            <option>Выдано</option>
            <option>Ожидает оплаты</option>
        </select>
        <button type="submit" class="btn btn-secondary">Фильтр</button>
    </form>

    <div class="ztl-cards-row">
        {% for w in ztls %}
        <div class="ztl-card shadow" onclick="showZtlModal({{ w|tojson|safe }}, '{{ patients.get(w.patient_id|string, {}).get('full_name', '') }}', '{{ doctors.get(w.doctor_id|string, {}).get('full_name', '') }}')">
            <div class="ztl-card-img">
                <img src="{{ w.file_url }}" alt="labwork">
            </div>
            <div class="ztl-card-title">{{ patients[w.patient_id].full_name if w.patient_id in patients else '—' }}</div>
            <div class="ztl-card-doctor">Врач: {{ doctors[w.doctor_id].full_name if w.doctor_id in doctors else '—' }}</div>
            <div class="ztl-card-type">
                <span class="ztl-badge-type">{{ w.type }}</span>
                <span class="ztl-badge-status {{ w.status|lower|replace(' ', '_') }}">{{ w.status }}</span>
            </div>
            <div class="ztl-card-dates">
                <span>Дата заказа: {{ w.order_date }}</span>
                <span>Срок: {{ w.due_date }}</span>
            </div>
            <div class="ztl-card-comment">{{ w.comment }}</div>
        </div>
        {% endfor %}
    </div>
</div>

<!-- Модалка деталей работы -->
<div class="modal" id="ztlModal" style="display:none;">
  <div class="modal-content" style="max-width:520px;">
    <span class="close" onclick="document.getElementById('ztlModal').style.display='none'">&times;</span>
    <img id="modalZtlImg" src="" style="width:96%;border-radius:14px;box-shadow:0 4px 20px #8fc7fa55;margin-bottom:14px;">
    <div id="modalZtlInfo" style="font-size:1.1em;"></div>
    <div id="modalZtlComment" style="margin:8px 0 0 0;color:#2563eb;"></div>
  </div>
</div>
<script>
function showZtlModal(w, patient, doctor) {
    document.getElementById('modalZtlImg').src = w.file_url;
    document.getElementById('modalZtlInfo').innerHTML =
      `<b>Пациент:</b> ${patient}<br><b>Врач:</b> ${doctor}<br>
       <b>Тип:</b> ${w.type}<br><b>Статус:</b> ${w.status}<br>
       <b>Дата заказа:</b> ${w.order_date} <br><b>Срок:</b> ${w.due_date}`;
    document.getElementById('modalZtlComment').innerText = w.comment || '';
    document.getElementById('ztlModal').style.display = 'flex';
}
window.onclick = function(e) {
    let modal = document.getElementById('ztlModal');
    if (e.target === modal) modal.style.display = 'none';
}
</script>

{% block head %}
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
<style>
.ztl-cabinet-wrap {
    max-width: 1200px; margin: 0 auto; padding: 38px 0 38px 0;
    display: flex; flex-direction: column; align-items: center;
}
.ztl-header-row {
    display: flex; align-items: center; justify-content: space-between;
    width: 100%; margin-bottom: 24px;
}
.ztl-header-row h2 { font-weight: 700; font-size: 2em; }
.btn-add-ztl {
    display: inline-flex; align-items: center; gap: 10px;
    background: linear-gradient(90deg,#2196f3 60%,#21b445 100%);
    color: #fff; font-weight: 700; border-radius: 10px; padding: 13px 34px; font-size: 1.09em;
    box-shadow: 0 4px 18px #b5e3cb22; border: none; text-decoration: none; transition: .14s; background-size: 200%;
}
.btn-add-ztl:hover { background-position: right; color: #fff; }
.ztl-filters {
    display: flex; gap: 13px; margin-bottom: 32px; flex-wrap: wrap; align-items: center;
    width: 100%; justify-content: center;
}
.ztl-cards-row {
    display: flex; flex-wrap: wrap; gap: 32px; justify-content: flex-start; width: 100%; margin-top: 10px;
}
.ztl-card {
    background: #fff; border-radius: 22px; box-shadow: 0 4px 24px #d7eafc45;
    padding: 23px 28px; min-width: 282px; width: 325px; max-width: 99vw; transition: box-shadow .17s;
    display: flex; flex-direction: column; align-items: flex-start; gap: 5px;
    cursor: pointer;
}
.ztl-card:hover { box-shadow: 0 8px 32px #b5e3cb70; transform: translateY(-2px) scale(1.025);}
.ztl-card-img { width: 100%; display: flex; justify-content: center; margin-bottom: 8px; }
.ztl-card-img img {
    width: 90px; height: 70px; object-fit: cover; border-radius: 11px; box-shadow: 0 2px 14px #a7d4fd44; background: #f4f6fb;
}
.ztl-card-title { font-weight: 600; font-size: 1.08em; color: #2a3555; margin-bottom: 1px;}
.ztl-card-doctor { color: #888; font-size: .98em; margin-bottom: 4px;}
.ztl-card-type { display: flex; gap: 10px; align-items: center; margin-bottom: 4px;}
.ztl-badge-type {
    background: #e9f4ff; color: #2196f3; font-weight: 600; font-size: .97em;
    border-radius: 7px; padding: 4px 13px;
}
.ztl-badge-status {
    background: #e2ebfa; color: #6c6c98; font-weight: 600; font-size: .97em;
    border-radius: 7px; padding: 4px 13px;
}
.ztl-badge-status.в_работе { background: #f4e4ff; color: #a44de0;}
.ztl-badge-status.готово { background: #e6fbe6; color: #21ba45;}
.ztl-badge-status.выдано { background: #e7f1fd; color: #2176bd;}
.ztl-badge-status.ожидает_оплаты { background: #fff6e3; color: #e39a1a;}
.ztl-card-dates { color: #8c8fa5; font-size: .95em; margin-bottom: 1px;}
.ztl-card-dates span { margin-right: 9px;}
.ztl-card-comment { font-size: .97em; color: #2563eb; margin-top: 1px;}
.modal { align-items: center; justify-content: center; }
.modal-content { animation: xraypop .3s; }
@keyframes xraypop {
    from { opacity:0; transform: scale(0.96);}
    to   { opacity:1; transform: scale(1);}
}
</style>
{% endblock %}
{% endblock %}
~~~

=== END FILE: .\templates\ztl.html ===
