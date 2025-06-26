from pymongo import MongoClient
from werkzeug.security import generate_password_hash  # Только если хочешь хешировать пароли

client = MongoClient("mongodb+srv://medadmin:medpass123@medplatforma.cnv7fbo.mongodb.net/")
db = client['medplatforma']

staff_list = [
    # Инвесторы
    {"full_name": "Наконечный Алексей", "role": "investor", "position": "Инвестор", "status": "активен", "email": "alexey@clinic.ru", "phone": "", "password": "password"},
    {"full_name": "Наконечная Елена",     "role": "investor", "position": "Инвестор", "status": "активен", "email": "", "phone": "", "password": "password"},
    {"full_name": "Гогуева Алина",        "role": "investor", "position": "Инвестор", "status": "активен", "email": "", "phone": "", "password": "password"},

    # Администраторы
    {"full_name": "Администратор (вакансия 1)", "role": "admin", "position": "Администратор", "status": "вакансия", "email": "", "phone": "", "password": "password"},
    {"full_name": "Администратор (вакансия 2)", "role": "admin", "position": "Администратор", "status": "вакансия", "email": "", "phone": "", "password": "password"},

    # Главный врач
    {"full_name": "Гогуева Алина",        "role": "chief_doctor", "position": "Главный врач", "status": "активен", "email": "", "phone": "", "password": "password"},
    {"full_name": "Главный врач (вакансия)", "role": "chief_doctor", "position": "Главный врач", "status": "вакансия", "email": "", "phone": "", "password": "password"},

    # Врачи
    {"full_name": "Гогуева Алина",        "role": "doctor", "position": "Врач", "status": "активен", "email": "", "phone": "", "password": "password"},
    {"full_name": "Роман Роман",          "role": "doctor", "position": "Врач", "status": "активен", "email": "", "phone": "", "password": "password"},
    {"full_name": "Айвазян Альберт",      "role": "doctor", "position": "Врач", "status": "активен", "email": "", "phone": "", "password": "password"},
    {"full_name": "Юрьева Анна",          "role": "doctor", "position": "Врач", "status": "активен", "email": "", "phone": "", "password": "password"},
    {"full_name": "Миргатия Ольга",       "role": "doctor", "position": "Врач", "status": "активен", "email": "", "phone": "", "password": "password"},
    {"full_name": "Калачев Алексей",      "role": "doctor", "position": "Врач", "status": "активен", "email": "", "phone": "", "password": "password"},
    {"full_name": "Врач (вакансия 1)", "role": "doctor", "position": "Врач", "status": "вакансия", "email": "", "phone": "", "password": "password"},
    {"full_name": "Врач (вакансия 2)", "role": "doctor", "position": "Врач", "status": "вакансия", "email": "", "phone": "", "password": "password"},
    {"full_name": "Врач (вакансия 3)", "role": "doctor", "position": "Врач", "status": "вакансия", "email": "", "phone": "", "password": "password"},
    {"full_name": "Врач (вакансия 4)", "role": "doctor", "position": "Врач", "status": "вакансия", "email": "", "phone": "", "password": "password"},
    {"full_name": "Врач (вакансия 5)", "role": "doctor", "position": "Врач", "status": "вакансия", "email": "", "phone": "", "password": "password"},

    # Кураторы
    {"full_name": "Куратор (вакансия 1)", "role": "curator", "position": "Куратор", "status": "вакансия", "email": "", "phone": "", "password": "password"},
    {"full_name": "Куратор (вакансия 2)", "role": "curator", "position": "Куратор", "status": "вакансия", "email": "", "phone": "", "password": "password"},

    # Управляющий директор
    {"full_name": "Управляющий директор (вакансия)", "role": "manager", "position": "Управляющий директор", "status": "вакансия", "email": "", "phone": "", "password": "password"},

    # Старшая медсестра
    {"full_name": "Старшая медсестра (вакансия)", "role": "nurse", "position": "Старшая медсестра", "status": "вакансия", "email": "", "phone": "", "password": "password"},

    # Ассистенты
    {"full_name": "Ульяна Аксенова", "role": "assistant", "position": "Ассистент", "status": "активен", "email": "", "phone": "", "password": "password"},
    {"full_name": "Мусаева Айшат",   "role": "assistant", "position": "Ассистент", "status": "активен", "email": "", "phone": "", "password": "password"},
    {"full_name": "Ассистент (вакансия 1)", "role": "assistant", "position": "Ассистент", "status": "вакансия", "email": "", "phone": "", "password": "password"},
    {"full_name": "Ассистент (вакансия 2)", "role": "assistant", "position": "Ассистент", "status": "вакансия", "email": "", "phone": "", "password": "password"},
    {"full_name": "Ассистент (вакансия 3)", "role": "assistant", "position": "Ассистент", "status": "вакансия", "email": "", "phone": "", "password": "password"},
]

# (Не забудь — если staff уже есть, можно сначала очистить коллекцию:)
db.staff.delete_many({})
db.staff.insert_many(staff_list)

print("Сотрудники добавлены!")
