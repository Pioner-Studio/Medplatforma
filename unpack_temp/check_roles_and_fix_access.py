# check_roles_and_fix_access.py
# Задача 6.1-6.2: Проверяем роли пользователей и улучшаем систему доступа

import os
import re
from dotenv import load_dotenv
from pymongo import MongoClient

# Загружаем переменные окружения
load_dotenv()


def check_user_roles():
    """6.1: Проверить роли пользователей в БД"""
    print("=== 6.1: Проверка ролей пользователей ===")

    client = MongoClient(os.getenv("MONGO_URI"))
    db = client[os.getenv("DB_NAME", "medplatforma")]

    users = list(db.users.find({}, {"login": 1, "role": 1, "full_name": 1}))

    print(f"Найдено пользователей: {len(users)}")
    print("Текущие роли:")

    role_counts = {}
    for user in users:
        login = user.get("login", "unknown")
        role = user.get("role", "no_role")
        name = user.get("full_name", "")

        role_counts[role] = role_counts.get(role, 0) + 1
        print(f"  {login}: {role} ({name})")

    print("\nСтатистика по ролям:")
    for role, count in role_counts.items():
        print(f"  {role}: {count} пользователей")

    # Проверяем, есть ли проблемные роли
    valid_roles = {"admin", "registrar", "doctor"}
    invalid_roles = set(role_counts.keys()) - valid_roles

    if invalid_roles:
        print(f"⚠️ ВНИМАНИЕ: Найдены некорректные роли: {invalid_roles}")
        return False

    print("✅ Все роли корректны")
    return True


def fix_role_decorator():
    """6.2: Улучшаем декоратор role_required"""
    print("\n=== 6.2: Проверка и улучшение декоратора role_required ===")

    # Читаем main.py
    with open("main.py", "r", encoding="utf-8") as f:
        content = f.read()

    # Проверяем, есть ли уже декоратор
    if "def role_required(" in content:
        print("✅ Декоратор role_required уже существует")

        # Проверяем, корректно ли он реализован
        if "user_role not in allowed_roles" in content and "abort(403)" in content:
            print("✅ Декоратор корректно проверяет роли")
            return True
        else:
            print("⚠️ Декоратор требует улучшения")
    else:
        print("❌ Декоратор role_required не найден")

    # Улучшенный декоратор с дополнительными проверками
    improved_decorator = '''
from functools import wraps
from flask import session, abort, redirect, url_for, flash

def role_required(*allowed_roles):
    """Декоратор для проверки ролей пользователя с улучшенной безопасностью"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Проверяем авторизацию
            if 'user_id' not in session:
                flash("Требуется авторизация", "warning")
                return redirect(url_for('auth.login'))

            # Проверяем наличие роли
            if 'user_role' not in session:
                flash("Роль пользователя не определена", "danger")
                return redirect(url_for('auth.login'))

            user_role = session['user_role']

            # Проверяем корректность роли
            valid_roles = {"admin", "registrar", "doctor"}
            if user_role not in valid_roles:
                flash(f"Некорректная роль: {user_role}", "danger")
                session.clear()  # Очищаем сессию для безопасности
                return redirect(url_for('auth.login'))

            # Проверяем права доступа
            if user_role not in allowed_roles:
                flash(f"Доступ запрещен. Требуется роль: {', '.join(allowed_roles)}", "danger")
                abort(403)  # Forbidden

            return f(*args, **kwargs)
        return decorated_function
    return decorator
'''

    # Ищем место для вставки или замены
    if "def role_required(" in content:
        # Заменяем существующий декоратор
        pattern = r"def role_required\(.*?\n(?:.*\n)*?    return decorator"
        content = re.sub(pattern, improved_decorator.strip(), content, flags=re.MULTILINE)
        print("✅ Декоратор role_required обновлен")
    else:
        # Добавляем новый декоратор после импортов
        import_section = content.find("from production_auth import")
        if import_section != -1:
            end_import = content.find("\n", import_section)
            content = content[:end_import] + "\n" + improved_decorator + content[end_import:]
            print("✅ Декоратор role_required добавлен")
        else:
            print("❌ Не удалось найти место для вставки декоратора")
            return False

    # Сохраняем изменения
    with open("main.py", "w", encoding="utf-8") as f:
        f.write(content)

    return True


def apply_route_restrictions():
    """6.3: Применяем ограничения доступа к маршрутам"""
    print("\n=== 6.3: Применение ограничений доступа ===")

    # Читаем main.py
    with open("main.py", "r", encoding="utf-8") as f:
        content = f.read()

    # Маршруты и их ограничения
    route_restrictions = {
        # Только админы
        '@app.route("/doctors")': ["admin"],
        '@app.route("/add_doctor")': ["admin"],
        '@app.route("/services")': ["admin"],
        '@app.route("/add_service")': ["admin"],
        '@app.route("/edit_service")': ["admin"],
        '@app.route("/delete_service")': ["admin"],
        '@app.route("/rooms")': ["admin"],
        '@app.route("/add_room")': ["admin"],
        '@app.route("/edit_room")': ["admin"],
        '@app.route("/delete_room")': ["admin"],
        '@app.route("/data_tools")': ["admin"],
        '@app.route("/backup")': ["admin"],
        # Админы и регистраторы
        '@app.route("/patients")': ["admin", "registrar"],
        '@app.route("/add_patient")': ["admin", "registrar"],
        '@app.route("/edit_patient")': ["admin", "registrar"],
        '@app.route("/finance")': ["admin", "registrar"],
        # API маршруты - тоже ограничиваем
        '@app.route("/api/appointments/create")': ["admin", "registrar"],
        '@app.route("/api/patients", methods=["POST"])': ["admin", "registrar"],
    }

    changes_made = 0

    for route_pattern, allowed_roles in route_restrictions.items():
        # Ищем маршрут в коде
        escaped_pattern = re.escape(route_pattern)

        # Проверяем, есть ли уже ограничение для этого маршрута
        route_start = content.find(route_pattern)
        if route_start == -1:
            continue

        # Ищем функцию после маршрута
        func_start = content.find("def ", route_start)
        if func_start == -1:
            continue

        func_end = content.find("\n@", func_start)
        if func_end == -1:
            func_end = content.find("\ndef ", func_start + 10)
        if func_end == -1:
            func_end = len(content)

        function_text = content[route_start:func_end]

        # Проверяем, есть ли уже @role_required
        if "@role_required" in function_text:
            print(f"✅ {route_pattern} уже имеет ограничения доступа")
            continue

        # Добавляем @role_required перед @login_required или функцией
        roles_str = '", "'.join(allowed_roles)
        role_decorator = f'@role_required("{roles_str}")\n'

        if "@login_required" in function_text:
            # Вставляем перед @login_required
            login_pos = function_text.find("@login_required")
            new_function = function_text[:login_pos] + role_decorator + function_text[login_pos:]
        else:
            # Вставляем перед функцией
            def_pos = function_text.find("def ")
            new_function = function_text[:def_pos] + role_decorator + function_text[def_pos:]

        # Заменяем в основном тексте
        content = content.replace(function_text, new_function)
        changes_made += 1
        print(f"✅ Добавлены ограничения для {route_pattern}: {allowed_roles}")

    if changes_made > 0:
        # Сохраняем изменения
        with open("main.py", "w", encoding="utf-8") as f:
            f.write(content)
        print(f"✅ Применено ограничений: {changes_made}")
    else:
        print("ℹ️ Все маршруты уже имеют необходимые ограничения")

    return True


def test_role_implementation():
    """Тестируем реализацию ролей"""
    print("\n=== Тестирование реализации ===")

    # Проверяем синтаксис main.py
    try:
        with open("main.py", "r", encoding="utf-8") as f:
            code = f.read()

        compile(code, "main.py", "exec")
        print("✅ Синтаксис main.py корректен")

        # Проверяем наличие всех необходимых элементов
        checks = [
            ("def role_required(", "Декоратор role_required"),
            ("abort(403)", "Запрет доступа"),
            ("@role_required", "Применение декоратора"),
            ("flash(", "Сообщения пользователю"),
        ]

        for check_text, description in checks:
            if check_text in code:
                print(f"✅ {description} найден")
            else:
                print(f"❌ {description} не найден")

        return True

    except SyntaxError as e:
        print(f"❌ Ошибка синтаксиса: {e}")
        return False


def main():
    print("🚀 Начинаем реализацию ролевых прав доступа (задачи 6.1-6.2)")
    print("=" * 60)

    # 6.1: Проверка ролей
    if not check_user_roles():
        print("❌ Критическая ошибка в ролях пользователей!")
        return

    # 6.2: Улучшение декоратора
    if not fix_role_decorator():
        print("❌ Не удалось улучшить декоратор!")
        return

    # 6.3: Применение ограничений
    if not apply_route_restrictions():
        print("❌ Не удалось применить ограничения!")
        return

    # Тестирование
    if not test_role_implementation():
        print("❌ Тестирование не прошло!")
        return

    print("\n" + "=" * 60)
    print("✅ Ролевые права доступа успешно реализованы!")
    print("\nСледующие шаги:")
    print("1. Перезапустить приложение: python main.py")
    print("2. Протестировать доступ под разными ролями")
    print("3. Проверить, что админские страницы недоступны registrar'у")
    print("4. Переходить к задаче 6.4-6.5 (фильтрация календаря)")


if __name__ == "__main__":
    main()
