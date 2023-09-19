import os

from demo.models.models import db
from flask.app import Flask

app = Flask(__name__)

db_path = os.path.abspath(os.path.join(__file__, "..", "..", "..", "..", "db.sql"))
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"


def create_all():
    with app.app_context():
        db.init_app(app)
        db.create_all()
