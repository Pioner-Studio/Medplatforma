from main import db
from bson import ObjectId
from datetime import datetime, timedelta

oid = ObjectId('68dd28b620210e8e4cad772b')
p = db.patients.find_one({'_id': oid})

print('Patient found:', p is not None)
if p:
    print('Name:', p.get('full_name'))

today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
today_end = today_start + timedelta(days=1)

appt = db.appointments.find_one({
    'patient_id': oid,
    'start': {'$gte': today_start, '$lt': today_end}
})

print('Appointment found:', appt is not None)
if appt:
    print('Appointment start:', appt.get('start'))
    print('Service ID:', appt.get('service_id'))
