from demo.models.models import db
from flask.app import Flask

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///../db.sql"


def create_all():
    with app.app_context():
        db.init_app(app)
        db.create_all()
