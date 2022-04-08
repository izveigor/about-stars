from tests.helpers import LIVE_SERVER_URL, get_element_by_id, create_data_for_test, JsonData, input_points
from selenium.webdriver.common.keys import Keys
import time


class TestSearchSegment:
    def test_search(self, browser):
        create_data_for_test()
        browser.get(LIVE_SERVER_URL)
        get_element_by_id("points_search", browser).click()
        points = JsonData.is_polygon_contains_point['points']

        input_points(points, browser)

        get_element_by_id("search_points_button", browser).click()
    
        testing_data = JsonData.segment_search_frontend
        minimum_input = get_element_by_id("minimum_input", browser)
        maximum_input = get_element_by_id("maximum_input", browser)

        browser.execute_script('document.getElementById("minimum_input").removeAttribute("value");')
        browser.execute_script('document.getElementById("maximum_input").removeAttribute("value");')

        minimum_input = get_element_by_id("minimum_input", browser)
        maximum_input = get_element_by_id("maximum_input", browser)
        for counter, (name, inputs) in enumerate(testing_data.items(), start=1):
            if counter != 1: 
                get_element_by_id(name, browser).click()
            for input_ in inputs:
                minimum_input.send_keys(input_["input"]["minimum"])
                maximum_input.send_keys(input_["input"]["maximum"], Keys.TAB)

                time.sleep(1)
                assert int(get_element_by_id("segment_number_of_stars", browser).text) == input_["result"]["sum"]
                assert get_element_by_id("minimum", browser).text == input_["result"]["minimum"]
                assert get_element_by_id("maximum", browser).text == input_["result"]["maximum"]

                minimum_input.clear()
                maximum_input.clear()
        