import redis
from enum import Enum
from .constants import CATALOGS, STR_CATALOGS, REDIS_SETTINGS, PAGINATION_SIZE
from models import CatalogAssociation


class TypeSearch(Enum):
    DISTANCE = 'dist'
    APPARENT_MAGNITUDE = 'mag'
    ABSOLUTE_MAGNITUDE = 'absmag'


def get_value(redis_, hash_, type_search : TypeSearch, index):
    name_of_hash = redis_.lrange(
        hash_ + ":" + type_search.value,
        index, index
    )
    to_dict = redis_.hgetall(name_of_hash[0])

    value = {
        "name": to_dict["name"],
        "value": float(to_dict["value"])
    }
    return value


class MetaSearch(type):
    _instances = {}

    def __call__(self, hash_, type_search : TypeSearch, *args, **kwargs):
        key = hash_ + ":" + type_search.value
        if key not in self._instances:
            self._instances[key] = super(MetaSearch, self).__call__(hash_, type_search, *args, **kwargs)
        return self._instances[key]
    
    def clear(self, hash_):
        for type_search in TypeSearch:
            try:
                del self._instances[hash_ + ":" + type_search.value]
            except KeyError:
                pass


class Search(metaclass=MetaSearch):
    def __init__(self, hash_, type_search : TypeSearch, stars=None):
        if stars is not None:
            self.redis_ = redis.StrictRedis(
                **REDIS_SETTINGS
            )
            self.hash_ : str = hash_
            self.type_search = type_search
            self.length = len(stars)

            sorted_stars = sorted(stars, key=lambda star: star[type_search.value])
            for star in sorted_stars:
                name_of_star = self.return_name_of_star(star['id'])
                name_of_hash = hash_ + ":" + self.type_search.value + ":" + name_of_star
                self.redis_.hset(
                    name_of_hash,
                    mapping={
                        "name": name_of_star,
                        "value": star[self.type_search.value],
                    }
                )
                self.redis_.rpush(
                    hash_ + ":" + type_search.value,
                    name_of_hash
                )
    
    def __del__(self):
        name_of_hash = self.hash_ + ":" + self.type_search.value
        for record in self.redis_.lrange(name_of_hash, 0, self.length):
            self.redis_.delete(record)
        self.redis_.delete(name_of_hash)

    def segment_search(self, minimum, maximum):
        min_value, min_index = self.binary_search(minimum, is_minimum=True)
        max_value, max_index = self.binary_search(maximum, is_minimum=False)

        if min_value is None or max_value is None or min_value["value"] > max_value["value"]:
            self.last_search = {}
            return {
                "minimum": "-",
                "maximum": "-",
                "sum": "-"
            }
        
        self.last_search = {
            "min_index": min_index,
            "max_index": max_index,
        }

        return {
            "minimum": min_value,
            "maximum": max_value,
            "sum": max_index - min_index + 1,
        }

    def binary_search(self, key, is_minimum):
        left = 0
        right = self.length - 1
        while left < right:
            mid = (left + right) // 2
            first_value = get_value(self.redis_, self.hash_, self.type_search, mid)
            second_value = get_value(self.redis_, self.hash_, self.type_search, mid + 1)

            if first_value["value"] <= key <= second_value["value"]:
                if is_minimum:
                    if first_value["value"] == second_value["value"]:
                        while first_value["value"] == key and mid > 0:
                            mid -= 1
                            first_value = get_value(self.redis_, self.hash_, self.type_search, mid)
                            second_value = get_value(self.redis_, self.hash_, self.type_search, mid + 1)

                        if mid == 0 and first_value["value"] == key:
                            result_value = first_value
                            result_index = mid
                        else:
                            result_value = second_value
                            result_index = mid + 1
                    else:
                        result_value = second_value
                        result_index = mid + 1
                else:
                    if first_value["value"] == second_value["value"]:
                        while second_value["value"] == key and mid + 1 < self.length-1:
                            mid += 1
                            first_value = get_value(self.redis_, self.hash_, self.type_search, mid)
                            second_value = get_value(self.redis_, self.hash_, self.type_search, mid + 1)
    
                        if mid + 1 == self.length - 1 and second_value["value"] == key:
                            result_value = second_value
                            result_index = mid + 1
                        else:
                            result_value = first_value
                            result_index = mid
                    else:
                        result_value = first_value
                        result_index = mid

                return result_value, result_index

            elif first_value["value"] < key:
                left = mid + 1
            elif first_value["value"] > key:
                right = mid
        
        if is_minimum:
            if first_value["value"] >= key: 
                return first_value, mid
        else:
            if second_value["value"] <= key:
                return second_value, mid + 1
        return None, None
    
    def sort_search(self, page, descending=False):
        try:
            min_index = self.last_search['min_index']
            max_index = self.last_search['max_index']
        except KeyError:
            return []

        result = []
        if descending:
            start_index = max_index - (page - 1) * PAGINATION_SIZE
            pagination_min = max_index - PAGINATION_SIZE * page + 1
            end_index = (pagination_min if pagination_min > min_index else min_index) - 1
            incr = -1
            if start_index < min_index:
                return result
        else:
            start_index = min_index + (page - 1) * PAGINATION_SIZE
            pagination_max = min_index + PAGINATION_SIZE * page - 1
            end_index = (pagination_max if pagination_max < max_index else max_index) + 1
            incr = 1
            if start_index > max_index:
                return result

        for index in range(
                start_index,
                end_index, incr
            ):
            value = get_value(
                self.redis_,
                self.hash_,
                self.type_search,
                index
            )
            result.append(value)
        
        return result

    @staticmethod
    def return_name_of_star(star_id):
        for tag in CATALOGS:
            catalog_association = CatalogAssociation.query.filter_by(
                star_id=star_id, 
                catalog_tag=tag,
            ).first()
            if catalog_association is not None:
                identifier = catalog_association.identifier
                return (
                        identifier if tag in STR_CATALOGS
                        else tag.upper() + ' ' + identifier
                )