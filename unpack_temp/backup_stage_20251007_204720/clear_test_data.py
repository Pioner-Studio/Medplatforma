from main import db
from datetime import datetime

print("=" * 60)
print("СКРИПТ ПОЛНОЙ ОЧИСТКИ ТЕСТОВЫХ ДАННЫХ")
print("=" * 60)
print()
print("БУДУТ УДАЛЕНЫ:")
print(f"  - Пациенты: {db.patients.count_documents({})}")
print(f"  - Финансы (ledger): {db.ledger.count_documents({})}")
print(f"  - Записи (appointments): {db.appointments.count_documents({})}")
print(f"  - Бонусы (bonus_history): {db.bonus_history.count_documents({})}")
print(f"  - Счетчики (counters): {db.counters.count_documents({})}")
print()
print("ОСТАНУТСЯ БЕЗ ИЗМЕНЕНИЙ:")
print(f"  - Врачи (doctors): {db.doctors.count_documents({})}")
print(f"  - Услуги (services): {db.services.count_documents({})}")
print(f"  - Кабинеты (rooms): {db.rooms.count_documents({})}")
print(f"  - Кассы (cashboxes): {db.cashboxes.count_documents({})} - балансы обнулятся")
print()
print("=" * 60)
confirm = input("Введите YES для подтверждения удаления: ")

if confirm != "YES":
    print("Отменено")
    exit()

print()
print("Удаление данных...")

# Очистка пациентов
r1 = db.patients.delete_many({})
print(f"✓ Удалено пациентов: {r1.deleted_count}")

# Очистка финансов
r2 = db.ledger.delete_many({})
print(f"✓ Удалено финансовых операций: {r2.deleted_count}")

# Очистка записей
r3 = db.appointments.delete_many({})
print(f"✓ Удалено записей: {r3.deleted_count}")

# Очистка бонусов
r4 = db.bonus_history.delete_many({})
print(f"✓ Удалено бонусных операций: {r4.deleted_count}")

# Сброс счетчиков
r5 = db.counters.delete_many({})
print(f"✓ Удалено счетчиков: {r5.deleted_count}")

# Обнуление балансов касс
r6 = db.cashboxes.update_many({}, {"$set": {"balance": 0, "updated_at": datetime.utcnow()}})
print(f"✓ Обнулено балансов касс: {r6.modified_count}")

print()
print("=" * 60)
print("ОЧИСТКА ЗАВЕРШЕНА")
print("=" * 60)
print()
print("ТЕКУЩЕЕ СОСТОЯНИЕ БАЗЫ:")
print(f"  Пациентов: {db.patients.count_documents({})}")
print(f"  Финансов: {db.ledger.count_documents({})}")
print(f"  Записей: {db.appointments.count_documents({})}")
print(f"  Бонусов: {db.bonus_history.count_documents({})}")
print(f"  Врачей: {db.doctors.count_documents({})}")
print(f"  Услуг: {db.services.count_documents({})}")
print(f"  Кабинетов: {db.rooms.count_documents({})}")
