#!/usr/bin/env python3
"""
Прямая проверка и исправление левого меню
"""

import os
import re


def check_current_menu():
    """Проверка текущего состояния меню"""
    print("🔍 ПРОВЕРКА ТЕКУЩЕГО МЕНЮ")
    print("=" * 30)

    base_html_path = "templates/base.html"

    if not os.path.exists(base_html_path):
        print("❌ Файл base.html не найден!")
        return False

    with open(base_html_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Ищем ссылки в меню
    print("📋 Найденные ссылки в меню:")

    # Ищем все ссылки href в левом меню
    href_pattern = r'href="([^"]+)"[^>]*>\s*<i[^>]*></i>\s*([^<]+)'
    matches = re.findall(href_pattern, content)

    for href, text in matches:
        print(f"   {text.strip()} → {href}")

    return True


def fix_menu_directly():
    """Прямое исправление меню"""
    print(f"\n🔧 ПРЯМОЕ ИСПРАВЛЕНИЕ МЕНЮ")
    print("=" * 35)

    base_html_path = "templates/base.html"

    with open(base_html_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Создаем резервную копию
    backup_path = base_html_path + ".backup_direct"
    with open(backup_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"💾 Создана резервная копия: {backup_path}")

    # Находим и заменяем конкретные проблемные ссылки
    replacements = [
        # Пациенты - должны вести на /patients
        (r'href="/ztl"([^>]*>\s*<i[^>]*></i>\s*Пациенты)', r'href="/patients"\1'),
        # Финансы - должны вести на /finance_report
        (r'href="[^"]*"([^>]*>\s*<i[^>]*></i>\s*Финансовый\s*отчет)', r'href="/finance_report"\1'),
        # Услуги - если есть неправильная ссылка
        (r'href="/add_service"([^>]*>\s*<i[^>]*></i>\s*Услуги)', r'href="/services"\1'),
    ]

    changes_made = 0
    for pattern, replacement in replacements:
        old_content = content
        content = re.sub(pattern, replacement, content, flags=re.IGNORECASE)
        if content != old_content:
            changes_made += 1
            print(f"✅ Исправлена ссылка: {pattern[:30]}...")

    # Если не нашли паттерны, делаем более агрессивную замену
    if changes_made == 0:
        print("⚠️ Паттерны не найдены, делаем прямую замену...")

        # Прямая замена всего левого меню
        new_menu = """                <ul class="nav flex-column">
                    <li class="nav-item">
                        <a class="nav-link" href="/">
                            <i class="fas fa-calendar-alt"></i> Расписание
                        </a>
                    </li>

                    <li class="nav-item">
                        <a class="nav-link" href="/patients">
                            <i class="fas fa-users"></i> Пациенты
                        </a>
                    </li>

                    <li class="nav-item">
                        <a class="nav-link" href="/doctors">
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
                        <a class="nav-link" href="/services">
                            <i class="fas fa-plus"></i> Услуги
                        </a>
                    </li>

                    <li class="nav-item">
                        <a class="nav-link" href="/ztl">
                            <i class="fas fa-upload"></i> ЗТЛ
                        </a>
                    </li>

                    <li class="nav-item">
                        <a class="nav-link" href="/partners">
                            <i class="fas fa-handshake"></i> Партнерская программа
                        </a>
                    </li>

                    <li class="nav-item">
                        <a class="nav-link" href="/finance_report">
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
                </ul>"""

        # Ищем существующий <ul class="nav flex-column"> и заменяем его
        ul_pattern = r'<ul class="nav flex-column">.*?</ul>'
        if re.search(ul_pattern, content, re.DOTALL):
            content = re.sub(ul_pattern, new_menu, content, flags=re.DOTALL)
            changes_made += 1
            print("✅ Заменено все меню целиком")
        else:
            print("❌ Не удалось найти меню для замены")

    # Сохраняем обновленный файл
    with open(base_html_path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"✅ Сделано изменений: {changes_made}")
    return changes_made > 0


def check_routes_exist():
    """Проверка существования маршрутов"""
    print(f"\n🔍 ПРОВЕРКА МАРШРУТОВ")
    print("=" * 25)

    main_py_path = "main.py"

    with open(main_py_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Проверяем ключевые маршруты
    routes_to_check = [
        ("/patients", "patients"),
        ("/finance_report", "finance_report"),
        ("/doctors", "doctors"),
        ("/services", "services"),
    ]

    print("📋 Статус маршрутов:")
    missing_routes = []

    for route, func_name in routes_to_check:
        route_exists = f"@app.route('{route}')" in content or f'@app.route("{route}")' in content
        func_exists = f"def {func_name}(" in content

        status = "✅" if route_exists and func_exists else "❌"
        print(f"   {status} {route} → {func_name}()")

        if not (route_exists and func_exists):
            missing_routes.append((route, func_name))

    return missing_routes


def add_missing_routes_quick():
    """Быстрое добавление недостающих маршрутов"""
    print(f"\n🔧 ДОБАВЛЕНИЕ НЕДОСТАЮЩИХ МАРШРУТОВ")
    print("=" * 40)

    missing_routes = check_routes_exist()

    if not missing_routes:
        print("✅ Все маршруты существуют")
        return True

    main_py_path = "main.py"

    with open(main_py_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Добавляем недостающие маршруты
    routes_code = ""

    for route, func_name in missing_routes:
        if route == "/patients" and func_name == "patients":
            routes_code += '''
@app.route('/patients')
@login_required
def patients():
    """Список всех пациентов"""
    try:
        patients_list = list(db.patients.find().sort('full_name', 1))
        for patient in patients_list:
            patient['_id'] = str(patient['_id'])
            patient['appointments_count'] = db.appointments.count_documents({
                'patient_id': patient['_id']
            })
        return render_template('patients.html', patients=patients_list)
    except Exception as e:
        flash(f'Ошибка при загрузке пациентов: {str(e)}', 'error')
        return render_template('patients.html', patients=[])
'''
        elif route == "/services" and func_name == "services":
            routes_code += '''
@app.route('/services')
@login_required
def services():
    """Список всех услуг"""
    try:
        services_list = list(db.services.find({'is_active': True}).sort('name', 1))
        return render_template('services.html', services=services_list)
    except Exception as e:
        flash(f'Ошибка при загрузке услуг: {str(e)}', 'error')
        return render_template('services.html', services=[])
'''

    if routes_code:
        # Добавляем маршруты
        pattern = r'(if __name__ == ["\']__main__["\']:.*)'
        match = re.search(pattern, content, re.DOTALL)

        if match:
            content = content.replace(match.group(1), routes_code + "\n\n" + match.group(1))
        else:
            content += routes_code

        # Сохраняем файл
        with open(main_py_path, "w", encoding="utf-8") as f:
            f.write(content)

        print(f"✅ Добавлены маршруты: {[route for route, _ in missing_routes]}")

    return True


def main():
    """Главная функция"""
    print("🔧 ПРЯМОЕ ИСПРАВЛЕНИЕ ПРОБЛЕМ НАВИГАЦИИ")
    print("=" * 45)

    # 1. Проверяем текущее состояние меню
    check_current_menu()

    # 2. Исправляем меню
    if fix_menu_directly():
        print("✅ Меню исправлено")
    else:
        print("⚠️ Не удалось исправить меню")

    # 3. Добавляем недостающие маршруты
    add_missing_routes_quick()

    print(f"\n{'='*45}")
    print("🎉 ИСПРАВЛЕНИЯ ЗАВЕРШЕНЫ!")
    print("\n🚀 СЛЕДУЮЩИЕ ШАГИ:")
    print("1. Перезапустите сервер: Ctrl+C, затем python main.py")
    print("2. Войдите в систему")
    print("3. Проверьте левое меню:")
    print("   - 'Пациенты' → должно открывать /patients")
    print("   - 'Финансовый отчет' → должно открывать /finance_report")
    print("   - 'Врачи' → должно открывать /doctors")
    print("\n📝 ЧТО ИСПРАВЛЕНО:")
    print("- Прямое обновление ссылок в левом меню")
    print("- Добавление недостающих маршрутов")
    print("- Исправление навигации к пациентам и финансам")


if __name__ == "__main__":
    main()
