
from db import db
import os

def init_db(app):
    db_file = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')

    if not os.path.exists(db_file):
        print("Creating database...")

        with app.app_context():
            db.create_all()

        print("Database created!")
    else:
        print("Database already exists!")
