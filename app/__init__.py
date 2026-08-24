import os
from flask import Flask
from dotenv import load_dotenv

from app.db import close_db
from app.routes import bp

load_dotenv()


def create_app() -> Flask:
    app = Flask(__name__)
    
    app.config["SECRET_KEY"] = os.environ["SECRET_KEY"]

    app.register_blueprint(bp)
    app.teardown_appcontext(close_db)
    return app
