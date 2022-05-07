from tests.helpers import (
    LIVE_SERVER_URL,
    get_element_by_id,
    create_data_for_test,
    JsonData,
    input_points,
)
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
import time


class TestSort:
    def test_sort(self, browser):
        create_data_for_test()
        browser.get(LIVE_SERVER_URL)
        browser.set_window_size(1500, 600)
        testing_data = JsonData.sort_search_frontend
        get_element_by_id("points_search", browser).click()
        points = testing_data["points"]

        input_points(points, browser)

        get_element_by_id("search_points_button", browser).click()

        minimum_input = get_element_by_id("minimum_input", browser)
        maximum_input = get_element_by_id("maximum_input", browser)

        browser.execute_script(
            'document.getElementById("minimum_input").removeAttribute("value");'
        )
        browser.execute_script(
            'document.getElementById("maximum_input").removeAttribute("value");'
        )

        minimum_input = get_element_by_id("minimum_input", browser)
        maximum_input = get_element_by_id("maximum_input", browser)
        descending_input = Select(get_element_by_id("descending", browser))
        for counter, (name, input_) in enumerate(
            testing_data["input"].items(), start=0
        ):
            if counter != 0:
                browser.execute_script(
                    f'document.getElementById("{name}").scrollIntoView();'
                )
                time.sleep(1)
                get_element_by_id(name, browser).click()

            minimum_input.send_keys(Keys.BACKSPACE, input_["minimum"])
            maximum_input.send_keys(Keys.BACKSPACE, input_["maximum"], Keys.TAB)

            time.sleep(1)

            for index, sort_data in enumerate(testing_data["sort"].values(), start=0):
                browser.execute_script(
                    'document.getElementById("descending").scrollIntoView();'
                )
                time.sleep(1)
                descending_input.select_by_index(index)
                get_element_by_id("sort_search", browser).click()
                browser.execute_script(
                    'document.getElementById("new_page_button").scrollIntoView();'
                )

                time.sleep(1)
                first_sort_result = get_element_by_id("sort_result", browser)
                for row, testing_result in zip(
                    first_sort_result.find_elements(By.TAG_NAME, "tr"),
                    sort_data[name][0],
                ):
                    name_of_star, value = [
                        td.text for td in row.find_elements(By.TAG_NAME, "td")
                    ]
                    assert name_of_star == testing_result["name"]
                    assert float(value) == testing_result["value"]

                new_page_button = get_element_by_id("new_page_button", browser)
                new_page_button.click()

                second_sort_result = get_element_by_id(
                    "sort_result", browser
                ).find_elements(By.TAG_NAME, "tr")[10:]
                for new_row, testing_result in zip(
                    second_sort_result, sort_data[name][1]
                ):
                    name_of_star, value = [
                        td.text for td in new_row.find_elements(By.TAG_NAME, "td")
                    ]
                    assert name_of_star == testing_result["name"]
                    assert float(value) == testing_result["value"]

                assert new_page_button.value_of_css_property("display") == "none"

            browser.execute_script(
                'document.getElementById("minimum_input").scrollIntoView();'
            )
            time.sleep(1)
            minimum_input.clear()
            maximum_input.clear()
