# import_real_data_fixed.py
import os
import csv
from dotenv import load_dotenv
from pymongo import MongoClient
from werkzeug.security import generate_password_hash
from datetime import datetime

load_dotenv()
client = MongoClient(os.getenv("MONGO_URI"))
db = client[os.getenv("DB_NAME", "medplatforma")]

# Очистим коллекции
db.rooms.delete_many({})
db.users.delete_many({})
db.doctors.delete_many({})
db.services.delete_many({})

print("Загружаем реальные данные из CSV...")

# ROOMS.CSV
with open("rooms.csv", "r", encoding="utf-8-sig") as f:
    reader = csv.DictReader(f, delimiter=";")
    rooms = []
    for row in reader:
        rooms.append(
            {
                "name": row["name"].strip(),
                "status": "available",
                "active": row.get("active", "true").lower() == "true",
                "created_at": datetime.utcnow(),
            }
        )
    if rooms:
        db.rooms.insert_many(rooms)
    print(f"✓ Кабинеты загружены: {len(rooms)}")

# USERS.CSV
with open("users.csv", "r", encoding="utf-8-sig") as f:
    reader = csv.DictReader(f, delimiter=";")
    users = []
    for row in reader:
        login = row["login"].strip()
        users.append(
            {
                "login": login,
                "full_name": row["name"].strip(),
                "role": row.get("role", "admin").strip(),
                "phone": row.get("phone", "").strip(),
                "active": True,
                "password_hash": generate_password_hash(
                    "ClubStom2024!"
                ),  # Временный пароль для всех
            }
        )
    if users:
        db.users.insert_many(users)
    print(f"✓ Пользователи загружены: {len(users)}")

# DOCTORS.CSV
with open("doctors.csv", "r", encoding="utf-8-sig") as f:
    reader = csv.DictReader(f, delimiter=";")
    doctors = []
    for row in reader:
        doctors.append(
            {
                "full_name": row["full_name"].strip(),
                "specialization": row.get("specialty", "").strip(),
                "phone": row.get("phone", "").strip() if row.get("phone") else "",
                "status": "активен",
                "active": (
                    row.get("active", "true").lower() == "true" if row.get("active") else True
                ),
                "created_at": datetime.utcnow(),
            }
        )
    if doctors:
        db.doctors.insert_many(doctors)
    print(f"✓ Врачи загружены: {len(doctors)}")

# SERVICES_PRICE_DUAL.CSV
with open("services_price_dual.csv", "r", encoding="utf-8-sig") as f:
    reader = csv.DictReader(f, delimiter=";")
    services = []
    for row in reader:
        # Генерируем код из названия
        name = row["name"].strip()
        code = "".join(word[0] for word in name.split()[:3]).upper()

        services.append(
            {
                "name": name,
                "code": f"{code}_{len(services)+1}",  # Уникальный код
                "duration_min": int(row.get("duration_min", 30)),
                "price": int(row.get("price_client", 0)),
                "price2": int(row.get("price_staff", 0)) if row.get("price_staff") else None,
                "is_active": row.get("active", "true").lower() == "true",
                "color": "#2196F3",  # Цвет по умолчанию
                "created_at": datetime.utcnow(),
            }
        )
    if services:
        db.services.insert_many(services)
    print(f"✓ Услуги загружены: {len(services)}")

# Добавим статусы визитов
visit_statuses = [
    {"key": "scheduled", "title": "Запланирован", "color": "#2196F3"},
    {"key": "confirmed", "title": "Подтверждён", "color": "#4CAF50"},
    {"key": "arrived", "title": "Пришёл", "color": "#FF9800"},
    {"key": "completed", "title": "Завершён", "color": "#8BC34A"},
    {"key": "cancelled", "title": "Отменён", "color": "#F44336"},
]

db.visit_statuses.delete_many({})
for status in visit_statuses:
    db.visit_statuses.insert_one(status)
print(f"✓ Статусы визитов загружены: {len(visit_statuses)}")

print("\n" + "=" * 50)
print("ИТОГО В БАЗЕ ДАННЫХ:")
print(f"  Пользователи: {db.users.count_documents({})}")
print(f"  Кабинеты: {db.rooms.count_documents({})}")
print(f"  Врачи: {db.doctors.count_documents({})}")
print(f"  Услуги: {db.services.count_documents({})}")
print("=" * 50)

# Выведем логины пользователей
print("\nПОЛЬЗОВАТЕЛИ СИСТЕМЫ:")
for user in db.users.find({}, {"login": 1, "full_name": 1, "role": 1}):
    print(f"  Логин: {user['login']:<15} Роль: {user['role']:<10} ФИО: {user['full_name']}")

print("\nВременный пароль для всех: ClubStom2024!")
print("Рекомендуется сменить пароли после первого входа!")
