from flask import Flask, render_template, request, redirect, url_for, jsonify
from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime

app = Flask(__name__)

# Подключение к MongoDB
client = MongoClient("mongodb+srv://medadmin:medpass123@medplatforma.cnv7fbo.mongodb.net/")
db = client['medplatforma']

# --- КАЛЕНДАРЬ: Главный экран
@app.route('/calendar')
def calendar():
    doctors = list(db.doctors.find())
    for d in doctors: d['_id'] = str(d['_id'])
    patients = list(db.patients.find())
    for p in patients: p['_id'] = str(p['_id'])
    events = list(db.events.find())
    for e in events:
        e['_id'] = str(e.get('_id', ''))
        e['doctor_id'] = str(e.get('doctor_id', ''))
        e['patient_id'] = str(e.get('patient_id', ''))
        e['title'] = f"{next((doc['full_name'] for doc in doctors if doc['_id'] == e['doctor_id']), '')} — {next((pat['full_name'] for pat in patients if pat['_id'] == e['patient_id']), '')}: {e.get('service', '')}"
        e['start'] = e.get('datetime', '')
    return render_template('calendar.html', doctors=doctors, patients=patients, events=events)

# --- API: Детали события для модалки
@app.route('/api/event/<event_id>')
def api_event(event_id):
    ev = db.events.find_one({'_id': ObjectId(event_id)})
    if not ev:
        return jsonify({'error': 'not found'}), 404
    doctor = db.doctors.find_one({'_id': ObjectId(ev.get('doctor_id'))}) if ev.get('doctor_id') else None
    patient = db.patients.find_one({'_id': ObjectId(ev.get('patient_id'))}) if ev.get('patient_id') else None
    data = {
        "_id": str(ev['_id']),
        "patient_id": str(ev.get('patient_id', '')),
        "patient_name": patient['full_name'] if patient else '—',
        "doctor_id": str(ev.get('doctor_id', '')),
        "doctor_name": doctor['full_name'] if doctor else '—',
        "datetime": ev.get('datetime', ''),
        "service": ev.get('service', ''),
        "sum": ev.get('sum', 0),
        "comment": ev.get('comment', '')
    }
    return jsonify(data)

# --- ДОБАВИТЬ приём (через модалку)
@app.route('/add_event', methods=['POST'])
def add_event():
    data = request.form
    event = {
        "doctor_id": ObjectId(data['doctor_id']),
        "patient_id": ObjectId(data['patient_id']),
        "service": data.get('service', ''),
        "datetime": data.get('datetime', ''),
        "sum": float(data.get('sum', 0)),
        "comment": data.get('comment', '')
    }
    db.events.insert_one(event)
    return redirect(url_for('calendar'))

# --- СПИСОК ПАЦИЕНТОВ
@app.route('/patients')
def patients():
    patients = list(db.patients.find())
    for p in patients:
        p['_id'] = str(p['_id'])
        p['dob'] = p.get('dob', '')
        p['phone'] = p.get('phone', '')
        p['email'] = p.get('email', '')
        p['debt'] = p.get('debt', 0)
        p['avatar_url'] = p.get('avatar_url', '/static/avatars/demo-patient.png')
    return render_template('patients.html', patients=patients)

# --- ДОБАВИТЬ ПАЦИЕНТА
@app.route('/add_patient', methods=['GET', 'POST'])
def add_patient():
    if request.method == 'POST':
        patient = {
            "full_name": request.form.get('full_name'),
            "dob": request.form.get('dob'),
            "email": request.form.get('email'),
            "phone": request.form.get('phone'),
            "avatar_url": request.form.get('avatar_url') or '/static/avatars/demo-patient.png',
            "notes": request.form.get('notes'),
            "debt": 0
        }
        db.patients.insert_one(patient)
        return redirect(url_for('patients'))
    return render_template('add_patient.html')

# --- КАРТОЧКА ПАЦИЕНТА
@app.route('/patient/<patient_id>')
def patient_card(patient_id):
    patient = db.patients.find_one({'_id': ObjectId(patient_id)})
    if not patient:
        return "Patient not found", 404
    appointments = list(db.events.find({'patient_id': patient['_id']}))
    for app in appointments:
        app['_id'] = str(app['_id'])
        app['doctor_id'] = str(app.get('doctor_id', ''))
        app['datetime'] = app.get('datetime', '')
        app['service'] = app.get('service', '')
        app['sum'] = float(app.get('sum', 0))
        doctor = db.doctors.find_one({'_id': ObjectId(app['doctor_id'])}) if app['doctor_id'] else None
        app['doctor_name'] = doctor['full_name'] if doctor else '—'
    total_paid = sum([app['sum'] for app in appointments])
    debt = patient.get('debt', 0)
    dob = patient.get('dob')
    if dob:
        try:
            dob_dt = datetime.strptime(dob, "%Y-%m-%d")
            age = (datetime.now() - dob_dt).days // 365
        except:
            age = ''
    else:
        age = ''
    patient['_id'] = str(patient['_id'])
    patient['avatar_url'] = patient.get('avatar_url', '/static/avatars/demo-patient.png')
    patient['appointments'] = appointments
    patient['total_paid'] = total_paid
    patient['debt'] = debt
    patient['age'] = age
    return render_template('patient_card.html', patient=patient)

# --- РЕДАКТИРОВАТЬ ПАЦИЕНТА
@app.route('/edit_patient/<patient_id>', methods=['GET', 'POST'])
def edit_patient(patient_id):
    patient = db.patients.find_one({'_id': ObjectId(patient_id)})
    if not patient:
        return "Patient not found", 404
    if request.method == 'POST':
        db.patients.update_one(
            {'_id': ObjectId(patient_id)},
            {'$set': {
                "full_name": request.form.get('full_name'),
                "dob": request.form.get('dob'),
                "email": request.form.get('email'),
                "phone": request.form.get('phone'),
                "avatar_url": request.form.get('avatar_url'),
                "notes": request.form.get('notes'),
            }})
        return redirect(url_for('patient_card', patient_id=patient_id))
    return render_template('edit_patient.html', patient=patient)

# --- ДОБАВИТЬ ОПЛАТУ
@app.route('/add_payment/<patient_id>', methods=['GET', 'POST'])
def add_payment(patient_id):
    patient = db.patients.find_one({'_id': ObjectId(patient_id)})
    if not patient:
        return "Patient not found", 404
    if request.method == 'POST':
        amount = float(request.form.get('amount', 0))
        comment = request.form.get('comment', '')
        payment = {
            "patient_id": ObjectId(patient_id),
            "amount": amount,
            "comment": comment,
            "datetime": datetime.now().strftime("%Y-%m-%d %H:%M"),
        }
        db.payments.insert_one(payment)
        db.patients.update_one({'_id': ObjectId(patient_id)}, {'$inc': {'debt': -amount}})
        return redirect(url_for('patient_card', patient_id=patient_id))
    return render_template('add_payment.html', patient=patient)

# --- СПИСОК ВРАЧЕЙ
@app.route('/doctors')
def doctors():
    doctors = list(db.doctors.find())
    for d in doctors:
        d['_id'] = str(d['_id'])
        d['full_name'] = d.get('full_name', '')
        d['specialization'] = d.get('specialization', '')
        d['phone'] = d.get('phone', '')
        d['email'] = d.get('email', '')
        d['status'] = d.get('status', '')
        d['avatar_url'] = d.get('avatar_url', '/static/avatars/demo-doctor.png')
    return render_template('doctors.html', doctors=doctors)

# --- ДОБАВИТЬ ВРАЧА
@app.route('/add_doctor', methods=['GET', 'POST'])
def add_doctor():
    if request.method == 'POST':
        doctor = {
            "full_name": request.form.get('full_name'),
            "specialization": request.form.get('specialization'),
            "email": request.form.get('email'),
            "phone": request.form.get('phone'),
            "avatar_url": request.form.get('avatar_url') or '/static/avatars/demo-doctor.png',
            "status": "активен"
        }
        db.doctors.insert_one(doctor)
        return redirect(url_for('doctors'))
    return render_template('add_doctor.html')

# --- КАРТОЧКА ВРАЧА
@app.route('/doctor/<doctor_id>')
def doctor_card(doctor_id):
    doctor = db.doctors.find_one({'_id': ObjectId(doctor_id)})
    if not doctor:
        return "Doctor not found", 404
    appointments = list(db.events.find({'doctor_id': doctor['_id']}))
    total_income = sum(a.get('sum', 0) for a in appointments)
    for a in appointments:
        a['_id'] = str(a['_id'])
        a['datetime'] = a.get('datetime', '')
        a['service'] = a.get('service', '')
        a['sum'] = a.get('sum', 0)
    doctor['_id'] = str(doctor['_id'])
    doctor['appointments'] = appointments
    doctor['total_income'] = total_income
    return render_template('doctor_card.html', doctor=doctor, is_admin=True)

# --- РЕДАКТИРОВАТЬ ВРАЧА
@app.route('/edit_doctor/<doctor_id>', methods=['GET', 'POST'])
def edit_doctor(doctor_id):
    doctor = db.doctors.find_one({'_id': ObjectId(doctor_id)})
    if not doctor:
        return "Doctor not found", 404
    if request.method == 'POST':
        db.doctors.update_one(
            {'_id': ObjectId(doctor_id)},
            {'$set': {
                "full_name": request.form.get('full_name'),
                "specialization": request.form.get('specialization'),
                "email": request.form.get('email'),
                "phone": request.form.get('phone'),
                "avatar_url": request.form.get('avatar_url'),
                "status": request.form.get('status', 'активен')
            }})
        return redirect(url_for('doctor_card', doctor_id=doctor_id))
    return render_template('edit_doctor.html', doctor=doctor)

# --- Главная страница (редирект на календарь)
@app.route('/')
def index():
    return redirect(url_for('calendar'))

# --- Запуск приложения
if __name__ == '__main__':
    app.run(debug=True)
