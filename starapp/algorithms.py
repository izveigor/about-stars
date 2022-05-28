from enum import Enum
from typing import Any, Optional, TypedDict, Union

import redis

from models import CatalogAssociation

from .constants import CATALOGS, PAGINATION_SIZE, REDIS_SETTINGS, STR_CATALOGS


class TypeSearch(Enum):
    DISTANCE = "dist"
    APPARENT_MAGNITUDE = "mag"
    ABSOLUTE_MAGNITUDE = "absmag"


TypeRedisValue = TypedDict("TypeRedisValue", {"name": str, "value": float}, total=False)


def get_value(
    redis_: Any, hash_: str, type_search: TypeSearch, index: int
) -> TypeRedisValue:
    name_of_hash = redis_.lrange(hash_ + ":" + type_search.value, index, index)
    to_dict = redis_.hgetall(name_of_hash[0])

    value: TypeRedisValue = {"name": to_dict["name"], "value": float(to_dict["value"])}
    return value


class MetaSearch(type):
    _instances: dict[str, object] = {}

    def __call__(self, hash_: str, type_search: TypeSearch, *args: Any, **kwargs: Any):  # type: ignore
        key: str = hash_ + ":" + type_search.value
        if key not in self._instances:
            self._instances[key] = super(MetaSearch, self).__call__(
                hash_, type_search, *args, **kwargs
            )
        return self._instances[key]

    def clear(self, hash_: str) -> None:
        for type_search in TypeSearch:
            try:
                del self._instances[hash_ + ":" + type_search.value]
            except KeyError:
                pass


class Search(metaclass=MetaSearch):
    redis_: Any
    hash_: str
    type_search: TypeSearch
    length: int
    last_search: dict[str, int]

    def __init__(
        self,
        hash_: str,
        type_search: TypeSearch,
        stars: Optional[list[dict[str, Any]]] = None,
    ):
        if stars is None:
            return

        self.redis_ = redis.StrictRedis(**REDIS_SETTINGS)
        self.hash_ = hash_
        self.type_search = type_search
        self.length = len(stars)

        sorted_stars = sorted(stars, key=lambda star: star[type_search.value])  # type: ignore
        for star in sorted_stars:
            name_of_star = self.return_name_of_star(star["id"])
            name_of_hash = hash_ + ":" + self.type_search.value + ":" + name_of_star
            self.redis_.hset(
                name_of_hash,
                mapping={
                    "name": name_of_star,
                    "value": star[self.type_search.value],
                },
            )
            self.redis_.rpush(hash_ + ":" + type_search.value, name_of_hash)

    def __del__(self) -> None:
        name_of_hash: str = self.hash_ + ":" + self.type_search.value
        for record in self.redis_.lrange(name_of_hash, 0, self.length):
            self.redis_.delete(record)
        self.redis_.delete(name_of_hash)

    def segment_search(
        self, minimum: float, maximum: float
    ) -> dict[str, Union[TypeRedisValue, int, str]]:
        min_value: Optional[TypeRedisValue]
        min_index: Optional[int]
        max_value: Optional[TypeRedisValue]
        max_index: Optional[int]
        min_value, min_index = self.binary_search(minimum, is_minimum=True)
        max_value, max_index = self.binary_search(maximum, is_minimum=False)

        is_one_of_values_none: bool = (min_value is None) or (max_value is None)
        is_one_of_indexes_none: bool = (min_index is None) or (max_index is None)

        if (
            is_one_of_values_none
            or is_one_of_indexes_none
            or (min_value["value"] > max_value["value"])  # type: ignore
        ):
            self.last_search = {}
            return {"minimum": "-", "maximum": "-", "sum": "-"}

        self.last_search = {
            "min_index": min_index,  # type: ignore
            "max_index": max_index,  # type: ignore
        }

        return {
            "minimum": min_value,  # type: ignore
            "maximum": max_value,  # type: ignore
            "sum": max_index - min_index + 1,  # type: ignore
        }

    def binary_search(
        self, key: float, is_minimum: bool
    ) -> tuple[Optional[TypeRedisValue], Optional[int]]:
        left: int = 0
        right: int = self.length - 1
        while left < right:
            mid: int = (left + right) // 2
            first_value = get_value(self.redis_, self.hash_, self.type_search, mid)
            second_value = get_value(self.redis_, self.hash_, self.type_search, mid + 1)

            if first_value["value"] <= key <= second_value["value"]:
                if is_minimum:
                    if first_value["value"] == second_value["value"]:
                        while first_value["value"] == key and mid > 0:
                            mid -= 1
                            first_value = get_value(
                                self.redis_, self.hash_, self.type_search, mid
                            )
                            second_value = get_value(
                                self.redis_, self.hash_, self.type_search, mid + 1
                            )

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
                        while (
                            second_value["value"] == key and mid + 1 < self.length - 1
                        ):
                            mid += 1
                            first_value = get_value(
                                self.redis_, self.hash_, self.type_search, mid
                            )
                            second_value = get_value(
                                self.redis_, self.hash_, self.type_search, mid + 1
                            )

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

    def sort_search(self, page: int, descending: bool = False) -> list[TypeRedisValue]:
        try:
            min_index: int = self.last_search["min_index"]
            max_index: int = self.last_search["max_index"]
        except KeyError:
            return []

        result: list[TypeRedisValue] = []
        incr: int
        start_index: int
        end_index: int
        if descending:
            start_index = max_index - (page - 1) * PAGINATION_SIZE
            pagination_min = max_index - PAGINATION_SIZE * page + 1
            end_index = (
                pagination_min if pagination_min > min_index else min_index
            ) - 1
            incr = -1
            if start_index < min_index:
                return result
        else:
            start_index = min_index + (page - 1) * PAGINATION_SIZE
            pagination_max = min_index + PAGINATION_SIZE * page - 1
            end_index = (
                pagination_max if pagination_max < max_index else max_index
            ) + 1
            incr = 1
            if start_index > max_index:
                return result

        for index in range(start_index, end_index, incr):
            value = get_value(self.redis_, self.hash_, self.type_search, index)
            result.append(value)

        return result

    @staticmethod
    def return_name_of_star(star_id: int) -> str:
        for tag in CATALOGS:
            catalog_association = CatalogAssociation.query.filter_by(
                star_id=star_id,
                catalog_tag=tag,
            ).first()
            if catalog_association is not None:
                identifier: str = catalog_association.identifier
                return (
                    identifier
                    if tag in STR_CATALOGS
                    else tag.upper() + " " + identifier
                )
        raise ValueError()
