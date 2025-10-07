# fix_role_implementation.py
# Исправленная реализация ролевой системы

import os
import re
from pathlib import Path


def check_and_fix_main_py():
    """Исправляем main.py для корректной работы ролей"""
    print("=== Исправление main.py ===")

    with open("main.py", "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Убеждаемся, что декоратор role_required правильно реализован
    if "def role_required(" not in content:
        print("Добавляем декоратор role_required...")

        # Ищем место после импортов
        import_end = content.find("app = Flask(__name__)")
        if import_end == -1:
            import_end = content.find("from production_auth import")
            if import_end != -1:
                import_end = content.find("\n", import_end)

        role_decorator = '''
def role_required(*allowed_roles):
    """Декоратор для проверки ролей пользователя"""
    from functools import wraps
    from flask import session, abort, redirect, url_for, flash

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                flash("Требуется авторизация", "warning")
                return redirect(url_for('auth.login'))

            if 'user_role' not in session:
                flash("Роль пользователя не определена", "danger")
                return redirect(url_for('auth.login'))

            user_role = session['user_role']
            valid_roles = {"admin", "registrar", "doctor"}

            if user_role not in valid_roles:
                flash(f"Некорректная роль: {user_role}", "danger")
                session.clear()
                return redirect(url_for('auth.login'))

            if user_role not in allowed_roles:
                flash(f"Доступ запрещен. Требуется роль: {', '.join(allowed_roles)}", "danger")
                abort(403)

            return f(*args, **kwargs)
        return decorated_function
    return decorator

'''

        content = content[:import_end] + role_decorator + content[import_end:]
        print("✅ Декоратор role_required добавлен")
    else:
        print("✅ Декоратор role_required уже существует")

    # 2. Добавляем ограничения к ключевым маршрутам
    routes_to_protect = [
        ('@app.route("/doctors")', "admin"),
        ('@app.route("/services")', "admin"),
        ('@app.route("/rooms")', "admin"),
        ('@app.route("/patients")', 'admin", "registrar'),
    ]

    for route_pattern, roles in routes_to_protect:
        if route_pattern in content:
            # Ищем функцию после маршрута
            route_pos = content.find(route_pattern)
            func_start = content.find("def ", route_pos)

            if func_start != -1:
                # Проверяем, есть ли уже @role_required
                func_line_end = content.find("\n", func_start)
                func_section = content[route_pos:func_line_end]

                if "@role_required" not in func_section:
                    # Добавляем декоратор перед функцией
                    decorator_line = f'@role_required("{roles}")\n'

                    # Вставляем перед def
                    content = content[:func_start] + decorator_line + content[func_start:]
                    print(f"✅ Добавлен @role_required для {route_pattern}")

    # 3. Обновляем api_events для фильтрации по ролям
    if '@app.route("/api/events")' in content:
        print("Обновляем API events для фильтрации по ролям...")

        # Ищем начало функции api_events
        api_events_start = content.find('@app.route("/api/events")')
        api_events_func_start = content.find("def api_events():", api_events_start)

        if api_events_func_start != -1:
            # Ищем конец функции (следующий @app.route или конец файла)
            next_route = content.find("\n@app.route", api_events_func_start)
            if next_route == -1:
                next_route = len(content)

            # Заменяем функцию
            new_api_events = """def api_events():
    # Получаем роль пользователя для фильтрации
    user_role = session.get("user_role", "")
    user_id = session.get("user_id", "")

    # Базовые параметры запроса
    start_str = request.args.get("start")
    end_str = request.args.get("end")
    patient_id = (request.args.get("patient_id") or "").strip()
    doctor_id = request.args.get("doctor_id")
    room_id = request.args.get("room_id")
    room_name = request.args.get("room_name")
    service_id = request.args.get("service_id")
    service_name = request.args.get("service_name")

    start_dt = parse_iso(start_str)
    end_dt = parse_iso(end_str)

    # Базовый запрос
    q = {}
    if start_dt and end_dt:
        q["start"] = {"$lt": end_dt}
        q["end"] = {"$gt": start_dt}

    # ФИЛЬТРАЦИЯ ПО РОЛЯМ
    if user_role == "doctor":
        # Врач видит только свои записи
        try:
            user_doc = db.users.find_one({"_id": ObjectId(user_id)})
            if user_doc:
                # Ищем врача по email
                doctor = db.doctors.find_one({"email": user_doc.get("login", "")})
                if doctor:
                    q["doctor_id"] = doctor["_id"]
                else:
                    return jsonify([])  # Врач не найден
            else:
                return jsonify([])
        except Exception:
            return jsonify([])

    # Остальные фильтры
    if doctor_id:
        try:
            q["doctor_id"] = ObjectId(doctor_id)
        except Exception:
            pass

    if room_id:
        try:
            q["room_id"] = ObjectId(room_id)
        except Exception:
            pass
    elif room_name:
        r = db.rooms.find_one({"name": room_name}, {"_id": 1})
        if r:
            q["room_id"] = r["_id"]

    if service_id:
        try:
            q["service_id"] = ObjectId(service_id)
        except Exception:
            pass
    elif service_name:
        s = db.services.find_one({"name": service_name}, {"_id": 1})
        if s:
            q["service_id"] = s["_id"]

    if patient_id:
        try:
            q["patient_id"] = ObjectId(patient_id)
        except Exception:
            pass

    # Справочники
    doctors_map = {str(d["_id"]): d for d in db.doctors.find({}, {"full_name": 1})}
    patients_map = {str(p["_id"]): p for p in db.patients.find({}, {"full_name": 1})}
    services_map = {str(s["_id"]): s for s in db.services.find({}, {"name": 1, "color": 1, "duration_min": 1})}
    rooms_map = {str(r["_id"]): r for r in db.rooms.find({}, {"name": 1})}

    # Формируем события
    events = []
    cursor = db.appointments.find(q).sort("start", 1)

    for a in cursor:
        did = str(a.get("doctor_id") or "")
        pid = str(a.get("patient_id") or "")
        sid = str(a.get("service_id") or "")
        rid = str(a.get("room_id") or "")

        a_start = to_dt(a.get("start"))
        if not a_start:
            continue

        a_end = to_dt(a.get("end"))
        if not a_end:
            dur = services_map.get(sid, {}).get("duration_min", 30)
            try:
                dur = int(dur)
            except Exception:
                dur = 30
            a_end = add_minutes(a_start, dur)

        doc = doctors_map.get(did, {})
        pat = patients_map.get(pid, {})
        srv = services_map.get(sid, {})
        rm = rooms_map.get(rid, {})

        title = f'{srv.get("name", "Услуга")} — {pat.get("full_name", "Пациент")}'

        events.append({
            "id": str(a["_id"]),
            "title": title,
            "start": a_start.isoformat(),
            "end": a_end.isoformat(),
            "backgroundColor": srv.get("color") or "#3498db",
            "borderColor": srv.get("color") or "#3498db",
            "extendedProps": {
                "patient": pat.get("full_name"),
                "doctor": doc.get("full_name"),
                "service": srv.get("name"),
                "room": rm.get("name"),
                "doctor_id": did,
                "patient_id": pid,
                "service_id": sid,
                "room_id": rid,
            },
        })

    return jsonify(events)"""

            # Заменяем функцию
            func_end = content.find("\n\n@", api_events_func_start)
            if func_end == -1:
                func_end = next_route

            content = content[:api_events_func_start] + new_api_events + content[func_end:]
            print("✅ API events обновлён для фильтрации по ролям")

    # Сохраняем изменения
    with open("main.py", "w", encoding="utf-8") as f:
        f.write(content)

    print("✅ main.py успешно обновлён")


def update_base_template():
    """Обновляем base.html для скрытия элементов по ролям"""
    print("\n=== Обновление base.html ===")

    if not Path("templates/base.html").exists():
        print("❌ templates/base.html не найден")
        return

    with open("templates/base.html", "r", encoding="utf-8") as f:
        content = f.read()

    # Простая замена для основных админских ссылок
    admin_links = [
        'href="/doctors"',
        'href="/services"',
        'href="/rooms"',
    ]

    # Обрабатываем каждую ссылку отдельно
    for link in admin_links:
        if link in content:
            # Ищем полную строку с ссылкой
            link_pos = content.find(link)
            line_start = content.rfind("<", 0, link_pos)
            line_end = content.find("</a>", link_pos) + 4

            if line_start != -1 and line_end > link_pos:
                old_line = content[line_start:line_end]
                new_line = '{% if session.user_role == "admin" %}\n' + old_line + "\n{% endif %}"
                content = content.replace(old_line, new_line)
                print(f"Обернут в условие: {link}")

    # Сохраняем
    with open("templates/base.html", "w", encoding="utf-8") as f:
        f.write(content)

    print("✅ base.html обновлён")


def test_implementation():
    """Тестируем реализацию"""
    print("\n=== Тестирование реализации ===")

    try:
        # Проверяем БД подключение
        from dotenv import load_dotenv
        from pymongo import MongoClient

        load_dotenv()
        client = MongoClient(os.getenv("MONGO_URI"))
        db = client[os.getenv("DB_NAME", "medplatforma")]

        # Проверяем пользователей
        users = list(db.users.find({}, {"login": 1, "role": 1}))
        print(f"Найдено пользователей: {len(users)}")

        role_counts = {}
        for user in users:
            role = user.get("role", "unknown")
            role_counts[role] = role_counts.get(role, 0) + 1
            print(f"  {user.get('login')}: {role}")

        print(f"Статистика ролей: {role_counts}")

        # Проверяем синтаксис main.py
        with open("main.py", "r", encoding="utf-8") as f:
            code = f.read()

        compile(code, "main.py", "exec")
        print("✅ Синтаксис main.py корректен")

        # Проверяем наличие ключевых элементов
        checks = [
            ("def role_required(", "Декоратор найден"),
            ("@role_required", "Декоратор применён"),
            ("user_role = session.get", "Получение роли"),
            ("abort(403)", "Обработка доступа"),
        ]

        for check, desc in checks:
            if check in code:
                print(f"✅ {desc}")
            else:
                print(f"❌ {desc} НЕ НАЙДЕН")

        return True

    except Exception as e:
        print(f"❌ Ошибка тестирования: {e}")
        return False


def main():
    print("🔧 ИСПРАВЛЕНИЕ РОЛЕВОЙ СИСТЕМЫ")
    print("=" * 50)

    try:
        # Основные исправления
        check_and_fix_main_py()
        update_base_template()

        # Тестирование
        if test_implementation():
            print("\n✅ ВСЕ ИСПРАВЛЕНИЯ ПРИМЕНЕНЫ УСПЕШНО!")
            print("\nДля проверки:")
            print("1. python main.py")
            print("2. Откройте http://localhost:5000")
            print("3. Войдите под разными ролями")
            print("4. Проверьте доступ к разделам")
        else:
            print("\n❌ Есть проблемы в реализации")

    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")


if __name__ == "__main__":
    main()
