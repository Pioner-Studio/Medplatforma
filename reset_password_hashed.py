from main import db
from werkzeug.security import generate_password_hash

hashed = generate_password_hash('ortoped456')
db.users.update_one({'username': 'kurdov'}, {'$set': {'password': hashed}})
print('Password hashed and updated for kurdov')
