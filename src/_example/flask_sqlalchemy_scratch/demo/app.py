from demo.forest_admin.agent import agent
from flask import Flask
from flask_cors import CORS

app = Flask(__name__)
CORS(
    app,
    resources={
        r"/forest/*": {"origins": r".*\.forestadmin\.com.*"},
    },
    supports_credentials=True,
)

agent.register_blueprint(app)
