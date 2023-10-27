from demo.forest_admin.agent import customize_agent
from demo.models.models import SQLITE_URI, Base
from flask import Flask
from flask_cors import CORS
from forestadmin.datasource_sqlalchemy.datasource import SqlAlchemyDatasource
from forestadmin.flask_agent.agent import build_agent


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
    agent = build_agent(app)
    agent.add_datasource(SqlAlchemyDatasource(Base, SQLITE_URI))
    customize_agent(agent)
    agent.start()
    return app


app = create_app()
