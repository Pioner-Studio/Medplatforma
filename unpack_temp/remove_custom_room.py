# remove_custom_room.py
import os
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()
client = MongoClient(os.getenv("MONGO_URI"))
db = client[os.getenv("DB_NAME", "medplatforma")]

# Удаляем кастомный кабинет
result = db.rooms.delete_one({"name": "Кастомный"})
print(f"Удален кастомный кабинет: {result.deleted_count}")

# Обновляем активность для всех кабинетов
db.rooms.update_many({}, {"$set": {"active": True}})
print("Все кабинеты отмечены как активные")
