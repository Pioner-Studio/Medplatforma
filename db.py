from pymongo import MongoClient

MONGO_URI = "mongodb+srv://medadmin:medpass123@medplatforma.cnv7fbo.mongodb.net/"
client = MongoClient(MONGO_URI)
db = client["medplatforma"]

doctors_collection = db["doctors"]
events_collection = db["events"]
