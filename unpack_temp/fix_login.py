# fix_login.py
import os
from dotenv import load_dotenv
from pymongo import MongoClient
from werkzeug.security import generate_password_hash

load_dotenv()
client = MongoClient(os.getenv("MONGO_URI"))
db = client[os.getenv("DB_NAME", "medplatforma")]

# Создаём пользователя demo
user = {
    "login": "demo",
    "full_name": "Администратор",
    "role": "admin",
    "active": True,
    "password_hash": generate_password_hash("ClubStom2024!"),
}

db.users.update_one({"login": "demo"}, {"$set": user}, upsert=True)

# Создаём базовые кабинеты
rooms = [
    {"name": "Детский", "status": "available"},
    {"name": "Ортопедия", "status": "available"},
    {"name": "Хирургия", "status": "available"},
    {"name": "Ортодонтия", "status": "available"},
    {"name": "Терапия", "status": "available"},
    {"name": "Кастомный", "status": "available"},
]

for room in rooms:
    db.rooms.update_one({"name": room["name"]}, {"$set": room}, upsert=True)

# Создаём тестового врача
doctor = {
    "full_name": "Иванов Иван Иванович",
    "specialization": "Терапевт",
    "phone": "+79991234567",
    "status": "активен",
}

db.doctors.update_one({"full_name": doctor["full_name"]}, {"$set": doctor}, upsert=True)

# Создаём тестовые услуги
services = [
    {"name": "Консультация", "code": "CONS", "price": 1500, "duration_min": 30, "is_active": True},
    {
        "name": "Лечение кариеса",
        "code": "CAR",
        "price": 5000,
        "duration_min": 60,
        "is_active": True,
    },
    {"name": "Удаление зуба", "code": "EXT", "price": 3000, "duration_min": 45, "is_active": True},
]

for service in services:
    db.services.update_one({"code": service["code"]}, {"$set": service}, upsert=True)

print("✅ Данные созданы:")
print(f"  Пользователи: {db.users.count_documents({})}")
print(f"  Кабинеты: {db.rooms.count_documents({})}")
print(f"  Врачи: {db.doctors.count_documents({})}")
print(f"  Услуги: {db.services.count_documents({})}")
print("\nДанные для входа:")
print("  Логин: demo")
print("  Пароль: ClubStom2024!")
