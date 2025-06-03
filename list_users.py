from app import create_app
from app.extensions import db
from app.models.user import User

app = create_app()

with app.app_context():
    users = User.query.all()
    print('Current users in the database:')
    for user in users:
        print(f'ID: {user.id}, Name: {user.first_name} {user.last_name}, Username: {user.username}, Email: {user.email}')
