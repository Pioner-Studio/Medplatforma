# seed_ru.py
import os
from datetime import datetime, timedelta
from pymongo import MongoClient, ASCENDING, TEXT
from bson import ObjectId
from dotenv import load_dotenv

from ru_catalogs import (
    DOCTOR_ROLES, DOCTORS, PATIENTS, ROOMS, SERVICES, VISIT_STATUSES
)

load_dotenv()
MONGO_URI = os.getenv("MONGO_URI", "mongodb://127.0.0.1:27017")
DB_NAME   = os.getenv("DB_NAME", "medplatforma")

client = MongoClient(MONGO_URI)
db = client[DB_NAME]
utc = lambda: datetime.utcnow()

def upsert(coll, filt, doc):
    doc["updated_at"] = utc()
    existing = coll.find_one(filt)
    if existing:
        coll.update_one({"_id": existing["_id"]}, {"$set": doc})
        return existing["_id"]
    doc.setdefault("created_at", utc())
    return coll.insert_one(doc).inserted_id

def ensure_indexes():
    db.patients.create_index([("full_name", TEXT)])
    db.doctors.create_index([("full_name", TEXT)])
    db.rooms.create_index([("name", ASCENDING)], unique=True)
    db.services.create_index([("code", ASCENDING)], unique=True)
    db.visit_statuses.create_index([("key", ASCENDING)], unique=True)
    db.appointments.create_index([("start", ASCENDING)])

def seed_statuses():
    ids = {}
    for s in VISIT_STATUSES:
        _id = upsert(db.visit_statuses, {"key": s["key"]}, s)
        ids[s["key"]] = _id
    return ids

def seed_rooms():
    m = {}
    for r in ROOMS:
        _id = upsert(db.rooms, {"name": r["name"]}, r)
        m[r["name"]] = _id
    return m

def seed_services():
    m = {}
    for s in SERVICES:
        s.setdefault("is_active", True)
        _id = upsert(db.services, {"code": s["code"]}, s)
        m[s["code"]] = _id
    return m

def seed_patients():
    ids = []
    for i,(name, gender) in enumerate(PATIENTS, start=1):
        p = {
            "full_name": name,
            "birthday": datetime(1990 + (i % 10), (i % 12) + 1, (i % 27) + 1),
            "gender": gender,
            "contacts": {
                "phone": f"+7 999 000-{i:04d}",
                "email": f"patient{i}@clubstom.pro",
                "whatsapp": f"+7 999 000-{i:04d}",
                "telegram": f"@patient{i}"
            },
            "address": {"city": "Москва", "street": f"Улица Пример, д.{10+i}", "zip": f"10{i:02d}"},
            "notes": "Демо‑пациент",
            "avatar": f"/static/avatars/patients/p{i}.jpg",
            "created_at": utc(), "updated_at": utc()
        }
        _id = upsert(db.patients, {"contacts.email": p["contacts"]["email"]}, p)
        ids.append(_id)
    return ids

def seed_doctors(room_map):
    room_names = list(room_map.keys())
    ids = []
    for i, fio in enumerate(DOCTORS, start=1):
        # распределяем роли по кругу
        role = list(DOCTOR_ROLES.keys())[(i-1) % len(DOCTOR_ROLES)]
        specs = DOCTOR_ROLES[role]
        primary = room_map[room_names[(i-1) % len(room_names)]]
        available = [primary]
        if len(room_names) > 1:
            available.append(room_map[room_names[i % len(room_names)]])
        d = {
            "full_name": fio,
            "role": role,
            "specialties": specs,
            "contacts": {
                "phone": f"+7 495 555-{i:04d}",
                "email": f"doctor{i}@clubstom.pro",
                "whatsapp": f"+7 495 555-{i:04d}",
                "telegram": f"@doctor{i}"
            },
            "primary_room_id": primary,
            "room_ids": available,
            "avatar": f"/static/avatars/doctors/d{i}.jpg",
            "is_active": True,
        }
        _id = upsert(db.doctors, {"contacts.email": d["contacts"]["email"]}, d)
        ids.append(_id)
    return ids

def seed_appointments(patient_ids, doctor_ids, room_map, service_map):
    """
    Создаём демо-записи ровно в ТЕКУЩУЮ НЕДЕЛЮ (пн-вс), чтобы они сразу
    отображались в представлении 'Неделя'.
    """
    # Понедельник текущей недели в 10:00 (локальное время машины)
    today = datetime.now()
    week_start = today - timedelta(days=today.weekday())  # понедельник
    anchor = week_start.replace(hour=10, minute=0, second=0, microsecond=0)
    week_end = anchor + timedelta(days=7)

    # Чистим только наши демо-записи в этой неделе (чтобы не плодить дубликаты)
    db.appointments.delete_many({
        "notes": "Демо‑запись",
        "start": {"$gte": anchor, "$lt": week_end}
    })

    docs = list(db.doctors.find({"_id": {"$in": doctor_ids}}))
    pats = list(db.patients.find({"_id": {"$in": patient_ids}}))
    service_ids = list(service_map.values())

    for idx, d in enumerate(docs):
        # разбрасываем врача по дням недели (пн‑пт)
        day_offset = idx % 5
        for j in range(2):  # по 2 записи на врача
            patient = pats[(idx*2 + j) % len(pats)]
            service_id = service_ids[(idx + j) % len(service_ids)]
            duration = db.services.find_one({"_id": service_id})["duration_min"]

            start = anchor + timedelta(days=day_offset, hours=2*j + (idx % 2))  # 10:00/12:00 или 11:00/13:00
            end = start + timedelta(minutes=duration)

            appt = {
                "patient_id": patient["_id"],
                "doctor_id": d["_id"],
                "room_id": d.get("primary_room_id"),
                "service_id": service_id,
                "status_key": ["scheduled","completed","cancelled","no_show"][(idx+j)%4],
                "start": start,
                "end": end,
                "notes": "Демо‑запись",
            }
            # уникальность по пациенту+доктору+start
            upsert(db.appointments,
                   {"patient_id": appt["patient_id"], "doctor_id": appt["doctor_id"], "start": appt["start"]},
                   appt)

def main():
    print(f"→ Подключение к {MONGO_URI} / DB={DB_NAME}")
    ensure_indexes()

    print("→ Статусы…");      seed_statuses()
    print("→ Кабинеты…");     room_map = seed_rooms()
    print("→ Услуги…");       service_map = seed_services()
    print("→ Пациенты…");     patient_ids = seed_patients()
    print("→ Врачи…");        doctor_ids = seed_doctors(room_map)
    print("→ Демозаписи…");   seed_appointments(patient_ids, doctor_ids, room_map, service_map)

    print("Готово. Все справочники и демо‑данные на русском.")

if __name__ == "__main__":
    main()
