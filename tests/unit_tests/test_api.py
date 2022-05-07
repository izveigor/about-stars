import pandas as pd
from unittest.mock import patch, call
from tests.helpers import (
    JsonData,
    check_model_fields,
    create_constellation_for_test,
    create_star_for_test,
    create_catalogs_for_test,
)
from starapp.api import *
from models import Catalog, Star, CatalogAssociation, Constellation, db
from starapp.constants import (
    CATALOGS,
    INT_CATALOGS,
    POINT,
    STR_CATALOGS,
    SPECT,
    OTHER_DATA,
    PATH_TO_HYGDATA_V3,
    CONSTELLATION,
    LIST_OF_CONSTELLATIONS,
)
import numpy as np
from sqlalchemy import text


class TestAddStar:
    def get_data_about_star_from_hygdata(self, hygdata, index, need_constellation=True):
        data_about_star = dict()
        for field in OTHER_DATA + POINT:
            data_about_star[field] = hygdata[field][index]
        data_about_star[SPECT] = hygdata[SPECT][index]
        data_about_star[CONSTELLATION] = (
            hygdata[CONSTELLATION][index] if need_constellation else None
        )
        data_about_star["id"] = int(hygdata["id"][index])
        return data_about_star

    @patch("starapp.api.get_api")
    def test_download_stars(self, mock_get_api, runner):
        result = runner.invoke(download_stars)
        assert (
            f'Start downloading information about stars from file "{PATH_TO_HYGDATA_V3}"'
            in result.output
        )
        assert (
            "Information about stars have successfully downloaded!\n" in result.output
        )
        mock_get_api.assert_called_once()

    def test_get_spect(self, client):
        data = pd.DataFrame.from_dict(JsonData.data_from_hygdata)
        for index, spect_data in enumerate(JsonData.data_after_api["spect"], start=0):
            assert get_spect(data.loc[index]["spect"]) == spect_data

        assert get_spect("It's not exist!") == None

    @patch("starapp.api.Manager")
    @patch("starapp.api.Pool")
    @patch("starapp.api.click.echo")
    @patch("starapp.api.click.progressbar")
    @patch("starapp.api.add_star")
    @patch("starapp.api.create_constellations")
    @patch("starapp.api.create_catalogs")
    @patch("starapp.api.pd.read_csv")
    def test_get_api(
        self,
        mock_read_csv,
        mock_create_catalogs,
        mock_create_constellations,
        mock_add_star,
        mock_progressbar,
        mock_click_echo,
        mock_pool,
        mock_manager,
        client,
    ):
        data_from_hygdata = JsonData.data_from_hygdata
        testing_data = pd.DataFrame.from_dict(data_from_hygdata)

        mock_progressbar.return_value.__enter__.return_value = range(len(testing_data))
        mock_read_csv.return_value = pd.DataFrame.from_dict(testing_data)

        def mock_pool_map(func, iterable):
            for element in iterable:
                func(element)

        mock_pool.return_value.__enter__.return_value.map = mock_pool_map
        create_catalogs_for_test()

        testing_data_for_catalogs = JsonData.data_after_api
        testing_data_catalogs = []
        testing_data_catalog_associations = dict()
        for tag in CATALOGS:
            catalog_associations = [
                CatalogAssociation(
                    **{
                        "star_id": int(testing_data_for_catalogs["id"][index]),
                        "identifier": str(testing_data_for_catalogs[tag][index]),
                        "catalog_tag": tag,
                    }
                )
                for index in range(len(testing_data))
                if testing_data_for_catalogs[tag][index] is not None
            ]
            testing_data_catalogs.extend(catalog_associations)
            testing_data_catalog_associations[tag] = catalog_associations

        mock_manager.return_value.__enter__.return_value.list.side_effect = [
            [
                Star(
                    **self.get_data_about_star_from_hygdata(
                        JsonData.data_after_api, index, False
                    )
                )
                for index in range(len(testing_data))
            ],
            testing_data_catalogs,
        ]

        get_api()

        mock_read_csv.assert_called_once_with(PATH_TO_HYGDATA_V3)
        mock_create_constellations.assert_called_once()
        mock_create_catalogs.assert_called_once()
        mock_click_echo.assert_has_calls(
            [
                call(f"\nStart downloading stars ({len(testing_data)})"),
                call("\nSaving stars in the database..."),
                call("Stars have successfully saved in the database"),
            ]
        )

        for index in range(len(mock_add_star.call_args_list)):
            for key in data_from_hygdata.keys():
                assert (
                    mock_add_star.call_args_list[index][0][2][key]
                    == data_from_hygdata[key][index]
                )

        for catalog_model in Catalog.query.all():
            for index, testing_data_example in enumerate(
                catalog_model.catalog_associations, start=0
            ):
                catalog_association_dict = vars(testing_data_example)
                catalog_association_dict.pop("_sa_instance_state")
                for key in catalog_association_dict.keys():
                    assert getattr(testing_data_example, key) == getattr(
                        testing_data_catalog_associations[catalog_model.tag][index], key
                    )

        assert CatalogAssociation.query.count() == len(testing_data_catalogs)

    @patch("starapp.api.click.echo")
    def test_create_catalogs(self, mock_click_echo, client):
        create_catalogs()

        mock_click_echo.assert_has_calls(
            [
                call(f"\nStart downloading catalogs"),
                *[call(f'Added catalog with tag: "{tag}"') for tag in CATALOGS],
                call("All catalogs have successfully saved in the database"),
            ]
        )

        for tag in CATALOGS:
            assert Catalog.query.filter_by(tag=tag).first() is not None

    @patch("starapp.api.click.echo")
    @patch("starapp.api.click.progressbar")
    def test_add_star(self, mock_progressbar, mock_click_echo, client):
        hygdata = pd.DataFrame.from_dict(JsonData.data_from_hygdata)
        data = hygdata.replace(np.nan, None)
        testing_data = JsonData.data_after_api

        mock_progressbar.return_value.__enter__.return_value = [
            con + ".txt" for con in list(testing_data[CONSTELLATION])
        ]

        for constellation_tag in testing_data[CONSTELLATION]:
            create_constellation_for_test(tag=constellation_tag)
        create_catalogs_for_test()

        stars, catalog_associations = [], []
        length_data = len(data)

        for index in range(length_data):
            add_star(stars, catalog_associations, data.loc[index])

        db.session.bulk_save_objects(stars)
        db.session.bulk_save_objects(catalog_associations)
        db.session.commit()

        for index in range(length_data):
            star_data = self.get_data_about_star_from_hygdata(testing_data, index)
            star_id = int(data.loc[index]["id"])
            check_model_fields(Star.query.get(star_id), star_data)

        testing_catalog_associations = []
        for tag in CATALOGS:
            for index in range(length_data):
                identifier = testing_data[tag][index]
                if identifier is not None:
                    testing_catalog_associations.append(
                        {
                            "star_id": testing_data["id"][index],
                            "identifier": str(identifier),
                            "catalog_tag": tag,
                        }
                    )

        for catalog_data in testing_catalog_associations:
            check_model_fields(
                CatalogAssociation.query.filter_by(
                    star_id=catalog_data["star_id"],
                    catalog_tag=catalog_data["catalog_tag"],
                ).first(),
                catalog_data,
            )

    @patch("starapp.api.create_views_for_constellation")
    @patch("starapp.api.click.echo")
    def test_add_constellation(
        self, mock_click_echo, mock_create_views_for_constellation, client
    ):
        create_constellations()

        mock_click_echo.assert_has_calls(
            [
                call(
                    f"\nStart downloading constellations ({len(LIST_OF_CONSTELLATIONS)})"
                ),
                call("Saving constellations in the database..."),
                call("Creating views for constellations"),
                call("Constellations have successfully saved in the database"),
            ]
        )
        constellations = mock_create_views_for_constellation.call_args_list[0][0][0]

        for tag, constellation_model in zip(LIST_OF_CONSTELLATIONS, constellations):
            assert Constellation.query.get(tag) is not None
            assert constellation_model.tag == tag

    def test_create_views_for_constellation(self, client):
        create_star_for_test(JsonData.star)
        constellation = JsonData.star[CONSTELLATION]
        create_views_for_constellation([type("", (), {"tag": constellation})])
        star_fields = POINT + (SPECT, "id", CONSTELLATION) + OTHER_DATA
        star_fields_str = ""
        for star_field in star_fields:
            star_fields_str += star_field + ","

        star_fields_str = star_fields_str[:-1]
        star = [
            {key: field for key, field in zip(star_fields, row)}
            for row in db.session.execute(
                text(f"""SELECT {star_fields_str} FROM stars_with_{constellation};""")
            )
        ][0]
        check_model_fields(Star.query.all()[0], star)
        db.session.execute(text(f"""DROP VIEW stars_with_{constellation};"""))
        db.session.commit()
