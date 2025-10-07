# integrate_patient_cards_and_navigation.py
# Интегрируем карточки пациентов с календарем и левым меню

import re
from pathlib import Path


def integrate_patient_creation_with_calendar():
    """Добавляем кнопку создания пациента и интеграцию с календарем"""
    print("=== Интеграция создания пациента с календарем ===")

    calendar_path = Path("templates/calendar.html")
    if not calendar_path.exists():
        print("❌ templates/calendar.html не найден")
        return False

    with open(calendar_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Добавляем кнопку "Новый пациент" в форму создания записи
    if "Новый пациент" not in content:
        # Ищем поле выбора пациента в модальном окне записи
        patient_select_pattern = r"(<select[^>]*patient[^>]*>.*?</select>)"

        if re.search(patient_select_pattern, content, re.DOTALL):
            # Добавляем кнопку после селекта пациентов
            new_patient_button = """
                    <button type="button" class="btn btn-sm btn-outline-primary" onclick="showNewPatientForm()" style="margin-top: 5px;">
                        + Новый пациент
                    </button>

                    <!-- Форма создания нового пациента -->
                    <div id="newPatientForm" style="display: none; margin-top: 10px; padding: 10px; border: 1px solid #ddd; border-radius: 5px;">
                        <h6>Новый пациент</h6>
                        <div class="mb-2">
                            <input type="text" id="newPatientName" placeholder="ФИО*" class="form-control form-control-sm" required>
                        </div>
                        <div class="mb-2">
                            <input type="tel" id="newPatientPhone" placeholder="Телефон" class="form-control form-control-sm">
                        </div>
                        <div class="mb-2">
                            <input type="date" id="newPatientBirthdate" class="form-control form-control-sm">
                        </div>
                        <div class="d-flex gap-2">
                            <button type="button" class="btn btn-sm btn-success" onclick="createPatientAndSelect()">Создать</button>
                            <button type="button" class="btn btn-sm btn-secondary" onclick="hideNewPatientForm()">Отмена</button>
                        </div>
                    </div>"""

            content = re.sub(r"(</select>\s*</div>)", r"\1" + new_patient_button, content, count=1)
            print("✅ Кнопка создания пациента добавлена в форму записи")

    # Добавляем JavaScript функции
    js_functions = """
<script>
// Функции для работы с созданием пациента в календаре
function showNewPatientForm() {
    document.getElementById('newPatientForm').style.display = 'block';
    document.getElementById('newPatientName').focus();
}

function hideNewPatientForm() {
    document.getElementById('newPatientForm').style.display = 'none';
    // Очищаем поля
    document.getElementById('newPatientName').value = '';
    document.getElementById('newPatientPhone').value = '';
    document.getElementById('newPatientBirthdate').value = '';
}

async function createPatientAndSelect() {
    const name = document.getElementById('newPatientName').value.trim();
    const phone = document.getElementById('newPatientPhone').value.trim();
    const birthdate = document.getElementById('newPatientBirthdate').value;

    if (!name) {
        alert('Введите ФИО пациента');
        return;
    }

    try {
        const response = await fetch('/api/patients', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                full_name: name,
                phone: phone,
                birthdate: birthdate
            })
        });

        const result = await response.json();

        if (result.ok) {
            // Добавляем в селект пациентов
            const patientSelect = document.querySelector('select[name="patient_id"]');
            if (patientSelect) {
                const option = new Option(name, result.id, true, true);
                patientSelect.add(option);
            }

            hideNewPatientForm();
            showNotification('Пациент создан и выбран', 'success');
        } else {
            showNotification('Ошибка создания: ' + (result.error || 'Неизвестная ошибка'), 'error');
        }
    } catch (error) {
        showNotification('Ошибка сети: ' + error.message, 'error');
    }
}

function showNotification(message, type = 'info') {
    const alertClass = type === 'success' ? 'alert-success' : type === 'error' ? 'alert-danger' : 'alert-info';

    const notification = document.createElement('div');
    notification.className = `alert ${alertClass} alert-dismissible fade show`;
    notification.style.cssText = 'position: fixed; top: 20px; right: 20px; z-index: 1050; min-width: 300px;';
    notification.innerHTML = `
        ${message}
        <button type="button" class="btn-close" onclick="this.parentElement.remove()"></button>
    `;

    document.body.appendChild(notification);

    setTimeout(() => {
        if (notification.parentNode) {
            notification.remove();
        }
    }, 5000);
}

// Интеграция с кликом по записи в календаре
function handleEventClick(info) {
    const eventId = info.event.id;
    const patientId = info.event.extendedProps.patient_id;

    if (patientId) {
        // Добавляем кнопку "Карточка пациента" в модальное окно
        const modal = document.querySelector('#eventModal') || document.querySelector('.modal');
        if (modal) {
            let patientBtn = modal.querySelector('.patient-card-btn');
            if (!patientBtn) {
                patientBtn = document.createElement('button');
                patientBtn.className = 'btn btn-outline-info btn-sm patient-card-btn';
                patientBtn.innerHTML = '<i class="fas fa-user"></i> Карточка пациента';
                patientBtn.onclick = () => openPatientCard(patientId);

                // Добавляем в футер модального окна
                const modalFooter = modal.querySelector('.modal-footer');
                if (modalFooter) {
                    modalFooter.appendChild(patientBtn);
                }
            }
        }
    }
}

function openPatientCard(patientId) {
    // Открываем карточку пациента в новой вкладке
    window.open(`/patients/${patientId}`, '_blank');
}
</script>"""

    # Добавляем JavaScript перед </body>
    if "createPatientAndSelect" not in content:
        content = content.replace("</body>", js_functions + "\n</body>")
        print("✅ JavaScript функции добавлены")

    # Сохраняем изменения
    with open(calendar_path, "w", encoding="utf-8") as f:
        f.write(content)

    return True


def create_patient_card_page():
    """Создаем страницу карточки пациента"""
    print("\n=== Создание страницы карточки пациента ===")

    templates_dir = Path("templates")
    templates_dir.mkdir(exist_ok=True)

    patient_card_template = """{% extends "base.html" %}
{% block title %}{{ patient.full_name }} - Карточка пациента{% endblock %}

{% block content %}
<div class="container-fluid">
    <div class="row">
        <div class="col-md-8">
            <!-- Основная информация -->
            <div class="card mb-4">
                <div class="card-header d-flex justify-content-between align-items-center">
                    <h5 class="mb-0">{{ patient.full_name }}</h5>
                    <div>
                        <button class="btn btn-sm btn-outline-primary" onclick="editPatient()">
                            <i class="fas fa-edit"></i> Редактировать
                        </button>
                        <button class="btn btn-sm btn-outline-success" onclick="createAppointment()">
                            <i class="fas fa-calendar-plus"></i> Новая запись
                        </button>
                    </div>
                </div>
                <div class="card-body">
                    <div class="row">
                        <div class="col-md-6">
                            <p><strong>Телефон:</strong> {{ patient.phone or '—' }}</p>
                            <p><strong>Email:</strong> {{ patient.email or '—' }}</p>
                            <p><strong>Дата рождения:</strong> {{ patient.birthdate or '—' }}</p>
                        </div>
                        <div class="col-md-6">
                            <p><strong>Карта №:</strong> {{ patient.card_no or '—' }}</p>
                            <p><strong>Создан:</strong> {{ patient.created_at.strftime('%d.%m.%Y') if patient.created_at else '—' }}</p>
                        </div>
                    </div>

                    {% if patient.notes %}
                    <div class="mt-3">
                        <strong>Заметки:</strong>
                        <p class="text-muted">{{ patient.notes }}</p>
                    </div>
                    {% endif %}
                </div>
            </div>

            <!-- История записей -->
            <div class="card">
                <div class="card-header">
                    <h6 class="mb-0">История записей</h6>
                </div>
                <div class="card-body">
                    {% if appointments %}
                    <div class="table-responsive">
                        <table class="table table-sm">
                            <thead>
                                <tr>
                                    <th>Дата</th>
                                    <th>Время</th>
                                    <th>Врач</th>
                                    <th>Услуга</th>
                                    <th>Статус</th>
                                    <th>Стоимость</th>
                                </tr>
                            </thead>
                            <tbody>
                                {% for appt in appointments %}
                                <tr>
                                    <td>{{ appt.start.strftime('%d.%m.%Y') if appt.start else '—' }}</td>
                                    <td>{{ appt.start.strftime('%H:%M') if appt.start else '—' }}</td>
                                    <td>{{ appt.doctor_name or '—' }}</td>
                                    <td>{{ appt.service_name or '—' }}</td>
                                    <td>
                                        <span class="badge bg-{{ 'success' if appt.status_key == 'paid' else 'primary' if appt.status_key == 'confirmed' else 'secondary' }}">
                                            {{ appt.status_title or appt.status_key or 'Запланирована' }}
                                        </span>
                                    </td>
                                    <td>{{ appt.cost or '—' }}₽</td>
                                </tr>
                                {% endfor %}
                            </tbody>
                        </table>
                    </div>
                    {% else %}
                    <p class="text-muted">Записей пока нет</p>
                    {% endif %}
                </div>
            </div>
        </div>

        <div class="col-md-4">
            <!-- Финансовая информация -->
            <div class="card mb-4">
                <div class="card-header">
                    <h6 class="mb-0">Финансы</h6>
                </div>
                <div class="card-body">
                    <div class="row text-center">
                        <div class="col-6">
                            <div class="border-end">
                                <h4 class="text-success mb-0">{{ finance.total_paid or 0 }}₽</h4>
                                <small class="text-muted">Оплачено</small>
                            </div>
                        </div>
                        <div class="col-6">
                            <h4 class="text-danger mb-0">{{ finance.total_debt or 0 }}₽</h4>
                            <small class="text-muted">Долг</small>
                        </div>
                    </div>

                    {% if finance.total_debt > 0 %}
                    <div class="mt-3">
                        <button class="btn btn-success btn-sm w-100" onclick="processPayment()">
                            <i class="fas fa-credit-card"></i> Оплатить долг
                        </button>
                    </div>
                    {% endif %}
                </div>
            </div>

            <!-- Быстрые действия -->
            <div class="card">
                <div class="card-header">
                    <h6 class="mb-0">Быстрые действия</h6>
                </div>
                <div class="card-body">
                    <div class="d-grid gap-2">
                        <button class="btn btn-outline-primary btn-sm" onclick="callPatient()">
                            <i class="fas fa-phone"></i> Позвонить
                        </button>
                        <button class="btn btn-outline-info btn-sm" onclick="sendMessage()">
                            <i class="fas fa-sms"></i> SMS
                        </button>
                        <button class="btn btn-outline-success btn-sm" onclick="sendWhatsApp()">
                            <i class="fab fa-whatsapp"></i> WhatsApp
                        </button>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>

<script>
function editPatient() {
    window.location.href = '/patients/{{ patient._id }}/edit';
}

function createAppointment() {
    // Открываем календарь с предвыбранным пациентом
    window.location.href = '/calendar?patient_id={{ patient._id }}';
}

function processPayment() {
    // Переход к форме оплаты
    window.location.href = '/finance/add?patient_id={{ patient._id }}&type=income';
}

function callPatient() {
    {% if patient.phone %}
    window.location.href = 'tel:{{ patient.phone }}';
    {% else %}
    alert('Телефон не указан');
    {% endif %}
}

function sendMessage() {
    {% if patient.phone %}
    window.location.href = 'sms:{{ patient.phone }}';
    {% else %}
    alert('Телефон не указан');
    {% endif %}
}

function sendWhatsApp() {
    {% if patient.phone %}
    const phone = '{{ patient.phone }}'.replace(/\D/g, '');
    window.open(`https://wa.me/${phone}`, '_blank');
    {% else %}
    alert('Телефон не указан');
    {% endif %}
}
</script>
{% endblock %}"""

    # Сохраняем шаблон
    with open(templates_dir / "patient_card.html", "w", encoding="utf-8") as f:
        f.write(patient_card_template)

    print("✅ Шаблон карточки пациента создан")
    return True


def integrate_with_left_navigation():
    """Интегрируем с левым меню навигации"""
    print("\n=== Интеграция с левым меню ===")

    # Обновляем базовый шаблон для правильной работы ссылок
    base_template_path = Path("templates/base.html")
    if not base_template_path.exists():
        print("❌ templates/base.html не найден")
        return False

    with open(base_template_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Проверяем и исправляем ссылки в меню
    menu_links = [
        ('href="/patients"', "Пациенты"),
        ('href="/finance"', "Финансовый отчет"),
        ('href="/doctors"', "Врачи"),
        ('href="/services"', "Услуги"),
    ]

    for link, name in menu_links:
        if link in content:
            print(f"✅ Ссылка '{name}' найдена в меню")
        else:
            print(f"⚠️ Ссылка '{name}' не найдена в меню")

    # Добавляем активный класс для текущей страницы
    if "request.endpoint" not in content:
        # Добавляем JavaScript для выделения активного пункта меню
        active_menu_script = """
<script>
// Выделение активного пункта меню
document.addEventListener('DOMContentLoaded', function() {
    const currentPath = window.location.pathname;
    const menuLinks = document.querySelectorAll('.nav-link, .sidebar a');

    menuLinks.forEach(link => {
        const href = link.getAttribute('href');
        if (href && currentPath.startsWith(href) && href !== '/') {
            link.classList.add('active');
            link.style.background = 'rgba(255,255,255,0.1)';
        }
    });
});
</script>"""

        content = content.replace("</body>", active_menu_script + "\n</body>")
        print("✅ Скрипт активного меню добавлен")

    # Сохраняем изменения
    with open(base_template_path, "w", encoding="utf-8") as f:
        f.write(content)

    return True


def update_main_py_routes():
    """Обновляем маршруты в main.py для карточек пациентов"""
    print("\n=== Обновление маршрутов в main.py ===")

    with open("main.py", "r", encoding="utf-8") as f:
        content = f.read()

    # Проверяем наличие маршрута карточки пациента
    if "/patients/<id>" not in content:
        print("Добавляем маршрут карточки пациента...")

        # Ищем место для добавления (после других patient routes)
        patient_routes_pos = content.find("/patients")
        if patient_routes_pos != -1:
            # Ищем конец функции
            func_end = content.find("\n\n@app.route", patient_routes_pos)
            if func_end == -1:
                func_end = content.find("\n@app.route", patient_routes_pos + 100)

            patient_card_route = '''

@app.route("/patients/<id>")
@login_required
def patient_card_view(id):
    """Карточка пациента с полной информацией"""
    try:
        patient_oid = ObjectId(id)
    except:
        flash("Некорректный ID пациента", "danger")
        return redirect(url_for("patients_list"))

    # Получаем пациента
    patient = db.patients.find_one({"_id": patient_oid})
    if not patient:
        flash("Пациент не найден", "danger")
        return redirect(url_for("patients_list"))

    # Получаем историю записей
    appointments = []
    appts_cursor = db.appointments.find({"patient_id": patient_oid}).sort("start", -1).limit(50)

    # Получаем справочники
    doctors = {str(d["_id"]): d for d in db.doctors.find({}, {"full_name": 1})}
    services = {str(s["_id"]): s for s in db.services.find({}, {"name": 1, "price": 1})}

    for appt in appts_cursor:
        doctor = doctors.get(str(appt.get("doctor_id", "")), {})
        service = services.get(str(appt.get("service_id", "")), {})

        appointments.append({
            "start": appt.get("start"),
            "doctor_name": doctor.get("full_name", ""),
            "service_name": service.get("name", ""),
            "status_key": appt.get("status_key", ""),
            "status_title": appt.get("status_key", "").title(),
            "cost": service.get("price", 0)
        })

    # Финансовая информация
    finance = {"total_paid": 0, "total_debt": 0}
    try:
        # Считаем оплаты
        paid_sum = db.ledger.aggregate([
            {"$match": {"patient_id": patient_oid, "kind": "payment"}},
            {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
        ])
        paid_result = list(paid_sum)
        finance["total_paid"] = paid_result[0]["total"] if paid_result else 0

        # Считаем долги
        debt_sum = db.ledger.aggregate([
            {"$match": {"patient_id": patient_oid, "kind": "service_charge"}},
            {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
        ])
        debt_result = list(debt_sum)
        finance["total_debt"] = max(0, (debt_result[0]["total"] if debt_result else 0) - finance["total_paid"])
    except Exception as e:
        print(f"Finance calculation error: {e}")

    return render_template("patient_card.html",
                         patient=patient,
                         appointments=appointments,
                         finance=finance)'''

            content = content[:func_end] + patient_card_route + content[func_end:]

            # Сохраняем
            with open("main.py", "w", encoding="utf-8") as f:
                f.write(content)

            print("✅ Маршрут карточки пациента добавлен")
    else:
        print("✅ Маршрут карточки пациента уже существует")

    return True


def main():
    print("🔗 ИНТЕГРАЦИЯ КАРТОЧЕК ПАЦИЕНТОВ И НАВИГАЦИИ")
    print("=" * 60)

    tasks = [
        ("Интеграция с календарем", integrate_patient_creation_with_calendar),
        ("Создание карточки пациента", create_patient_card_page),
        ("Интеграция с меню", integrate_with_left_navigation),
        ("Обновление маршрутов", update_main_py_routes),
    ]

    completed = 0
    for task_name, task_func in tasks:
        print(f"\n--- {task_name} ---")
        try:
            if task_func():
                completed += 1
                print(f"✅ {task_name} завершена")
            else:
                print(f"❌ {task_name} не удалась")
        except Exception as e:
            print(f"❌ Ошибка в {task_name}: {e}")

    print("\n" + "=" * 60)
    print(f"Выполнено: {completed}/{len(tasks)} задач")

    if completed >= len(tasks) * 0.75:
        print("\n✅ ИНТЕГРАЦИЯ ЗАВЕРШЕНА!")
        print("\nТеперь доступно:")
        print("1. Создание пациента прямо из календаря")
        print("2. Карточка пациента: /patients/<id>")
        print("3. Переходы между календарем и карточками")
        print("4. Финансовая информация в карточке")
        print("\nДля тестирования:")
        print("- Перезапустите сервер: python main.py")
        print("- Откройте календарь, создайте запись")
        print("- Попробуйте создать нового пациента")
        print("- Кликните на запись - должна быть кнопка 'Карточка пациента'")
        print("- Перейдите в /patients для списка всех пациентов")
    else:
        print("\n❌ Требуются доработки")


if __name__ == "__main__":
    main()
