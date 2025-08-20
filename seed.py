import random
from datetime import datetime, timedelta

from pymongo import MongoClient

client = MongoClient("mongodb+srv://medadmin:medpass123@medplatforma.cnv7fbo.mongodb.net/")
db = client["medplatforma"]

# ЧИСТИМ коллекции:
db.doctors.delete_many({})
db.patients.delete_many({})
db.events.delete_many({})

# 1. Демо-врачи
doctor_names = [
    "Смирнов Павел",
    "Иванова Анна",
    "Кузнецов Дмитрий",
    "Попова Мария",
    "Волков Артём",
    "Соколова Екатерина",
    "Лебедев Сергей",
    "Козлова Юлия",
    "Новиков Андрей",
    "Федорова Елена",
]
specializations = [
    "Терапевт",
    "Хирург",
    "Ортопед",
    "Детский стоматолог",
    "Пародонтолог",
    "Рентгенолог",
    "Ортодонт",
    "Гигиенист",
    "Имплантолог",
    "Стоматолог общей практики",
]
doctor_ids = []
for i, name in enumerate(doctor_names):
    doc = {
        "full_name": name,
        "specialization": specializations[i],
        "email": f"doctor{i+1}@mail.ru",
        "phone": f"+79990000{str(100+i)}",
        "avatar_url": f"/static/avatars/doctor_{i%6+1}.png",
        "status": "активен",
    }
    res = db.doctors.insert_one(doc)
    doctor_ids.append(str(res.inserted_id))

# 2. Демо-пациенты
patient_names = [
    "Петров Иван",
    "Сидорова Ольга",
    "Михайлов Сергей",
    "Егорова Татьяна",
    "Орлов Дмитрий",
    "Семенова Мария",
    "Васильев Антон",
    "Громова Наталья",
    "Зайцев Алексей",
    "Тихонова Ирина",
]
patient_ids = []
for i, name in enumerate(patient_names):
    pat = {
        "full_name": name,
        "dob": f"198{random.randint(0,9)}-0{random.randint(1,9)}-{random.randint(10,28)}",
        "phone": f"+79990000{str(200+i)}",
        "email": f"patient{i+1}@mail.ru",
        "avatar_url": f"/static/avatars/patient_{i%6+1}.png",
    }
    res = db.patients.insert_one(pat)
    patient_ids.append(str(res.inserted_id))

# 3. Демо-записи (20 штук в разные даты месяца)
cabinets = [
    "Терапевтический",
    "Хирургический",
    "Ортопедический",
    "Детский",
    "Пародонтологический",
    "Рентген",
]
services = ["Пломба", "Имплантация", "Лечение", "Гигиена"]
statuses = ["Первичный", "Повторный", "Оплачен", "Отказ"]

for i in range(20):
    # Генерируем даты строго внутри текущего месяца
    now = datetime.now()
    year, month = now.year, now.month
    day = 1 + (i % 28)  # дни с 1 по 28
    hour = 9 + (i % 8)  # время 9:00 - 16:00
    try:
        start_dt = datetime(year, month, day, hour, 0)
    except ValueError:
        start_dt = now  # fallback, если вдруг выйдет за границы месяца

    ev = {
        "doctor_id": random.choice(doctor_ids),
        "patient_id": random.choice(patient_ids),
        "cabinet": random.choice(cabinets),
        "start": start_dt.strftime("%Y-%m-%dT%H:%M"),
        "service": random.choice(services),
        "sum": random.choice([2000, 3500, 4000, 4500, 5000, 6000]),
        "status": random.choice(statuses),
        "status_color": "",
        "comment": f"Автосгенерированная запись №{i+1}",
        "phone": f"+79990000{str(200 + random.randint(0,9))}",
        "whatsapp": f"79990000{str(200 + random.randint(0,9))}",
        "telegram": f"patient{i%10+1}",
    }
    db.events.insert_one(ev)

print("Демо-данные успешно добавлены!")
