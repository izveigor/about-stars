import json
from models import db, Constellation, Catalog, CatalogAssociation, Star
from starapp.constants import (CONSTELLATION, POINT, INT_CATALOGS, STR_CATALOGS, CATALOGS,
                               POINT, SPECT, OTHER_DATA)
from starapp.constants import SERVER_URL
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def json_decoder(data):
    try:
        return json.loads(data)
    except:
        print('Wrong json')


class _JsonData:
    '''Testing class of getting data from "data.json"
       To get test data from file, get attribute from instance of class (JsonData) with name of field.
       For example: JsonData.star (return star like a python dictionary)
       To get test data with json encoding, get attribute from instance of class (JsonData) with name of field + "_json".
       For example: JsonData.star_json (return star like a json data).
    '''
    _file_name = 'tests/data.json'
    
    def __getattr__(self, name):
        with open(self._file_name) as json_file:
            file_data = json_file.read()
            data = json_decoder(file_data)
            try:
                if name.rfind('_json', -5) != -1:
                    return json.dumps(data[name[:-5]])
                else:
                    return data[name]
            except KeyError as e:
                raise e


JsonData = _JsonData()
LIVE_SERVER_URL = "http://" + SERVER_URL + "/"


def create_constellation_for_test(tag):
    db.session.add(Constellation(tag=tag))
    db.session.commit()


def create_star_for_test(data):
    try:
        create_constellation_for_test(tag=data[CONSTELLATION])
    except:
        pass

    db.session.add(Star(**data))
    db.session.commit()


def create_catalog_association_for_test(data):
    db.session.add(CatalogAssociation(**data))
    db.session.commit()


def create_catalogs_for_test():
    for tag in CATALOGS:
        db.session.add(Catalog(tag=tag))
    db.session.commit()


def create_data_for_test():
    data_for_test = JsonData.data_after_api
    create_catalogs_for_test()
    for index in range(len(data_for_test[CONSTELLATION])):
        create_star_for_test({
            "id": data_for_test["id"][index],
            "spect": data_for_test[SPECT][index],
            "con": data_for_test[CONSTELLATION][index],
            **{key: data_for_test[key][index] for key in OTHER_DATA},
            "ra": data_for_test[POINT[0]][index],
            "dec": data_for_test[POINT[1]][index],
        })

        for type_catalogs, func in zip((INT_CATALOGS, STR_CATALOGS), (int, str)):
            for tag in type_catalogs:
                if data_for_test[tag][index] is not None:
                    create_catalog_association_for_test({
                        "star_id": data_for_test["id"][index],
                        "catalog_tag": tag,
                        "identifier": func(data_for_test[tag][index]),
                    })



def check_model_fields(model, data, *args):
    '''Compare fields of model and testing data from JsonData'''
    fields = vars(model)
    fields.pop('_sa_instance_state')

    for delete_field in args:
        fields.pop(delete_field)

    for key in fields.keys():
        assert fields[key] == data[key]


def get_element_by_id(id, browser):
    element = WebDriverWait(browser, 5).until(
        EC.presence_of_element_located((
            By.ID,
            id
        ))
    )
    return element


def input_points(points, browser):
    ra_input = get_element_by_id("ra_input", browser)
    dec_input = get_element_by_id("dec_input", browser)
    add_points_button = get_element_by_id("add_points_button", browser)

    for counter, point in enumerate(points, start=1):
        ra_input.send_keys(point['ra'])
        dec_input.send_keys(point['dec'])
        add_points_button.click()
        ra_input.clear()
        dec_input.clear()

        if counter == 1:
            assert get_element_by_id("clear_points", browser).value_of_css_property("display") == "block"
            assert get_element_by_id("search_points_button", browser).value_of_css_property("display") == "block"