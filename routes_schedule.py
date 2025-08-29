# routes_schedule.py
from datetime import datetime, time, timedelta
from typing import Optional, Dict, Any, List

from flask import Blueprint, current_app, request, jsonify
from bson import ObjectId

# -------------------------
#  Блюпринты
# -------------------------
api_bp = Blueprint("api", __name__, url_prefix="/api")
schedule_bp = Blueprint("schedule", __name__, url_prefix="/schedule")


# -------------------------
#  Доступ к БД
# -------------------------
def get_db():
    """
    Унифицированный доступ к БД:
    - current_app.config['DB'] (PyMongo Database)
    - current_app.mongo.db     (Flask-PyMongo)
    - current_app.db           (кастомно)
    """
    db = (
        current_app.config.get("DB")
        or getattr(getattr(current_app, "mongo", None), "db", None)
        or getattr(current_app, "db", None)
    )
    if db is None:
        raise RuntimeError("DB is not configured on current_app")
    return db


# -------------------------
#  Хелперы
# -------------------------
CLINIC_START = time(9, 0)
CLINIC_END = time(21, 0)
SLOT_MIN = 15


def _oid(v: Optional[str]) -> Optional[ObjectId]:
    try:
        return ObjectId(v) if v else None
    except Exception:
        return None


def _in_hours(dt: datetime) -> bool:
    t = dt.time()
    return CLINIC_START <= t <= CLINIC_END


def _aligned(dt: datetime) -> bool:
    return dt.second == 0 and dt.microsecond == 0 and dt.minute % SLOT_MIN == 0


def _iso(s: str) -> datetime:
    return datetime.fromisoformat(s)


# -------------------------
#  /api/dicts — словари для UI
# -------------------------
@api_bp.get("/dicts")
def api_dicts():
    """
    Возвращает списки докторов, пациентов, кабинетов, услуг:
    {
      "ok": true,
      "doctors":  [{"id": "...", "name": "..."}, ...],
      "patients": [{"id": "...", "name": "..."}, ...],
      "rooms":    [{"id": "...", "name": "..."}, ...],
      "services": [{"id": "...", "name": "...", "duration_min": 30}, ...]
    }
    """
    db = get_db()

    def map_coll(coll, fields, name_key):
        out = []
        for x in coll:
            item = {"id": str(x["_id"]), "name": x.get(name_key, "")}
            # прокидываем duration_min для услуги, если есть
            if "duration_min" in fields:
                item["duration_min"] = int(x.get("duration_min", SLOT_MIN))
            out.append(item)
        return out

    doctors = map_coll(db.doctors.find({}, {"full_name": 1}), {"full_name"}, "full_name")
    patients = map_coll(db.patients.find({}, {"full_name": 1}), {"full_name"}, "full_name")
    rooms = map_coll(db.rooms.find({}, {"name": 1}), {"name"}, "name")
    services = map_coll(
        db.services.find({}, {"name": 1, "duration_min": 1}), {"name", "duration_min"}, "name"
    )

    return jsonify(ok=True, doctors=doctors, patients=patients, rooms=rooms, services=services)


# -------------------------
#  /api/events — события для FullCalendar
# -------------------------
@api_bp.get("/events")
def api_events():
    """
    Query:
      start=ISO, end=ISO
      doctor_id?=oid, service_id?=oid, room_id? / room_name?
    Возвращает массив событий для FullCalendar.
    """
    db = get_db()
    qs = request.args

    try:
        start = _iso(qs.get("start"))
        end = _iso(qs.get("end"))
    except Exception:
        return jsonify([])

    q: Dict[str, Any] = {"start": {"$lt": end}, "end": {"$gt": start}}

    # фильтры (если приходят)
    did = _oid(qs.get("doctor_id"))
    sid = _oid(qs.get("service_id"))
    rid = _oid(qs.get("room_id"))
    rname = qs.get("room_name")

    if did:
        q["doctor_id"] = did
    if sid:
        q["service_id"] = sid
    if rid:
        q["room_id"] = rid
    if rname:  # фильтр по имени кабинета
        room = db.rooms.find_one({"name": rname}, {"_id": 1})
        q["room_id"] = room["_id"] if room else ObjectId("0" * 24)  # ничего не найдёт

    items = db.appointments.find(q)

    def label(doc: Dict[str, Any]) -> str:
        # подписываем: Время — Услуга — Пациент/Доктор
        parts: List[str] = []

        if doc.get("service_id"):
            s = db.services.find_one({"_id": doc["service_id"]}, {"name": 1})
            if s:
                parts.append(s.get("name", ""))

        if doc.get("patient_id"):
            p = db.patients.find_one({"_id": doc["patient_id"]}, {"full_name": 1})
            if p:
                parts.append(p.get("full_name", ""))

        if not parts and doc.get("doctor_id"):
            d = db.doctors.find_one({"_id": doc["doctor_id"]}, {"full_name": 1})
            if d:
                parts.append(d.get("full_name", ""))

        return " — ".join([x for x in parts if x])

    events = []
    for it in items:
        events.append(
            {
                "id": str(it["_id"]),
                "start": it["start"].isoformat(),
                "end": it["end"].isoformat(),
                "title": label(it) or "Запись",
            }
        )
    return jsonify(events)


# -------------------------
#  /api/doctor_schedule — график врача
# -------------------------
@api_bp.post("/doctor_schedule")
def api_doctor_schedule():
    """
    Body: {"doctor_id": "<oid>"}
    Ответ: {"ok": true, "schedule": {"0":{"start":"09:00","end":"21:00"}, ...}}
    где 0..6 — пн..вс
    """
    payload = request.get_json(silent=True) or {}
    did = payload.get("doctor_id")
    default_sched = {str(i): {"start": "09:00", "end": "21:00"} for i in range(7)}

    if not did:
        return jsonify(ok=True, schedule=default_sched)

    db = get_db()
    doc = db.doctors.find_one({"_id": _oid(did)}, {"schedule": 1, "working_hours": 1})

    sched = None
    if doc:
        if isinstance(doc.get("schedule"), dict):
            sched = doc["schedule"]
        elif isinstance(doc.get("working_hours"), dict):
            map_wd = {"mon": 0, "tue": 1, "wed": 2, "thu": 3, "fri": 4, "sat": 5, "sun": 6}
            sched = {
                str(map_wd[k]): {"start": v.get("start"), "end": v.get("end")}
                for k, v in doc["working_hours"].items()
                if v
            }
    return jsonify(ok=True, schedule=sched or default_sched)


# -------------------------
#  /schedule/api/create — создать запись
# -------------------------
@schedule_bp.post("/api/create")
def schedule_api_create():
    db = get_db()
    p = request.get_json(force=True, silent=True) or {}

    start_str = p.get("start")
    end_str = p.get("end")
    room_id = _oid(p.get("room_id"))

    if not start_str or not end_str or not room_id:
        return jsonify(ok=False, error="start/end/room_id are required"), 400

    try:
        start = _iso(start_str)
        end = _iso(end_str)
    except Exception:
        return jsonify(ok=False, error="Invalid datetime (ISO required)"), 400

    if start >= end:
        return jsonify(ok=False, error="end must be after start"), 400
    if not (_in_hours(start) and _in_hours(end)):
        return jsonify(ok=False, error="Outside working hours (09:00–21:00)"), 400
    if not (_aligned(start) and _aligned(end)):
        return jsonify(ok=False, error="Time must align to 15-min slots"), 400

    did = _oid(p.get("doctor_id"))
    pid = _oid(p.get("patient_id"))
    sid = _oid(p.get("service_id"))
    note = (p.get("note") or "").strip()

    conflict_filters = [{"room_id": room_id, "start": {"$lt": end}, "end": {"$gt": start}}]
    if did:
        conflict_filters.append({"doctor_id": did, "start": {"$lt": end}, "end": {"$gt": start}})

    if db.appointments.find_one({"$or": conflict_filters}):
        return jsonify(ok=False, error="Time conflict detected"), 409

    ins = db.appointments.insert_one(
        {
            "start": start,
            "end": end,
            "room_id": room_id,
            "doctor_id": did,
            "patient_id": pid,
            "service_id": sid,
            "status": "scheduled",
            "note": note,
            "created_at": datetime.utcnow(),
        }
    )
    return jsonify(ok=True, id=str(ins.inserted_id))


# -------------------------
#  /schedule/api/move — перенести запись
# -------------------------
@schedule_bp.post("/api/move")
def schedule_api_move():
    db = get_db()
    p = request.get_json(force=True, silent=True) or {}
    appt_id = _oid(p.get("id"))
    if not appt_id:
        return jsonify(ok=False, error="id required"), 400
    try:
        start = _iso(p["start"])
        end = _iso(p["end"])
    except Exception:
        return jsonify(ok=False, error="Invalid datetime (ISO required)"), 400

    if start >= end:
        return jsonify(ok=False, error="end must be after start"), 400
    if not (_in_hours(start) and _in_hours(end)):
        return jsonify(ok=False, error="Outside working hours (09:00–21:00)"), 400
    if not (_aligned(start) and _aligned(end)):
        return jsonify(ok=False, error="Time must align to 15-min slots"), 400

    appt = db.appointments.find_one({"_id": appt_id})
    if not appt:
        return jsonify(ok=False, error="appointment not found"), 404

    room_id = appt.get("room_id")
    doctor_id = appt.get("doctor_id")

    conflict_filters = [
        {"room_id": room_id, "start": {"$lt": end}, "end": {"$gt": start}, "_id": {"$ne": appt_id}}
    ]
    if doctor_id:
        conflict_filters.append(
            {
                "doctor_id": doctor_id,
                "start": {"$lt": end},
                "end": {"$gt": start},
                "_id": {"$ne": appt_id},
            }
        )

    if db.appointments.find_one({"$or": conflict_filters}):
        return jsonify(ok=False, error="Time conflict detected"), 409

    db.appointments.update_one({"_id": appt_id}, {"$set": {"start": start, "end": end}})
    return jsonify(ok=True)


# -------------------------
#  /schedule/api/delete — удалить запись
# -------------------------
@schedule_bp.post("/api/delete")
def schedule_api_delete():
    db = get_db()
    p = request.get_json(force=True, silent=True) or {}
    appt_id = _oid(p.get("id"))
    if not appt_id:
        return jsonify(ok=False, error="id required"), 400

    res = db.appointments.delete_one({"_id": appt_id})
    if res.deleted_count != 1:
        return jsonify(ok=False, error="not found"), 404
    return jsonify(ok=True)
