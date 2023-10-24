from demo.forest_admin.agent import customize_agent
from demo.models.models import db
from flask import Flask
from flask_cors import CORS
from forestadmin.datasource_sqlalchemy.datasource import SqlAlchemyDatasource
from forestadmin.flask_agent.agent import create_agent


def create_app():
    app = Flask(__name__)
    app.config.from_object("demo.config.FlaskConfig")

    CORS(
        app,
        resources={
            r"/forest/*": {"origins": r".*\.forestadmin\.com.*"},
        },
        supports_credentials=True,
    )
    agent = create_agent(app)
    with app.app_context():
        db.init_app(app)
        # agent.add_datasource(SqlAlchemyDatasource(db, db_uri=app.config["SQLALCHEMY_DATABASE_URI"]))
        agent.add_datasource(SqlAlchemyDatasource(db))
    customize_agent(agent)
    agent.start()
    return app
