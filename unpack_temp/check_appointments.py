from main import db
from datetime import datetime, timedelta

today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
today_end = today_start + timedelta(days=1)

print("Today range:", today_start, "-", today_end)

appts = list(db.appointments.find({"start": {"$gte": today_start, "$lt": today_end}}))
print("Appointments today:", len(appts))

for a in appts:
    print(f"- Patient: {a.get('patient_id')}, Start: {a.get('start')}")
