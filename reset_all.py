from main import db
from werkzeug.security import generate_password_hash

users = [
    ('kurdov', 'dental123'),
    ('gogueva', 'summer2025'),
    ('nakonechny', 'director2025'),
    ('nakonechnaya', 'clinic2025'),
    ('ayvazyan', 'dental123'),
    ('kalachev', 'ortodont789'),
    ('mirgatiya', 'child2025')
]

for username, password in users:
    hashed = generate_password_hash(password)
    result = db.users.update_one(
        {'username': username},
        {'$set': {'password': hashed}}
    )
    if result.matched_count > 0:
        print(f'Обновлён {username}')
    else:
        print(f'Не найден {username}')
