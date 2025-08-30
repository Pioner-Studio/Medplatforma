# routes_schedule.py  — минимальный рабочий набор ручек для календаря
from datetime import datetime, time, timedelta
from bson import ObjectId
from flask import Blueprint, current_app, request, jsonify

schedule_bp = Blueprint("schedule", __name__)  # будет смонтирован как /schedule


from flask import current_app


def db():
    """
    Единая точка доступа к БД без булевых проверок.
    Поддерживает:
      - current_app.config["DB"] (PyMongo Database)
      - current_app.mongo.db     (Flask-PyMongo)
      - current_app.db           (кастом)
    """
    d = current_app.config.get("DB")
    if d is None:
        mongo = getattr(current_app, "mongo", None)
        d = getattr(mongo, "db", None) if mongo is not None else None
    if d is None:
        d = getattr(current_app, "db", None)
    if d is None:
        raise RuntimeError("DB is not configured on current_app")
    return d


def _oid(v):
    if not v:
        return None
    return v if isinstance(v, ObjectId) else ObjectId(v)


# --- бизнес-ограничения клиники ---
CLINIC_START = time(9, 0)
CLINIC_END = time(21, 0)
SLOT_MIN = 15


def _to_dt(s: str):
    try:
        return datetime.fromisoformat(s) if s else None
    except Exception:
        return None


def _in_hours(dt: datetime) -> bool:
    return CLINIC_START <= dt.time() <= CLINIC_END


def _slot_ok(dt: datetime) -> bool:
    return dt.minute % SLOT_MIN == 0 and dt.second == 0 and dt.microsecond == 0


# --- 1) создать запись: POST /schedule/api/create ---
@schedule_bp.route("/api/create", methods=["POST"])
def api_create_appointment():
    payload = request.get_json(force=True, silent=True) or {}
    start = _to_dt(payload.get("start"))
    end = _to_dt(payload.get("end"))
    room_id = _oid(payload.get("room_id"))
    doctor_id = _oid(payload.get("doctor_id"))
    patient_id = _oid(payload.get("patient_id"))
    service_id = _oid(payload.get("service_id"))
    note = (payload.get("note") or "").strip()

    if not (start and end and room_id):
        return jsonify({"ok": False, "error": "start/end/room_id required"}), 400
    if not (_in_hours(start) and _in_hours(end)):
        return jsonify({"ok": False, "error": "Outside working hours (09:00–21:00)"}), 400
    if not (_slot_ok(start) and _slot_ok(end)):
        return jsonify({"ok": False, "error": "Time must align to 15-min slots"}), 400
    if start >= end:
        return jsonify({"ok": False, "error": "end must be after start"}), 400

    D = db()
    # конфликт по кабинету и (опционально) по врачу
    conflict_q = [{"room_id": room_id, "start": {"$lt": end}, "end": {"$gt": start}}]
    if doctor_id:
        conflict_q.append({"doctor_id": doctor_id, "start": {"$lt": end}, "end": {"$gt": start}})
    if D.appointments.find_one({"$or": conflict_q}):
        return jsonify({"ok": False, "error": "conflict"}), 409

    ins = D.appointments.insert_one(
        {
            "start": start,
            "end": end,
            "room_id": room_id,
            "doctor_id": doctor_id,
            "patient_id": patient_id,
            "service_id": service_id,
            "status_key": "scheduled",
            "comment": note,
            "created_at": datetime.utcnow(),
        }
    )
    return jsonify({"ok": True, "id": str(ins.inserted_id)})


# --- 2) перенести/растянуть: POST /schedule/api/move ---
@schedule_bp.route("/api/move", methods=["POST"])
def api_move_appointment():
    p = request.get_json(force=True, silent=True) or {}
    appt_id = _oid(p.get("id"))
    start = _to_dt(p.get("start"))
    end = _to_dt(p.get("end"))
    if not (appt_id and start and end):
        return jsonify({"ok": False, "error": "id/start/end required"}), 400
    if not (_in_hours(start) and _in_hours(end)):
        return jsonify({"ok": False, "error": "Outside working hours (09:00–21:00)"}), 400
    if not (_slot_ok(start) and _slot_ok(end)):
        return jsonify({"ok": False, "error": "Time must align to 15-min slots"}), 400
    if start >= end:
        return jsonify({"ok": False, "error": "end must be after start"}), 400

    D = db()
    appt = D.appointments.find_one({"_id": appt_id}, {"room_id": 1, "doctor_id": 1})
    if not appt:
        return jsonify({"ok": False, "error": "not_found"}), 404

    room_id = appt.get("room_id")
    doctor_id = appt.get("doctor_id")

    conflict_q = [
        {"room_id": room_id, "start": {"$lt": end}, "end": {"$gt": start}, "_id": {"$ne": appt_id}}
    ]
    if doctor_id:
        conflict_q.append(
            {
                "doctor_id": doctor_id,
                "start": {"$lt": end},
                "end": {"$gt": start},
                "_id": {"$ne": appt_id},
            }
        )
    if D.appointments.find_one({"$or": conflict_q}):
        return jsonify({"ok": False, "error": "conflict"}), 409

    D.appointments.update_one({"_id": appt_id}, {"$set": {"start": start, "end": end}})
    return jsonify({"ok": True})


# --- 3) удалить: POST /schedule/api/delete ---
@schedule_bp.route("/api/delete", methods=["POST"])
def api_delete_appointment():
    p = request.get_json(force=True, silent=True) or {}
    appt_id = _oid(p.get("id"))
    if not appt_id:
        return jsonify({"ok": False, "error": "id required"}), 400

    D = db()
    res = D.appointments.delete_one({"_id": appt_id})
    return (
        jsonify({"ok": True})
        if res.deleted_count == 1
        else (jsonify({"ok": False, "error": "not_found"}), 404)
    )
