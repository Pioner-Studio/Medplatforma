# -*- coding: utf-8 -*-
from pymongo import MongoClient
import os

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("MONGO_DB", "medplatforma")

DATA = [
    {"code": "kids", "name": "Детский"},
    {"code": "prosthetics", "name": "Ортопедия"},
    {"code": "surgery", "name": "Хирургия"},
    {"code": "orthodontics", "name": "Ортодонтия"},
    {"code": "therapy", "name": "Терапия"},
    {"code": "extra", "name": "Кабинет 6"},
]


def main():
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    db.rooms.delete_many({})  # чистим на старте, чтобы не плодить дубликаты
    db.rooms.insert_many(DATA)
    print(f"Inserted rooms: {len(DATA)}")


if __name__ == "__main__":
    main()
