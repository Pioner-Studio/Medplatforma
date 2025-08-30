from datetime import datetime, time, timedelta
from bson import ObjectId
from flask import (
    Blueprint,
    current_app,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    jsonify,
)

bp = Blueprint("schedule", __name__, url_prefix="/schedule")

# Константы расписания (поддерживают чек-лист)
CLINIC_START = time(9, 0)
CLINIC_END = time(21, 0)
SLOT = timedelta(minutes=15)


def _parse_oid(val):
    try:
        return ObjectId(val) if val else None
    except Exception:
        return None


def _is_in_business_hours(dt: datetime) -> bool:
    t = dt.time()
    return (t >= CLINIC_START) and (t <= CLINIC_END)


def _is_slot_aligned(dt: datetime) -> bool:
    return (dt.minute % 15 == 0) and (dt.second == 0) and (dt.microsecond == 0)


@bp.route("/", methods=["GET"])
def list_view():
    """Табличный вид расписания (по кабинетам/врачам)."""
    db = current_app.config["DB"]
    rooms = list(db.rooms.find({}, {"_id": 1, "name": 1}))
    doctors = list(db.doctors.find({}, {"_id": 1, "full_name": 1}))
    return render_template("schedule/list.html", rooms=rooms, doctors=doctors)


@bp.route("/add", methods=["POST"])
def add_appointment():
    """
    Создаёт запись в нормализованной коллекции appointments:
    start/end (datetime), ссылки на doctor_id, patient_id, room_id, service_id, статус, заметка.
    """
    db = current_app.config["DB"]
    form = request.form or request.json or {}

    # ожидание ISO-строк от фронта
    start_str = form.get("start")
    end_str = form.get("end")
    doctor_id = _parse_oid(form.get("doctor_id"))
    patient_id = _parse_oid(form.get("patient_id"))
    room_id = _parse_oid(form.get("room_id"))
    service_id = _parse_oid(form.get("service_id"))
    note = form.get("note", "").strip()

    if not start_str or not end_str or not room_id:
        return jsonify({"ok": False, "error": "start/end/room_id are required"}), 400

    try:
        start = datetime.fromisoformat(start_str)
        end = datetime.fromisoformat(end_str)
    except Exception:
        return jsonify({"ok": False, "error": "Invalid datetime format (use ISO)"}), 400

    if start >= end:
        return jsonify({"ok": False, "error": "end must be after start"}), 400

    # Бизнес-правила: окно + шаг 15 минут
    if not (_is_in_business_hours(start) and _is_in_business_hours(end)):
        return jsonify({"ok": False, "error": "Outside clinic working hours (09:00–21:00)"}), 400

    if not (_is_slot_aligned(start) and _is_slot_aligned(end)):
        return jsonify({"ok": False, "error": "Time must align to 15-min slots"}), 400

    # Проверка конфликтов: по кабинету и врачу (если указан)
    conflict_filters = [{"room_id": room_id, "start": {"$lt": end}, "end": {"$gt": start}}]
    if doctor_id:
        conflict_filters.append(
            {"doctor_id": doctor_id, "start": {"$lt": end}, "end": {"$gt": start}}
        )

    conflict = db.appointments.find_one({"$or": conflict_filters})
    if conflict:
        return jsonify({"ok": False, "error": "Time conflict detected"}), 409

    doc = {
        "start": start,
        "end": end,
        "room_id": room_id,
        "doctor_id": doctor_id,
        "patient_id": patient_id,
        "service_id": service_id,
        "status": "scheduled",
        "note": note,
        "created_at": datetime.utcnow(),
    }
    ins = db.appointments.insert_one(doc)
    return jsonify({"ok": True, "id": str(ins.inserted_id)})


# (опционально) простой API свободных слотов для подсказок наводкой
@bp.route("/free_slots", methods=["GET"])
def free_slots():
    """
    ?room_id=&date=YYYY-MM-DD&duration=30
    Возвращает ISO-диапазоны свободных слотов на день для комнаты (учтёт конфликты).
    """
    db = current_app.config["DB"]
    room_id = _parse_oid(request.args.get("room_id"))
    date_str = request.args.get("date")
    duration_min = int(request.args.get("duration", "15"))

    if not (room_id and date_str):
        return jsonify([])

    try:
        day = datetime.fromisoformat(date_str).date()
    except Exception:
        return jsonify([])

    start_dt = datetime.combine(day, CLINIC_START)
    end_dt = datetime.combine(day, CLINIC_END)

    busy = list(
        db.appointments.find(
            {"room_id": room_id, "start": {"$lt": end_dt}, "end": {"$gt": start_dt}},
            {"start": 1, "end": 1, "_id": 0},
        )
    )
    busy_ranges = [(b["start"], b["end"]) for b in busy]

    cur = start_dt
    out = []
    step = timedelta(minutes=15)
    need = timedelta(minutes=duration_min)

    while cur + need <= end_dt:
        candidate_start = cur
        candidate_end = cur + need
        # конфликт?
        conflict = any(not (candidate_end <= s or candidate_start >= e) for s, e in busy_ranges)
        if not conflict:
            out.append({"start": candidate_start.isoformat(), "end": candidate_end.isoformat()})
        cur += step

    return jsonify(out)
