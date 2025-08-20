import os
import calendar
import csv
import io
from collections import OrderedDict
from datetime import datetime, timedelta
from pathlib import Path

# --- third-party
from bson import ObjectId  # ОСТАВЛЯЕМ только ЭТОТ импорт ObjectId (без дубля из bson.objectid)
from flask import (
    Flask, Response, flash, jsonify, redirect,
    render_template, request, send_file, session, url_for
)
from markupsafe import Markup
from pymongo import MongoClient, ReturnDocument
import urllib
from dotenv import load_dotenv

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
    """Безопасно преобразует строку в ObjectId или возвращает None."""
    try:
        return ObjectId(s) if s else None
    except Exception:
        return None

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
load_dotenv()  # загружаем config.env

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev-secret-change-me")

MONGO_URI = os.getenv("MONGO_URI")
MONGO_DB  = os.getenv("MONGO_DB",  "medplatforma")

password = urllib.parse.quote_plus("medpass123")  # если пароль с особыми символами
uri = "mongodb+srv://medadmin:Med12345!@medplatforma.cnv7fbo.mongodb.net/medplatforma?retryWrites=true&w=majority"
client = MongoClient(uri)
db = client["medplatforma"]

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
    """Парсит 'YYYY-MM-DDTHH:MM' или datetime -> datetime | None"""
    if isinstance(s, datetime):
        return s
    if not s:
        return None
    try:
        # допускаем обе формы: '2025-08-14T17:05' и '2025-08-14 17:05'
        s = s.replace(" ", "T")
        return datetime.strptime(s[:16], "%Y-%m-%dT%H:%M")
    except Exception:
        return None


def add_minutes(dt, mins):
    return dt + timedelta(minutes=int(mins))


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

# --- быстрая health‑проверка (смок-тест)
@app.route("/healthz")
def healthz():
    try:
        client.admin.command("ping")
        return jsonify({"ok": True, "db": MONGO_DB})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

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
    data = request.get_json()
    doctor_id = data["doctor_id"]
    doctor = db.doctors.find_one({"_id": doctor_id})
    if not doctor:
        return jsonify({"error": "not found"}), 404
    # Пример структуры расписания: {"0": {"start": "08:00", "end": "18:00"}, ...}
    schedule = doctor.get("schedule", {})
    # Находим все события по врачу за нужную дату (или диапазон)
    events = list(db.events.find({"doctor_id": doctor_id}))
    busy_slots = [{"start": e["start"], "end": e.get("end", e["start"])} for e in events]
    return jsonify(
        {
            "schedule": schedule,  # dict с днями недели, когда врач работает
            "busy_slots": busy_slots,  # список {"start": "...", "end": "..."}
        }
    )


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


@app.route("/xray_room")
def xray_room():
    xrays = list(db.xrays.find())
    patients = {str(p["_id"]): p for p in db.patients.find()}
    doctors = {str(d["_id"]): d for d in db.doctors.find()}
    # фильтры (добавь, если надо)
    return render_template("xray_room.html", xrays=xrays, patients=patients, doctors=doctors)


@app.route("/add_xray", methods=["GET", "POST"])
def add_xray():
    if request.method == "POST":
        # Загружаем файл (image), сохраняем в /static/xrays/
        # Вносим в коллекцию xrays все данные
        # ...
        flash("Снимок успешно добавлен!", "success")
        return redirect(url_for("xray_room"))
    patients = list(db.patients.find())
    doctors = list(db.doctors.find())
    return render_template("add_xray.html", patients=patients, doctors=doctors)


from bson import ObjectId


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
    logs = list(db.logs.find().sort("time", -1))  # Сортируем по дате
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


# 1) Справочники для модалки
@app.route("/api/dicts")
def api_dicts():
    docs = list(db.doctors.find({}, {"full_name": 1}))
    srvs = list(db.services.find({}, {"name": 1, "duration_min": 1, "price": 1}))
    return jsonify(
        {
            "ok": True,
            "doctors": [{"id": str(x["_id"]), "name": x.get("full_name", "")} for x in docs],
            "services": [
                {
                    "id": str(x["_id"]),
                    "name": x.get("name", ""),
                    "duration_min": x.get("duration_min", 30),
                    "price": x.get("price", 0),
                }
                for x in srvs
            ],
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

    # Пересчитать статус кабинета
    try:
        if room_id:
            recalc_room_status(room_id)
    except Exception:
        pass

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

    # собрать обновления
    updates = {}

    # привязки
    def as_oid(key):
        v = data.get(key)
        if not v:
            return None
        try:
            return ObjectId(v)
        except Exception:
            return None

    doc_oid = as_oid("doctor_id")
    pat_oid = as_oid("patient_id")
    srv_oid = as_oid("service_id")
    room_oid = as_oid("room_id") or a.get("room_id")

    if doc_oid:
        updates["doctor_id"] = doc_oid
    if pat_oid:
        updates["patient_id"] = pat_oid
    if srv_oid:
        updates["service_id"] = srv_oid
    if room_oid:
        updates["room_id"] = room_oid

    # статус/коммент
    if "status_key" in data:
        updates["status_key"] = (data.get("status_key") or "scheduled").strip()
    if "comment" in data:
        updates["comment"] = (data.get("comment") or "").strip()

    # время
    start_dt = to_dt(data.get("start")) or a.get("start")
    end_dt = to_dt(data.get("end")) or a.get("end")

    # если конец не задан — вычислим по услуге (или 30 мин)
    if not end_dt:
        dur = 30
        if srv_oid:
            srv = db.services.find_one({"_id": srv_oid}, {"duration_min": 1})
            if srv:
                try:
                    dur = int(srv.get("duration_min", 30))
                except Exception:
                    dur = 30
        end_dt = add_minutes(start_dt, dur)

    if not isinstance(start_dt, datetime) or not isinstance(end_dt, datetime) or end_dt <= start_dt:
        return jsonify({"ok": False, "error": "bad_dates"}), 400

    updates["start"] = start_dt
    updates["end"] = end_dt

    # конфликт по кабинету
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
    except Exception:
        pass

    return jsonify({"ok": True})


# --- 2.3.3: перенос/растягивание события мышкой (DnD/resize) ---
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
        return jsonify({"ok": False, "error": "bad_dates"}), 400

    appt = db.appointments.find_one({"_id": oid}, {"room_id": 1})
    if not appt:
        return jsonify({"ok": False, "error": "not_found"}), 404

    room_id = appt.get("room_id")

    # конфликт по кабинету
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
        recalc_room_status(room_id)
    except Exception:
        pass

    return jsonify({"ok": True})


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


# =================== /ПАЦИЕНТЫ (patients) ======================

# ======= ЗАПУСК =======
if __name__ == "__main__":
    app.run(debug=True)
