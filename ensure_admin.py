# ensure_admin.py — создаёт/обновляет admin demo/ClubStom2024!
import os
from dotenv import load_dotenv
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash

load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME", "medplatforma")
if not MONGO_URI:
    raise RuntimeError("MONGO_URI is not set in .env")

client = MongoClient(MONGO_URI)
db = client[DB_NAME]

login = "demo"
password = "ClubStom2024!"
doc = {
    "login": login,
    "full_name": "Администратор",
    "role": "admin",
    "active": True,
    "password_hash": generate_password_hash(password),
}

res = db.users.update_one({"login": login}, {"$set": doc}, upsert=True)
u = db.users.find_one(
    {"login": login}, {"_id": 0, "login": 1, "role": 1, "active": 1, "password_hash": 1}
)
print("Upserted:", bool(res.upserted_id))
print("User:", {k: (v if k != "password_hash" else "***hash***") for k, v in u.items()})
print("Password OK:", check_password_hash(u["password_hash"], password))
print(f"Готово. Логин: {login}  Пароль: {password}")
