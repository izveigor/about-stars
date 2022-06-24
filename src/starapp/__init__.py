import os

from flask import Flask
from flask_cors import CORS
from flask_migrate import Migrate

from models import db

from .api import bp_cli
from .constants import POSTGRESQL_SETTINGS, SERVER, SERVER_URL
from .views import bp_views


def create_app(config: str = "PRODUCTION") -> Flask:
    app = Flask(__name__)
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY")
    if SERVER:
        app.config["SERVER_NAME"] = SERVER_URL
    app.config["TESTING"] = True if config == "TESTING" else False
    app.app_context().push()
    db.init_app(app)
    CORS(app)
    app.register_blueprint(bp_views)
    app.register_blueprint(bp_cli)
    app.config[
        "SQLALCHEMY_DATABASE_URI"
    ] = f'postgresql://{POSTGRESQL_SETTINGS["POSTGRES_USER"]}:{POSTGRESQL_SETTINGS["POSTGRES_PASSWORD"]}@{POSTGRESQL_SETTINGS["POSTGRES_HOST"]}:{POSTGRESQL_SETTINGS["POSTGRES_PORT"]}/{POSTGRESQL_SETTINGS["POSTGRES_DB"]}'
    if config != "TESTING":
        migrate = Migrate()
        migrate.init_app(app, db)
    return app
