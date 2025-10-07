# ru_catalogs.py
from datetime import datetime

DOCTOR_ROLES = {
    "Стоматолог-терапевт": ["Терапия"],
    "Стоматолог-хирург": ["Хирургия"],
    "Стоматолог-ортодонт": ["Ортодонтия"],
    "Гигиенист": ["Гигиена"],
    "Эндодонтист": ["Эндодонтия"],
    "Рентгенолог": ["Рентгенология"],
    "Имплантолог": ["Имплантология"],
    "Пародонтолог": ["Пародонтология"],
    "Ортопед": ["Ортопедия"],
    "Стоматолог-эстетист": ["Эстетика"],
}

DOCTORS = [
    "д-р Иван Соколов",
    "д-р Мария Иванова",
    "д-р Алексей Петров",
    "д-р Анна Волкова",
    "д-р Сергей Кузнецов",
    "д-р Ольга Смирнова",
    "д-р Дмитрий Орлов",
    "д-р Елена Фёдорова",
    "д-р Павел Егоров",
    "д-р София Никитина",
]

PATIENTS = [
    ("Иван Петров", "male"),
    ("Мария Смирнова", "female"),
    ("Алексей Иванов", "male"),
    ("Анна Волкова", "female"),
    ("Сергей Кузнецов", "male"),
    ("Ольга Соколова", "female"),
    ("Дмитрий Орлов", "male"),
    ("Елена Фёдорова", "female"),
    ("Павел Егоров", "male"),
    ("Светлана Никитина", "female"),
]

ROOMS = [
    {"name": "Кабинет 1", "type": "Терапия", "status": "available", "color": "#1abc9c"},
    {"name": "Кабинет 2", "type": "Хирургия", "status": "available", "color": "#9b59b6"},
    {"name": "Рентген",   "type": "Рентген",  "status": "maintenance", "color": "#f39c12"},
    {"name": "Гигиена",   "type": "Гигиена",  "status": "available", "color": "#2ecc71"},
    {"name": "Кабинет 5", "type": "Терапия",  "status": "occupied", "color": "#e67e22"},
]

SERVICES = [
    {"name": "Консультация",      "code": "CONSULT", "description": "Первичная консультация",        "price": 3000, "duration_min": 20, "color": "#3498db"},
    {"name": "Гигиена",           "code": "HYGIENE", "description": "Профессиональная чистка",       "price": 4500, "duration_min": 40, "color": "#1abc9c"},
    {"name": "Пломба",            "code": "FILL",    "description": "Восстановление пломбой",        "price": 6000, "duration_min": 50, "color": "#9b59b6"},
    {"name": "Лечение каналов",   "code": "ROOT",    "description": "Эндодонтическое лечение",       "price": 12000,"duration_min": 90, "color": "#e67e22"},
    {"name": "Коронка",           "code": "CROWN",   "description": "Установка коронки",             "price": 18000,"duration_min": 60, "color": "#e74c3c"},
    {"name": "Осмотр ортодонта",  "code": "ORTHO",   "description": "Контроль брекет‑системы",       "price": 5000, "duration_min": 30, "color": "#2ecc71"},
    {"name": "Отбеливание",       "code": "WHITE",   "description": "Осветление эмали",              "price": 9000, "duration_min": 45, "color": "#16a085"},
    {"name": "Консультация по имплантам", "code": "IMPCON", "description": "Подбор имплантации",   "price": 4000, "duration_min": 30, "color": "#34495e"},
    {"name": "Рентген",           "code": "XRAY",    "description": "Диагностика на рентгене",       "price": 1500, "duration_min": 15, "color": "#95a5a6"},
    {"name": "Удаление зуба",     "code": "EXTR",    "description": "Хирургическое удаление",        "price": 8000, "duration_min": 40, "color": "#c0392b"},
    {"name": "Виниры",            "code": "VENEER",  "description": "Установка виниров",             "price": 45000,"duration_min": 80, "color": "#8e44ad"},
    {"name": "Пародонтология",    "code": "PERIO",   "description": "Лечение тканей пародонта",      "price": 10000,"duration_min": 50, "color": "#27ae60"},
]

VISIT_STATUSES = [
    {"key": "scheduled", "title": "Запланирована", "color": "#3498db", "order": 1},
    {"key": "completed", "title": "Выполнена",     "color": "#2ecc71", "order": 2},
    {"key": "cancelled", "title": "Отменена",      "color": "#e74c3c", "order": 3},
    {"key": "no_show",   "title": "Не пришёл",     "color": "#f1c40f", "order": 4},
]
