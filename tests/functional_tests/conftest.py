import pytest
from starapp import create_app
from models import db
from selenium.webdriver.firefox.options import Options
from selenium import webdriver
from starapp import create_app
import threading
from werkzeug.serving import make_server
from starapp.constants import SERVER, PORT


firefox_options = Options()
firefox_options.headless = True


@pytest.fixture()
def browser():
    app = create_app('TESTING')
    db.create_all()

    browser = webdriver.Firefox(options=firefox_options)
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
