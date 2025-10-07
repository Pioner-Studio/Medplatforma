# implement_role_system.py
# Реализуем систему ролевых прав доступа

import re

# 1. Создаем декоратор для ролей
role_decorator = '''
from functools import wraps
from flask import session, abort, redirect, url_for

def role_required(*allowed_roles):
    """Декоратор для проверки ролей пользователя"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_role' not in session:
                return redirect(url_for('auth.login'))

            user_role = session['user_role']
            if user_role not in allowed_roles:
                abort(403)  # Forbidden

            return f(*args, **kwargs)
        return decorated_function
    return decorator
'''

# 2. Читаем main.py
with open("main.py", "r", encoding="utf-8") as f:
    content = f.read()

# 3. Добавляем декоратор после импортов
import_section = content.find("from production_auth import")
if import_section != -1:
    # Находим конец строки импорта
    end_import = content.find("\n", import_section)
    content = content[:end_import] + "\n\n" + role_decorator + content[end_import:]

# 4. Применяем ограничения к маршрутам
routes_to_restrict = {
    '@app.route("/doctors")': '@role_required("admin")',
    '@app.route("/add_doctor")': '@role_required("admin")',
    '@app.route("/edit_doctor")': '@role_required("admin")',
    '@app.route("/services")': '@role_required("admin")',
    '@app.route("/add_service")': '@role_required("admin")',
    '@app.route("/edit_service")': '@role_required("admin")',
    '@app.route("/rooms")': '@role_required("admin")',
    '@app.route("/add_room")': '@role_required("admin")',
    '@app.route("/edit_room")': '@role_required("admin")',
    '@app.route("/patients")': '@role_required("admin", "registrar")',
    '@app.route("/add_patient")': '@role_required("admin", "registrar")',
    '@app.route("/edit_patient")': '@role_required("admin", "registrar")',
    '@app.route("/finance")': '@role_required("admin", "registrar")',
    '@app.route("/data_tools")': '@role_required("admin")',
    '@app.route("/backup")': '@role_required("admin")',
}

# Добавляем декораторы перед функциями
for route_pattern, decorator in routes_to_restrict.items():
    pattern = f"({re.escape(route_pattern)}.*?@login_required)"
    replacement = f"\\1\n{decorator}"
    content = re.sub(pattern, replacement, content, flags=re.DOTALL)

# 5. Сохраняем
with open("main.py", "w", encoding="utf-8") as f:
    f.write(content)

print("✅ Декоратор ролей добавлен")
print("✅ Ограничения доступа применены к маршрутам")
