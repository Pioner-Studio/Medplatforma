from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime, timedelta

def to_dt(s):
    if isinstance(s, datetime): return s
    if not s: return None
    try:
        if 'T' in s and len(s) >= 16:
            try:
                return datetime.strptime(s[:16], "%Y-%m-%dT%H:%M")
            except ValueError:
                pass
        return datetime.fromisoformat(s.replace('Z','+00:00'))
    except Exception:
        return None

def add_minutes(dt, m): return dt + timedelta(minutes=int(m or 0))

client = MongoClient("mongodb+srv://medadmin:medpass123@medplatforma.cnv7fbo.mongodb.net/")
db = client['medplatforma']

def migrate():
    src = list(db.events.find())
    print(f"Найдено в events: {len(src)}")
    inserted = 0
    for e in src:
        start_dt = to_dt(e.get("start") or e.get("datetime"))
        if not start_dt:
            continue
        # кабинет по имени -> room_id
        room = db.rooms.find_one({"name": e.get("cabinet")}) if e.get("cabinet") else None
        # длительность по умолчанию 30 мин
        end_dt = add_minutes(start_dt, 30)

        doc = {
            "doctor_id":  ObjectId(e["doctor_id"]) if e.get("doctor_id") else None,
            "patient_id": ObjectId(e["patient_id"]) if e.get("patient_id") else None,
            "room_id":    room["_id"] if room else None,
            "service_id": None,
            "start":      start_dt,
            "end":        end_dt,
            "status_key": "scheduled",
            "comment":    e.get("comment",""),
            "sum":        int((e.get("sum") or 0)) if str(e.get("sum","")).isdigit() else 0
        }
        db.appointments.insert_one(doc)
        inserted += 1
    print(f"Перенесено в appointments: {inserted}")

if __name__ == "__main__":
    migrate()
