from datetime import datetime
from bson import ObjectId
from pymongo import MongoClient

client = MongoClient("mongodb+srv://medadmin:medpass123@medplatforma.cnv7fbo.mongodb.net/")
db = client['medplatforma']

patients = [
    {
        "_id": ObjectId("66bbf001fe3f2a1c11111111"),
        "full_name": "Иванов Павел",
        "avatar_url": "/static/avatars/patient_1.png",
        "invited_by": None,
        "referrals": [
            ObjectId("66bbf001fe3f2a1c22222222"),
            ObjectId("66bbf001fe3f2a1c33333333")
        ],
        "created_at": datetime.now()
    },
    {
        "_id": ObjectId("66bbf001fe3f2a1c22222222"),
        "full_name": "Сидорова Ольга",
        "avatar_url": "/static/avatars/patient_2.png",
        "invited_by": ObjectId("66bbf001fe3f2a1c11111111"),
        "referrals": [],
        "created_at": datetime.now()
    },
    {
        "_id": ObjectId("66bbf001fe3f2a1c33333333"),
        "full_name": "Петров Сергей",
        "avatar_url": "/static/avatars/patient_3.png",
        "invited_by": ObjectId("66bbf001fe3f2a1c11111111"),
        "referrals": [ObjectId("66bbf001fe3f2a1c44444444")],
        "created_at": datetime.now()
    },
    {
        "_id": ObjectId("66bbf001fe3f2a1c44444444"),
        "full_name": "Михайлова Анна",
        "avatar_url": "/static/avatars/patient_4.png",
        "invited_by": ObjectId("66bbf001fe3f2a1c33333333"),
        "referrals": [],
        "created_at": datetime.now()
    }
]

db.patients.delete_many({})
db.patients.insert_many(patients)

print("✅ Демо-партнёрские связи успешно добавлены")
