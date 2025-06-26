from flask import Flask, render_template, request, redirect, url_for, session, flash
from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'topsecretkey'  # замени на свой!

client = MongoClient("mongodb+srv://medadmin:medpass123@medplatforma.cnv7fbo.mongodb.net/")
db = client['medplatforma']

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
    for e in events:
        e['_id'] = str(e.get('_id', ''))
        e['doctor_id'] = str(e.get('doctor_id', ''))
        e['patient_id'] = str(e.get('patient_id', ''))
        e['title'] = f"{next((doc['full_name'] for doc in doctors if doc['_id'] == e['doctor_id']), '')} — {next((pat['full_name'] for pat in patients if pat['_id'] == e['patient_id']), '')}: {e.get('service', '')}"
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
        return redirect(url_for('patients'))
    return render_template('add_patient.html')

# --- Пациенты, врачи, задачи, staff, отчёты ---
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

# --- Запуск ---
if __name__ == '__main__':
    app.run(debug=True)
