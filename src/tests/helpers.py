import json
from typing import Any, Union

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from models import Catalog, CatalogAssociation, Constellation, Star, db
from starapp.constants import (
    CATALOGS,
    CONSTELLATION,
    DEC,
    INT_CATALOGS,
    OTHER_DATA,
    RA,
    SERVER_URL,
    SPECT,
    STR_CATALOGS,
)


def json_decoder(data: Any) -> Any:
    try:
        return json.loads(data)
    except:
        print("Wrong json")


class _JsonData:
    """Testing class of getting data from "data.json"
    To get test data from file, get attribute from instance of class (JsonData) with name of field.
    For example: JsonData.star (return star like a python dictionary)
    To get test data with json encoding, get attribute from instance of class (JsonData) with name of field + "_json".
    For example: JsonData.star_json (return star like a json data).
    """

    _file_name = "tests/data.json"

    def __getattr__(self, name: str) -> Any:
        with open(self._file_name) as json_file:
            file_data = json_file.read()
            data = json_decoder(file_data)
            try:
                if name.rfind("_json", -5) != -1:
                    return json.dumps(data[name[:-5]])
                else:
                    return data[name]
            except KeyError as e:
                raise e


JsonData = _JsonData()
LIVE_SERVER_URL: str = "http://" + SERVER_URL + "/"


def create_constellation_for_test(tag: str) -> None:
    db.session.add(Constellation(tag=tag))
    db.session.commit()


def create_star_for_test(data: dict[str, str]) -> None:
    try:
        create_constellation_for_test(tag=data[CONSTELLATION])
    except:
        pass

    db.session.add(Star(**data))
    db.session.commit()


def create_catalog_association_for_test(data: dict[str, Union[str, int]]) -> None:
    db.session.add(CatalogAssociation(**data))
    db.session.commit()


def create_catalogs_for_test() -> None:
    for tag in CATALOGS:
        db.session.add(Catalog(tag=tag))
    db.session.commit()


def create_data_for_test() -> None:
    data_for_test = JsonData.data_after_api
    create_catalogs_for_test()
    for index in range(len(data_for_test[CONSTELLATION])):
        create_star_for_test(
            {
                "id": data_for_test["id"][index],
                "spect": data_for_test[SPECT][index],
                "con": data_for_test[CONSTELLATION][index],
                **{key: data_for_test[key][index] for key in OTHER_DATA},
                "ra": data_for_test[RA][index],
                "dec": data_for_test[DEC][index],
            }
        )

        for type_catalogs, func in zip((INT_CATALOGS, STR_CATALOGS), (int, str)):
            for tag in type_catalogs:
                if data_for_test[tag][index] is not None:
                    create_catalog_association_for_test(
                        {
                            "star_id": data_for_test["id"][index],
                            "catalog_tag": tag,
                            "identifier": func(data_for_test[tag][index]),
                        }
                    )


def check_model_fields(model: db.Model, data: dict[Any, Any], *args: str) -> None:
    """Compare fields of model and testing data from JsonData"""
    fields: dict[str, Any] = vars(model)
    fields.pop("_sa_instance_state")

    for delete_field in args:
        fields.pop(delete_field)

    for key in fields.keys():
        assert fields[key] == data[key]


def get_element_by_id(id: str, browser: webdriver.Firefox) -> WebElement:
    element = WebDriverWait(browser, 5).until(
        EC.presence_of_element_located((By.ID, id))
    )
    return element


def input_points(
    points: list[dict[str, Union[float, int]]], browser: webdriver.Firefox
) -> None:
    ra_input = get_element_by_id("ra_input", browser)
    dec_input = get_element_by_id("dec_input", browser)
    add_points_button = get_element_by_id("add_points_button", browser)

    for counter, point in enumerate(points, start=1):
        ra_input.send_keys(point["ra"])
        dec_input.send_keys(point["dec"])
        add_points_button.click()
        ra_input.clear()
        dec_input.clear()

        if counter == 1:
            assert (
                get_element_by_id("clear_points", browser).value_of_css_property(
                    "display"
                )
                == "block"
            )
            assert (
                get_element_by_id(
                    "search_points_button", browser
                ).value_of_css_property("display")
                == "block"
            )
