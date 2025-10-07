# make_doctor_logins.py
import os, re, unicodedata
from dotenv import load_dotenv
from pymongo import MongoClient
from werkzeug.security import generate_password_hash

TEMP_PASSWORD = "ChangeMe123!"   # выдай врачам и поменяйте после входа

load_dotenv()
client = MongoClient(os.getenv("MONGO_URI"))
db = client[os.getenv("DB_NAME", "medplatforma")]

def slug(s: str) -> str:
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii")
    s = re.sub(r"[^a-zA-Z0-9]+", ".", s).strip(".").lower()
    s = re.sub(r"\.+", ".", s)
    return s or "user"

for d in db.doctors.find({"active": True}):
    doctor_id = d.get("_id")
    email = (d.get("email") or "").strip().lower()
    base = email.split("@")[0] if email else slug(d.get("full_name") or d.get("name") or "doctor")
    login = base

    # уникализируем логин
    i = 1
    while db.users.find_one({"login": login}):
        i += 1
        login = f"{base}{i}"

    user = {
        "login": login,
        "full_name": d.get("full_name") or d.get("name"),
        "role": "doctor",
        "doctor_id": doctor_id,
        "active": True,
        "password_hash": generate_password_hash(TEMP_PASSWORD),
    }
    db.users.insert_one(user)
    print(f"Created: {login}")

print("Done. Temporary password for all:", TEMP_PASSWORD)
