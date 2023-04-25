from demo.forestadmin.agent import agent
from flask import Flask
from flask_cors import CORS


app = Flask(__name__)
CORS(
    app,
    resources={
        r"/forest/*": {"origins": r".*\.forestadmin\.com.*"},
    },
    allow_headers=[
        "accept",
        "accept-encoding",
        "authorization",
        "content-type",
        "dnt",
        "origin",
        "user-agent",
        "x-csrftoken",
        "x-requested-with",
        "forest-context-url",
    ],
    expose_headers=["Content-Disposition"],
    supports_credentials=True,
)

agent.register_blueprint(app)
agent.loop.run_until_complete(agent.start())
