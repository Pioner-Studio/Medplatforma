from pymongo import MongoClient

client = MongoClient("mongodb+srv://medadmin:medpass123@medplatforma.cnv7fbo.mongodb.net/")
db = client["medplatforma"]

doctors_collection = db["doctors"]
patients_collection = db["patients"]
events_collection = db["events"]

# Очистка (для дев-режима)
doctors_collection.delete_many({})
patients_collection.delete_many({})
events_collection.delete_many({})

# Врачи
doctors = [
    {"title": "Иванов"},
    {"title": "Смирнов"},
    {"title": "Петров"},
]
doctor_ids = doctors_collection.insert_many(doctors).inserted_ids

# Пациенты
patients = [
    {"full_name": "Алексей Горелов"},
    {"full_name": "Мария Павлова"},
]
patient_ids = patients_collection.insert_many(patients).inserted_ids

# События
events = [
    {
        "title": "Приём: Горелов",
        "date": "2025-06-25T10:00:00",
        "resourceId": str(doctor_ids[0]),
        "doctor": "Иванов",
        "patient": "Алексей Горелов",
        "service": "Чистка зубов"
    },
    {
        "title": "Приём: Павлова",
        "date": "2025-06-25T12:00:00",
        "resourceId": str(doctor_ids[1]),
        "doctor": "Смирнов",
        "patient": "Мария Павлова",
        "service": "Консультация"
    }
]
events_collection.insert_many(events)

print("Данные успешно загружены.")
