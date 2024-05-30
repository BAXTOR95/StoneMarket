from app import app, db
from flask_migrate import upgrade

with app.app_context():
    db.create_all()
    upgrade()
