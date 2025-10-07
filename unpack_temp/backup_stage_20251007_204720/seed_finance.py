from datetime import datetime, timedelta
from pymongo import MongoClient

client = MongoClient("mongodb+srv://medadmin:medpass123@medplatforma.cnv7fbo.mongodb.net/")
db = client['medplatforma']

ops = []
start_date = datetime(2025, 1, 1)
doctors = ['Д-р Иванов Александр', 'Д-р Сидоров Алексей']
patients = ['Смирнова Елена', 'Петров Сергей', 'Васильева Мария', 'Козлова Ольга']
services = ['Консультация', 'Чистка зубов', 'Рентген', 'Лечение', 'Удаление зуба']
types = ['Доход', 'Расход']
status = ['оплачен', 'отменён', 'новый']

for i in range(1, 50):
    dt = start_date + timedelta(days=i*3)
    op = {
        'date': dt.strftime('%d.%m.%Y'),
        'doctor': doctors[i % 2],
        'patient': patients[i % 4],
        'service': services[i % 5],
        'type': types[i % 2],
        'amount': 1000 * (i % 5 + 2),
        'status': status[i % 3],
        'comment': f"Комментарий к операции {i}"
    }
    ops.append(op)

db.finance.delete_many({})
db.finance.insert_many(ops)
print("Демо-операции для финотчёта добавлены!")
