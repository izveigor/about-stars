from tests.helpers import JsonData, create_data_for_test
from models import db, Constellation
from sqlalchemy import text
from starapp.algorithms import Search
from starapp.constants import (
    ERROR_IS_POINTS_RANGE_VALID,
    ERROR_NOT_ENOUGH_POINTS,
    ERROR_CONSTELLATION_DOES_NOT_EXIST,
    REDIS_SETTINGS,
)
import json
from collections import Counter
from starapp.views import (
    _counter_with_percentage,
    _result_from_stars_with_constellation_to_dict,
    TypeSearch,
    get_hash,
)
from unittest.mock import patch, call
from flask import jsonify


@patch("starapp.views.render_template")
class TestMainAndAbout:
    def test_main(self, mock_render_template, client):
        mock_render_template.return_value = jsonify()
        client.get("/")
        mock_render_template.assert_called_once_with("index.html")

    def test_about(self, mock_render_template, client):
        mock_render_template.return_value = jsonify()
        client.get("/about")
        mock_render_template.assert_called_once_with("about.html")


class TestDeleteAll:
    @patch("starapp.views.Search.clear")
    def test_delete(self, mock_search_clear, client):
        random_hash = "random_hash"
        with client.session_transaction() as session:
            session["request"] = random_hash

        client.get("/delete_all")

        mock_search_clear.assert_called_once_with(hash_=random_hash)
        with client.session_transaction() as session:
            assert session.get("request") is None
        Search.clear(hash_=random_hash)


class TestGetDataFromConstellation:
    @patch("starapp.views.Search.__init__")
    @patch("starapp.views.get_hash")
    @patch("starapp.views._result_from_stars_with_constellation_to_dict")
    def test_get(
        self,
        mock_result_from_stars_with_constellation_to_dict,
        mock_hash,
        mock_search,
        client,
    ):
        create_data_for_test()
        constellation = JsonData.constellation

        db.session.execute(
            text(
                f"""
            CREATE VIEW stars_with_{constellation['tag']} AS
                SELECT * FROM star WHERE con='{constellation['tag']}';
        """
            )
        )
        db.session.commit()

        result_from_stars_with_constellation = [JsonData.star]
        random_hash = "random_hash"

        mock_result_from_stars_with_constellation_to_dict.return_value = (
            result_from_stars_with_constellation,
            1,
        )
        mock_hash.return_value = random_hash
        mock_search.return_value = None

        response = client.post(
            "/search_constellation",
            data=json.dumps(constellation),
            content_type="application/json",
        )

        mock_search.assert_has_calls(
            [
                call(
                    random_hash, type_search, stars=result_from_stars_with_constellation
                )
                for type_search in TypeSearch
            ]
        )

        with client.session_transaction() as session:
            assert session["request"] == random_hash

        db.session.execute(
            text(
                f"""
            DROP VIEW stars_with_{constellation['tag']} CASCADE;
        """
            )
        )
        db.session.commit()

        assert JsonData.get_data_from_constellation == response.data.decode("utf-8")
        Search.clear(hash_=random_hash)

    @patch("starapp.views.Search.clear")
    @patch("starapp.views.Search.__init__")
    @patch("starapp.views.get_hash")
    @patch("starapp.views._result_from_stars_with_constellation_to_dict")
    def test_clear_session(
        self,
        mock_result_from_stars_with_constellation_to_dict,
        mock_hash,
        mock_search,
        mock_search_clear,
        client,
    ):
        create_data_for_test()
        constellation = JsonData.constellation

        db.session.execute(
            text(
                f"""
            CREATE VIEW stars_with_{constellation['tag']} AS
                SELECT * FROM star WHERE con='{constellation['tag']}';
        """
            )
        )
        db.session.commit()

        old_hash = "old_hash"
        new_hash = "new_hash"
        with client.session_transaction() as session:
            session["request"] = old_hash

        mock_result_from_stars_with_constellation_to_dict.return_value = (None, None)
        mock_hash.return_value = new_hash
        mock_search.return_value = None

        client.post(
            "/search_constellation",
            data=json.dumps(constellation),
            content_type="application/json",
        )

        mock_search_clear.assert_called_once_with(hash_=old_hash)
        with client.session_transaction() as session:
            assert session.get("request") == new_hash

        db.session.execute(
            text(
                f"""
            DROP VIEW stars_with_{constellation['tag']} CASCADE;
        """
            )
        )
        db.session.commit()

    def test_result_from_stars_with_constellation_to_dict(self, client):
        create_data_for_test()
        constellation = JsonData.constellation
        db.session.execute(
            text(
                f"""
            CREATE VIEW stars_with_{constellation['tag']} AS
                SELECT * FROM star WHERE con='{constellation['tag']}';
        """
            )
        )
        db.session.commit()
        assert _result_from_stars_with_constellation_to_dict(constellation["tag"]) == (
            [JsonData.star],
            1,
        )
        db.session.execute(
            text(
                f"""
            DROP VIEW stars_with_{constellation['tag']};
        """
            )
        )
        db.session.commit()

    def test_with_not_existing_constellation(self, client):
        create_data_for_test()
        response = client.post(
            "/search_constellation",
            data=json.dumps({"tag": "It's not exist!"}),
            content_type="application/json",
        )
        assert (
            f'{{"error":"{ERROR_CONSTELLATION_DOES_NOT_EXIST}"}}\n'
            == response.data.decode("utf-8")
        )

    @patch("starapp.views.random.randint")
    def test_get_hash(self, mock_random_randint, client):
        hash_ = "a0e7f02206e3a9ab50ee8994157b648fd3576d8dcca3dab8b74d68e88e1d7120"
        mock_random_randint.side_effect = [
            10,
            0,
            14,
            7,
            15,
            0,
            2,
            2,
            0,
            6,
            14,
            3,
            10,
            9,
            10,
            11,
            5,
            0,
            14,
            14,
            8,
            9,
            9,
            4,
            1,
            5,
            7,
            11,
            6,
            4,
            8,
            15,
            13,
            3,
            5,
            7,
            6,
            13,
            8,
            13,
            12,
            12,
            10,
            3,
            13,
            10,
            11,
            8,
            11,
            7,
            4,
            13,
            6,
            8,
            14,
            8,
            8,
            14,
            1,
            13,
            7,
            1,
            2,
            0,
        ]
        assert get_hash() == hash_


class TestGetDataWithPoints:
    @patch("starapp.views.Search.__init__")
    @patch("starapp.views.get_hash")
    def test_get(self, mock_get_hash, mock_search, client):
        create_data_for_test()
        testing_data = JsonData.get_data_with_points

        random_hash = "random_hash"
        mock_get_hash.return_value = random_hash
        mock_search.return_value = None

        response = client.post(
            "/search_points",
            data=json.dumps(testing_data["points"]),
            content_type="application/json",
        )

        mock_search.assert_has_calls(
            [
                call(random_hash, type_search, stars=testing_data["stars"])
                for type_search in TypeSearch
            ]
        )

        with client.session_transaction() as session:
            assert session["request"] == random_hash

        assert testing_data["result"] == response.data.decode("utf-8")
        Search.clear(hash_=random_hash)

    @patch("starapp.views.Search.clear")
    @patch("starapp.views.Search.__init__")
    @patch("starapp.views.get_hash")
    def test_clear_session(self, mock_get_hash, mock_search, mock_search_clear, client):
        create_data_for_test()
        testing_data = JsonData.get_data_with_points

        old_hash = "old_hash"
        new_hash = "new_hash"
        mock_get_hash.return_value = new_hash
        mock_search.return_value = None

        with client.session_transaction() as session:
            session["request"] = old_hash

        client.post(
            "/search_points",
            data=json.dumps(testing_data["points"]),
            content_type="application/json",
        )

        mock_search_clear.assert_called_once_with(hash_=old_hash)
        with client.session_transaction() as session:
            assert session.get("request") == new_hash

    def test_counter_with_percentage(self, client):
        testing_data = JsonData.counter_with_percentage
        result = _counter_with_percentage(Counter(testing_data["data"]), "tag")
        assert result == testing_data["result"]

    def test_points_must_be_list(self, client):
        response = client.post(
            "/search_points", data=json.dumps(43), content_type="application/json"
        )
        assert response.status_code == 400

    def test_points_must_contain_dictionaries(self, client):
        response = client.post(
            "/search_points", data=json.dumps([15]), content_type="application/json"
        )
        assert response.status_code == 400

    def test_points_must_contain_ra_and_dec_attributes(self, client):
        response = client.post(
            "/search_points",
            data=json.dumps([{"ra": 15}]),
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_is_points_range_valid(self, client):
        response = client.post(
            "/search_points",
            data=json.dumps(
                [{"ra": 33, "dec": 56}, {"ra": 15, "dec": 56}, {"ra": 15, "dec": 56}]
            ),
            content_type="application/json",
        )
        assert f'{{"error":"{ERROR_IS_POINTS_RANGE_VALID}"}}\n' == response.data.decode(
            "utf-8"
        )

    def test_error_not_enough_points(self, client):
        response = client.post(
            "/search_points",
            data=json.dumps([{"ra": 15, "dec": 56}, {"ra": 10, "dec": -34}]),
            content_type="application/json",
        )
        assert f'{{"error":"{ERROR_NOT_ENOUGH_POINTS}"}}\n' == response.data.decode(
            "utf-8"
        )


class TestSegmentSearch:
    @patch("starapp.views.Search.segment_search")
    @patch("starapp.views.Search.__init__")
    def test_segment_search(self, mock__init__, mock_segment_search, client):
        mock__init__.return_value = None
        testing_data = JsonData.segment_search
        mock_segment_search.side_effect = [
            search_segment["result"] for search_segment in testing_data
        ]
        with client.session_transaction() as session:
            session["request"] = "random_hash"

        for data, result in zip(testing_data, JsonData.views_search_segment_result):
            response = client.post(
                "/segment_search",
                data=json.dumps({"type": "dist", **data["input"]}),
                content_type="application/json",
            )
            assert response.data.decode("utf-8") == result

    def test_hash_is_none(self, client):
        input_ = JsonData.segment_search[0]["input"]
        response = client.post(
            "/segment_search",
            data=json.dumps({"type": "dist", **input_}),
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_error_type(self, client):
        with client.session_transaction() as session:
            session["request"] = "random_hash"

        input_ = JsonData.segment_search[0]["input"]
        response = client.post(
            "segment_search",
            data=json.dumps({"type": "wrong_type", **input_}),
            content_type="application/json",
        )
        assert response.status_code == 400


class TestSortSearch:
    @patch("starapp.views.Search.sort_search")
    @patch("starapp.views.Search.__init__")
    def test_sort(self, mock__init__, mock_sort_search, client):
        mock__init__.return_value = None
        mock_sort_search.side_effect = JsonData.algorithms_search_sort_result
        with client.session_transaction() as session:
            session["request"] = "random_hash"

        for testing_data, testing_result in zip(
            JsonData.sort_search, JsonData.views_search_sort_result
        ):
            response = client.post(
                "/sort_search",
                data=json.dumps(testing_data["input"]),
                content_type="application/json",
            )
            assert testing_result == response.data.decode("utf-8")

    def test_error_type(self, client):
        with client.session_transaction() as session:
            session["request"] = "random_hash"

        input_ = JsonData.sort_search[0]["input"]
        input_.pop("type")
        response = client.post(
            "/sort_search",
            data=json.dumps({"type": "wrong_type", **input_}),
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_hash_is_none(self, client):
        input_ = JsonData.sort_search[0]["input"]
        response = client.post(
            "/sort_search", data=json.dumps(input_), content_type="application/json"
        )
        assert response.status_code == 400
