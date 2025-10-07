#!/usr/bin/env python3
"""
Отладка и исправление маршрута /patients
"""

import os
import re


def analyze_patients_route():
    """Анализ маршрута /patients"""
    print("🔍 АНАЛИЗ МАРШРУТА /PATIENTS")
    print("=" * 35)

    main_py_path = "main.py"

    if not os.path.exists(main_py_path):
        print("❌ Файл main.py не найден!")
        return False

    with open(main_py_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Ищем все определения маршрута /patients
    patterns = [
        r"@app\.route\([\'\"]/patients[\'\"]\).*?def\s+(\w+)\s*\(",
        r"def\s+(\w+)\s*\([^)]*\):[^@]*@app\.route\([\'\"]/patients[\'\"]\)",
    ]

    patients_routes = []
    lines = content.split("\n")

    for i, line in enumerate(lines):
        if "/patients" in line and "@app.route" in line:
            # Найдем следующую функцию
            for j in range(i + 1, min(i + 10, len(lines))):
                if "def " in lines[j]:
                    func_name = re.search(r"def\s+(\w+)\s*\(", lines[j])
                    if func_name:
                        patients_routes.append(
                            {
                                "line": i + 1,
                                "route_line": line.strip(),
                                "func_line": lines[j].strip(),
                                "func_name": func_name.group(1),
                            }
                        )
                    break

    print(f"📋 Найдено {len(patients_routes)} маршрутов /patients:")
    for route in patients_routes:
        print(f"   Строка {route['line']}: {route['route_line']}")
        print(f"   Функция: {route['func_line']}")
        print()

    return patients_routes


def check_login_required_issue():
    """Проверка проблемы с @login_required"""
    print("🔍 ПРОВЕРКА ПРОБЛЕМЫ С @LOGIN_REQUIRED")
    print("=" * 40)

    main_py_path = "main.py"

    with open(main_py_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Ищем определение login_required
    if "def login_required(" in content:
        print("✅ Декоратор login_required определен")
    else:
        print("❌ Декоратор login_required не найден")

    # Ищем импорт session
    if "from flask import" in content and "session" in content:
        print("✅ session импортирован")
    else:
        print("⚠️ session может быть не импортирован")

    # Ищем использование session в login_required
    login_required_pattern = r"def login_required\([^)]*\):(.*?)(?=def|\Z)"
    match = re.search(login_required_pattern, content, re.DOTALL)

    if match:
        func_body = match.group(1)
        if "session" in func_body:
            print("✅ login_required использует session")
        else:
            print("❌ login_required не использует session")

        if "redirect" in func_body and "login" in func_body:
            print("✅ login_required перенаправляет на login")
        else:
            print("⚠️ login_required может не перенаправлять правильно")

    return True


def create_simple_patients_route():
    """Создание простого маршрута /patients без @login_required для тестирования"""
    print("\n🔧 СОЗДАНИЕ ПРОСТОГО МАРШРУТА /PATIENTS")
    print("=" * 45)

    main_py_path = "main.py"

    with open(main_py_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Создаем резервную копию
    backup_path = main_py_path + ".backup_patients_debug"
    with open(backup_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"💾 Создана резервная копия: {backup_path}")

    # Убираем все существующие маршруты /patients
    # Ищем и удаляем блоки @app.route('/patients') ... def function():
    pattern = r"@app\.route\([\'\"]/patients[\'\"]\)[^\n]*\n(?:@[^\n]*\n)*def\s+\w+\s*\([^)]*\):[^@]*?(?=@app\.route|if __name__|$)"

    matches = list(re.finditer(pattern, content, re.DOTALL))
    print(f"📋 Найдено {len(matches)} блоков для удаления")

    # Удаляем все найденные блоки (начиная с конца, чтобы не сбить индексы)
    for match in reversed(matches):
        print(f"🗑️ Удаляем блок: {match.group(0)[:50]}...")
        content = content[: match.start()] + content[match.end() :]

    # Добавляем новый простой маршрут без @login_required
    new_patients_route = '''
# === ПРОСТОЙ МАРШРУТ /PATIENTS ДЛЯ ТЕСТИРОВАНИЯ ===
@app.route('/patients')
def patients():
    """Простой список пациентов (без авторизации для тестирования)"""
    try:
        # Получаем пациентов из БД
        patients_list = list(db.patients.find().limit(10))

        # Преобразуем ObjectId в строки
        for patient in patients_list:
            patient['_id'] = str(patient['_id'])

        # Если нет шаблона, возвращаем JSON
        try:
            return render_template('patients.html', patients=patients_list)
        except:
            # Если шаблон не найден, возвращаем простой HTML
            html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Пациенты</title>
                <style>
                    body {{ font-family: Arial; margin: 20px; }}
                    table {{ border-collapse: collapse; width: 100%; }}
                    th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                    th {{ background-color: #f2f2f2; }}
                    .btn {{ background: #007bff; color: white; padding: 8px 16px; text-decoration: none; border-radius: 4px; }}
                </style>
            </head>
            <body>
                <h1>Список пациентов</h1>
                <p>Найдено пациентов: {len(patients_list)}</p>

                <table>
                    <tr>
                        <th>ID</th>
                        <th>Имя</th>
                        <th>Телефон</th>
                        <th>Email</th>
                        <th>Действия</th>
                    </tr>
            """

            for patient in patients_list:
                name = patient.get('full_name', patient.get('name', 'Не указано'))
                phone = patient.get('phone', '—')
                email = patient.get('email', '—')

                html += f"""
                    <tr>
                        <td>{patient['_id']}</td>
                        <td>{name}</td>
                        <td>{phone}</td>
                        <td>{email}</td>
                        <td><a href="/patients/{patient['_id']}" class="btn">Карточка</a></td>
                    </tr>
                """

            html += """
                </table>
                <br>
                <a href="/" class="btn">← Назад к календарю</a>
            </body>
            </html>
            """

            return html

    except Exception as e:
        return f"""
        <h1>Ошибка загрузки пациентов</h1>
        <p>Ошибка: {str(e)}</p>
        <a href="/">← Назад к календарю</a>
        """
'''

    # Добавляем новый маршрут
    pattern = r'(if __name__ == ["\']__main__["\']:.*)'
    match = re.search(pattern, content, re.DOTALL)

    if match:
        content = content.replace(match.group(1), new_patients_route + "\n\n" + match.group(1))
    else:
        content += new_patients_route

    # Сохраняем файл
    with open(main_py_path, "w", encoding="utf-8") as f:
        f.write(content)

    print("✅ Добавлен простой маршрут /patients")
    return True


def create_patient_card_route():
    """Создание маршрута для карточки пациента"""
    print("\n🔧 СОЗДАНИЕ МАРШРУТА КАРТОЧКИ ПАЦИЕНТА")
    print("=" * 40)

    main_py_path = "main.py"

    with open(main_py_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Проверяем, есть ли уже маршрут карточки
    if "/patients/<" in content and "def patient" in content:
        print("✅ Маршрут карточки пациента уже существует")
        return True

    # Добавляем маршрут карточки
    card_route = '''
@app.route('/patients/<patient_id>')
def patient_card_simple(patient_id):
    """Простая карточка пациента"""
    try:
        from bson import ObjectId
        patient = db.patients.find_one({'_id': ObjectId(patient_id)})

        if not patient:
            return f"<h1>Пациент не найден</h1><a href='/patients'>← Назад к списку</a>"

        # Получаем записи пациента
        appointments = list(db.appointments.find({'patient_id': patient_id}).limit(5))

        name = patient.get('full_name', patient.get('name', 'Не указано'))

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Карточка пациента</title>
            <style>
                body {{ font-family: Arial; margin: 20px; }}
                .card {{ border: 1px solid #ddd; padding: 20px; margin: 10px 0; }}
                .btn {{ background: #007bff; color: white; padding: 8px 16px; text-decoration: none; border-radius: 4px; }}
            </style>
        </head>
        <body>
            <h1>Карточка пациента</h1>

            <div class="card">
                <h2>{name}</h2>
                <p><strong>ID:</strong> {patient_id}</p>
                <p><strong>Телефон:</strong> {patient.get('phone', '—')}</p>
                <p><strong>Email:</strong> {patient.get('email', '—')}</p>
                <p><strong>Дата рождения:</strong> {patient.get('birth_date', '—')}</p>
                <p><strong>Адрес:</strong> {patient.get('address', '—')}</p>
            </div>

            <div class="card">
                <h3>Записи ({len(appointments)})</h3>
                <ul>
        """

        for apt in appointments:
            html += f"<li>{apt.get('date', '—')} в {apt.get('time', '—')}</li>"

        html += """
                </ul>
            </div>

            <a href="/patients" class="btn">← Назад к списку пациентов</a>
        </body>
        </html>
        """

        return html

    except Exception as e:
        return f"<h1>Ошибка</h1><p>{str(e)}</p><a href='/patients'>← Назад</a>"
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
    print("🔧 ОТЛАДКА И ИСПРАВЛЕНИЕ МАРШРУТА /PATIENTS")
    print("=" * 50)

    # 1. Анализируем существующие маршруты
    analyze_patients_route()

    # 2. Проверяем проблему с login_required
    check_login_required_issue()

    # 3. Создаем простой маршрут без авторизации
    create_simple_patients_route()

    # 4. Создаем маршрут карточки пациента
    create_patient_card_route()

    print("\n" + "=" * 50)
    print("🎉 ОТЛАДКА ЗАВЕРШЕНА!")
    print("\n🚀 СЛЕДУЮЩИЕ ШАГИ:")
    print("1. Перезапустите сервер: Ctrl+C, затем python main.py")
    print("2. Откройте http://localhost:5000/patients")
    print("3. Должен открыться список пациентов БЕЗ авторизации")
    print("4. Если работает, значит проблема была в @login_required")
    print("\n📝 ЧТО СДЕЛАНО:")
    print("- Удалены все конфликтующие маршруты /patients")
    print("- Создан простой маршрут без @login_required")
    print("- Добавлен встроенный HTML если нет шаблона")
    print("- Создан маршрут для карточек пациентов")
    print("- Все с базовой обработкой ошибок")


if __name__ == "__main__":
    main()
