from main import db

rooms = list(db.rooms.find({}))
for r in rooms:
    print(f"{r.get('name')} - {r['_id']}")
