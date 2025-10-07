# check_demo_user.py
import os
from dotenv import load_dotenv
from pymongo import MongoClient
from werkzeug.security import check_password_hash

load_dotenv()
client = MongoClient(os.getenv("MONGO_URI"))
db = client[os.getenv("DB_NAME", "medplatforma")]

u = db.users.find_one({"login": "demo"})
print("User:", u)
print("active:", u.get("active"))
print("has password_hash:", bool(u.get("password_hash")))
print("password ok:", check_password_hash(u.get("password_hash", ""), "ClubStom2024!"))
