import threading

import pytest
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from werkzeug.serving import make_server

from starapp import create_app
from starapp.constants import PORT, SERVER

from models import db  # isort:skip

firefox_options = Options()
firefox_options.headless = True


@pytest.fixture()  # type: ignore
def browser() -> webdriver.Firefox:
    app = create_app("TESTING")
    db.create_all()

    browser: webdriver.Firefox = webdriver.Firefox(options=firefox_options)
    s = make_server(SERVER, PORT, app)
    t = threading.Thread(target=s.serve_forever)
    t.start()
    yield browser
    browser.quit()

    s.shutdown()
    t.join()

    with app.app_context():
        db.session.remove()
        db.drop_all()
