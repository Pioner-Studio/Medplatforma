#!/usr/bin/env python3
"""
Скрипт для поиска и исправления дублирующих маршрутов в main.py
"""

import os
import re


def find_duplicate_routes():
    """Поиск дублирующих маршрутов"""
    print("🔍 ПОИСК ДУБЛИРУЮЩИХ МАРШРУТОВ")
    print("=" * 40)

    main_py_path = "main.py"

    if not os.path.exists(main_py_path):
        print("❌ Файл main.py не найден!")
        return False

    # Читаем файл
    with open(main_py_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Ищем все маршруты
    route_pattern = r'@app\.route\([\'"]([^\'"]+)[\'"].*?\)\s*\ndef\s+(\w+)'
    routes = re.findall(route_pattern, content, re.MULTILINE)

    print("📋 Найденные маршруты:")
    route_count = {}
    function_count = {}

    for route_path, function_name in routes:
        print(f"   {route_path} → {function_name}()")

        # Считаем дубликаты маршрутов
        if route_path in route_count:
            route_count[route_path] += 1
        else:
            route_count[route_path] = 1

        # Считаем дубликаты функций
        if function_name in function_count:
            function_count[function_name] += 1
        else:
            function_count[function_name] = 1

    # Проверяем дубликаты
    duplicated_routes = {k: v for k, v in route_count.items() if v > 1}
    duplicated_functions = {k: v for k, v in function_count.items() if v > 1}

    print(f"\n❌ Дублированные маршруты:")
    for route, count in duplicated_routes.items():
        print(f"   {route} (найдено {count} раз)")

    print(f"\n❌ Дублированные функции:")
    for func, count in duplicated_functions.items():
        print(f"   {func}() (найдено {count} раз)")

    return duplicated_routes, duplicated_functions


def remove_duplicate_routes():
    """Удаление дублирующих маршрутов"""
    print(f"\n🔧 УДАЛЕНИЕ ДУБЛИРУЮЩИХ МАРШРУТОВ")
    print("=" * 40)

    main_py_path = "main.py"

    # Читаем файл
    with open(main_py_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # Создаем резервную копию
    backup_path = main_py_path + ".backup_duplicates"
    with open(backup_path, "w", encoding="utf-8") as f:
        f.writelines(lines)
    print(f"💾 Создана резервная копия: {backup_path}")

    content = "".join(lines)

    # Находим и удаляем дублированные блоки маршрутов
    # Ищем блоки, добавленные нашими скриптами

    # Удаляем блок "ОСНОВНЫЕ СТРАНИЦЫ МЕДПЛАТФОРМЫ"
    pattern1 = r"# === ОСНОВНЫЕ СТРАНИЦЫ МЕДПЛАТФОРМЫ ===.*?# === КОНЕЦ ОСНОВНЫХ СТРАНИЦ ==="
    match1 = re.search(pattern1, content, re.DOTALL)
    if match1:
        content = content.replace(match1.group(0), "")
        print("✅ Удален блок 'ОСНОВНЫЕ СТРАНИЦЫ МЕДПЛАТФОРМЫ'")

    # Удаляем блок "НЕДОСТАЮЩИЕ МАРШРУТЫ"
    pattern2 = r"# === НЕДОСТАЮЩИЕ МАРШРУТЫ ===.*?# === КОНЕЦ НЕДОСТАЮЩИХ МАРШРУТОВ ==="
    match2 = re.search(pattern2, content, re.DOTALL)
    if match2:
        content = content.replace(match2.group(0), "")
        print("✅ Удален блок 'НЕДОСТАЮЩИЕ МАРШРУТЫ'")

    # Удаляем отдельные дублированные маршруты
    duplicated_routes = [
        r"@app\.route\(\'/doctors\'\)\s*\ndef doctors\(\):.*?(?=@app\.route|if __name__|$)",
        r"@app\.route\(\'/patients\'\)\s*\ndef patients\(\):.*?(?=@app\.route|if __name__|$)",
        r"@app\.route\(\'/services\'\)\s*\ndef services\(\):.*?(?=@app\.route|if __name__|$)",
        r"@app\.route\(\'/rooms\'\)\s*\ndef rooms\(\):.*?(?=@app\.route|if __name__|$)",
        r"@app\.route\(\'/reports\'\)\s*\ndef reports\(\):.*?(?=@app\.route|if __name__|$)",
    ]

    removed_count = 0
    for pattern in duplicated_routes:
        matches = list(re.finditer(pattern, content, re.DOTALL))
        if len(matches) > 1:
            # Удаляем все дубликаты, кроме первого
            for match in reversed(matches[1:]):
                content = content[: match.start()] + content[match.end() :]
                removed_count += 1

    if removed_count > 0:
        print(f"✅ Удалено {removed_count} дублирующих маршрутов")

    # Сохраняем очищенный файл
    with open(main_py_path, "w", encoding="utf-8") as f:
        f.write(content)

    print("✅ Файл очищен от дубликатов")
    return True


def check_syntax_after_cleanup():
    """Проверка синтаксиса после очистки"""
    print(f"\n🧪 ПРОВЕРКА СИНТАКСИСА")
    print("=" * 30)

    try:
        import ast

        with open("main.py", "r", encoding="utf-8") as f:
            content = f.read()

        # Пытаемся скомпилировать
        ast.parse(content)
        print("✅ Синтаксис корректен!")
        return True

    except SyntaxError as e:
        print(f"❌ Синтаксическая ошибка:")
        print(f"   Строка {e.lineno}: {e.text.strip() if e.text else 'неизвестно'}")
        print(f"   Ошибка: {e.msg}")
        return False
    except Exception as e:
        print(f"❌ Ошибка при проверке: {e}")
        return False


def add_missing_routes_safely():
    """Безопасное добавление недостающих маршрутов"""
    print(f"\n🔧 БЕЗОПАСНОЕ ДОБАВЛЕНИЕ МАРШРУТОВ")
    print("=" * 40)

    main_py_path = "main.py"

    # Читаем файл
    with open(main_py_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Проверяем, какие маршруты реально отсутствуют
    missing_routes = []

    if not re.search(r"@app\.route\(\'/patients\'\)", content):
        missing_routes.append("patients")
    if not re.search(r"@app\.route\(\'/services\'\)", content):
        missing_routes.append("services")
    if not re.search(r"@app\.route\(\'/doctors\'\)", content):
        missing_routes.append("doctors")
    if not re.search(r"@app\.route\(\'/rooms\'\)", content):
        missing_routes.append("rooms")
    if not re.search(r"@app\.route\(\'/reports\'\)", content):
        missing_routes.append("reports")

    print(f"📋 Отсутствующие маршруты: {missing_routes}")

    if not missing_routes:
        print("✅ Все маршруты уже существуют")
        return True

    # Добавляем только отсутствующие маршруты
    routes_code = ""

    if "patients" in missing_routes:
        routes_code += '''
@app.route('/patients')
def patients():
    """Список всех пациентов"""
    try:
        patients_list = list(db.patients.find().sort('name', 1))
        for patient in patients_list:
            patient['appointments_count'] = db.appointments.count_documents({
                'patient_id': str(patient['_id'])
            })
        return render_template('patients.html', patients=patients_list)
    except Exception as e:
        flash(f'Ошибка при загрузке пациентов: {str(e)}', 'error')
        return render_template('patients.html', patients=[])
'''

    if "services" in missing_routes:
        routes_code += '''
@app.route('/services')
def services():
    """Список всех услуг"""
    try:
        services_list = list(db.services.find({'active': True}).sort('name', 1))
        return render_template('services.html', services=services_list)
    except Exception as e:
        flash(f'Ошибка при загрузке услуг: {str(e)}', 'error')
        return render_template('services.html', services=[])
'''

    if "doctors" in missing_routes:
        routes_code += '''
@app.route('/doctors')
def doctors():
    """Список всех врачей"""
    try:
        doctors_list = list(db.doctors.find({'active': True}).sort('name', 1))
        for doctor in doctors_list:
            doctor['appointments_count'] = db.appointments.count_documents({
                'doctor_id': str(doctor['_id'])
            })
        return render_template('doctors.html', doctors=doctors_list)
    except Exception as e:
        flash(f'Ошибка при загрузке врачей: {str(e)}', 'error')
        return render_template('doctors.html', doctors=[])
'''

    if "rooms" in missing_routes:
        routes_code += '''
@app.route('/rooms')
def rooms():
    """Управление кабинетами"""
    try:
        rooms_list = list(db.rooms.find().sort('number', 1))
        return render_template('rooms.html', rooms=rooms_list)
    except Exception as e:
        flash(f'Ошибка при загрузке кабинетов: {str(e)}', 'error')
        return render_template('rooms.html', rooms=[])
'''

    if "reports" in missing_routes:
        routes_code += '''
@app.route('/reports')
def reports():
    """Страница отчетов"""
    try:
        today = datetime.now()
        month_start = today.replace(day=1).strftime('%Y-%m-%d')

        total_appointments = db.appointments.count_documents({
            'date': {'$gte': month_start}
        })

        stats = {
            'total_appointments': total_appointments,
            'period': month_start
        }

        return render_template('reports.html', stats=stats)
    except Exception as e:
        flash(f'Ошибка при формировании отчетов: {str(e)}', 'error')
        return render_template('reports.html', stats={})
'''

    if routes_code:
        # Найдем место для вставки
        pattern = r'(if __name__ == ["\']__main__["\']:.*)'
        match = re.search(pattern, content, re.DOTALL)

        if match:
            content = content.replace(match.group(1), f"\n{routes_code}\n\n{match.group(1)}")
        else:
            content += f"\n{routes_code}\n"

        # Сохраняем файл
        with open(main_py_path, "w", encoding="utf-8") as f:
            f.write(content)

        print(f"✅ Добавлены маршруты: {', '.join(missing_routes)}")

    return True


def main():
    """Главная функция"""
    print("🔧 ИСПРАВЛЕНИЕ ДУБЛИРУЮЩИХ МАРШРУТОВ")
    print("=" * 50)

    # 1. Находим дубликаты
    duplicated_routes, duplicated_functions = find_duplicate_routes()

    if not duplicated_routes and not duplicated_functions:
        print("\n✅ Дубликаты не найдены!")
        return

    # 2. Удаляем дубликаты
    if not remove_duplicate_routes():
        print("❌ Ошибка при удалении дубликатов")
        return

    # 3. Проверяем синтаксис
    if not check_syntax_after_cleanup():
        print("❌ Проблемы с синтаксисом после очистки")
        return

    # 4. Добавляем недостающие маршруты безопасно
    if not add_missing_routes_safely():
        print("❌ Ошибка при добавлении маршрутов")
        return

    # 5. Финальная проверка
    if check_syntax_after_cleanup():
        print("\n🎉 ИСПРАВЛЕНИЕ ЗАВЕРШЕНО!")
        print("\n🚀 Теперь можно запустить сервер:")
        print("python main.py")
        print("\nили")
        print("flask --app main run --no-reload")
    else:
        print("\n❌ Требуется дополнительная проверка")


if __name__ == "__main__":
    main()
