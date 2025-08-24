# seed_services.py
# Сидируем базовые услуги в коллекцию "services"

from models.services import services

default_services = [
    {"code": "SVC001", "name": "Приём терапевта", "price": 1500},
    {"code": "SVC002", "name": "Рентген зуба", "price": 1200},
    {"code": "SVC003", "name": "Чистка зубов", "price": 2500},
    {"code": "SVC004", "name": "Удаление зуба", "price": 3500}
]

if __name__ == "__main__":
    services.delete_many({})  # очищаем коллекцию
    services.insert_many(default_services)
    print(f"✅ Засеяно {len(default_services)} услуг в коллекцию 'services'")
