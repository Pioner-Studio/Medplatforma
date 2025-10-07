from datetime import datetime, timedelta
from bson import ObjectId
import random

def rand_date(offset=10):
    return (datetime.now() - timedelta(days=random.randint(0, offset))).strftime('%Y-%m-%d')

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

types = ["Коронка", "Винир", "Брекеты", "Протез", "Каппа"]
statuses = ["В работе", "Готово", "Выдано", "Ожидает оплаты"]

ztls = []
for i in range(12):
    pat = random.choice(patients)
    doc = random.choice(doctors)
    t = random.choice(types)
    status = random.choice(statuses)
    order_date = rand_date(12)
    due_date = (datetime.strptime(order_date, "%Y-%m-%d") + timedelta(days=random.randint(3, 15))).strftime('%Y-%m-%d')
    ztls.append({
        "_id": ObjectId(),
        "patient_id": pat["_id"],
        "doctor_id": doc["_id"],
        "type": t,
        "order_date": order_date,
        "due_date": due_date,
        "status": status,
        "comment": f"Комментарий к заказу {i+1}",
        "file_url": f"/static/ztl/demo_ztl_{(i % 5) + 1}.png",
        "created_at": order_date
    })

if __name__ == "__main__":
    from pymongo import MongoClient
    client = MongoClient("mongodb+srv://medadmin:medpass123@medplatforma.cnv7fbo.mongodb.net/")
    db = client['medplatforma']
    db.ztl.delete_many({})
    db.ztl.insert_many(ztls)
    print("✅ ZTL DEMO готово! Записей добавлено:", len(ztls))
