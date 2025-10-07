# create_admin.py
from werkzeug.security import generate_password_hash
from pymongo import MongoClient
import os

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "medplatforma")

client = MongoClient(MONGO_URI)
db = client[DB_NAME]

login = "Gogueva"  # <- логин, которым входишь
password = "ClubStom2024!"  # <- новый пароль

db.users.update_one(
    {"login": login},
    {
        "$set": {
            "login": login,
            "full_name": "Гогуева Алина Темурлановна",
            "role": "admin",
            "active": True,
            "password_hash": generate_password_hash(password),
        }
    },
    upsert=True,
)

print("OK")
