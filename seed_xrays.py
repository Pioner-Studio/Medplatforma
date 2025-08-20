from datetime import datetime, timedelta
from bson import ObjectId
import random

def rand_date(days=10):
    return (datetime.now() - timedelta(days=random.randint(0, days))).strftime('%Y-%m-%d %H:%M')

def pick(lst):
    return random.choice(lst)

patients = [
    {"_id": ObjectId("666666666666666666666601"), "full_name": "Иванов Владимир"},
    {"_id": ObjectId("666666666666666666666602"), "full_name": "Петрова Мария"},
    {"_id": ObjectId("666666666666666666666603"), "full_name": "Сидорова Ольга"},
    {"_id": ObjectId("666666666666666666666604"), "full_name": "Лебедев Сергей"},
    {"_id": ObjectId("666666666666666666666605"), "full_name": "Козлова Анна"},
]
doctors = [
    {"_id": ObjectId("777777777777777777777701"), "full_name": "Д-р Сидоров Алексей"},
    {"_id": ObjectId("777777777777777777777702"), "full_name": "Д-р Михайлова Елена"},
    {"_id": ObjectId("777777777777777777777703"), "full_name": "Д-р Иванов Дмитрий"},
]
types = ["Панорама", "Прицельный", "КТ"]

comments = [
    "Патологий не выявлено.",
    "Визуализируется кариес премоляра.",
    "Рекомендовано КТ для детализации.",
    "Восстановление после имплантации.",
    "Контрольная снимок после лечения."
]

reports = [
    "Все ткани без изменений. Костная структура в норме.",
    "Обнаружен кариес. Рекомендовано лечение.",
    "В области 1.6 незначительное затемнение.",
    "Восстановление пройдено успешно.",
    "Проведена имплантация зуба 2.4, состояние хорошее."
]

images = [
    "/static/xrays/demo_xray_1.png",
    "/static/xrays/demo_xray_2.png",
    "/static/xrays/demo_xray_3.png",
    "/static/xrays/demo_xray_4.png",
    "/static/xrays/demo_xray_5.png",
]

xrays = []

for i in range(12):
    pat = pick(patients)
    doc = pick(doctors)
    xrays.append({
        "_id": ObjectId(),
        "patient_id": pat["_id"],
        "doctor_id": doc["_id"],
        "date": rand_date(),
        "type": pick(types),
        "image_url": pick(images),
        "comment": pick(comments),
        "report": pick(reports),
        "uploaded_by": pick([doc["full_name"], "admin"]),
        "created_at": rand_date()
    })

if __name__ == "__main__":
    from pymongo import MongoClient
    client = MongoClient("mongodb+srv://medadmin:medpass123@medplatforma.cnv7fbo.mongodb.net/")
    db = client['medplatforma']
    db.xrays.delete_many({})
    db.xrays.insert_many(xrays)
    print("✅ Сид-файл рентген-кабинета успешно выполнен! Добавлено:", len(xrays))
