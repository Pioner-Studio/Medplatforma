from main import db
from datetime import datetime

# Все записи на 03.10.2025
appts = list(db.appointments.find({
    'start': {
        '$gte': datetime(2025, 10, 3, 0, 0, 0),
        '$lt': datetime(2025, 10, 4, 0, 0, 0)
    }
}))

print(f'Записей на 03.10.2025: {len(appts)}')
for a in appts:
    print(f"- Patient ID: {a.get('patient_id')}")
    print(f"  Start: {a.get('start')}")
    print(f"  Service: {a.get('service_id')}")
    print()
