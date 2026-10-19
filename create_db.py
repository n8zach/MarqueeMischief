from flask_app import app
from flask_migrate import upgrade

with app.app_context():
    upgrade()
