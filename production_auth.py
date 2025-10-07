# production_auth.py
from __future__ import annotations

from typing import Iterable, Callable, Optional
import re

from flask import (
    Blueprint,
    current_app,
    request,
    session,
    redirect,
    url_for,
    render_template,
    jsonify,
    flash,
)
from functools import wraps
from werkzeug.security import check_password_hash as wz_check, generate_password_hash

# Для bcrypt
try:
    import bcrypt
except ImportError:
    bcrypt = None

# Типы PyMongo (используем для безопасной проверки)
try:
    from pymongo.database import Database as _MongoDatabase
    from pymongo.collection import Collection as _MongoCollection
except Exception:
    _MongoDatabase = object  # type: ignore
    _MongoCollection = object  # type: ignore


# ---------------------------------------------------------------------
# ВСПОМОГАТЕЛЬНОЕ
# ---------------------------------------------------------------------


def _get_db():
    """Берём "источник данных" из конфигурации приложения.
    Допускаем три варианта:
      1) dict с ключом "users" (сидовые пользователи)
      2) PyMongo Database
      3) PyMongo Collection (именно коллекция users)
    """
    return current_app.config.get("DB")


def _users_from_dict(db_dict: dict) -> list[dict]:
    return list(db_dict.get("users", []))


def _users() -> list[dict]:
    """Возвращает всех пользователей:
    - для PyMongo DB/Collection — list(find({}))
    - для dict — содержимое ключа "users"
    """
    db = _get_db()
    if db is None:
        return []

    # Вариант 1: словарь со списком пользователей
    if isinstance(db, dict):
        return _users_from_dict(db)

    # Вариант 2а: нам передали саму БАЗУ (Database)
    if isinstance(db, _MongoDatabase):
        try:
            return list(db.get_collection("users").find({}))
        except Exception:
            return []

    # Вариант 2б: нам передали коллекцию (Collection)
    if isinstance(db, _MongoCollection):
        try:
            return list(db.find({}))
        except Exception:
            return []

    return []


def _find_user(login: str) -> Optional[dict]:
    """Находим пользователя по логину:
    - для PyMongo делаем find_one
    - для dict ищем в списке
    """
    login = (login or "").strip()
    if not login:
        return None

    db = _get_db()

    # PyMongo Database
    if isinstance(db, _MongoDatabase):
        try:
            doc = db.get_collection("users").find_one({"login": login})
            return doc or None
        except Exception:
            pass

    # PyMongo Collection
    if isinstance(db, _MongoCollection):
        try:
            doc = db.find_one({"login": login})
            return doc or None
        except Exception:
            pass

    # dict
    if isinstance(db, dict):
        for u in _users_from_dict(db):
            if (u.get("login") or "").strip().lower() == login.lower():
                return u

    return None


def _verify_password(user: dict, raw_password: str) -> bool:
    """Проверяем пароль. Поддерживаем только хэш (bcrypt/scrypt/pbkdf2).
    Если вдруг в БД лежит старое поле 'password' с *хэшем* — тоже ок.
    """
    if not raw_password:
        return False

    pwd_hash = user.get("password_hash") or user.get("password")
    if not pwd_hash:
        return False

    try:
        return check_password_hash(pwd_hash, raw_password)
    except Exception:
        # если лежит не-хэш — никого не пускаем
        return False


def _set_session_user(user: dict) -> None:
    session["user"] = {
        "login": user.get("login"),
        "full_name": user.get("full_name") or user.get("name") or user.get("login"),
        "role": user.get("role", "registrar"),
        "doctor_id": user.get("doctor_id"),
        "active": user.get("active", True),
    }


# ---------------------------------------------------------------------
# ДЕКОРАТОРЫ ДОСТУПА
# ---------------------------------------------------------------------


def login_required(view: Callable) -> Callable:
    @wraps(view)
    def wrapper(*args, **kwargs):
        user = session.get("user")
        print(f"========================\n")

        if not user:
            next_url = request.path if request.method == "GET" else url_for("calendar_view")
            return redirect(url_for("auth.login", next=next_url))
        return view(*args, **kwargs)

    return wrapper


def role_required(roles: Iterable[str]) -> Callable:
    def decorator(view: Callable) -> Callable:
        @wraps(view)
        def wrapper(*args, **kwargs):
            required_roles = set(roles)
            u = session.get("user")

            print(f"\n[role_required] Path: {request.path}, Method: {request.method}")
            print(
                f"[role_required] Required: {required_roles}, User role: {u.get('role') if u else None}"
            )

            if not u:
                # ...
                return redirect(url_for("auth.login", next=request.path))

            if u.get("role") not in required_roles:
                flash("Недостаточно прав доступа", "error")
                return redirect(url_for("calendar_view"))
            return view(*args, **kwargs)

        return wrapper

    return decorator


def admin_required(view: Callable) -> Callable:
    return role_required({"admin", "owner"})(view)


# ---------------------------------------------------------------------
# BLUEPRINT AUTH
# ---------------------------------------------------------------------

auth_bp = Blueprint("auth", __name__, template_folder="templates")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    login_input = (request.form.get("login") or "").strip()
    password_input = request.form.get("password") or ""

    if not login_input or not password_input:
        flash("Введите логин и пароль", "danger")
        current_app.logger.warning("LOGIN FAIL: empty login/password")
        return render_template("login.html"), 401

    # Получаем db из конфигурации Flask app
    db = current_app.config.get("DB")
    if db is None:
        flash("Ошибка конфигурации системы", "danger")
        current_app.logger.error("DB not configured in app.config")
        return render_template("login.html"), 500

    # Ищем юзера по login/username (без учёта регистра)
    try:
        u = db.users.find_one(
            {
                "$or": [
                    {"login": {"$regex": f"^{re.escape(login_input)}$", "$options": "i"}},
                    {"username": {"$regex": f"^{re.escape(login_input)}$", "$options": "i"}},
                ]
            }
        )
    except Exception as e:
        current_app.logger.exception("DB query error: %s", e)
        flash("Ошибка подключения к базе данных", "danger")
        return render_template("login.html"), 500

    if not u:
        flash("Неверный логин или пароль", "danger")
        current_app.logger.warning("LOGIN FAIL: user not found for %r", login_input)
        return render_template("login.html"), 401

    # Проверка пароля
    ok = False
    pwd_field = u.get("password") or u.get("password_hash") or u.get("pwd")

    try:
        if bcrypt and isinstance(pwd_field, bytes) and pwd_field.startswith(b"$2b$"):
            ok = bcrypt.checkpw(password_input.encode("utf-8"), pwd_field)
        elif bcrypt and isinstance(pwd_field, str) and pwd_field.startswith("$2b$"):
            ok = bcrypt.checkpw(password_input.encode("utf-8"), pwd_field.encode("utf-8"))
        elif isinstance(pwd_field, str) and pwd_field.startswith("pbkdf2:"):
            ok = wz_check(pwd_field, password_input)
        elif isinstance(pwd_field, str):
            # Временно допускаем простой текст
            ok = pwd_field == password_input
    except Exception as e:
        current_app.logger.exception("Password check error: %s", e)
        ok = False

    if not ok:
        flash("Неверный логин или пароль", "danger")
        current_app.logger.warning("LOGIN FAIL: bad password for %r", login_input)
        return render_template("login.html"), 401

    # Успешный вход - создаем сессию
    session.clear()
    session.permanent = True
    normalized_role = str(u.get("role") or "registrar").strip().lower()
    avatar = u.get("avatar") or "default.png"

    session["user"] = {
        "_id": str(u.get("_id")),
        "login": u.get("login") or u.get("username") or login_input,
        "username": u.get("username"),
        "full_name": u.get("full_name") or u.get("name") or u.get("login") or login_input,
        "role": normalized_role,
        "avatar": avatar,
        "active": True,
    }
    session["role"] = normalized_role
    session["user_id"] = str(u.get("_id"))
    session.modified = True

    current_app.logger.info("LOGIN SUCCESS: %s (role: %s)", login_input, normalized_role)

    next_url = request.args.get("next") or url_for("calendar_view")
    return redirect(next_url)


@auth_bp.route("/logout", methods=["GET"])
def logout():
    session.pop("user", None)
    flash("Вы вышли из системы", "success")
    return redirect(url_for("auth.login"))


@auth_bp.route("/api/current-user", methods=["GET"])
def current_user_api():
    return jsonify({"ok": True, "user": session.get("user")})


@auth_bp.route("/change-password", methods=["POST"])
@login_required
def change_password():
    """Простая смена пароля текущему пользователю (JSON):
    body: { "old_password": "...", "new_password": "..." }
    Для dict-хранилища — перезапишем в памяти; для Mongo — потребуется код в проекте,
    который реально сохранит изменения (здесь не трогаем БД).
    """
    data = request.get_json(silent=True) or {}
    old_pwd = data.get("old_password", "")
    new_pwd = data.get("new_password", "")

    me = session.get("user") or {}
    user = _find_user(me.get("login"))
    if not user:
        return jsonify({"ok": False, "error": "user_not_found"}), 404

    if not _verify_password(user, old_pwd):
        return jsonify({"ok": False, "error": "bad_old_password"}), 400

    # меняем только в объекте; для реальной БД — нужна своя логика апдейта
    user["password_hash"] = generate_password_hash(new_pwd)

    flash("Пароль изменён", "success")
    return jsonify({"ok": True})


# ---------------------------------------------------------------------
# ИНИЦИАЛИЗАЦИЯ
# ---------------------------------------------------------------------


def init_auth(app) -> None:
    """Вызывается один раз из main.py:
    from production_auth import init_auth
    init_auth(app)
    """
    if not getattr(app, "secret_key", None):
        app.secret_key = "change-me-in-production"
    # Регистрируем blueprint 'auth'
    app.register_blueprint(auth_bp)
