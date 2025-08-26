import os
import random
from datetime import datetime, date, time, timedelta

from pymongo import MongoClient
from pymongo.errors import PyMongoError
from bson import ObjectId  # 👈 добавляем сюда

# =========================
#  Config / DB (via .env)
# =========================
from dotenv import load_dotenv

load_dotenv()


MONGO_URI = os.getenv("MONGO_URI")  # из .env
DB_NAME = os.getenv("DB_NAME", "medplatforma")


def _connect():
    if not MONGO_URI:
        raise RuntimeError("MONGO_URI is not set. Put it into .env")

    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=8000)
    try:
        client.admin.command("ping")  # проверка соединения/авторизации
    except PyMongoError as e:
        print(
            "\n[seed] Mongo connection/auth FAILED.\n"
            "Проверьте:\n"
            "  1) .env → корректный MONGO_URI (логин/пароль, спецсимволы)\n"
            "  2) Atlas → Network Access: ваш IP в белом списке\n"
            "  3) Atlas → Database Access: пользователь/роль\n"
            '  4) Установлен dnspython: pip install "pymongo[srv]"\n'
        )
        raise
    return client


client = _connect()
db = client[DB_NAME]

# Рабочие часы и шаг
CLINIC_START = time(9, 0)
CLINIC_END = time(21, 0)
SLOT_MIN = 15  # минут


# =========================
#  Helpers
# =========================
def align_to_slot(dt: datetime) -> datetime:
    m = (dt.minute // SLOT_MIN) * SLOT_MIN
    return dt.replace(minute=m, second=0, microsecond=0)


def in_hours(dt: datetime) -> bool:
    t = dt.time()
    return CLINIC_START <= t <= CLINIC_END


def has_conflict(
    start: datetime, end: datetime, room_id: ObjectId, doctor_id: ObjectId | None
) -> bool:
    ors = [{"room_id": room_id, "start": {"$lt": end}, "end": {"$gt": start}}]
    if doctor_id:
        ors.append({"doctor_id": doctor_id, "start": {"$lt": end}, "end": {"$gt": start}})
    return db.appointments.find_one({"$or": ors}) is not None


# =========================
#  Seeds
# =========================
def seed_rooms():
    """Шесть кабинетов без рентгена (идемпотентно)."""
    rooms_target = [
        "Детский",
        "Ортопедия",
        "Хирургия",
        "Ортодонтия",
        "Терапия",
        "Кабинет 6 (кастомный)",
    ]
    # подчистим лишние (в т.ч. «Рентген»)
    db.rooms.delete_many({"name": {"$nin": rooms_target}})
    for name in rooms_target:
        db.rooms.update_one({"name": name}, {"$set": {"name": name}}, upsert=True)
    print(f"[seed] rooms → OK ({len(rooms_target)} шт.)")


def seed_doctors():
    """Демо-врачи (без рентгенолога). upsert по full_name."""
    names_specs = [
        ("Смирнов Павел", "Терапевт"),
        ("Иванова Анна", "Хирург"),
        ("Кузнецов Дмитрий", "Ортопед"),
        ("Попова Мария", "Ортодонт"),
        ("Волков Артём", "Детский стоматолог"),
        ("Соколова Екатерина", "Гигиенист"),
        ("Лебедев Сергей", "Имплантолог"),
        ("Козлова Юлия", "Пародонтолог"),
    ]
    for i, (name, spec) in enumerate(names_specs, start=1):
        db.doctors.update_one(
            {"full_name": name},
            {
                "$set": {
                    "full_name": name,
                    "specialization": spec,
                    "email": f"doctor{i}@mail.ru",
                    "phone": f"+7999000{100+i:03d}",
                    "avatar_url": f"/static/avatars/doctor_{(i-1)%6+1}.png",
                    "status": "активен",
                }
            },
            upsert=True,
        )
    print(f"[seed] doctors → OK ({len(names_specs)} шт.)")


def seed_patients():
    """Демо-пациенты. upsert по full_name."""
    names = [
        "Петров Иван",
        "Сидорова Ольга",
        "Михайлов Сергей",
        "Егорова Татьяна",
        "Орлов Дмитрий",
        "Семёнова Мария",
        "Васильев Антон",
        "Громова Наталья",
        "Зайцев Алексей",
        "Тихонова Ирина",
    ]
    for i, name in enumerate(names, start=1):
        # простой birthdate: 1980–1989, рандомный месяц/день
        bd = date(1980 + random.randint(0, 9), random.randint(1, 12), random.randint(1, 28))
        db.patients.update_one(
            {"full_name": name},
            {
                "$set": {
                    "full_name": name,
                    "birthdate": bd.isoformat(),
                    "phone": f"+7999000{200+i:03d}",
                    "email": f"patient{i}@mail.ru",
                    "avatar_url": f"/static/avatars/patient_{(i-1)%6+1}.png",
                }
            },
            upsert=True,
        )
    print(f"[seed] patients → OK ({len(names)} шт.)")


def seed_services():
    """
    Базовые услуги с обязательным уникальным code.
    - правим старые документы без code (генерируем из name);
    - создаём/обновляем базовый набор (upsert по name) с корректным code.
    """
    import re
    import random

    def make_code(name: str, suffix: str = "") -> str:
        base = re.sub(r"\W+", "_", (name or "SERVICE").upper()).strip("_")
        return f"SVC_{base}{suffix}"

    # 0) Индекс на code (если вдруг его нет) — уникальный
    try:
        db.services.create_index("code", unique=True)
    except Exception:
        # уже есть — норм
        pass

    # 1) Миграция: для существующих услуг без code или с code=None проставим код
    existing = list(
        db.services.find(
            {"$or": [{"code": {"$exists": False}}, {"code": None}]}, {"_id": 1, "name": 1}
        )
    )
    for doc in existing:
        name = doc.get("name") or "SERVICE"
        code = make_code(name)
        # если такой code уже есть у другого документа — добавим суффикс хвостом _id
        while db.services.find_one({"code": code, "_id": {"$ne": doc["_id"]}}):
            code = make_code(name, suffix=f"_{str(doc['_id'])[-4:]}")
        db.services.update_one({"_id": doc["_id"]}, {"$set": {"code": code}})

    # 2) Базовый набор услуг
    base = [
        ("Консультация", 15, 0),
        ("Пломба", 45, 3500),
        ("Лечение кариеса", 60, 5000),
        ("Гигиена", 60, 4500),
        ("Имплантация", 90, 65000),
    ]

    for name, dur, price in base:
        code = make_code(name)
        # если такой code почему-то занят другой услугой — добавим суффикс
        while db.services.find_one({"code": code, "name": {"$ne": name}}):
            code = make_code(name, suffix=f"_{random.randint(100,999)}")

        db.services.update_one(
            {"name": name},  # upsert по имени (как и раньше)
            {"$set": {"name": name, "duration_min": int(dur), "price": price, "code": code}},
            upsert=True,
        )

    print(f"[seed] services → OK ({len(base)} шт. + миграция code для старых)")


# --- helpers для выборок (ТОП-уровень, не внутри функций!) ---
def _fetch_ids(coll, projection):
    return list(db[coll].find({}, projection))


def seed_appointments(count: int = 24):
    """
    Демо-приёмы на текущую неделю, без конфликтов, 15-мин кратность, окно 09:00–21:00.
    Использует rooms/doctors/patients/services из БД.
    """
    # справочники
    rooms = _fetch_ids("rooms", {"_id": 1, "name": 1})
    doctors = _fetch_ids("doctors", {"_id": 1, "full_name": 1})
    patients = _fetch_ids("patients", {"_id": 1, "full_name": 1})
    services = list(db.services.find({}, {"_id": 1, "name": 1, "duration_min": 1}))

    if not rooms or not doctors or not patients or not services:
        print("[seed] appointments → SKIP (нет данных в справочниках)")
        return

    # очищаем только демо (для простоты — всё)
    db.appointments.delete_many({})

    today = date.today()
    monday = today - timedelta(days=today.weekday())
    rng = random.Random(42)

    created = 0
    attempts = 0
    while created < count and attempts < count * 15:
        attempts += 1

        room = rng.choice(rooms)
        doctor = rng.choice(doctors)
        patient = rng.choice(patients)
        service = rng.choice(services)

        # случайный день пн–сб
        day_offset = rng.randint(0, 5)
        base_day = monday + timedelta(days=day_offset)

        # случайное время, кратное 15 мин, в окне 09:00–21:00
        hour = rng.randint(9, 20)  # последний старт — 20:xx
        minute = rng.choice([0, 15, 30, 45])
        start = datetime.combine(base_day, time(hour, minute))
        start = align_to_slot(start)

        dur = int(service.get("duration_min") or SLOT_MIN)
        if dur < SLOT_MIN:
            dur = SLOT_MIN
        dur = ((dur + SLOT_MIN - 1) // SLOT_MIN) * SLOT_MIN  # кратно 15
        end = start + timedelta(minutes=dur)

        if not (in_hours(start) and in_hours(end)):
            continue

        room_id: ObjectId = room["_id"]
        doctor_id: ObjectId = doctor["_id"]
        patient_id: ObjectId = patient["_id"]
        service_id: ObjectId = service["_id"]

        if has_conflict(start, end, room_id, doctor_id):
            continue

        db.appointments.insert_one(
            {
                "start": start,
                "end": end,
                "room_id": room_id,
                "doctor_id": doctor_id,
                "patient_id": patient_id,
                "service_id": service_id,
                "status": "scheduled",
                "note": f"Демо-запись (seed) {created+1}",
                "created_at": datetime.utcnow(),
            }
        )
        created += 1

    print(f"[seed] appointments → OK (создано: {created})")


# =========================
#  Main
# =========================
if __name__ == "__main__":
    import traceback

    print("[seed] __file__:", __file__)
    print("[seed] cwd     :", os.getcwd())
    print("[seed] target DB:", DB_NAME)

    steps = [
        ("rooms", seed_rooms),
        ("doctors", seed_doctors),
        ("patients", seed_patients),
        ("services", seed_services),
        ("appointments", lambda: seed_appointments(count=24)),
    ]

    for name, fn in steps:
        try:
            print(f"[seed] >>> {name}...")
            fn()
        except Exception as e:
            print(f"[seed] !!! ERROR in {name}: {e}")
            traceback.print_exc()
            raise

    print("[seed] done.")
