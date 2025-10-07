from pymongo import MongoClient
from datetime import datetime, timedelta
import random

client = MongoClient("mongodb+srv://medadmin:medpass123@medplatforma.cnv7fbo.mongodb.net/")
db = client['medplatforma']

# --- 1. Очищаем старые тестовые данные (по желанию, можно убрать если боишься потерять ручные) ---
db.patients.delete_many({'phone': {'$regex': '^+7999'}})
db.doctors.delete_many({'phone': {'$regex': '^+7888'}})
db.events.delete_many({'comment': {'$regex': '^DEMO'}})

# --- 2. Добавляем 10 демо-пациентов ---
patients = []
for i in range(10):
    pat = {
        "full_name": f"Демо Пациент {i+1}",
        "phone": f"+7999{i:07d}",
        "email": f"demo_patient_{i+1}@mail.ru",
        "avatar_url": "/static/avatars/demo-patient.png",
        "dob": "1990-01-01",
        "notes": f"DEMO patient {i+1}",
        "debt": 0,
        "deposit": 0,
        "partner_points": 0,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }
    patients.append(pat)

patient_ids = [db.patients.insert_one(p).inserted_id for p in patients]

# --- 3. Добавляем 10 демо-врачей ---
specializations = ["Терапевт", "Хирург", "Ортопед", "Детский стоматолог", "Пародонтолог", "Рентгенолог"]
doctors = []
for i in range(10):
    doc = {
        "full_name": f"Демо Врач {i+1}",
        "specialization": random.choice(specializations),
        "phone": f"+7888{i:07d}",
        "email": f"demo_doctor_{i+1}@mail.ru",
        "avatar_url": "/static/avatars/demo-doctor.png",
        "status": "активен"
    }
    doctors.append(doc)

doctor_ids = [db.doctors.insert_one(d).inserted_id for d in doctors]

# --- 4. Добавляем 20 демо-записей (events) на разные дни месяца ---
cabinets = [
    "Терапевтический",
    "Хирургический",
    "Ортопедический",
    "Детский",
    "Пародонтологический",
    "Рентген"
]
services = ["Пломба", "Имплантация", "Лечение", "Гигиена", "Консультация", "Удаление"]

status_list = ["Первичный", "Оплачен", "Отказ", "Повторный"]

base_date = datetime.now().replace(day=1, hour=9, minute=0, second=0, microsecond=0)
for i in range(20):
    day = random.randint(0, 29)  # любые дни месяца
    hour = random.choice([9, 10, 11, 12, 13, 14, 15, 16, 17])
    start = (base_date + timedelta(days=day, hours=hour - 9)).strftime("%Y-%m-%dT%H:%M")
    ev = {
        "doctor_id": str(random.choice(doctor_ids)),
        "patient_id": str(random.choice(patient_ids)),
        "cabinet": random.choice(cabinets),
        "start": start,
        "service": random.choice(services),
        "sum": str(random.randint(2000, 12000)),
        "status": random.choice(status_list),
        "comment": f"DEMO запись {i+1}",
        "phone": "+79991112233",
        "whatsapp": "79991112233",
        "telegram": "demopatient"
    }
    db.events.insert_one(ev)

print("Готово! 10 демо-пациентов, 10 демо-врачей и 20 демо-записей добавлены.")
