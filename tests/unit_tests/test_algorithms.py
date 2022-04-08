from unittest.mock import patch
from fakeredis import FakeStrictRedis
from starapp.algorithms import Search, TypeSearch, get_value, MetaSearch
from models import Star, CatalogAssociation
from tests.helpers import JsonData, create_data_for_test, create_catalog_association_for_test, create_star_for_test, create_catalogs_for_test
import math


@patch('starapp.algorithms.redis.StrictRedis', FakeStrictRedis)
class TestSearch:
    hash_ = "example_hash"

    def _return_search(self, hash_=None):
        return Search(
            hash_=self.hash_ if hash_ is None else hash_,
            type_search=TypeSearch('dist'),
            stars=[vars(star) for star in Star.query.all()]
        )
    
    @patch('starapp.algorithms.Search.return_name_of_star')
    def test__init__(self, mock_return_name_of_star, client):
        result = JsonData.search_dist
        mock_return_name_of_star.side_effect = [data["name"] for data in result]
        create_data_for_test()
        search = self._return_search()
        testing_array = search.redis_.lrange(
            self.hash_ + ":dist",
            0, len(result)
        )

        assert testing_array != []

        for hash_data, result in zip(testing_array, result):
            testing_dict = search.redis_.hgetall(hash_data)
            assert {
                "name": testing_dict["name"],
                "value": float(testing_dict["value"])
             } == result
        
        Search.clear(hash_=self.hash_)
    
    def test__del__(self, client):
        delete_hash = "delete_hash"
        create_data_for_test()
        search = self._return_search(hash_=delete_hash)
        length = search.length
        redis_ = search.redis_
        search.__del__()
        testing_data = JsonData.search_dist
        
        for dict_ in testing_data:
            data_hash = redis_.hgetall(
                delete_hash + ":dist:" + dict_["name"]
            )
            assert data_hash == {}
        
        assert redis_.lrange(delete_hash + ":dist", 0, length) == []

    def test_return_name_of_star(self, client):
        create_data_for_test()
        search = self._return_search()
        for id, result in zip(JsonData.data_after_api["id"], JsonData.return_name_of_star):
            assert search.return_name_of_star(
                id
            ) == result
    
    def test_get_value(self, client):
        create_data_for_test()
        search = self._return_search()
        testing_data = JsonData.search_dist

        for dict_ in testing_data:
            data_hash = search.redis_.hset(
                self.hash_ + ":dist:" + dict_["name"],
                mapping=dict_
            )
            search.redis_.rpush(
                self.hash_ + ":dist",
                data_hash
            )
        
        for index, result in enumerate(testing_data, start=0):
            assert get_value(search.redis_, self.hash_, TypeSearch.DISTANCE, index) == result
        Search.clear(hash_=self.hash_)

    def test_binary_search(self, client):
        create_data_for_test()
        search = self._return_search()

        for testing_data in JsonData.binary_search:
            result = search.binary_search(
                **testing_data['input']
            ) 
            if result is not None:
                result = list(result)
            assert result == testing_data['result']
        Search.clear(hash_=self.hash_)
    
    def test_binary_search_if_first_value_equals_second_value(self, client):
        create_catalogs_for_test()
        testing_data = JsonData.first_value_equals_second_value
        def create_stars(index):
            for data in testing_data["stars"][index]:
                catalog_association_data = data.pop('catalog')
                star = create_star_for_test(data)
                create_catalog_association_for_test({
                    **catalog_association_data
                })
        
        create_stars(0)
        search = self._return_search()
        for counter, (input_, testing_result) in enumerate(zip(testing_data["inputs"], testing_data["result"]), start=1):
            if counter == 3:
                CatalogAssociation.query.delete()
                Star.query.delete()
                create_stars(1)
                Search.clear(hash_=self.hash_)
                search = self._return_search()
            result = search.binary_search(**input_)
            assert testing_result == list(result)
        Search.clear(hash_=self.hash_)

    def test_segment_search(self, client):
        create_data_for_test()
        search = self._return_search()

        for testing_data in JsonData.segment_search:
            assert search.segment_search(
                **testing_data['input']
            ) == testing_data['result']
        Search.clear(hash_=self.hash_)
    
    def test_sort_search(self, client):
        create_data_for_test()
        search = self._return_search()
        for testing_data, testing_result in zip(JsonData.sort_search, JsonData.algorithms_search_sort_result):
            search.last_search = testing_data["last_search"]

            result = search.sort_search(
                page=testing_data["input"]["page"],
                descending=testing_data["input"]["descending"]
            )
 
            assert result == testing_result
        Search.clear(hash_=self.hash_)
    

class TestSearchMeta:
    def test__call__(self, client):
        class ExampleClass(metaclass=MetaSearch):
            def __init__(self, hash_, type_search : TypeSearch):
                self.hash_ = hash_
                self.type_search = type_search

        first_class = ExampleClass(hash_='first_hash', type_search=TypeSearch.DISTANCE)
        second_class = ExampleClass(hash_='first_hash', type_search=TypeSearch.DISTANCE)
        third_class = ExampleClass(hash_='first_hash', type_search=TypeSearch.APPARENT_MAGNITUDE)
        fourth_class = ExampleClass(hash_='second_hash', type_search=TypeSearch.APPARENT_MAGNITUDE)

        assert first_class == second_class
        assert first_class != third_class
        assert first_class != fourth_class
        ExampleClass.clear(hash_="first_hash")
        ExampleClass.clear(hash_="second_hash")
        del ExampleClass
    
    def test_clear(self, client):
        class ExampleClass(metaclass=MetaSearch):
            def __init__(self, hash_, type_search : TypeSearch):
                self.hash_ = hash_
                self.type_search = type_search
    
        random_hash = 'random_hash'
        first_class = ExampleClass(hash_=random_hash, type_search=TypeSearch.DISTANCE)
        second_class = ExampleClass(hash_=random_hash, type_search=TypeSearch.APPARENT_MAGNITUDE)
        ExampleClass.clear(hash_=random_hash)
        assert first_class != ExampleClass(hash_=random_hash, type_search=TypeSearch.DISTANCE)
        assert second_class != ExampleClass(hash_=random_hash, type_search=TypeSearch.APPARENT_MAGNITUDE)
        ExampleClass.clear(hash_=random_hash)
        del ExampleClass