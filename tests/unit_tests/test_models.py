from tests.helpers import (
    JsonData,
    check_model_fields,
    create_constellation_for_test,
    create_star_for_test,
    create_catalogs_for_test,
)
from models import Catalog, Constellation, Star, CatalogAssociation, db
from starapp.constants import CATALOGS


class TestModels:
    def test_catalogs(self, client):
        create_catalogs_for_test()
        for tag in CATALOGS:
            assert Catalog.query.get(tag) is not None

    def test_catalog_association(self, client):
        create_catalogs_for_test()
        create_star_for_test(JsonData.star)

        testing_data_catalog_association = JsonData.catalog_association

        catalog_association = CatalogAssociation(**testing_data_catalog_association)

        db.session.add(catalog_association)
        db.session.commit()

        testing_catalog_association = CatalogAssociation.query.all()[0]
        testing_catalog = Catalog.query.get(JsonData.catalog)
        testing_star = Star.query.all()[0]

        assert testing_catalog.catalog_associations == [testing_catalog_association]
        assert testing_catalog_association.star == testing_star

        check_model_fields(
            testing_catalog_association, testing_data_catalog_association, "star"
        )

    def test_constellation(self, client):
        create_constellation_for_test(JsonData.constellation["tag"])
        check_model_fields(Constellation.query.all()[0], JsonData.constellation)

    def test_star(self, client):
        create_star_for_test(JsonData.star)
        check_model_fields(Star.query.all()[0], JsonData.star, "id")
