from pymongo import MongoClient
import os
from dotenv import load_dotenv
load_dotenv()
client = MongoClient(os.getenv("MONGO_URI","mongodb://127.0.0.1:27017"))
db = client[os.getenv("DB_NAME","medplatforma")]

print("patients:", db.patients.count_documents({}))
print("doctors:", db.doctors.count_documents({}))
print("rooms:", db.rooms.count_documents({}))
print("services:", db.services.count_documents({}))
print("appointments total:", db.appointments.count_documents({}))

from datetime import datetime, timedelta
today = datetime.now()
week_start = today - timedelta(days=today.weekday())
week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
week_end = week_start + timedelta(days=7)
print("appointments this week:",
      db.appointments.count_documents({"start": {"$gte": week_start, "$lt": week_end}}))
