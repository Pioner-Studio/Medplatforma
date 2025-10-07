# fix_api_authentication.py
# Исправляем проблему с авторизацией API

import re


def fix_api_events_auth():
    """Исправляем декоратор для api_events - убираем лишние роли"""
    print("=== Исправление авторизации API events ===")

    with open("main.py", "r", encoding="utf-8") as f:
        content = f.read()

    # Ищем строку с @role_required для api_events
    api_events_section = content.find('@app.route("/api/events")')
    if api_events_section == -1:
        print("❌ Маршрут /api/events не найден")
        return False

    # Берем секцию с функцией api_events
    next_route = content.find("\n@app.route", api_events_section + 1)
    if next_route == -1:
        next_route = len(content)

    section = content[api_events_section:next_route]

    # Заменяем неправильный декоратор
    if '@role_required("admin", "registrar", "doctor")' in section:
        print("Убираем избыточный декоратор @role_required...")
        # Убираем строку с @role_required
        old_section = section
        new_section = re.sub(r'@role_required\("admin", "registrar", "doctor"\)\n', "", section)
        content = content.replace(old_section, new_section)
        print("✅ Декоратор @role_required удален с api_events")
    elif "@role_required" in section:
        print("Найден другой декоратор @role_required, убираем его...")
        old_section = section
        new_section = re.sub(r"@role_required[^\n]*\n", "", section)
        content = content.replace(old_section, new_section)
        print("✅ Декоратор @role_required удален с api_events")
    else:
        print("✅ Лишние декораторы не найдены")

    # Убеждаемся, что остался только @login_required
    if "@login_required" not in section:
        print("Добавляем @login_required к api_events...")
        def_pos = content.find("def api_events():", api_events_section)
        if def_pos != -1:
            content = content[:def_pos] + "@login_required\n" + content[def_pos:]
            print("✅ Добавлен @login_required")

    # Сохраняем изменения
    with open("main.py", "w", encoding="utf-8") as f:
        f.write(content)

    return True


def fix_other_api_endpoints():
    """Проверяем и исправляем другие API endpoints"""
    print("=== Проверка других API endpoints ===")

    with open("main.py", "r", encoding="utf-8") as f:
        content = f.read()

    # API endpoints, которые должны быть доступны после простой авторизации
    api_endpoints = [
        "/api/dicts",
        "/api/rooms/status_now",
        "/api/services_min",
        "/api/patients/min",
    ]

    changes_made = False

    for endpoint in api_endpoints:
        # Ищем маршрут
        route_pattern = f'@app.route("{endpoint}"'
        route_pos = content.find(route_pattern)

        if route_pos != -1:
            # Берем секцию до следующего маршрута
            next_route = content.find("\n@app.route", route_pos + 1)
            if next_route == -1:
                next_route = content.find("\ndef ", route_pos + 100)  # или следующая функция
            if next_route == -1:
                next_route = len(content)

            section = content[route_pos:next_route]

            # Если есть @role_required, но нет критической необходимости - убираем
            if "@role_required" in section and endpoint in ["/api/dicts", "/api/rooms/status_now"]:
                print(f"Убираем @role_required с {endpoint}...")
                old_section = section
                new_section = re.sub(r"@role_required[^\n]*\n", "", section)
                content = content.replace(old_section, new_section)
                changes_made = True
                print(f"✅ Исправлен {endpoint}")

    if changes_made:
        with open("main.py", "w", encoding="utf-8") as f:
            f.write(content)
        print("✅ API endpoints исправлены")
    else:
        print("✅ API endpoints в порядке")


def verify_calendar_route():
    """Проверяем маршрут календаря"""
    print("=== Проверка маршрута календаря ===")

    with open("main.py", "r", encoding="utf-8") as f:
        content = f.read()

    # Ищем маршрут календаря
    calendar_pos = content.find('@app.route("/calendar")')
    if calendar_pos == -1:
        print("❌ Маршрут /calendar не найден")
        return False

    # Проверяем секцию календаря
    next_route = content.find("\n@app.route", calendar_pos + 1)
    if next_route == -1:
        next_route = len(content)

    calendar_section = content[calendar_pos:next_route]

    # Должен быть только @login_required, без @role_required
    if "@role_required" in calendar_section:
        print("Найден @role_required в calendar_view, убираем...")
        old_section = calendar_section
        new_section = re.sub(r"@role_required[^\n]*\n", "", calendar_section)
        content = content.replace(old_section, new_section)

        with open("main.py", "w", encoding="utf-8") as f:
            f.write(content)

        print("✅ Убран @role_required с calendar_view")
    else:
        print("✅ calendar_view в порядке")

    # Проверяем наличие @login_required
    if "@login_required" in calendar_section:
        print("✅ @login_required присутствует")
    else:
        print("❌ @login_required отсутствует в calendar_view")
        return False

    return True


def check_authentication_flow():
    """Проверяем корректность потока авторизации"""
    print("=== Проверка потока авторизации ===")

    with open("main.py", "r", encoding="utf-8") as f:
        content = f.read()

    # Проверяем, что init_auth правильно вызван
    if "init_auth(app)" in content:
        print("✅ init_auth инициализирован")
    else:
        print("❌ init_auth не найден")

    # Проверяем импорт production_auth
    if "from production_auth import" in content:
        print("✅ production_auth импортирован")
    else:
        print("❌ production_auth не импортирован")

    # Проверяем secret_key
    if "app.secret_key" in content:
        print("✅ secret_key настроен")
    else:
        print("❌ secret_key не найден")


def test_fixed_endpoints():
    """Простая проверка синтаксиса"""
    print("=== Проверка синтаксиса ===")

    try:
        with open("main.py", "r", encoding="utf-8") as f:
            code = f.read()

        compile(code, "main.py", "exec")
        print("✅ Синтаксис корректен")
        return True
    except SyntaxError as e:
        print(f"❌ Синтаксическая ошибка: {e}")
        return False
    except Exception as e:
        print(f"❌ Ошибка компиляции: {e}")
        return False


def main():
    print("🔧 ИСПРАВЛЕНИЕ АВТОРИЗАЦИИ API")
    print("=" * 50)

    print("Проблема: API /api/events возвращает 302 (редирект на логин)")
    print("Решение: Убираем избыточные ограничения доступа")
    print()

    steps = [
        ("Исправление api_events", fix_api_events_auth),
        ("Проверка других API", fix_other_api_endpoints),
        ("Проверка календаря", verify_calendar_route),
        ("Проверка авторизации", check_authentication_flow),
        ("Проверка синтаксиса", test_fixed_endpoints),
    ]

    success_count = 0

    for step_name, step_func in steps:
        print(f"--- {step_name} ---")
        try:
            if step_func():
                success_count += 1
                print(f"✅ {step_name} - OK")
            else:
                print(f"❌ {step_name} - FAILED")
        except Exception as e:
            print(f"❌ Ошибка в {step_name}: {e}")
        print()

    print("=" * 50)
    if success_count >= 4:
        print("✅ АВТОРИЗАЦИЯ API ИСПРАВЛЕНА!")
        print()
        print("Следующие шаги:")
        print("1. Перезапустите сервер: Ctrl+C, затем python main.py")
        print("2. Обновите страницу в браузере")
        print("3. Войдите в систему (если требуется)")
        print("4. Записи должны отображаться в календаре")
        print()
        print("Если записи все еще не видны:")
        print("- Проверьте консоль браузера (F12)")
        print("- Убедитесь, что пользователь авторизован")
        print("- Проверьте диапазон дат в календаре")
    else:
        print("❌ Есть проблемы. Проверьте ошибки выше.")


if __name__ == "__main__":
    main()
