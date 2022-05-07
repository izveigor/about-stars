import pytest
from starapp import create_app
from models import db


@pytest.fixture()
def testing_app():
    app = create_app("TESTING")
    db.create_all()
    yield app

    with app.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(testing_app):
    return testing_app.test_client()


@pytest.fixture()
def runner(testing_app):
    return testing_app.test_cli_runner()
