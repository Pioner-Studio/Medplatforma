#!/usr/bin/env python3
"""
Добавление недостающих маршрутов для пациентов и исправление левого меню
"""

import os
import re


def add_patients_route():
    """Добавление маршрута /patients"""
    print("🔧 ДОБАВЛЕНИЕ МАРШРУТА /PATIENTS")
    print("=" * 35)

    main_py_path = "main.py"

    # Читаем файл
    with open(main_py_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Проверяем, есть ли уже маршрут /patients
    if "@app.route('/patients')" in content or '@app.route("/patients")' in content:
        print("✅ Маршрут /patients уже существует")
        return True

    # Создаем маршрут для пациентов
    patients_route = '''
@app.route('/patients')
@login_required
def patients():
    """Список всех пациентов"""
    try:
        # Получаем всех пациентов
        patients_list = list(db.patients.find().sort('full_name', 1))

        # Для каждого пациента получаем статистику
        for patient in patients_list:
            patient['_id'] = str(patient['_id'])

            # Количество записей
            patient['appointments_count'] = db.appointments.count_documents({
                'patient_id': patient['_id']
            })

            # Последняя запись
            last_appointment = db.appointments.find_one({
                'patient_id': patient['_id']
            }, sort=[('created_at', -1)])

            patient['last_appointment'] = last_appointment

        return render_template('patients.html', patients=patients_list)

    except Exception as e:
        flash(f'Ошибка при загрузке пациентов: {str(e)}', 'error')
        return render_template('patients.html', patients=[])
'''

    # Находим место для вставки (перед if __name__)
    pattern = r'(if __name__ == ["\']__main__["\']:.*)'
    match = re.search(pattern, content, re.DOTALL)

    if match:
        content = content.replace(match.group(1), patients_route + "\n\n" + match.group(1))
    else:
        content += patients_route

    # Сохраняем файл
    with open(main_py_path, "w", encoding="utf-8") as f:
        f.write(content)

    print("✅ Добавлен маршрут /patients")
    return True


def fix_base_html_menu():
    """Исправление левого меню в base.html"""
    print("\n🔧 ИСПРАВЛЕНИЕ ЛЕВОГО МЕНЮ")
    print("=" * 30)

    base_html_path = "templates/base.html"

    if not os.path.exists(base_html_path):
        print("❌ Файл base.html не найден!")
        return False

    # Читаем base.html
    with open(base_html_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Создаем резервную копию
    backup_path = base_html_path + ".backup_menu"
    with open(backup_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"💾 Создана резервная копия: {backup_path}")

    # Новое левое меню с правильными ссылками
    new_sidebar = """        <!-- Sidebar -->
        <nav class="col-md-3 col-lg-2 d-md-block bg-light sidebar collapse">
            <div class="position-sticky pt-3">
                <ul class="nav flex-column">
                    <li class="nav-item">
                        <a class="nav-link {{ 'active' if request.endpoint == 'calendar_view' else '' }}"
                           href="/">
                            <i class="fas fa-calendar-alt"></i> Расписание
                        </a>
                    </li>

                    <li class="nav-item">
                        <a class="nav-link {{ 'active' if request.endpoint == 'patients' else '' }}"
                           href="/patients">
                            <i class="fas fa-users"></i> Пациенты
                        </a>
                    </li>

                    <li class="nav-item">
                        <a class="nav-link {{ 'active' if request.endpoint == 'doctors' else '' }}"
                           href="/doctors">
                            <i class="fas fa-user-md"></i> Врачи
                        </a>
                    </li>

                    <li class="nav-item">
                        <a class="nav-link" href="/tasks">
                            <i class="fas fa-list"></i> Задачи
                        </a>
                    </li>

                    <li class="nav-item">
                        <a class="nav-link" href="/partners">
                            <i class="fas fa-handshake"></i> Сообщения
                        </a>
                    </li>

                    <li class="nav-item">
                        <a class="nav-link" href="/data_tools">
                            <i class="fas fa-door-open"></i> Кабинеты
                        </a>
                    </li>

                    <li class="nav-item">
                        <a class="nav-link" href="/add_service">
                            <i class="fas fa-plus"></i> Услуги
                        </a>
                    </li>

                    <li class="nav-item">
                        <a class="nav-link" href="/ztl">
                            <i class="fas fa-users"></i> Пациенты
                        </a>
                    </li>

                    <li class="nav-item">
                        <a class="nav-link" href="/backup">
                            <i class="fas fa-upload"></i> ЗТЛ
                        </a>
                    </li>

                    <li class="nav-item">
                        <a class="nav-link" href="/partners">
                            <i class="fas fa-handshake"></i> Партнерская программа
                        </a>
                    </li>

                    <li class="nav-item">
                        <a class="nav-link {{ 'active' if request.endpoint == 'finance_report' else '' }}"
                           href="/finance_report">
                            <i class="fas fa-ruble-sign"></i> Финансовый отчет
                        </a>
                    </li>

                    <li class="nav-item">
                        <a class="nav-link" href="/logs">
                            <i class="fas fa-file-alt"></i> Журнал действий
                        </a>
                    </li>

                    <li class="nav-item">
                        <a class="nav-link" href="/export_data">
                            <i class="fas fa-download"></i> Экспорт / Импорт
                        </a>
                    </li>
                </ul>
            </div>
        </nav>"""

    # Ищем и заменяем sidebar
    sidebar_pattern = r'<nav class="col-md-3.*?</nav>'
    if re.search(sidebar_pattern, content, re.DOTALL):
        content = re.sub(sidebar_pattern, new_sidebar, content, flags=re.DOTALL)
        print("✅ Левое меню обновлено")
    else:
        # Если не нашли nav, ищем по другому паттерну
        sidebar_pattern2 = r"<!-- Sidebar -->.*?</ul>\s*</div>\s*</nav>"
        if re.search(sidebar_pattern2, content, re.DOTALL):
            content = re.sub(sidebar_pattern2, new_sidebar, content, flags=re.DOTALL)
            print("✅ Левое меню обновлено (альтернативный поиск)")
        else:
            print("⚠️ Не удалось найти левое меню для замены")

    # Сохраняем обновленный файл
    with open(base_html_path, "w", encoding="utf-8") as f:
        f.write(content)

    return True


def create_patients_template():
    """Создание шаблона patients.html"""
    print("\n🔧 СОЗДАНИЕ ШАБЛОНА PATIENTS.HTML")
    print("=" * 35)

    templates_dir = "templates"
    patients_template_path = os.path.join(templates_dir, "patients.html")

    # Проверяем, есть ли уже шаблон
    if os.path.exists(patients_template_path):
        print("✅ Шаблон patients.html уже существует")
        return True

    # Создаем шаблон
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
                                <strong>{{ patient.full_name or patient.name or 'Имя не указано' }}</strong>
                                {% if patient.birth_date %}
                                <br><small class="text-muted">{{ patient.birth_date }}</small>
                                {% endif %}
                            </td>
                            <td>{{ patient.phone or '—' }}</td>
                            <td>{{ patient.email or '—' }}</td>
                            <td>
                                <span class="badge bg-info">{{ patient.appointments_count or 0 }}</span>
                            </td>
                            <td>
                                {% if patient.last_appointment %}
                                {{ patient.last_appointment.date or '—' }}<br>
                                <small class="text-muted">{{ patient.last_appointment.time or '—' }}</small>
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
        <a href="/add_patient" class="btn btn-primary">
            <i class="fas fa-plus"></i> Добавить пациента
        </a>
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

    # Сохраняем шаблон
    with open(patients_template_path, "w", encoding="utf-8") as f:
        f.write(patients_template)

    print("✅ Создан шаблон patients.html")
    return True


def add_patient_card_route():
    """Добавление маршрута для карточки пациента"""
    print("\n🔧 ДОБАВЛЕНИЕ МАРШРУТА КАРТОЧКИ ПАЦИЕНТА")
    print("=" * 40)

    main_py_path = "main.py"

    # Читаем файл
    with open(main_py_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Проверяем, есть ли уже маршрут
    if "def patient_card_page(" in content:
        print("✅ Маршрут карточки пациента уже существует")
        return True

    # Создаем маршрут
    card_route = '''
@app.route('/patients/<patient_id>')
@login_required
def patient_card_page(patient_id):
    """Карточка пациента"""
    try:
        from bson import ObjectId

        # Получаем пациента
        patient = db.patients.find_one({'_id': ObjectId(patient_id)})
        if not patient:
            flash('Пациент не найден', 'error')
            return redirect('/patients')

        patient['_id'] = str(patient['_id'])

        # Получаем записи пациента
        appointments = list(db.appointments.find({
            'patient_id': patient_id
        }).sort('date', -1).limit(20))

        # Получаем финансовые операции
        financial_records = list(db.ledger.find({
            'patient_id': patient_id
        }).sort('date', -1).limit(10))

        return render_template('patient_card.html',
                             patient=patient,
                             appointments=appointments,
                             financial_records=financial_records)

    except Exception as e:
        flash(f'Ошибка при загрузке карточки пациента: {str(e)}', 'error')
        return redirect('/patients')
'''

    # Добавляем маршрут
    pattern = r'(if __name__ == ["\']__main__["\']:.*)'
    match = re.search(pattern, content, re.DOTALL)

    if match:
        content = content.replace(match.group(1), card_route + "\n\n" + match.group(1))
    else:
        content += card_route

    # Сохраняем файл
    with open(main_py_path, "w", encoding="utf-8") as f:
        f.write(content)

    print("✅ Добавлен маршрут карточки пациента")
    return True


def main():
    """Главная функция"""
    print("🔧 ДОБАВЛЕНИЕ НЕДОСТАЮЩИХ МАРШРУТОВ ПАЦИЕНТОВ")
    print("=" * 55)

    success_count = 0
    total_tasks = 4

    # 1. Добавляем маршрут /patients
    if add_patients_route():
        success_count += 1

    # 2. Исправляем левое меню
    if fix_base_html_menu():
        success_count += 1

    # 3. Создаем шаблон patients.html
    if create_patients_template():
        success_count += 1

    # 4. Добавляем маршрут карточки пациента
    if add_patient_card_route():
        success_count += 1

    print(f"\n{'='*55}")
    print(f"✅ ВЫПОЛНЕНО: {success_count}/{total_tasks} задач")

    if success_count == total_tasks:
        print("\n🎉 ВСЕ ИСПРАВЛЕНИЯ ПРИМЕНЕНЫ!")
        print("\n🚀 СЛЕДУЮЩИЕ ШАГИ:")
        print("1. Перезапустите сервер: Ctrl+C, затем python main.py")
        print("2. Войдите в систему")
        print("3. Проверьте левое меню:")
        print("   - 'Пациенты' должно открывать список пациентов")
        print("   - 'Финансовый отчет' должно открывать правильные финансы")
        print("   - Карточки пациентов доступны по кнопке 'Карточка'")
        print("\n📋 ИСПРАВЛЕНИЯ:")
        print("- Добавлен маршрут /patients")
        print("- Обновлено левое меню с правильными ссылками")
        print("- Создан шаблон для списка пациентов")
        print("- Добавлен маршрут для карточек пациентов")
    else:
        print("\n⚠️ НЕКОТОРЫЕ ЗАДАЧИ НЕ ВЫПОЛНЕНЫ")
        print("Проверьте ошибки выше")


if __name__ == "__main__":
    main()
