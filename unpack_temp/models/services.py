# models/services.py
# Модель коллекции "services" (прайс-лист)

from pymongo import MongoClient
import os

MONGO_URI = os.getenv("MONGO_URI", "mongodb+srv://medadmin:Med12345!@medplatforma.cnv7fbo.mongodb.net/")
DB_NAME = os.getenv("DB_NAME", "medplatforma")

client = MongoClient(MONGO_URI)
db = client[DB_NAME]
services = db["services"]  # коллекция с прайсом
