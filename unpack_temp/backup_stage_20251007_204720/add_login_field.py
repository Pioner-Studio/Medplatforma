from main import db

users = ['kurdov', 'gogueva', 'nakonechny', 'nakonechnaya', 'ayvazyan', 'kalachev', 'mirgatiya']

for username in users:
    result = db.users.update_one(
        {'username': username},
        {'$set': {'login': username}}
    )
    if result.matched_count > 0:
        print(f'Добавлено поле login для {username}')
    else:
        print(f'Не найден {username}')
