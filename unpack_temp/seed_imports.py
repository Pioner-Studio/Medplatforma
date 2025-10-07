from datetime import datetime, timedelta
from pymongo import MongoClient

client = MongoClient("mongodb+srv://medadmin:medpass123@medplatforma.cnv7fbo.mongodb.net/")
db = client['medplatforma']

imports = [
    {
        "time": (datetime.now() - timedelta(hours=1)).strftime('%Y-%m-%d %H:%M'),
        "user": "Иванова Татьяна",
        "filename": "patients_2025-07-05.xlsx",
        "status": "ok",
        "count": 12
    },
    {
        "time": (datetime.now() - timedelta(hours=2)).strftime('%Y-%m-%d %H:%M'),
        "user": "Петров Иван",
        "filename": "events_2025-07-04.csv",
        "status": "error",
        "error": "Ошибка в строке 8"
    }
]

db.imports.delete_many({})
db.imports.insert_many(imports)
print("История импортов успешно добавлена")
