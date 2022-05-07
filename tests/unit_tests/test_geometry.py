from starapp.geometry import (
    is_points_range_valid,
    is_polygon_contains_point,
    Graham_scan,
)
from tests.helpers import JsonData


class TestGeometry:
    def test_is_polygon_contains_point(self, client):
        testing_data = JsonData.is_polygon_contains_point
        data_about_stars = JsonData.data_after_api

        for ra, dec, result in zip(
            data_about_stars["ra"], data_about_stars["dec"], testing_data["result"]
        ):
            assert is_polygon_contains_point(testing_data["points"], ra, dec) == result

    def test_is_points_range_valid(self, client):
        testing_data = JsonData.is_points_range_valid
        for wrong_data in testing_data["points_with_wrong_range"]:
            assert is_points_range_valid(wrong_data) == False

        for right_data in testing_data["points_with_right_range"]:
            assert is_points_range_valid(right_data) == True

    def test_Graham_scan(self, client):
        data_after_api = JsonData.data_after_api
        testing_data = [
            {
                "ra": ra,
                "dec": dec,
            }
            for ra, dec in zip(data_after_api["ra"], data_after_api["dec"])
        ]
        assert Graham_scan(testing_data) == JsonData.Graham_scan
