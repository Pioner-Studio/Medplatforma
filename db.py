# db.py
from pymongo import MongoClient

MONGO_URI = "mongodb+srv://medadmin:medpass123@medplatforma.cnv7fbo.mongodb.net/medplatforma?retryWrites=true&w=majority&appName=medplatforma"
client = MongoClient(MONGO_URI)
db = client["medplatforma"]

patients_collection = db["patients"]
doctors_collection = db["doctors"]
events_collection = db["events"]
