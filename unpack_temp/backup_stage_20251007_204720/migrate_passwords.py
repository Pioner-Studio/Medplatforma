# migrate_passwords.py
from pymongo import MongoClient
from werkzeug.security import generate_password_hash
import os, re

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "medplatforma")

client = MongoClient(MONGO_URI)
db = client[DB_NAME]
users = db.get_collection("users")

bcrypt_like = re.compile(r"^\$2[aby]?\$")

for u in users.find({}, {"login": 1, "password": 1, "password_hash": 1}):
    if u.get("password_hash"):
        continue
    pwd = u.get("password")
    if isinstance(pwd, str) and bcrypt_like.match(pwd):
        # пароля в чистом виде нет — только хэш; задаём временный общий пароль
        # ВНИМАНИЕ: замени на желаемый временный пароль и затем попроси пользователей его сменить
        temp_password = "ClubStom2024!"
        users.update_one(
            {"_id": u["_id"]},
            {"$set": {"password_hash": generate_password_hash(temp_password)},
             "$unset": {"password": ""}}
        )
        print("migrated:", u.get("login"))
