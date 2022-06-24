import pytest
from flask import Flask
from flask.testing import FlaskClient, FlaskCliRunner

from models import db
from starapp import create_app


@pytest.fixture()  # type: ignore
def testing_app() -> Flask:
    app: Flask = create_app("TESTING")
    db.create_all()
    yield app

    with app.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture()  # type: ignore
def client(testing_app: Flask) -> FlaskClient:
    return testing_app.test_client()


@pytest.fixture()  # type: ignore
def runner(testing_app: Flask) -> FlaskCliRunner:
    return testing_app.test_cli_runner()
