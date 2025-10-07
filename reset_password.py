from main import db
db.users.update_one({'username': 'kurdov'}, {'$set': {'password': 'ortoped456'}})
print('Password reset for kurdov')
