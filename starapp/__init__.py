from flask import Flask
from models import db
from .api import bp_cli
from .views import bp_views
from flask_migrate import Migrate
from .constants import SERVER_URL, SERVER, POSTGRESQL_SETTINGS
from flask_cors import CORS


def create_app(config="PRODUCTION"):
    app = Flask(__name__)
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SECRET_KEY"] = "secret!"
    app.config["SERVER_NAME"] = SERVER_URL
    app.config["TESTING"] = True if config == "TESTING" else False
    app.app_context().push()
    db.init_app(app)
    CORS(app)
    app.register_blueprint(bp_views)
    app.register_blueprint(bp_cli)
    if config != "TESTING":
        app.config[
            "SQLALCHEMY_DATABASE_URI"
        ] = f'postgresql://{POSTGRESQL_SETTINGS["POSTGRES_USER"]}:{POSTGRESQL_SETTINGS["POSTGRES_PASSWORD"]}@db:5432/{POSTGRESQL_SETTINGS["POSTGRES_DB"]}'
        migrate = Migrate()
        migrate.init_app(app, db)
    else:
        app.config[
            "SQLALCHEMY_DATABASE_URI"
        ] = f'postgresql://{POSTGRESQL_SETTINGS["POSTGRES_USER"]}:{POSTGRESQL_SETTINGS["POSTGRES_PASSWORD"]}@localhost:5432/{POSTGRESQL_SETTINGS["POSTGRES_DB"]}'
    return app
