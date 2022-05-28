from typing import Any
from unittest.mock import patch

import pytest
from fakeredis import FakeStrictRedis
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from sqlalchemy import text

from models import db
from starapp.constants import (
    ERROR_CONSTELLATION_DOES_NOT_EXIST,
    ERROR_IS_POINTS_RANGE_VALID,
    ERROR_NOT_ENOUGH_POINTS,
)
from tests.helpers import (
    LIVE_SERVER_URL,
    JsonData,
    create_data_for_test,
    get_element_by_id,
    input_points,
)


def check_fields_search_statistics(
    testing_data: Any, browser: webdriver.Firefox
) -> None:
    for type_of_data in ("catalogs", "constellations", "spects"):
        table = get_element_by_id(type_of_data, browser)
        for row, testing_row in zip(
            table.find_elements(By.TAG_NAME, "tr"), testing_data[type_of_data]
        ):
            first_field, percentage = [
                td.text for td in row.find_elements(By.TAG_NAME, "td")
            ]
            testing_percentage, testing_first_field = list(testing_row.values())
            assert first_field == testing_first_field
            assert percentage == str(testing_percentage) + "%"


@patch("starapp.algorithms.redis.StrictRedis", FakeStrictRedis)
class TestInputs:
    def test_change(self, browser: webdriver.Firefox) -> None:
        CONSTELLATION_SEARCH_TITLE = "Search with constellation:"
        CONSTELLATION_SEARCH_DESCRIPTION = "Input tag of constellation (for example ori (Orion)) and we will see the statistics about this constellation!"
        POINTS_SEARCH_TITLE = "Search with points:"
        POINTS_SEARCH_DESCRIPTION = "Add points and the server will build a convex polygon for these points. We will see statistics about stars in the polygon."

        browser.get(LIVE_SERVER_URL)
        constellation_search = get_element_by_id("constellation_search", browser)
        points_search = get_element_by_id("points_search", browser)

        assert "active" in constellation_search.get_attribute("class")
        assert "active" not in points_search.get_attribute("class")
        with pytest.raises(TimeoutException):
            get_element_by_id("add_points_button", browser)
        assert get_element_by_id("search_constellation_button", browser)
        assert (
            get_element_by_id("search_title", browser).text
            == CONSTELLATION_SEARCH_TITLE
        )
        assert (
            get_element_by_id("search_description", browser).text
            == CONSTELLATION_SEARCH_DESCRIPTION
        )

        points_search.click()

        assert "active" not in constellation_search.get_attribute("class")
        assert "active" in points_search.get_attribute("class")
        assert get_element_by_id("add_points_button", browser)
        with pytest.raises(TimeoutException):
            get_element_by_id("search_constellation_button", browser)
        assert get_element_by_id("search_title", browser).text == POINTS_SEARCH_TITLE
        assert (
            get_element_by_id("search_description", browser).text
            == POINTS_SEARCH_DESCRIPTION
        )

        constellation_search.click()

        assert "active" in constellation_search.get_attribute("class")
        assert "active" not in points_search.get_attribute("class")
        with pytest.raises(TimeoutException):
            get_element_by_id("add_points_button", browser)
        assert get_element_by_id("search_constellation_button", browser)
        assert (
            get_element_by_id("search_title", browser).text
            == CONSTELLATION_SEARCH_TITLE
        )
        assert (
            get_element_by_id("search_description", browser).text
            == CONSTELLATION_SEARCH_DESCRIPTION
        )

    def test_search_constellation(self, browser: webdriver.Firefox) -> None:
        create_data_for_test()
        tag = JsonData.constellation["tag"]
        testing_data = JsonData.get_data_from_constellation_frontend
        db.session.execute(
            text(
                f"""
            CREATE VIEW stars_with_{tag} AS
                SELECT * FROM star WHERE con='{tag}';
        """
            )
        )
        db.session.commit()

        browser.get(LIVE_SERVER_URL)
        get_element_by_id("constellation_input", browser).send_keys(tag)
        get_element_by_id("search_constellation_button", browser).click()

        assert (
            get_element_by_id("search_statistics", browser).value_of_css_property(
                "display"
            )
            == "flex"
        )
        assert (
            get_element_by_id("search_actions", browser).value_of_css_property(
                "display"
            )
            == "flex"
        )

        check_fields_search_statistics(testing_data, browser)

        db.session.execute(
            text(
                f"""
            DROP VIEW stars_with_{tag};
        """
            )
        )
        db.session.commit()

    def test_input_points(self, browser: webdriver.Firefox) -> None:
        create_data_for_test()
        browser.get(LIVE_SERVER_URL)
        get_element_by_id("points_search", browser).click()
        points = JsonData.is_polygon_contains_point["points"]

        ra_input = get_element_by_id("ra_input", browser)
        dec_input = get_element_by_id("dec_input", browser)
        add_points_button = get_element_by_id("add_points_button", browser)

        input_points(points, browser)

        element_points = get_element_by_id("points", browser)
        for row, point in zip(element_points.find_elements(By.TAG_NAME, "tr"), points):
            ra, dec = [td for td in row.find_elements(By.TAG_NAME, "td")]
            assert ra == "Ra: " + str(point["ra"])
            assert dec == "Dec: " + str(point["dec"])

        assert (
            get_element_by_id("clear_points", browser).value_of_css_property("display")
            == "block"
        )
        assert (
            get_element_by_id("search_points_button", browser).value_of_css_property(
                "display"
            )
            == "block"
        )

        get_element_by_id("clear_points", browser).click()

        element_points = get_element_by_id("points", browser)
        assert element_points.text == ""
        assert (
            get_element_by_id("clear_points", browser).value_of_css_property("display")
            == "none"
        )
        assert (
            get_element_by_id("search_points_button", browser).value_of_css_property(
                "display"
            )
            == "none"
        )

        input_points(points, browser)
        assert (
            get_element_by_id("search_points_button", browser).value_of_css_property(
                "display"
            )
            == "block"
        )
        get_element_by_id("search_points_button", browser).click()

        testing_data = JsonData.get_data_with_points_frontend
        check_fields_search_statistics(testing_data, browser)

    def test_with_not_existing_constellation(self, browser: webdriver.Firefox) -> None:
        create_data_for_test()
        browser.get(LIVE_SERVER_URL)

        get_element_by_id("constellation_input", browser).send_keys("It's not exist!")
        get_element_by_id("search_constellation_button", browser).click()

        assert (
            get_element_by_id("error", browser).text
            == ERROR_CONSTELLATION_DOES_NOT_EXIST
        )

    def test_is_points_range_valid(self, browser: webdriver.Firefox) -> None:
        browser.get(LIVE_SERVER_URL)
        get_element_by_id("points_search", browser).click()

        points = [{"ra": 33, "dec": 56}, {"ra": 15, "dec": 56}, {"ra": 15, "dec": 56}]
        input_points(points, browser)  # type: ignore
        get_element_by_id("search_points_button", browser).click()

        assert get_element_by_id("error", browser).text == ERROR_IS_POINTS_RANGE_VALID

    def test_error_not_enough_points(self, browser: webdriver.Firefox) -> None:
        browser.get(LIVE_SERVER_URL)
        get_element_by_id("points_search", browser).click()

        points = [{"ra": 15, "dec": 56}, {"ra": 10, "dec": -34}]
        input_points(points, browser)  # type: ignore
        get_element_by_id("search_points_button", browser).click()

        assert get_element_by_id("error", browser).text == ERROR_NOT_ENOUGH_POINTS
