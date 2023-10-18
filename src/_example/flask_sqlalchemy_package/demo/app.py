import os

from demo.forest_admin.agent import customize_agent
from demo.forest_admin.settings import SETTINGS
from demo.models.models import db
from flask import Flask
from flask_cors import CORS
from forestadmin.datasource_sqlalchemy.datasource import SqlAlchemyDatasource
from forestadmin.flask_agent.agent import create_agent


def create_app():
    app = Flask(__name__)

    db_path = os.path.abspath(os.path.join(__file__, "..", "..", "db.sql"))

    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"

    CORS(
        app,
        resources={
            r"/forest/*": {"origins": r".*\.forestadmin\.com.*"},
        },
        supports_credentials=True,
    )
    agent = create_agent(SETTINGS)
    with app.app_context():
        db.init_app(app)

        # agent.add_datasource(SqlAlchemyDatasource(db, db_uri=app.config["SQLALCHEMY_DATABASE_URI"]))
        agent.add_datasource(SqlAlchemyDatasource(db))

    customize_agent(agent)
    agent.register_blueprint(app)
    return app
