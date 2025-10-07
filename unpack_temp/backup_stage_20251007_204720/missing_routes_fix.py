#!/usr/bin/env python3
"""
Скрипт для добавления недостающих маршрутов в main.py
"""

import re
import os


def add_missing_routes():
    print("🔧 ДОБАВЛЕНИЕ НЕДОСТАЮЩИХ МАРШРУТОВ")
    print("=" * 60)

    main_py_path = "main.py"

    if not os.path.exists(main_py_path):
        print("❌ Файл main.py не найден!")
        return False

    # Читаем текущий main.py
    with open(main_py_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Маршруты для добавления
    new_routes = '''
# === НЕДОСТАЮЩИЕ МАРШРУТЫ ===

@app.route('/add_patient', methods=['GET', 'POST'])
def add_patient():
    """Добавление нового пациента"""
    if request.method == 'POST':
        try:
            # Получаем данные из формы
            patient_data = {
                'name': request.form.get('name', '').strip(),
                'phone': request.form.get('phone', '').strip(),
                'email': request.form.get('email', '').strip(),
                'birth_date': request.form.get('birth_date', '').strip(),
                'address': request.form.get('address', '').strip(),
                'notes': request.form.get('notes', '').strip(),
                'created_at': datetime.now(),
                'updated_at': datetime.now()
            }

            # Валидация обязательных полей
            if not patient_data['name']:
                flash('Имя пациента обязательно для заполнения', 'error')
                return render_template('add_patient.html', patient=patient_data)

            # Проверяем уникальность телефона
            if patient_data['phone'] and db.patients.find_one({'phone': patient_data['phone']}):
                flash('Пациент с таким телефоном уже существует', 'error')
                return render_template('add_patient.html', patient=patient_data)

            # Сохраняем в БД
            result = db.patients.insert_one(patient_data)
            patient_id = str(result.inserted_id)

            flash('Пациент успешно добавлен!', 'success')
            return redirect(f'/patients/{patient_id}')

        except Exception as e:
            flash(f'Ошибка при добавлении пациента: {str(e)}', 'error')
            return render_template('add_patient.html', patient=patient_data)

    # GET запрос - показываем форму
    return render_template('add_patient.html')

@app.route('/add_service', methods=['GET', 'POST'])
def add_service():
    """Добавление новой услуги"""
    if request.method == 'POST':
        try:
            # Получаем данные из формы
            service_data = {
                'name': request.form.get('name', '').strip(),
                'price': float(request.form.get('price', 0)),
                'duration': int(request.form.get('duration', 30)),
                'description': request.form.get('description', '').strip(),
                'category': request.form.get('category', 'Общие').strip(),
                'active': True,
                'created_at': datetime.now(),
                'updated_at': datetime.now()
            }

            # Валидация
            if not service_data['name']:
                flash('Название услуги обязательно для заполнения', 'error')
                return render_template('add_service.html', service=service_data)

            if service_data['price'] <= 0:
                flash('Цена услуги должна быть больше 0', 'error')
                return render_template('add_service.html', service=service_data)

            # Проверяем уникальность названия
            if db.services.find_one({'name': service_data['name']}):
                flash('Услуга с таким названием уже существует', 'error')
                return render_template('add_service.html', service=service_data)

            # Сохраняем в БД
            result = db.services.insert_one(service_data)

            flash('Услуга успешно добавлена!', 'success')
            return redirect('/services')

        except ValueError as e:
            flash('Неверный формат цены или продолжительности', 'error')
            return render_template('add_service.html', service=service_data)
        except Exception as e:
            flash(f'Ошибка при добавлении услуги: {str(e)}', 'error')
            return render_template('add_service.html', service=service_data)

    # GET запрос - показываем форму
    categories = ['Консультации', 'Диагностика', 'Лечение', 'Профилактика', 'Общие']
    return render_template('add_service.html', categories=categories)

@app.route('/edit_patient/<patient_id>', methods=['GET', 'POST'])
def edit_patient(patient_id):
    """Редактирование данных пациента"""
    try:
        from bson import ObjectId
        patient = db.patients.find_one({'_id': ObjectId(patient_id)})

        if not patient:
            flash('Пациент не найден', 'error')
            return redirect('/patients')

        if request.method == 'POST':
            # Обновляем данные пациента
            update_data = {
                'name': request.form.get('name', '').strip(),
                'phone': request.form.get('phone', '').strip(),
                'email': request.form.get('email', '').strip(),
                'birth_date': request.form.get('birth_date', '').strip(),
                'address': request.form.get('address', '').strip(),
                'notes': request.form.get('notes', '').strip(),
                'updated_at': datetime.now()
            }

            # Валидация
            if not update_data['name']:
                flash('Имя пациента обязательно для заполнения', 'error')
                return render_template('edit_patient.html', patient=patient)

            # Обновляем в БД
            db.patients.update_one(
                {'_id': ObjectId(patient_id)},
                {'$set': update_data}
            )

            flash('Данные пациента обновлены!', 'success')
            return redirect(f'/patients/{patient_id}')

        # GET запрос - показываем форму редактирования
        return render_template('edit_patient.html', patient=patient)

    except Exception as e:
        flash(f'Ошибка при редактировании пациента: {str(e)}', 'error')
        return redirect('/patients')

@app.route('/rooms')
def rooms():
    """Управление кабинетами"""
    try:
        # Получаем все кабинеты
        rooms_list = list(db.rooms.find().sort('number', 1))

        # Статистика использования кабинетов
        for room in rooms_list:
            # Считаем записи на сегодня
            today = datetime.now().strftime('%Y-%m-%d')
            room['today_appointments'] = db.appointments.count_documents({
                'room_id': str(room['_id']),
                'date': today
            })

            # Следующая доступная запись
            next_appointment = db.appointments.find_one({
                'room_id': str(room['_id']),
                'date': {'$gte': today}
            }, sort=[('date', 1), ('time', 1)])

            room['next_appointment'] = next_appointment

        return render_template('rooms.html', rooms=rooms_list)

    except Exception as e:
        flash(f'Ошибка при загрузке кабинетов: {str(e)}', 'error')
        return render_template('rooms.html', rooms=[])

@app.route('/reports')
def reports():
    """Страница отчетов"""
    try:
        # Базовая статистика за текущий месяц
        today = datetime.now()
        month_start = today.replace(day=1).strftime('%Y-%m-%d')
        month_end = today.strftime('%Y-%m-%d')

        # Статистика записей
        total_appointments = db.appointments.count_documents({
            'date': {'$gte': month_start, '$lte': month_end}
        })

        completed_appointments = db.appointments.count_documents({
            'date': {'$gte': month_start, '$lte': month_end},
            'status': 'completed'
        })

        # Финансовая статистика
        total_revenue = 0
        revenue_pipeline = [
            {'$match': {
                'date': {'$gte': month_start, '$lte': month_end},
                'type': 'income'
            }},
            {'$group': {'_id': None, 'total': {'$sum': '$amount'}}}
        ]

        revenue_result = list(db.ledger.aggregate(revenue_pipeline))
        if revenue_result:
            total_revenue = revenue_result[0]['total']

        # Статистика по врачам
        doctors_stats = []
        doctors = list(db.doctors.find({'active': True}))

        for doctor in doctors:
            doctor_appointments = db.appointments.count_documents({
                'doctor_id': str(doctor['_id']),
                'date': {'$gte': month_start, '$lte': month_end}
            })

            doctor_revenue = 0
            doctor_revenue_result = list(db.ledger.aggregate([
                {'$match': {
                    'doctor_id': str(doctor['_id']),
                    'date': {'$gte': month_start, '$lte': month_end},
                    'type': 'income'
                }},
                {'$group': {'_id': None, 'total': {'$sum': '$amount'}}}
            ]))

            if doctor_revenue_result:
                doctor_revenue = doctor_revenue_result[0]['total']

            doctors_stats.append({
                'name': doctor['name'],
                'appointments': doctor_appointments,
                'revenue': doctor_revenue
            })

        stats = {
            'period': f"{month_start} - {month_end}",
            'total_appointments': total_appointments,
            'completed_appointments': completed_appointments,
            'completion_rate': round((completed_appointments / total_appointments * 100) if total_appointments > 0 else 0, 1),
            'total_revenue': total_revenue,
            'doctors_stats': doctors_stats
        }

        return render_template('reports.html', stats=stats)

    except Exception as e:
        flash(f'Ошибка при формировании отчетов: {str(e)}', 'error')
        return render_template('reports.html', stats={})

# === КОНЕЦ НЕДОСТАЮЩИХ МАРШРУТОВ ===
'''

    # Проверяем, есть ли уже эти маршруты
    if "/add_patient" in content and "/add_service" in content:
        print("✅ Маршруты уже добавлены")
        return True

    # Найдем место для вставки (перед if __name__ == '__main__':)
    pattern = r'(if __name__ == ["\']__main__["\']:.*)'
    match = re.search(pattern, content, re.DOTALL)

    if match:
        # Вставляем маршруты перед главным блоком
        content = content.replace(match.group(1), new_routes + "\n\n" + match.group(1))
    else:
        # Если не найден главный блок, добавляем в конец
        content += new_routes

    # Сохраняем обновленный файл
    with open(main_py_path, "w", encoding="utf-8") as f:
        f.write(content)

    print("✅ Недостающие маршруты добавлены:")
    print("   - /add_patient (GET, POST)")
    print("   - /add_service (GET, POST)")
    print("   - /edit_patient/<id> (GET, POST)")
    print("   - /rooms (GET)")
    print("   - /reports (GET)")

    return True


def create_missing_templates():
    """Создание недостающих шаблонов"""
    print("\n--- Создание недостающих шаблонов ---")

    templates_dir = "templates"
    if not os.path.exists(templates_dir):
        os.makedirs(templates_dir)

    # Шаблон добавления пациента
    add_patient_template = """{% extends "base.html" %}
{% set page_title = "Добавить пациента" %}

{% block content %}
<div class="container-fluid">
    <div class="row">
        <div class="col-md-8 offset-md-2">
            <div class="card">
                <div class="card-header">
                    <h3>Добавить нового пациента</h3>
                </div>
                <div class="card-body">
                    <form method="POST">
                        <div class="row">
                            <div class="col-md-6">
                                <div class="form-group mb-3">
                                    <label for="name">Имя и фамилия *</label>
                                    <input type="text" class="form-control" id="name" name="name"
                                           value="{{ patient.name if patient else '' }}" required>
                                </div>

                                <div class="form-group mb-3">
                                    <label for="phone">Телефон</label>
                                    <input type="tel" class="form-control" id="phone" name="phone"
                                           value="{{ patient.phone if patient else '' }}"
                                           placeholder="+7 (999) 123-45-67">
                                </div>

                                <div class="form-group mb-3">
                                    <label for="email">Email</label>
                                    <input type="email" class="form-control" id="email" name="email"
                                           value="{{ patient.email if patient else '' }}">
                                </div>
                            </div>

                            <div class="col-md-6">
                                <div class="form-group mb-3">
                                    <label for="birth_date">Дата рождения</label>
                                    <input type="date" class="form-control" id="birth_date" name="birth_date"
                                           value="{{ patient.birth_date if patient else '' }}">
                                </div>

                                <div class="form-group mb-3">
                                    <label for="address">Адрес</label>
                                    <textarea class="form-control" id="address" name="address" rows="2">{{ patient.address if patient else '' }}</textarea>
                                </div>

                                <div class="form-group mb-3">
                                    <label for="notes">Примечания</label>
                                    <textarea class="form-control" id="notes" name="notes" rows="2">{{ patient.notes if patient else '' }}</textarea>
                                </div>
                            </div>
                        </div>

                        <div class="text-center mt-4">
                            <button type="submit" class="btn btn-primary">
                                <i class="fas fa-save"></i> Сохранить пациента
                            </button>
                            <a href="/patients" class="btn btn-secondary ms-2">
                                <i class="fas fa-times"></i> Отмена
                            </a>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}"""

    # Шаблон добавления услуги
    add_service_template = """{% extends "base.html" %}
{% set page_title = "Добавить услугу" %}

{% block content %}
<div class="container-fluid">
    <div class="row">
        <div class="col-md-6 offset-md-3">
            <div class="card">
                <div class="card-header">
                    <h3>Добавить новую услугу</h3>
                </div>
                <div class="card-body">
                    <form method="POST">
                        <div class="form-group mb-3">
                            <label for="name">Название услуги *</label>
                            <input type="text" class="form-control" id="name" name="name"
                                   value="{{ service.name if service else '' }}" required>
                        </div>

                        <div class="row">
                            <div class="col-md-6">
                                <div class="form-group mb-3">
                                    <label for="price">Цена (руб.) *</label>
                                    <input type="number" class="form-control" id="price" name="price"
                                           value="{{ service.price if service else '' }}"
                                           min="0" step="0.01" required>
                                </div>
                            </div>
                            <div class="col-md-6">
                                <div class="form-group mb-3">
                                    <label for="duration">Продолжительность (мин)</label>
                                    <input type="number" class="form-control" id="duration" name="duration"
                                           value="{{ service.duration if service else '30' }}"
                                           min="5" max="480">
                                </div>
                            </div>
                        </div>

                        <div class="form-group mb-3">
                            <label for="category">Категория</label>
                            <select class="form-control" id="category" name="category">
                                {% for cat in categories %}
                                <option value="{{ cat }}"
                                        {% if service and service.category == cat %}selected{% endif %}>
                                    {{ cat }}
                                </option>
                                {% endfor %}
                            </select>
                        </div>

                        <div class="form-group mb-3">
                            <label for="description">Описание</label>
                            <textarea class="form-control" id="description" name="description" rows="3">{{ service.description if service else '' }}</textarea>
                        </div>

                        <div class="text-center mt-4">
                            <button type="submit" class="btn btn-primary">
                                <i class="fas fa-save"></i> Сохранить услугу
                            </button>
                            <a href="/services" class="btn btn-secondary ms-2">
                                <i class="fas fa-times"></i> Отмена
                            </a>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}"""

    # Шаблон редактирования пациента
    edit_patient_template = """{% extends "base.html" %}
{% set page_title = "Редактировать пациента" %}

{% block content %}
<div class="container-fluid">
    <div class="row">
        <div class="col-md-8 offset-md-2">
            <div class="card">
                <div class="card-header">
                    <h3>Редактировать пациента: {{ patient.name }}</h3>
                </div>
                <div class="card-body">
                    <form method="POST">
                        <div class="row">
                            <div class="col-md-6">
                                <div class="form-group mb-3">
                                    <label for="name">Имя и фамилия *</label>
                                    <input type="text" class="form-control" id="name" name="name"
                                           value="{{ patient.name }}" required>
                                </div>

                                <div class="form-group mb-3">
                                    <label for="phone">Телефон</label>
                                    <input type="tel" class="form-control" id="phone" name="phone"
                                           value="{{ patient.phone or '' }}"
                                           placeholder="+7 (999) 123-45-67">
                                </div>

                                <div class="form-group mb-3">
                                    <label for="email">Email</label>
                                    <input type="email" class="form-control" id="email" name="email"
                                           value="{{ patient.email or '' }}">
                                </div>
                            </div>

                            <div class="col-md-6">
                                <div class="form-group mb-3">
                                    <label for="birth_date">Дата рождения</label>
                                    <input type="date" class="form-control" id="birth_date" name="birth_date"
                                           value="{{ patient.birth_date or '' }}">
                                </div>

                                <div class="form-group mb-3">
                                    <label for="address">Адрес</label>
                                    <textarea class="form-control" id="address" name="address" rows="2">{{ patient.address or '' }}</textarea>
                                </div>

                                <div class="form-group mb-3">
                                    <label for="notes">Примечания</label>
                                    <textarea class="form-control" id="notes" name="notes" rows="2">{{ patient.notes or '' }}</textarea>
                                </div>
                            </div>
                        </div>

                        <div class="text-center mt-4">
                            <button type="submit" class="btn btn-primary">
                                <i class="fas fa-save"></i> Сохранить изменения
                            </button>
                            <a href="/patients/{{ patient._id }}" class="btn btn-info ms-2">
                                <i class="fas fa-eye"></i> Просмотр карточки
                            </a>
                            <a href="/patients" class="btn btn-secondary ms-2">
                                <i class="fas fa-times"></i> Отмена
                            </a>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}"""

    # Шаблон кабинетов
    rooms_template = """{% extends "base.html" %}
{% set page_title = "Управление кабинетами" %}

{% block content %}
<div class="container-fluid">
    <div class="d-flex justify-content-between align-items-center mb-4">
        <h2>Управление кабинетами</h2>
        <button class="btn btn-primary" data-bs-toggle="modal" data-bs-target="#addRoomModal">
            <i class="fas fa-plus"></i> Добавить кабинет
        </button>
    </div>

    <div class="row">
        {% for room in rooms %}
        <div class="col-md-6 col-lg-4 mb-4">
            <div class="card h-100">
                <div class="card-header d-flex justify-content-between">
                    <h5 class="mb-0">Кабинет {{ room.number }}</h5>
                    <span class="badge bg-{{ 'success' if room.active else 'secondary' }}">
                        {{ 'Активный' if room.active else 'Неактивный' }}
                    </span>
                </div>
                <div class="card-body">
                    <p class="text-muted">{{ room.description or 'Без описания' }}</p>

                    <div class="row text-center">
                        <div class="col-6">
                            <strong>{{ room.today_appointments }}</strong><br>
                            <small class="text-muted">Записей сегодня</small>
                        </div>
                        <div class="col-6">
                            {% if room.next_appointment %}
                            <strong>{{ room.next_appointment.time }}</strong><br>
                            <small class="text-muted">Следующая запись</small>
                            {% else %}
                            <strong>—</strong><br>
                            <small class="text-muted">Свободен</small>
                            {% endif %}
                        </div>
                    </div>
                </div>
                <div class="card-footer">
                    <button class="btn btn-sm btn-outline-primary me-2">
                        <i class="fas fa-edit"></i> Редактировать
                    </button>
                    <button class="btn btn-sm btn-outline-info">
                        <i class="fas fa-calendar"></i> Расписание
                    </button>
                </div>
            </div>
        </div>
        {% endfor %}
    </div>

    {% if not rooms %}
    <div class="text-center py-5">
        <i class="fas fa-door-open fa-3x text-muted mb-3"></i>
        <h4 class="text-muted">Кабинеты не найдены</h4>
        <p class="text-muted">Добавьте первый кабинет для начала работы</p>
    </div>
    {% endif %}
</div>
{% endblock %}"""

    # Шаблон отчетов
    reports_template = """{% extends "base.html" %}
{% set page_title = "Отчеты" %}

{% block content %}
<div class="container-fluid">
    <div class="d-flex justify-content-between align-items-center mb-4">
        <h2>Отчеты и аналитика</h2>
        <div class="btn-group">
            <button class="btn btn-outline-primary">Текущий месяц</button>
            <button class="btn btn-outline-secondary">Прошлый месяц</button>
            <button class="btn btn-outline-info">Год</button>
        </div>
    </div>

    {% if stats %}
    <div class="row mb-4">
        <div class="col-md-3">
            <div class="card text-center">
                <div class="card-body">
                    <i class="fas fa-calendar-check fa-2x text-primary mb-3"></i>
                    <h4>{{ stats.total_appointments }}</h4>
                    <p class="text-muted">Всего записей</p>
                </div>
            </div>
        </div>

        <div class="col-md-3">
            <div class="card text-center">
                <div class="card-body">
                    <i class="fas fa-check-circle fa-2x text-success mb-3"></i>
                    <h4>{{ stats.completed_appointments }}</h4>
                    <p class="text-muted">Завершенных</p>
                </div>
            </div>
        </div>

        <div class="col-md-3">
            <div class="card text-center">
                <div class="card-body">
                    <i class="fas fa-percentage fa-2x text-info mb-3"></i>
                    <h4>{{ stats.completion_rate }}%</h4>
                    <p class="text-muted">Процент завершения</p>
                </div>
            </div>
        </div>

        <div class="col-md-3">
            <div class="card text-center">
                <div class="card-body">
                    <i class="fas fa-ruble-sign fa-2x text-warning mb-3"></i>
                    <h4>{{ "{:,.0f}".format(stats.total_revenue) }}</h4>
                    <p class="text-muted">Доход (руб.)</p>
                </div>
            </div>
        </div>
    </div>

    <div class="card">
        <div class="card-header">
            <h5>Статистика по врачам ({{ stats.period }})</h5>
        </div>
        <div class="card-body">
            <div class="table-responsive">
                <table class="table table-hover">
                    <thead>
                        <tr>
                            <th>Врач</th>
                            <th>Записей</th>
                            <th>Доход (руб.)</th>
                            <th>Средний чек</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for doctor in stats.doctors_stats %}
                        <tr>
                            <td>{{ doctor.name }}</td>
                            <td>{{ doctor.appointments }}</td>
                            <td>{{ "{:,.0f}".format(doctor.revenue) }}</td>
                            <td>
                                {% if doctor.appointments > 0 %}
                                {{ "{:,.0f}".format(doctor.revenue / doctor.appointments) }}
                                {% else %}
                                —
                                {% endif %}
                            </td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
    </div>
    {% else %}
    <div class="text-center py-5">
        <i class="fas fa-chart-bar fa-3x text-muted mb-3"></i>
        <h4 class="text-muted">Данные для отчета недоступны</h4>
    </div>
    {% endif %}
</div>
{% endblock %}"""

    # Создаем шаблоны
    templates_to_create = [
        ("add_patient.html", add_patient_template),
        ("add_service.html", add_service_template),
        ("edit_patient.html", edit_patient_template),
        ("rooms.html", rooms_template),
        ("reports.html", reports_template),
    ]

    created_count = 0
    for filename, template_content in templates_to_create:
        template_path = os.path.join(templates_dir, filename)

        if not os.path.exists(template_path):
            with open(template_path, "w", encoding="utf-8") as f:
                f.write(template_content)
            print(f"✅ Создан шаблон: {filename}")
            created_count += 1
        else:
            print(f"⚠️ Шаблон уже существует: {filename}")

    print(f"\n✅ Создано {created_count} новых шаблонов")
    return True


def main():
    """Главная функция"""
    print("🔧 ФИНАЛЬНОЕ ИСПРАВЛЕНИЕ МЕДПЛАТФОРМЫ")
    print("=" * 60)

    success = True

    # 1. Добавляем недостающие маршруты
    print("--- Этап 1: Добавление маршрутов ---")
    if not add_missing_routes():
        success = False

    # 2. Создаем недостающие шаблоны
    print("\n--- Этап 2: Создание шаблонов ---")
    if not create_missing_templates():
        success = False

    print("\n" + "=" * 60)
    if success:
        print("✅ ВСЕ ИСПРАВЛЕНИЯ ПРИМЕНЕНЫ!")
        print("\n🚀 СЛЕДУЮЩИЕ ШАГИ:")
        print("1. Перезапустите сервер: python main.py")
        print("2. Войдите в систему (Gogueva/пароль)")
        print("3. Протестируйте новые страницы:")
        print("   - /patients - список пациентов")
        print("   - /add_patient - добавление пациента")
        print("   - /services - список услуг")
        print("   - /add_service - добавление услуги")
        print("   - /rooms - управление кабинетами")
        print("   - /reports - отчеты и аналитика")
        print("\n📋 ДЛЯ ПОЛНОЙ ГОТОВНОСТИ:")
        print("- Проверьте работу всех ссылок в меню")
        print("- Протестируйте создание/редактирование записей")
        print("- Убедитесь, что финансовые операции работают")
        print("- Настройте ролевые ограничения в production")
    else:
        print("❌ ВОЗНИКЛИ ОШИБКИ ПРИ ИСПРАВЛЕНИИ")
        print("Проверьте вывод выше и устраните проблемы")


if __name__ == "__main__":
    main()
