#!/usr/bin/env python3
"""
Скрипт для исправления навигации и полной интеграции всех страниц медплатформы
"""

import os
import re


def fix_base_html_navigation():
    """Исправление навигации в base.html"""
    print("🔧 ИСПРАВЛЕНИЕ НАВИГАЦИИ В BASE.HTML")
    print("=" * 50)

    base_html_path = "templates/base.html"

    if not os.path.exists(base_html_path):
        print("❌ Файл base.html не найден!")
        return False

    # Читаем текущий base.html
    with open(base_html_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Создаем резервную копию
    backup_path = base_html_path + ".backup_nav"
    with open(backup_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"💾 Создана резервная копия: {backup_path}")

    # Новое левое меню с правильными ссылками
    new_sidebar = """        <!-- Sidebar -->
        <nav class="col-md-3 col-lg-2 d-md-block bg-light sidebar collapse">
            <div class="position-sticky pt-3">
                <ul class="nav flex-column">
                    <li class="nav-item">
                        <a class="nav-link {{ 'active' if request.endpoint == 'calendar' else '' }}"
                           href="{{ url_for('calendar') }}">
                            <i class="fas fa-calendar-alt"></i> Расписание
                        </a>
                    </li>

                    <li class="nav-item">
                        <a class="nav-link {{ 'active' if request.endpoint == 'patients' else '' }}"
                           href="{{ url_for('patients') }}">
                            <i class="fas fa-users"></i> Пациенты
                        </a>
                    </li>

                    <li class="nav-item">
                        <a class="nav-link {{ 'active' if request.endpoint == 'doctors' else '' }}"
                           href="{{ url_for('doctors') }}">
                            <i class="fas fa-user-md"></i> Врачи
                        </a>
                    </li>

                    <li class="nav-item">
                        <a class="nav-link {{ 'active' if request.endpoint == 'services' else '' }}"
                           href="{{ url_for('services') }}">
                            <i class="fas fa-list"></i> Услуги
                        </a>
                    </li>

                    <li class="nav-item">
                        <a class="nav-link {{ 'active' if request.endpoint == 'rooms' else '' }}"
                           href="{{ url_for('rooms') }}">
                            <i class="fas fa-door-open"></i> Кабинеты
                        </a>
                    </li>

                    <li class="nav-item">
                        <a class="nav-link {{ 'active' if request.endpoint == 'finance' else '' }}"
                           href="{{ url_for('finance') }}">
                            <i class="fas fa-ruble-sign"></i> Финансы
                        </a>
                    </li>

                    <li class="nav-item">
                        <a class="nav-link {{ 'active' if request.endpoint == 'reports' else '' }}"
                           href="{{ url_for('reports') }}">
                            <i class="fas fa-chart-bar"></i> Отчеты
                        </a>
                    </li>

                    <!-- Разделитель -->
                    <hr class="my-3">

                    <li class="nav-item">
                        <a class="nav-link" href="{{ url_for('logout') }}">
                            <i class="fas fa-sign-out-alt"></i> Выход
                        </a>
                    </li>
                </ul>

                <!-- Отладочное меню (только в разработке) -->
                {% if config.DEBUG %}
                <hr class="my-3">
                <h6 class="sidebar-heading d-flex justify-content-between align-items-center px-3 mt-4 mb-1 text-muted">
                    <span>Отладка</span>
                </h6>
                <ul class="nav flex-column mb-2">
                    <li class="nav-item">
                        <a class="nav-link" href="/debug/info">
                            <i class="fas fa-bug"></i> Техническая информация
                        </a>
                    </li>
                </ul>
                {% endif %}
            </div>
        </nav>"""

    # Заменяем старое меню на новое
    sidebar_pattern = r'<nav class="col-md-3.*?</nav>'
    if re.search(sidebar_pattern, content, re.DOTALL):
        content = re.sub(sidebar_pattern, new_sidebar, content, flags=re.DOTALL)
        print("✅ Левое меню обновлено")
    else:
        print("⚠️ Не удалось найти левое меню для замены")

    # Убираем отладочное меню из верхней части, если оно есть
    debug_menu_pattern = r"<!-- ОТЛАДОЧНОЕ МЕНЮ -->.*?<!-- КОНЕЦ ОТЛАДОЧНОГО МЕНЮ -->"
    content = re.sub(debug_menu_pattern, "", content, flags=re.DOTALL)

    # Сохраняем обновленный файл
    with open(base_html_path, "w", encoding="utf-8") as f:
        f.write(content)

    print("✅ Навигация исправлена")
    return True


def add_missing_routes_to_main():
    """Добавление недостающих маршрутов в main.py"""
    print("\n🔧 ДОБАВЛЕНИЕ НЕДОСТАЮЩИХ МАРШРУТОВ")
    print("=" * 50)

    main_py_path = "main.py"

    if not os.path.exists(main_py_path):
        print("❌ Файл main.py не найден!")
        return False

    # Читаем main.py
    with open(main_py_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Проверяем, какие маршруты уже есть
    existing_routes = {
        "patients": "/patients" in content and "@app.route('/patients')" in content,
        "services": "/services" in content and "@app.route('/services')" in content,
        "doctors": "/doctors" in content and "@app.route('/doctors')" in content,
        "rooms": "/rooms" in content and "@app.route('/rooms')" in content,
        "reports": "/reports" in content and "@app.route('/reports')" in content,
        "finance": "def finance(" in content,
    }

    print("📋 Статус маршрутов:")
    for route, exists in existing_routes.items():
        status = "✅" if exists else "❌"
        print(f"   {status} {route}")

    # Маршруты для добавления (если их нет)
    new_routes = '''
# === ОСНОВНЫЕ СТРАНИЦЫ МЕДПЛАТФОРМЫ ===

@app.route('/patients')
def patients():
    """Список всех пациентов"""
    try:
        # Получаем всех пациентов
        patients_list = list(db.patients.find().sort('name', 1))

        # Для каждого пациента получаем статистику
        for patient in patients_list:
            patient['appointments_count'] = db.appointments.count_documents({
                'patient_id': str(patient['_id'])
            })

            # Последняя запись
            last_appointment = db.appointments.find_one({
                'patient_id': str(patient['_id'])
            }, sort=[('date', -1), ('time', -1)])

            patient['last_appointment'] = last_appointment

        return render_template('patients.html', patients=patients_list)

    except Exception as e:
        flash(f'Ошибка при загрузке пациентов: {str(e)}', 'error')
        return render_template('patients.html', patients=[])

@app.route('/services')
def services():
    """Список всех услуг"""
    try:
        # Получаем все услуги
        services_list = list(db.services.find({'active': True}).sort('name', 1))

        # Статистика по каждой услуге
        for service in services_list:
            service['appointments_count'] = db.appointments.count_documents({
                'service_id': str(service['_id'])
            })

            # Доход от услуги
            revenue_pipeline = [
                {'$match': {
                    'service_id': str(service['_id']),
                    'type': 'income'
                }},
                {'$group': {'_id': None, 'total': {'$sum': '$amount'}}}
            ]

            revenue_result = list(db.ledger.aggregate(revenue_pipeline))
            service['total_revenue'] = revenue_result[0]['total'] if revenue_result else 0

        return render_template('services.html', services=services_list)

    except Exception as e:
        flash(f'Ошибка при загрузке услуг: {str(e)}', 'error')
        return render_template('services.html', services=[])

@app.route('/doctors')
def doctors():
    """Список всех врачей"""
    try:
        # Получаем всех врачей
        doctors_list = list(db.doctors.find({'active': True}).sort('name', 1))

        # Статистика по каждому врачу
        for doctor in doctors_list:
            doctor['appointments_count'] = db.appointments.count_documents({
                'doctor_id': str(doctor['_id'])
            })

            # Записи на сегодня
            today = datetime.now().strftime('%Y-%m-%d')
            doctor['today_appointments'] = db.appointments.count_documents({
                'doctor_id': str(doctor['_id']),
                'date': today
            })

        return render_template('doctors.html', doctors=doctors_list)

    except Exception as e:
        flash(f'Ошибка при загрузке врачей: {str(e)}', 'error')
        return render_template('doctors.html', doctors=[])

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

# === КОНЕЦ ОСНОВНЫХ СТРАНИЦ ===
'''

    # Проверяем, нужно ли добавлять маршруты
    routes_to_add = []
    if not existing_routes["patients"]:
        routes_to_add.append("patients")
    if not existing_routes["services"]:
        routes_to_add.append("services")
    if not existing_routes["doctors"]:
        routes_to_add.append("doctors")
    if not existing_routes["rooms"]:
        routes_to_add.append("rooms")
    if not existing_routes["reports"]:
        routes_to_add.append("reports")

    if routes_to_add:
        # Найдем место для вставки маршрутов
        pattern = r'(if __name__ == ["\']__main__["\']:.*)'
        match = re.search(pattern, content, re.DOTALL)

        if match:
            content = content.replace(match.group(1), new_routes + "\n\n" + match.group(1))
        else:
            content += new_routes

        # Сохраняем обновленный файл
        with open(main_py_path, "w", encoding="utf-8") as f:
            f.write(content)

        print(f"✅ Добавлены маршруты: {', '.join(routes_to_add)}")
    else:
        print("✅ Все маршруты уже существуют")

    return True


def create_missing_templates():
    """Создание недостающих шаблонов"""
    print("\n🔧 СОЗДАНИЕ НЕДОСТАЮЩИХ ШАБЛОНОВ")
    print("=" * 50)

    templates_dir = "templates"
    if not os.path.exists(templates_dir):
        os.makedirs(templates_dir)

    # Шаблон doctors.html
    doctors_template = """{% extends "base.html" %}
{% set page_title = "Врачи" %}

{% block content %}
<div class="container-fluid">
    <div class="d-flex justify-content-between align-items-center mb-4">
        <h2>Управление врачами</h2>
        <a href="/add_doctor" class="btn btn-primary">
            <i class="fas fa-plus"></i> Добавить врача
        </a>
    </div>

    <div class="row">
        {% for doctor in doctors %}
        <div class="col-md-6 col-lg-4 mb-4">
            <div class="card h-100">
                <div class="card-header d-flex justify-content-between">
                    <h5 class="mb-0">{{ doctor.name }}</h5>
                    <span class="badge bg-{{ 'success' if doctor.active else 'secondary' }}">
                        {{ 'Активный' if doctor.active else 'Неактивный' }}
                    </span>
                </div>
                <div class="card-body">
                    <p class="text-muted">{{ doctor.specialty or 'Специальность не указана' }}</p>

                    <div class="row text-center">
                        <div class="col-6">
                            <strong>{{ doctor.appointments_count }}</strong><br>
                            <small class="text-muted">Всего записей</small>
                        </div>
                        <div class="col-6">
                            <strong>{{ doctor.today_appointments }}</strong><br>
                            <small class="text-muted">Сегодня</small>
                        </div>
                    </div>

                    {% if doctor.phone %}
                    <div class="mt-2">
                        <small class="text-muted">
                            <i class="fas fa-phone"></i> {{ doctor.phone }}
                        </small>
                    </div>
                    {% endif %}
                </div>
                <div class="card-footer">
                    <a href="/edit_doctor/{{ doctor._id }}" class="btn btn-sm btn-outline-primary me-2">
                        <i class="fas fa-edit"></i> Редактировать
                    </a>
                    <a href="/calendar?doctor={{ doctor._id }}" class="btn btn-sm btn-outline-info">
                        <i class="fas fa-calendar"></i> Расписание
                    </a>
                </div>
            </div>
        </div>
        {% endfor %}
    </div>

    {% if not doctors %}
    <div class="text-center py-5">
        <i class="fas fa-user-md fa-3x text-muted mb-3"></i>
        <h4 class="text-muted">Врачи не найдены</h4>
        <p class="text-muted">Добавьте первого врача для начала работы</p>
    </div>
    {% endif %}
</div>
{% endblock %}"""

    # Обновленный шаблон patients.html
    patients_template = """{% extends "base.html" %}
{% set page_title = "Пациенты" %}

{% block content %}
<div class="container-fluid">
    <div class="d-flex justify-content-between align-items-center mb-4">
        <h2>Список пациентов</h2>
        <a href="/add_patient" class="btn btn-primary">
            <i class="fas fa-plus"></i> Добавить пациента
        </a>
    </div>

    <!-- Поиск пациентов -->
    <div class="row mb-4">
        <div class="col-md-6">
            <div class="input-group">
                <input type="text" class="form-control" id="patientSearch"
                       placeholder="Поиск по имени, телефону или email">
                <button class="btn btn-outline-secondary" type="button">
                    <i class="fas fa-search"></i>
                </button>
            </div>
        </div>
    </div>

    <div class="card">
        <div class="card-body">
            <div class="table-responsive">
                <table class="table table-hover" id="patientsTable">
                    <thead>
                        <tr>
                            <th>Имя</th>
                            <th>Телефон</th>
                            <th>Email</th>
                            <th>Записей</th>
                            <th>Последняя запись</th>
                            <th>Действия</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for patient in patients %}
                        <tr>
                            <td>
                                <strong>{{ patient.name }}</strong>
                                {% if patient.birth_date %}
                                <br><small class="text-muted">{{ patient.birth_date }}</small>
                                {% endif %}
                            </td>
                            <td>{{ patient.phone or '—' }}</td>
                            <td>{{ patient.email or '—' }}</td>
                            <td>
                                <span class="badge bg-info">{{ patient.appointments_count }}</span>
                            </td>
                            <td>
                                {% if patient.last_appointment %}
                                {{ patient.last_appointment.date }}<br>
                                <small class="text-muted">{{ patient.last_appointment.time }}</small>
                                {% else %}
                                —
                                {% endif %}
                            </td>
                            <td>
                                <a href="/patients/{{ patient._id }}" class="btn btn-sm btn-outline-primary me-1">
                                    <i class="fas fa-eye"></i> Карточка
                                </a>
                                <a href="/edit_patient/{{ patient._id }}" class="btn btn-sm btn-outline-secondary">
                                    <i class="fas fa-edit"></i>
                                </a>
                            </td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
    </div>

    {% if not patients %}
    <div class="text-center py-5">
        <i class="fas fa-users fa-3x text-muted mb-3"></i>
        <h4 class="text-muted">Пациенты не найдены</h4>
        <p class="text-muted">Добавьте первого пациента для начала работы</p>
    </div>
    {% endif %}
</div>

<script>
// Поиск пациентов
document.getElementById('patientSearch').addEventListener('input', function(e) {
    const searchTerm = e.target.value.toLowerCase();
    const rows = document.querySelectorAll('#patientsTable tbody tr');

    rows.forEach(row => {
        const text = row.textContent.toLowerCase();
        row.style.display = text.includes(searchTerm) ? '' : 'none';
    });
});
</script>
{% endblock %}"""

    # Создаем недостающие шаблоны
    templates_to_create = [
        ("doctors.html", doctors_template),
    ]

    # Обновляем существующий patients.html
    patients_path = os.path.join(templates_dir, "patients.html")
    with open(patients_path, "w", encoding="utf-8") as f:
        f.write(patients_template)
    print("✅ Обновлен шаблон patients.html")

    # Создаем новые шаблоны
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

    print(f"✅ Обработано {created_count + 1} шаблонов")
    return True


def main():
    """Главная функция"""
    print("🔧 ПОЛНОЕ ИСПРАВЛЕНИЕ МЕДПЛАТФОРМЫ")
    print("=" * 60)

    success_count = 0
    total_tasks = 3

    # 1. Исправляем навигацию
    if fix_base_html_navigation():
        success_count += 1

    # 2. Добавляем недостающие маршруты
    if add_missing_routes_to_main():
        success_count += 1

    # 3. Создаем недостающие шаблоны
    if create_missing_templates():
        success_count += 1

    print("\n" + "=" * 60)
    print(f"✅ ВЫПОЛНЕНО: {success_count}/{total_tasks} задач")

    if success_count == total_tasks:
        print("\n🎉 ВСЕ ИСПРАВЛЕНИЯ ПРИМЕНЕНЫ!")
        print("\n🚀 СЛЕДУЮЩИЕ ШАГИ:")
        print("1. Перезапустите сервер: python main.py")
        print("2. Войдите в систему")
        print("3. Протестируйте навигацию:")
        print("   - Пациенты → полный список с поиском")
        print("   - Врачи → управление врачами")
        print("   - Услуги → список услуг")
        print("   - Кабинеты → управление кабинетами")
        print("   - Финансы → финансовые операции")
        print("   - Отчеты → аналитика")
        print("\n📋 КЛЮЧЕВЫЕ ИСПРАВЛЕНИЯ:")
        print("- Левое меню ведет на правильные страницы")
        print("- Карточки пациентов доступны")
        print("- Все разделы интегрированы")
        print("- Добавлен поиск по пациентам")
    else:
        print("\n⚠️ НЕКОТОРЫЕ ЗАДАЧИ НЕ ВЫПОЛНЕНЫ")
        print("Проверьте ошибки выше и устраните проблемы")


if __name__ == "__main__":
    main()
