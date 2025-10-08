# ======== STD LIB ========
import os, hashlib
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
from datetime import datetime, timedelta, time, timezone
from pathlib import Path
from io import StringIO
import csv

# Если используешь конкретные функции из urllib.parse — лучше импортировать явно: ТЕСТ 07.10.25 +1
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
    make_response,
)
from markupsafe import Markup
from pymongo import MongoClient, ReturnDocument
from bson.objectid import ObjectId  # <-- выбираем ровно этот вариант и больше нигде не дублируем
from routes_transfer import transfer_bp
from production_auth import init_auth, login_required, admin_required, role_required

from functools import wraps
from flask import session, abort, redirect, url_for

# ============================================
# КОНСТАНТЫ ДЛЯ ПЛАНОВ ЛЕЧЕНИЯ
# ============================================

# Статусы планов лечения
TREATMENT_PLAN_STATUS = {
    "draft": "Черновик",
    "pending_approval": "На согласовании",
    "approved": "Одобрен",
    "rejected": "Отклонен",
    "needs_revision": "Требует доработки",
    "completed": "Завершен",
}

# Статусы услуг в плане
SERVICE_STATUS = {"planned": "Запланировано", "completed": "Выполнено"}

# Статусы долгов
DEBT_STATUS = {"unpaid": "Не оплачен", "partially_paid": "Частично оплачен", "paid": "Оплачен"}

# Статусы платежей
PAYMENT_STATUS = {"completed": "Завершен", "pending_confirmation": "Ожидает подтверждения"}

# Статусы авансов
ADVANCE_STATUS = {"active": "Активен", "depleted": "Использован"}


app = Flask(__name__)

# === TEMP-A1: calendar_view with debug headers (remove later) ===============
CAL_TPL_PATH = os.path.join(app.root_path, "templates", "calendar.html")

@app.route("/calendar")
def calendar_view():
    return render_template("calendar.html")


# Отключить кэш шаблонов для разработки
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0
app.jinja_env.auto_reload = True
app.jinja_env.cache = {}

app.config.setdefault("SEED_ON_STARTUP", False)
app.secret_key = os.getenv("SECRET_KEY", "dev")


@app.context_processor
def inject_user():
    """Добавляет данные пользователя во все шаблоны"""
    all_users = list(
        db.users.find({}, {"full_name": 1, "username": 1, "avatar": 1, "role": 1}).sort(
            "full_name", 1
        )
    )
    return dict(
        current_user=session.get("user", {}), role=session.get("role", "user"), all_users=all_users
    )


# правильно: просто вызываем
init_auth(app)


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


def write_audit_log(action, obj_type, obj_id=None, comment="", details=None, patient_id=None):
    """Подробное логирование для аудита медицинской системы"""
    log_entry = {
        "timestamp": datetime.utcnow() + timedelta(hours=3),  # MSK (UTC+3)
        "timestamp_local": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
        "user_id": session.get("user_id"),
        "user_name": session.get("user_name", "Неизвестный"),
        "user_role": session.get("user_role", ""),
        "ip_address": request.remote_addr,
        "user_agent": request.headers.get("User-Agent", "")[:200],  # ограничим длину
        "action": action,  # create, update, delete, view, export, login, logout
        "object_type": obj_type,  # patient, appointment, service, user
        "object_id": str(obj_id) if obj_id else None,
        "patient_id": str(patient_id) if patient_id else None,
        "comment": comment,
        "details": details or {},
        "url": request.url,
        "method": request.method,
    }

    db.audit_logs.insert_one(log_entry)
    return log_entry

# === RBAC helpers: who can modify appointments ===
def current_role() -> str:
    # совместимость с разными версиями сессии
    return session.get("user_role") or session.get("role") or "user"

def _lookup_current_doctor_id():
    """Найти ObjectId врача, связанного с текущим user_id (users.login == doctors.email)."""
    uid = session.get("user_id")
    if not uid:
        return None
    user_doc = db.users.find_one({"_id": ObjectId(uid)})
    if not user_doc:
        return None
    doc = db.doctors.find_one({"email": user_doc.get("login", "")}, {"_id": 1})
    return doc["_id"] if doc else None

def can_modify_appointment(appt: dict) -> bool:
    role = current_role()
    if role in ("admin", "owner", "chief_doctor", "registrar"):
        return True
    if role == "doctor":
        did = _lookup_current_doctor_id()
        return bool(did and appt and appt.get("doctor_id") == did)
    return False
# === /RBAC helpers ===

@app.route("/switch-user/<user_id>")
@login_required
def switch_user(user_id):
    """Быстрая смена пользователя"""
    try:
        user = db.users.find_one({"_id": ObjectId(user_id)})
        if not user:
            flash("Пользователь не найден", "danger")
            return redirect("/calendar")

        session["user_id"] = str(user["_id"])
        session["username"] = user.get("username", user.get("login"))
        session["role"] = user.get("role", "user")
        session["user"] = {
            "login": user.get("login") or user.get("username"),
            "username": user.get("username"),
            "full_name": user.get("full_name") or user.get("name"),
            "role": user.get("role", "user"),
            "avatar": user.get("avatar", "default.jpg"),
            "active": True,
        }

        flash(f"Вы вошли как {user.get('full_name')}", "success")
        return redirect("/calendar")

    except Exception as e:
        flash(f"Ошибка: {e}", "danger")
        return redirect("/calendar")


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

app.config["DB"] = db
app.config["USERS_COLLECTION"] = db["users"]


@app.context_processor
def inject_metrics():
    """Автоматически добавляет metrics во все шаблоны"""
    try:
        total_rooms = db.rooms.count_documents({})
        now = datetime.utcnow()
        busy_rooms = db.appointments.count_documents({"start": {"$lte": now}, "end": {"$gte": now}})
        free_rooms = max(0, total_rooms - busy_rooms)

        return {"metrics": {"total_rooms": total_rooms, "free_rooms": free_rooms}}
    except:
        return {"metrics": {"total_rooms": 0, "free_rooms": 0}}


# --- Rooms bootstrap (идемпотентно) ---
from datetime import datetime

DEFAULT_ROOMS = ["Детский", "Ортопедия", "Хирургия", "Ортодонтия", "Терапия", "Эндодонтия"]


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

        # --- Rooms bootstrap (идемпотентно) ---


# запускать автосоздание кабинетов только явно по флагу
if app.config.get("SEED_ON_STARTUP", True):
    try:
        ensure_rooms()
    except Exception as e:
        app.logger.exception("ensure_rooms failed: %s", e)

# --- Админ/сид блюпринт: /admin/seed и /api/dicts ---
from routes_admin_seed import admin_seed_bp

app.register_blueprint(admin_seed_bp)  # без префикса: /admin/seed и /api/dicts
app.logger.info("Blueprint admin_seed_bp registered")

app.register_blueprint(transfer_bp)
app.logger.info("Blueprint transfer_bp registered")


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
@login_required
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


@app.route("/api/patients/<patient_id>/bonus")
def api_patient_bonus(patient_id):
    """API для получения баланса бонусов пациента"""
    try:
        patient_oid = ObjectId(patient_id)
        patient = db.patients.find_one({"_id": patient_oid})

        if not patient:
            return jsonify({"success": False, "error": "Пациент не найден"})

        bonus_balance = patient.get("bonus_balance", 0)

        return jsonify(
            {
                "success": True,
                "bonus_balance": bonus_balance,
                "patient_name": patient.get("full_name", ""),
            }
        )
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@app.route("/api/patients/<patient_id>/bonus/add", methods=["POST"])
@login_required
def api_patient_bonus_add(patient_id):
    """Начисление бонусов пациенту"""
    try:
        patient_oid = ObjectId(patient_id)
        patient = db.patients.find_one({"_id": patient_oid})
        if not patient:
            return jsonify({"ok": False, "error": "Пациент не найден"})

        data = request.get_json()
        amount = int(data.get("amount", 0))
        comment = data.get("comment", "Ручное начисление")

        if amount <= 0:
            return jsonify({"ok": False, "error": "Сумма должна быть положительной"})

        # Обновляем баланс
        db.patients.update_one({"_id": patient_oid}, {"$inc": {"bonus_balance": amount}})

        # Записываем в историю
        db.bonus_history.insert_one(
            {
                "patient_id": patient_oid,
                "operation": "manual_add",
                "amount": amount,
                "comment": comment,
                "ts": datetime.utcnow(),
                "user": session.get("username", "admin"),
            }
        )

        return jsonify({"ok": True, "new_balance": patient.get("bonus_balance", 0) + amount})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})


@app.route("/api/patients/<patient_id>/bonus/withdraw", methods=["POST"])
@login_required
def api_patient_bonus_withdraw(patient_id):
    """Списание бонусов у пациента"""
    try:
        patient_oid = ObjectId(patient_id)
        patient = db.patients.find_one({"_id": patient_oid})
        if not patient:
            return jsonify({"ok": False, "error": "Пациент не найден"})

        data = request.get_json()
        amount = int(data.get("amount", 0))
        comment = data.get("comment", "Ручное списание")

        current_balance = patient.get("bonus_balance", 0)

        if amount <= 0:
            return jsonify({"ok": False, "error": "Сумма должна быть положительной"})

        if amount > current_balance:
            return jsonify({"ok": False, "error": "Недостаточно бонусов"})

        # Обновляем баланс
        db.patients.update_one({"_id": patient_oid}, {"$inc": {"bonus_balance": -amount}})

        # Записываем в историю
        db.bonus_history.insert_one(
            {
                "patient_id": patient_oid,
                "operation": "manual_withdraw",
                "amount": -amount,
                "comment": comment,
                "ts": datetime.utcnow(),
                "user": session.get("username", "admin"),
            }
        )

        return jsonify({"ok": True, "new_balance": current_balance - amount})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})


@app.route("/api/patients/<patient_id>/bonus/history")
@login_required
def api_patient_bonus_history(patient_id):
    """История бонусных операций пациента"""
    try:
        patient_oid = ObjectId(patient_id)

        history = list(db.bonus_history.find({"patient_id": patient_oid}).sort("ts", -1).limit(50))

        items = []
        for h in history:
            items.append(
                {
                    "date": h.get("ts").strftime("%d.%m.%Y %H:%M") if h.get("ts") else "—",
                    "amount": h.get("amount", 0),
                    "comment": h.get("comment", ""),
                    "operation": h.get("operation", ""),
                }
            )

        return jsonify({"ok": True, "items": items})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})


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

@app.get("/api/patients/<pid>/appointments")
@login_required
def api_patient_appointments(pid):
    try:
        pid_oid = ObjectId(pid)
    except Exception:
        return jsonify({"items": []})

    cur = db.appointments.find({"patient_id": pid_oid}).sort("start", -1)

    doc_map = {str(d["_id"]): d.get("full_name", "") for d in db.doctors.find({}, {"full_name": 1})}
    srv_map = {str(s["_id"]): s.get("name", "") for s in db.services.find({}, {"name": 1})}
    room_map= {str(r["_id"]): r.get("name", "") for r in db.rooms.find({}, {"name": 1})}

    items = []
    for a in cur:
        did = str(a.get("doctor_id") or "")
        sid = str(a.get("service_id") or "")
        rid = str(a.get("room_id") or "")
        s = to_dt(a.get("start"))
        e = to_dt(a.get("end"))
        items.append({
            "id": str(a["_id"]),
            "start": s.isoformat() if s else None,
            "end":   e.isoformat() if e else None,
            "doctor": doc_map.get(did, ""),
            "service": srv_map.get(sid, ""),
            "room": room_map.get(rid, ""),
            "status": a.get("status", "scheduled"),
        })
    return jsonify({"items": items})



# ============================================================================
# API: Treatment Plans (Планы лечения)
# ============================================================================


@app.route("/api/patients/<patient_id>/treatment-plans")
@login_required
def api_patient_treatment_plans(patient_id):
    """API для получения планов лечения пациента"""
    try:
        patient_oid = ObjectId(patient_id)
    except:
        return jsonify({"error": "Invalid patient ID"}), 400

    # Получаем все планы пациента, отсортированные по дате создания
    plans = list(db.treatment_plans.find({"patient_id": patient_oid}).sort("created_at", -1))

    result = []
    for plan in plans:
        # ИСПРАВЛЕНО: Получаем врача из db.users
        doctor = db.users.find_one({"_id": plan["doctor_id"]}) if plan.get("doctor_id") else None

        # Рассчитываем общую стоимость
        total_cost = sum(service.get("price", 0) for service in plan.get("services", []))

        # Считаем выполненные услуги
        completed_services = sum(
            1 for s in plan.get("services", []) if s.get("status") == "completed"
        )
        total_services = len(plan.get("services", []))

        # ИСПРАВЛЕНО: Конвертируем ObjectId в строки для services
        services_clean = []
        for s in plan.get("services", []):
            services_clean.append(
                {
                    "service_id": str(s.get("service_id")) if s.get("service_id") else None,
                    "name": s.get("service_name", ""),
                    "price": s.get("price", 0),
                    "status": s.get("status", "planned"),
                    "comment": s.get("comment", ""),
                }
            )

        result.append(
            {
                "_id": str(plan["_id"]),
                "status": plan.get("status", "draft"),
                "created_at": (
                    plan.get("created_at").isoformat() if plan.get("created_at") else None
                ),
                "approved_at": (
                    plan.get("approved_at").isoformat() if plan.get("approved_at") else None
                ),
                "doctor_name": doctor.get("full_name") if doctor else "Не указан",
                "diagnosis": plan.get("diagnosis", ""),
                "total_cost": total_cost,
                "services_count": total_services,
                "completed_count": completed_services,
                "services": services_clean,  # Очищенный массив
            }
        )

    return jsonify(result)


@app.route("/patients/<id>")
def patient_card_page(id):
    patient_oid = ObjectId(id)
    patient = db.patients.find_one({"_id": patient_oid})
    try:
        oid = ObjectId(id)
    except Exception:
        flash("Некорректный ID пациента.", "danger")
        return redirect(url_for("patients_list"))

    p = db.patients.find_one({"_id": oid})
    if not p:
        flash("Пациент не найден.", "danger")
        return redirect(url_for("patients_list"))

    # Нормализуем поля для шаблона
    patient = {
        "_id": str(p["_id"]),
        "full_name": p.get("full_name", ""),
        "phone": p.get("phone", ""),
        "email": p.get("email", ""),
        "birthdate": p.get("birthdate", ""),
        "card_no": p.get("card_no", ""),
        "created_at": p.get("created_at"),
        "notes": p.get("notes", ""),
        "bonus_balance": p.get("bonus_balance", 0),
        "referred_by_patient_id": p.get("referred_by_patient_id"),
        "referred_by_name": p.get("referred_by_name"),
    }

    # История записей
    appointments = []
    for a in db.appointments.find({"patient_id": oid}).sort("start", -1).limit(20):
        # Получаем данные врача и услуги
        doctor = db.doctors.find_one({"_id": a.get("doctor_id")}) if a.get("doctor_id") else None
        service = (
            db.services.find_one({"_id": a.get("service_id")}) if a.get("service_id") else None
        )

        appointments.append(
            {
                "start": a.get("start"),
                "doctor_name": doctor.get("full_name", "") if doctor else "",
                "service_name": service.get("name", "") if service else "",
                "status_key": a.get("status_key", "scheduled"),
                "status_title": a.get("status_key", "Запланирована"),
                "cost": service.get("price", "") if service else "",
            }
        )

    # ИСПРАВЛЕНО: Читаем долг и депозит из БД
    finance = {
        "total_paid": 0,  # TODO: рассчитать из ledger
        "total_debt": p.get("debt_balance", 0),
        "deposit": p.get("deposit_balance", 0),
    }

    referred_patients_count = db.patients.count_documents({"referred_by_patient_id": patient_oid})

    # НОВОЕ: Получить текущую запись (сегодня)
    from datetime import datetime, timedelta

    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start + timedelta(days=1)

    current_appointment = db.appointments.find_one(
        {"patient_id": oid, "start": {"$gte": today_start, "$lt": today_end}}  # ← ИСПРАВЛЕНО
    )

    # Если есть запись, получить информацию об услуге
    if current_appointment and current_appointment.get("service_id"):
        service = db.services.find_one({"_id": current_appointment["service_id"]})
        if service:
            current_appointment["service_name"] = service.get("name", "")
            current_appointment["service_price"] = service.get("price", 0)

    # Получить все услуги для модального окна
    all_services = list(db.services.find({"is_active": True}).sort("name", 1))

    # Получить роль из сессии
    user_role = (session.get("role") or session.get("user", {}).get("role") or "").strip().lower()

    return render_template(
        "patient_card.html",
        patient=patient,
        appointments=appointments,
        finance=finance,
        referred_patients_count=referred_patients_count,
        current_appointment=current_appointment,  # НОВОЕ
        all_services=all_services,  # НОВОЕ
        user_role=user_role,  # НОВОЕ
    )


@app.route("/patients/<patient_id>/current-visit/complete", methods=["POST"])
@login_required
def complete_current_visit(patient_id):
    """Завершение услуг текущего приёма"""
    try:
        from bson.objectid import ObjectId
        from datetime import datetime

        # Проверка роли
        user = db.users.find_one({"_id": ObjectId(session.get("user_id"))})
        if not user or user.get("role") not in ["doctor", "owner"]:
            flash("Доступ запрещён", "error")
            return redirect(url_for("patient_card_page", id=patient_id))

        patient_oid = ObjectId(patient_id)
        patient = db.patients.find_one({"_id": patient_oid})

        if not patient:
            flash("Пациент не найден", "error")
            return redirect(url_for("patients_list"))

        # Получить отмеченные услуги
        service_ids = request.form.getlist("service_ids[]")

        if not service_ids:
            flash("Не выбрано ни одной услуги", "warning")
            return redirect(url_for("patient_card_page", id=patient_id))

        # Создать долги за каждую услугу
        total_debt = 0
        created_debts = []

        for service_id_str in service_ids:
            service_id = ObjectId(service_id_str)
            service = db.services.find_one({"_id": service_id})

            if not service:
                continue

            # Получить комментарий
            comment_key = f"comment_{service_id_str}"
            comment = request.form.get(comment_key, "").strip()

            # Определить цену (льготная или обычная)
            if patient.get("use_preferential_pricing") and service.get("employee_price"):
                price = int(service.get("employee_price", 0))
            else:
                price = int(service.get("price", 0))

            # Создать долг
            debt = {
                "patient_id": patient_oid,
                "treatment_plan_id": None,  # Нет плана - текущий приём
                "service_id": service_id,
                "service_name": service.get("name", ""),
                "service_comment": comment,
                "amount": price,
                "status": "unpaid",
                "paid_amount": 0,
                "remaining_amount": price,
                "created_at": datetime.now(),
                "created_by_doctor_id": ObjectId(session.get("user_id")),
            }

            result = db.debts.insert_one(debt)
            created_debts.append(result.inserted_id)
            total_debt += price

        # Обновить debt_balance пациента
        db.patients.update_one({"_id": patient_oid}, {"$inc": {"debt_balance": total_debt}})

        # Логирование
        db.audit_logs.insert_one(
            {
                "action": "complete_current_visit",
                "user_id": ObjectId(session.get("user_id")),
                "user_name": user.get("full_name", ""),
                "patient_id": patient_oid,
                "patient_name": patient.get("full_name", ""),
                "details": {
                    "services_count": len(service_ids),
                    "total_amount": total_debt,
                    "debt_ids": [str(d) for d in created_debts],
                },
                "timestamp": datetime.now(),
            }
        )

        flash(
            f"✅ Завершено услуг: {len(service_ids)}. Создан долг: {total_debt:,} ₽".replace(
                ",", " "
            ),
            "success",
        )
        return redirect(url_for("patient_card_page", id=patient_id))

    except Exception as e:
        flash(f"Ошибка при завершении приёма: {str(e)}", "error")
        return redirect(url_for("patient_card_page", id=patient_id))


# --- /Rooms bootstrap ---

# Регистрируем блюпринты
from routes_schedule import bp as schedule_bp

app.register_blueprint(schedule_bp, url_prefix="/schedule")

# --- финмодуль: импорт и регистрация блюпринта ---
try:
    # в routes_finance.py блюпринт называется bp
    from routes_finance import bp as bp_finance
    from routes_bonus import bp as bp_bonus

    # url_prefix уже задан внутри файла: Blueprint("finance", ..., url_prefix="/finance")
    app.register_blueprint(bp_finance)
    app.register_blueprint(bp_bonus)
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
@login_required
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


# === TEMP-A1: Redirect /schedule -> /calendar (remove later) ================
@app.route("/schedule")
def schedule_redirect():
    qs = request.query_string.decode() if request.query_string else ""
    target = url_for("calendar_view")
    if qs:
        target += "?" + qs
    return redirect(target, code=302)


@app.route("/api/rooms/status_now")
@login_required
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
@login_required
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
@login_required
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


# Добавьте этот код в main.py после определения декоратора login_required


@app.route("/api/patients/export/csv")
@login_required
def download_patients_csv():
    """Экспорт пациентов в CSV"""
    patients = list(db.patients.find().sort("full_name", 1))

    output = io.StringIO()
    writer = csv.writer(output, delimiter=";")

    writer.writerow(["ФИО", "Телефон", "Email", "Дата рождения", "Карта №", "Заметки"])

    for p in patients:
        writer.writerow(
            [
                p.get("full_name", ""),
                p.get("phone", ""),
                p.get("email", ""),
                p.get("birthdate", ""),
                p.get("card_no", ""),
                p.get("notes", ""),
            ]
        )

    response = Response(
        output.getvalue(),
        mimetype="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f"attachment; filename=patients_{datetime.now().strftime('%Y%m%d')}.csv"
        },
    )
    return response


@app.route("/api/patients/export/excel")
@login_required
def download_patients_excel():
    """Экспорт пациентов в Excel формат"""
    patients = list(db.patients.find().sort("full_name", 1))

    output = io.StringIO()
    writer = csv.writer(output, delimiter="\t")

    writer.writerow(["ФИО", "Телефон", "Email", "Дата рождения", "Карта №", "Заметки"])

    for p in patients:
        writer.writerow(
            [
                p.get("full_name", ""),
                p.get("phone", ""),
                p.get("email", ""),
                p.get("birthdate", ""),
                p.get("card_no", ""),
                p.get("notes", ""),
            ]
        )

    response = Response(
        output.getvalue(),
        mimetype="application/vnd.ms-excel",
        headers={
            "Content-Disposition": f"attachment; filename=patients_{datetime.now().strftime('%Y%m%d')}.xls"
        },
    )
    return response


@app.route("/patients/import", methods=["GET", "POST"])
@login_required
def import_patients():
    if request.method == "GET":
        return render_template("import_patients.html")

    file = request.files.get("file")
    if not file or not file.filename:
        flash("Файл не выбран", "danger")
        return redirect(url_for("import_patients"))

    update_existing = bool(request.form.get("update_existing"))

    try:
        if file.filename.endswith(".csv"):
            # Обработка CSV
            import pandas as pd

            df = pd.read_csv(file, delimiter=";")
        else:
            # Обработка Excel
            import pandas as pd

            df = pd.read_excel(file)

        imported = 0
        updated = 0
        errors = []

        for index, row in df.iterrows():
            try:
                patient_data = {
                    "full_name": str(row.get("ФИО", "")).strip(),
                    "phone": str(row.get("Телефон", "")).strip(),
                    "email": str(row.get("Email", "")).strip(),
                    "birthdate": str(row.get("Дата рождения", "")).strip(),
                    "notes": str(row.get("Заметки", "")).strip(),
                    "created_at": datetime.utcnow(),
                }

                # Пропускаем пустые записи
                if not patient_data["full_name"]:
                    continue

                # Проверяем существующего пациента по телефону
                if patient_data["phone"] and update_existing:
                    existing = db.patients.find_one({"phone": patient_data["phone"]})
                    if existing:
                        db.patients.update_one({"_id": existing["_id"]}, {"$set": patient_data})
                        updated += 1
                        continue

                # Создаем нового пациента
                db.patients.insert_one(patient_data)
                imported += 1

            except Exception as e:
                errors.append(f"Строка {index + 2}: {str(e)}")

        if errors:
            flash(
                f"Импортировано: {imported}, обновлено: {updated}. Ошибки: {len(errors)}", "warning"
            )
        else:
            flash(f"Успешно импортировано: {imported}, обновлено: {updated}", "success")

        write_log(
            "import",
            comment=f"Импорт пациентов: {imported} новых, {updated} обновлено",
            obj="Пациенты",
        )

    except Exception as e:
        flash(f"Ошибка обработки файла: {str(e)}", "danger")

    return redirect(url_for("patients_list"))


@app.route("/dashboard")
@login_required
def dashboard():
    return redirect(url_for("calendar_view"))


# --- Маршрут: Добавление события ---
@app.route("/add_event", methods=["GET", "POST"])
@login_required
def add_event():
    # Справочники для формы
    doctors = list(db.doctors.find({}, {"full_name": 1}).sort("full_name", 1))
    patients = list(db.patients.find({}, {"full_name": 1}).sort("full_name", 1))
    services = list(
        db.services.find({"is_active": True}, {"name": 1, "duration_min": 1, "price": 1}).sort(
            "name", 1
        )
    )
    rooms = list(db.rooms.find({}, {"name": 1, "status": 1}).sort("name", 1))

    if request.method == "POST":
        # 1) Читаем поля
        doctor_id_s = request.form.get("doctor_id") or ""
        patient_id_s = request.form.get("patient_id") or ""
        service_id_s = request.form.get("service_id") or ""
        room_id_s = request.form.get("room_id") or ""
        start_s = request.form.get("start") or ""
        end_s = request.form.get("end") or ""
        comment = (request.form.get("comment") or "").strip()
        status_key = (request.form.get("status_key") or "scheduled").strip()
        payment_method = request.form.get("payment_method", "later")

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
        print(f"[DEBUG] Appointment created with ID: {appt['_id']}")

        # TODO: БЛОК 2.1 - АВТОСОЗДАНИЕ LEDGER ОТКЛЮЧЕНО
        # Теперь долг создается только при завершении приема
        # Старый код закомментирован (строки 1841-1961)

        # 7) Создаём финансовую запись в ledger с поддержкой бонусов
        # try:
        # Получаем цену услуги
        # service = db.services.find_one({"_id": service_id}, {"name": 1, "price": 1})
        # if service and service.get("price"):
        # service_price = int(service["price"])

        # Обработка бонусной оплаты
        # if payment_method == "bonus":
        # Проверка баланса бонусов
        # patient = db.patients.find_one({"_id": patient_id})
        # current_bonus = patient.get("bonus_balance", 0)

        # if current_bonus < service_price:
        # flash(
        # f"Недостаточно бонусов. Доступно: {current_bonus}, требуется: {service_price}",
        # "danger",
        # )
        # return render_template(
        # "add_event.html",
        # doctors=doctors,
        # patients=patients,
        # services=services,
        # rooms=rooms,
        # )

        # Списание бонусов
        # db.patients.update_one(
        # {"_id": patient_id}, {"$inc": {"bonus_balance": -service_price}}
        # )

        # Запись в историю бонусов
        # db.bonus_history.insert_one(
        # {
        # "patient_id": patient_id,
        # "operation": "withdraw",
        # "amount": service_price,
        # "comment": f"Оплата услуги: {service['name']}",
        # "ts": datetime.utcnow(),
        # }
        # )

        # Создание ledger записи (всегда pending)
        # ledger_entry = {
        # "patient_id": patient_id,
        # "appointment_id": appt["_id"],
        # "service_id": service_id,
        # "kind": "service_charge",
        # "amount": service_price,
        # "description": f"Услуга: {service['name']}",
        # "status": "pending",
        # "ts": datetime.utcnow(),
        # "ts_iso": datetime.utcnow().strftime("%Y-%m-%dT%H:%M"),
        # }

        # Логируем бонусную оплату
        # write_audit_log(
        # "create",
        # "ledger",
        # obj_id=str(appt["_id"]),
        # comment=f"Оплата бонусами: {service['name']} - {service_price}₽",
        # patient_id=str(patient_id),
        # )

        # elif payment_method != "later":
        # Обычная оплата (cash, alpha, sber)
        # ledger_entry = {
        # "patient_id": patient_id,
        # "appointment_id": appt["_id"],
        # "service_id": service_id,
        # "kind": "income",
        # "source": payment_method,
        # "amount": service_price,
        # "description": f"Оплата {payment_method}: {service['name']}",
        # "status": "completed",
        # "ts": datetime.utcnow(),
        # "ts_iso": datetime.utcnow().strftime("%Y-%m-%dT%H:%M"),
        # }

        # Логируем обычную оплату
        # write_audit_log(
        # "create",
        # "ledger",
        # obj_id=str(appt["_id"]),
        # comment=f"Оплата {payment_method}: {service['name']} - {service_price}₽",
        # patient_id=str(patient_id),
        # )

        # else:
        # Оплата позже
        # ledger_entry = {
        # "patient_id": patient_id,
        # "appointment_id": appt["_id"],
        # "service_id": service_id,
        # "kind": "service_charge",
        # "amount": service_price,
        # "description": f"Услуга: {service['name']}",
        # "status": "pending",
        # "ts": datetime.utcnow(),
        # "ts_iso": datetime.utcnow().strftime("%Y-%m-%dT%H:%M"),
        # }

        # Логируем начисление услуги
        # write_audit_log(
        # "create",
        # "ledger",
        # obj_id=str(appt["_id"]),
        # comment=f"Начисление услуги: {service['name']} - {service_price}₽",
        # patient_id=str(patient_id),
        # )

        # Сохраняем ledger запись
        # db.ledger.insert_one(ledger_entry)
        # print(
        # f"[DEBUG] SUCCESS: Created ledger entry: {service['name']} - {service_price}₽"
        # )

        # except Exception as e:
        # print(f"[ERROR] LEDGER FAILED: {str(e)}")
        # import traceback

        # traceback.print_exc()

        # 8) Обновим статус кабинета
        try:
            recalc_room_status(room_id)
        except Exception:
            pass

        flash("Запись создана.", "success")
        return redirect(url_for("calendar_view"))

    # GET запрос - показываем форму
    total_rooms = db.rooms.count_documents({})
    now = datetime.utcnow()
    busy_rooms = db.appointments.count_documents({"start": {"$lte": now}, "end": {"$gte": now}})
    free_rooms = max(0, total_rooms - busy_rooms)

    return render_template(
        "add_event.html",
        doctors=doctors,
        patients=patients,
        services=services,
        rooms=rooms,
        metrics={"total_rooms": total_rooms, "free_rooms": free_rooms},
    )


@app.route("/edit_event/<event_id>", methods=["GET", "POST"])
def edit_event(event_id):
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
@login_required
# @role_required("admin")  # временно отключено
def doctors():
    doctors = list(db.doctors.find())
    for d in doctors:
        d["_id"] = str(d["_id"])
    return render_template("doctors.html", doctors=doctors)


@app.route("/add_doctor", methods=["GET", "POST"])
@login_required
def add_doctor():
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


@app.route("/finance/debtors")
@login_required
def finance_debtors():
    """Страница списка должников"""
    # Получаем всех пациентов с долгами
    debtors = list(
        db.patients.find(
            {"debt_balance": {"$gt": 0}},
            {"full_name": 1, "phone": 1, "card_no": 1, "debt_balance": 1},
        ).sort("debt_balance", -1)
    )  # Сортировка по убыванию долга

    # Общая сумма долгов
    total_debt = sum(p.get("debt_balance", 0) for p in debtors)

    return render_template(
        "finance/debtors.html", debtors=debtors, total_debt=total_debt, count=len(debtors)
    )


@app.route("/api/reports/doctors_revenue", methods=["GET"])
@login_required
@role_required(["admin", "registrar"])
def api_doctors_revenue_report():
    """Отчет по доходам врачей"""

    # Параметры фильтрации
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")

    # Базовый пайплайн агрегации
    pipeline = [
        # Соединяем ledger с appointments
        {
            "$lookup": {
                "from": "appointments",
                "localField": "appointment_id",
                "foreignField": "_id",
                "as": "appointment",
            }
        },
        {"$unwind": "$appointment"},
        # Соединяем с врачами
        {
            "$lookup": {
                "from": "doctors",
                "localField": "appointment.doctor_id",
                "foreignField": "_id",
                "as": "doctor",
            }
        },
        {"$unwind": "$doctor"},
        # Группируем по врачам
        {
            "$group": {
                "_id": "$doctor._id",
                "doctor_name": {"$first": "$doctor.full_name"},
                "total_revenue": {"$sum": "$amount"},
                "appointments_count": {"$sum": 1},
                "avg_check": {"$avg": "$amount"},
            }
        },
        # Сортируем по доходу
        {"$sort": {"total_revenue": -1}},
    ]

    # Фильтр по датам если указан
    if start_date and end_date:
        try:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            end_dt = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)

            pipeline.insert(
                0, {"$match": {"ts": {"$gte": start_dt, "$lt": end_dt}, "kind": "payment"}}
            )
        except ValueError:
            pass
    else:
        pipeline.insert(0, {"$match": {"kind": "payment"}})

    try:
        results = list(db.ledger.aggregate(pipeline))

        # Форматируем результат
        doctors_revenue = []
        for result in results:
            doctors_revenue.append(
                {
                    "doctor_id": str(result["_id"]),
                    "doctor_name": result["doctor_name"],
                    "total_revenue": int(result["total_revenue"]),
                    "appointments_count": result["appointments_count"],
                    "avg_check": int(result["avg_check"]),
                }
            )

        return jsonify(
            {
                "ok": True,
                "period": f"{start_date} - {end_date}" if start_date and end_date else "Все время",
                "doctors": doctors_revenue,
                "total_doctors": len(doctors_revenue),
            }
        )

    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


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
@login_required
def logs():
    """Улучшенный журнал действий с фильтрацией и экспортом"""
    write_audit_log("view", "logs", comment="Просмотр журнала действий")

    # Параметры фильтрации
    search = request.args.get("search", "")
    user_filter = request.args.get("user", "")
    action_filter = request.args.get("action", "")
    date_from = request.args.get("date_from", "")
    date_to = request.args.get("date_to", "")
    page = int(request.args.get("page", 1))
    per_page = 50

    # Построение фильтра для MongoDB
    filter_dict = {}
    if search:
        filter_dict["$or"] = [
            {"action": {"$regex": search, "$options": "i"}},
            {"comment": {"$regex": search, "$options": "i"}},
            {"obj": {"$regex": search, "$options": "i"}},
        ]
    if user_filter:
        filter_dict["username"] = {"$regex": user_filter, "$options": "i"}
    if action_filter:
        filter_dict["action"] = {"$regex": action_filter, "$options": "i"}
    if date_from or date_to:
        date_filter = {}
        if date_from:
            date_filter["$gte"] = datetime.strptime(date_from, "%Y-%m-%d")
        if date_to:
            date_filter["$lte"] = datetime.strptime(date_to + " 23:59:59", "%Y-%m-%d %H:%M:%S")
        filter_dict["datetime"] = date_filter

    # Получение записей с пагинацией
    total_logs = db.logs.count_documents(filter_dict)
    logs = list(
        db.logs.find(filter_dict).sort("datetime", -1).skip((page - 1) * per_page).limit(per_page)
    )

    # Обогащение данных пользователей
    for log in logs:
        if "user_id" in log:
            user = db.users.find_one({"_id": ObjectId(log["user_id"])})
            if user:
                log["user_name"] = f"{user.get('first_name', '')} {user.get('last_name', '')}"
                log["user_role"] = user.get("role", "Неизвестно")
            else:
                log["user_name"] = log.get("username", "Неизвестный пользователь")
                log["user_role"] = "Неизвестно"
        else:
            log["user_name"] = log.get("username", "Системное действие")
            log["user_role"] = "Система"

    # Информация для пагинации
    total_pages = (total_logs - 1) // per_page + 1 if total_logs > 0 else 1
    has_prev = page > 1
    has_next = page < total_pages
    prev_num = page - 1 if has_prev else None
    next_num = page + 1 if has_next else None

    # Уникальные значения для фильтров
    unique_users = list(set([log.get("username", "") for log in db.logs.find({}, {"username": 1})]))
    unique_actions = list(set([log.get("action", "") for log in db.logs.find({}, {"action": 1})]))

    return render_template(
        "audit_logs.html",
        logs=logs,
        total_logs=total_logs,
        page=page,
        total_pages=total_pages,
        has_prev=has_prev,
        has_next=has_next,
        prev_num=prev_num,
        next_num=next_num,
        search=search,
        user_filter=user_filter,
        action_filter=action_filter,
        date_from=date_from,
        date_to=date_to,
        unique_users=sorted([u for u in unique_users if u]),
        unique_actions=sorted([a for a in unique_actions if a]),
    )


@app.route("/logs/export")
@login_required
def export_logs():
    """Экспорт журнала в CSV"""
    write_audit_log("export", "logs", comment="Экспорт журнала действий в CSV")

    # Получение тех же фильтров что и в основном просмотре
    search = request.args.get("search", "")
    user_filter = request.args.get("user", "")
    action_filter = request.args.get("action", "")
    date_from = request.args.get("date_from", "")
    date_to = request.args.get("date_to", "")

    # Построение того же фильтра
    filter_dict = {}
    if search:
        filter_dict["$or"] = [
            {"action": {"$regex": search, "$options": "i"}},
            {"comment": {"$regex": search, "$options": "i"}},
            {"obj": {"$regex": search, "$options": "i"}},
        ]
    if user_filter:
        filter_dict["username"] = {"$regex": user_filter, "$options": "i"}
    if action_filter:
        filter_dict["action"] = {"$regex": action_filter, "$options": "i"}
    if date_from or date_to:
        date_filter = {}
        if date_from:
            date_filter["$gte"] = datetime.strptime(date_from, "%Y-%m-%d")
        if date_to:
            date_filter["$lte"] = datetime.strptime(date_to + " 23:59:59", "%Y-%m-%d %H:%M:%S")
        filter_dict["timestamp"] = date_filter

    # Получение всех записей (без пагинации для экспорта)
    logs = list(db.logs.find(filter_dict).sort("timestamp", -1))

    return export_logs_csv(logs)


def export_logs_csv(logs):
    """Генерация CSV файла с логами"""
    output = StringIO()
    writer = csv.writer(output)

    # Заголовки CSV
    writer.writerow(["Дата/Время", "Пользователь", "Действие", "Объект", "Комментарий", "IP-адрес"])

    # Данные
    for log in logs:
        timestamp = log.get("timestamp", datetime.now()).strftime("%d.%m.%Y %H:%M:%S")
        username = log.get("username", "Неизвестно")
        action = log.get("action", "")
        obj = log.get("obj", "")
        comment = log.get("comment", "")
        ip = log.get("ip_address", "")

        writer.writerow([timestamp, username, action, obj, comment, ip])

    # Подготовка файла для скачивания
    output.seek(0)
    current_date = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"audit_logs_{current_date}.csv"

    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@app.route("/audit")
@login_required
@role_required(["admin", "registrar"])
def audit_logs():
    """Единый журнал аудита системы"""
    # Параметры фильтрации
    page = int(request.args.get("page", 1))
    per_page = 50
    user_filter = request.args.get("user", "").strip()
    action_filter = request.args.get("action", "").strip()
    date_from = request.args.get("date_from", "").strip()
    date_to = request.args.get("date_to", "").strip()

    # Экспорт
    if request.args.get("export") == "csv":
        return export_audit_csv(user_filter, action_filter, date_from, date_to)

    # Фильтр для объединенного запроса
    filters = {}

    if user_filter:
        filters["$or"] = [
            {"user": {"$regex": user_filter, "$options": "i"}},
            {"user_name": {"$regex": user_filter, "$options": "i"}},
        ]

    if action_filter:
        filters["action"] = action_filter

    if date_from or date_to:
        date_filter = {}
        if date_from:
            try:
                date_filter["$gte"] = datetime.strptime(date_from, "%Y-%m-%d")
            except:
                pass
        if date_to:
            try:
                date_filter["$lte"] = datetime.strptime(date_to, "%Y-%m-%d") + timedelta(days=1)
            except:
                pass
        if date_filter:
            filters["$or"] = [
                {"datetime": {"$exists": True}},  # для старых записей
                {"timestamp": date_filter},  # для новых записей
            ]

    # Получаем данные из обеих коллекций
    logs_old = list(db.logs.find(filters).sort("datetime", -1))
    logs_new = list(db.audit_logs.find(filters).sort("timestamp", -1))

    # Нормализуем данные к единому формату
    normalized_logs = []

    # Старые записи из коллекции logs
    for log in logs_old:
        normalized_logs.append(
            {
                "_id": str(log["_id"]),
                "timestamp_local": log.get("datetime", ""),
                "user_name": log.get("user", "Unknown"),
                "user_role": log.get("role", ""),
                "ip_address": log.get("ip", ""),
                "action": log.get("action", ""),
                "object_type": log.get("object", ""),
                "comment": log.get("comment", ""),
                "user_agent": "",
                "url": "",
                "method": "",
                "details": {},
                "source": "old",
            }
        )

    # Новые записи из коллекции audit_logs
    for log in logs_new:
        normalized_logs.append(
            {
                "_id": str(log["_id"]),
                "timestamp_local": log.get("timestamp_local", ""),
                "user_name": log.get("user_name", "Unknown"),
                "user_role": log.get("user_role", ""),
                "ip_address": log.get("ip_address", ""),
                "action": log.get("action", ""),
                "object_type": log.get("object_type", ""),
                "comment": log.get("comment", ""),
                "user_agent": log.get("user_agent", ""),
                "url": log.get("url", ""),
                "method": log.get("method", ""),
                "details": log.get("details", {}),
                "source": "new",
            }
        )

    # Сортировка по времени (новые сверху)
    normalized_logs.sort(key=lambda x: x["timestamp_local"], reverse=True)

    # Пагинация
    total = len(normalized_logs)
    start = (page - 1) * per_page
    end = start + per_page
    logs = normalized_logs[start:end]

    # Данные для шаблона
    total_pages = (total + per_page - 1) // per_page
    has_prev = page > 1
    has_next = page < total_pages

    return render_template(
        "audit_logs.html",
        logs=logs,
        total=total,
        page=page,
        total_pages=total_pages,
        has_prev=has_prev,
        has_next=has_next,
        user_filter=user_filter,
        action_filter=action_filter,
        date_from=date_from,
        date_to=date_to,
    )


@app.route("/api/audit/<log_id>")
@login_required
def api_audit_details(log_id):
    """API для получения деталей записи аудита"""
    try:
        # Ищем в обеих коллекциях
        log = db.audit_logs.find_one({"_id": ObjectId(log_id)})
        if not log:
            log = db.logs.find_one({"_id": ObjectId(log_id)})

        if not log:
            return jsonify({"ok": False, "error": "not_found"}), 404

        # Нормализуем данные
        result = {
            "timestamp_local": log.get("timestamp_local") or log.get("datetime", ""),
            "user_name": log.get("user_name") or log.get("user", "Unknown"),
            "user_role": log.get("user_role") or log.get("role", ""),
            "ip_address": log.get("ip_address") or log.get("ip", ""),
            "action": log.get("action", ""),
            "object_type": log.get("object_type") or log.get("object", ""),
            "comment": log.get("comment", ""),
            "user_agent": log.get("user_agent", ""),
            "url": log.get("url", ""),
            "method": log.get("method", ""),
            "details": log.get("details", {}),
        }

        return jsonify({"ok": True, "log": result})

    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


def export_audit_csv(user_filter="", action_filter="", date_from="", date_to=""):
    """Экспорт журнала аудита в CSV"""
    write_audit_log("export", "audit_logs", comment="Экспорт журнала аудита")

    # Здесь же логика фильтрации как в audit_logs()
    filters = {}
    if user_filter:
        filters["$or"] = [
            {"user": {"$regex": user_filter, "$options": "i"}},
            {"user_name": {"$regex": user_filter, "$options": "i"}},
        ]

    # Получаем все записи без пагинации
    logs_old = list(db.logs.find(filters).sort("datetime", -1))
    logs_new = list(db.audit_logs.find(filters).sort("timestamp", -1))

    output = io.StringIO()
    writer = csv.writer(output, delimiter=";")

    # Заголовки
    writer.writerow(
        [
            "Дата/Время",
            "Пользователь",
            "Роль",
            "Действие",
            "Объект",
            "Комментарий",
            "IP адрес",
            "URL",
            "Метод",
        ]
    )

    # Старые записи
    for log in logs_old:
        writer.writerow(
            [
                log.get("datetime", ""),
                log.get("user", ""),
                log.get("role", ""),
                log.get("action", ""),
                log.get("object", ""),
                log.get("comment", ""),
                log.get("ip", ""),
                "",  # URL
                "",  # Method
            ]
        )

    # Новые записи
    for log in logs_new:
        writer.writerow(
            [
                log.get("timestamp_local", ""),
                log.get("user_name", ""),
                log.get("user_role", ""),
                log.get("action", ""),
                log.get("object_type", ""),
                log.get("comment", ""),
                log.get("ip_address", ""),
                log.get("url", ""),
                log.get("method", ""),
            ]
        )

    output.seek(0)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    filename = f"audit_log_{timestamp}.csv"

    return Response(
        output.getvalue(),
        mimetype="text/csv; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@app.route("/backup")
def backup():
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
@login_required
def api_events():
    """
    Выдаёт события календаря в формате FullCalendar.
    По умолчанию показывает ВСЁ в переданном интервале для любых ролей.
    Опциональные фильтры: doctor_id, room_id/room_name, patient_id, service_id/service_name, status.
    """
    # 1) Интервал от FullCalendar
    start_str = request.args.get("start")
    end_str   = request.args.get("end")

    # 2) Опциональные фильтры из URL
    patient_id   = (request.args.get("patient_id") or "").strip()
    doctor_id    = (request.args.get("doctor_id")  or "").strip()
    room_id      = (request.args.get("room_id")    or "").strip()
    room_name    = (request.args.get("room_name")  or "").strip()
    service_id   = (request.args.get("service_id") or "").strip()
    service_name = (request.args.get("service_name") or "").strip()
    status       = (request.args.get("status")     or "").strip()

    start_dt = parse_iso(start_str)
    end_dt   = parse_iso(end_str)

    # Если вдруг фронт не передал даты — даём безопасный дефолт (+/- 30 дней)
    if not start_dt or not end_dt:
        now = datetime.utcnow()
        start_dt = start_dt or (now - timedelta(days=30))
        end_dt   = end_dt   or (now + timedelta(days=30))

    # 3) Базовый фильтр по пересечению интервала
    q = {
        "start": {"$lt": end_dt},
        "end":   {"$gt": start_dt},
    }

    # 4) ВАЖНО: больше НЕТ автосужения "врач видит только свои"
    # Все роли (doctor/chief_doctor/registrar/admin/owner) по умолчанию видят всё.
    # Сужаем только если фильтр явно передан в запросе.

    # 5) Явные сужения
    if doctor_id:
        try:
            q["doctor_id"] = ObjectId(doctor_id)
        except Exception:
            pass

    if room_id:
        try:
            q["room_id"] = ObjectId(room_id)
        except Exception:
            pass
    elif room_name:
        r = db.rooms.find_one({"name": room_name}, {"_id": 1})
        if r:
            q["room_id"] = r["_id"]

    if service_id:
        try:
            q["service_id"] = ObjectId(service_id)
        except Exception:
            pass
    elif service_name:
        s = db.services.find_one({"name": service_name}, {"_id": 1})
        if s:
            q["service_id"] = s["_id"]

    if patient_id:
        try:
            q["patient_id"] = ObjectId(patient_id)
        except Exception:
            pass

    if status:
        # если храните статус в другом поле (например, status_key) — поправьте строку ниже
        q["status"] = status

    # 6) Справочники
    doctors_map  = {str(d["_id"]): d for d in db.doctors.find({},  {"full_name": 1, "avatar": 1})}
    patients_map = {str(p["_id"]): p for p in db.patients.find({}, {"full_name": 1, "avatar": 1})}
    services_map = {str(s["_id"]): s for s in db.services.find({}, {"name": 1, "color": 1, "duration_min": 1})}
    status_map   = {s["key"]: s for s in db.visit_statuses.find({}, {"key": 1, "title": 1, "color": 1})}
    rooms_map    = {str(r["_id"]): r for r in db.rooms.find({},    {"name": 1})}

    # 7) Формирование ответа
    events = []
    cursor = db.appointments.find(q).sort("start", 1)

    for a in cursor:
        did = str(a.get("doctor_id")  or "")
        pid = str(a.get("patient_id") or "")
        sid = str(a.get("service_id") or "")
        rid = str(a.get("room_id")    or "")

        a_start = to_dt(a.get("start"))
        if not a_start:
            continue

        a_end = to_dt(a.get("end"))
        if not a_end:
            dur = services_map.get(sid, {}).get("duration_min", 30)
            try:
                dur = int(dur)
            except Exception:
                dur = 30
            a_end = add_minutes(a_start, dur)

        doc = doctors_map.get(did, {})
        pat = patients_map.get(pid, {})
        srv = services_map.get(sid, {})
        rm  = rooms_map.get(rid, {})
        st  = status_map.get(a.get("status_key", "scheduled"), {})

        title = f'{srv.get("name", "Услуга")} — {pat.get("full_name", "Пациент")}'

        events.append({
            "id": str(a["_id"]),
            "title": title,
            "start": a_start.isoformat(),
            "end": a_end.isoformat(),
            "backgroundColor": st.get("color") or srv.get("color") or "#3498db",
            "borderColor":     st.get("color") or srv.get("color") or "#3498db",
            "extendedProps": {
                "patient":       pat.get("full_name", ""),
                "doctor":        doc.get("full_name", ""),
                "service":       srv.get("name", ""),
                "room":          rm.get("name", ""),
                "patient_name":  pat.get("full_name", ""),
                "doctor_name":   doc.get("full_name", ""),
                "service_name":  srv.get("name", ""),
                "status":        a.get("status", "scheduled"),
                "doctor_id":     did,
                "patient_id":    pid,
                "service_id":    sid,
                "room_id":       rid,
            },
        })

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
    """Возвращает справочники для фильтров календаря"""

    # Врачи из реальной БД
    doctors = []
    for doc in db.doctors.find({"status": "активен"}, {"full_name": 1, "specialization": 1}):
        doctors.append(
            {
                "id": str(doc["_id"]),
                "name": doc.get("full_name", ""),
                "specialization": doc.get("specialization", ""),
            }
        )

    # Услуги из реальной БД - только активные
    services = []
    for srv in db.services.find({"is_active": True}, {"name": 1, "duration_min": 1, "price": 1}):
        services.append(
            {
                "id": str(srv["_id"]),
                "name": srv.get("name", ""),
                "duration_min": int(srv.get("duration_min", 30)),
                "price": int(srv.get("price", 0)),
            }
        )

    # Пациенты из реальной БД
    patients = []
    for pat in db.patients.find({}, {"full_name": 1, "birthdate": 1}).limit(50):
        patients.append(
            {
                "id": str(pat["_id"]),
                "name": pat.get("full_name", ""),
                "birthdate": pat.get("birthdate", ""),
            }
        )

    # Кабинеты из реальной БД - только активные
    rooms = []
    for room in db.rooms.find({"active": True}, {"name": 1}):
        rooms.append({"id": str(room["_id"]), "name": room.get("name", "")})

    return jsonify(
        {"ok": True, "doctors": doctors, "services": services, "patients": patients, "rooms": rooms}
    )


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
        return {"ok": False, "error": "Некорректные данные: вид операции и сумма обязательны"}
    # 🔥 ОБНОВЛЕНИЕ СТАТУСА ЗАПИСИ ПРИ ОПЛАТЕ
    if kind == "payment" and service_id:
        try:
            # Находим запись по service_id и patient_id
            appointment = db.appointments.find_one(
                {
                    "patient_id": pid,
                    "service_id": service_id,
                    "status_key": {"$in": ["scheduled", "confirmed"]},
                }
            )

            if appointment:
                # Проверяем, покрывает ли оплата стоимость услуги
                service = db.services.find_one({"_id": service_id}, {"price": 1})
                if service and amount >= service.get("price", 0):
                    # Обновляем статус записи на "paid"
                    db.appointments.update_one(
                        {"_id": appointment["_id"]}, {"$set": {"status_key": "paid", "paid_at": ts}}
                    )
                    print(f"[FINANCE] Запись {appointment['_id']} помечена как оплаченная")
        except Exception as e:
            print(f"[APPOINTMENT UPDATE ERROR] {e}")

    # 💳 ОБНОВЛЕНИЕ СТАТУСА ЗАПИСИ ПРИ ОПЛАТЕ
    if kind == "payment":
        try:
            # Ищем запись через ledger с service_charge
            debt_record = db.ledger.find_one(
                {"patient_id": pid, "kind": "service_charge", "appointment_id": {"$exists": True}}
            )

            if debt_record and debt_record.get("appointment_id"):
                appointment_id = debt_record["appointment_id"]

                # Обновляем статус записи на "paid"
                db.appointments.update_one(
                    {"_id": appointment_id},
                    {"$set": {"status_key": "paid", "paid_at": ts, "payment_amount": amount}},
                )

                write_log(
                    "appointment_paid",
                    comment=f"Запись оплачена: {amount}₽",
                    obj=str(appointment_id),
                )
        except Exception as e:
            print(f"[PAYMENT UPDATE ERROR] {e}")
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
    employee_price = request.form.get("employee_price") or ""
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

    # Валидация льготной цены для сотрудников
    emp_price = None
    if employee_price:
        try:
            emp_price = int(employee_price)
            if emp_price < 0:
                errors.append("Льготная цена для сотрудников не может быть отрицательной.")
        except ValueError:
            errors.append("Льготная цена для сотрудников должна быть числом.")

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
        "employee_price": emp_price,
        "duration_min": duration_min if not isinstance(duration_min, str) else 30,
        "color": color,
        "is_active": is_active,
    }
    return data, errors


@app.route("/services")
# @role_required("admin")  # временно отключено
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
            return render_template("edit_service.html", form=item)

        db.services.update_one(
            {"_id": ObjectId(id)}, {"$set": {**data, "updated_at": datetime.utcnow()}}
        )
        flash("Изменения сохранены.", "success")
        return redirect(url_for("services_list"))

    # GET - передаём item как form
    print(f"DEBUG edit_service: {item.get('name')} | employee_price = {item.get('employee_price')}")
    return render_template("edit_service.html", form=item)


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
# @role_required("admin")  # временно отключено
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
@login_required
def patients_list():
    q = {}
    search = (request.args.get("q") or "").strip()
    if search:
        q = {
            "$or": [
                {"full_name": {"$regex": search, "$options": "i"}},
                {"phone": {"$regex": search, "$options": "i"}},
                {"email": {"$regex": search, "$options": "i"}},
            ]
        }
    items = list(db.patients.find(q).sort([("full_name", 1)]))

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

    # Нормализация для отображения
    patients = []
    for p in items:
        pid = str(p.get("_id"))
        patients.append(
            {
                "_id": pid,
                "name": p.get("full_name", ""),
                "full_name": p.get("full_name", ""),
                "phone": p.get("phone", ""),
                "email": p.get("email", ""),
                "birth_date": p.get("birthdate", ""),
                "card_no": p.get("card_no", ""),
                "appointments_count": appts_count.get(pid, 0),
                "last_appointment": None,
            }
        )

    total_rooms = db.rooms.count_documents({})
    now = datetime.utcnow()
    busy_rooms = db.appointments.count_documents({"start": {"$lte": now}, "end": {"$gte": now}})
    free_rooms = max(0, total_rooms - busy_rooms)

    return render_template(
        "patients.html",
        patients=patients,
        appts_count=appts_count,
        search=search,
        metrics={"total_rooms": total_rooms, "free_rooms": free_rooms},
    )


@app.route("/patients/debtors")
@login_required
def patients_debtors():
    """Список пациентов с долгами"""
    # Находим всех пациентов с долгом > 0
    debtors = list(
        db.patients.find(
            {"debt_balance": {"$gt": 0}},
            {
                "full_name": 1,
                "phone": 1,
                "card_no": 1,
                "debt_balance": 1,
                "created_at": 1,
            },
        ).sort(
            "debt_balance", -1
        )  # Сортировка по убыванию долга
    )

    # Подсчитываем общую сумму долгов
    total_debt = sum(p.get("debt_balance", 0) for p in debtors)

    return render_template(
        "patients_debtors.html",
        debtors=debtors,
        total_debt=total_debt,
        debtors_count=len(debtors),
    )


@app.route("/add_patient", methods=["GET", "POST"])
def add_patient():
    if request.method == "POST":
        # Получаем данные из формы
        full_name = request.form.get("full_name", "").strip()
        phone = request.form.get("phone", "").strip()
        email = request.form.get("email", "").strip()
        birthdate = request.form.get("birthdate", "").strip()
        notes = request.form.get("notes", "").strip()
        return_to = request.form.get("return_to", "")  # НОВОЕ

        # Реферальные данные
        referral_type = request.form.get("referral_type", "").strip()
        referred_by_patient_id = request.form.get("referred_by_patient_id", "").strip()
        referred_by_name = request.form.get("referred_by_name", "").strip()

        # Валидация
        if not full_name:
            flash("ФИО обязательно для заполнения", "danger")
            return render_template(
                "add_patient.html",
                form={
                    "full_name": full_name,
                    "phone": phone,
                    "email": email,
                    "birthdate": birthdate,
                    "notes": notes,
                },
                return_to=return_to,  # НОВОЕ
                all_patients=list(
                    db.patients.find({}, {"full_name": 1, "phone": 1}).sort("full_name", 1)
                ),
            )

        # Создаем пациента
        patient_data = {
            "full_name": full_name,
            "phone": phone,
            "email": email,
            "birthdate": birthdate,
            "notes": notes,
            "card_no": make_card_no(),
            "bonus_balance": 0,
            "bonus_updated_at": datetime.utcnow(),
            "created_at": datetime.utcnow(),
        }

        # Добавляем реферальные данные
        if referral_type == "patient" and referred_by_patient_id:
            try:
                patient_data["referred_by_patient_id"] = ObjectId(referred_by_patient_id)
                patient_data["referred_by_name"] = None
            except:
                pass
        elif referral_type == "other" and referred_by_name:
            patient_data["referred_by_patient_id"] = None
            patient_data["referred_by_name"] = referred_by_name
        else:
            patient_data["referred_by_patient_id"] = None
            patient_data["referred_by_name"] = None

        result = db.patients.insert_one(patient_data)
        flash("Пациент успешно добавлен", "success")

        # НОВОЕ: Проверяем откуда пришли
        if return_to == "add_event":
            return redirect(f"/add_event?patient_id={result.inserted_id}")
        else:
            return redirect(url_for("patients_list"))

    # GET запрос
    return_to = request.args.get("return_to", "")  # НОВОЕ

    total_rooms = db.rooms.count_documents({})
    now = datetime.utcnow()
    busy_rooms = db.appointments.count_documents({"start": {"$lte": now}, "end": {"$gte": now}})
    free_rooms = max(0, total_rooms - busy_rooms)

    all_patients = list(db.patients.find({}, {"full_name": 1, "phone": 1}).sort("full_name", 1))

    return render_template(
        "add_patient.html",
        form={},
        return_to=return_to,  # НОВОЕ
        metrics={"total_rooms": total_rooms, "free_rooms": free_rooms},
        all_patients=all_patients,
    )


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

    # Формируем медицинские заметки из анкеты
    medical_notes = []
    mq = p.get("medical_questionnaire", {})

    if mq.get("allergies", {}).get("has_allergies"):
        details = mq["allergies"].get("details", "")
        medical_notes.append(f"⚠️ Аллергия: {details}" if details else "⚠️ Есть аллергии")

    if mq.get("heart_conditions", {}).get("has_conditions"):
        details = mq["heart_conditions"].get("details", "")
        medical_notes.append(
            f"❤️ Сердечно-сосудистые: {details}" if details else "❤️ Проблемы с сердцем"
        )

    chronic = mq.get("chronic_diseases", {})
    if chronic.get("diabetes"):
        medical_notes.append("💊 Диабет")
    if chronic.get("asthma"):
        medical_notes.append("🫁 Астма")
    if chronic.get("oncology"):
        medical_notes.append("🩺 Онкология")

    if mq.get("pregnancy"):
        medical_notes.append("🤰 Беременность")

    if mq.get("dental_trauma", {}).get("has_trauma"):
        details = mq["dental_trauma"].get("details", "")
        medical_notes.append(
            f"🦷 Травма челюсти: {details}" if details else "🦷 Была травма челюсти"
        )

    if mq.get("smoking", {}).get("smokes"):
        duration = mq["smoking"].get("duration", "")
        medical_notes.append(f"🚬 Курит {duration}" if duration else "🚬 Курит")

    if mq.get("other_notes"):
        medical_notes.append(f"📝 {mq['other_notes']}")

    # Объединяем с обычными заметками
    combined_notes = p.get("notes", "")
    if medical_notes:
        medical_block = "\n\n=== МЕДИЦИНСКИЕ ДАННЫЕ ===\n" + "\n".join(medical_notes)
        combined_notes = (
            (combined_notes + medical_block) if combined_notes else medical_block.strip()
        )

    p["notes"] = combined_notes

    # Добавляем metrics для topbar
    total_rooms = db.rooms.count_documents({})
    now = datetime.utcnow()
    busy_rooms = db.appointments.count_documents({"start": {"$lte": now}, "end": {"$gte": now}})
    free_rooms = max(0, total_rooms - busy_rooms)

    # Финансовые данные пациента
    _id = p["_id"]
    svc_total = sum(
        int(x.get("amount", 0) or 0)
        for x in db.ledger.find({"patient_id": _id, "kind": "service_charge"})
    )
    pay_total = sum(
        int(x.get("amount", 0) or 0) for x in db.ledger.find({"patient_id": _id, "kind": "payment"})
    )
    # ИСПРАВЛЕНО: Читаем долг напрямую из БД вместо пересчета
    print(f"DEBUG patient_card: patient_id={oid}, debt_balance={p.get('debt_balance', 'MISSING')}")
    debt = p.get("debt_balance", 0)
    deposit = p.get("deposit_balance", 0)

    finance = {
        "total_debt": debt,
        "debt": debt,
        "services_total": svc_total,
        "payments_total": pay_total,
        "deposit": deposit,
    }

    # Подсчёт приведённых пациентов
    referred_patients_count = db.patients.count_documents({"referred_by_patient_id": oid})

    return render_template(
        "patient_card.html",
        patient=p,
        p=p,
        questionary=questionary,
        finance=finance,
        metrics={"total_rooms": total_rooms, "free_rooms": free_rooms},
        referred_patients_count=referred_patients_count,
    )


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
        "use_preferential_pricing": data.get("use_preferential_pricing", False),
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

    # Финансовая информация
    debt = p.get("debt_balance", 0)
    deposit = p.get("deposit_balance", 0)

    return jsonify(
        {
            "ok": True,
            "patient": {
                "_id": str(p["_id"]),
                "full_name": p.get("full_name", ""),
                "phone": p.get("phone", ""),
                "email": p.get("email", ""),
                "debt_balance": debt,
                "deposit_balance": deposit,
            },
            "ledger": ledger,
        }
    )


@app.route("/patients/<patient_id>/questionnaire", methods=["GET", "POST"])
@login_required
def patient_questionnaire(patient_id):
    """Медицинская анкета пациента"""
    try:
        patient_oid = ObjectId(patient_id)
    except:
        flash("Неверный ID пациента", "error")
        return redirect(url_for("patients_list"))

    patient = db.patients.find_one({"_id": patient_oid})
    if not patient:
        flash("Пациент не найден", "error")
        return redirect(url_for("patients_list"))

    if request.method == "POST":
        questionnaire_data = {
            "allergies": {
                "has_allergies": request.form.get("has_allergies") == "on",
                "details": request.form.get("allergies_details", "").strip(),
            },
            "heart_conditions": {
                "has_conditions": request.form.get("has_heart_conditions") == "on",
                "details": request.form.get("heart_conditions_details", "").strip(),
            },
            "chronic_diseases": {
                "diabetes": request.form.get("diabetes") == "on",
                "asthma": request.form.get("asthma") == "on",
                "oncology": request.form.get("oncology") == "on",
            },
            "pregnancy": request.form.get("pregnancy") == "on",
            "dental_trauma": {
                "has_trauma": request.form.get("has_dental_trauma") == "on",
                "when": request.form.get("dental_trauma_when", "").strip(),
                "details": request.form.get("dental_trauma_details", "").strip(),
            },
            "smoking": {
                "smokes": request.form.get("smokes") == "on",
                "duration": request.form.get("smoking_duration", "").strip(),
            },
            "other_notes": request.form.get("other_notes", "").strip(),
        }

        db.patients.update_one(
            {"_id": patient_oid},
            {
                "$set": {
                    "medical_questionnaire": questionnaire_data,
                    "questionnaire_filled": True,
                    "questionnaire_date": datetime.utcnow(),
                    "questionnaire_signature": request.form.get("signature", "").strip(),
                }
            },
        )

        flash("Медицинская анкета успешно сохранена", "success")
        return redirect(url_for("patient_card", id=patient_id))

    # GET запрос - показываем форму
    questionnaire = patient.get("medical_questionnaire", {})

    # Добавляем metrics для topbar
    total_rooms = db.rooms.count_documents({})
    now = datetime.utcnow()
    busy_rooms = db.appointments.count_documents({"start": {"$lte": now}, "end": {"$gte": now}})
    free_rooms = max(0, total_rooms - busy_rooms)

    return render_template(
        "patient_questionnaire.html",
        patient=patient,
        questionnaire=questionnaire,
        metrics={"total_rooms": total_rooms, "free_rooms": free_rooms},
    )


# ============== ПАЦИЕНТ: просмотр/редактирование ==============


# --- в начале файла убедитесь, что есть эти импорты ---
from bson import ObjectId
from flask import render_template
from datetime import datetime

# предполагаю, что у вас доступ к БД как current_app.config['DB'] или глобальный db
from flask import current_app


def _db():
    return current_app.config["DB"]


# --- карточка пациента ---
# --- patient card -------------------------------------------------
from datetime import datetime


# --- patients card (единственный вариант) ---
from flask import abort, render_template


@app.get("/patients/<pid>/edit")
def patient_edit_form(pid):
    p = db.patients.find_one({"_id": ObjectId(pid)})
    if not p:
        abort(404)
    return render_template("patient_edit.html", patient=p)


@app.post("/patients/<pid>/edit")
@login_required
def patient_edit_save(pid):
    data = request.form.to_dict()

    upd = {
        "full_name": data.get("full_name", "").strip(),
        "phone": data.get("phone", "").strip(),
        "email": data.get("email", "").strip(),
        "birthdate": data.get("birthdate") or None,
        "notes": data.get("notes", "").strip(),
        "updated_at": datetime.utcnow(),
    }

    db.patients.update_one({"_id": ObjectId(pid)}, {"$set": upd})
    flash("Данные пациента обновлены", "success")
    return redirect(f"/patients/{pid}")


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
        doc["card_no"] = make_card_no()

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

    # 💰 АВТОСОЗДАНИЕ ДОЛГА ПРИ СОЗДАНИИ ЗАПИСИ
    try:
        if service_oid:
            service = db.services.find_one({"_id": service_oid}, {"price": 1, "name": 1})
            if service and service.get("price", 0) > 0:
                price = int(service["price"])

                # Создаем запись о долге
                debt_record = {
                    "patient_id": patient_oid,
                    "appointment_id": ins.inserted_id,
                    "kind": "service_charge",
                    "amount": price,
                    "service_id": service_oid,
                    "description": f"Услуга: {service.get('name', '')}",
                    "ts": datetime.utcnow(),
                    "ts_iso": datetime.utcnow().strftime("%Y-%m-%dT%H:%M"),
                    "status": "pending",
                }

                db.ledger.insert_one(debt_record)
                write_log(
                    "debt_created",
                    comment=f"Создан долг {price}₽ за услугу",
                    obj=str(ins.inserted_id),
                )
    except Exception as e:
        print(f"[DEBT ERROR] {e}")

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

# ===== API ДЛЯ ТОПБАРА =====


@app.route("/api/dashboard/today-appointments", methods=["GET"])
@login_required
def api_today_appointments_count():
    """Количество записей на сегодня"""
    from datetime import timedelta

    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start + timedelta(days=1)

    count = db.appointments.count_documents(
        {"start": {"$gte": today_start, "$lt": today_end}, "status_key": {"$ne": "cancelled"}}
    )

    return jsonify({"count": count})


@app.route("/api/dashboard/doctor-plans", methods=["GET"])
@login_required
def api_doctor_plans_count():
    """Количество планов врача по статусам"""
    user_id = session.get("user_id")
    user = session.get("user", {})

    # Показываем только врачам
    if user.get("role") not in ["doctor", "owner"]:
        return jsonify({"total": 0, "pending": 0, "needs_revision": 0, "approved": 0})

    doctor_oid = ObjectId(user_id)

    # Считаем планы врача по статусам
    pending = db.treatment_plans.count_documents(
        {"doctor_id": doctor_oid, "status": "pending_approval"}
    )

    needs_revision = db.treatment_plans.count_documents(
        {
            "doctor_id": doctor_oid,
            "status": "needs_revision",
            "comments_viewed_by_doctor": False,  # Только непрочитанные
        }
    )

    approved = db.treatment_plans.count_documents({"doctor_id": doctor_oid, "status": "approved"})

    total = pending + needs_revision

    return jsonify(
        {
            "total": total,  # Требуют внимания
            "pending": pending,
            "needs_revision": needs_revision,
            "approved": approved,
        }
    )


@app.route("/api/dashboard/pending-plans", methods=["GET"])
@login_required
def api_pending_plans_count():
    """Количество планов на согласовании (только для главврача)"""
    user = session.get("user", {})

    # Показываем только главврачу
    if user.get("role") != "owner":
        return jsonify({"count": 0})

    count = db.treatment_plans.count_documents({"status": "pending_approval"})

    return jsonify({"count": count})


@app.route("/api/dashboard/debtors", methods=["GET"])
@login_required
def api_debtors_count():
    """Количество должников"""
    count = db.patients.count_documents({"debt_balance": {"$gt": 0}})
    return jsonify({"count": count})


# ======= ЗАПУСК =======


@app.route("/services")
def services():
    """Список всех услуг"""
    try:
        services_list = list(db.services.find({"active": True}).sort("name", 1))
        return render_template("services.html", services=services_list)
    except Exception as e:
        flash(f"Ошибка при загрузке услуг: {str(e)}", "error")
        return render_template("services.html", services=[])


@app.route("/rooms")
def rooms():
    """Управление кабинетами"""
    try:
        rooms_list = list(db.rooms.find().sort("number", 1))
        return render_template("rooms.html", rooms=rooms_list)
    except Exception as e:
        flash(f"Ошибка при загрузке кабинетов: {str(e)}", "error")
        return render_template("rooms.html", rooms=[])


@app.route("/reports")
def reports():
    """Страница отчетов"""
    try:
        today = datetime.now()
        month_start = today.replace(day=1).strftime("%Y-%m-%d")

        total_appointments = db.appointments.count_documents({"date": {"$gte": month_start}})

        stats = {"total_appointments": total_appointments, "period": month_start}

        return render_template("reports.html", stats=stats)
    except Exception as e:
        flash(f"Ошибка при формировании отчетов: {str(e)}", "error")
        return render_template("reports.html", stats={})


# === ПРОСТОЙ МАРШРУТ /PATIENTS ДЛЯ ТЕСТИРОВАНИЯ ===
@app.route("/patients")
def patients():
    """Простой список пациентов (без авторизации для тестирования)"""
    try:
        # Получаем пациентов из БД
        patients_list = list(db.patients.find().limit(10))

        # Преобразуем ObjectId в строки
        for patient in patients_list:
            patient["_id"] = str(patient["_id"])

        # Если нет шаблона, возвращаем JSON
        try:
            return render_template("patients.html", patients=patients_list)
        except:
            # Если шаблон не найден, возвращаем простой HTML
            html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Пациенты</title>
                <style>
                    body {{ font-family: Arial; margin: 20px; }}
                    table {{ border-collapse: collapse; width: 100%; }}
                    th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                    th {{ background-color: #f2f2f2; }}
                    .btn {{ background: #007bff; color: white; padding: 8px 16px; text-decoration: none; border-radius: 4px; }}
                </style>
            </head>
            <body>
                <h1>Список пациентов</h1>
                <p>Найдено пациентов: {len(patients_list)}</p>

                <table>
                    <tr>
                        <th>ID</th>
                        <th>Имя</th>
                        <th>Телефон</th>
                        <th>Email</th>
                        <th>Действия</th>
                    </tr>
            """

            for patient in patients_list:
                name = patient.get("full_name", patient.get("name", "Не указано"))
                phone = patient.get("phone", "—")
                email = patient.get("email", "—")

                html += f"""
                    <tr>
                        <td>{patient['_id']}</td>
                        <td>{name}</td>
                        <td>{phone}</td>
                        <td>{email}</td>
                        <td><a href="/patients/{patient['_id']}" class="btn">Карточка</a></td>
                    </tr>
                """

            html += """
                </table>
                <br>
                <a href="/" class="btn">← Назад к календарю</a>
            </body>
            </html>
            """

            return html

    except Exception as e:
        return f"""
        <h1>Ошибка загрузки пациентов</h1>
        <p>Ошибка: {str(e)}</p>
        <a href="/">← Назад к календарю</a>
        """


# === ВРЕМЕННЫЕ РОУТЫ ДЛЯ ОЧИСТКИ (ВСТАВИТЬ СЮДА) ===
@app.route("/admin/clean_all_demo")
@login_required
def clean_all_demo():
    """Простая очистка всех демо-пациентов"""
    try:
        # Сохраняем ID нашего тестового пациента
        test_patient = db.patients.find_one({"phone": "+7 912 345-67-89"})
        test_id = test_patient["_id"] if test_patient else None

        # Удаляем всех пациентов кроме тестового
        if test_id:
            result = db.patients.delete_many({"_id": {"$ne": test_id}})
        else:
            result = db.patients.delete_many({})

        return f"Удалено демо-пациентов: {result.deleted_count}. Сохранен тестовый пациент."

    except Exception as e:
        return f"Ошибка: {str(e)}"


@app.route("/admin/create_test_patient")
@login_required
def create_test_patient():
    # Создаем нормального пациента для тестирования
    patient = {
        "full_name": "Иванов Иван Иванович",
        "phone": "+7 912 345-67-89",
        "email": "ivanov@example.com",
        "birthdate": "1985-03-15",
        "card_no": "001",
        "created_at": datetime.utcnow(),
        "notes": "Тестовый пациент для проверки системы",
    }

    result = db.patients.insert_one(patient)
    return f"Создан тестовый пациент: {result.inserted_id}"


@app.route("/admin/mass_cleanup")
@login_required
def mass_cleanup():
    """Очистка всех демо-данных кроме реальных"""

    # Удаляем демо-пациентов по паттернам
    demo_patients = db.patients.delete_many(
        {
            "$or": [
                {"full_name": {"$in": ["", None, "—"]}},
                {"full_name": {"$regex": "^patient"}},
                {"phone": {"$regex": "^\\+799900002"}},
                {"email": {"$regex": "^patient.*@gmail\\.ru"}},
                {"birthdate": {"$in": ["2004-08-08", "2011-07-25", "2001-05-04"]}},  # из скриншота
                {
                    "_id": {"$ne": ObjectId("68d2a9083271ea14c93e1a9a")}
                },  # сохраняем тестового Иванова
            ]
        }
    )

    # Удаляем связанные записи демо-пациентов
    db.appointments.delete_many({"patient_id": {"$in": []}})  # пустой список пока

    # Статистика
    result = f"""
    Очистка завершена:
    - Удалено демо-пациентов: {demo_patients.deleted_count}
    - Сохранен тестовый пациент: Иванов Иван Иванович
    """

    return f"<pre>{result}</pre>"


@app.route("/admin/init_production_data")
@login_required
def init_production_data():
    """Создание минимального набора боевых данных"""

    result = []

    # Проверяем есть ли админ-пользователь
    admin_count = db.users.count_documents({"role": "admin"})
    if admin_count == 0:
        admin_user = {
            "login": "admin",
            "password_hash": "hashed_password_here",  # замените на реальный хеш
            "role": "admin",
            "full_name": "Администратор",
            "active": True,
            "created_at": datetime.utcnow(),
        }
        db.users.insert_one(admin_user)
        result.append("✓ Создан админ-пользователь")

    # Проверяем базовые статусы визитов
    statuses = [
        {"key": "scheduled", "title": "Запланирован", "color": "#3498db"},
        {"key": "confirmed", "title": "Подтвержден", "color": "#2ecc71"},
        {"key": "completed", "title": "Завершен", "color": "#27ae60"},
        {"key": "paid", "title": "Оплачен", "color": "#16a085"},
        {"key": "cancelled", "title": "Отменен", "color": "#e74c3c"},
        {"key": "no_show", "title": "Не явился", "color": "#f39c12"},
    ]

    for status in statuses:
        db.visit_statuses.update_one({"key": status["key"]}, {"$setOnInsert": status}, upsert=True)
    result.append("✓ Проверены статусы визитов")

    return "<br>".join(result)


@app.route("/debug/patients")
@login_required
def debug_patients():
    import json

    patients = list(db.patients.find())
    return f"<pre>{json.dumps(patients, indent=2, default=str)}</pre>"


# === КОНЕЦ ВРЕМЕННЫХ РОУТОВ ===

# ============================================
# ПЛАНЫ ЛЕЧЕНИЯ
# ============================================


print(">>> LOADING treatment_plan_new_get FUNCTION <<<")


@app.route("/patients/<patient_id>/treatment-plan/new", methods=["GET", "POST"])
@login_required
@role_required(["doctor", "owner"])
def treatment_plan_new(patient_id):
    """Создание плана лечения"""

    if request.method == "POST":
        # POST логика
        print(f"\n=== POST PLAN FOR PATIENT {patient_id} ===")
        print(f"Form data: {request.form}")

        try:
            patient_oid = ObjectId(patient_id)
            patient = db.patients.find_one({"_id": patient_oid})

            if not patient:
                flash("Пациент не найден", "error")
                return redirect("/patients")

            # Получить данные формы
            action = request.form.get("action")
            notes = request.form.get("notes", "").strip()

            # Получить услуги
            import json

            services_json = request.form.get("services", "[]")
            services_data = json.loads(services_json)

            if not services_data:
                flash("Добавьте хотя бы одну услугу в план", "warning")
                return redirect(f"/patients/{patient_id}/treatment-plan/new")

            # Подготовить услуги
            services_list = []
            total_amount = 0

            for svc in services_data:
                service = db.services.find_one({"_id": ObjectId(svc["service_id"])})
                if not service:
                    continue

                service_data = {
                    "service_id": ObjectId(svc["service_id"]),
                    "service_name": service["name"],
                    "price": int(service["price"]),
                    "comment": svc.get("comment", "").strip(),
                    "status": "planned",
                    "completed_at": None,
                    "completed_by_doctor_id": None,
                }
                services_list.append(service_data)
                total_amount += service_data["price"]

            # Определить статус и автоутверждение для главврача
            doctor_id = session.get("user_id")
            doctor = db.users.find_one({"_id": ObjectId(doctor_id)})
            is_chief = doctor and doctor.get("role") == "owner"

            if action == "submit":
                if is_chief:
                    # Главврач сам утверждает свой план
                    status = "approved"
                    submitted_to_chief_at = datetime.now(timezone.utc)
                    chief_doctor_id = ObjectId(doctor_id)
                    approved_at = datetime.now(timezone.utc)
                    approved_by = ObjectId(doctor_id)
                else:
                    # Обычный врач отправляет на согласование
                    status = "pending_approval"
                    submitted_to_chief_at = datetime.now(timezone.utc)
                    chief = db.users.find_one({"role": "owner"})
                    chief_doctor_id = chief["_id"] if chief else None
                    approved_at = None
                    approved_by = None
            else:
                # Сохранить как черновик
                status = "draft"
                submitted_to_chief_at = None
                chief_doctor_id = None
                approved_at = None
                approved_by = None

            plan = {
                "patient_id": patient_oid,
                "doctor_id": ObjectId(doctor_id),
                "status": status,
                "services": services_list,
                "submitted_to_chief_at": submitted_to_chief_at,
                "chief_doctor_id": chief_doctor_id,
                "approved_at": None,
                "approved_by": None,
                "rejection_reason": None,
                "total_amount": total_amount,
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
                "requires_reapproval": False,
                "last_change_description": None,
                "notes": notes,
            }

            print(f"\n=== SAVING PLAN ===")
            print(f"Plan data: {plan}")

            result = db.treatment_plans.insert_one(plan)

            print(f"Plan saved! ID: {result.inserted_id}")

            # Логирование
            db.audit_logs.insert_one(
                {
                    "user_id": ObjectId(doctor_id),
                    "action": "create_treatment_plan",
                    "details": {
                        "plan_id": str(result.inserted_id),
                        "patient_id": str(patient_oid),
                        "status": status,
                        "total_amount": total_amount,
                    },
                    "ts": datetime.now(timezone.utc),
                }
            )

            if action == "submit":
                flash("План лечения отправлен главврачу на согласование", "success")
            else:
                flash("Черновик плана сохранён", "success")

            return redirect(f"/patients/{patient_id}")

        except Exception as e:
            flash(f"Ошибка при создании плана: {str(e)}", "error")
            print(f"ERROR CREATING PLAN: {str(e)}")
            import traceback

            traceback.print_exc()
            return redirect(f"/patients/{patient_id}/treatment-plan/new")

    # GET логика
    try:
        patient_oid = ObjectId(patient_id)
        patient = db.patients.find_one({"_id": patient_oid})

        if not patient:
            flash("Пациент не найден", "error")
            return redirect("/patients")

        services = list(db.services.find({"is_active": True}).sort("name", 1))
        doctor_id = session.get("user_id")
        doctor = db.users.find_one({"_id": ObjectId(doctor_id)})

        return render_template(
            "treatment_plan_new.html",
            patient=patient,
            services=services,
            doctor=doctor,
            TREATMENT_PLAN_STATUS=TREATMENT_PLAN_STATUS,
            SERVICE_STATUS=SERVICE_STATUS,
        )
    except Exception as e:
        flash(f"Ошибка: {str(e)}", "error")
        return redirect("/patients")


@app.route("/patients/<patient_id>/treatment-plan/<plan_id>/edit", methods=["GET", "POST"])
@login_required
@role_required(["doctor", "owner"])
def treatment_plan_edit(patient_id, plan_id):
    """Редактирование плана лечения"""

    if request.method == "POST":
        # POST логика - обновление плана
        try:
            plan_oid = ObjectId(plan_id)
            patient_oid = ObjectId(patient_id)

            plan = db.treatment_plans.find_one({"_id": plan_oid})
            if not plan:
                flash("План не найден", "error")
                return redirect(f"/patients/{patient_id}")

            # Проверка прав: только свой план
            doctor_id = session.get("user_id")
            if str(plan["doctor_id"]) != doctor_id:
                flash("Доступ запрещен", "error")
                return redirect(f"/patients/{patient_id}")

            # Получить данные формы
            action = request.form.get("action")
            notes = request.form.get("notes", "").strip()

            # Получить услуги
            import json

            services_json = request.form.get("services", "[]")
            services_data = json.loads(services_json)

            if not services_data:
                flash("Добавьте хотя бы одну услугу в план", "warning")
                return redirect(f"/patients/{patient_id}/treatment-plan/{plan_id}/edit")

            # Подготовить услуги
            services_list = []
            total_amount = 0

            for svc in services_data:
                service = db.services.find_one({"_id": ObjectId(svc["service_id"])})
                if not service:
                    continue

                service_data = {
                    "service_id": ObjectId(svc["service_id"]),
                    "service_name": service["name"],
                    "price": int(service["price"]),
                    "comment": svc.get("comment", "").strip(),
                    "status": "planned",
                    "completed_at": None,
                    "completed_by_doctor_id": None,
                }
                services_list.append(service_data)
                total_amount += service_data["price"]

            # Определить статус
            doctor = db.users.find_one({"_id": ObjectId(doctor_id)})
            is_chief = doctor and doctor.get("role") == "owner"

            if action == "submit":
                if is_chief:
                    # Главврач автоутверждает
                    status = "approved"
                    approved_at = datetime.now(timezone.utc)
                else:
                    # Обычный врач отправляет на согласование
                    status = "pending_approval"
                    approved_at = None
            else:
                # Черновик
                status = "draft"
                approved_at = None

            # Обновить план
            update_data = {
                "$set": {
                    "services": services_list,
                    "total_amount": total_amount,
                    "notes": notes,
                    "status": status,
                    "updated_at": datetime.now(timezone.utc),
                    "approved_at": approved_at,
                    "comments_viewed_by_doctor": False,  # Сбросить флаг
                },
                "$unset": {"plan_comments": ""},  # Удалить старые комментарии
            }

            db.treatment_plans.update_one({"_id": plan_oid}, update_data)

            # Логирование
            db.audit_logs.insert_one(
                {
                    "user_id": ObjectId(doctor_id),
                    "action": "update_treatment_plan",
                    "details": {
                        "plan_id": str(plan_oid),
                        "patient_id": str(patient_oid),
                        "status": status,
                        "total_amount": total_amount,
                    },
                    "ts": datetime.now(timezone.utc),
                }
            )

            if action == "submit":
                flash("План обновлен и отправлен на согласование", "success")
            else:
                flash("Черновик плана обновлен", "success")

            return redirect(f"/patients/{patient_id}")

        except Exception as e:
            flash(f"Ошибка при обновлении плана: {str(e)}", "error")
            import traceback

            traceback.print_exc()
            return redirect(f"/patients/{patient_id}/treatment-plan/{plan_id}/edit")

    # GET логика - показать форму
    try:
        plan_oid = ObjectId(plan_id)
        patient_oid = ObjectId(patient_id)

        plan = db.treatment_plans.find_one({"_id": plan_oid})
        if not plan:
            flash("План не найден", "error")
            return redirect(f"/patients/{patient_id}")

        # Проверка прав
        doctor_id = session.get("user_id")
        if str(plan["doctor_id"]) != doctor_id:
            flash("Доступ запрещен", "error")
            return redirect(f"/patients/{patient_id}")

        patient = db.patients.find_one({"_id": patient_oid})
        if not patient:
            flash("Пациент не найден", "error")
            return redirect("/patients")

        services = list(db.services.find({"is_active": True}).sort("name", 1))
        doctor = db.users.find_one({"_id": ObjectId(doctor_id)})

        return render_template(
            "treatment_plan_edit.html",
            patient=patient,
            plan=plan,
            services=services,
            doctor=doctor,
            TREATMENT_PLAN_STATUS=TREATMENT_PLAN_STATUS,
            SERVICE_STATUS=SERVICE_STATUS,
        )
    except Exception as e:
        flash(f"Ошибка: {str(e)}", "error")
        import traceback

        traceback.print_exc()
        return redirect(f"/patients/{patient_id}")


@app.route("/chief/pending-plans")
@login_required
@role_required(["owner"])
def chief_pending_plans():
    """Список планов на согласовании для главврача"""
    try:
        # Получить все планы на согласовании
        plans = list(
            db.treatment_plans.find({"status": "pending_approval"}).sort(
                "submitted_to_chief_at", -1
            )
        )

        # Загрузить данные пациентов и врачей
        for plan in plans:
            patient = db.patients.find_one({"_id": plan["patient_id"]})
            doctor = db.users.find_one({"_id": plan["doctor_id"]})

            plan["patient_name"] = (
                patient.get("full_name", "Неизвестно") if patient else "Неизвестно"
            )
            plan["doctor_name"] = doctor.get("full_name", "Неизвестно") if doctor else "Неизвестно"

        return render_template(
            "chief_pending_plans.html", plans=plans, TREATMENT_PLAN_STATUS=TREATMENT_PLAN_STATUS
        )
    except Exception as e:
        flash(f"Ошибка: {str(e)}", "error")
        return redirect("/calendar")


@app.route("/doctor/my-plans")
@login_required
@role_required(["doctor", "owner"])
def doctor_my_plans():
    """Список планов врача"""
    try:
        user_id = session.get("user_id")
        doctor_oid = ObjectId(user_id)

        # Получить все планы этого врача
        plans = list(db.treatment_plans.find({"doctor_id": doctor_oid}).sort("created_at", -1))

        # Загрузить данные пациентов
        for plan in plans:
            patient = db.patients.find_one({"_id": plan["patient_id"]})
            plan["patient_name"] = (
                patient.get("full_name", "Неизвестно") if patient else "Неизвестно"
            )

        return render_template(
            "doctor_my_plans.html", plans=plans, TREATMENT_PLAN_STATUS=TREATMENT_PLAN_STATUS
        )
    except Exception as e:
        flash(f"Ошибка: {str(e)}", "error")
        return redirect("/calendar")


@app.route("/chief/plan-details/<plan_id>")
@login_required
@role_required(["owner", "doctor", "admin"])
def chief_plan_details(plan_id):
    """API: Детали плана для модального окна"""
    try:
        plan = db.treatment_plans.find_one({"_id": ObjectId(plan_id)})
        if not plan:
            return jsonify({"error": "План не найден"}), 404

        # ПРОВЕРКА ПРАВ: Врач видит только свои планы
        user = session.get("user", {})
        user_id = session.get("user_id")

        if user.get("role") == "doctor":
            if str(plan["doctor_id"]) != user_id:
                return jsonify({"error": "Доступ запрещен"}), 403

        patient = db.patients.find_one({"_id": plan["patient_id"]})
        doctor = db.users.find_one({"_id": plan["doctor_id"]})

        # Конвертируем ObjectId в строки для JSON
        services_clean = []
        for s in plan.get("services", []):
            services_clean.append(
                {
                    "service_id": str(s.get("service_id")) if s.get("service_id") else None,
                    "service_name": s.get("service_name", ""),
                    "price": s.get("price", 0),
                    "comment": s.get("comment", ""),
                    "status": s.get("status", "planned"),
                }
            )

        # Конвертируем ObjectId в комментариях
        comments_clean = []
        for c in plan.get("plan_comments", []):
            comments_clean.append(
                {
                    "author_id": str(c.get("author_id")) if c.get("author_id") else None,
                    "author_name": c.get("author_name", ""),
                    "author_role": c.get("author_role", ""),
                    "text": c.get("text", ""),
                    "created_at": str(c.get("created_at", "")),
                }
            )

        # Если врач смотрит свой план со статусом needs_revision - помечаем как прочитанный
        if user.get("role") == "doctor" and plan.get("status") == "needs_revision":
            if not plan.get("comments_viewed_by_doctor", False):
                db.treatment_plans.update_one(
                    {"_id": ObjectId(plan_id)}, {"$set": {"comments_viewed_by_doctor": True}}
                )

        return jsonify(
            {
                "patient_name": patient.get("full_name", "Неизвестно") if patient else "Неизвестно",
                "doctor_name": doctor.get("full_name", "Неизвестно") if doctor else "Неизвестно",
                "services": services_clean,
                "total_amount": plan.get("total_amount", 0),
                "notes": plan.get("notes", ""),
                "status": plan.get("status", "draft"),
                "plan_comments": comments_clean,
            }
        )
    except Exception as e:
        print(f"ERROR in chief_plan_details: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/chief/approve-plan/<plan_id>", methods=["POST"])
@login_required
@role_required(["owner"])
def chief_approve_plan(plan_id):
    """Утверждение плана лечения"""
    try:
        chief_id = session.get("user_id")

        result = db.treatment_plans.update_one(
            {"_id": ObjectId(plan_id)},
            {
                "$set": {
                    "status": "approved",
                    "approved_at": datetime.now(timezone.utc),
                    "approved_by": ObjectId(chief_id),
                    "updated_at": datetime.now(timezone.utc),
                }
            },
        )

        if result.modified_count == 0:
            return jsonify({"success": False, "error": "План не найден"}), 404

        # Логирование
        plan = db.treatment_plans.find_one({"_id": ObjectId(plan_id)})
        db.audit_logs.insert_one(
            {
                "user_id": ObjectId(chief_id),
                "action": "approve_treatment_plan",
                "details": {
                    "plan_id": plan_id,
                    "patient_id": str(plan["patient_id"]),
                    "total_amount": plan["total_amount"],
                },
                "ts": datetime.now(timezone.utc),
            }
        )

        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/chief/request-revision/<plan_id>", methods=["POST"])
@login_required
@role_required(["owner"])
def chief_request_revision(plan_id):
    """Запрос изменений в плане лечения"""
    try:
        data = request.json
        comment = data.get("comment", "").strip()

        if not comment:
            return jsonify({"success": False, "error": "Укажите комментарий"}), 400

        chief_id = session.get("user_id")
        chief = db.users.find_one({"_id": ObjectId(chief_id)})

        # Обновляем план
        result = db.treatment_plans.update_one(
            {"_id": ObjectId(plan_id)},
            {
                "$set": {
                    "status": "needs_revision",
                    "comments_viewed_by_doctor": False,
                    "updated_at": datetime.now(timezone.utc),
                },
                "$push": {
                    "plan_comments": {
                        "author_id": ObjectId(chief_id),
                        "author_name": chief.get("full_name", "Главврач"),
                        "author_role": "owner",
                        "text": comment,
                        "created_at": datetime.now(timezone.utc),
                    }
                },
            },
        )

        if result.modified_count == 0:
            return jsonify({"success": False, "error": "План не найден"}), 404

        # Логирование
        plan = db.treatment_plans.find_one({"_id": ObjectId(plan_id)})
        db.audit_logs.insert_one(
            {
                "user_id": ObjectId(chief_id),
                "action": "request_plan_revision",
                "details": {
                    "plan_id": plan_id,
                    "patient_id": str(plan["patient_id"]),
                    "comment": comment,
                },
                "ts": datetime.now(timezone.utc),
            }
        )

        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/test-session")
def test_session():
    from flask import jsonify

    return jsonify({"session_user": session.get("user"), "session_keys": list(session.keys())})


@app.route("/test-treatment-plan")
@login_required
def test_treatment_plan():
    return f"<h1>Работает! Пользователь: {session.get('user')}</h1>"


# ==================== API: УПРАВЛЕНИЕ СТАТУСАМИ ЗАПИСЕЙ ====================


@app.route("/appointments/<appointment_id>/arrive", methods=["POST"])
@login_required
def appointment_arrive(appointment_id):
    """Отметить что пациент пришёл"""
    from bson.objectid import ObjectId

    db.appointments.update_one(
        {"_id": ObjectId(appointment_id)},
        {"$set": {"status": "arrived", "arrived_at": datetime.utcnow()}},
    )

    return jsonify({"success": True, "message": "Пациент отмечен как пришедший"})


@app.route("/appointments/<appointment_id>/no-show", methods=["POST"])
@login_required
def appointment_no_show(appointment_id):
    """Отметить что пациент не явился"""
    from bson.objectid import ObjectId

    appt = db.appointments.find_one({"_id": ObjectId(appointment_id)})
    if appt:
        db.appointments.update_one(
            {"_id": ObjectId(appointment_id)},
            {"$set": {"status": "no_show", "no_show_at": datetime.utcnow()}},
        )

        db.patients.update_one({"_id": appt["patient_id"]}, {"$inc": {"no_show_count": 1}})

    return jsonify({"success": True, "message": "Отмечено: пациент не явился"})


@app.route("/appointments/<appointment_id>/cancel", methods=["POST"])
@login_required
def appointment_cancel(appointment_id):
    """Отменить запись"""
    from bson.objectid import ObjectId

    data = request.get_json() or {}
    reason = data.get("reason", "")

    db.appointments.update_one(
        {"_id": ObjectId(appointment_id)},
        {
            "$set": {
                "status": "cancelled",
                "cancellation_reason": reason,
                "cancelled_by": ObjectId(session["user_id"]),
                "cancelled_at": datetime.utcnow(),
            }
        },
    )

    return jsonify({"success": True, "message": "Запись отменена"})


@app.route("/appointments/<appointment_id>/reschedule", methods=["POST"])
@login_required
def appointment_reschedule(appointment_id):
    """Перенести запись"""
    from bson.objectid import ObjectId

    data = request.get_json() or {}
    new_start = data.get("new_start")
    new_end = data.get("new_end")

    old_appt = db.appointments.find_one({"_id": ObjectId(appointment_id)})
    if old_appt:
        new_appt = {
            **old_appt,
            "_id": ObjectId(),
            "start": datetime.fromisoformat(new_start),
            "end": datetime.fromisoformat(new_end),
            "status": "scheduled",
            "original_appointment_id": ObjectId(appointment_id),
            "created_at": datetime.utcnow(),
        }
        db.appointments.insert_one(new_appt)

        db.appointments.update_one(
            {"_id": ObjectId(appointment_id)},
            {"$set": {"status": "rescheduled", "rescheduled_to": new_appt["_id"]}},
        )

    return jsonify({"success": True, "message": "Запись перенесена"})


@app.route("/appointments/<appointment_id>/complete", methods=["POST"])
@login_required
def appointment_complete(appointment_id):
    """Завершить приём с созданием долга/депозита"""
    from bson.objectid import ObjectId

    data = request.get_json() or {}
    visit_comment = data.get("visit_comment", "")
    visit_number = data.get("visit_number", 1)
    total_visits = data.get("total_visits", 1)

    appt = db.appointments.find_one({"_id": ObjectId(appointment_id)})
    if not appt:
        return jsonify({"success": False, "error": "Запись не найдена"}), 404

    patient = db.patients.find_one({"_id": appt["patient_id"]})
    service = db.services.find_one({"_id": appt["service_id"]})

    if patient.get("use_preferential_pricing") and service.get("employee_price"):
        price = int(service["employee_price"])
    else:
        price = int(service["price"])

    deposit = patient.get("deposit_balance", 0)

    if deposit >= price:
        deposit_used = price
        debt_created = 0
        new_deposit = deposit - price
        new_debt = patient.get("debt_balance", 0)
    else:
        deposit_used = deposit
        debt_created = price - deposit
        new_deposit = 0
        new_debt = patient.get("debt_balance", 0) + debt_created

    db.patients.update_one(
        {"_id": patient["_id"]},
        {"$set": {"deposit_balance": new_deposit, "debt_balance": new_debt}},
    )

    ledger_entry = {
        "patient_id": patient["_id"],
        "appointment_id": appt["_id"],
        "service_id": service["_id"],
        "kind": "service_completed",
        "amount": price,
        "deposit_used": deposit_used,
        "debt_created": debt_created,
        "description": f"Завершение: {service['name']}",
        "ts": datetime.utcnow(),
    }
    db.ledger.insert_one(ledger_entry)

    # Создать детализированную запись долга если есть недоплата
    if debt_created > 0:
        debt_record = {
            "patient_id": patient["_id"],
            "appointment_id": appt["_id"],
            "service_name": service["name"],
            "total_amount": price,
            "paid_amount": price - debt_created,
            "debt_amount": debt_created,
            "created_at": datetime.utcnow(),
            "status": "unpaid",
            "ledger_id": ledger_entry["_id"] if "_id" in ledger_entry else None,
        }
        db.debts.insert_one(debt_record)

    db.appointments.update_one(
        {"_id": appt["_id"]},
        {
            "$set": {
                "status": "completed",
                "completed_at": datetime.utcnow(),
                "completed_by": ObjectId(session["user_id"]),
                "visit_comment": visit_comment,
                "visit_number": visit_number,
                "total_visits": total_visits,
            }
        },
    )

    if appt.get("treatment_plan_id"):
        plan = db.treatment_plans.find_one({"_id": appt["treatment_plan_id"]})
        if plan:
            for i, svc in enumerate(plan.get("services", [])):
                if svc.get("service_id") == service["_id"] and svc.get("status") == "planned":
                    db.treatment_plans.update_one(
                        {"_id": plan["_id"]},
                        {
                            "$set": {
                                f"services.{i}.status": "completed",
                                f"services.{i}.completed_at": datetime.utcnow(),
                            }
                        },
                    )
                    break

    write_audit_log(
        "complete",
        "appointments",
        obj_id=str(appt["_id"]),
        comment=f"Завершён приём: {service['name']}, долг: {debt_created}₽",
        patient_id=str(patient["_id"]),
    )

    return jsonify(
        {
            "success": True,
            "message": "Приём завершён",
            "debt_created": debt_created,
            "deposit_used": deposit_used,
        }
    )


@app.route("/api/patients/<patient_id>/debts")
@login_required
def api_patient_debts(patient_id):
    """Получить детализированные долги пациента"""
    from bson.objectid import ObjectId

    debts = list(db.debts.find({"patient_id": ObjectId(patient_id)}, sort=[("created_at", -1)]))

    result = []
    for debt in debts:
        result.append(
            {
                "id": str(debt["_id"]),
                "service_name": debt.get("service_name", ""),
                "total_amount": debt.get("total_amount", 0),
                "paid_amount": debt.get("paid_amount", 0),
                "debt_amount": debt.get("debt_amount", 0),
                "created_at": (
                    debt.get("created_at").strftime("%d.%m.%Y") if debt.get("created_at") else ""
                ),
                "status": debt.get("status", "unpaid"),
            }
        )

    return jsonify(result)


if __name__ == "__main__":
    # На Windows отключаем перезагрузчик, чтобы не ловить WinError 10038 в Werkzeug
    app.run(debug=True, use_reloader=False)


# === ОТЛАДОЧНЫЕ МАРШРУТЫ ===
@app.route("/services")
@login_required
def services_list_debug():
    """Временный маршрут для списка услуг"""
    try:
        # Получаем услуги
        services = list(db.services.find().sort("name", 1))

        # Нормализуем данные
        for s in services:
            s["_id"] = str(s["_id"])
            if "is_active" not in s:
                s["is_active"] = True

        return render_template("services.html", items=services)
    except Exception as e:
        flash(f"Ошибка загрузки услуг: {e}", "danger")
        return render_template("services.html", items=[])


@app.route("/debug/info")
@login_required
def debug_info():
    """Отладочная информация"""
    info = {
        "user_id": session.get("user_id"),
        "user_role": session.get("user_role"),
        "user_name": session.get("user_name"),
        "session_keys": list(session.keys()),
        "db_collections": db.list_collection_names(),
        "patients_count": db.patients.count_documents({}),
        "services_count": db.services.count_documents({}),
        "appointments_count": db.appointments.count_documents({}),
    }
    return f"<pre>{json.dumps(info, indent=2, default=str)}</pre>"
