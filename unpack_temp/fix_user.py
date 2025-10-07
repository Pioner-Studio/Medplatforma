# fix_user.py
from __future__ import annotations
import os
from dotenv import load_dotenv
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash

# ---------- настройки ----------
LOGIN = "demo"
PASSWORD = "ClubStom2024!"
ROLE = "admin"           # можешь поменять на "registrar"
FULL_NAME = "Demo Admin" # опционально
# -------------------------------

def main():
    load_dotenv()  # подтянет MONGO_URI и DB_NAME из .env

    mongo_uri = os.getenv("MONGO_URI")
    db_name = os.getenv("DB_NAME", "medplatforma")

    if not mongo_uri:
        raise RuntimeError("MONGO_URI отсутствует. Укажи его в .env")

    client = MongoClient(mongo_uri)
    try:
        client.admin.command("ping")
    except Exception as e:
        raise RuntimeError(f"Нет соединения с MongoDB: {e}")

    db = client[db_name]
    users = db.get_collection("users")

    # пароль в совместимом формате
    pwd_hash = generate_password_hash(PASSWORD)

    # апсерт пользователя по логину
    result = users.update_one(
        {"login": LOGIN},
        {
            "$set": {
                "login": LOGIN,
                "full_name": FULL_NAME,
                "role": ROLE,
                "active": True,
                "password_hash": pwd_hash,
            },
            "$unset": {  # на всякий случай уберём старое поле password, если было
                "password": ""
            },
        },
        upsert=True,
    )

    doc = users.find_one({"login": LOGIN}, {"_id": 0})
    ok = check_password_hash(doc.get("password_hash", ""), PASSWORD)

    print("Upsert:", result.raw_result)
    print("User:", doc)
    print("Password check:", ok)

    if not ok:
        raise RuntimeError("Хэш пароля записался неверно — проверь зависимости")

    print("\nГотово. Логин: demo  Пароль: ClubStom2024!\n")

if __name__ == "__main__":
    main()
