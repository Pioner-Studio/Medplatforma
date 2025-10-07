from main import db

updates = [
    ("Гогуева Алина Темурлановна", "gogueva.jpg"),
    ("Миргатия Ольга Сергеевна", "mirgatiya.jpg"),
    ("Курдов Кадыр Мурадович", "kurdov.jpg"),
    ("Айвазян Альберт Гагикович", "ayvazyan.jpg"),
    ("Калачев Алексей Николаевич", "kalachev.jpg"),
]

for name, avatar in updates:
    result = db.doctors.update_one(
        {"full_name": name},
        {"$set": {"avatar": avatar}}
    )
    print(f"{name}: обновлено {result.modified_count}")

print("\nПроверка:")
docs = list(db.doctors.find({}, {"full_name": 1, "avatar": 1}))
for d in docs:
    print(f"{d.get('full_name')}: {d.get('avatar', 'НЕТ')}")
