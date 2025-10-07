# debug_api_dicts.py
# Проверим, что именно возвращает API /api/dicts

import os
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()
client = MongoClient(os.getenv("MONGO_URI"))
db = client[os.getenv("DB_NAME", "medplatforma")]

print("=== ПРЯМАЯ ПРОВЕРКА БД ===")

# Врачи
doctors_count = db.doctors.count_documents({"status": "активен"})
print(f"Врачи со статусом 'активен': {doctors_count}")

# Все врачи
all_doctors = db.doctors.count_documents({})
print(f"Всего врачей в БД: {all_doctors}")

# Проверим статусы врачей
for doc in db.doctors.find({}, {"full_name": 1, "status": 1}).limit(5):
    print(f"  {doc.get('full_name')} - статус: '{doc.get('status')}'")

# Услуги
services_active = db.services.count_documents({"is_active": True})
print(f"Активных услуг: {services_active}")

all_services = db.services.count_documents({})
print(f"Всего услуг: {all_services}")

# Проверим активность услуг
for srv in db.services.find({}, {"name": 1, "is_active": 1}).limit(5):
    print(f"  {srv.get('name')} - активна: {srv.get('is_active')}")

# Кабинеты
rooms_active = db.rooms.count_documents({"active": True})
print(f"Активных кабинетов: {rooms_active}")

all_rooms = db.rooms.count_documents({})
print(f"Всего кабинетов: {all_rooms}")

# Проверим активность кабинетов
for room in db.rooms.find({}, {"name": 1, "active": 1}):
    print(f"  {room.get('name')} - активен: {room.get('active')}")
