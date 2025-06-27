from flask import Flask, render_template, request, redirect, url_for, session, flash, Response
from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'topsecretkey'  # замени на свой!

client = MongoClient("mongodb+srv://medadmin:medpass123@medplatforma.cnv7fbo.mongodb.net/")
db = client['medplatforma']

def log_event(user, action, details=''):
    db.logs.insert_one({
        'datetime': datetime.now().strftime('%Y-%m-%d %H:%M'),
        'user': user,
        'action': action,
        'details': details
    })

# --- Авторизация ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        user = db.staff.find_one({"email": email})
        if user:
            session['user_id'] = str(user['_id'])
            session['user_role'] = user['role']
            session['user_name'] = user['full_name']
            return redirect(url_for('calendar'))
        else:
            flash("Неверный логин!", "danger")
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# --- Главный календарь ---
@app.route('/')
@app.route('/calendar')
def calendar():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    doctors = list(db.doctors.find())
    for d in doctors: d['_id'] = str(d['_id'])
    patients = list(db.patients.find())
    for p in patients: p['_id'] = str(p['_id'])
    events = list(db.events.find())

    # --- Исправляем все ObjectId ---
    for e in events:
        e['_id'] = str(e['_id'])
        if 'doctor_id' in e:
            e['doctor_id'] = str(e['doctor_id'])
        if 'patient_id' in e:
            e['patient_id'] = str(e['patient_id'])
        # Формируем title для календаря (опционально)
        doctor_name = next((d['full_name'] for d in doctors if d['_id'] == e.get('doctor_id')), '')
        patient_name = next((p['full_name'] for p in patients if p['_id'] == e.get('patient_id')), '')
        e['title'] = f"{doctor_name} — {patient_name}: {e.get('service', '')}"
        e['start'] = e.get('datetime', '')

    return render_template('calendar.html', doctors=doctors, patients=patients, events=events)

# --- Добавить пациента ---
@app.route('/add_patient', methods=['GET', 'POST'])
def add_patient():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        patient = {
            "full_name": request.form.get('full_name'),
            "dob": request.form.get('dob'),
            "phone": request.form.get('phone'),
            "passport": request.form.get('passport'),
            "referral": request.form.get('referral'),
            "reg_address": request.form.get('reg_address'),
            "live_address": request.form.get('live_address'),
            "email": request.form.get('email'),
            "business": request.form.get('business'),
            "hobby": request.form.get('hobby'),
            "notes": request.form.get('notes'),
            "debt": 0,
            "deposit": 0,
            "partner_points": 0,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M")
        }
        db.patients.insert_one(patient)
        log_event(session['user_name'], 'Добавлен пациент', patient['full_name'])
        return redirect(url_for('patients'))
    return render_template('add_patient.html')

@app.route('/patients')
def patients():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    patients = list(db.patients.find())
    for p in patients: p['_id'] = str(p['_id'])
    return render_template('patients.html', patients=patients)

@app.route('/doctors')
def doctors():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    doctors = list(db.doctors.find())
    for d in doctors: d['_id'] = str(d['_id'])
    return render_template('doctors.html', doctors=doctors)

# --- Пациенты, врачи, задачи, staff, отчёты ---
@app.route('/patient/<patient_id>')
def patient_card(patient_id):
    try:
        patient = db.patients.find_one({'_id': ObjectId(patient_id)})
    except Exception as ex:
        print("ObjectId error:", ex)
        return "Пациент не найден", 404
    if not patient:
        return "Пациент не найден", 404
    patient['_id'] = str(patient['_id'])
    return render_template('patient_card.html', patient=patient)

    # История процедур (appointments/events)
    appointments = list(db.events.find({'patient_id': ObjectId(patient_id)}))
    for app in appointments:
        app['_id'] = str(app['_id'])
        app['doctor'] = db.doctors.find_one({'_id': ObjectId(app.get('doctor_id', ''))}) if app.get('doctor_id') else None
        app['doctor_name'] = app['doctor']['full_name'] if app['doctor'] else '—'
        app['service'] = app.get('service', '—')
        app['datetime'] = app.get('datetime', '—')
        app['sum'] = app.get('sum', 0)

    # История оплат
    payments = list(db.payments.find({'patient_id': ObjectId(patient_id)}))
    for pay in payments:
        pay['_id'] = str(pay['_id'])
        pay['datetime'] = pay.get('datetime', '—')
        pay['amount'] = pay.get('amount', 0)
        pay['comment'] = pay.get('comment', '')

    return render_template(
        'patient_card.html',
        patient=patient,
        appointments=appointments,
        payments=payments
    )

@app.route('/doctor/<doctor_id>')
def doctor_card(doctor_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    doctor = db.doctors.find_one({'_id': ObjectId(doctor_id)})
    if not doctor:
        return "Врач не найден", 404
    doctor['_id'] = str(doctor['_id'])
    return render_template('doctor_card.html', doctor=doctor)

@app.route('/tasks')
def tasks():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    tasks = list(db.tasks.find()) if 'tasks' in db.list_collection_names() else []
    return render_template('tasks.html', tasks=tasks)

@app.route('/staff')
def staff():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    staff_list = list(db.staff.find())
    for s in staff_list: s['_id'] = str(s['_id'])
    return render_template('staff.html', staff_list=staff_list)

@app.route('/reports')
def reports():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('reports.html')

# --- Финансовый отчёт (для инвестора) ---
@app.route('/finance_report')
def finance_report():
    if 'user_id' not in session or session['user_role'] != 'investor':
        return redirect(url_for('login'))
    patients = list(db.patients.find())
    doctors = list(db.doctors.find())
    events = list(db.events.find())
    total_income = sum(float(e.get('sum', 0)) for e in events)
    total_debt = sum(float(p.get('debt', 0)) for p in patients)
    for p in patients:
        p['_id'] = str(p['_id'])
        p['total_paid'] = sum(float(e.get('sum', 0)) for e in events if str(e.get('patient_id')) == p['_id'])
    top_patients = sorted(patients, key=lambda x: x['total_paid'], reverse=True)[:10]
    for d in doctors:
        d['_id'] = str(d['_id'])
        d['total_income'] = sum(float(e.get('sum', 0)) for e in events if str(e.get('doctor_id')) == d['_id'])
    top_doctors = sorted(doctors, key=lambda x: x['total_income'], reverse=True)[:10]
    return render_template('finance_report.html', total_income=total_income, total_debt=total_debt, top_patients=top_patients, top_doctors=top_doctors)

# --- Партнёрская программа ---
@app.route('/partners')
def partners():
    if 'user_id' not in session or session['user_role'] != 'investor':
        return redirect(url_for('login'))
    patients = list(db.patients.find())
    partners_list = [p for p in patients if p.get('referral')]
    for p in partners_list:
        p['_id'] = str(p['_id'])
        p['partner_points'] = p.get('partner_points', 0)
    top_partners = sorted(partners_list, key=lambda x: x['partner_points'], reverse=True)[:10]
    return render_template('partners.html', partners=partners_list, top_partners=top_partners)

# --- Учёт расходов ---
@app.route('/add_expense', methods=['GET', 'POST'])
def add_expense():
    if 'user_id' not in session or session['user_role'] != 'investor':
        return redirect(url_for('login'))
    if request.method == 'POST':
        expense = {
            "date": request.form.get('date'),
            "category": request.form.get('category'),
            "amount": float(request.form.get('amount', 0)),
            "comment": request.form.get('comment', '')
        }
        db.expenses.insert_one(expense)
        return redirect(url_for('expenses'))
    return render_template('add_expense.html')

@app.route('/expenses')
def expenses():
    if 'user_id' not in session or session['user_role'] != 'investor':
        return redirect(url_for('login'))
    expenses = list(db.expenses.find())
    for e in expenses:
        e['_id'] = str(e['_id'])
        e['amount'] = float(e.get('amount', 0))
    total_expenses = sum(e['amount'] for e in expenses)
    total_income = sum(float(e.get('sum', 0)) for e in db.events.find())
    profit = total_income - total_expenses
    return render_template('expenses.html', expenses=expenses, total_expenses=total_expenses, profit=profit, total_income=total_income)

# --- Должники/Депозиты ---
@app.route('/debtors')
def debtors():
    if 'user_id' not in session or session['user_role'] != 'investor':
        return redirect(url_for('login'))
    debtors = list(db.patients.find({'debt': {'$gt': 0}}))
    for p in debtors: p['_id'] = str(p['_id'])
    depositors = list(db.patients.find({'deposit': {'$gt': 0}}))
    for p in depositors: p['_id'] = str(p['_id'])
    return render_template('debtors.html', debtors=debtors, depositors=depositors)

from flask import Response
import csv

@app.route('/export/patients')
def export_patients():
    if session.get('user_role') != 'investor':
        return "Нет доступа", 403
    patients = list(db.patients.find())
    fieldnames = ['full_name', 'dob', 'phone', 'passport', 'email', 'referral', 'debt', 'deposit']
    def generate():
        yield ';'.join(fieldnames) + '\n'
        for p in patients:
            yield ';'.join([str(p.get(f, '')) for f in fieldnames]) + '\n'
    return Response(generate(), mimetype='text/csv',
                    headers={'Content-Disposition': 'attachment;filename=patients.csv'})

@app.route('/export/doctors')
def export_doctors():
    if session.get('user_role') != 'investor':
        return "Нет доступа", 403
    doctors = list(db.doctors.find())
    fieldnames = ['full_name', 'specialization', 'email', 'phone']
    def generate():
        yield ';'.join(fieldnames) + '\n'
        for d in doctors:
            yield ';'.join([str(d.get(f, '')) for f in fieldnames]) + '\n'
    return Response(generate(), mimetype='text/csv',
                    headers={'Content-Disposition': 'attachment;filename=doctors.csv'})

@app.route('/logs')
def logs():
    if 'user_id' not in session or session['user_role'] not in ['investor','admin']:
        return redirect(url_for('login'))
    logs = list(db.logs.find().sort('datetime', -1).limit(100))
    return render_template('logs.html', logs=logs)

# --- Запуск ---
if __name__ == '__main__':
    app.run(debug=True)
