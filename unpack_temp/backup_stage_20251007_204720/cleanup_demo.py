# cleanup_demo.py
import os
import re
from pymongo import MongoClient, ASCENDING
from dotenv import load_dotenv

load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME", "medplatforma")

if not MONGO_URI:
    raise RuntimeError("MONGO_URI is not set")

client = MongoClient(MONGO_URI)
db = client[DB_NAME]

# --- 1) Удаляем ДЕМО-пользователей безопасно ---
# никаких "$role" и пр. — только валидные поля
demo_logins = {"demo", "demo2"}  # если что-то ещё — добавьте сюда
# логины, которые генерились в make_doctor_logins.py
bulk_demo_prefixes = [r"^doctor\d+$", r"^user\d+$"]

cond = {
    "$or": [{"login": {"$in": list(demo_logins)}}]
    + [{"login": {"$regex": p}} for p in bulk_demo_prefixes]
}
res_users = db.users.delete_many(cond)
print(f"Removed demo users: {res_users.deleted_count}")

# --- 2) Демокабинеты (оставляем только «боевые», если они уже есть) ---
default_rooms = [
    "Детский",
    "Ортопедия",
    "Хирургия",
    "Ортодонтия",
    "Терапия",
    "Кастомный",
]
res_rooms = db.rooms.delete_many({"name": {"$in": default_rooms}})
print(f"Removed default rooms: {res_rooms.deleted_count}")

# Индекс по комнатам — создаём, если ещё нет. Игнорируем конфликт имён.
try:
    db.rooms.create_index([("name", ASCENDING)], name="name_1", unique=True)
except Exception as e:
    # Если индекс уже есть с другим именем — пропускаем.
    if "IndexOptionsConflict" not in str(e):
        raise

# --- 3) Демо-услуги ---
# Если у вас уже есть флаг demo=True — используйте его.
deleted_services = db.services.delete_many({"demo": True})
print(f"Removed demo services (demo=True): {deleted_services.deleted_count}")

# Если флагов нет, но остались старые «пустые»/тестовые услуги — можно
# подчистить по признаку коротких имён/специальных маркеров и т.п.
# (закомментировано, чтобы не снести реальные данные случайно)
# db.services.delete_many({"name": {"$in": ["Тестовая услуга", "Demo"]}})

# --- 4) Демо-врачи ---
# Самый безопасный вариант: деактивировать «явно демо» (по паттерну телефона)
# чтобы никого случайно не удалить.
demo_phone_prefix = r"^\+?7?999000"  # ваши демо начинались с +7999000...
res_set_inactive = db.doctors.update_many(
    {"phone": {"$regex": demo_phone_prefix}}, {"$set": {"active": False}}
)
print(f"Doctors set active=False (by phone pattern): {res_set_inactive.modified_count}")

print("Done.")
